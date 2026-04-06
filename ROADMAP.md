# Hoja de Ruta

> [!NOTE]
> **Versión**: 3.9.0 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores

Resumen de prioridades del repositorio tras consolidar los casos 01, 02, 09, 10 y 13 como referencias operativas
y completar la auditoría de seguridad por 8 capas (v3.9.0).

---

## Estado actual

| Área | Estado |
|:---|:---|
| Casos operativos (01, 02, 09, 10, 13) | Completos con backend real, DEMO/LIVE y CI |
| Auditoría de seguridad por 8 capas | Completada en v3.9.0 |
| HTTP security headers (25 demos) | Implementados |
| Puertos ligados a `127.0.0.1` | Implementado |
| Imágenes Docker pineadas | Implementado |
| Grype scan en CI | Implementado |
| Dependabot | Configurado |
| Detección Trojan Source (bidi) | Implementado en CI |
| Hub CLI y documentación | Sincronizados |
| READMEs scaffold (20 casos) | Actualizados con Mermaid y stack técnico |

---

## Próximos focos

### Corto plazo

- Perfil de reverse proxy/TLS opinionado para demos públicas (nginx + Let's Encrypt).
- Adoptar `pip-compile` (pip-tools) o Poetry para lock files deterministas por caso.
- Activar escaneo histórico de secretos con `detect-secrets --scan` en modo schedule.
- Extender `grype` a modo `fail-build: true` cuando se detecten CVEs críticos en producción.

### Mediano plazo

- Observabilidad más profunda con LangSmith u OpenTelemetry para trazas distribuidas.
- Autenticación más robusta (OAuth2 / OIDC) para casos expuestos de forma persistente.
- Más casos con backend real: candidatos prioritarios son 03 (SRE), 19 (DevEx) y 25 (Multi-agente).
- Dashboards de métricas por caso (latencia, errores, modo DEMO/LIVE).

### Largo plazo

- Despliegues maduros en Kubernetes con `NetworkPolicy` y `SecurityContext` completos.
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud.
- Catálogo de casos con criterios explícitos de madurez, seguridad y valor de negocio.
- Integración con un secret manager externo (Vault, AWS Secrets Manager) para demos persistentes.

---

## Criterios de madurez por nivel

```text
SCAFFOLD → demo estática + README con Mermaid
       ↓
OPERATIVO → backend real + DEMO/LIVE + Docker + tests básicos + docs
       ↓
INDUSTRIAL → streaming + observabilidad + hardening + docs operativas completas
```
