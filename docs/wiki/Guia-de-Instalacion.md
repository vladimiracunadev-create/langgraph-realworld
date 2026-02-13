# Guía de Instalación 🚀

Siga estos pasos para levantar el entorno de **LangGraph Real-World** en su máquina local de forma rápida y segura.

---

## 🐳 Vía Docker (Recomendado)

La forma más sencilla de ejecutar los casos es utilizando Docker Compose:

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
    cd langgraph-realworld
    ```
2.  **Configurar Entorno**:
    Cree un archivo `.env` basado en el `.env.example`.
3.  **Lanzar Entorno**:
    ```bash
    docker compose up --build
    ```

---

## 🎮 Modalidades de Ejecución

1.  **Modo Desarrollador**: `python cases/09-backend/src/api.py`.
2.  **Modo Hub CLI**: `python hub.py serve 09`.
3.  **Modo Docker Compose**: `make up` (Recomendado).

Consulte la guía completa en [INSTALL.md](../INSTALL.md).
