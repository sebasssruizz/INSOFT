# Plan técnico — Asistente "Agregar pregunta" + Modo práctica

Fase 0 (reconocimiento). Línea base y decisiones.

## Línea base

- Suite: **128 passed**. `npm run build`: OK.
- Stash `stash@{0}` intacto (no se toca).

## Hallazgos clave

- **Sí hay chat del asistente en producción**: `AiChatWidget.jsx` montado en
  `Layout.jsx` (en `AiTestChat.jsx` no existe; el grep solo encuentra
  `aiService.js`). Detecta `courseId`/`subtopicId` via `useMatch`. Fase 3: botón
  "Ponme a prueba" en ese widget + botones en SubtopicPage y UnitQuizPage.
- **Fase 1**: `POST /api/content/subtopics/{id}/questions` ya existe (crea
  `approved`); `QuestionForm.jsx` tiene la validación inline → extraer
  `validateQuestion` a `frontend/src/lib/questionValidation.js` y reutilizarla
  (sin tocar QuestionForm salvo un mínimo cambio de import).
- **Fase 2**: `QuestionStatus` sin CHECK en BD (texto libre) → agregar
  `PRACTICE="practice"` y revisar filtros: `get_approved_*` (usa
  `status == APPROVED`, ya excluye practice), cola de pendientes
  (`status == PENDING`), `estimate_minutes` (solo approved), importador (solo
  official), `count_approved_*`, resumen del banco (agregar conteo `practice`),
  `submit_answer` (404 para no approved → aceptar también practice).
- Repos a reutilizar: `ai_query_repository._get_teacher_student_ids`,
  `chunk_repo.list_chunks_for_subtopic`, `ai_service.generate_questions_for_subtopic`
  (se factoriza un guardado con status parametrizable o se replica el bloque de
  guardado con `status=practice`), `quiz_answer_repository` (respuestas 14 días).
- Popularity: conteo de `ai_queries` por `subtopic_id` (últimos 30 días,
  estudiantes de los mismos cursos del usuario) + 3× propias; solo IDs agregados,
  nunca texto ajeno.
- Config nueva: `PRACTICE_RATE_LIMIT=30/hour`, `PRACTICE_DEFAULT_COUNT=5`,
  `PRACTICE_MAX_COUNT=10`, `PRACTICE_AI_RATIO=0.4`,
  `PRACTICE_MAX_GENERATIONS_PER_SUBTOPIC_PER_DAY=4`; `AI_ASK_RATE_LIMIT` → `60/hour`.
- Router nuevo `routes/practice.py` con limiter propio (patrón quiz.py).
- Estadísticas: `origen` (`banco`|`practica`) en overview/preguntas/CSV comparando
  `source == 'ai' AND status == 'practice'`… decisión: columna `origen` calculada
  con join a `questions` (question_answers no guarda source) — se une por
  question_id ya existente en `iter_answers_for_export`; en overview se filtra por
  pregunta de práctica con EXISTS (retrocompatible).

## Decisiones

1. **Fase 1 sin backend nuevo** (salvo hueco descubierto). Wizard con 3 pasos,
   estado en un solo componente; helpers compartidos; accesibilidad (foco, Esc,
   aria-live).
2. **Costo**: reutilización primero (pool `practice` sin responder), máx 2 llamadas
   LLM por sesión y 1 por subtema, tope diario por subtema contando practice
   creadas hoy.
3. Fallo de IA → degradación silenciosa con `ai_available: false`.
4. Fase 4 (promover/descartar practice desde el banco): excepción de permisos
   documentada (cualquier profesor con acceso al subtema porque `created_by=NULL`).
