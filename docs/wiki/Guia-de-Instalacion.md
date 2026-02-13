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

## 🐍 Vía Python Local

Si prefiere ejecutar el código directamente:

1.  **Crear venv**: `python -m venv venv`
2.  **Activar venv**: `source venv/bin/activate` (o `venv\Scripts\activate` en Windows)
3.  **Instalar dependencias**: `pip install -r requirements.txt`

Para más detalles sobre la configuración, consulte [INSTALL.md](../INSTALL.md).
