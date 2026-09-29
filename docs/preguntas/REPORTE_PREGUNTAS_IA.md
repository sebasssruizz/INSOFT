# Reporte final — Banco de preguntas del profesor + preguntas IA

Trabajo autónomo del 29/09. Rama: `feat/preguntas-ia-banco-profesor` (sin push).

## Resumen por fase

| Fase | Qué se hizo | Commit |
|---|---|---|
| 0 | Reconocimiento, línea base de tests, aislamiento de DB de tests (conftest), PLAN_TECNICO.md | `288df22` |
| 1 | Columnas `source`/`status`/`created_by`, migración idempotente, filtro approved centralizado, tope de quiz, protección del importador | `6d32e20` |
| 2 | CRUD del profesor, banco, resumen por subtema, revisión IA, validaciones y permisos | `2a3d608` |
| 3 | `POST /api/ai/questions/generate` con RAG, parser robusto, reintentos y rate limit propio | `b69a3de` |
| 4 | Frontend: `questionService.js`, `QuestionBank`, `QuestionCard`, `QuestionForm`, integración en `TeacherCoursePage` | `4ce059f` |
| 5 | Endurecimiento: N+1 eliminado, conteos solo approved, verificación de sanitización/reindexado/transacciones | `21e0966` |
| 6 | README, `.env.example`, `docker-compose.yml` | `99c46aa` |

## Archivos creados/modificados

**Backend (nuevos):** `app/models/question_meta.py`, `app/services/question_service.py`,
`app/services/question_parser.py`, `tests/conftest.py`, `tests/test_question_migration.py`,
`tests/test_teacher_questions_crud.py`, `tests/test_question_generator.py`.
**Backend (modificados):** `app/models/content.py`, `app/database/migrations.py`,
`app/repositories/content_repository.py`, `app/services/content_service.py`,
`app/services/content_import.py`, `app/services/ai_service.py`, `app/services/course_service.py`,
`app/services/study_time.py`, `app/schemas/content.py`, `app/schemas/ai.py`,
`app/api/routes/content.py`, `app/api/routes/ai.py`, `app/core/config.py`,
`app/core/openrouter_client.py`.
**Frontend (nuevos):** `src/services/questionService.js`, `src/components/teacher/{QuestionBank,QuestionCard,QuestionForm}.jsx`.
**Frontend (modificados):** `src/pages/TeacherCoursePage.jsx`.
**Config/docs:** `.env.example`, `docker-compose.yml`, `README.md`, `docs/preguntas/PLAN_TECNICO.md`.

## Resultados de tests y build

- **Antes (línea base):** 46 passed (excluyendo 2 archivos huérfanos, ver abajo).
- **Después:** **100 passed** (46 previos sin regresiones + 54 nuevos).
- Suite completa corrida **10+ veces** (incluida `-p no:randomly`): verde constante.
- `npm run build`: OK (solo warnings preexistentes de chunk size por three.js).
- No existe lint ni runner de tests de frontend configurado (no instalé ninguno).

### Archivos excluidos (no son mios ni regresiones)

`tests/test_ai_history.py` y `tests/test_ai_stats.py`: sin seguimiento en git, con errores
de sintaxis y prueban endpoints que no existen (`/api/ai/history`, `/api/ai/stats/*`).
Deben correrse con `--ignore`. Igual el `frontend/src/pages/TeacherAiStats.jsx` sin
seguimiento: no lo commiteé ni lo toqué.

### Flake observado (1 vez, no reproducible)

En 2 de ~10 corridas tempranas falló 1 test con `429` de rate limit (`/ask`, límite
`10/hour` compartido por user_id entre módulos porque la DB nueva re-numera usuarios
desde 1). El `limiter.reset()` por módulo del conftest lo eliminó: las últimas **10 corridas completas consecutivas** fueron verdes. Si reaparece, sube `AI_ASK_RATE_LIMIT`
en los tests o resetea el limiter también en los módulos de ask/gemini.

## Decisiones de diseño

1. **Sin endpoint de calificación**: la corrección del quiz es cliente-side
   (formativo). El "tope y muestreo" vive en los endpoints de listado
   (`get_subtopic_detail`, `get_topic_questions`) via `_sample_questions`.
2. **Migración**: `server_default` en el ALTER + UPDATE de respaldo (con WHERE) para
   filas viejas → todo queda `official/approved`. Índice `(subtopic_id, status)`.
   Sin CHECK constraints (el proyecto no usa; validación con constantes
   `QuestionSource`/`QuestionStatus` en `models/question_meta.py` + Pydantic).
3. **Ownership**: solo el autor (`created_by`) edita/borra/revisa; oficiales de solo
   lectura para todos (403 con mensaje). Ayuda única
   `assert_teacher_can_manage_subtopic` (404/403) reutilizada en todos los endpoints,
   incluida la generación IA.
4. **Duplicados**: normalización en Python (minúsculas, espacios colapsados, sin
   puntuación final) comparada contra las preguntas del subtema excepto rechazadas;
   409 con mensaje claro. En edición excluye la propia pregunta.
5. **Generación IA**: contexto delimitado `<contexto>` + instrucción anti-inyección en
   el system prompt; tope ~2000 palabras; lista de enunciados existentes (max 30) en el
   prompt **y** filtro post-parseo contra la BD. `topic_id` → reparte entre subtemas con
   chunks (máx. 3, 1 llamada por subtema; un subtema sin respuesta válida no aborta el
   resto). Reintentos: solo si 0 preguntas válidas, temperatura 0.3→0.1; errores de
   cuota/saturación del proveedor NO reintentan (429/503). JSON irrecuperable → 502.
   Guardado en una transacción con rollback. `correct_index` string "2" se castea;
   bools/otras basura → pregunta descartada.
6. **Borrado**: borrado duro (no hay tablas con FK a `questions` hoy); el código ya
   contempla archivar (status=rejected) si aparecen respuestas asociadas.
7. **Importador no destructivo reforzado**: solo compara/actualiza/borra
   `source='official'`; teacher/ai intactas; los `order` de las no oficiales se
   reacomodan después de las oficiales. `next_question_order` unificado en el repositorio.
8. **N+1 evitado**: conteos de aprobadas por curso/unidad con una query agregada
   (`count_approved_questions_by_subtopics`, GROUP BY) alimentando
   `get_course_content`, el resumen del panel y `course_service`.
9. **Rate limits independientes**: `/ask` (`AI_ASK_RATE_LIMIT=10/hour`) y
   `/questions/generate` (`AI_QUESTION_RATE_LIMIT=5/hour`), ambos por usuario JWT.
10. **Concurrencia doble clic**: botón deshabilitado en UI + rate limit por usuario.
    No agregué lock por profesor+subtema (el límite de 5/hora hace el doble envío
    inocuo); reevaluar si el límite crece.
11. **Estimación de tiempo**: `estimate_minutes` ahora cuenta solo preguntas approved.

## Verificación en Docker (real, sin LLM)

- `docker compose up -d --build backend`: OK; logs sin errores;
  `/health` → `{"status":"ok"}`; `/docs` → 200.
- Migración aplicada en PostgreSQL: columnas `source/status/created_by` e índice
  `ix_questions_subtopic_status` verificados por inspección.
- Flujo completo por API real (login dev → curso → pregunta manual → banco → summary →
  estudiante la ve en el quiz sin metadatos → review de teacher da 409 → PATCH →
  DELETE → deja de ser visible): **todo correcto**. Script usado: `/tmp/opencode/flow_test.py`.
- Generación IA **no** se probó contra el LLM real (cuota): cubierta por 25 tests
  mockeados y verificable manualmente cuando haya cuota.

## Comandos para la mañana

```bash
cd /home/sebassruizz/Proyectos/INSOFT/INSOFT

# 1. Revisar los commits de la rama
git log --oneline main..feat/preguntas-ia-banco-profesor

# 2. Correr la suite (venv del backend)
cd backend && source .venv/bin/activate
python -m pytest tests/ -q --ignore=tests/test_ai_history.py --ignore=tests/test_ai_stats.py

# 3. Build del frontend
cd ../frontend && npm run build

# 4. Rebuild del backend en Docker (aplica la migración al arrancar)
cd .. && docker compose up -d --build backend

# 5. Push cuando estés conforme
git push -u origin feat/preguntas-ia-banco-profesor
```

## Checklist de prueba manual en el navegador

1. Entrar como profesor (o login dev) → panel del curso → sección "Banco de preguntas".
2. Expandir una unidad → elegir un subtema → "Nueva pregunta": escribir enunciado, las
   4 opciones, marcar la correcta; probar que el botón queda deshabilitado con opciones
   vacías/repetidas o sin correcta; usar "Vista previa"; guardar.
3. Verificar que la pregunta aparece al instante con badge "Docente".
4. Entrar como estudiante al curso → quiz del subtema → la pregunta nueva aparece
   (si supera el tope de 10, entra en el muestreo aleatorio).
5. "Generar con IA" (requiere cuota de OpenRouter/Gemini): elegir cantidad → aparecen
   como "IA · pendiente" (no visibles para el estudiante) → Aprobar una y verificar que
   el estudiante ya la ve; Rechazar otra.
6. Cola de "Pendientes de revisión": aprobar/rechazar desde ahí; el badge de pendientes
   de la unidad se actualiza sin recargar.
7. Editar una pregunta propia (los cambios no aprueban una IA pendiente) y borrar otra
   (con confirmación).
8. Confirmar que las preguntas "Oficial" no ofrecen editar/eliminar.
9. Intentar duplicar un enunciado (variando mayúsculas/espacios) → mensaje 409.

## Supuestos que necesito confirmar

- ¿Está bien que el generador IA use el modelo `OPENROUTER_ANSWER_MODEL` (el mismo de
  `/ask`)? No hardcodeé modelos nuevos.
- El tope `QUIZ_MAX_QUESTIONS=10` con muestreo aleatorio por request: si prefieren un
  quiz fijo por estudiante (misma muestra guardada), es un cambio aparte.
- `TeacherAiStats.jsx` (sin seguimiento) queda fuera de esta rama a la espera de los
  endpoints `/api/ai/stats/*` que lo alimentan.

## Pendientes / mejoras sugeridas

- Aprobación por lote (seleccionar varias pendientes).
- Regenerar una pregunta IA individual rechazada.
- Estadísticas de acierto por pregunta (requiere registrar intentos: hoy no hay tabla
  de respuestas de estudiantes).
- Control de dificultad en preguntas IA (fácil/media/difícil en el prompt).
- Campo "curso" en las preguntas docente si algún día no deben compartirse entre cursos
  (hoy el contenido oficial es global por diseño).
