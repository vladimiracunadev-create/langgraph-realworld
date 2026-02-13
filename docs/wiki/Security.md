# Seguridad y Hardening 🔒

La seguridad es un pilar fundamental en la construcción de agentes de IA. Este documento detalla nuestras políticas y herramientas de protección automática aplicadas en el portafolio.

---

## 🛡️ Herramientas de Seguridad (GitHub Actions)

Contamos con escaneos automáticos en cada cambio de código para asegurar la integridad del ecosistema:

1.  **Trivy**: Escanea vulnerabilidades conocidas tanto en los paquetes de Python (via `requirements.txt`) como en las capas de las imágenes de Docker.
2.  **Detect-Secrets**: Verificación estática para evitar que credenciales de APIs (como OpenAI o AWS) se filtren accidentalmente en los commits.
3.  **SAST**: Análisis estático de código para detectar debilidades estructurales y patrones de ataque comunes.

---

## 🐳 Seguridad en Contenedores

Siguiendo las mejores prácticas de la industria, aplicamos hardening a nivel de infraestructura:

- **Non-privileged User**: Todas nuestras imágenes (ej: Caso 09) corren bajo el usuario `1000:1000` (appuser), limitando el radio de explosión en caso de compromiso.
- **Minimal Images**: Utilizamos versiones `slim` o `alpine` de las imágenes base para reducir la superficie de ataque.

---

## 📚 Referencias
Para un análisis técnico profundo y configuraciones específicas, consulte:
- [SECURITY.md](../../SECURITY.md): Política global de seguridad del repositorio.
- [GitHub Actions](GitHub-Actions): Detalle de los workflows de seguridad automatizados.
