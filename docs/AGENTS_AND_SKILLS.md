# Infraestructura de Agentes y Skills

Este repositorio incluye una capa local de habilidades en `.agents/` para que asistentes automatizados puedan operar el repo con menos improvisacion y mas consistencia.

---

## Como funciona

1. El agente detecta una tarea compatible con un skill.
2. Lee el `SKILL.md` correspondiente.
3. Ejecuta el flujo sugerido respetando el contrato del repositorio.
4. Sincroniza codigo, documentacion, operacion y hardening cuando aplica.

---

## Skills principales

| Skill | Ruta | Uso |
| :--- | :--- | :--- |
| Actualizar Documentacion | `.agents/skills/actualizar_doc/SKILL.md` | Sincronizar README, docs y wiki local |
| Crear Caso LangGraph | `.agents/skills/crear_caso/SKILL.md` | Crear un caso nuevo con backend, demo y Docker |
| Validar Caso LangGraph | `.agents/skills/validar_caso/SKILL.md` | Auditar un caso existente, validar Docker/CI, DEMO/LIVE, Hub, seguridad y docs |

---

## Principios que siguen los skills

- aislamiento por caso;
- contratos explicitos de estado y configuracion;
- operacion por Docker y por entorno local cuando sea razonable;
- documentacion alineada con la implementacion real;
- hardening compatible con demos, quickstart y experiencia de exploracion.
