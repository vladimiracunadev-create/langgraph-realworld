# Especificaciones Técnicas 🛠️

Detalle del stack tecnológico y los estándares operativos aplicados en este proyecto.

---

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11, LangGraph, FastAPI.
- **Persistencia**: SQLite, Redis (opcional).
- **Frontend**: Vanilla JavaScript, Tailwind CSS, Glassmorphism.
- **DevOps**: GitHub Actions (Wiki Async), Docker, Trivy.

---

## 🏥 Contratos de Observabilidad

Cada servicio implementa los siguientes estándares:
- **Liveness**: `/health` -> `{"status": "ok", "ts": <timestamp>}`.
- **Readiness**: `/ready` -> `{"status": "ready"}`.
- **Logs**: Formato JSON estructurado enviado a `stdout`.

Consulte las especificaciones completas en [TECHNICAL_SPECS.md](../TECHNICAL_SPECS.md).
