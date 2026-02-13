# Política de Seguridad (SECURITY.md) 🛡️

La seguridad es el pilar fundamental de **LangGraph Realworld**. Este documento define nuestra postura oficial y los protocolos de protección de datos aplicados en todos los casos de uso.

---

## 🛡️ Protocolos de Protección de Datos

### 1. Gestión de Secretos (12-Factor App)
Nunca guardamos claves de APIs (OpenAI, Anthropic, etc.) en el código fuente. Toda la información sensible se gestiona mediante:
- Archivos `.env` (excluidos de Git via `.gitignore`).
- Secretos de Kubernetes (en entornos de producción).
- Inyección de variables en tiempo de ejecución.

### 2. Aislamiento de Procesos (Container Hardening)
Al utilizar Docker y Kubernetes, cada agente se ejecuta en un entorno aislado. Esto previene que un compromiso en un nodo del grafo afecte a la integridad del sistema operativo anfitrión.
- **Imágenes Non-Root**: Todos los procesos corren con el usuario `1000` (no privilegiado).
- **Network Policies**: Restricción de tráfico este-oeste para limitar el movimiento lateral.

### 3. Resiliencia y Control de Flujo
Nuestra arquitectura incluye salvaguardas contra fallos y bucles infinitos:
- **Recursion Limits**: Máximo de 50 pasos por agente.
- **Tenacity Retries**: Estrategias de reintento para evitar fallos por latencia de red en APIs externas.

---

## 📝 Reporte de Vulnerabilidades

Valoramos enormemente el trabajo de los investigadores de seguridad. Si descubre un fallo:

1. **No abra un Issue público**.
2. Contacte directamente a través de un mensaje privado al mantenedor en GitHub.
3. Proporcione una prueba de concepto (PoC) detallada.

Nos comprometemos a:
- Acusar recibo en **menos de 48 horas**.
- Proporcionar un parche de seguridad prioritario según la severidad.

---

## 🚫 Despliegue en Entornos Públicos

**ADVERTENCIA**: Este repositorio está diseñado como una herramienta de demostración y portafolio técnico.

Si planea exponer estos agentes a la web pública, es **obligatorio**:
1. Utilizar **HTTPS/TLS** para todas las comunicaciones de streaming.
2. Implementar una capa de **Autenticación (OIDC/JWT)**, ya que los endpoints `/api/run` son abiertos por defecto.
3. Configurar **Rate Limiting** para protegerse contra ataques de denegación de servicio y costos excesivos de API LLM.
