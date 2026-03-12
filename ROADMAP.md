# Hoja de Ruta

> [!NOTE]
> **Versión**: 3.5.0 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores

Resumen de prioridades del repositorio después de consolidar los casos 01, 09, 10 y 13 como referencias operativas del portafolio.

## Estado actual

- Caso 01 listo como referencia operativa de soporte omnicanal y fallback DEMO/LIVE.
- Caso 09 listo como referencia de resiliencia.
- Caso 10 listo como referencia de flujo empresarial.
- Caso 13 listo como referencia de analítica conversacional.
- Hub CLI y documentación sincronizados como capa de operación del monorepo.

## Próximos focos

### Corto plazo

- ampliar cobertura de tests en los casos operativos;
- corregir mojibake o divergencias restantes entre raíz, docs y wiki;
- estandarizar más casos con `case.yml` y arranque reproducible.

### Medio plazo

- observabilidad más profunda con LangSmith u OpenTelemetry;
- autenticación para endpoints expuestos públicamente;
- más casos con backend real, no solo demo estática.

### Largo plazo

- despliegues más maduros en Kubernetes;
- IaC para entornos reproducibles;
- catálogo de casos con criterios más explícitos de madurez.
