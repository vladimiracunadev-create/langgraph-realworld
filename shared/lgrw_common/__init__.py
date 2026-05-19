"""
lgrw_common — Módulos compartidos entre los 25 backends de LangGraph Realworld.

Extracción introducida en v4.15.0 para eliminar ~6.500 LOC duplicado y centralizar
fixes de seguridad. Antes de esta versión, cada caso tenía su propio auth.py y
settings.py idénticos al 100%.

Módulos:
- lgrw_common.auth     middleware OAuth2/DEMO con JWKS cache + aud/iss obligatorios
- lgrw_common.settings carga de .env, helpers de paths (case_root, data_dir, web_dir)
"""
from __future__ import annotations

__version__ = "4.15.0"
