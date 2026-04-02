# Caso 02: Mesa de Ayuda TI / Runbooks

**Estado:** `INDUSTRIAL` (v3.6.0)

Sistema de respuesta MLOps/SRE automatizado. Diagnóstico y ejecución de runbooks con verificación.

## Arquitectura LangGraph
El caso usa un `StateGraph` centralizado (`HelpdeskState`) con 6 fases clave:
1. `receive_ticket`: Ingesta la solicitud del usuario.
2. `classify_issue`: LLM categoriza el problema en hardware, red, accesos o infra.
3. `select_runbook`: Escoge el set de instrucciones pertinentes.
4. `execute_runbook`: Ejecuta de manera simulada las instrucciones recopilando el log resultante.
5. `validate_resolution`: LLM evalúa los logs versus el ticket de origen y determina si "RESOLVED" o "ESCALATED".
6. `draft_response`: LLM redacta la respuesta final humana en base a la traza SRE.

## Dual Mode (DEMO / LIVE)
Por defecto, el sistema se ejecuta usando **Fallback Mockers** si no encuentra `OPENAI_API_KEY` en `.env`. Los logs, selecciones de runbook, el JSON estático, y las resoluciones corren en "Ruta Protegida".

Al inyectar Key, los nodos activan el LLM (gpt-3.5-turbo), pasando a analizar orgánicamente el prompt del usuario y validando lógicamente los logs de terminal contra el problema para decidir si continuar la cadena o detener el pipeline y escalar.

## Frontend Activo
El frontend simula mediante SSE (NDJSON streaming) cómo una terminal técnica SRE imprime en directo los logs, inyectando pausas falsas para demostración visual UX (Cyberpunk).

## Cómo ejecutar

```bash
cd backend
uvicorn src.api:app --port 8002
```
Abre en tu navegador: [http://localhost:8002/web/](http://localhost:8002/web/)
