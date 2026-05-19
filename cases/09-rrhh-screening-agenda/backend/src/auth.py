"""
lgrw_common.auth — Middleware de autenticación y guardrails compartido.

Patrón unificado para los 25 backends: DEMO sin credenciales o
OAuth2/OIDC con Bearer JWT (opt-in vía USE_OAUTH2=true).

Hardening v4.15.0:
- JWKS cache con TTL 300s (antes: fetch HTTP en cada request).
- OAUTH2_AUDIENCE y OAUTH2_ISSUER obligatorios cuando USE_OAUTH2=true.
- Mensaje 401 OAuth2 sin filtrar detalles internos del error.
- Verificación JWT con joserfc (reemplaza python-jose+ecdsa abandonada).
"""
from __future__ import annotations

import os
import time
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
    return path.startswith("/api/")


def client_identity(request: Request) -> str:
    if trust_proxy_headers():
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for.strip():
            return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


_JWKS_CACHE: dict[str, tuple[float, dict]] = {}
_JWKS_TTL_SECONDS = 300


def _fetch_jwks(jwks_url: str) -> dict:
    now = time.monotonic()
    cached = _JWKS_CACHE.get(jwks_url)
    if cached is not None and (now - cached[0]) < _JWKS_TTL_SECONDS:
        return cached[1]
    import json as _json
    import urllib.request
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
        from joserfc import jwt
        from joserfc.jwk import KeySet
        keys_dict = _fetch_jwks(jwks_url)
        key_set = KeySet.import_key_set(keys_dict)
        decoded = jwt.decode(token, key_set, algorithms=["RS256", "ES256"])
        claims_registry = jwt.JWTClaimsRegistry(
            aud={"essential": True, "value": audience},
            iss={"essential": True, "value": issuer},
            exp={"essential": True},
        )
        claims_registry.validate(decoded.claims)
    except ImportError as exc:
        raise ValueError("joserfc no instalado") from exc
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
