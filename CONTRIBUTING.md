# Guía de Contribución

> [!NOTE]
> **Versión**: 1.2.0 | **Estado**: Activo | **Audiencia**: Colaboradores, Desarrolladores Open Source

Bienvenido al ecosistema de **LangGraph Realworld** — un monorepo modular con 25 casos de uso empresariales construidos con LangGraph y FastAPI.
Para mantener la calidad técnica y la portabilidad, seguimos reglas estrictas de contribución.

---

## Estructura de un caso

Cada caso de uso debe ser **autocontenido** y seguir el patrón de "Agente con Estado".

```text
cases/NN-slug/
├── README.md              # Descripción, flujo Mermaid, stack y estado
├── case.yml               # Configuración para Hub CLI
├── data/                  # Datos de muestra (readonly en Docker)
├── backend/
│   ├── .env.example       # Plantilla de variables (sin secretos reales)
│   ├── requirements.txt   # Dependencias aisladas por caso
│   ├── Dockerfile         # Imagen con usuario non-root y versión pineada
│   ├── compose.yml        # Compose aislado del caso
│   └── src/
│       ├── graph.py       # StateGraph de LangGraph (lógica principal)
│       ├── api.py         # FastAPI — endpoints /health, /ready, /api/run
│       ├── settings.py    # Detección DEMO/LIVE y configuración
│       └── integrations.py# Clientes reales y fallbacks DEMO
└── demo/
    ├── Dockerfile         # nginx:1.27.3-alpine con USER nginx
    ├── nginx.conf         # Con HTTP security headers
    └── index.html         # UI de demostración
```

---

## Estándares de código

El pipeline de CI rechazará cualquier cambio que no cumpla con:

### Python

- **Linter y formatter**: [Ruff](https://docs.astral.sh/ruff/). Ejecuta `ruff check .` antes de subir.
- **Tipado**: adhesión estricta con `typing` y `Annotated`.
- **Tests**: cada caso operativo debe incluir al menos pruebas de API y flujo LangGraph.

### Docker

- Imágenes base pineadas a versión exacta (ej: `python:3.11.10-slim`, `nginx:1.27.3-alpine`).
- Usuario non-root obligatorio (`USER appuser` o `USER nginx`).
- Healthcheck funcional con binario disponible en la imagen.

### Documentación

- Cada caso debe tener su propio `README.md` con un diagrama Mermaid del `StateGraph`.
- El README debe ser honesto sobre el estado actual: `SCAFFOLD`, `OPERATIVO` o `INDUSTRIAL`.

---

## Flujo de trabajo

1. **Fork & Branch** — crea una rama descriptiva:

   ```text
   feature/case-26-legal-advisor
   fix/case-09-healthcheck
   docs/update-security-audit
   ```

2. **Docker First** — asegúrate de que tu caso construye y arranca:

   ```bash
   docker build -t mi-caso:test cases/NN-slug/backend
   docker build -t mi-caso-demo:test cases/NN-slug/demo
   ```

3. **Tests** — agrega o actualiza los tests del caso:

   ```bash
   pytest -q cases/NN-slug/backend/tests
   ```

4. **Pull Request** — describe en el PR:
   - el valor de negocio del caso,
   - el patrón de LangGraph utilizado,
   - cómo probaste DEMO y LIVE.

---

## Modo DEMO / LIVE

Todo caso debe funcionar **en DEMO sin credenciales externas**.
El modo LIVE se activa automáticamente cuando existen credenciales válidas.

```python
# En settings.py
USE_LLM = bool(os.getenv("OPENAI_API_KEY"))
MODE = "LIVE" if USE_LLM else "DEMO"
```

---

## Seguridad

- **Nunca incluyas secretos** en commits. El hook de `detect-secrets` bloqueará cualquier intento de subir claves de API.
- Usa `.env.example` con valores vacíos o placeholders.
- Los puertos en `docker-compose.yml` deben usar `127.0.0.1:PORT:PORT`.
- Si encuentras una vulnerabilidad, consulta [SECURITY.md](SECURITY.md).

---

## Convenciones de puerto

| Caso | Puerto backend | Puerto demo |
|:---|:---:|:---:|
| Portal raíz | 8080 | — |
| Caso NN | `8000 + NN` | 80 (interno) |

---

> [!IMPORTANT]
> **Calidad sobre cantidad.** Preferimos casos con grafos bien definidos, manejo de errores robusto, modo DEMO funcional y documentación honesta sobre el estado real.
