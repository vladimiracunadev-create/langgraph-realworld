# LangGraph – Casos del mundo real (Repo scaffold + demos)

Este repositorio contiene **25 casos** típicos donde LangGraph encaja muy bien (flujos con estado, rutas, herramientas y memoria).

- Cada caso vive en `cases/<NN>-<slug>/`
- La raíz tiene `indexado.html` (moderno) que **indexa** los casos y enlaza a un demo por caso.
- Por desafío/complejidad se implementa completo el **Caso 09 (RR.HH. Screening + Agenda)**, con:
  - datos simulados,
  - backend FastAPI + LangGraph,
  - UI web con **streaming** (en tiempo real) mostrando qué está ocurriendo.

> Nota: Los demos en GitHub Pages funcionan como UI estática.  
> Para ver “tiempo real” de verdad en el Caso 09 necesitas correr el backend localmente.

## Cómo correr el caso 09

1) Entra a `cases/09-rrhh-screening-agenda/backend/`

2) Crea venv e instala:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3) Copia `.env.example` a `.env` (opcional) y ejecuta:
```bash
uvicorn src.api:app --reload --port 8009
```

4) Abre el demo:
- Local (recomendado): `http://localhost:8009`
- UI estática: `cases/09-rrhh-screening-agenda/demo/index.html` (apunta a `http://localhost:8009`)


## Docker por caso + ¿Un YML por repo confunde a GitHub?

No: **GitHub no se confunde** si cada subcarpeta necesita versiones distintas.

- **Docker** encapsula dependencias por caso (runtime, librerías, versiones).
- En **GitHub Actions** (archivos `.github/workflows/*.yml`) puedes:
  - usar un **job por caso** o una **matriz** (como en este repo) para buildear cada caso con su Dockerfile;
  - usar Python/Node/etc con **versiones distintas** por job.
- Lo importante es mantener cada caso **autocontenible**: su `Dockerfile`, `requirements.txt`/`package.json`, y README.

### Cómo ejecutar con Docker (rápido)

- Sitio estático con el index y demos:
```bash
docker compose up --build site
# abre http://localhost:8080
```

- Caso 09 (backend + UI):
```bash
docker compose up --build case09
# abre http://localhost:8009
```

- Ambos:
```bash
docker compose up --build
```

### Instaladores

- Linux/Mac:
```bash
bash scripts/install.sh
```

- Windows PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

## CI/CD (qué hace)

Este repo trae CI en `.github/workflows/ci.yml` que:

1) **Lint + compile** del backend del Caso 09 (ruff + compileall).
2) **Build de Docker** para *cada* `cases/*/demo` y, si existe, `cases/*/backend`.

> Si más adelante quieres “CD” real, se puede extender para **publicar imágenes** a GHCR (GitHub Container Registry)
y crear releases con artefactos.

## Caso 09: “hacerlo real” (sin que yo lo implemente)

En `cases/09-rrhh-screening-agenda/backend/src/integrations.py` dejé **stubs con comentarios efectivos**
para que tú conectes:
- parsing de CVs (PDF/DOCX),
- persistencia/ATS,
- Google Calendar,
- email (SMTP/SendGrid),
- y LLM opcional.

Las librerías ya están en `cases/09-rrhh-screening-agenda/backend/requirements.txt`.
