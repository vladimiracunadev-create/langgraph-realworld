# Guia de Instalacion y Despliegue

> [!NOTE]
> **Version**: 3.9.0 | **Estado**: Estable | **Audiencia**: Desarrolladores, DevOps

Esta guia explica como levantar el repositorio completo y como ejecutar por separado los casos operativos 01, 02, 09, 10 y 13.

---

## Requisitos Previos

- Git
- Python 3.11+
- Docker Desktop o Docker Engine recomendado
- `pip` disponible en PATH

Mas detalle en [REQUIREMENTS.md](REQUIREMENTS.md).

---

## Opcion 1: Docker Compose del repositorio

```bash
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld
docker compose up --build
```

Antes o despues del primer arranque puedes preparar las variables opcionales:

```bash
copy cases\01-soporte-cliente-omnicanal\backend\.env.example cases\01-soporte-cliente-omnicanal\backend\.env
copy cases\02-mesa-ayuda-ti-runbooks\backend\.env.example cases\02-mesa-ayuda-ti-runbooks\backend\.env
copy cases\09-rrhh-screening-agenda\backend\.env.example cases\09-rrhh-screening-agenda\backend\.env
copy cases\10-onboarding-empleados\backend\.env.example cases\10-onboarding-empleados\backend\.env
copy cases\13-bi-analista-datos\backend\.env.example cases\13-bi-analista-datos\backend\.env
```

Tambien puedes abrir el portal y usar el boton `Configurar APIs del portfolio` para completar credenciales opcionales y exportar el `.env` de cada caso operativo.

Servicios principales:

- Portal: `http://localhost:8080`
- Caso 01: `http://localhost:8001`
- Caso 02: `http://localhost:8002`
- Caso 09: `http://localhost:8009`
- Caso 10: `http://localhost:8010`
- Caso 13: `http://localhost:8013`

---

## Opcion 2: Hub CLI

```bash
pip install -r requirements.txt
python hub.py list
python hub.py serve 01
```

Casos hoy estandarizados para el Hub:

- 01
- 02
- 09
- 10
- 13

> [!NOTE]
> `hub.py` ejecuta solo comandos allowlisted declarados en `case.yml`, sin `shell=True`, sin metacaracteres de shell y sin salirse del directorio del caso.

---

## Opcion 3: Ejecucion local por caso

### Caso 01

```bash
cd cases/01-soporte-cliente-omnicanal/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8001
```

UI del caso 01: `http://localhost:8001/web/`

### Caso 02

```bash
cd cases/02-mesa-ayuda-ti-runbooks/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8002
```

UI del caso 02: `http://localhost:8002/web/`

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

Cada caso operativo incluye o acepta configuracion por `.env`:

- caso 01: `cases/01-soporte-cliente-omnicanal/backend/.env`
- caso 02: `cases/02-mesa-ayuda-ti-runbooks/backend/.env`
- caso 09: `cases/09-rrhh-screening-agenda/backend/.env`
- caso 10: `cases/10-onboarding-empleados/backend/.env`
- caso 13: `cases/13-bi-analista-datos/backend/.env`

Flujo recomendado profesional:

1. Copiar `backend/.env.example` a `backend/.env` en cada caso que quieras activar en LIVE.
2. Completar solo las variables que realmente usaras.
3. Si prefieres no tocarlas al instalar, abrir el portal raiz y usar `Configurar APIs del portfolio`.
4. Copiar o descargar el contenido `.env` generado y llevarlo al caso correspondiente.

La mayoria de las integraciones reales son opcionales; si no existen credenciales, el repositorio cae a modo demo.

### Endurecimiento opcional para exposicion externa

Si el backend va a salir de `localhost`, agrega tambien:

```env
DEMO_AUTH_TOKEN=replace-with-a-long-random-token
RATE_LIMIT_RPM=60
TRUST_PROXY_HEADERS=false
```

- `DEMO_AUTH_TOKEN` exige el header `X-Demo-Token` en endpoints operativos.
- `RATE_LIMIT_RPM` aplica rate limiting en memoria por cliente.
- `TRUST_PROXY_HEADERS` solo debe ponerse en `true` si estas detras de un proxy controlado.

> [!IMPORTANT]
> El modo `Guardar localmente` del portal usa `localStorage` del navegador y no cifra valores. Usalo solo en un equipo confiable y borralo despues si trabajaste con credenciales reales.

---

## Validacion Rapida

### Caso 01

```bash
python -m compileall cases/01-soporte-cliente-omnicanal/backend/src -q
python -m pytest -q cases/01-soporte-cliente-omnicanal/backend/tests
```

### Caso 02

```bash
python -m compileall cases/02-mesa-ayuda-ti-runbooks/backend/src cases/02-mesa-ayuda-ti-runbooks/backend/tests -q
python -m pytest -q cases/02-mesa-ayuda-ti-runbooks/backend/tests
```

### Caso 13

```bash
python cases/13-bi-analista-datos/data/init_db.py
python -m compileall cases/13-bi-analista-datos/backend/src -q
python -m pytest -q cases/13-bi-analista-datos/backend/tests
```

### Hub

```bash
python hub.py doctor
```

---

## Problemas Comunes

- `ModuleNotFoundError`: faltan dependencias del caso o del Hub.
- `Docker not in PATH`: el daemon no esta activo o Docker Desktop no esta iniciado.
- `OPENAI_API_KEY` ausente: el caso sigue funcionando en demo si soporta modo offline.
- No quieres completar APIs durante instalacion: usa el portal raiz, abre `Configurar APIs del portfolio` y exporta el `.env` mas tarde.
- Quieres abrir un backend hacia una red externa: activa `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y un proxy/TLS antes de hacerlo.
