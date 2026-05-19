# Hub CLI

## Estado actual (v4.14.0)

- casos 01, 02, 03, 04, 05, 06, 07, 08, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 y 25: `Operativo (v4.14.0)`
- casos 09, 10 y 13: `Industrial (v4.14.0)`
- scaffolds: ninguno (Ola 3 cerrada en v4.14.0)

## Guardrails de seguridad

- `hub.py` solo ejecuta comandos allowlisted definidos en `case.yml`.
- No se permiten `shell=True`, metacaracteres de shell ni `python -c` inline.
- Los comandos deben resolverse dentro del directorio del caso.
- Las variables `env` declaradas en `case.yml` deben estar en formato `UPPER_SNAKE_CASE`.
- La allowlist del Hub privilegia compatibilidad con `python`, `uvicorn` y `docker compose` sin abrir ejecucion arbitraria.
