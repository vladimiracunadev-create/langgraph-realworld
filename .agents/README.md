# Agentes operativos — `.agents/`

Esta carpeta contiene la configuración de **Skills** (habilidades) y **Workflows** (flujos de trabajo)
utilizados por los asistentes de IA para operar este repositorio de manera industrial.

---

## Estructura

```text
.agents/
├── skills/
│   ├── crear_caso/        # Crear o elevar un caso LangGraph
│   │   ├── SKILL.md       # Instrucciones detalladas del skill
│   │   └── no_aplica.md   # Skill alternativo para mejorar casos existentes
│   ├── validar_caso/      # Auditar y validar un caso existente
│   │   └── SKILL.md
│   └── actualizar_doc/    # Sincronizar documentación del repositorio
│       └── SKILL.md
└── workflows/
    └── crear_caso.md      # Guía paso a paso para crear un caso desde cero
```

---

## Skills disponibles

| Skill | Cuándo usarlo |
|:---|:---|
| [Crear Caso](skills/crear_caso/SKILL.md) | Crear un caso nuevo o elevar un scaffold a operativo/industrial |
| [Validar Caso](skills/validar_caso/SKILL.md) | Auditar que un caso está realmente operativo antes de marcarlo como tal |
| [Actualizar Doc](skills/actualizar_doc/SKILL.md) | Sincronizar toda la documentación del repo a una nueva versión |

---

## Principios de operación

1. **La evidencia manda** — no declarar un caso como completo sin verificar estructura, endpoints, Docker y tests.
2. **No romper casos existentes** — toda modificación debe respetar los casos 01, 02, 09, 10 y 13 como referencia.
3. **Modo híbrido obligatorio** — todo caso debe funcionar en DEMO sin credenciales externas.
4. **Documentación honesta** — el estado en el README debe reflejar la realidad técnica, no la intención.

---

> Para una explicación detallada de cómo funciona esta infraestructura y cómo extenderla,
> consulta [docs/AGENTS_AND_SKILLS.md](../docs/AGENTS_AND_SKILLS.md).
