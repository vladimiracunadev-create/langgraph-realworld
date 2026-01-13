# LangGraph – 25 casos del mundo real (repo de demos)

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)

Repositorio de portafolio con **25 escenarios reales** donde **LangGraph** brilla: flujos con **estado**, **rutas condicionales**, **tools**, **memoria**, **checkpoints** y (opcional) **observabilidad**.

**TL;DR (30s):**
- ✅ **Caso 09** completo: **FastAPI + LangGraph** + **UI con streaming** en tiempo real.
- 🧩 **Casos 01–08 y 10–25**: scaffold + UI demo para completar lógica real.
- 🎯 Enfoque portafolio: estructura repetible + CI + demos navegables.

---

## ✅ Estado del repo
- ✅ **Caso 09 (RR.HH. Screening + Agenda)**: implementado (backend + UI streaming).
- 🧩 Casos 01–08 y 10–25: scaffold + demo UI (plantilla).

---

## 🧭 Índice de casos (resumen rápido)

| Caso | Nombre | Estado |
|------|--------|--------|
| 09 | RR.HH. Screening + Agenda | ✅ Implementado |
| 01–08 | Varios | 🧩 Scaffold |
| 10–25 | Varios | 🧩 Scaffold |

---

## 🗂️ Estructura
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

