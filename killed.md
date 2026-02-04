# Security Policy (Killed.md)

Este documento detalla las medidas de seguridad y políticas aplicadas al monorepo `langgraph-realworld`.

## Políticas de Ejecución
- **Tool Allowlist**: Solo se permite la ejecución de herramientas definidas en el `case.yml`.
- **Red Aislada**: Los contenedores Docker no tienen acceso a la red externa por defecto (solo vía proxies controlados o si el caso lo requiere explícitamente).
- **No-Root**: Todos los contenedores deben correr con usuarios no privilegiados.

## Guardrails de Aplicación
- **Sanitización de Inputs**: Todos los parámetros pasados vía `hub.py --input` son validados para prevenir Command Injection.
- **Prompt Injection**: Los agentes de LangGraph utilizan esquemas de validación de salida (Pydantic) para mitigar manipulaciones de instrucciones.
- **Path Traversal**: El Hub CLI valida que los IDs de los casos no contengan secuencias `../`.

## Infraestructura (K8s)
- **SecurityContext**: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`.
- **ResourceLimits**: Memoria y CPU limitados por caso para prevenir DoS local.
- **NetworkPolicy**: Denegación por defecto de tráfico entrante no autorizado.

## CI/CD
- **Secret Scanning**: GitHub Secret Scanning + `detect-secrets` en pre-commit.
- **Dependency Scan**: Snyk o Dependabot para auditar `requirements.txt`.
- **CodeQL**: Análisis estático de Python activo.

## Logging & Auditoría
- Todos los comandos ejecutados vía `hub.py` son registrados con timestamp e ID de usuario.
