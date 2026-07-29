# Guia para Recruiters, Hiring Managers y Tech Leads

> [!NOTE]
> **Version**: 4.15.0 | **Estado**: Industrial | **Audiencia**: Recruiters, Lideres de Ingenieria y Evaluadores de Talento

Este repositorio no es solo una coleccion de prompts o demos triviales. Muestra como construir casos de IA aplicada con arquitectura clara, flujos LangGraph, APIs reales, operacion portable y una postura de seguridad compatible con el uso local y la revision tecnica seria.

## Lo que demuestra

- Backend AI-first con FastAPI y LangGraph.
- Casos de negocio operables y no solo maquetas visuales.
- Degradacion DEMO/LIVE pensada para demos, evaluacion tecnica y quickstart.
- Capacidad de endurecer CI/CD, secretos, herramientas y APIs sin romper la experiencia del repo.
- Atencion al detalle documental: README, docs, wiki y Hub CLI alineados.

## Casos que conviene mirar

1. **Caso 01**: soporte omnicanal con routing y fallback DEMO/LIVE.
2. **Caso 02**: agente SRE/Helpdesk con CMDB mock, HITL, suite propia y guardrails de exposicion.
3. **Caso 04**: SOC Triage con router de riesgo, threat intel y SIEM context.
4. **Caso 05**: analisis de documentos legales con clasificacion de riesgo y 7 nodos LangGraph.
5. **Caso 09**: screening y agenda con resiliencia.
6. **Caso 10**: onboarding y RBAC.
7. **Caso 13**: analitica conversacional con SQL endurecido.

## Senales de seniority

- aislamiento por caso sin perder coherencia monorepo;
- contratos operativos reproducibles (`case.yml`, `hub.py`, Docker, pytest);
- seguridad aplicada a un repo de IA sin maximalismo ni humo;
- criterio para priorizar compatibilidad y experiencia de exploracion.
