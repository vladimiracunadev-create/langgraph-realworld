# LangGraph – 25 casos del mundo real (repo de demos)

## 🚀 Hub CLI (Novedad)
Este repo incluye un **Hub CLI** estandarizado para gestionar los casos sin romper la estructura original.
```bash
python hub.py list      # Listar casos y su estado
python hub.py doctor    # Verificar entorno
make case-up CASE=09    # Levantar un caso específico
```
> [!NOTE]
> El Hub es opcional. Puedes seguir usando los métodos directos (Docker, CD, etc.) descritos abajo.

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)

Repositorio de portafolio con **25 escenarios reales** donde **LangGraph** brilla: flujos con **estado**, **rutas condicionales**, **tools**, **memoria**, **checkpoints** y (opcional) **observabilidad**.

**TL;DR (30s):**
- ✅ **Caso 09** completo: **FastAPI + LangGraph** + **UI con streaming** en tiempo real.
- 🚧 **Casos 01–08 y 10–25**: scaffold + UI demo para completar lógica real.
- 🧪 **Enfoque portafolio**: estructura repetible + CI + demos navegables.

----

## 🛡️ Seguridad
Este repositorio aplica prácticas modernas de seguridad:
- **Secret Scanning**: Pre-commit hooks (`detect-secrets`) y escaneo en CI.
- **Supply Chain**: Escaneo de dependencias en `requirements.txt`.
- **Infrastructure Hardening**:
  - Contenedores **Non-Root** (usuario 1000/101).
  - Políticas de red (NetworkPolicies) restrictivas.
  - Tags de imagen fijos (no `latest`).
- **Ver más**: Consulta [SECURITY.md](SECURITY.md) y [killed.md](killed.md) para detalles técnicos.

---

## 🚦 Estado del repo
- ✅ **Caso 09 (RR.HH. Screening + Agenda)**: implementado (backend + UI streaming).
- 🚧 Casos 01–08 y 10–25: scaffold + demo UI (plantilla).

---

## 📚 Índice de casos (resumen rápido)

| Caso | Nombre | Estado |
|------|--------|--------|
| 09 | RR.HH. Screening + Agenda | ✅ Implementado |
| 01–08 | Varios | 🚧 Scaffold |
| 10–25 | Varios | 🚧 Scaffold |

---

## 🛠️ Estructura
- Cada caso vive en: `cases/<NN>-<slug>/`
- Índice moderno: `indexado.html` (raíz)
- Caso 09 completo:
  - `cases/09-rrhh-screening-agenda/backend/` (FastAPI + LangGraph)
  - `cases/09-rrhh-screening-agenda/data/` (datos simulados)
  - `cases/09-rrhh-screening-agenda/demo/` (UI estática que apunta a `localhost:8009`)

---

## 🏗️ Arquitectura Caso 09 (alto nivel)

```mermaid
flowchart LR
  UI[UI demo - browser] -->|streaming| API[FastAPI - puerto 8009]
  API --> LG[LangGraph - graph]
  LG --> TL[Tools - reglas - scoring]
  LG --> CK[Checkpoints - memoria]
  API --> OB[Logs - tracing]
```
