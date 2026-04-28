# Hub CLI

## Estado actual (v4.2.0)

- casos 01, 02, 03, 04, 05, 19 y 25: `Operativo (v4.2.0)`
- casos 09, 10 y 13: `Industrial (v4.2.0)`
- casos 06–08, 11–12, 14–18, 20–24: `Scaffold`

## Guardrails de seguridad

- `hub.py` solo ejecuta comandos allowlisted definidos en `case.yml`.
- No se permiten `shell=True`, metacaracteres de shell ni `python -c` inline.
- Los comandos deben resolverse dentro del directorio del caso.
- Las variables `env` declaradas en `case.yml` deben estar en formato `UPPER_SNAKE_CASE`.
- La allowlist del Hub privilegia compatibilidad con `python`, `uvicorn` y `docker compose` sin abrir ejecucion arbitraria.
