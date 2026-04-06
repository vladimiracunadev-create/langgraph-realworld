# Hoja de Ruta

> [!NOTE]
> **Version**: 3.8.0 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores

Resumen de prioridades del repositorio despues de consolidar los casos 01, 02, 09, 10 y 13 como referencias operativas del portafolio.

## Estado actual

- Caso 01 listo como referencia operativa de soporte omnicanal y fallback DEMO/LIVE.
- Caso 02 listo como referencia operativa SRE Agentic, con suite propia y job dedicado en CI.
- Caso 09 listo como referencia de resiliencia.
- Caso 10 listo como referencia de flujo empresarial.
- Caso 13 listo como referencia de analitica conversacional con SQL endurecido.
- Hub CLI y documentacion sincronizados como capa de operacion del monorepo.
- Fase 2 aplicada para exposicion externa opcional y documentacion completa alineada.

## Proximos focos

### Corto plazo

- agregar un perfil de reverse proxy/TLS mas opinionado para demos publicas;
- mejorar lockfiles o constraints por caso para auditoria mas determinista;
- explorar escaneo historico de secretos en modo manual/schedule.

### Medio plazo

- observabilidad mas profunda con LangSmith u OpenTelemetry;
- auth mas robusta si algunos casos se exponen de forma persistente;
- mas casos con backend real, no solo demo estatica.

### Largo plazo

- despliegues mas maduros en Kubernetes;
- IaC para entornos reproducibles;
- catalogo de casos con criterios mas explicitos de madurez y seguridad.
