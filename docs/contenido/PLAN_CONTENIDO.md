# PLAN_CONTENIDO — Completar unidades restantes (6–8)

Fecha: 2026-10-01 · Rama: `feat/contenido-unidades-restantes`

## 1. Estado de la carga y formato del importador

- Las **9 unidades ya existen en la BD** (tabla `topics`, orders 0–8). Las unidades 1–5 están
  completas (19 subtemas) y **no se tocan**. La unidad 9 (pterigión) ya está cargada y
  tampoco se toca.
- Los subtemas de las unidades 6, 7 y 8 son **placeholders** (~30–36 palabras, sin contenido
  real) y son la brecha a cerrar.
- **Dónde viven los archivos:** `docs/importacion/units_v2/unidadN.md` (formato actual,
  un archivo por unidad, commiteados). Los nuevos: `unidad6.md`, `unidad7.md`, `unidad8.md`.
- **Formato exacto que acepta el importador** (`backend/app/services/content_import.py`,
  endpoint `POST /api/content/import`, script `backend/app/scripts/import_document.py`):
  - `# UNIDAD N. Nombre` — empareja la unidad **por nombre** (debe coincidir con el existente
    en BD; si no existe, crea y agrega al final).
  - Párrafo siguiente a `#` = descripción de la unidad.
  - `## Nombre del subtema` — se sincroniza **por posición (order)** dentro de la unidad:
    el contenido nuevo reemplaza al placeholder.
  - Contenido libre (párrafos, negritas, listas `-`/`1.`, tablas, subtítulos `###` internos,
    que se conservan como texto del subtema).
  - `### Preguntas` — preguntas numeradas `1.` con opciones `- [ ]` y correcta `- [x]`;
    líneas posteriores a las opciones = explicación (admite `Correcta:` como fallback).
  - Importador **idempotente y no destructivo** (`import_document` con `prune=False`):
    nunca borra subtemas/preguntas no mencionadas; las preguntas `teacher`/`ai` no se tocan;
    las `official` se actualizan por posición y las nuevas se agregan al final. Reindexa RAG
    y enlaza a todos los cursos automáticamente.
- **Línea de fuente:** el formato actual no contempla campo de fuente. Decisión: cerrar cada
  subtema nuevo con una línea visible `Fuente: <archivo>, <páginas/diapositivas>`.
  El exportador a Word la detectará con regex para resaltarla.

## 2. Vara de calidad (medidas en BD sobre unidades 1–5)

- **Palabras por subtema:** mediana **953** (rango 640–1287). Objetivo: 715–1190 (±25%).
- **Preguntas oficiales por subtema:** **3** en los 19 subtemas de U1–5.
  Las unidades nuevas llevan **4–5 preguntas** (mínimo 3, la vara lo permite).
- Estructura de secciones observada en `units_v2` (referencia de estilo):
  Introducción → Ficha técnica rápida → Concepto e indicaciones → Anatomía aplicada y
  puntos críticos → Lista de chequeo – Mesa de Mayo → Técnica quirúrgica paso a paso →
  Complicaciones y respuesta del instrumentador → Manejo posoperatorio → Alertas y perlas
  del instrumentador → Términos clave.

## 3. Matriz de brechas (verificada contra BD, no asumida)

| Unidad | Subtema según compendio | Estado en BD | Acción |
|---|---|---|---|
| U1–U5 (19 subtemas) | — | completo (640–1287 palabras, 3 preguntas, chunks) | no tocar |
| U6 Corrección de estrabismo | Técnicas para Corrección de estrabismo | **incompleto** (36 palabras) | redactar |
| U7 Patologías refractivas | Miopía, Hipermetropía y Astigmatismo | **incompleto** (33 palabras) | redactar |
| U8 Oculoplastia | Cirugía en Párpados | **incompleto** (31 palabras) | redactar |
| U9 Pterigión | 4 subtemas | cargado, subtemas breves (64–398 palabras) vs. su propia referencia `unidad9_pterigion_v1.md` (más extensa) | **no tocar** (regla del encargo); discrepancia anotada en `PENDIENTES_CLAUDIA.md` |

## 4. Mapeo preliminar subtema → fuente

| Subtema | Fuente | Cobertura |
|---|---|---|
| U6 · Técnicas para Corrección de estrabismo | `Manual-de-tecnicas-quirurgicas-de-oftalmologia.pdf` págs. 13–16 (concepto, grupos de técnicas, indicaciones, contraindicaciones, instrumental, suturas Vicryl 6/0 y 7/0, descripción técnica completa retroimplante/reimplante de rectos) | completa |
| U7 · Miopía, Hipermetropía y Astigmatismo | `Manual…pdf` págs. 39–41 (cirugía refractiva LASIK: refracciones corregibles, indicaciones, contraindicaciones, cuidados de enfermería, instrumental, técnica) | completa para la técnica; la explicación fisiopatológica de cada ametropía es limitada en la fuente → se redacta solo lo que la fuente dice |
| U8 · Cirugía en Párpados | `Manual…pdf` págs. 58–59 (chalazión, procedimiento palpebral) + págs. 5–9 y Guía (anatomía de párpados, blefaróstato, riendas palpebrales) | **parcial**: no existe en las fuentes técnica de blefaroplastia/ptosis/entropión/ectropión → se marca `PENDIENTE CLAUDIA` y se redacta solo lo cubierto |

- Banco de preguntas de la docente (`Banco_de_preguntas_Cirugia_de_Pterigion.docx`) cubre
  solo pterigión (U9, ya cargada): **no hay banco docente para U6–U8** → las preguntas de
  esas unidades se crean a partir de las fuentes.
- Nota: el Guion/PPTX de inyección intravítrea cubre U2 (ya hecha); PTERIGIÓN.docx cubre U9.

## 5. Decisión documentada sobre la estructura

`PROPUESTA DISEÑO COMPENDIO.docx` define 8 unidades con subtemas explícitos (U1: 7,
U2: 4, U3: 3, U4: 3, U5: 2, U6: 1, U7: 1, U8: 1) y la U9 se definió después (pterigión paso
a paso, 4 subtemas según su referencia). La BD refleja exactamente esa estructura, así que
**no se agregan ni renombran unidades ni subtemas**: solo se rellena el contenido de los
placeholders de U6–U8.

## 6. Baseline

- Suite de tests: **140 passed** (backend `.venv`).
- Docker compose levantado (backend :8000, frontend :3000, db :5433).
- `stash@{0}` intacto, sin push, sin tocar `main`.
