# Contribuir

Este repo es un **monorepo** de demos (25 casos). Cada caso debe ser **autocontenible**.

Reglas prácticas:
- Cada caso vive en `cases/NN-slug/`.
- Si el caso tiene backend, debe tener:
  - `backend/Dockerfile`
  - `backend/requirements.txt` (o equivalente para otro runtime)
  - `backend/src/` (código)
- Todos los demos deben poder ejecutarse vía Docker.

Recomendado:
- Usa `ruff` para Python.
- Agrega tests cuando el caso pase de scaffold a “implementado”.
