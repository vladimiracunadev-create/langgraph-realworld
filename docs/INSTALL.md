# 🚀 Guía de Instalación y Despliegue

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Estable | **Audiencia**: Desarrolladores, DevOps

Esta guía explica cómo levantar el repositorio completo y cómo ejecutar por separado los casos industriales 09, 10 y 13.

---

## Requisitos Previos

- Git
- Python 3.11+
- Docker Desktop o Docker Engine recomendado
- `pip` disponible en PATH

Más detalle en [REQUIREMENTS.md](REQUIREMENTS.md).

---

## Opción 1: Docker Compose del repositorio

```bash
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld
docker compose up --build
```

Servicios principales:
- Portal: `http://localhost:8080`
- Caso 09: `http://localhost:8009`
- Caso 10: `http://localhost:8010`
- Caso 13: `http://localhost:8013`

---

## Opción 2: Hub CLI

```bash
pip install -r requirements.txt
python hub.py list
python hub.py serve 13
```

Casos hoy estandarizados para el Hub:
- 09
- 10
- 13

---

## Opción 3: Ejecución local por caso

### Caso 09

```bash
cd cases/09-rrhh-screening-agenda/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8009
```

### Caso 10

```bash
cd cases/10-onboarding-empleados/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8010
```

### Caso 13

```bash
python cases/13-bi-analista-datos/data/init_db.py
cd cases/13-bi-analista-datos/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8013
```

UI del caso 13: `http://localhost:8013/web/`

---

## Variables de Entorno

Cada caso industrial incluye o acepta configuración por `.env`:

- caso 09: `cases/09-rrhh-screening-agenda/backend/.env`
- caso 10: `cases/10-onboarding-empleados/backend/.env`
- caso 13: `cases/13-bi-analista-datos/backend/.env`

La mayoría de las integraciones reales son opcionales; si no existen credenciales, el repositorio cae a modo demo.

---

## Validación Rápida

### Caso 13

```bash
python cases/13-bi-analista-datos/data/init_db.py
python -m compileall cases/13-bi-analista-datos/backend/src -q
pytest -q cases/13-bi-analista-datos/backend/tests
```

### Hub

```bash
python hub.py doctor
```

---

## Problemas Comunes

- `ModuleNotFoundError`: faltan dependencias del caso o del Hub.
- `Docker not in PATH`: el daemon no está activo o Docker Desktop no está iniciado.
- `OPENAI_API_KEY` ausente: el caso sigue funcionando en demo si soporta modo offline.