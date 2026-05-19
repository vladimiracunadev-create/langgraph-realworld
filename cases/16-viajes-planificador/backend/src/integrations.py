"""
integrations.py — Adaptadores de datos para Caso 16 (Planificador de Viajes).

DEMO: lectura local de viajes.json, politica_viajes.json, inventario_vuelos.json,
inventario_hoteles.json, inventario_movilidad.json.

LIVE: un cliente real envolvería APIs de GDS/OTA (Amadeus, Sabre, Skyscanner,
Booking, Google Flights), políticas corporativas configurables por empresa
y motores de booking transaccionales.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer %s: %s", path.name, exc)
        return fallback


def get_viajes(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "viajes.json", [])


def get_viaje(viaje_id: str, data_dir: str) -> dict:
    items = get_viajes(data_dir)
    for v in items:
        if v.get("id") == viaje_id:
            return v
    if items:
        logger.info("viaje_id=%s no encontrado; fallback a la primera.", viaje_id)
        return items[0]
    return {
        "id": viaje_id, "viajero": "", "origen": "", "destino": "",
        "ciudad_destino": "", "fecha_ida": "", "fecha_vuelta": "",
        "noches": 0, "presupuesto_clp": 0, "preferencias": {},
        "decision_viajero": "aprobar", "ajuste_solicitado": "",
    }


def get_politica_viajes(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "politica_viajes.json", {})


def get_inventario_vuelos(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "inventario_vuelos.json", {})


def get_inventario_hoteles(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "inventario_hoteles.json", {})


def get_inventario_movilidad(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "inventario_movilidad.json", {})


# ---------------------------------------------------------------------------
# Búsqueda determinista (DEMO)
# ---------------------------------------------------------------------------

_CLASE_RANK = {"economy": 1, "premium_economy": 2, "business": 3, "first": 4}


def buscar_vuelo_optimo(origen: str, destino: str, clase_max: str, inventario: dict) -> dict:
    """Devuelve el vuelo más barato cuya clase no supere `clase_max`."""
    ruta = f"{origen}-{destino}"
    opciones = inventario.get(ruta, []) or []
    max_rank = _CLASE_RANK.get(clase_max, 1)
    candidatos = [v for v in opciones if _CLASE_RANK.get(v.get("clase", "economy"), 1) <= max_rank]
    if not candidatos:
        return {}
    return sorted(candidatos, key=lambda x: x.get("precio_clp", 10**12))[0]


def buscar_hotel_optimo(ciudad: str, categoria_min: int, categoria_max: int, inventario: dict) -> dict:
    """Hotel más barato dentro de rango de categoría permitido."""
    opciones = inventario.get(ciudad.lower(), []) or []
    candidatos = [
        h for h in opciones
        if categoria_min <= h.get("categoria", 0) <= categoria_max
    ]
    if not candidatos:
        # fallback: cualquier hotel disponible bajo el máximo (puede violar mínimo)
        candidatos = [h for h in opciones if h.get("categoria", 0) <= categoria_max]
    if not candidatos:
        return {}
    return sorted(candidatos, key=lambda x: x.get("tarifa_noche_clp", 10**12))[0]


def buscar_movilidad_paquete(ciudad: str, dias: int, inventario: dict) -> dict:
    """Combina transfer aeropuerto + transporte local por `dias`."""
    opciones = inventario.get(ciudad.lower(), []) or []
    if not opciones:
        return {"items": [], "costo_total_clp": 0}
    transfer = next((m for m in opciones if m.get("tipo") == "transfer_aeropuerto"), {})
    local = next((m for m in opciones if m.get("tipo") == "transporte_local_dia"), {})
    items = []
    total = 0
    if transfer:
        items.append({**transfer, "subtotal_clp": transfer.get("precio_clp", 0)})
        total += transfer.get("precio_clp", 0)
    if local:
        sub = local.get("precio_clp", 0) * max(dias, 0)
        items.append({**local, "dias": dias, "subtotal_clp": sub})
        total += sub
    return {"items": items, "costo_total_clp": total}
