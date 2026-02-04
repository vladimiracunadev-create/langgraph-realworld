# Seguridad y Hardening

Este repositorio aplica prácticas "Production-Ready" para asegurar los despliegues de LangGraph.

## 🛡️ Principios Generales
1.  **Least Privilege**: Los contenedores corren como usuarios no-root.
2.  **Immutability**: Tags de imágenes fijos (`v1.0.0`) en despliegues.
3.  **Isolation**: Políticas de red para restringir tráfico lateral y egreso no autorizado.

## 🔒 Hardening de Contenedores
### Dockerfile
Todos los `Dockerfile` (ej. Caso 09) siguen este patrón:

```dockerfile
# Base segura
FROM python:3.11-slim

# Crear usuario sin privilegios
RUN groupadd -r appuser && useradd -r -g appuser appuser

# ... instalación de deps ...

# Cambiar a usuario no-root
USER appuser
```

### Kubernetes SecurityContext
Los despliegues en K8s fuerzan el uso del usuario no-root:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

## 🌐 Network Policies
Por defecto, se recomienda una política **Deny-All** y permitir solo lo necesario.

**Ejemplo (Caso 09):**
- **Ingress**: Permitido desde `hub-gateway`.
- **Egress**:
    - DNS (UDP/TCP 53)
    - Internet (API Calls a OpenAI, LangSmith)
    - *Bloqueado*: Tráfico a red interna privada (10.x, 192.168.x).

## 🔑 Gestión de Secretos
- **Detección**: Pre-commit hooks con `detect-secrets` y escaneo en CI `security.yml` (TruffleHog).
- **Manejo**: `.env.example` proporcionado como plantilla. Nunca subir `.env` reales.

## 📋 Auditoría
Consultar `killed.md` en la raíz del repositorio para decisiones de arquitectura de seguridad históricas.
