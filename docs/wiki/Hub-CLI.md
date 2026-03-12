# Hub CLI

El Hub CLI centraliza operaciones simples sobre los casos del monorepo.

## Qué hace

- listar casos y su estado;
- ejecutar un caso si tiene `case.yml`;
- servir un caso cuando existe comando `serve`.

## Comandos

```bash
python hub.py list
python hub.py doctor
python hub.py serve 01
```

## Estado actual

- caso 01: `Operational (v3.5.0)`
- casos 09, 10 y 13: `Industrial (v3.4.0)`
- resto del catálogo: `Legacy` o `Scaffold`

## Requisito

El Hub depende de `PyYAML` para leer `case.yml`.
