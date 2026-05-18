# Changelog

Todos los cambios notables del repositorio se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## v4.13.0 — 2026-05-18

### Agregado

- **Caso 22 — Backoffice Automatización elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 11 nodos: `parsear_solicitud → clasificar_tipo_operacion → verificar_identidad → {permisos_router} → validar_datos_operacion → {completitud_router} → ejecutar_operacion → {ejecucion_router} → confirmar_solicitante | escalar_soporte | rechazar_solicitud → registrar_log_auditoria → producir_resumen`.
  - **3 routers** independientes con resultados terminales distintos:
    - `permisos_router`: `permisos_ok=True → validar_datos_operacion`; si no → `rechazar_solicitud` (estado final `rechazada`).
    - `completitud_router` con loop (`max_iter_completitud=2`): si hay campos faltantes y queda margen → `solicitar_informacion` (autocompletado DEMO determinista por nombre de campo) → reintenta `validar_datos_operacion`.
    - `ejecucion_router`: `resultado.ok=True → confirmar_solicitante` (estado final `exitosa`); si no → `escalar_soporte` (estado final `escalada` a `soporte_email` de `policy.json`).
  - **Cadena de custodia SHA-256** encadenada sobre todos los eventos del pipeline (`hash_n = SHA256(hash_{n-1} | sort_json(evento))` desde `hash_0 = "0"·64`). Mismo patrón que casos 06 (Compliance), 07 (Compras OC) y 15 (E-commerce etiquetas). Cualquier alteración rompe la cadena.
  - Verificación de identidad determinista contra `empleados.json` (4 empleados con matriz de permisos por rol). La operación solicitada debe estar en `operaciones_catalog.json` (4 operaciones: CRM, HRIS, BI) y el empleado debe tener el permiso correspondiente activo.
  - Referencia de ejecución determinista basada en `sha256(sort_json(datos))[:8]` — no depende de `PYTHONHASHSEED`, garantiza idempotencia.
  - Modo DEMO: 4 solicitudes calibradas —
    - `SOL-001` (alta_usuario_crm · brief limpio, permisos OK): `exitosa`, 0 iter.
    - `SOL-002` (modificacion_datos_cliente · falta `nuevo_valor`): `exitosa`, iter ≥ 1.
    - `SOL-003` (baja_empleado_hris · solicitante sin permiso): `rechazada` con motivo `sin_permiso_para_operacion`, no llega a ejecución.
    - `SOL-004` (reporte_ventas_mensual · `falla_simulada=true` en catálogo): `escalada` a `soporte-it@acme.cl`.
  - Modo LIVE: GPT-4o-mini sólo redacta el resumen ejecutivo final (≤ 120 palabras). El pipeline operativo permanece determinista en LIVE.
  - 33 tests (18 graph flow + 15 API) — todos verdes. Cubren: helpers (`_hash_eslabon` cambia con payload y encadena), nodos (parseo / clasificación / identidad OK y sin permiso), 3 routers en sus 2 estados cada uno + loop de completitud, 4 flujos end-to-end por solicitud, eventos completos, integridad de la cadena de hashes, determinismo de la referencia entre dos compilaciones del grafo.
  - Docker: `Dockerfile` non-root + `compose.yml` aislado (puerto 8022). Misma plantilla observable que casos 04/05/06/07/11/12/14/15/18/21 (8 capas de seguridad: rate limit, OAuth2/OIDC opt-in, trace IDs, JSON structured logging, `/metrics`, healthchecks, validación Pydantic, CORS controlado).
  - UI dark theme acento sky (#38bdf8) con selector de solicitud, timeline de eventos, chips de estado/iteraciones/sistema, mensaje al solicitante, hash final de auditoría, panel de resumen, badge DEMO/LIVE.

### Modificado

- **`docker-compose.yml` raíz**: bloques `case18` y `case22` migrados de `demo/` (Nginx estático en :9018/:9022) al backend operativo (`backend/` en :8018/:8022) con volúmenes para `data` y `web`, env `OPENAI_API_KEY` opt-in.
- **Portal raíz (`index.html`)**: cards 18 y 22 actualizadas de `LEGACY` → `OPERATIVO` apuntando a `http://localhost:8018/` y `http://localhost:8022/`; contador `18/25` → `21/25`, pill `18 Casos Activos` → `21 Casos Activos`, banner principal → v4.13.0.
- **README raíz**: contador `20/25` → `21/25` (84%), scaffolds `5` → `4`, badge versión → 4.13.0, lista canónica de operativos incluye caso 22, nueva fila de destacados para caso 22.
- **ROADMAP v4.13.0**: caso 22 movido de scaffold a operativos (21 casos totales). Scaffolds Ola 3 reducidos a 4 (24, 16, 20, 23).

---

## v4.12.0 — 2026-05-18

### Agregado

- **Caso 18 — Marketing de Contenido con QA elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos: `parsear_brief → generar_borrador → revisar_estilo_marca → {estilo_router} → verificar_hechos → {hechos_router} → optimizar_seo → aprobacion_editor → publicar_contenido → producir_resumen`.
  - Dos loops condicionales independientes con topes (`max_iter_estilo=2`, `max_iter_hechos=2`):
    - **Loop tono**: `revisar_estilo_marca → reescribir_tono → revisar_estilo_marca` cuando el score de estilo < 80 o se detectan palabras prohibidas.
    - **Loop hechos**: `verificar_hechos → corregir_hechos → verificar_hechos` cuando hay alucinaciones (claims no respaldados) o hechos obligatorios faltantes.
  - QA estilo determinista: detecta palabras prohibidas (10 entradas en `brand_style.json`: «revolucionario», «#1», «garantizado», etc.), palabras no preferidas (sustituciones tipo «usuarios»→«clientes»), frases por encima de 28 palabras.
  - QA factual determinista: contrasta el borrador contra `fact_sources.json` (6 fuentes autorizadas: PRICING-2026, SUPPORT-MATRIX, ONBOARDING-POLICY, EVENTS-2026, MEDIA-RETENTION, COMPLIANCE-2026). Los `claims_riesgosos` del brief representan afirmaciones sin respaldo que el agente debe retirar; los `hechos_obligatorios` no presentes se inyectan citando la fuente.
  - SEO determinista: densidad de keywords por frase, presencia de H1, presencia de CTA reconocible.
  - Editor: score global ponderado (`hechos·0.5 + estilo·0.3 + seo·0.2`) → riesgo verde/amarillo/rojo y decisión aprobado / aprobado_con_observaciones / rechazado.
  - Modo DEMO: 3 briefs calibrados —
    - `BR-001` (blog_post · Plan Pro · brief limpio): verde, 0 iter. hechos.
    - `BR-002` (email · webinar IA · 2 claims riesgosos): iter. hechos ≥ 1, alucinaciones retiradas.
    - `BR-003` (landing · enterprise legacy · 3 claims riesgosos + tono formal): iter. hechos ≥ 1, riesgo medio/alto.
  - Modo LIVE: GPT-4o-mini sólo redacta el resumen ejecutivo final (≤ 150 palabras, español). El pipeline QA permanece determinista en LIVE.
  - 28 tests (17 graph flow + 11 API) — todos verdes. Cubren: helpers de render por formato, parseo de brief, routers en sus 3 estados, 3 flujos end-to-end por brief, eventos completos, consistencia de métricas, retiro efectivo de alucinaciones, alineación riesgo↔decisión editor.
  - Docker: `Dockerfile` non-root + `compose.yml` aislado (puerto 8018). Misma plantilla observable que casos 04/05/06/07/11/12/14/15/21 (8 capas de seguridad: rate limit, OAuth2/OIDC opt-in, trace IDs, JSON structured logging, `/metrics`, healthchecks, validación Pydantic, CORS controlado).
  - UI dark theme acento púrpura (#a78bfa) con selector de brief, timeline de eventos, KPIs (global · estilo · hechos · seo), chips de riesgo + decisión editor + iteraciones, panel de contenido final renderizado, badge DEMO/LIVE.

### Modificado

- **README raíz**: contador `19/25` → `20/25` (80%), scaffolds `9` → `5`, badge versión → 4.12.0, lista canónica de operativos incluye caso 18, fila de scaffolds reducida (16/20/22/23/24), nueva fila de destacados para caso 18.
- **ROADMAP v4.12.0**: caso 18 movido de scaffold a operativos (20 casos totales). Scaffolds Ola 3 reducidos a 5 (22, 24, 16, 20, 23).

---

## v4.11.0 — 2026-05-15

### Agregado

- **Caso 12 — Psicometría y Evaluaciones elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos: `cargar_especificacion → revisar_items → ensamblar_instrumento → aplicar_evaluacion → analisis_psicometrico → {router validez: valido | requiere_revision}`. Rama `valido` o tope alcanzado → `calibrar_baremos → generar_informe_individual → generar_informe_grupal → END`. Rama `requiere_revision` → `revisar_items_problematicos → analisis_psicometrico` (loop con tope `max_iteraciones_validez = 2`).
  - Router único de validez con loop psicométrico: si α de Cronbach < `umbral_alpha` del instrumento, se re-ingresa al análisis tras excluir ítems problemáticos (dificultad fuera de rango, discriminación item-total baja o DIF entre grupos sobre umbral). Tope evita ciclos infinitos.
  - Helpers psicométricos deterministas, puros en `statistics` + `math` (sin scipy ni pingouin): `alpha_cronbach` (K/(K-1) · (1 − Σvar_item / var_total)), `indice_dificultad` (p para dicotómico, media para Likert), `indice_discriminacion` (Pearson item‑total corregido), `dif_entre_grupos` (|p_grupo_a − p_grupo_b|).
  - Simulador de pilotaje determinista (`integrations.generate_responses`) — modelo Rasch‐like dicotómico (sigmoide sobre habilidad − dificultad + sesgo direccional por grupo) y modelo aditivo Likert 1‑5 con ítems inversos. Dificultad efectiva por ítem combina claridad/representatividad + spread por `crc32` del id (estable entre procesos, no usa `hash()` que está randomizado por PYTHONHASHSEED).
  - Modo DEMO: 3 instrumentos calibrados —
    - `INST-COMP-DIG-01` (Competencias Digitales, dicotómico, banco 12 → objetivo 10, cohorte 40, 2 grupos interno/externo): CD-12 rechazado en revisión por sesgo (0.18 > umbral 0.15).
    - `INST-RAZ-LOG-02` (Razonamiento Lógico, dicotómico, banco 10 → objetivo 8, cohorte 35, 2 modalidades): RL-07 y RL-09 rechazados en revisión; loop psicométrico activado por DIF residual.
    - `INST-ESC-BIE-03` (Bienestar Laboral, Likert 5, banco 8 = objetivo 8, cohorte 50, 3 áreas): 2 ítems inversos (BL-03 estrés, BL-06 desconexión) recodeados antes de generar respuestas.
  - Modo LIVE: GPT-4o-mini redacta el informe ejecutivo grupal con prompt acotado (≤ 220 palabras, español). El análisis psicométrico sigue siendo determinista en LIVE; sólo cambia la redacción del reporte.
  - Calibración baremos por percentiles (P25/P50/P75) sobre puntajes totales. Bandas por defecto: bajo (≤P25), medio_bajo (≤P50), medio_alto (≤P75), alto (>P75). Etiquetas configurables en `policy.json`.
  - 29 tests (19 graph flow + 10 API) — todos verdes. Cubren: helpers (`alpha_cronbach` con datos consistentes vs azarosos, dificultad dicotómica/Likert, discriminación positiva e invertida, DIF con y sin diferencia), router de validez en sus 3 estados, 3 flujos end-to-end por instrumento, baremos ordenados, percentiles 0–100, distribución de bandas, eventos del pipeline completos.
  - Docker: `Dockerfile` non-root + `compose.yml` aislado (puerto 8012). Misma plantilla observable que casos 04/05/06/07/11/14/15 (8 capas de seguridad: rate limit, OAuth2/OIDC opt-in, trace IDs, JSON structured logging, `/metrics`, healthchecks, validación Pydantic, CORS controlado).
  - UI dark theme acento teal (#14b8a6) con selector de instrumento, vista previa por escenario con resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON con dots coloreados por severidad, KPIs (α · ítems activos · evaluados · iteraciones), distribución por banda, tabla de métricas por ítem (dificultad / discriminación / DIF / estado), medias por grupo, tabla de informes individuales (primeros 10) e informe ejecutivo Markdown.
- **`docker-compose.yml` raíz**: reemplazo del bloque legacy `case12` (demo estática Nginx en :9012) por el backend operativo en :8012 con volúmenes para data y web, env `OPENAI_API_KEY` opt-in.
- **Portal raíz (`index.html`)**: card de caso 12 reemplazada de `LEGACY` → `OPERATIVO` apuntando a `http://localhost:8012/web/`; contador `18/25` → `19/25`, scaffolds `7` → `6`, lista canónica de operativos actualizada, banner principal → v4.11.0.
- **ROADMAP v4.11.0**: caso 12 movido de scaffold a operativos (19 casos totales). Scaffolds Ola 3 reducidos a 6.

### Modificado

- `README.md`: badge de versión → 4.11.0, contador de operativos 18 → 19 (76%), caso 12 agregado en tabla de operativos, scaffolds 7 → 6.
- `ROADMAP.md`: versión → 4.11.0, caso 12 marcado como completado en Ola 3, scaffolds 7 → 6.
- `cases/12-psicometria-evaluaciones/case.yml`: `status: scaffold` → `operativo`, `version: 4.0.0` → `4.11.0`, `working_dir: demo` → `backend`, puerto `9012` → `8012`, compose/dockerfile apuntan a `backend/`.
- `cases/12-psicometria-evaluaciones/README.md`: reescrito completo siguiendo el estándar (estado OPERATIVO, flujo Mermaid, tabla de nodos, stack técnico, endpoints, modo DEMO/LIVE, datos DEMO, 3 escenarios, comandos local/Docker/compose, tests).

### Eliminado

- `cases/12-psicometria-evaluaciones/demo/` (legacy nginx + index estático): reemplazado por backend real con LangGraph, FastAPI y UI dinámica.

---

## v4.10.0 — 2026-05-11

### Agregado

- **Caso 15 — E-commerce Postventa elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 11 nodos: `recibir_solicitud → lookup_pedido → clasificar_intencion → {router intención: seguimiento | devolucion | cambio}`. Camino seguimiento → `consultar_tracking`. Camino devolución → `verificar_elegibilidad → {router elegibilidad: elegible → generar_etiqueta | no_elegible → derivar_humano}`. Camino cambio → `verificar_stock → {router stock: disponible → procesar_cambio | agotado → derivar_humano}`. Todos los caminos convergen en `redactar_respuesta → producir_resumen → END`.
  - Tres routers condicionales (intención · elegibilidad · stock) y un nodo de convergencia `derivar_humano` que captura los casos no automatizables (plazo excedido, categoría no devolvible, SKU destino sin stock).
  - Etiqueta de retorno con trazabilidad SHA-256 sobre payload canonicalizado: `etiqueta_id`, `order_id`, `cliente`, `carrier`, `monto_a_reembolsar`, `items_a_retornar`, `fecha_emision`, `max_dias_procesamiento`. Modificar cualquier campo cambia el hash.
  - Política de postventa configurable en `data/return_policy.json`: plazo devolución (30d), plazo cambio (15d), categorías no devolvibles (`ropa_intima`, `alimentos_perecibles`, `personalizado`), carrier por defecto, prefijo de etiqueta, monto mínimo de nota de crédito, días máximos de procesamiento.
  - Inventario en `data/inventory.json` con stock real por SKU para verificación de cambios (5 SKUs DEMO con stock variable).
  - Modo DEMO: 5 escenarios calibrados para los 5 caminos del grafo — `ORD-001` seguimiento con tracking activo en BlueExpress; `ORD-002` devolución dentro de plazo → etiqueta `RET-ORD-002-...` emitida con hash; `ORD-003` devolución vencida (83 días) + categoría ropa_intima bloqueada → 2 razones de rechazo y derivación; `ORD-004` cambio talla con stock disponible (12 unidades) → reserva BlueExpress; `ORD-005` cambio color con SKU destino sin stock (0 unidades) → derivación. Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta la respuesta empática al cliente. La lógica de elegibilidad, stock y emisión de etiqueta sigue siendo determinista para reproducibilidad.
  - 33 tests (23 graph flow + 10 API) — todos verdes. Cubren: helpers (`_label_hash`, `_parse_date`), 3 routers en todas sus ramas, clasificación de intención (input cliente / pedido / default), 5 flujos end-to-end por escenario, override de intención vía input, eventos completos por camino, respuestas y resúmenes no vacíos.
  - `FECHA_HOY` env var permite override determinista de la fecha para tests reproducibles.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8015). Misma plantilla observable que casos 04/05/06/07/11/14 (8 capas de seguridad).
  - UI dark theme acento rosa (#f472b6) con selector de pedido y selector independiente de intención (override), vista previa por escenario con resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON con dot coloreado, KPIs (intención · ítems · monto · derivado), tabla de hitos de tracking, tarjetas de elegibilidad / etiqueta / stock / cambio / derivación, visor de respuesta al cliente y resumen ejecutivo.
- **ROADMAP v4.10.0**: caso 15 movido de scaffold a operativos (18 casos totales). Scaffolds Ola 3 reducidos a 7.
- **Barrido profundo de documentación**: sincronización completa de `docs/` y `docs/wiki/` con la versión 4.10.0 — listas canónicas de operativos (01–11, 13–14, 15, 17, 19, 21, 25), contadores actualizados en badges, sidebar, RECRUITER, ARCHITECTURE, TECHNICAL_SPECS, INSTALL, HUB, COSTS, CLOUD_AWS, UV, BEGINNERS_GUIDE, REQUIREMENTS, Roadmap wiki, Changelog wiki, Home wiki y todos los espejos en español/inglés.

### Modificado

- `README.md`: badge de versión → 4.10.0, contador de operativos 17 → 18 (72%), caso 15 agregado en tabla de operativos, scaffolds 8 → 7.
- `ROADMAP.md`: versión → 4.10.0, caso 15 marcado como completado en Ola 3, scaffolds 8 → 7.
- `index.html` portal: tarjeta de caso 15 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8015/`, contadores y lista de operativos actualizados.
- `docker-compose.yml` raíz: servicio `case15` migrado de demo nginx (puerto 9015) a backend real FastAPI (puerto 8015) con volúmenes `data/` y `web/`.
- Versión bumped a 4.10.0 en README, ROADMAP, CHANGELOG, portal y toda la documentación de `docs/` y `docs/wiki/`.

---

## v4.9.0 — 2026-05-11

### Agregado

- **Caso 11 — Tutor Adaptativo elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos: `cargar_perfil → {router diagnostico: sin → aplicar_diagnostico} → seleccionar_item → presentar_actividad → evaluar_respuesta → {router desempeño: domina | error_conceptual | frustracion} → {aumentar_dificultad | remediar_concepto | reducir_dificultad} → {router continuar: loop | finalizar} → actualizar_perfil → producir_reporte`. Tres routers condicionales y un loop adaptativo con tope `max_items_sesion`.
  - Simulador IRT determinista (per-student seed): `gap = dificultad − habilidad` clasifica entre `correcto` (gap ≤ 0), `error_conceptual` (umbral_error ≤ gap < umbral_frustracion), `frustracion` (gap ≥ umbral_frustracion o racha ≥ N), con zona borderline resuelta por rng con seed.
  - Adaptación dinámica de habilidad en escala 1.0–10.0 con deltas configurables (`delta_aumento = +0.4`, `delta_remediar = −0.3`, `delta_reducir = −0.6`) y clamp a `[habilidad_min, habilidad_max]`.
  - Banco de 15 ítems de fracciones y porcentajes (dificultad 1.5–8.5, 9 conceptos), cada uno con `prompt`, `respuesta_correcta`, `retroalimentacion` y `formato` (explicación / ejemplo / práctica). Selección adaptativa prefiere el formato del estudiante en empates de dificultad.
  - Política de tutoría configurable en `data/tutor_policy.json`: items por sesión, items de diagnóstico, umbrales, deltas, criterio de promoción (`min_aciertos_promocion = 0.6`).
  - Modo DEMO: 3 estudiantes calibrados para ejercitar las 3 vías del router de desempeño — `STU-001` Marta sin diagnóstico (aplica pretest, avance con errores), `STU-002` Diego nivel medio (promociona con 1 remediación), `STU-003` Ana nivel bajo (progresa consolidando fundamentos). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta el reporte ejecutivo para docente / apoderado. El simulador sigue siendo determinista para reproducibilidad pedagógica.
  - 30 tests (22 graph flow + 8 API) — todos verdes. Cubren: helpers (`_clamp`, `_simulate_response` en sus 4 ramas), 3 routers, 7 flujos end-to-end por estudiante (incluyendo diagnóstico opcional, tope de ítems, no-repetición, métricas consistentes, habilidad acotada, reporte no vacío, eventos completos).
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8011). Misma plantilla observable que casos 04/05/06/07/14 (8 capas de seguridad: TraceID, OAuth2 opt-in, rate limit, validación Pydantic, regex en IDs, X-Demo-Token, X-Trace-ID, HSTS implícito via uvicorn).
  - UI dark theme acento índigo (#818cf8) con selector de estudiante, vista previa de perfil + resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON con dot coloreado por resultado, KPIs (ítems, acierto, habilidad final, Δ habilidad), barra de progreso de habilidad, tabla de ítems aplicados con tag de resultado, tarjetas de conceptos dominados / a remediar, recomendación próxima sesión, visor del reporte ejecutivo.
- **ROADMAP v4.9.0**: caso 11 movido de scaffold a operativos (17 casos totales). Scaffolds Ola 3 reducidos a 8.

### Modificado

- `README.md`: badge de versión → 4.9.0, contador de operativos 16 → 17.
- `ROADMAP.md`: versión → 4.9.0, caso 11 marcado como completado en Ola 3, scaffolds 9 → 8.
- `index.html` portal: tarjeta de caso 11 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8011/`, contador de operativos 15 → 16, scaffolds 10 → 9, lista de operativos actualizada con 07 y 11.

---

## v4.8.0 — 2026-05-07

### Agregado

- **Caso 07 — Compras y Abastecimiento elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos: `validar_solicitud → buscar_proveedores → lanzar_rfq → recopilar_cotizaciones → comparar_ofertas → {router politica_compras: dentro_politica | requiere_comite → escalar_comite} → recomendar_proveedor → aprobacion_responsable → generar_orden_compra → producir_resumen`. El router activa el camino con comité cuando el monto supera el umbral configurable (25M CLP), cuando el mejor proveedor no es preferido y supera el umbral menor (5M CLP), o cuando la PR está incompleta.
  - Score multi-criterio determinista 0-100 con pesos configurables (precio 40% / plazo 30% / riesgo proveedor 30%). Cada criterio se calcula con clamp 0-100 sobre presupuesto disponible, plazo máximo (30 días) y riesgo del proveedor (0-1). El score total ordena la comparativa para la recomendación.
  - Trazabilidad SHA-256 sobre payload canonicalizado de la OC: `po_numero`, items, supplier, monto, plazo, condiciones de pago, fecha de emisión y estado de aprobación. Modificar cualquier campo cambia el hash.
  - Catálogo de 9 proveedores homologados en 4 categorías (oficina, hardware, servicios profesionales, ingeniería) con flag `preferido`, score `riesgo` y lead time promedio. Política configurable en `data/procurement_policy.json` (umbrales, pesos, miembros del comité, quorum).
  - Modo DEMO: 3 escenarios calibrados para los 3 caminos del router — `PR-001` insumos oficina ~3M CLP → APROBADA con OC emitida directamente; `PR-002` 25 notebooks ~17M CLP → APROBADA tras comparativa cerrada (~3% diferencia entre top y segundo); `PR-003` estudio ingeniería ~87M CLP → CONDICIONAL escalada a comité con OC en estado PENDIENTE_COMITE. Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta justificación de la recomendación + resumen ejecutivo para el responsable del centro de costo.
  - 25 tests (17 graph flow + 8 API) — todos verdes. Cubren: helpers (score con clamp, hash estable), validación PR, router en sus 4 ramas (preferido/no preferido × monto bajo/alto, PR inválida), 3 flujos end-to-end por escenario, eventos completos, consistencia recomendación↔comparativa, OC con hash y po_numero únicos.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8007). Imagen Python 3.11-slim con curl para healthcheck.
  - UI dark theme acento ámbar (#f59e0b) con selector de PR, vista previa de centro de costo + resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON, KPIs (cotizaciones, monto top, plazo, score), tabla de comparativa con tag preferido/homologado y resaltado del top, tarjetas de recomendación + escalación + aprobación + OC con hash, visor de resumen ejecutivo.
- **`docs/COSTS.md`**: nuevo documento maestro de costos DEMO vs LIVE. Tabla por caso con proveedor, variables `.env`, pricing público y lo que desbloquea. Agrupación por dependencia: DEMO puro (7 casos), solo OpenAI (8 casos ~$5–20/mes), multi-integración enterprise (caso 10), stubs pendientes. Infraestructura transversal (LLM backbone, observabilidad, hosting, secretos, auth). Receta para activar LIVE en 4 pasos. Estimaciones por escenario (lab personal ~$5/mes, demo comercial ~$50/mes, productivo enterprise ~$600–1,200/mes). Enlazado desde README, ROADMAP y READMEs de casos.
- **ROADMAP v4.8.0**: caso 07 movido de scaffold a operativos (16 casos totales). Iniciada Ola 3.

### Modificado

- `README.md`: badge de versión → 4.8.0, contador de operativos 15 → 16, caso 07 movido de scaffold a OPERATIVO en ambas tablas, fila destacada "Compras" agregada, link a `docs/COSTS.md` en sección de documentación técnica, taxonomía actualizada.
- `ROADMAP.md`: versión → 4.8.0, caso 07 marcado como completado en Ola 3, scaffolds 10 → 9.
- `index.html` portal: tarjeta de caso 07 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8007/`.
- `docker-compose.yml` raíz: servicio `case07` cambiado de demo nginx (puerto 9007) a backend real FastAPI (puerto 8007) con volúmenes `data/` y `web/`.

---

## v4.7.0 — 2026-05-05

### Agregado

- **Caso 21 — Documentación Automática elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 9 nodos: `escanear_repositorio → extraer_artefactos → generar_outline → redactar_secciones → qa_precision_tecnica → {router calidad: revisar_secciones | qa_coherencia_global} → publicar_documentacion → producir_resumen`. El router `calidad_seccion_router` cierra un loop con `revisar_secciones → qa_precision_tecnica` con tope de 3 iteraciones (`max_iteraciones_revision` configurable en `quality_rules.json`).
  - Outline adaptativo según tipo de proyecto: plantillas para `api_rest` (overview, instalación, uso, endpoints, modelo, tests, changelog) y `integration` (overview, instalación, endpoints, integraciones, tests, operación). Extensible vía `data/outline_template.json`.
  - Redacción 100% determinista a partir de los artefactos extraídos del repo (endpoints, schemas, funciones públicas, tests, changelog, ratio docstring) — sin red, sin LLM en DEMO.
  - QA por sección con score 0-100 y penalizaciones configurables: endpoint sin doc (8), función sin docstring (4), sin README (15), sin changelog (10), tests fallando (12), cobertura baja <60% (8), sin CI (6). Umbral de aprobación 80, umbrales de riesgo verde ≥90 / amarillo ≥70 / rojo <70.
  - Modo DEMO: 3 escenarios calibrados (`DOC-001` fastapi-orders limpio score ≥90 0 iteraciones, `DOC-002` billing-service con docstrings parciales y test fallando issues detectadas, `DOC-003` legacy-erp-bridge sin README/CI/docstrings 1-3 iteraciones de revisión). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta resumen ejecutivo final.
  - Publicación: documento Markdown completo con todas las secciones + diff (`secciones_agregadas`, `secciones_modificadas`, `secciones_intactas`, `lineas_totales`).
  - 25 tests (15 graph flow + 10 API) — todos verdes. Cubren: render por tipo de sección, router de calidad en sus 3 ramas (loop con pendientes, sin pendientes, agotado), end-to-end por escenario, eventos completos, consistencia de métricas.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8021). Imagen Python 3.11-slim con curl para healthcheck.
  - UI dark theme acento rosa (#f472b6) con selector de repositorio, vista previa de tipo/framework/resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON, KPIs (secciones, iteraciones de revisión, issues, líneas .md), listado de secciones con estado coloreado (aprobada/revisada/pendiente), tarjetas por issue con tipo + sección + ref, visor de Markdown generado y resumen ejecutivo.
- **ROADMAP v4.7.0**: caso 21 movido de scaffold a operativos (15 casos totales). Ola 2 cerrada — siguiente prioridad es Ola 3 (07, 11, 12, 15, 16, 18, 20, 22, 23, 24).

### Modificado

- `README.md`: badge de versión → 4.7.0, contador de operativos 14 → 15, caso 21 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.7.0, caso 21 marcado como completado, scaffolds 11 → 10.
- `index.html` portal: tarjeta de caso 21 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8021/`.
- `docker-compose.yml` raíz: servicio `case21` cambiado de demo nginx (puerto 9021) a backend real FastAPI (puerto 8021) con volúmenes `data/`.

---

## v4.6.0 — 2026-05-05

### Agregado

- **Caso 06 — Compliance & Auditorías elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 8 nodos: `parsear_alcance → mapear_controles → recopilar_evidencias → {router severidad: escalar_responsable | validar_evidencias} → generar_expediente → log_trazabilidad → producir_resumen`. Router condicional ramifica por severidad de faltantes; el camino "alta" pasa por `escalar_responsable` antes de validar.
  - Cadena de custodia SHA-256 encadenada (append-only): cada acción del agente queda registrada con `seq`, `ts` UTC ISO-8601, `accion`, `detalle` canonicalizado, `prev_hash` y `hash`. La primera entrada usa `prev_hash="GENESIS"`. Modificar cualquier `detalle` rompe la cadena en todas las entradas posteriores.
  - 3 marcos regulatorios soportados: ISO 27001:2022 (4 controles A.5.1, A.5.15, A.8.16, A.8.28), SOC 2 Type II (CC6.1, CC7.2, CC8.1, A1.2) y GDPR (Art.30 ROPA, Art.32, Art.33, Art.35 DPIA). Catálogo extensible en `data/marcos.json` con título, fuente (documentacion/iam/siem/git/monitoring/ticketing), owner por email y criticidad alta/media.
  - Score de cumplimiento 0-100: controles completos cuentan 100, parciales 50, sin evidencia 0. Indicador verde/amarillo/rojo según umbrales (verde ≥95 sin sin_evidencia, amarillo ≥75, rojo <75).
  - Validación de evidencias determinista: campos obligatorios, sistemas válidos, antigüedad máxima 365d, alerta a 180d, fechas dentro de período (acepta `YYYY-Qn`, `YYYY-MM` y `YYYY`).
  - Modo DEMO: 3 escenarios calibrados (`AUD-001` ISO limpio score 100 riesgo verde, `AUD-002` SOC 2 con faltantes en CC6.1/CC7.2 escala a IAM y SOC, `AUD-003` GDPR con ROPA Nov-2024 y DPIA Ago-2024 vencidas → evidencias inválidas y escalación al DPO). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta resumen ejecutivo para comité de auditoría.
  - 26 tests (15 graph flow + 11 API) — todos verdes. Cubren: hash chain encadenamiento, periodo bounds, router severidad, end-to-end por escenario, consistencia de métricas y eventos.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8006). Imagen Python 3.11-slim con curl para healthcheck.
  - UI dark theme acento índigo (#818cf8) con selector de auditoría, vista previa de marco/periodo/resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON, KPIs (controles OK/parciales/sin/evidencias inválidas), tabla índice por control con estado coloreado (verde/amarillo/rojo), tarjetas por faltante y por evidencia inválida, panel de escalaciones con cuerpo de email, visor de cadena de custodia con seq/timestamp/acción/hash y resumen ejecutivo.
- **ROADMAP v4.6.0**: caso 06 movido de scaffold a operativos (14 casos totales). Pendientes Ola 2: caso 21 (Documentación Automática).

### Modificado

- `README.md`: badge de versión → 4.6.0, contador de operativos 13 → 14, caso 06 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.6.0, caso 06 marcado como completado, scaffolds 12 → 11.
- `index.html` portal: tarjeta de caso 06 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8006/`.

---

## v4.5.0 — 2026-05-04

### Agregado

- **Caso 14 — Finanzas: Conciliación elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 9 nodos: `normalizar_transacciones → clasificar_transacciones → matching_automatico → detectar_outliers → proponer_ajuste → escalar_auditoria → marcar_partida_en_transito → generar_reporte_cuadre → producir_resumen`. Las 3 ramas de discrepancia se ejecutan en serie y filtran el array `outliers` por su `tipo`, evitando merge de estado por bifurcación.
  - Matching automático multi-criterio con score 1.0/0.7/0.6: exact match (referencia + fecha ±1 día + monto), match amplio (fecha ±3 días + monto), match por contraparte (sin referencia). Tolerancia de monto configurable (`tolerancia_monto_pesos: 1000`).
  - Detección de outliers determinista con z-score sobre histórico del propio escenario (umbral 2.5σ), implementado en Python puro (`math.sqrt`) sin pandas/numpy/scikit-learn — mantiene el caso ligero y consistente con los demás del repo.
  - Clasificación de discrepancias en 3 tipos: (a) `error_contable` con asiento contable sugerido (cuenta origen → cuenta destino, débito/haber, monto absoluto), (b) `posible_fraude` que escala a auditoría interna con nota formal incluyendo motivo, severidad y acción requerida, (c) `partida_en_transito` para diferencias legítimas de timing (cheques emitidos no cobrados, depósitos en cola al cierre).
  - Detección de fraude por señales combinadas: contraparte con keywords offshore (`llc`, `panamá`, `bvi`, `offshore`, `trust`), descripción atípica (`urgente`, `consultoría exterior`), monto mínimo configurable (20M CLP).
  - Indicador de riesgo verde/amarillo/rojo según porcentaje de cuadre, presencia de ajustes y escalaciones.
  - Modo DEMO: 3 escenarios calibrados (`SCN-001` cierre limpio 100% riesgo verde, `SCN-002` 91% con ajustes y partidas en tránsito riesgo amarillo, `SCN-003` 20% con transferencia offshore de 47.8M CLP a "Servicios Globales LLC (Panamá)" riesgo rojo). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta justificación contable formal de cada ajuste y resumen ejecutivo para el controller.
  - Categorías contables predefinidas en `account_mapping.json` (remuneraciones, arriendo, servicios básicos, suministros, equipos, ventas, impuestos, comisiones bancarias, servicios profesionales, transferencias internacionales, otros) con cuenta + centro de costo + keywords de matching.
  - 22 tests (13 graph flow + 9 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8014).
  - UI dark theme con selector de período, vista previa del escenario, badge DEMO/LIVE, timeline streaming NDJSON, KPIs en grilla (totales banco/contable/conciliado/pendiente), tabla de matches con score y criterio, tarjetas por outlier coloreadas según tipo (rojo fraude, amarillo error, verde tránsito), asientos contables sugeridos, notas de escalación a auditoría, reporte de cuadre tipográfico monoespaciado y resumen ejecutivo.
- **ROADMAP v4.5.0**: caso 14 movido de Ola 2 a operativos (13 casos totales). Pendientes Ola 2: casos 06 (Compliance) y 21 (Documentación Automática).

### Modificado

- `README.md`: badge de versión → 4.5.0, contador de operativos 12 → 13, caso 14 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.5.0, caso 14 marcado como completado, scaffolds 13 → 12.
- `docker-compose.yml` raíz: servicio `case14` cambiado de demo nginx (puerto 9014) a backend real FastAPI (puerto 8014) con volúmenes `data/` y `web/`.
- `index.html` portal: tarjeta de caso 14 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8014/`.

---

## v4.4.0 — 2026-05-04

### Agregado

- **Caso 08 — Ventas B2B + CRM elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos y 2 routers condicionales: `investigar_cuenta → calificar_lead → [router score_icp → descartar | personalizar_outreach → seleccionar_canal → simular_envio → monitorear_respuesta → router señal_interes → {escalar_ejecutivo | programar_followup | descartar}] → actualizar_crm → producir_resumen`.
  - Scoring ICP determinista (0-100) ponderando industria prioritaria, tamaño de empresa, modernidad del stack tecnológico, señales de compra activas y noticias recientes; configurable vía `icp.json`.
  - Selección automática de canal y cadencia: C-level → email + LinkedIn (3 toques en días 0/4/8); roles intermedios → email solo (2 toques en días 0/5).
  - Plantillas de outreach por industria (logistics, fintech, media, default) con sustitución de variables `{{company_name}}`, `{{contacto_nombre}}`, `{{benchmark}}`, `{{tech_observado}}`.
  - Asignación de AE por industria + país + menor `deals_activos`, con 4 ejecutivos comerciales en `sales_reps.json`.
  - Estados de CRM finales: `Meeting Scheduled`, `Nurturing`, `Closed Lost`, `Disqualified`. Notas y `next_step` consolidados en cada record.
  - Modo DEMO: 4 cuentas (`ACC-001` Logistics mid-market positiva, `ACC-002` Gaming startup sin respuesta, `ACC-003` Retail tradicional fuera_icp, `ACC-004` Banca enterprise con freeze de vendors negativo) que ejercitan los 4 caminos del pipeline.
  - Modo LIVE: GPT-4o-mini mejora la redacción del mensaje de outreach y genera el resumen ejecutivo si hay credenciales.
  - 23 tests (14 graph flow + 9 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8008).
  - UI dark theme con selector de cuenta, vista previa de empresa/tech/noticias, badge DEMO/LIVE, timeline streaming NDJSON, panel de razones del scoring ICP, mock-up de email del outreach, cadencia visual, señal del prospect con color, ficha del AE asignado, registro CRM y resumen ejecutivo.
- **ROADMAP v4.4.0**: caso 08 movido de Ola 2 a operativos (12 casos totales). Siguiente Ola 2: casos 14, 06, 21.

### Modificado

- `README.md`: badge de versión → 4.4.0, contador de operativos 11 → 12, caso 08 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.4.0, caso 08 marcado como completado, scaffolds 14 → 13.
- `docker-compose.yml` raíz: servicio `case08` cambiado de demo nginx (puerto 9008) a backend real FastAPI (puerto 8008) con volúmenes `data/` y `web/`.
- `index.html` portal: tarjeta de caso 08 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8008/`.

---

## v4.3.0 — 2026-05-04

### Agregado

- **Caso 17 — Legal Intake elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos y 2 routers condicionales: `recibir_solicitud → entrevista_inicial → clasificar_tipo_caso → [router especialidad → recopilar_hechos_{laboral|mercantil|civil}] → validar_informacion → [router completitud → solicitar_informacion_faltante] → evaluar_urgencia → generar_borrador_documento → asignar_abogado → producir_resumen_intake`.
  - Clasificación por especialidad legal mediante keyword scoring sobre `specialty_keywords.json` (laboral, mercantil, civil) y detección de subtipo (despido injustificado, incumplimiento contractual, sucesión intestada, etc.).
  - Extracción heurística DEMO de hechos estructurados desde el relato libre del cliente (montos, fechas, causales legales, partes, evidencia documental).
  - Validación de completitud contra campos requeridos por subtipo (`required_fields.json`); branch separado para registrar preguntas pendientes al cliente sin bloquear la generación del borrador.
  - Evaluación de urgencia procesal usando matriz de plazos legales típicos (60 días art. 168 CT, prescripción de títulos ejecutivos, etc.).
  - Generación de borrador inicial con plantillas (`templates.json`): demanda laboral, requerimiento extrajudicial, posesión efectiva. Placeholders no resueltos quedan marcados como `{{PENDIENTE: campo}}` para el abogado revisor.
  - Asignación automática del abogado responsable por especialidad y carga (`lawyers.json`, 6 abogados con casos activos simulados).
  - Modo DEMO: 3 intakes realistas (`INT-001` despido, `INT-002` incumplimiento contractual con cláusula penal, `INT-003` sucesión intestada con info faltante). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini mejora la redacción del borrador y el resumen ejecutivo si hay credenciales.
  - 26 tests (16 graph flow + 10 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado con volumen data/ read-only (puerto 8017).
  - UI dark theme con selector de intake, vista previa de la solicitud, badge DEMO/LIVE, timeline streaming NDJSON, panel de hechos extraídos, preguntas pendientes, borrador con highlight de placeholders, ficha del abogado asignado y resumen ejecutivo.
- **ROADMAP v4.3.0**: caso 17 movido de Ola 1 a operativos (11 casos totales). Siguiente Ola 2: casos 08, 14, 06, 21.

### Modificado

- `README.md`: badge de versión → 4.3.0, contador de operativos 10 → 11, caso 17 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.3.0, caso 17 marcado como completado, scaffolds 15 → 14.
- `docker-compose.yml` raíz: servicio `case17` cambiado de demo nginx (puerto 9017) a backend real FastAPI (puerto 8017) con volumen `data/` y `web/`.
- `index.html` portal: tarjeta de caso 17 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8017/`.

---

## v4.2.0 — 2026-04-28

### Agregado

- **Caso 05 — Analista de Documentos elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 7 nodos y 1 router condicional: `ingesta_texto → segmentar_secciones → extraer_clausulas → clasificar_riesgos → [escalar_revision_legal →] generar_checklist → producir_resumen_ejecutivo`.
  - Keyword extraction sobre secciones contractuales segmentadas por regex (CLÁUSULA, ARTÍCULO, SECCIÓN, CONSIDERANDOS, etc.).
  - Score de riesgo compuesto (0-100) a partir de cláusulas detectadas; router dirige a escalación legal solo si riesgo es ALTO.
  - Modo DEMO: lógica determinista sobre 3 documentos locales (NDA/bajo, Servicios TI/medio, Licitación/alto) y 8 patrones de cláusulas en `clause_patterns.json`.
  - Modo LIVE: GPT-4o-mini ajusta el score de riesgo y genera resumen ejecutivo narrativo.
  - 27 tests (18 graph flow + 9 API) — todos pasando.
  - Docker: Dockerfile non-root + compose.yml con volumen data/ read-only (puerto 8005).
  - UI dark theme con selector de documento, badge DEMO/LIVE, timeline de nodos y panel de resultados (cláusulas, checklist, resumen ejecutivo, escalación).
- **ROADMAP v4.2.0**: caso 05 movido de scaffold a operativos (10 casos totales). Siguiente Ola 1: caso 17 (Legal Intake).

### Modificado

- `README.md`: badge de versión → 4.2.0, contador de casos operativos 9 → 10, taxonomía corregida (caso 05 en OPERATIVO).
- `ROADMAP.md`: versión → 4.2.0, caso 05 marcado como completado, scaffolds 16 → 15.
- `docs/ARCHITECTURE.md`, `docs/wiki/Home.md`, `docs/wiki/Roadmap.md`, `docs/wiki/README.md`, `docs/wiki/_Sidebar.md`: versión → 4.2.0, 10 operativos.

---

## v4.1.0 — 2026-04-22

### Agregado

- **Caso 04 — SOC Triage de Alertas elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 8 nodos y 2 routers condicionales: `normalizar_alerta → enriquecer_ioc → correlacionar_eventos → evaluar_riesgo → [cerrar_automatico | investigacion_adicional → decision | escalar_analista → generar_informe_triage]`.
  - Score de riesgo compuesto (0-100) que pondera reputación de IOCs (VirusTotal/AbuseIPDB), desviación del baseline SIEM y severidad de la fuente.
  - Modo DEMO: lógica determinista sobre `alerts.json` (5 alertas reales: brute force SSH, nmap, Emotet, DNS C2, off-hours login) y `threat_intel.json` (IP reputation + file hashes + dominios + MITRE ATT&CK mapping).
  - Modo LIVE: GPT-4o-mini ajusta el score de riesgo y redacta el informe de triage narrativo.
  - Stubs de VirusTotal, AbuseIPDB, MISP, Splunk/Elastic y JIRA/ServiceNow listos para reemplazar por APIs reales.
  - 19 tests (7 API + 12 graph flow) — todos pasando.
  - Docker: Dockerfile + compose.yml + `.env.example` (puerto 8004).
- **`.secrets.baseline` actualizado**: hashes MD5 de malware demo registrados como falsos positivos conocidos.
- **ROADMAP v4.1.0**: caso 04 movido de scaffold a operativos (9 casos totales). Siguiente Ola 1: caso 05 (Analista de Documentos).

### Modificado

- `README.md`: badge de versión → 4.1.0, contador de casos operativos 8 → 9, tabla de estados actualizada, taxonomía corregida.
- `index.html`: caso 04 badge `LEGACY` → `OPERATIVO`, enlace al backend (puerto 8004).
- `docs/ARCHITECTURE.md`, `docs/wiki/Home.md`, `docs/wiki/Roadmap.md`, `docs/wiki/_Sidebar.md`: versión → 4.1.0, 9 operativos.

### Seguridad / Despliegue

- **`security.yml` — detect-secrets**: agregado `--exclude-files 'cases/.*/data/'` al paso de full filesystem scan para excluir hashes MD5 de IOCs de malware demo (falsos positivos). Consistente con la exclusión ya existente en el job `supply_chain`.
- **`security.yml` — grype matrix**: caso 04 añadido al escaneo de imagen Docker.
- **CVEs resueltos en los 9 backends** — lockfiles regenerados con `pip-compile`:

  | Paquete | Antes | Después | Referencia |
  |---|---|---|---|
  | `langsmith` | 0.7.30 | 0.7.31 | GHSA-rr7j-v2q5-chgv |
  | `langchain-openai` | 1.1.12 | 1.1.14 | GHSA-r7w7-9xr2-qq2r |
  | `langchain-core` | 1.2.28 | 1.3.0 | transitivo (requerido por langchain-openai 1.1.14) |
  | `lxml` *(caso 09)* | 6.0.3 | 6.1.0 | CVE-2026-41066 |
  | `pypdf` *(caso 09)* | 6.10.0 | 6.10.2 | GHSA-jj6c / GHSA-4pxv / GHSA-7gw9 / GHSA-x284 |

- **`requirements.in` de los 9 casos**: pins mínimos actualizados para que futuros `pip-compile` no regresen a versiones vulnerables.

---

## v4.0.1 — 2026-04-10

### Agregado

- **Interfaces web `backend/web/index.html`** para los casos 03, 19 y 25 (faltaban completamente).
  Cada interfaz incluye: hero en español con descripción del flujo, badge DEMO/LIVE, enlace `← VOLVER AL HUB` a `http://localhost:8080/`, pillrow de tecnologías, timeline de eventos en vivo via NDJSON streaming y panel de resultados con badges y listas.
  - **Caso 03 — Incident Response**: select INC-001/INC-002/INC-003, timeline de severidad P1/P2/P3, recovery checks, postmortem.
  - **Caso 19 — DevEx PR Review**: select PR-001/PR-042/PR-105, timeline de hallazgos por severidad, decision badge (REQUEST_CHANGES/APPROVE_WITH_COMMENTS/APPROVE).
  - **Caso 25 — Supervisor/Workers**: select DDL-2026-001/002/003, workers timeline con iconos, viability score coloreado, conflictos detectados y condiciones para proceder.
- **Datos DEMO completos** para casos 19 y 25:
  - `cases/19-devex-pr-review/data/sample_pr.json`: convertido de objeto único a array con 3 PRs distintos. PR-001 (SQL injection + eval → CRITICAL), PR-042 (creds hardcodeadas + shell injection → HIGH), PR-105 (solo docs → APPROVE).
  - `cases/25-supervisor-workers/data/sample_task.json`: convertido de objeto único a array con 3 tareas distintas. DDL-2026-001 (TechStartup $5M), DDL-2026-002 (FinTech $3.2M), DDL-2026-003 (CloudData $12M).
- **Sección "Estandar de la interfaz web"** en `.agents/skills/crear_caso/SKILL.md`: define qué es y qué NO es un caso (no es un link a JSON, no es una página sin UI, DEMO siempre funciona, datos deben cubrir todas las opciones del select).

### Corregido

- `cases/19-devex-pr-review/backend/src/integrations.py`: fallback gracioso a stub en vez de `ValueError` cuando el `pr_id` solicitado no existe en el JSON de datos.
- `index.html` (hub raíz): casos 03, 19 y 25 marcados como `OPERATIVO` con links correctos a `http://localhost:8003/web/`, `http://localhost:8019/web/` y `http://localhost:8025/web/`.

---

## v4.0.0 — 2026-04-09

### Agregado

- **Casos 03, 19, 25 elevados a OPERATIVO**: backends FastAPI + LangGraph completos con modo DEMO/LIVE, tests, Docker y CI.
  - **Caso 03** — Incident Response SRE: StateGraph con HITL auto-aprobado en DEMO, runbooks P1/P2/P3, integrations stub (PagerDuty, remediación, recovery), postmortem.
  - **Caso 19** — DevEx PR Review: análisis de seguridad/calidad/tests sobre diffs con detección de patrones (SQL injection, eval, imports), router por nivel de riesgo, changelog automático.
  - **Caso 25** — Supervisor/Workers: patrón multi-agente con 4 workers (financial, legal, operational, reputational), acumulación de resultados con `Annotated[list, operator.add]`, reconciliación y detección de conflictos.
- **OAuth2/OIDC opt-in** en todos los backends: nuevo módulo `auth.py` por caso con validación JWT vía JWKS. `USE_OAUTH2=false` por defecto (backward-compatible). Activa con `USE_OAUTH2=true` + `OAUTH2_JWKS_URL`.
- **Logging JSON estructurado** estandarizado en los 8 backends operativos: `ContextVar` + `TraceIdFilter` + `LOG_FORMAT` JSON + `X-Trace-ID` en respuestas. Los casos 01, 02 y 13 ahora tienen el mismo nivel de observabilidad que 09 y 10.
- **Endpoint `/metrics`** en todos los backends: uptime, requests_total, errors_total, avg_latency_ms, modo DEMO/LIVE, langsmith_enabled, oauth2_enabled.
- **LangSmith opt-in**: `langsmith` agregado a `requirements.in/txt` de los 8 casos. Activar con `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`. Sin credenciales, LangSmith permanece inactivo (modo DEMO intacto).
- **Nginx reverse proxy + TLS**: `nginx/` con Dockerfile, `nginx.conf`, `conf.d/default.conf` (8 upstreams), `scripts/gen-certs.sh` (self-signed para dev). `docker-compose.tls.yml` como override sin tocar el compose principal.
- **pip-compile workflow**: `requirements.in` para los 8 casos operativos, `scripts/pip-compile-all.sh` con modo `--check`, job `dependency_lock_check` en CI.
- **Seguridad CI mejorada**: grype con `fail-build: true` + `.grype.yaml` (`only-fixed: true`). detect-secrets con escaneo completo del filesystem y últimos 50 commits del git history.

### Modificado

- `docker-compose.yml`: agregados case03, case19, case25 (ports en `127.0.0.1`).
- `docker-compose.tls.yml`: 3 casos nuevos con ports reseteados para acceso solo vía nginx.
- `nginx/conf.d/default.conf`: upstreams y locations para case03, case19, case25.
- `.github/workflows/ci.yml`: jobs `python_case03`, `python_case19`, `python_case25` + `dependency_lock_check`.
- `.github/workflows/security.yml`: 3 casos nuevos en matrix de grype, `fail-build: true`, steps de full-scan y git-history-scan en detect-secrets.
- `Makefile`: targets `test-case03`, `test-case19`, `test-case25`, `pip-compile`, `pip-compile-check`.
- `scripts/pip-compile-all.sh`: casos 03, 19, 25 incluidos en la lista de compilación.
- `cases/09, 10 api.py`: middleware refactorizado para usar `auth.py` centralizado; eliminado código duplicado.

---

## v3.9.0 — 2026-04-06

### Seguridad

- **Auditoría completa por 8 capas**: contenedor/proceso, red, credenciales, servidor web, herramientas, autenticación, CI/CD y cadena de suministro.
- **Capa 1 — Contenedor**: backends 01 y 02 con usuario `appuser` (non-root) y imagen pineada a `python:3.11.10-slim`. Backend 13 también pineado.
- **Capa 1 — Demos nginx**: todos los 25 casos con `nginx:1.27.3-alpine` (antes `nginx:alpine` flotante) y `USER nginx` con chown correcto.
- **Capa 1 — Healthcheck**: demos corregidas de `curl` (ausente en Alpine) a `wget --spider` (BusyBox nativo). Puertos de healthcheck de casos 02–25 corregidos de 8080 a 80.
- **Capa 2 — Red**: todos los puertos de `docker-compose.yml` vinculados a `127.0.0.1` para prevenir acceso desde la red local.
- **Capa 4 — Servidor web**: 25 `nginx.conf` actualizados con `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy` y `Permissions-Policy`.
- **Capa 7 — CI/CD**: Dependabot configurado para pip (raíz + 5 backends), GitHub Actions y Docker.
- **Capa 7 — CI/CD**: escaneo de imágenes Docker con `grype` (Anchore) pineado por SHA. Se eligió grype sobre Trivy por incidente de supply chain conocido.
- **Capa 8 — Supply chain**: job `supply_chain` en CI detecta caracteres Unicode bidi (CVE-2021-42574 "Trojan Source") y patrones de ofuscación (`exec+base64`, `eval()` dinámico, `os.system` con concatenación).

### Documentación

- `SECURITY.md` actualizado a v3.9.0 con tabla de estado por capa, riesgos aceptados y pendientes.
- `README.md` y `CHANGELOG.md` actualizados a v3.9.0.
- Todos los documentos revisados para consistencia de versión y ortografía.
- 20 READMEs de casos scaffold reescritos con flujos Mermaid, tablas de stack técnico y descripción de valor de negocio.

---

## v3.8.0 — 2026-04-06

### Agregado

- Fase 2 de hardening aplicada a los casos operativos con `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y `TRUST_PROXY_HEADERS` como guardrails opcionales de exposición externa.
- Suite propia para el caso 02 (`pytest`) con validación de API, auth opcional, rate limiting y flujo LangGraph.
- Job dedicado en CI para el caso 02.

### Cambiado

- README, docs, wiki local, casos clave y Hub CLI sincronizados a v3.8.0.
- Documentación reescrita en ASCII para reducir drift y problemas de codificación.
- `hub.py` y la documentación del Hub alineados con la taxonomía `Operational/Industrial (v3.8.0)`.

### Seguridad — v3.8.0 — 2026-04-06

- Postura de seguridad actualizada para reflejar claramente controles implementados y límites de alcance.
- Guardrails de exposición externa documentados sin romper quickstart ni demos locales.
- CI y seguridad automatizada ahora reflejan el caso 02 como backend validado, no solo docker-build.

---

## v3.7.0 — 2026-04-02

### Agregado — v3.7.0 — 2026-04-02

- Caso 02 elevado a operacional con UI SRE, runbooks y nodos LangGraph adicionales.
- Frontend interactivo para el caso 02 con sugerencias y tracker de eventos.
- Rediseño del portal raíz hacia catálogo de automatizaciones IA.

---

## v3.6.0 — 2026-03-13

### Agregado — v3.6.0 — 2026-03-13

- Centro de APIs compartido para el portal y los casos operativos 01, 09, 10 y 13.
- Formulario de credenciales opcionales con nombre de variable, caso vinculado, enlace oficial y exportación `.env` por caso.
- Guía documental explícita para instalar primero y completar APIs después sin bloquear el modo DEMO.
