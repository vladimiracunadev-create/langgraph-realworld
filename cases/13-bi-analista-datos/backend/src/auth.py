"""
auth.py — Middleware de autenticación y guardrails para Caso 13.

Soporta dos modos (opt-in, backward-compatible):
  - Modo DEMO (default): DEMO_AUTH_TOKEN opcional vía header X-Demo-Token.
  - Modo OAuth2/OIDC:    USE_OAUTH2=true + Bearer JWT validado contra JWKS.

Nota: El endpoint protegido en este caso es /chat (no /api/).
"""
from __future__ import annotations

import os
from collections import deque
from hmac import compare_digest
from time import monotonic
from typing import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse


def demo_auth_token() -> str:
    return os.getenv("DEMO_AUTH_TOKEN", "").strip()


def rate_limit_rpm() -> int:
    raw = os.getenv("RATE_LIMIT_RPM", "0").strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        return 0


def trust_proxy_headers() -> bool:
    return os.getenv("TRUST_PROXY_HEADERS", "false").strip().lower() in {"1", "true", "yes", "on"}


def use_oauth2() -> bool:
    return os.getenv("USE_OAUTH2", "false").strip().lower() in {"1", "true", "yes"}


def protected_path(path: str) -> bool:
    # Caso 13 protege /chat en lugar de /api/
    return path == "/chat"


def client_identity(request: Request) -> str:
    if trust_proxy_headers():
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for.strip():
            return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"



import time

_JWKS_CACHE: dict[str, tuple[float, dict]] = {}
_JWKS_TTL_SECONDS = 300


def _fetch_jwks(jwks_url: str) -> dict:
    now = time.monotonic()
    cached = _JWKS_CACHE.get(jwks_url)
    if cached is not None and (now - cached[0]) < _JWKS_TTL_SECONDS:
        return cached[1]
    import urllib.request
    import json as _json
    with urllib.request.urlopen(jwks_url, timeout=5) as resp:  # noqa: S310
        keys = _json.loads(resp.read())
    _JWKS_CACHE[jwks_url] = (now, keys)
    return keys


def _validate_jwt(token: str) -> None:
    jwks_url = os.getenv("OAUTH2_JWKS_URL", "").strip()
    audience = os.getenv("OAUTH2_AUDIENCE", "").strip()
    issuer = os.getenv("OAUTH2_ISSUER", "").strip()
    if not jwks_url:
        raise ValueError("USE_OAUTH2=true pero OAUTH2_JWKS_URL no está configurado")
    if not audience:
        raise ValueError("USE_OAUTH2=true requiere OAUTH2_AUDIENCE configurado")
    if not issuer:
        raise ValueError("USE_OAUTH2=true requiere OAUTH2_ISSUER configurado")

    try:
        from jose import jwt
        keys = _fetch_jwks(jwks_url)
        options: dict = {}
        jwt.decode(token, keys, algorithms=["RS256", "ES256"],
                   audience=audience or None, issuer=issuer or None, options=options)
    except ImportError as exc:
        raise ValueError("python-jose no instalado") from exc
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Token OAuth2 invalido") from exc


async def auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable],
    rate_limit_buckets: dict,
    trace_id: str = "",
) -> JSONResponse:
    if not protected_path(request.url.path):
        return await call_next(request)

    if use_oauth2():
        bearer = request.headers.get("Authorization", "").strip()
        token = bearer.removeprefix("Bearer ").strip()
        try:
            _validate_jwt(token)
        except ValueError as exc:
            resp = JSONResponse(status_code=401, content={"detail": str(exc)})
            if trace_id:
                resp.headers["X-Trace-ID"] = trace_id
            return resp
    else:
        expected = demo_auth_token()
        if expected:
            provided = request.headers.get("x-demo-token", "").strip()
            if not compare_digest(provided, expected):
                resp = JSONResponse(status_code=401, content={"detail": "Missing or invalid X-Demo-Token"})
                if trace_id:
                    resp.headers["X-Trace-ID"] = trace_id
                return resp

    limit = rate_limit_rpm()
    if limit > 0:
        now = monotonic()
        bucket: deque = rate_limit_buckets.setdefault(client_identity(request), deque())
        while bucket and now - bucket[0] >= 60:
            bucket.popleft()
        if len(bucket) >= limit:
            resp = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            if trace_id:
                resp.headers["X-Trace-ID"] = trace_id
            resp.headers["X-RateLimit-Limit"] = str(limit)
            resp.headers["X-RateLimit-Remaining"] = "0"
            return resp
        bucket.append(now)

    response = await call_next(request)
    if limit > 0:
        bucket = rate_limit_buckets.get(client_identity(request), deque())
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(limit - len(bucket), 0))
    return response
