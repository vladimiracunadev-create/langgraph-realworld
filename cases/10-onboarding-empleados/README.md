# 🚀 Caso 10: Onboarding de Empleados (Industrial v3.4.0)

> [!IMPORTANT]
> **Estado**: Industrial | **Versión**: 3.4.0 | **Referencia**: Flujo empresarial y RBAC

Caso de referencia para onboarding con clasificación por rol, aprovisionamiento e integraciones híbridas.

## Qué demuestra

- ramas de negocio por tipo de empleado;
- checklist y notificaciones por flujo;
- integración híbrida demo/live;
- backend FastAPI con streaming del estado;
- separación entre API, grafo, settings e integraciones.

## Implementación actual

- estado tipado con `TypedDict`;
- `MemorySaver` como checkpointer actual;
- endpoints `/health`, `/ready`, `/api/run` y `/api/stream`.

## Ejecución rápida

### Docker

```bash
docker compose up --build case10
```

### Local

```bash
cd cases/10-onboarding-empleados/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --port 8010
```