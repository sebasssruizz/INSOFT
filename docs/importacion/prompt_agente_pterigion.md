Necesito que hagas 3 cosas en orden, sobre el proyecto INSOFT. No avances al siguiente bloque hasta confirmar que el anterior funcionó.

═══════════════════════════════════════
BLOQUE 1 — Importar contenido de lectura de Pterigión
═══════════════════════════════════════

Te adjunto el archivo `unidad9_pterigion.md`, ya escrito en el formato que espera `content_import.py` (# unidad, ## subtema, ### Preguntas con - [x] en la opción correcta). Tiene 4 subtemas: Definición, Indicaciones/Contraindicaciones, Técnica Quirúrgica, Complicaciones.

1. Copia el archivo a `docs/importacion/unidad9_pterigion.md` en el repo.
2. Reconstruye el backend si aún no lo hiciste desde la última sesión:
   ```
   cd INSOFT && sudo docker compose up -d --build backend
   ```
3. Impórtalo con el CLI (o dime si prefieres que lo haga por la UI en /teacher/import):
   ```
   docker compose exec backend python -m app.scripts.import_document docs/importacion/unidad9_pterigion.md
   ```
4. Verifica que haya sincronizado sin duplicar contenido existente de pterigio (recuerda: el sincronizador es no-destructivo, actualiza por nombre). Si ya existe una "UNIDAD 9. Cirugía de Pterigión" del demo anterior, confírmame si se actualizó esa misma unidad o si creó una nueva — necesito que NO queden duplicadas.
5. Confirma cuántos subtopics y chunks quedaron indexados para esta unidad (deberían ser 4 subtemas).

═══════════════════════════════════════
BLOQUE 2 — Migración de base de datos: session_id y model_used
═══════════════════════════════════════

Agregar dos columnas a `ai_queries` para poder agrupar conversaciones y saber qué modelo respondió cada fila:

```sql
ALTER TABLE ai_queries ADD COLUMN session_id UUID;
ALTER TABLE ai_queries ADD COLUMN model_used VARCHAR;
CREATE INDEX idx_ai_queries_session_id ON ai_queries(session_id);
```

1. Agrega estas columnas en `migrations.py` (el proyecto no usa Alembic, usa migrations.py + create_all — sigue ese mismo patrón).
2. Actualiza el modelo SQLAlchemy `AiQuery` (en el archivo del modelo correspondiente) agregando:
   ```python
   session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
   model_used = Column(String, nullable=True)
   ```
3. Actualiza `ai_query_repository.py` para que al guardar una consulta, si el request incluye `session_id`, lo guarde (si no viene, queda NULL — no rompe el flujo actual). También guarda `model_used` con el nombre del modelo que generó la respuesta (ahora mismo debería ser `nvidia/nemotron-3-super-120b-a12b:free`).
4. El campo `session_id` es opcional en el body de `POST /api/ai/ask` por ahora — no lo hagas obligatorio, así no rompes al AiTestChat.jsx que ya existe.
5. Corre las migraciones y confírmame que la tabla `ai_queries` tiene las columnas nuevas.

═══════════════════════════════════════
BLOQUE 3 — Batch de pruebas con las 80 preguntas reales de pterigio
═══════════════════════════════════════

Te adjunto `qa_pairs_pterigion.json`: 80 pares pregunta/respuesta-esperada (20 fáciles, 25 medias, 35 complejas), ya parseados Y etiquetados por subtema, con esta forma:
```json
[
  {"id": 1, "difficulty": "facil", "question": "...", "expected_answer": "...", "subtopic": "definicion"},
  ...
]
```
El campo `subtopic` toma uno de estos 4 valores, que corresponden 1:1 a los subtemas importados en el Bloque 1 (en el mismo orden en que aparecen en `unidad9_pterigion.md`):
- `definicion` → "Definición y generalidades"
- `indicaciones` → "Indicaciones y contraindicaciones"
- `tecnica` → "Técnica quirúrgica e instrumentación"
- `complicaciones` → "Complicaciones"

Distribución: 41 técnica, 20 complicaciones, 14 definición, 5 indicaciones. La clasificación se hizo por palabras clave + revisión manual de casos ambiguos — si al correr el batch ves que alguna pregunta claramente quedó en el subtema equivocado, es un error menor de etiquetado, no del pipeline de IA; anótalo pero no lo cuentes como falla de RAG.

1. Copia el archivo a `scripts/qa_pairs_pterigion.json`.
2. Crea `scripts/run_qa_batch.py` que:
   - Lea `qa_pairs_pterigion.json`
   - Genere un `session_id` (UUID) único para toda la corrida, para que las 80 preguntas queden agrupadas como una sola "sesión" en `ai_queries`
   - Obtenga el mapeo `subtopic` (slug) → `subtopic_id` real en la BD, consultando los 4 subtemas de "UNIDAD 9. Cirugía de Pterigión" por nombre (deben coincidir con los 4 `##` de `unidad9_pterigion.md`)
   - Para cada una de las 80 preguntas, haga `POST /api/ai/ask` con un token de estudiante de prueba, `question`, el `subtopic_id` que le corresponde según su campo `subtopic`, y el `session_id` de la corrida
   - Guarde localmente un CSV o JSON de salida con: `id, question, expected_answer, ai_answer, chunks_used, match_aproximado (compáralo tú con criterio simple, ej. si comparten al menos 2-3 palabras clave del expected_answer)`
   - Imprima al final un resumen: cuántas de las 80 la IA respondió con "no sé"/genérico vs. cuántas dieron contenido relacionado
3. Corre el batch:
   ```
   docker compose exec backend python -m app.scripts.run_qa_batch
   ```
4. Pásame el resumen de resultados y 3-4 ejemplos de preguntas donde la respuesta de la IA se alejó bastante de `expected_answer`, para que decidamos si hay que ajustar el chunking o el prompt de generación.
5. Confírmame que las 80 filas quedaron en `ai_queries` con el mismo `session_id`, para poder revisarlas después desde la vista de profesor.

═══════════════════════════════════════
Al terminar los 3 bloques, dime en qué quedó cada uno y si algo no cuadró con la arquitectura actual.
