# Plan técnico — Historial/stats de IA (recuperación) + intentos de quiz calificados

Fase 0 (reconocimiento). Línea base y decisiones.

## Línea base

- Suite: **100 passed** (`python -m pytest tests/ -q --ignore=tests/test_ai_history.py --ignore=tests/test_ai_stats.py`).
- La solución de sintaxis de reportes anteriores sobre los tests huérfanos ya no aplica:
  hoy parsean OK (no hay errores de sintaxis); lo que falla es su entorno (pisan
  `os.environ["DATABASE_URL"]` y borran tablas a mano, incompatible con el conftest aislado).
- `stash@{0}` leído completo. **Incompletables tal cual**: el diff paísma el archivo
  `ai_query_repository.py` (bloques duplicados) y `TeacherAiStats.jsx` tiene JSX roto
  (`</header>` extra, `</ul>` mal cerrado,`}` de más al final). El resto (rutas, repos,
  servicios, migración) es sólido. Se aplicará con `git stash apply` y se depurará a mano.

## Hallazgos del stash (lo que se recupera)

- `models/ai_query.py`: `session_id` (UUID), `model_used`, `response_time_ms`.
- `migrations.py`: columnas idempotentes + índice `idx_ai_queries_session_id`.
- `ai_query_repository.py`: helpers `_get_teacher_student_ids`, `get_by_user`,
  `get_all_filtered`, `get_by_normalized`, `get_stats_overview|students|subtopics`.
- `routes/ai.py`: `GET /history`, `/history/all`, `/stats/overview|students|subtopics`.
- `schemas/ai.py` + `ai_service.py`: `session_id` en AskRequest, medición de tiempo
  y caché de respuestas normalizadas (riesgo: la caché rompe `test_ask_ai_*` que
  siembran la misma pregunta 2 veces → **decisión: NO restaurar la caché**;
  sí restaurar `session_id` y `response_time_ms`).
- `TeacherDashboard.jsx`: enlace “Estadísticas de IA” + card lateral.
- Bug del stash: `get_all_filtered` usa `or_(*conditions)` (debe ser `and_`).

## Decisión sobre student payload

`_serialize_question` (usada por `get_subtopic_detail` y `get_topic_questions`) deja
de incluir `correct_index`/`explanation`; `QuestionRead` pierde esos campos.
Profesor: `serialize_question_for_teacher` intacta.

## Nombres reales reutilizados

- `_ensure_subtopic_access` (ai_service), `get_course_with_access_check` (course_service).
- `course_repo.get_courses_for_teacher` → inscripción: `CourseMembership`.
- `QuestionStatus.REJECTED` etc. (`models/question_meta.py`), `delete_question` ya
  contempla archivar si `_question_has_student_answers` da True (hoy hardcode False).
- Rate limit: `routes/ai.py` `limiter` con key por user_id JWT.

## Diseño Fase 2

- Tabla `question_answers` (FK users/questions ON DELETE CASCADE,
  subtopic_id denorm., `attempt_id` UUID, unique `(attempt_id, question_id)`).
- `POST /api/quiz/answers`: valida acceso al subtema + pregunta approved; calcula
  `is_correct` en servidor; idempotente; rate limit `QUIZ_ANSWER_RATE_LIMIT=120/hour`.
- `_question_has_student_answers` pasa a consultar la tabla real → archivar funciona.
- Stats quiz: repositorio nuevo `quiz_stats_repository.py` con el mismo filtro de
  estudiantes del profesor; endpoints `GET /api/quiz/stats/*` + export CSV
  (escape de fórmulas Excel: prefijo `'`).
- Frontend: `Quiz.jsx` recibe `onAnswer(questionId, selectedIndex) -> Promise` desde
  las páginas; `attempt_id` con `crypto.randomUUID()` por intento; feedback via
  respuesta del servidor; el render visual no cambia.
