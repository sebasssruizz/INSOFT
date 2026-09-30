# Reporte final — Historial/stats de IA (recuperado del stash) + intentos de quiz calificados

Trabajo autónomo del 30/09/2026. Rama: `feat/estadisticas-intentos-quiz` (desde
`feat/preguntas-ia-banco-profesor`; sin push, sin tocar `main`).

## Resumen por fase

| Fase | Qué se hizo | Commit |
|---|---|---|
| 0 | Reconocimiento, línea base 100 passed, `PLAN_TECNICO.md` | `95207ec` |
| 1 | Recuperación del stash (`stash@{0}`, intacto): endpoints de historial/stats de IA, columnas `session_id/model_used/response_time_ms`, tests huérfanos verdes, página de estadísticas + ruta en el router | `620a99f` |
| 2 | Tabla `question_answers`, `POST /api/quiz/answers` (calificación en servidor, idempotente), el cliente deja de recibir `correct_index`/`explanation`, stats de quiz, export CSV (IA y quiz), pestañas IA/Quizzes en el frontend | `31a0d00` |
| 2b | Fix `attempt_id` VARCHAR(36) (portabilidad SQLite/PostgreSQL detectada en Docker) | `6256736` |
| 3 | README, `.env.example`, `docker-compose.yml`, verificación Docker + smoke por API, este reporte | `e4eb84b` + final |

## Qué se recuperó del stash y qué se completó

**Recuperado tal cual** (tras `git stash apply`, resolviendo conflictos conservando
la rama y añadiendo lo del stash): columnas del modelo `AiQuery`, migración
idempotente, helpers del repositorio (`_get_teacher_student_ids`, `get_by_user`,
`get_all_filtered`, stats), endpoints `/api/ai/history`, `/history/all`,
`/stats/overview|students|subtopics`, `session_id` en `AskRequest`, medición de
`response_time_ms`, enlaces del `TeacherDashboard`.

**Completado/corregido** (el stash estaba incompleto o roto):

1. `ai_query_repository.py` venía con el módulo duplicado entero (dos `def create`,
   dos header); se reescribió limpio.
2. `get_all_filtered` usaba `or_(*condiciones)` (los filtros se OR-an); corregido a
   filtros acumulativos (AND).
3. `get_stats_students` usaba `from sqlalchemy import subquery` (import inválido) y
   `func.array_agg` (no existe en SQLite); reescrito con subquery + join portables.
4. `history/all` del stash no filtraba por estudiantes del profesor (bug de seguridad);
   ahora scopia por `_get_teacher_student_ids`.
5. La caché de respuestas ("Opción B" del stash, `get_by_normalized`) NO se restauró:
   devolvía respuestas compartidas entre usuarios y rompía la semántica de los tests
   de `/ask`. El `AskResponse` del stash además no declaraba `from_cache`.
6. `TeacherAiStats.jsx` tenía JSX roto (`</header>` extra, cierre de lista mal, `}`
   de más), usaba `react-icons` (no instalado) y `api.get` de axios (no existe: el
   proyecto usa `apiFetch`), y tenía subtemas hardcodeados (ids 29–32). Reescrita.
7. `migrations.py` del stash cambiaba `NEW_INDEXES` a claves tupla sin actualizar el
   bucle de abajo; integrado ambos formatos correctamente.

## Fase 2: decisiones

- **Calificación en servidor**: `POST /api/quiz/answers` valida acceso al subtema
  (misma regla que `/ask`, `_ensure_subtopic_access`), exige pregunta `approved`
  (404), 422 si `selected_index` fuera de 0–3 o `attempt_id` no es UUID, 401 sin
  token, 403 sin acceso. Idempotente por unique `(attempt_id, question_id)`:
  repetir devuelve la respuesta ya guardada (no cambia el resultado).
- **Payload de estudiante** (`QuestionRead` y `_serialize_question`) sin
  `correct_index` ni `explanation`; el banco del profesor los conserva.
- **Borrado**: `_question_has_student_answers` ahora consulta la tabla real →
  borrar una pregunta con respuestas la **archiva** (`status='rejected'`), testeado.
- **Rate limit**: `QUIZ_ANSWER_RATE_LIMIT=120/hour` por usuario (limiter propio en
  `routes/quiz.py`, misma key_func JWT que el de IA).
- **CSV**: endpoints `GET /api/ai/stats/export.csv` y `GET /api/quiz/stats/export.csv`;
  solo estudiantes del profesor; escape de fórmulas Excel (prefijo `'` a celdas
  que empiezan por `= + - @`), testeado con nombre `=HYPERLINK(...)`.
- **Frontend**: `Quiz.jsx` recibe `onAnswer(questionId, optionIndex)` (async) y
  muestra el feedback con la respuesta del servidor; `attempt_id` con
  `crypto.randomUUID()` al iniciar el quiz (y nuevo al "Repetir el repaso");
  error de red → mensaje y las opciones vuelven a habilitarse (evita doble clic
  con `submitting`); la experiencia visual es la misma.
- **Estadísticas frontend**: `TeacherAiStats.jsx` con pestañas **Uso de IA** y
  **Quizzes**, barras Tailwind (sin dependencias nuevas), botón "Exportar CSV"
  con token (`downloadCsv` en `api.js`), estados de carga/vacío/error, responsive.
  Ruta `/teacher/ai-stats` registrada en `App.jsx` (protegida, rol TEACHER).

## Tests: antes y después

| | Antes | Después |
|---|---|---|
| Suite backend | 100 passed (2 huérfanos fuera) | **128 passed** (+10 de historial/stats IA recuperados, +9 quiz answers, +9 quiz stats) |

- Corridas seguidas verde: 6+ (detecté y arreglé un flake PREEXISTENTE en
  `test_review_aprobar_hace_visible`: el muestreo aleatorio del tope podía excluir
  la pregunta aprobada; se fuerza `QUIZ_MAX_QUESTIONS=0` en ese test).
- `npm run build`: OK (solo warnings preexistentes de chunk size por three.js).
- `git stash list`: `stash@{0}` sigue intacto (se usó `apply`, nunca `pop`/`drop`).

## Verificación en Docker (real, sin LLM)

- `docker compose up -d --build backend`: OK; logs sin errores; `/health` →
  `{"status":"ok"}`; `/docs` → 200.
- Migración en PostgreSQL verificada: tabla `question_answers` (PK serial, UNIQUE
  `(attempt_id, question_id)`, FKs ON DELETE CASCADE), columnas `session_id`,
  `model_used`, `response_time_ms` en `ai_queries`.
- Smoke por API real (`/tmp/opencode/smoke_estadisticas.py`), sin llamadas al LLM:
  payload del estudiante sin respuesta correcta → respuesta calificada en servidor +
  idempotencia → overview aislado por profesor (T1 ve 1 respuesta, T2 ve 0,
  estudiante 403) → CSV aislado descargable → stats IA vacías + 403 estudiante +
  historial propio 200.

## Bloqueos / notas

- Fallo puntual del smoke detectado y arreglado: `attempt_id` declarado `Uuid` en el
  modelo vs `VARCHAR(36)` en la migración PG → `operator does not exist: varchar = uuid`.
  Alineado el modelo a `String(36)` (commit `6256736`).
- La primera corrida del smoke chocó con 409 de enunciado duplicado (residuo de la
  corrida anterior en la BD real): el smoke ahora usa enunciado único por corrida.
- Generación IA con LLM real: no probada (prohibido); cubierta por tests mockeados.

## Comandos para probar

```bash
cd /home/sebassruizz/Proyectos/INSOFT/INSOFT

# Tests (venv del backend)
cd backend && source .venv/bin/activate && python -m pytest tests/ -q

# Build frontend
cd ../frontend && npm run build

# Backend en Docker (migra al arrancar) y health
cd .. && docker compose up -d --build backend
curl http://localhost:8000/health && curl -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs

# Smoke de extremo a extremo (sin LLM): python3 /tmp/opencode/smoke_estadisticas.py
```

## Checklist de prueba manual en el navegador

1. Login profesor (o dev) → panel → card/enlace "Estadísticas de IA" → `/teacher/ai-stats`.
2. Pestaña **Uso de IA**: si no hay consultas, mensajes de vacío; tras unas preguntas
   al asistente (requiere cuota), ver total, últimos 7 días, tiempo medio, barras por
   subtema, tabla por estudiante e historial; filtrar por subtema y por sesión;
   "Exportar CSV" descarga el archivo.
3. Pestaña **Quizzes**: tarjetas de intentos/respuestas/% acierto/estudiantes activos;
   tablas por pregunta (con la opción incorrecta más elegida, letra), por estudiante
   (% acierto con barra) y por subtema; "Exportar CSV".
4. Como estudiante: abrir un subtema → "Empezar el repaso": elegir una opción → la UI
   muestra correcto/incorrecto + explicación igual que antes (ahora la trae el
   servidor); fallar a propósito y verificar el resaltado de la correcta; avanzar;
   resultado final con las falladas y su explicación.
5. Repasar la unidad entera (`Repaso de la unidad`) y repetir el repaso: cada intento
   nuevo debe permitir responder de nuevo (attempt_id distinto).
6. Desconectar la red (o frenar el backend) y elegir una opción: aparece el mensaje
   de error de red y se puede reintentar.
7. Confirmar con devtools (Network) que el payload del quiz **no** contiene
   `correct_index` ni `explanation` antes de responder.
8. Profesora B no debe ver en las estadísticas a estudiantes de la profesora A
   (probar con dos profesores reales o via API).
