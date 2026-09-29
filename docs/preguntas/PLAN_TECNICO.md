# Plan técnico — Banco de preguntas del profesor + preguntas IA

Fase 0 (reconocimiento). Resumen de lo encontrado y decisiones de diseño.

## Línea base de tests (antes de tocar nada)

- Suite completa: **46 passed** (`pytest tests/` excluyendo los 2 huérfanos, ver abajo).
- Verificado en 3 corridas completas seguidas (incluida una con orden aleatorio) y por archivo.

### Excluidos de la línea base (no son regresiones)

- `tests/test_ai_history.py` y `tests/test_ai_stats.py`: prueban endpoints que NO existen
  (`/api/ai/history`, `/api/ai/stats/*`) y tenían errores de sintaxis. Son archivos sin
  seguimiento en git de una sesión anterior; se dejan intactos y fuera con `--ignore`.

## Trabajo hecho en Fase 0 (infra de tests, rama propia)

1. **`tests/conftest.py` (nuevo)** — DB de tests aislada:
   - SQLite temporal único por ejecución en `tempfile.mkdtemp()`.
   - El engine singleton se crea en conftest (import temprano), así los
     `os.environ["DATABASE_URL"]` de los módulos ya no re-apuntan la DB.
   - La Settings singleton se actualiza in-place con las env vars de cada módulo
     (para que DEV_AUTH_ENABLED, claves, etc. no queden congelados a los defaults
     de conftest) y DATABASE_URL se re-fuerza al archivo temporal.
   - Tablas drop/create **por módulo** + `limiter.reset()`: elimina residuos entre
     módulos (cursos que hacían fallar `len(courses)==1`) y contadores de rate
     limit heredados (los user_id se re-numeran desde 1 en cada módulo).
   - Raíz del problema original: fixtures viejos hacían `os.remove()` del archivo
     SQLite compartido a mitad de sesión → `readonly database` / `no such table`.
2. **`app/database/migrations.py`**: comentario aclaratorio (la reflexión del
   inspector no se cachea entre llamadas).

## Nombres reales encontrados (a reutilizar)

- Auth: `get_current_user`, `require_teacher` (`app/auth/dependencies.py`).
- Ownership de curso: `Course.teacher_id` (`app/models/course.py`); tópicos habilitados
  por curso: `CourseTopic(course_id, topic_id, enabled)`; acceso: `course_service.get_course_with_access_check`.
- Cursos del profesor: `course_repo.get_courses_for_teacher(db, user_id)`.
- Acceso a subtema (patrón ya existente): `ai_service._ensure_subtopic_access(...)`.
- RAG: `ai_service._retrieve_chunks(db, query, subtopic_id, course_id)`,
  `chunk_repo.list_chunks_for_subtopic(db, subtopic_id)`,
  `embeddings_service.embed_text/cosine_similarity`.
- LLM: `call_openrouter(model, system_prompt, user_content)` (con
  `OpenRouterSaturatedError`/`OpenRouterCallError`), `ai_service.call_gemini(...)`,
  selector `settings.AI_PROVIDER`.
- Preguntas: `Question` (`app/models/content.py`), preguntas por subtema cargadas via
  `Subtopic.questions` (relationship, `order_by Question.order`); serialización en
  `content_service._serialize_question`; sincronización oficial en
  `content_import.sync_questions` (crea/actualiza/borra por orden, prune).
- Consumo por estudiantes: `content_service.get_subtopic_detail` (subtema completo con
  preguntas) y `get_topic_questions` (repaso de unidad). **No hay endpoint de
  calificación separado**: `QuestionRead` expone `correct_index` y el cliente corrige.
- Rate limit: `slowapi.Limiter` con `key_func` por user_id del JWT (`routes/ai.py`),
  límite via `settings.AI_ASK_RATE_LIMIT`.
- Tests: patrón en `tests/test_ai_ask.py` — env vars al inicio, `TestClient(app)`
  module-scoped, login dev `/api/auth/dev` con rol, `@patch(...call_openrouter)`.
  DB via conftest (nuevo). Fixtures útiles: `create_teacher_course`, `disable_topic_in_course`.

## Decisiones de diseño

- **Sin calificación en backend**: el envío del quiz no existe como endpoint; la
  corrección es cliente-side. El "tope y muestreo del quiz" se implementa en los
  endpoints que listan preguntas (`get_subtopic_detail`/`get_topic_questions`) y en el
  repositorio, filtrando `status='approved'`.
- **Banco del profesor**: se agrega a `content.py` (rutas) + `content_service.py`
  (lógica) + `content_repository.py` (queries), sin servicio nuevo.
- **Oficiales solo lectura**: el importador sigue siendo el dueño de `source='official'`;
  el panel no las edita ni borra.
- **IA siempre `pending`**: nunca visible hasta aprobación del profesor.
- Variables nuevas: `AI_QUESTION_RATE_LIMIT` (5/hour), `AI_QUESTION_MAX_ATTEMPTS` (2),
  `QUIZ_MAX_QUESTIONS` (10).

## Archivos previstos a tocar

Backend: `models/content.py`, `database/migrations.py`, `schemas/content.py`,
`services/content_service.py`, `services/content_import.py`, `repositories/content_repository.py`,
`api/routes/content.py`, `api/routes/ai.py`, `services/ai_service.py`,
`core/config.py`, `core/openrouter_client.py` (params opcionales).
Frontend: `services/questionService.js` (nuevo), `pages/TeacherCoursePage.jsx`,
`components/teacher/QuestionBank.jsx|QuestionCard.jsx|QuestionForm.jsx|AiGenerateButton.jsx` (nuevos).
Config/docs: `.env.example`, `docker-compose.yml`, `README.md`.
Tests: `tests/test_question_migration.py`, `tests/test_teacher_questions_crud.py`,
`tests/test_question_generator.py`.
