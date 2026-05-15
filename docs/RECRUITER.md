# Guia para Recruiters, Hiring Managers y Tech Leads

> [!NOTE]
> **Version**: 4.11.0 | **Estado**: Industrial | **Audiencia**: Recruiters, Lideres de Ingenieria y Evaluadores de Talento

Este repositorio no es solo una coleccion de prompts o demos triviales. Muestra como construir 25 casos de IA aplicada con arquitectura clara, **19 backends operativos** con flujos LangGraph, APIs reales, operacion portable y una postura de seguridad compatible con el uso local y la revision tecnica seria.

## Lo que demuestra

- Backend AI-first con FastAPI y LangGraph (19 backends operativos en `cases/01..25`).
- Casos de negocio operables y no solo maquetas visuales.
- Degradacion DEMO/LIVE pensada para demos, evaluacion tecnica y quickstart.
- Capacidad de endurecer CI/CD, secretos, herramientas y APIs sin romper la experiencia del repo.
- Atencion al detalle documental: README, docs, wiki y Hub CLI alineados.
- Tooling moderno: `pip` + `pip-tools` por defecto, `uv` (Astral) opcional como reemplazo ~10x mas rapido.

## Casos que conviene mirar

1. **Caso 01**: soporte omnicanal con routing y fallback DEMO/LIVE.
2. **Caso 02**: agente SRE/Helpdesk con CMDB mock, HITL, suite propia y guardrails de exposicion.
3. **Caso 04**: SOC Triage con router de riesgo, threat intel y SIEM context.
4. **Caso 05**: analisis de documentos legales con clasificacion de riesgo y 7 nodos LangGraph.
5. **Caso 06**: preparacion de auditorias ISO/SOC2/GDPR con cadena de custodia SHA-256 encadenada.
6. **Caso 09**: screening y agenda con resiliencia.
7. **Caso 10**: onboarding y RBAC.
8. **Caso 13**: analitica conversacional con SQL endurecido.
9. **Caso 14**: conciliacion bancaria con matching multi-criterio y deteccion z-score.
10. **Caso 17**: legal intake con 3 especialidades y plantillas.
11. **Caso 21**: documentacion automatica con loop QA condicional (tope 3 iteraciones).

## Senales de seniority

- aislamiento por caso sin perder coherencia monorepo;
- contratos operativos reproducibles (`case.yml`, `hub.py`, Docker, pytest);
- seguridad aplicada a un repo de IA sin maximalismo ni humo;
- criterio para priorizar compatibilidad y experiencia de exploracion.
