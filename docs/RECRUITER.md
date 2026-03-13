# Guía para Recruiters y Hiring Managers

> **Versión**: 3.5.0 | **Estado**: Industrial | **Audiencia**: Recruiters, Hiring Managers, líderes técnicos y evaluadores de portafolio

Este documento resume el repositorio desde una perspectiva de contratación: qué construye, qué evidencia entrega y por qué este portafolio es útil para evaluar capacidad real de diseño, implementación y operación con agentes basados en LangGraph.

## Resumen ejecutivo

**LangGraph Realworld** es un portafolio técnico orientado a casos de negocio, no a demos aisladas. El repositorio reúne flujos empresariales implementados con LangGraph y FastAPI, con documentación operativa, modo DEMO/LIVE y casos que pueden ejecutarse por Docker, Hub CLI o entorno local.

La evidencia más fuerte hoy está en cuatro casos operables:

| Caso | Dominio | Qué demuestra |
| :--- | :--- | :--- |
| **01** | Soporte cliente omnicanal | Triage, priorización, routing, respuesta final y degradación DEMO/LIVE |
| **09** | RR.HH. screening y agenda | Resiliencia, streaming, trazabilidad y backoffice de recruiting |
| **10** | Onboarding de empleados | RBAC, aprovisionamiento, flujos empresariales e integraciones híbridas |
| **13** | Analítica BI conversacional | SQL seguro, visualización, UX de datos y operación reproducible |

## Qué hace valioso este repositorio para evaluación

Este portafolio permite evaluar capacidades que suelen quedar invisibles en repositorios de ejemplo más superficiales:

- diseño de grafos con estado explícito y pasos de negocio legibles;
- separación clara entre API, grafo, configuración, integraciones y frontend local;
- uso de FastAPI como capa real de exposición, no solo notebooks o scripts;
- observabilidad mínima operativa con `/health`, `/ready`, streaming o `trace_id` según el caso;
- estrategia DEMO/LIVE para demostrar producto sin bloquearse por credenciales o dependencias externas;
- documentación transversal pensada para distintos perfiles: técnico, operativo, principiante y recruiter.

## Señales de seniority que sí se pueden verificar

Si estás evaluando experiencia práctica y no solo familiaridad con prompts, este repositorio aporta señales concretas:

| Señal | Evidencia en el repositorio |
| :--- | :--- |
| Arquitectura modular | Casos con backend propio, separación `src/`, assets locales y docs por caso |
| Diseño de agentes orientado a negocio | Flujos de soporte, recruiting, onboarding y analítica con etapas explícitas |
| Enfoque de producto | UIs locales, rutas de operación, documentación por audiencia y portal unificado |
| Robustez operativa | Endpoints de salud, Docker, Hub CLI, fallback DEMO/LIVE y degradación razonable |
| Escalabilidad documental | README raíz, docs técnicas, wiki local y skills para automatizar mantenimiento |

## Ruta rápida de evaluación

Si tienes poco tiempo, esta es la secuencia más eficiente:

1. Lee el [README.md](../README.md) para entender el mapa general y la taxonomía de madurez.
2. Revisa el [Caso 01](../cases/01-soporte-cliente-omnicanal/README.md) para ver una implementación operativa con ruteo, priorización y UI.
3. Revisa el [Caso 09](../cases/09-rrhh-screening-agenda/README.md) si quieres evidencia más cercana a recruiting y resiliencia.
4. Revisa el [Caso 10](../cases/10-onboarding-empleados/README.md) si te interesa evaluar diseño de procesos internos y RBAC.
5. Revisa el [Caso 13](../cases/13-bi-analista-datos/README.md) si quieres una demo clara de analítica agentic con frontend visual.

## Lectura por tipo de vacante

### Backend / Platform / AI Engineer

Prioriza:

- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/TECHNICAL_SPECS.md](TECHNICAL_SPECS.md)
- [cases/01-soporte-cliente-omnicanal/README.md](../cases/01-soporte-cliente-omnicanal/README.md)
- [cases/09-rrhh-screening-agenda/README.md](../cases/09-rrhh-screening-agenda/README.md)

Busca especialmente:

- modelado de estado;
- separación de responsabilidades;
- resiliencia y degradación;
- consistencia entre documentación y ejecución.

### Product Engineer / Full Stack AI

Prioriza:

- [cases/13-bi-analista-datos/README.md](../cases/13-bi-analista-datos/README.md)
- [cases/01-soporte-cliente-omnicanal/README.md](../cases/01-soporte-cliente-omnicanal/README.md)
- `index.html` como portal de entrada del portafolio

Busca especialmente:

- integración backend + UI;
- experiencia demostrable sin depender de infraestructura compleja;
- claridad para convertir una capacidad técnica en una demo evaluable.

### Automation / Internal Tools / Ops AI

Prioriza:

- [cases/10-onboarding-empleados/README.md](../cases/10-onboarding-empleados/README.md)
- [docs/HUB.md](HUB.md)
- [docs/AGENTS_AND_SKILLS.md](AGENTS_AND_SKILLS.md)

Busca especialmente:

- estandarización;
- automatización repetible;
- visión de operación y mantenimiento más allá del prototipo.

## Características distintivas del repositorio

### 1. Portafolio centrado en casos de negocio

Los ejemplos no están construidos alrededor de tareas de laboratorio, sino de procesos reconocibles por empresas: soporte, RR.HH., onboarding, BI, compliance, compras, ventas y automatización interna.

### 2. Evidencia técnica con narrativa entendible

Cada caso importante tiene un README con propósito, estado, endpoints y formas de ejecución. Esto reduce la fricción de evaluación para perfiles no técnicos y, al mismo tiempo, mantiene trazabilidad para perfiles de ingeniería.

### 3. Modo DEMO/LIVE bien planteado

Una de las fortalezas más prácticas del repositorio es que no depende completamente de tener credenciales o entornos externos para demostrar valor. Eso es importante en procesos de selección, demos y revisión asincrónica.

### 4. Madurez documental por capas

El repositorio ya no se apoya en un solo README. Tiene una capa de entrada para principiantes, una capa técnica, una wiki local y documentación operativa por caso.

### 5. Repositorio `agent-aware`

Incluye skills locales en `.agents/` para automatizar tareas como actualización documental, creación de casos y validación. Eso muestra interés por gobernanza, consistencia y trabajo asistido por agentes dentro del mismo repositorio.

## Qué puede afirmar un recruiter con confianza

Después de revisar este repositorio, un recruiter o hiring manager puede afirmar con evidencia que aquí hay experiencia en:

- diseño de aplicaciones agentic con LangGraph;
- construcción de APIs reales con FastAPI;
- traducción de procesos de negocio a flujos técnicos ejecutables;
- documentación orientada a distintas audiencias;
- criterio para demos reproducibles y evaluación asincrónica;
- enfoque de producto y no solo de experimento técnico.

## Cómo validar rápidamente que no es solo documentación

Opciones simples de verificación:

```bash
docker compose up --build
python hub.py list
python hub.py doctor
python hub.py serve 01
```

Servicios destacados:

- Portal: `http://localhost:8080`
- Caso 01: `http://localhost:8001`
- Caso 09: `http://localhost:8009`
- Caso 10: `http://localhost:8010`
- Caso 13: `http://localhost:8013`

## Documentos complementarios

- [README.md](../README.md)
- [docs/BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/TECHNICAL_SPECS.md](TECHNICAL_SPECS.md)
- [docs/HUB.md](HUB.md)
- [docs/AGENTS_AND_SKILLS.md](AGENTS_AND_SKILLS.md)
- [docs/wiki/Home.md](wiki/Home.md)

## Nota editorial

La estructura de esta guía se reforzó tomando como referencia el patrón público del ecosistema de repositorios de [vladimiracunadev-create](https://github.com/vladimiracunadev-create): documentación por audiencia, lectura rápida para evaluación, foco en evidencia demostrable y recorrido sugerido según perfil.
