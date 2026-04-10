"""
integrations.py — Stubs de análisis para Due Diligence (Caso 25).

Todos los stubs retornan datos DEMO sin llamadas externas.
En modo LIVE, reemplazar con llamadas reales a APIs financieras, bases de datos
legales, herramientas de OSINT, etc.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def get_task(task_id: str, data_dir: str) -> Dict[str, Any]:
    """
    Carga la tarea de due diligence desde sample_task.json.

    Args:
        task_id: Identificador de la tarea (p.ej. "DDL-2026-001").
        data_dir: Directorio donde se encuentran los JSON de datos.

    Returns:
        Diccionario con los datos de la tarea. Si no coincide el task_id,
        retorna el primer registro encontrado (comportamiento DEMO).
    """
    task_path = Path(data_dir) / "sample_task.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    # En DEMO, el archivo tiene una sola tarea; en LIVE podría ser una lista
    if isinstance(task, list):
        for t in task:
            if t.get("task_id") == task_id:
                return t
        return task[0] if task else {}

    return task


def financial_analysis_stub(company: str, budget: float) -> Dict[str, Any]:
    """
    Análisis financiero DEMO de la empresa objetivo.

    Args:
        company: Nombre de la empresa a analizar.
        budget: Presupuesto de adquisición en USD.

    Returns:
        Diccionario con métricas financieras estimadas.
    """
    return {
        "company": company,
        "mode": "DEMO",
        "revenue_estimate_usd": budget * 0.6,
        "burn_rate_monthly_usd": budget * 0.04,
        "runway_months": 15,
        "ebitda_margin_pct": -12.5,
        "debt_usd": budget * 0.15,
        "cash_position_usd": budget * 0.08,
        "risk_score": 6.2,  # 1-10, mayor es más riesgo
        "valuation_multiple": 5.0,
        "recommendation": "Revisar métricas de crecimiento antes de proceder",
        "flags": ["burn_rate_elevado", "margen_negativo"],
    }


def legal_analysis_stub(company: str) -> Dict[str, Any]:
    """
    Análisis legal DEMO de la empresa objetivo.

    Args:
        company: Nombre de la empresa a analizar.

    Returns:
        Diccionario con estado legal y riesgos identificados.
    """
    return {
        "company": company,
        "mode": "DEMO",
        "pending_litigations": 2,
        "litigation_details": [
            {"case": "LAB-2024-112", "type": "laboral", "risk": "medio", "amount_usd": 45000},
            {"case": "COM-2025-007", "type": "contractual", "risk": "bajo", "amount_usd": 12000},
        ],
        "ip_status": "parcialmente_registrado",
        "ip_details": {
            "patents": 0,
            "trademarks": 1,
            "copyrights": "pendiente",
        },
        "regulatory_issues": ["falta_certificacion_iso27001"],
        "data_privacy_compliance": "GDPR_parcial",
        "corporate_structure_risk": "bajo",
        "recommendation": "Resolver litigios laborales antes del cierre",
        "flags": ["litigios_pendientes", "ip_incompleta"],
    }


def operational_analysis_stub(company: str) -> Dict[str, Any]:
    """
    Análisis operacional DEMO de la empresa objetivo.

    Args:
        company: Nombre de la empresa a analizar.

    Returns:
        Diccionario con métricas operacionales clave.
    """
    return {
        "company": company,
        "mode": "DEMO",
        "team_size": 28,
        "engineering_team_size": 12,
        "key_person_dependency": True,
        "key_persons": ["CTO", "Lead Architect"],
        "tech_stack": ["Python", "React", "PostgreSQL", "AWS"],
        "tech_debt_level": "medio",  # bajo | medio | alto | crítico
        "tech_debt_details": "Cobertura de tests < 40%, sin CI/CD robusto",
        "product_maturity": "beta",  # mvp | beta | ga | maduro
        "infrastructure_scalability": "limitada",
        "monthly_active_users": 1200,
        "churn_rate_monthly_pct": 5.2,
        "nps_score": 32,
        "recommendation": "Plan de retención para personal clave es crítico",
        "flags": ["dependencia_personas_clave", "deuda_tecnica_media"],
    }


def reputational_analysis_stub(company: str) -> Dict[str, Any]:
    """
    Análisis reputacional DEMO de la empresa objetivo.

    Args:
        company: Nombre de la empresa a analizar.

    Returns:
        Diccionario con métricas de reputación y percepción de marca.
    """
    return {
        "company": company,
        "mode": "DEMO",
        "press_sentiment": "neutral",  # positivo | neutral | negativo | mixto
        "press_articles_analyzed": 47,
        "press_negative_pct": 18.0,
        "glassdoor_rating": 3.4,
        "glassdoor_reviews": 23,
        "glassdoor_ceo_approval_pct": 62,
        "social_mentions_monthly": 340,
        "social_sentiment_score": 0.55,  # -1 a 1
        "brand_awareness_level": "nicho",
        "customer_complaints_public": 8,
        "influencer_endorsements": 2,
        "recommendation": "Reputación aceptable, monitorear comentarios negativos de empleados",
        "flags": ["glassdoor_rating_bajo", "noticias_negativas_recientes"],
    }
