# 🛠️ Especificaciones Técnicas

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Industrial | **Audiencia**: Seniors, DevOps

Este documento detalla el stack tecnológico, los estándares de código y los contratos de observabilidad para asegurar la excelencia operativa del proyecto.

---

## 🛠️ Stack Tecnológico

### Backend & AI

- **Python 3.11+**: Lenguaje base para la lógica de agentes y API.
- **LangGraph**: Framework de orquestación para grafos cíclicos con estado.
- **FastAPI**: Servidor ASGI para la exposición de endpoints y streaming NDJSON.
- **Tenacity**: Librería para la implementación de políticas de reintento avanzadas.
- **SQLite**: Motor persistente para el almacenamiento de checkpoints del grafo.

### Frontend & Demo

- **Vanilla JavaScript (ES6+)**: Consumo de streams SSE/NDJSON y renderizado dinámico.
- **Tailwind CSS / Glassmorphism**: Estilizado moderno para dashboards de alta fidelidad.
- **Chart.js**: Visualización de datos dinámica y dashboards de BI.
- **Mermaid.js**: Visualización dinámica de la arquitectura del grafo en tiempo de ejecución.

---

## 🏗️ Principios Arquitectónicos

1.  **Aislamiento por Caso (Modularidad)**: Cada carpeta en `cases/` es un ecosistema independiente para evitar regresiones cruzadas.
2.  **Estado Externo (Idempotencia)**: El estado del agente se persiste en cada paso, permitiendo la recuperación ante reinicios.
3.  **Configuración via Entorno**: Adhesión estricta a *12-Factor App* usando archivos `.env` y variables de entorno del sistema.
4.  **Hibridación (IA-Híbrida)**: Capacidad de operar en modo "Mock" (sin coste) o "Real" (con LLM) sin cambiar una sola línea de código, basándose en la presencia de secretos.

---

## 🧠 Contrato de IA Híbrida

Para garantizar la estabilidad del portafolio, el backend sigue este protocolo de detección:

| Componente | Acción en Modo Mock | Acción en Modo Real |
| :--- | :--- | :--- |
| **Scoring** | Lógica de Python (IF/ELSE) | Análisis semántico (LLM) |
| **Generación** | Fallback determinista | Prompt Engineering dinámico |
| **Dependencia** | Sin coste / Local | Token-based / OpenAI API |

## 🏥 Contrato de Salud y Resiliencia (Observability Standard)

Siguiendo nuestro estándar de observabilidad, cada backend debe implementar:

### 1. Endpoint de Liveness (`/health`)
- **Propósito**: Verificar que el proceso Python/FastAPI esté activo.
- **Respuesta**: 200 OK - `{"status": "ok", "ts": <timestamp>}`.

### 2. Endpoint de Readiness (`/ready`)
- **Propósito**: Confirmar que el grafo de LangGraph ha compilado correctamente y está listo para recibir transacciones.
- **Respuesta**: 200 OK - `{"status": "ready"}` o 503 si falla la compilación.

### 3. Registro de Eventos (Structured Logging)
- **Formato**: JSON.
- **Campos Obligatorios**: `ts`, `level`, `name`, `msg`, `trace_id` (si está disponible).
- **Destino**: `stdout` (para captura por Docker/K8s).

---

## 🔒 Seguridad e Integridad

- **Secret Scanning**: Uso de `detect-secrets` y `TruffleHog` en la fase de CI.
- **Non-Root Images**: Todas las imágenes de Docker corren con un UID no privilegiado (1000).
- **SAST**: Análisis estático constante mediante el pipeline de GitHub Actions.

---

## 🛡️ Contrato de Resiliencia (Resilience Standards)

Para garantizar la robustez, cada agente debe cumplir con:

1.  **Reintentos**: Mínimo 3 intentos para llamadas de red.
2.  **Persistencia**: Uso obligatorio de un `checkpointer` (SQLite/Redis) para threads de larga duración.
3.  **Timeout**: Límite máximo de 60 segundos por paso del grafo (evita bucles infinitos y costos excesivos).
4.  **Error Schema**: Todas las excepciones deben ser capturadas y transformadas en eventos de log estructurados antes de propagarse.

---

## 📅 Contrato de la Fase 3 (Acción y Agendamiento)

Para que un caso sea considerado **Industrial (v3.4.0)**, la fase de acción debe cumplir:

- **Detección de Credenciales**: El sistema debe verificar la presencia de `GOOGLE_CALENDAR_ID` o secretos equivalentes.
- **Hibridación Visual**: Si no hay credenciales, la UI debe mostrar los slots programados de forma simulada pero profesional.
- **Idempotencia**: El agendamiento no debe duplicar eventos en el calendario si se re-ejecuta el mismo `thread_id`.

---

## 📱 Contrato de la Fase 4 (Notificaciones Email/WA)

Para garantizar una comunicación industrial, la fase de notificación debe cumplir:

- **Protocolo Híbrido**: El sistema debe conmutar entre proveedores reales (Twilio, SMTP) y simulaciones visuales profesionales.
- **Privacidad de Datos**: El uso de correos y teléfonos debe estar restringido a la Fase 4 y no persistirse en logs públicos.
- **Resiliencia de Envío**: Uso de reintentos exponenciales para manejar caídas en las pasarelas de mensajería.

---

## 🛡️ Patrones de Resiliencia Avanzada (v3.4.0)

El sistema implementa una arquitectura de "Misión Crítica" basada en:

### 1. Aislamiento de Errores (Error Boundaries)
Cada fase del grafo y cada elemento dentro de un bucle de procesamiento (ej: notificaciones a múltiples candidatos) está envuelto en bloques `try/except` independientes. Un fallo en el envío a un candidato **no detiene** el flujo de los demás.

### 2. Backoff Adaptativo e Industrial
- **Multiplexor de Reintentos**: Uso de `tenacity` con esperas exponenciales (`min=2s`, `max=10s`).
- **ResilienceException**: Tipado de errores para distinguir fallos transitorios de red de errores de lógica de negocio.

### 3. Matriz de Degradación Graciosa

| Componente | Fallo Detectado | Comportamiento en Degradación | Estado UI |
| :--- | :--- | :--- | :--- |
| **IA (Capa 2)** | API Offline / Rate Limit | Uso de Fallback Heurístico (Banco de Preguntas) | `MOCK_INDUSTRIAL` |
| **Agenda (Capa 3)** | Calendar API Error | Reserva Visual Local (sin link externo) | `DEMO_LOCAL` |
| **Email (Capa 4)** | SMTP Failure | Marcado de fallo individual, WA continúa | `FAILED_DEGRADED` |
| **WhatsApp (Capa 4)**| Sandbox/Twilio Error | Marcado de fallo individual, Email continúa | `FAILED_DEGRADED` |

---

---

## 🛠️ Guía de Estilo

- **Ruff**: Linter y formateador oficial. Se debe ejecutar antes de cada commit.
- **CamelCase**: Para nombres de clases y componentes React/Frontend.
- **snake_case**: Para variables, funciones y métodos en Python.
- **Kebab-case**: Para nombres de carpetas y archivos estáticos.

---

## 📊 Matriz de Capacidades Industriales (v3.4.0)

| Característica | Caso 09 (RRHH) | Caso 10 (Onboarding) | Caso 13 (BI Analyst) |
| :--- | :---: | :---: | :---: |
| **Persistencia (SQLite)** | ✅ Full | ✅ Full | ✅ Full |
| **Validación Pydantic** | ✅ Estricta | ✅ Estricta | ✅ Estricta |
| **Streaming NDJSON** | ✅ Real-time | ✅ Real-time | ✅ Real-time |
| **Hibridación (Mock/Real)** | ✅ Dinámica | ✅ Dinámica | ✅ Dinámica |
| **Visualización (Charts)** | ❌ N/A | ❌ N/A | ✅ Chart.js |
| **Integración SQL** | ❌ N/A | ❌ N/A | ✅ Agente SQL |
| **Multicanal (WA/Email)** | ✅ Simulado | ✅ Real/Sim | ❌ N/A |

---

## 🧭 Navegación
- [⬅️ Volver al README](../README.md)
- [🏗️ Arquitectura](ARCHITECTURE.md)
- [🚀 Instalación](INSTALL.md)
- [🛡️ Seguridad](../SECURITY.md)
