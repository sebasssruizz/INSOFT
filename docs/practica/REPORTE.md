# Reporte final — Asistente "Agregar pregunta" + Modo práctica

Trabajo autónomo. Rama: `feat/practica-y-agregar-pregunta` (desde
`feat/estadisticas-intentos-quiz`; sin push, sin tocar `main`, `stash@{0}` intacto).

## Resumen por fase

| Fase | Qué se hizo | Commit |
|---|---|---|
| 0 | Reconocimiento, baseline 128 passed + build OK, `docs/practica/PLAN_TECNICO.md` | `4f617f9` |
| 1 | Asistente "Agregar pregunta" (`AddQuestionWizard.jsx`), validación compartida, integración en `TeacherCoursePage` | `c33b1ad` |
| 2 | `QuestionStatus.PRACTICE`, `POST /api/practice/sessions`, config, stats con `origen`, 12 tests | `733716a` |
| 3 | Modo práctica en el frontend (subtema, unidad, chat "Ponme a prueba") | `f101180` |
| 4 | Banco: promover/descartar practice (badge, filtro, permisos) + tests | `1e35afb` |
| 5 | README/`.env.example`/`docker-compose.yml`, Docker + smoke, este reporte | final |

Nota: el commit `4f617f9` del plan técnico quedó en la rama base
(`feat/estadisticas-intentos-quiz`) por orden de operaciones (se creó la rama
después). No hay riesgo: la rama nueva lo incluye en su historia; no se force-pushó.

## Fase 1 — Asistente "Agregar pregunta" (frontend)

- Botón **"Agregar pregunta"** destacado en la cabecera del curso
  (`TeacherCoursePage`, junto a "Estudiantes inscritos").
- `AddQuestionWizard.jsx` (componente nuevo): Paso 1 (módulo → submódulo
  dependiente → enunciado → A–D + radio correcta → explicación plegada),
  Paso 2 (confirmación de solo lectura con estilo de estudiante y ruta
  "Módulo › Submódulo", botones Editar / Confirmar y guardar), Paso 3 (éxito con
  "Agregar otra en este submódulo" (conserva ubicación, limpia y enfoca el
  enunciado), "Agregar en otro submódulo", "Terminar" y contador "Agregadas en
  esta sesión").
- **Validación compartida**: `frontend/src/lib/questionValidation.js`
  (`validateQuestionDraft` + `optionDraftError`); `QuestionForm.jsx` refactorizado
  para usarla (sin duplicar lógica).
- Errores del servidor (409/422/403) vuelven al Paso 1 conservando lo escrito;
  `Esc` cierra con confirmación si hay cambios; foco al abrir y cambiar de paso;
  `aria-live` para errores; responsive (hoja en móvil, modal en desktop).
- **Sin endpoints nuevos** (usa `POST /api/content/subtopics/{id}/questions`).
- Ediciones mínimas en archivos compartidos: `QuestionBank.jsx` recibe props
  opcionales (`refreshSignal`, `onSelectedSubtopicChange`) — precarga el submódulo
  ya seleccionado en el banco y refresca lista/conteos tras guardar.

## Fase 2 — Modo práctica (backend)

- `QuestionStatus.PRACTICE = "practice"` (`models/question_meta.py`). Revisión de
  todos los filtros: el quiz/repaso normal usa `status == APPROVED` (intacto),
  la cola de pendientes usa `status == PENDING` (intacto), `estimate_minutes`
  solo cuenta approved (intacto), el importador solo toca `official` (intacto).
  `count_approved_*` no cuenta practice; el resumen del banco suma el conteo
  separado `practice`. `POST /quiz/answers` acepta `approved` **o** `practice`.
- **Columna nueva `questions.created_at`** (aditiva e idempotente, DDL por
  dialecto): necesaria para el tope diario de generaciones por subtema
  (implementación documentada: contar preguntas `practice` creadas hoy por subtema).
- **Config** (`config.py`, `.env.example`, `docker-compose.yml`):
  `PRACTICE_RATE_LIMIT=30/hour`, `PRACTICE_DEFAULT_COUNT=5`,
  `PRACTICE_MAX_COUNT=10`, `PRACTICE_AI_RATIO=0.4`,
  `PRACTICE_MAX_GENERATIONS_PER_SUBTOPIC_PER_DAY=4`; `AI_ASK_RATE_LIMIT` → `60/hour`
  (conservado). Los decoradores de slowapi ahora leen `settings` por request
  (lambda) — necesario para que el env por módulo de tests aplique.
- **`POST /api/practice/sessions`** (`routes/practice.py` + `practice_service.py`
  + `practice_repository.py`, limiter propio):
  1. Exactamente uno de `subtopic_id`/`topic_id` (422). Acceso igual que `/ask`
     (404/403 vía `ServiceError`).
  2. Subtemas objetivo: el subtema dado, o los del módulo con contenido; se
     ponderan por **popularidad** = consultas de pares de los mismos cursos
     (últimos 30 días, SOLO conteos agregados; nunca texto ajeno) + 3× consultas
     propias + bonus por menor % de acierto propio en `question_answers`.
  3. Banco ≈ `ceil(count × (1−ratio))`: `approved` docente > oficial > IA,
     excluye lo acertado en 14 días y prioriza lo fallado; reparto parejo por
     subtema según popularidad.
  4. IA: primero reutiliza `practice` no respondidas del subtema; solo si falta,
     genera reutilizando `generate_questions_for_subtopic` (parametrizado con
     `status`/`created_by`): máx 1 llamada por subtema, 2 por sesión, tope diario.
  5. Fallo del LLM → completa con banco, `ai_available: false`, sin error; sin
     nada disponible → 404 "Aún no hay preguntas disponibles para practicar este tema".
  6. Respuesta: `attempt_id` (UUID del servidor), `mode`, preguntas SIN
     `correct_index`/`explanation` con `is_ai_generated`, `composition`, orden mezclado.
- **Estadísticas**: `origen` (`banco`|`practica`) en overview
  (`respuestas_practica`), por pregunta y CSV (columna nueva, retrocompatible).

## Fase 3 — Frontend del estudiante

- **Sí existe chat del asistente en producción** (`AiChatWidget.jsx` en
  `Layout.jsx`): se agregó el botón **"Ponme a prueba"** cuando hay subtema
  activo; navega al subtema con `?practice=1` y la página abre la práctica.
- Botón **"Modo práctica"** junto a "Empezar el repaso" (`SubtopicPage`) y en el
  repaso de la unidad (`UnitQuizPage`, usa `topic_id`).
- Componente nuevo `PracticeQuiz.jsx`: estado "Preparando tu práctica…",
  reutiliza `Quiz.jsx` con el `attempt_id` del servidor (vía el mismo
  `POST /quiz/answers`), feedback por pregunta, "Practicar de nuevo" (nueva
  sesión), 404 amable, 429 "intenta más tarde", error de red con Reintentar.
- Etiqueta discreta **"Generada por IA · no revisada"** vía nueva prop opcional
  `badgeFor` en `Quiz.jsx` (edición mínima, no rompe usos existentes).
- Advertencia "la IA no está disponible ahora" cuando `ai_available=false`.

## Fase 4 — Banco del profesor

- Filtro **"Práctica IA"** + badge "IA · práctica" + contador "n práctica" en la
  lista de subtemas; acciones **"Aprobar para el banco"** y **"Descartar"**.
- `POST /api/content/questions/{id}/review` extiende: acepta preguntas
  `practice`. **Regla de permisos (excepción documentada)**: como `created_by`
  es NULL, la revisión de practice requiere solo acceso al subtema
  (`assert_teacher_can_manage_subtopic`); en este proyecto todo curso de
  profesor habilita todos los topics, así que en la práctica cualquier profesor
  con cursos puede revisar; un profesor sin cursos → 403 (testeado).

## Tests: antes y después

| | Antes | Después |
|---|---|---|
| Suite backend | 128 passed | **140 passed** (+12 `test_practice_mode.py`) |

- `npm run build`: OK. Docker: `up -d --build backend` limpio, migración de
  `questions.created_at` aplicada en PostgreSQL, `/health` OK, `/docs` 200.
- Cobertura nueva: composición banco→IA, 0 llamadas LLM con pool suficiente,
  exclusión de acertadas / prioridad de falladas, degradación por fallo de
  proveedor, 404 sin preguntas, tope diario por subtema, 401/403/422, payload sin
  respuesta correcta, aislamiento de practice (quiz normal, cola pendientes,
  resumen del banco), calificación de practice, privacidad (texto ajeno nunca en
  la respuesta), 429, promover/descartar desde el banco.

## Decisiones y notas

1. **Tope diario simple**: contar `questions` con `status='practice'` y
   `created_at >= inicio del día (UTC)` por subtema; requirió añadir
   `created_at` (aditiva, `NOT NULL DEFAULT NOW()` en PG).
2. **`created_by=NULL` y permisos**: excepción única en `review_ai_question`
   documentada; el resto del CRUD sigue exigiendo autoría.
3. **Fallo mío en el smoke (1 llamada real al LLM)**: la primera corrida del
   smoke contra Docker no tenía pool de práctica sembrado y el backend generó
   con el LLM real (2 preguntas). Corregido el smoke: siembra practice por SQL y
   las corridas siguientes no llaman al LLM. Los tests nunca llaman al LLM.
4. `_ensure_subtopic_access`/`ServiceError` se reutilizaron para el 403/404
   (sin duplicar reglas de acceso).
5. No existe lint ni runner de tests de frontend configurado (como en sesiones
   anteriores; no instalé ninguno).

## Comandos para probar

```bash
cd /home/sebassruizz/Proyectos/INSOFT/INSOFT

# Tests backend
cd backend && source .venv/bin/activate && python -m pytest tests/ -q

# Build frontend
cd ../frontend && npm run build

# Docker (migra al arrancar) + health/docs
cd .. && docker compose up -d --build backend
curl http://localhost:8000/health && curl -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs

# Smoke por API (sin LLM real): python3 /tmp/opencode/smoke_practica.py
# Smoke de la sesión anterior (quiz/estadísticas): python3 /tmp/opencode/smoke_estadisticas.py
```

## Checklist de prueba manual en el navegador

### Wizard de la profesora
1. Login profesor → curso → botón "Agregar pregunta" (cabecera).
2. Paso 1: elegir módulo → el select de submódulo se habilita; escribir
   enunciado, A–D, marcar la correcta; probar que "Continuar" queda deshabilitado
   con opciones vacías/repetidas o sin correcta; "Agregar explicación" plegable.
3. Paso 2: verificar la vista de solo lectura (ruta "Módulo › Submódulo",
   correcta marcada) → "Editar" vuelve al paso 1 con todo conservado.
4. "Confirmar y guardar" → Paso 3: "Pregunta guardada", contador "Agregadas en
   esta sesión: n".
5. "Agregar otra en este submódulo": el formulario queda limpio y enfocado en el
   enunciado, módulo/submódulo conservados → repetir 3 preguntas seguidas.
6. Intentar duplicar un enunciado (409): el error aparece en línea y vuelves al
   Paso 1 con lo escrito intacto.
7. "Agregar en otro submódulo" reinicia la selección; "Terminar" cierra. El
   banco (si estaba abierto con un submódulo) muestra la pregunta nueva y los
   conteos actualizados; con un submódulo ya seleccionado en el banco, el wizard
   lo precarga.
8. `Esc` a mitad del formulario pide confirmación; probar en móvil (hoja inferior).

### Modo práctica del estudiante
9. Login estudiante → subtema → "Modo práctica" → "Preparando tu práctica…" →
   quiz con 5 preguntas: las del banco y (si el pool de IA no alcanza) generadas
   por IA con la etiqueta "Generada por IA · no revisada".
10. Responder: feedback correcto/incorrecto + explicación como en el repaso;
    confirmar en devtools que el payload no trae la respuesta correcta.
11. Al final, "Practicar de nuevo" → nueva sesión; lo acertado hace un rato no
    vuelve a aparecer.
12. "Ponme a prueba" en el asistente (estando en un subtema) abre la práctica.
13. Repaso de unidad → "Modo práctica de la unidad" (práctica del módulo entero).
14. Sin preguntas disponibles (subtema nuevo sin contenido) → mensaje amable 404;
    tras agotar `PRACTICE_RATE_LIMIT` → 429.
15. Profesor: banco → filtro "Práctica IA" → "Aprobar para el banco" en una
    (aparece en el quiz normal) y "Descartar" en otra.
16. Estadísticas del profesor: overview muestra "respuestas de práctica", la
    tabla por pregunta distingue origen banco/práctica y el CSV trae la columna
    `origen`.
