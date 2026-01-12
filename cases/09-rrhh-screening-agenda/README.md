# Caso 09: RR.HH. Screening + Agenda (IMPLEMENTADO)

Flujo:
1) cargar vacante + candidatos (datos simulados),
2) scoring incremental (1 candidato por iteración),
3) shortlist (top N con umbral),
4) agenda entrevistas (slots),
5) “emails” simulados.

## Ejecutar backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env  # opcional
uvicorn src.api:app --reload --port 8009
```

Abre: `http://localhost:8009`

## Datos
- `data/job.json`
- `data/candidates.json`

## Docker (recomendado)

Desde `cases/09-rrhh-screening-agenda/backend`:

```bash
docker compose -f compose.yml up --build
```

Abre: `http://localhost:8009`

## Para volverlo REAL (guía rápida)

Este caso ya trae instaladas las librerías típicas para que lo conviertas en un flujo real:

- Parsing CV: `pypdf`, `pdfminer.six`, `python-docx`
- Upload: `python-multipart`
- Email: `aiosmtplib` (SMTP) y `sendgrid` (API)
- Calendar: Google Calendar API libs
- Reintentos: `tenacity`
- HTTP: `httpx`

### Dónde implementar cada parte

- **Parsing y extracción**: `backend/src/integrations.py`
  - `parse_resume_to_text()`
  - `extract_candidate_signals()`

- **Persistencia / ATS**: `backend/src/integrations.py`
  - `upsert_candidate_in_db()`
  - `update_ats_status()`

- **Calendar + Email**: `backend/src/graph.py` en `schedule_interviews()`
  - ahí está el comentario “TODO REAL” con las funciones a llamar.

- **Subida de CVs (endpoint)**: `backend/src/api.py`
  - `/api/cv/upload` existe como stub (501) con instrucciones.

### Recomendación práctica

Primero haz real el *ingreso de candidatos*:
1) Implementa upload + guardado de archivos.
2) Implementa parsing a texto y extracción de skills.
3) Guarda en una DB real.
Luego recién conectas calendar y email.
