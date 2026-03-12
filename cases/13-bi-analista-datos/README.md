# 📊 Caso 13: Analista de Datos BI (Industrial v3.4.0)

> [!IMPORTANT]
> **Estado**: Industrial | **Versión**: 3.4.0 | **Referencia**: SQL seguro + Data Viz

Caso de referencia para analítica conversacional con LangGraph, FastAPI, SQLite y visualización dinámica.

## Qué demuestra

- traducción de preguntas a SQL en modo demo o live;
- ejecución segura de consultas `SELECT`;
- base demo regenerable con `data/init_db.py`;
- gráficos dinámicos en la UI web;
- operación por Docker, Hub o modo local.

## Endpoints principales

- `/health`
- `/ready`
- `/examples`
- `/chat`
- `/web/`

## Ejecución rápida

### Docker

```bash
docker compose up -d --build case13
```

### Hub

```bash
python hub.py serve 13
```

### Local

```bash
python data/init_db.py
cd cases/13-bi-analista-datos/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --port 8013
```

UI: [http://localhost:8013/web/](http://localhost:8013/web/)