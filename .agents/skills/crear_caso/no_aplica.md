---
name: mejorar-caso-langgraph
description: Mejora o crea un caso LangGraph usando como referencia los Casos 09 y 10, sin modificarlos, dejando el caso integrado en el repositorio, visible en el index principal y con documentación sincronizada.
---

# Skill: Mejorar o crear caso LangGraph

## Objetivo

Mejorar o crear un caso dentro de `cases/` tomando como referencia técnica y estructural los Casos 09 y 10, sin modificar esos casos, y dejando el resultado correctamente integrado en el repositorio.

## Alcance

Este skill se usa cuando el usuario pide:

- crear un nuevo caso;
- mejorar un caso existente;
- estandarizar un caso scaffold;
- elevar un caso para que quede coherente con el nivel del repositorio.

Este skill no se usa para modificar directamente los Casos 09 y 10, salvo que el usuario lo pida de forma explícita.

## Reglas obligatorias

1. No modificar los Casos 09 y 10.  
   Solo se usan como referencia.

2. No romper el repositorio.  
   Toda mejora debe respetar la estructura y funcionamiento actual.

3. Trabajar solo en el caso objetivo.  
   Los cambios deben concentrarse en la carpeta del caso solicitado y en los archivos globales que correspondan.

4. Actualizar siempre el `index.html` principal.  
   Si se crea o mejora un caso, debe quedar visible y enlazado desde la portada principal del proyecto.

5. Actualizar siempre la documentación relacionada.  
   El cambio debe reflejarse en el README del caso y en la documentación general si corresponde.

6. Mantener el estado honesto del caso.  
   No declarar un caso como completo, industrial o equivalente si aún no corresponde.

## Referencia de arquitectura

### Cuándo usar Caso 09 como referencia

Usar Caso 09 si el caso requiere:

- proceso iterativo;
- flujo con repeticiones;
- evaluación progresiva;
- scoring, ranking o selección;
- avance por etapas repetidas.

### Cuándo usar Caso 10 como referencia

Usar Caso 10 si el caso requiere:

- flujo lineal;
- etapas secuenciales;
- checklist;
- asignación de acciones, accesos, permisos o tareas;
- orquestación paso a paso.

### Si el caso mezcla ambos

Tomar como base el Caso 10 y usar lógica tipo Caso 09 solo en la parte que necesite iteración o reintento.

## Flujo de trabajo obligatorio

### 1. Analizar el caso solicitado

- entender el objetivo del caso;
- identificar si se parece más al Caso 09, al Caso 10 o a un híbrido;
- revisar la carpeta actual del caso dentro de `cases/`;
- definir con claridad qué se debe mejorar o crear.

### 2. Respetar el alcance del cambio

- si el caso ya existe, mejorarlo sin tocar 09 ni 10;
- si el caso no existe, crearlo con la convención del repositorio;
- mantener nombres, estructura y estilo coherentes con el proyecto.

### 3. Sincronizar el caso con el repositorio

Actualizar lo que corresponda en:

- carpeta del caso;
- README del caso;
- metadata del caso;
- documentación general si aplica;
- navegación principal del proyecto.

### 4. Actualizar el `index.html` principal

Siempre que un caso se cree o mejore:

- agregar o actualizar su enlace en la portada;
- mostrar nombre y descripción breve;
- verificar que la ruta funcione;
- evitar enlaces rotos o error 404;
- mantener el estilo visual existente.

### 5. Verificar consistencia final

Antes de cerrar:

- confirmar que el caso quedó visible;
- confirmar que el `index.html` principal quedó actualizado;
- confirmar que la documentación coincide con el estado real;
- confirmar que no se tocaron los Casos 09 y 10;
- confirmar que no se rompió el repositorio.

## Resultado esperado

Este skill debe dejar:

- un caso creado o mejorado;
- los Casos 09 y 10 intactos;
- la documentación actualizada;
- el `index.html` principal actualizado;
- el caso visible desde la portada;
- el repositorio consistente y sin roturas.