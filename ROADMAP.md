# 🛣️ Hoja de Ruta (Roadmap)

> [!NOTE]
> **Versión**: 3.2.0 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores

Esta hoja de ruta presenta objetivos y prioridades generales para el desarrollo de **LangGraph Realworld**.

## Visión
Crear un conjunto de demos y casos de uso reproducibles que sirvan como referencia para proyectos que integran LangGraph y arquitecturas de agentes conversacionales.

## Prioridades a corto plazo (0–3 meses) ✅
- Documentación: mejorar guías de inicio rápido y ejemplos en `cases/*`.
- Tests básicos y CI para asegurar que los demos arranquen en Docker.
- Plantillas y linters para uniformidad (autorouter, ruff, etc.).
- **Milestone 09**: Implementado estándar de resiliencia y observabilidad (Caso 09).

## Prioridades a medio plazo (3–9 meses) 🔧
- **Observabilidad Avanzada**: Integración nativa con **LangSmith** y **OpenTelemetry** para rastreo de trazas de agentes en producción.
- **Capa de Seguridad Empresarial**: Implementación de **OIDC/JWT** para proteger los endpoints de ejecución de los agentes.
- **Multi-Agent Orchestration**: Casos de uso complejos con múltiples grafos colaborando entre sí.
- **Frontend Pro**: Migración de las demos Vanilla JS a un framework moderno (Next.js/React) para mayor escalabilidad.

## Prioridades a largo plazo (9–18 meses) 🚀
- **Agentes Auto-Mejorables**: Implementación de bucles de feedback de aprendizaje por refuerzo (RLHF) para optimizar prompts automáticamente.
- **Infraestructura como Código (IaC)**: Módulos de **Terraform/Pulumi** para desplegar el Hub completo en AWS EKS de forma automatizada.
- **Marketplace de Casos**: Sistema de plugins para que terceros puedan inyectar sus propios grafos de LangGraph de forma dinámica.

## Cómo contribuir
- Abre Issues para discutir nuevas ideas o cambios de prioridad.
- Envía PRs para pequeñas mejoras: documentación, tests, correcciones.
- Para cambios grandes (nuevos casos o arquitectura), crea un Issue con propuesta y plan.

---

*Esta hoja de ruta es orientativa y puede ajustarse según la contribución de la comunidad y requisitos del proyecto.*
