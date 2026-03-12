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
| Validar Caso LangGraph | `.agents/skills/validar_caso/SKILL.md` | Auditar un caso existente, validar Docker/CI, DEMO/LIVE, Hub y docs |

---

## Principios que siguen los skills

- aislamiento por caso;
- contratos explícitos de estado y configuración;
- operación por Docker y por entorno local cuando sea razonable;
- documentación alineada con la implementación real.

## Importancia del Skill de Validación

`Validar Caso LangGraph` cubre una necesidad crítica de este monorepo: aquí no basta con que un caso “parezca listo”. También debe construir en CI, ser coherente con `case.yml`, aparecer correctamente en `hub.py`, degradar a DEMO cuando falten credenciales y no dejar documentación desincronizada.

Este skill es especialmente útil después de crear o promover un caso, cuando hay que confirmar que el repositorio quedó consistente de extremo a extremo y no solo a nivel de código fuente.

---

## Navegación

- [README.md](../README.md)
- [HUB.md](HUB.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
