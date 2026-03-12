# Especificaciones Técnicas

> [!NOTE]
> **Versión**: 3.5.0 | **Estado**: Industrial | **Audiencia**: Seniors, DevOps

Resumen técnico del stack y de los contratos que hoy sostienen los casos operativos del repositorio.

---

## Stack Base

- Python 3.11+
- FastAPI para APIs HTTP
- LangGraph para orquestación de estados
- Uvicorn para ejecución local
- Docker Compose para levantamiento rápido
- Pytest cuando el caso ya tiene cobertura mínima

---

## Patrones de Implementación

### Estado

- `TypedDict` para contratos de estado en LangGraph.
- acumulación de eventos cuando la UI necesita trazabilidad.
- `MemorySaver` en los casos 01, 09 y 10.
- SQLite en el caso 13 como base de datos del dominio BI.

### APIs

Los casos industriales u operativos deben exponer o aspirar a exponer:

- `GET /health`
- `GET /ready`
- endpoint principal de ejecución
- streaming cuando aporta valor de UX

### Modo DEMO/LIVE

- DEMO por defecto si faltan credenciales o configuración usable.
- LIVE solo cuando la integración real está disponible.
- Nunca romper la experiencia completa solo porque falte una API key.

---

## Casos Operativos

### Caso 01

- soporte omnicanal
- clasificación de intención
- cálculo de prioridad
- ruteo y acciones sugeridas
- respuesta final con fallback DEMO/LIVE

### Caso 09

- scoring y shortlist de candidatos
- agenda y notificaciones
- resiliencia por integración

### Caso 10

- onboarding empresarial
- RBAC e integraciones híbridas
- checklist y notificaciones

### Caso 13

- lenguaje natural a SQL seguro
- ejecución validada
- visualización con Chart.js

---

## Criterios de Madurez

Para considerar un caso “industrial” dentro de este repositorio, buscamos:

1. backend real;
2. estado explícito;
3. arranque reproducible;
4. documentación suficiente para reproducir el caso;
5. validación mínima ejecutable.
