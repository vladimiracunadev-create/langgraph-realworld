# Caso 10: Onboarding de Empleados

> [!IMPORTANT]
> **Estado**: `INDUSTRIAL` | **Versión**: 3.9.0 | **Referencia**: Flujo empresarial y RBAC

Agente de onboarding que orquesta el proceso de incorporación de nuevos empleados:
provisionamiento de cuentas, asignación de accesos según rol (RBAC), notificaciones
a equipos y seguimiento del checklist de tareas hasta completar la incorporación.

---

## Integraciones opcionales

| Servicio | Variable | Descripción |
|:---|:---|:---|
| OpenAI | `OPENAI_API_KEY` | Personalización con LLM |
| Google Workspace | `GOOGLE_CREDS_JSON` | Creación de cuentas y calendarios |
| Slack | `SLACK_BOT_TOKEN` | Notificaciones al equipo |
| GitHub | `GITHUB_TOKEN` | Acceso a repositorios |
| AWS | `AWS_*` | Recursos cloud |
| SMTP | `SMTP_*` | Emails de bienvenida |

Funciona en **DEMO** sin ninguna de estas variables.

---

## Controles de seguridad

- Imagen Docker: `python:3.11.10-slim`, usuario `appuser` (non-root).
- `DEMO_AUTH_TOKEN` y `RATE_LIMIT_RPM` opcionales para exposición externa controlada.
- Formulario de APIs en la UI para exportar el `.env` del caso.

---

## Cómo ejecutar

```bash
# Con Docker
docker compose up case10

# En local
cd cases/10-onboarding-empleados/backend
uvicorn src.api:app --reload --port 8010
```

UI del caso: [http://localhost:8010/web/](http://localhost:8010/web/)

---

> [!TIP]
> Ver [SECURITY.md](../../SECURITY.md) para el detalle de los controles de hardening activos en este caso.
