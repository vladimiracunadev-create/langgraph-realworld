# Requisitos del Sistema

> [!NOTE]
> **Version**: 3.8.0 | **Estado**: Estable | **Audiencia**: Infraestructura, DevOps, Reclutadores

## Requisitos minimos

- Git
- Python 3.11+
- `pip`
- Docker Desktop o Docker Engine recomendado

## Requisitos para trabajo con APIs reales

- Credenciales por caso segun su `.env.example`
- Un equipo confiable si vas a usar `localStorage` del portal
- Preferencia por variables de entorno o secret manager para credenciales reales

## Requisitos para exposicion externa responsable

Si algun backend va a salir de `localhost`, agrega como minimo:

- `DEMO_AUTH_TOKEN`
- `RATE_LIMIT_RPM`
- TLS y reverse proxy
- logging y observabilidad basica

Este repositorio no asume esos componentes por defecto porque prioriza exploracion local y demos reproducibles.
