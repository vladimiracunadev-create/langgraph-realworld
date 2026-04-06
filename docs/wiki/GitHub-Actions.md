# Referencia de GitHub Actions

Este documento resume los workflows que sostienen integridad, seguridad y sincronizacion documental del repositorio **LangGraph Realworld**.

---

## 1. Integracion Continua (`ci.yml`)

- Trigger: `push` y `pull_request`.
- Permisos por defecto: `contents: read`.
- Controles principales:
  - checks Python del repositorio (`hub.py` y tests raiz);
  - checks Python del caso 02;
  - checks Python del caso 09;
  - checks Python del caso 13;
  - build Docker de los 25 casos;
  - build Docker del sitio raiz.
- Actions pinneadas por commit SHA.

## 2. Seguridad Automatizada (`security.yml`)

- Triggers:
  - `pull_request`;
  - `push` a `main`;
  - `schedule` semanal;
  - `workflow_dispatch`.
- Jobs:
  - `CodeQL` para Python;
  - `detect-secrets` con baseline versionada;
  - `pip-audit` sobre `requirements.txt` raiz y de cada backend.
- Modo de enforcement:
  - PR: dependency audit en modo `soft` para no bloquear contribuciones por hallazgos pendientes;
  - `main` / `schedule` / `workflow_dispatch`: dependency audit en modo `hard`.

## 3. Wiki Sync (`wiki-sync.yml`)

- Trigger: cambios en `docs/wiki/**` sobre `main`.
- Permiso elevado solo donde se necesita: `contents: write`.
- Concurrency group para evitar pushes concurrentes a la wiki.
- Action pinneada por commit SHA.

---

## Criterios de endurecimiento aplicados

- no depender de tags mutables en Actions criticas;
- no dar permisos de escritura globales a workflows de solo lectura;
- mantener un camino contribuible en PR sin desactivar controles;
- dejar el comportamiento documentado para auditores y mantenedores;
- validar el caso 02 en CI como backend real, no solo como build de Docker.
