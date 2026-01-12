# LangGraph – 25 casos del mundo real (repo de demos)

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)

Este repositorio agrupa **25 escenarios reales** donde **LangGraph** calza muy bien (flujos con estado, rutas condicionales, herramientas, memoria, checkpoints y observabilidad).

## Estado del repo

- ✅ **Caso 09 (RR.HH. Screening + Agenda)**: implementado con backend **FastAPI + LangGraph** y UI web con **streaming** (tiempo real).
- 🧩 Casos 01–08 y 10–25: **scaffold + demo UI** (plantilla) para que completes la lógica real de cada caso.

> Los demos en GitHub Pages funcionan como UI estática.  
> Para ver “tiempo real” en el Caso 09 debes correr el backend localmente (o con Docker).

## Estructura

- Cada caso vive en: `cases/<NN>-<slug>/`
- Índice moderno: `indexado.html` (en la raíz)
- Caso 09 completo:
  - `cases/09-rrhh-screening-agenda/backend/` (FastAPI + LangGraph)
  - `cases/09-rrhh-screening-agenda/data/` (datos simulados)
  - `cases/09-rrhh-screening-agenda/demo/` (UI estática que apunta a `localhost:8009`)

## Quickstart (Docker)

Requisitos: Docker Desktop (o Docker Engine + Compose)

```bash
docker compose up --build
