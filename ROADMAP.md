# Hoja de Ruta

> [!NOTE]
> **Versión**: 4.0.0 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores

Resumen de prioridades del repositorio tras completar la hoja de ruta de corto y mediano plazo (v4.0.0).

---

## Estado actual

| Área | Estado |
|:---|:---|
| Casos operativos (01, 02, 03, 09, 10, 13, 19, 25) | Completos con backend real, DEMO/LIVE y CI |
| Auditoría de seguridad por 8 capas | Completada en v3.9.0 |
| Nginx reverse proxy + TLS (self-signed dev / real cert prod) | Implementado en v4.0.0 |
| pip-compile lock files deterministas | Implementado en v4.0.0 |
| Grype `fail-build: true` + `.grype.yaml` | Implementado en v4.0.0 |
| detect-secrets full-scan + git history | Implementado en v4.0.0 |
| Logging JSON estructurado en 8 backends | Estandarizado en v4.0.0 |
| OAuth2/OIDC opt-in (USE_OAUTH2) | Implementado en v4.0.0 |
| Endpoint `/metrics` en todos los backends | Implementado en v4.0.0 |
| LangSmith opt-in (LANGCHAIN_TRACING_V2) | Disponible en v4.0.0 |
| HTTP security headers (25 demos) | Implementados |
| Puertos ligados a `127.0.0.1` | Implementado |
| Imágenes Docker pineadas | Implementado |
| Dependabot | Configurado |
| Detección Trojan Source (bidi) | Implementado en CI |
| Hub CLI y documentación | Sincronizados |
| READMEs scaffold (17 casos restantes) | Con Mermaid y stack técnico |

---

## Próximos focos

### Corto plazo (completado en v4.0.0)

- ~~Perfil de reverse proxy/TLS opinionado para demos públicas.~~ ✅
- ~~Adoptar `pip-compile` para lock files deterministas por caso.~~ ✅
- ~~Activar escaneo histórico de secretos con `detect-secrets --scan`.~~ ✅
- ~~Extender `grype` a modo `fail-build: true` para CVEs críticos.~~ ✅

### Mediano plazo (completado en v4.0.0)

- ~~Observabilidad con LangSmith (opt-in automático vía env vars).~~ ✅
- ~~Autenticación OAuth2/OIDC opt-in para casos expuestos.~~ ✅
- ~~Más casos con backend real: 03 (SRE), 19 (DevEx), 25 (Multi-agente).~~ ✅
- ~~Endpoint `/metrics` por caso con latencia, errores y modo DEMO/LIVE.~~ ✅

### Largo plazo

- Despliegues maduros en Kubernetes con `NetworkPolicy` y `SecurityContext` completos.
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud.
- Catálogo de casos con criterios explícitos de madurez, seguridad y valor de negocio.
- Integración con un secret manager externo (Vault, AWS Secrets Manager) para demos persistentes.
- Elevar casos adicionales a OPERATIVO: candidatos 04 (SOC), 05 (Documentos), 17 (Legal).
- OpenTelemetry para trazas distribuidas entre servicios (más allá de LangSmith).

---

## Criterios de madurez por nivel

```text
SCAFFOLD → demo estática + README con Mermaid
       ↓
OPERATIVO → backend real + DEMO/LIVE + Docker + tests básicos + docs
       ↓
INDUSTRIAL → streaming + observabilidad + hardening + docs operativas completas
```
