# 🛠️ Especificaciones Técnicas

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Industrial | **Audiencia**: Seniors, DevOps

Este documento resume el stack real del repositorio y delimita qué significa hoy “industrial” dentro de este portafolio.

---

## Stack Principal

### Backend

- Python 3.11+
- FastAPI
- LangGraph
- `tenacity` en casos que modelan integraciones con reintentos
- SQLite para datos de dominio y casos demo

### Frontend

- HTML, CSS y JavaScript vanilla
- Chart.js en el caso 13
- Mermaid en documentación técnica

### Calidad

- Ruff para lint y formato
- Pytest donde el caso ya tiene cobertura mínima
- GitHub Actions para CI y scanning de seguridad

---

## Contrato de Salud

Los casos industriales deben exponer o aspirar a exponer:

- `GET /health`
- `GET /ready`
- un flujo de arranque documentado
- una vía reproducible para demo local o Docker

---

## Contrato de Estado

El repositorio usa hoy:

- `TypedDict` para contratos de estado en LangGraph.
- `MemorySaver` en los casos 09 y 10.
- SQLite en el caso 13 como base de datos del dominio BI.

No se documenta como realidad actual el uso generalizado de Pydantic ni de `SqliteSaver` para todos los casos industriales.

---

## Contrato de Resiliencia

Para considerar un caso “industrial” dentro de este repositorio, buscamos:

1. manejo explícito de errores;
2. rutas demo y live claras;
3. validación operativa por health/readiness, tests o compile checks;
4. documentación suficiente para reproducir el caso.

---

## Matriz de Capacidades

| Capacidad | Caso 09 | Caso 10 | Caso 13 |
| :--- | :---: | :---: | :---: |
| FastAPI real | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ |
| Estado tipado | ✅ | ✅ | ✅ |
| Checkpointer en memoria | ✅ | ✅ | ❌ |
| Base SQLite de dominio | ❌ | ❌ | ✅ |
| UI con gráficos | ❌ | ❌ | ✅ |
| Docker backend | ✅ | ✅ | ✅ |
| README operativo | ✅ | ✅ | ✅ |
| Tests mínimos | ✅ | ✅ | ✅ |

---

## Navegación

- [README.md](../README.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [INSTALL.md](INSTALL.md)
- [REQUIREMENTS.md](REQUIREMENTS.md)