# 🚀 Hub CLI

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Estable | **Audiencia**: Desarrolladores, DevOps

El Hub CLI centraliza operaciones simples sobre los casos del monorepo.

## Qué hace hoy

- listar casos y su estado;
- ejecutar entrypoints estandarizados;
- levantar casos con comando `serve` cuando existe `case.yml`.

## Requisitos

```bash
pip install -r requirements.txt
```

## Comandos

```bash
python hub.py list
python hub.py doctor
python hub.py serve 13
python hub.py run 13
```

## Casos estandarizados actualmente

- 09
- 10
- 13