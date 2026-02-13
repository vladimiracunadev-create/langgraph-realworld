# 🐣 Guía para Principiantes

> [!NOTE]
> **Versión**: 1.1.0 | **Estado**: Estable | **Audiencia**: Nuevos Usuarios, Juniors

Si quieres entender exactamente qué hay dentro de cada "cajón" de este proyecto y cómo empezar con LangGraph, este manual es para ti.

---

## 📂 1. La carpeta `cases/` (El Laboratorio)

Esta es la zona de trabajo principal. Aquí es donde están los 25 casos de uso reales.

* **¿Qué hay dentro?**: Una carpeta por cada caso (ej. `09-rrhh-screening-agenda/`).
* **En cada subcarpeta encontrarás**:
  * `backend/`: El código Python (FastAPI + LangGraph) que hace la magia.
  * `demo/`: Una interfaz web sencilla para interactuar con el agente.
  * `README.md`: Las instrucciones específicas de ese caso.
* **Para el novato**: Cada carpeta es un "miniproyecto" independiente que puedes ejecutar y modificar.

---

## 📂 2. La carpeta `docs/` (La Biblioteca)

Aquí guardamos el conocimiento para que no te pierdas.

* **`ARCHITECTURE.md`**: El mapa técnico de cómo se conectan las piezas.
* **`TECHNICAL_SPECS.md`**: El detalle del stack tecnológico y estándares.
* **`REQUIREMENTS.md`**: Qué necesitas instalado en tu PC para que todo funcione.
* **Para el novato**: Es donde debes mirar si quieres entender "por qué" las cosas se hicieron de cierta manera.

---

## 📂 3. La carpeta `k8s/` (El Despliegue Cloud)

Aquí están los planos para llevar el proyecto a la nube (AWS/Kubernetes).

* **¿Qué hay dentro?**: Archivos YAML que le dicen a Kubernetes cómo levantar los servidores, proteger la red y gestionar recursos.
* **Para el novato**: Piensa en esto como los planos de construcción para un rascacielos. Solo los necesitas cuando vas a desplegar a gran escala.

---

## 📂 4. La carpeta `.github/` (Los Robots Invisibles)

Esta carpeta automatiza el trabajo sucio.

* **Subcarpeta `workflows/`**:
  * `ci.yml`: El robot que revisa que todo funcione (linting, tests) antes de aceptar cambios.
  * `security.yml`: El robot que busca contraseñas expuestas o librerías peligrosas.
* **Para el novato**: Es un equipo de limpieza y seguridad que trabaja 24/7 cada vez que subes código.

---

## 📄 Archivos clave en la raíz

* **`hub.py`**: Tu panel de control CLI. Ejecuta `python hub.py list` para ver todos los casos.
* **`Makefile`**: Atajos rápidos. Escribe `make help` para ver qué botones puedes pulsar.
* **`RECRUITER.md`**: Un resumen ejecutivo si estás mostrando este proyecto en una entrevista.
* **`.env.example`**: Una plantilla de las "llaves" (API Keys) que necesitas configurar.

---

## 💡 Consejos para Empezar

1.  **Explora el Caso 09**: Es el más completo y el mejor ejemplo de lo que puedes lograr.
2.  **Usa el Hub CLI**: Es mucho más fácil que navegar por carpetas manualmente.
3.  **No tengas miedo a Docker**: Es la forma más fácil de que todo funcione a la primera.

**¡Diviértete explorando el mundo de los agentes resilientes!** 🚀🤖
