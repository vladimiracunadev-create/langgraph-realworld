"""
integrations.py — Adaptadores y simulador de pilotaje para Caso 12.

DEMO: lectura local de instruments.json, item_banks.json, policy.json y
generación determinista de la matriz de respuestas piloto a partir de la
cohorte declarada en cada instrumento.

LIVE: en una integración real, estos adaptadores conectarían con LMS
(Moodle, Canvas), plataformas de pilotaje en línea (Qualtrics, REDCap)
o bases vectoriales con bancos de ítems calibrados (pgvector + py-irt).
"""
from __future__ import annotations

import json
import logging
import random
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer %s: %s", path.name, exc)
        return fallback


def get_instrument(instrument_id: str, data_dir: str) -> dict:
    instruments = _load_json(Path(data_dir) / "instruments.json", [])
    for inst in instruments:
        if inst.get("id") == instrument_id:
            return inst
    if instruments:
        logger.info("instrument_id=%s no encontrado; fallback al primero.", instrument_id)
        return instruments[0]
    return {}


def get_item_bank(instrument_id: str, data_dir: str) -> list:
    banks = _load_json(Path(data_dir) / "item_banks.json", {})
    return banks.get(instrument_id, [])


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "policy.json", {})


# ---------------------------------------------------------------------------
# Generador determinista de respuestas piloto
# ---------------------------------------------------------------------------

def _ability_dist(rng: random.Random, n: int, mu: float, sigma: float,
                  lo: float, hi: float) -> list[float]:
    """Distribución gaussiana truncada determinista para habilidad latente."""
    abilities = []
    for _ in range(n):
        a = rng.gauss(mu, sigma)
        abilities.append(max(lo, min(hi, a)))
    return abilities


def _difficulty_from_meta(item: dict) -> float:
    """
    Mapea claridad/representatividad + un spread determinista (hash del id)
    a una dificultad teórica en [0,1]. Ítems con baja claridad/representatividad
    tienden a mayor dificultad efectiva; el hash inyecta variabilidad entre
    ítems para que la matriz piloto no sea degenerada.
    """
    claridad = float(item.get("claridad", 0.85))
    repr_ = float(item.get("representatividad", 0.85))
    base = 1.0 - 0.5 * (claridad + repr_) / 2 - 0.10
    # Spread determinista por id (crc32 — estable entre procesos): ±0.30
    h = zlib.crc32(str(item.get("id", "")).encode("utf-8")) % 1000
    spread = (h / 1000.0) * 0.60 - 0.30
    return max(0.10, min(0.90, base + spread))


def _group_bias(item: dict, grupo: str, all_grupos: list[str]) -> float:
    """
    Sesgo direccional por grupo. Para items con sesgo_estimado alto,
    penaliza al segundo grupo declarado en `grupos_dif`. Determinista.
    """
    sesgo = float(item.get("sesgo_estimado", 0.0))
    if not all_grupos or sesgo < 0.12:
        return 0.0
    if len(all_grupos) >= 2 and grupo == all_grupos[1]:
        return -sesgo
    return 0.0


def generate_dicotomic_responses(instrument: dict, items: list) -> list[dict]:
    """
    Genera respuestas piloto correcto/incorrecto a partir de un modelo
    Rasch‐like: P(correcto) = sigmoide(habilidad - dificultad + sesgo).
    """
    cohorte = instrument.get("cohorte", {})
    n = int(cohorte.get("n", 30))
    seed = int(cohorte.get("seed", 12000))
    mu = float(cohorte.get("habilidad_media", 0.5))
    sigma = float(cohorte.get("habilidad_sd", 0.18))
    grupos = instrument.get("grupos_dif", []) or ["grupo_a", "grupo_b"]

    rng = random.Random(seed)
    abilities = _ability_dist(rng, n, mu, sigma, 0.05, 0.95)
    respuestas = []
    for i, hab in enumerate(abilities):
        grupo = grupos[i % len(grupos)]
        ev_id = f"E-{i + 1:03d}"
        items_resp = {}
        for it in items:
            d = _difficulty_from_meta(it)
            bias = _group_bias(it, grupo, grupos)
            # diferencial ability-difficulty con leve ruido determinista
            # Mayor pendiente (5.5) y menor ruido (±0.15) → señal item-total fuerte,
            # produciendo α aceptable cuando los ítems están bien calibrados.
            x = (hab - d + bias) * 5.5 + rng.uniform(-0.15, 0.15)
            p = 1.0 / (1.0 + pow(2.71828, -x))
            correcta = 1 if rng.random() < p else 0
            items_resp[it["id"]] = correcta
        respuestas.append({
            "evaluado_id": ev_id,
            "grupo": grupo,
            "habilidad_real": round(hab, 3),
            "respuestas": items_resp,
        })
    return respuestas


def generate_likert_responses(instrument: dict, items: list) -> list[dict]:
    """
    Genera respuestas piloto Likert 1‑5. Modelo: respuesta ≈ latente + ruido,
    clip [1,5]; items inversos invierten la dirección antes de generar.
    """
    cohorte = instrument.get("cohorte", {})
    n = int(cohorte.get("n", 50))
    seed = int(cohorte.get("seed", 12000))
    mu = float(cohorte.get("habilidad_media", 3.4))
    sigma = float(cohorte.get("habilidad_sd", 0.85))
    grupos = instrument.get("grupos_dif", []) or ["grupo_a"]

    rng = random.Random(seed)
    latentes = _ability_dist(rng, n, mu, sigma, 1.0, 5.0)
    respuestas = []
    for i, lat in enumerate(latentes):
        grupo = grupos[i % len(grupos)]
        ev_id = f"E-{i + 1:03d}"
        items_resp = {}
        for it in items:
            sesgo = float(it.get("sesgo_estimado", 0.0))
            bias = _group_bias(it, grupo, grupos)
            base = lat + bias * 2.5 + rng.gauss(0, 0.45 + sesgo)
            if it.get("inverso"):
                base = 6.0 - base  # invierte alrededor de 3
            val = int(round(max(1.0, min(5.0, base))))
            items_resp[it["id"]] = val
        respuestas.append({
            "evaluado_id": ev_id,
            "grupo": grupo,
            "habilidad_real": round(lat, 3),
            "respuestas": items_resp,
        })
    return respuestas


def generate_responses(instrument: dict, items: list) -> list[dict]:
    formato = instrument.get("formato", "dicotomico")
    if formato == "likert":
        return generate_likert_responses(instrument, items)
    return generate_dicotomic_responses(instrument, items)
