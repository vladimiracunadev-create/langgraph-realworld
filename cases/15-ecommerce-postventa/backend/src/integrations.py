"""
integrations.py — Adaptadores de datos para Caso 15 (E-commerce Postventa).

DEMO: lectura local de orders.json, return_policy.json, inventory.json.
LIVE: en una integración real este módulo encapsularía clientes de OMS/ERP
(Shopify, VTEX, Magento, SAP), APIs de carriers (BlueExpress, Chilexpress,
FedEx) para etiquetas y tracking, y sistemas de inventario en tiempo real.
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


def get_order(order_id: str, data_dir: str) -> dict:
    orders = _load_json(Path(data_dir) / "orders.json", [])
    for o in orders:
        if o.get("id") == order_id:
            return o
    if orders:
        logger.info("order_id=%s no encontrado; fallback al primero.", order_id)
        return orders[0]
    return {"id": order_id, "estado": "no_encontrado"}


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "return_policy.json", {})


def get_inventory(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "inventory.json", {})


def stock_disponible(sku: str, data_dir: str) -> int:
    inv = get_inventory(data_dir)
    return int(inv.get(sku, {}).get("stock_disponible", 0))
