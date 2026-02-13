# Guía de Instalación y Despliegue (INSTALL) 🚀

Este documento proporciona las instrucciones paso a paso para poner en marcha los agentes de **LangGraph Realworld** en diferentes entornos.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de cumplir con los [Requisitos del Sistema](REQUIREMENTS.md) y tener a mano:
- Una clave de API de OpenAI (u otro proveedor soportado).
- Git instalado.
- Docker Desktop (Recomendado).

---

## 🐳 Opción 1: Docker (Recomendada)

Esta es la forma más rápida y segura de ejecutar los casos sin preocuparse por las dependencias de Python locales.

### 1. Clonar el repositorio
```bash
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Edita el archivo .env y añade tu OPENAI_API_KEY
```

### 3. Levantar un caso específico (Ej: Caso 09)
```bash
make case-up CASE=09
```
*Esto descargará las imágenes, compilará el backend y levantará la UI en `http://localhost:8009`.*

---

## 🐍 Opción 2: Instalación Local (venv)

Si prefieres trabajar directamente con el código sin contenedores:

### 1. Preparar el entorno para un caso
```bash
cd cases/09-rrhh-screening-agenda/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
uvicorn src.api:app --reload --port 8009
```

---

## 🎮 Modalidades de Ejecución

Este sistema está diseñado para ser flexible según el perfil del usuario:

### 1. Modo Desarrollador (Python Pure)
Ideal para debuggear la lógica del grafo o navegar el portal sin Docker.

#### **A. Ejecución del Portal (Front-end Central)**
Este comando levanta el portal en el puerto **8080** para navegar los 25 casos.
```bash
python serve_site.py
```

#### **B. Configuración de IA (LLM vs Mock)**
El Caso 09 permite dos modalidades de backend:

| Modalidad | Script | Requisitos | Uso |
| :--- | :--- | :--- | :--- |
| **Instant Demo (Mock)** | `mock_api.py` | Ninguno | Prueba visual inmediata, sin costo de API. |
| **AI Real (LangGraph)** | `src/api.py` | `OPENAI_API_KEY` | Procesamiento real con agentes e inteligencia artificial. |

**Para configurar el modo AI Real:**
1. Copia `.env.example` a un nuevo archivo `.env`.
2. Edita el `.env` y coloca tu clave en `OPENAI_API_KEY=sk-...`.
3. El archivo `.env` está en el `.gitignore`, por lo que tus claves permanecerán **seguras y ocultas** al subir cambios.

**Ejecución del Backend (Puerto 8009):**
```bash
# Para el demo instantáneo (Sin LLM):
python cases/09-rrhh-screening-agenda/backend/mock_api.py

# Para el modo Inteligencia Artificial (Con LLM):
python cases/09-rrhh-screening-agenda/backend/src/api.py
```

### 2. Modo Estándar (Hub CLI)
Usa el punto de entrada unificado del proyecto.
```bash
python hub.py serve 09
```

### 3. Modo Aislado (Docker Standalone)
Para probar un micro-servicio de forma independiente.
```bash
docker build -t caso-09 -f cases/09-rrhh-screening-agenda/backend/Dockerfile .
docker run -p 8009:8009 caso-09
```

### 4. Modo Ecosistema (Docker Compose) - **RECOMENDADO**
Levanta el backend, la UI y el entorno de monitoreo en un solo comando.
```bash
make up  # Levanta el sitio principal y los casos activos
# o manualmente:
docker compose -f cases/09-rrhh-screening-agenda/backend/compose.yml up
```

---

## 🧪 Validación de la Instalación (Smoke Tests)

Para asegurar que todo está configurado correctamente, puedes ejecutar los tests de humo automatizados:

```bash
cd cases/09-rrhh-screening-agenda/backend
docker compose -f compose.smoke.yml up --build --abort-on-container-exit
```

---

## ⚠️ Solución de Problemas Comunes

- **Error: `ModuleNotFoundError`**: Asegúrate de haber activado el entorno virtual (`.venv`) y ejecutado `pip install`.
- **Error: `InsufficientQuotaError`**: Tu clave de OpenAI no tiene saldo o has alcanzado el límite.
- **Error de Docker en Windows**: Asegúrate de que Docker Desktop esté corriendo y que el motor de WSL2 esté habilitado.

---

## 💡 Tips de Rendimiento

- **SQLite**: No requiere configuración, pero asegúrate de que el proceso tenga permisos de escritura en la carpeta `backend/` para los checkpoints.
- **Hot-Reload**: El servidor FastAPI tiene `--reload` activo por defecto en modo local para facilitar el desarrollo.
