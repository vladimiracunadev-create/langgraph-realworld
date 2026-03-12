# 🤖 Infraestructura de Agentes y Skills

Este repositorio incluye una capa local de habilidades en `.agents/` para que asistentes automatizados puedan operar el repo con menos improvisación y más consistencia.

---

## Cómo funciona

1. El agente detecta una tarea compatible con un skill.
2. Lee el `SKILL.md` correspondiente.
3. Ejecuta el flujo sugerido respetando el contrato del repositorio.
4. Sincroniza código, documentación y operación según el skill usado.

---

## Skills principales

| Skill | Ruta | Uso |
| :--- | :--- | :--- |
| Actualizar Documentación | `.agents/skills/actualizar_doc/SKILL.md` | Sincronizar README, docs y wiki local |
| Crear Caso LangGraph | `.agents/skills/crear_caso/SKILL.md` | Crear un caso nuevo con backend, demo y Docker |

---

## Principios que siguen los skills

- aislamiento por caso;
- contratos explícitos de estado y configuración;
- operación por Docker y por entorno local cuando sea razonable;
- documentación alineada con la implementación real.

---

## Navegación

- [README.md](../README.md)
- [HUB.md](HUB.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)