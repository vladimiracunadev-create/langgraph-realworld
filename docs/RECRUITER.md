# 💼 Guía para Recruiters, Hiring Managers y Tech Leads

> [!NOTE]
> **Versión**: 3.7.0 | **Estado**: Industrial | **Audiencia**: Recruiters, Líderes de Ingeniería y Evaluadores de Talento

Bienvenido a **LangGraph Realworld**. Si estás evaluando mi perfil profesional para un rol de *AI Engineer*, *Backend Developer* o *Tech Lead*, este documento es tu hoja de ruta.

## 🚀 El "Elevator Pitch" de este Portafolio

La industria está llena de demos triviales donde un script envía un texto a ChatGPT y devuelve la respuesta. **Este repositorio NO es eso.**

He construido un **Ecosistema de Microservicios Orquestados por IA** nivel corporativo. LangGraph Realworld demuestra cómo controlar modelos de lenguaje erráticos (LLMs), forzarlos a seguir estados de proceso rígidos (StateGraphs) e integrarlos bidireccionalmente con sistemas tradicionales (BBDD, APIs, Consolas), manteniendo toda la arquitectura empaquetada en contenedores Docker y separando limpiamente el Frontend del Backend.

## 🏆 Señales de Seniority (Lo que encontrarás en el código)

En lugar de código aglomerado, este proyecto exhibe patrones de desarrollo industrial reales:

- 🧱 **Clean Architecture & API-First:** Todos los asistentes residen en un Backend desacoplado en **FastAPI**. El Frontend (Vanilla JS) solo consume servicios REST y Streams asíncronos.
- 🐳 **Infraestructura Ágil:** Creación y multi-despliegue mediante **Docker Compose**. Los casos se lanzan como servicios independientes y eficientes.
- 🛡️ **Control de Flujo con LangGraph:** Uso de estructuras `TypedDict` y *Conditional Edges* para evitar que las IA alucinen. Los agentes pueden buscar datos en JSONs, pedir autorizaciones a managers (HITL - Human in the Loop) y abortar misiones si el prompt del usuario atenta contra las reglas de sistema.
- ⚡ **Asincronía y Experiencia de Usuario:** Implementación hardcore de **Server-Sent Events (SSE)** mediante el envío de JSON concatenado (`NDJSON`). Esto permite que el usuario vea reaccionar a la IA y a los sistemas corporativos componente a componente en "tiempo real".
- 🌓 **Modo Resiliente (Dual-Mode):** Los servicios evitan el fallo catastrófico. Si faltan credenciales (`OPENAI_API_KEY`), enrutan a sistemas "Mock" internos para que la operación (o la demo) continúe sirviendo valor al cliente de forma predecible.

## 🎯 Soluciones de Negocio Activas

Explora los 5 microsistemas 100% operativos, listos para correr:

1. **[Atención Omnicanal (Caso 01)](../cases/01-soporte-cliente-omnicanal/README.md):** Arquitectura de Triage de Tickets, balanceo de carga y priorización automática de clientes.
2. **[Soporte SRE Helpdesk (Caso 02)](../cases/02-mesa-ayuda-ti-runbooks/README.md):** Agente de TI con consultas a CMDB (inventario) y ejecución de Runbooks con detención inteligente pre-ejecución.
3. **[Filtro HR Screening (Caso 09)](../cases/09-rrhh-screening-agenda/README.md):** Parseo cognitivo profundo y automatización de agendas.
4. **[Onboarding de Empleados (Caso 10)](../cases/10-onboarding-empleados/README.md):** Sistema de altas, generación de correos corporativos y checklists dinámicos por cargo.
5. **[Analista BI (Caso 13)](../cases/13-bi-analista-datos/README.md):** Motor de *Agentic SQL* inyectando métricas directamente a componentes visuales Graph.JS.

## 🤝 Hablemos

Este repositorio prueba mi capacidad para liderar y construir productos de software impulsados por IA que **funcionan de verdad en el mundo empresarial**. Si estas arquitecturas encajan con los desafíos de tu organización, estaré encantado de conversar.
