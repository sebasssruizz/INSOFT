# Reporte de sesión — Fases 0 a 5

Fecha: 2026-10-07 · Repo: `INSOFT/` · Todas las ramas creadas desde `main` actualizado.

## Resumen por fase

| Fase | Rama | Commit(s) | Estado |
|------|------|-----------|--------|
| 0 — Reporte de estado | (ninguna) | — | ✔ sin cambios |
| 1 — Quitar tiempos | `chore/quitar-tiempos` | `fccba62` | ✔ push OK, build + 147 tests backend ✓ |
| 2 — Auditoría preguntas | `chore/auditoria-preguntas` | `ad6e4e7` | ✔ push OK (solo lectura; `--apply` NO ejecutado) |
| 3 — Pulido repaso | `fix/repaso-ui` | `3b46b6c` | ✔ push OK, build ✓ |
| 4 — Agregar preguntas | `feat/agregar-preguntas-ajustes` | `b75c601` | ✔ push OK, build ✓, 10 tests frontend ✓, 147 tests backend ✓ |
| 5 — Despliegue | `chore/deploy-config` | `4c9b393` | ✔ push OK (workflow de Actions EXCLUIDO del commit, ver abajo) |
| Reporte | `docs/reporte-sesion` | este archivo | ✔ |

**PRs no creados**: `gh` está autenticado pero el token (PAT) no tiene permiso
`pull_requests:write` ni `workflow`. Los PR se deben abrir a mano (ver "Pasos manuales").

---

## FASE 0 — Reporte de estado

**a) Frontend**: React 18 + **Vite 5** (no Next.js). Scripts `package.json`: `dev` (vite, puerto
5173), `build` → `vite build` → carpeta `dist/`. URL base de la API: `frontend/src/services/api.js`,
variable `VITE_API_URL` (`import.meta.env`); fallback dev `http://localhost:8000`; si el host no es
localhost infiere `http://<host>:8000` (uso actual del Compose en LAN; en Vercel SIEMPRE se pone
`VITE_API_URL`). No había pruebas de frontend ni linter configurados.

**b) Duración/tiempo**:
- Backend: NO hay columna en BD. `estimated_minutes` es **cálculo en runtime**
  (`app/services/study_time.py` ritmo 90 palabras/min + 1.5 min por pregunta aprobada; mínimo 4 min),
  expuesto por los schemas `TopicRead/CourseRead/SubtopicRead`.
- Frontend: se mostraba en `CourseShell` (cabecera "N unidades · N subtemas · 7 h 24 min"),
  `CourseOverview` (tarjeta de unidad), `UnitPage` (título y filas de subtema), `SubtopicPage`,
  `StudentDashboard` (tarjeta de curso + "de estudio en total"), `ContentRail` (índice lateral) y
  textos de la landing. Con icono `faClock`, formateadores `formatDuration`/`formatDurationShort`.
- **Lógica**: el progreso/orden NO dependen del tiempo (barra = proporcion de subtemas
  completados; orden por `order` de subtopics). Los minutos solo viajaban para mostrarse.
  En `useCourse.jsx` `totalMinutes/remainingMinutes` eran solo visuales → eliminados limpios;
  la lógica de progreso quedó intacta.
- El importador de Markdown **no** se tocó (compatibilidad conservada en backend).

**c) Repaso y miniquiz**:
- Tablas: `questions` (FK `subtopics.id`; `options` JSON con 4 opciones; `correct_index`;
  `explanation`; `source` [official/ai/teacher]; `status` [approved/pending/rejected/practice];
  `created_by` → users). Respuestas: `question_answers` (califica el SERVIDOR, idempotente por
  `attempt_id` + `question_id`).
- Filtros: repaso del subtema y de la unidad usan **solo `status=approved`**
  (`content_repo.get_approved_questions_by_subtopic/_topic`) con muestreo aleatorio de
  `QUIZ_MAX_QUESTIONS` (10) ordenado por `order`. Los estudiantes ven esos question sets
  (`QuestionRead` SIN correct_index/source/status); el docente ve banco completo
  (`/content/.../bank`, `QuestionTeacherRead`). Las AI `practice` no se califican en intentos.
- "Pregunta banco <hex>": NO está en ningún código/seed de `main` — se crearon por la API del
  banco docente (ver Fase 2/4).

**d) ¿Por qué no veías "Agregar preguntas"?** El botón EXISTÍA pero:
1. Se llamaba **"Agregar pregunta"** (singular) — tu búsqueda no lo encontraba.
2. Vive en la ruta `/teacher/courses/:courseId`, protegida por `ProtectedRoute requiredRole="TEACHER"`
   `frontend/src/App.jsx:76`; solo se llega desde las tarjetas de "Mis cursos" del panel docente
   (`DashboardPage` renderiza `StudentDashboard` si `user.role !== 'TEACHER'`).
3. `user.role` es `TEACHER` (mayúsculas) — si tu correo no está en `TEACHER_EMAILS` al crear la
   cuenta, eres `STUDENT` y toda la ruta redirige a `/dashboard`. Además el login dev
   (`DEV_AUTH_ENABLED=true`) sincroniza el rol con el solicitado.
4. La vista del curso del ESTUDIANTE (`/courses/:id`) no tiene el botón (por diseño), ahí no debía
   estar.
En la Fase 4 el botón se renombró a "Agregar preguntas" y la guía de pruebas ahora documenta rol
+ rutas. El backend ya rechaza a estudiantes con 403 (`assert_teacher_can_manage_subtopic`, y el
test `test_teacher_questions_crud.py` lo cubre).

---

## FASE 1 — Quitar los tiempos (`fccba62`)

Frontend solamente: cabecera del curso ("9 unidades · 26 subtemas"), tarjetas de unidad
("7 subtemas"), filas de subtema (icono reloj/"1h 7m"), índice lateral, dashboard del estudiante y
copy de la landing ya no anuncian minutos. Eliminados `formatDuration/formatDurationShort`
(`curriculum.js`) y `totalMinutes/remainingMinutes` (`useCourse.jsx`). **No se usa en lógica** —
nada más se borró. Alineación revisada: los `Meta` restantes quedan flexibles; build limpio.

---

## FASE 2 — Auditoría (`ad6e4e7`) — SOLO LECTURA en ejecución

- `backend/scripts/audit_questions.py`: conteos por source/status, desglose unidad→subtema,
  y marca sospechosas por: "Pregunta banco"/ids hex, opciones a/b/c/d o ≤2 chars, repetidas,
  `correct_index` fuera de rango, explicación vacía, enunciados duplicados. Escribe
  `docs/auditoria-preguntas.md` (resumen + lista id/enunciado/motivos). **No modifica nada.**
- `backend/scripts/cleanup_placeholder_questions.py`: **dry-run por defecto**; guarda respaldo
  JSON y con `--apply` marca `status=rejected` (borrado suave reversible; no borra filas).
  **No se ejecutó `--apply`.**
- Resultado corrido contra la base local (`insoft-db`): **122 preguntas** (85 oficial/approved,
  32 teacher/approved, 5 ai/practice). **43 sospechosas (35 fuertes)**: 30 "¿Pregunta banco
  XXXXXX?" (opciones a/b/c/d, explicación "porque sí"), 1 "¿Pregunta de humo f916f7?" y 3
  smoke de práctica IA ("¿Práctica smoke N <uuid>?").
- **Origen**: NO hay seed/migración/proceso automático que las cree (`app/seed/seed_questions.py`
  contiene solo el temario real). Fueron creadas vía `POST /api/content/subtopics/{id}/questions`
  por 5 cuentas docentes de prueba (created_by 42,45,47,47,49,51) el 2026-09-30 en ráfaga de
  milisegundos — experimento ad-hoc de carga local (aparece también material similar en el
  script local sin trackear `backend/app/scripts/run_qa_batch.py`, que evalúa /api/ai/ask y no
  crea preguntas). **Propuesta**: no hay nada que desactivar en el repo; solo evitar correr
  estos scripts de prueba contra bases compartidas y limpiar sus restos (ver pasos manuales).
- **¿Las ven estudiantes reales?** SÍ: las 32 teacher están `approved` y el repaso muestrea
  approved del subtema; en "Anatomía del Globo Ocular" hay ~30 de relleno entre 40 → señalaría
  basura en la mayoría del repaso de ese subtema hasta que corras `--apply`.

---

## FASE 3 — Pulido del repaso (`3b46b6c`) (`Quiz.jsx`, sin tocar backend)

- La opción correcta después de fallar YA se resaltaba (`revealed`), pero con tono tenue
  (`border-correct-200`, fondo 60 %): pasó a verde sólido (`border-correct-500 bg-correct-50`),
  mismo tratamiento que "acertada" pero distinguible (la elegida incorrecta sigue roja).
- Recuadro inline "Por qué la respuesta es otra" y el resumen "Preguntas que fallaste" muestran
  ahora **"Esta pregunta aún no tiene explicación."** cuando `explanation` es vacía (caso de las
  questions oficiales de la unidad 9).
- Sin cambios en puntuación ni accesibilidad (se mantiene aria-live/roles).

---

## FASE 4 — Agregar preguntas (`b75c601`) — sin tocar backend

- `TeacherCoursePage.jsx`: botón con texto literal **"Agregar preguntas"** (el gate solo-docente ya
  existía vía `requiredRole="TEACHER"`), abre el asistente con el curso ya cargado.
- `AddQuestionWizard.jsx` reescrito (100 % frontend, reglas iguales al backend):
  - **Un** formulario con selectores dependientes **Unidad → Subtema** siempre visibles.
  - Enunciado (5-500), **4 opciones A-D** con la correcta marcada, explicación opcional.
  - **"Guardar y agregar otra"**: conserva unidad+subtema, limpia enunciado/opciones/correcta/
    explicación, muestra confirmación inline ("Pregunta guardada…", contador de sesión) y
    **devuelve el foco al enunciado**.
  - **"Guardar y salir"**: guarda y cierra (el banco de abajo refresca por `onSaved`).
  - Eliminados el paso-puente "Continuar/Confirmar y guardar" y la pantalla final de éxito
    (no eran parte del flujo deseado).
- Pruebas nuevas: **vitest + testing-library** (no había suite). `npm test` → **10 tests**
  (`questionValidation.test.js`, `AddQuestionWizard.test.jsx` incluyendo conservación de
  unidad/subtema, limpieza y cierre). Build `vite build` ✓ y backend 147/147 ✓ (incluye el
  403 docente/estudiante de `test_teacher_questions_crud.py`).
- Cómo probarlo como docente: sección nueva **"10. Probar 'Agregar preguntas'"** en
  `GUIA_DE_PRUEBAS.md` (`TEACHER_EMAILS`, `DEV_AUTH_ENABLED`, `docker compose up --build`,
  login dev con rol teacher y verificación vía `GET /api/auth/me` → `"role": "TEACHER"`).

---

## FASE 5 — Despliegue (`4c9b393`)

Frontend:
- `api.js` usa **solo** `VITE_API_URL` para todas las llamadas (documentado en
  `frontend/.env.example`, sin secretos). `vercel.json` con la reescritura SPA.
- **SlowServerBanner**: si una petición supera 5 s (backend Render free dormido) muestra
  "El servidor se está despertando, un momento…" (contador por peticiones concurrentes,
  eventos `insoft:api-slow[-end]`).

Backend:
- `Dockerfile` producción: sin reload, `--host 0.0.0.0`, puerto de la variable `PORT`
  (`${PORT:-8000}`).
- `GET /health` sin autenticación — **ya existía** (`app/main.py`, verificado, nada que hacer).
- `DATABASE_URL` del entorno + **SSL automático para Neon** (`sslmode=require`; se activa si el
  host es `neon.tech`, o forzado con `DATABASE_SSL=true`). Documentado en
  `app/database/session.py`: las migraciones (lifespan) usan la URL **directa**; la *pooler* de
  Neon no soporta DDL. **Este repo no usa Alembic**: las migraciones propias
  (`ensure_schema_compatibility` + `create_all` en el arranque) corren **antes** de cada
  despliegue automáticamente (lo pidió la fase; se documentó la diferencia; NO se introdujo
  Alembic nuevo).
- CORS: lista por comas (`BACKEND_CORS_ORIGINS`) + regex que ahora incluye
  `^https://.*\.vercel\.app$` para previews.
- `CREATE EXTENSION IF NOT EXISTS vector` ya corre en migraciones (verificado `migrations.py:46`).
- Escaneo de secretos: **ningún secreto real en el repo ni en working tree** (solo placeholders
  y fakes de tests). `.env` está gitignored. *Alerta*: `SECRET_KEY` por defecto
  `"change-me-in-production"` en `config.py`; en producción o Compose SIEMPRE se debe definir
  por env var (`docker-compose.yml` ya la pasa).

Despliegue como código:
- `render.yaml`: servicio web Docker free, `healthCheckPath=/health`, variables sensibles
  `sync:false`.
- `docker-compose.yml`: YA usa imagen `pgvector/pgvector:pg16`, volumen `postgres_data`,
  healthchecks y `restart: unless-stopped` ✓ (nada por cambiar; única diferencia menor vs. lo
  pedido: uso `unless-stopped` en vez de `always` — más prudente).
- `DEPLOY.md` (español): ruta A Neon+Render+Vercel y ruta B PC+Compose+túnel (Cloudflare /
  Tailscale Funnel / ngrok), variables por servicio, carga inicial (seed automático + rol
  docente + `/teacher/import`), orígenes de Google Cloud, flujo de ramas
  (main=prod, staging=pruebas URL estable, feature/*=previews por PR).
- Workflow GitHub Actions (optional 13): escrito y **deja en disco** en
  `.github/workflows/tests.yml` (untracked, listo para `git add` + push por ti): PAT sin scope
  `workflow` lo bloquea.

---

## Decisiones que tomé (sin confirmación)

1. **Trabajar solo en `INSOFT/`** (no en `INSOFT-deploy/`): es el repo de desarrollo activo en
   carpetas anteriores. `INSOFT-deploy/` no se tocó.
2. **No demoler `api.js`**: conservé el fallback de inferencia de host para el modo Compose/LAN
   (hoy lo usan), obligando `VITE_API_URL` en producción (docs de Vercel). Reversible en 1 línea.
3. **No introducir Alembic**: el repo ya usa migraciones aditivas propias ejecutadas en arranque;
   agregar Alembic era predecible e invasivo. WARN documentado en DEPLOY.md y arriba.
4. **No crear PR**: el PAT no tiene scope; quedan como paso manual (fallaron, no se reintentaron
   en bucle).
5. **`docker-compose`**: `restart: unless-stopped` en vez de `always` (reversible en 1 línea).
6. **Frontend sin flaky-async**: tras guardar, el foco va al enunciado de forma determinista
   (`promptRef.current?.focus()` inmediato, sin re-print).
7. **Fase 2**: respaldo JSON del dry-run se guardó en `docs/` (lo pide la fase) con datos de la
   base LOCAL (no sensibles).
8. **Fase 0d**: la corrección elegida fue renombrar (visibilidad del botón dependía del nombre y
   del rol, no de un bug de montaje). El gating de TEACHER ya era correcto.

## Lo que falló o quedó pendiente

| Ítem | Estado | Solución |
|------|--------|----------|
| PRs via `gh` | falló (PAT sin scope) | abrir a mano al hacer merge (5 ramas en remoto) |
| Push `.github/workflows/tests.yml` | falló (PAT sin scope `workflow`) | el archivo está en el repo local, `git add + commit + push` |
| `cleanup_placeholder_questions.py --apply` | NO ejecutado (regla de la fase) | tú decides (ver pasos manuales) |
| ESLint frontend | no está configurado en el repo | opcional; solo `npm run build` + `npm test` |
| Workflow de la ruta B en Docker | sin probar contra dominio real con túnel | requiere PC del equipo |

## Cómo probar cada fase

1. **Fase 1**: `git checkout chore/quitar-tiempos && cd frontend && npm run build` y navegar el
   curso: cabecera/tarjetas/filas ya no muestran horas. El importador sigue aceptando el campo
   (backend sin tocar).
2. **Fase 2**: `cd backend && .venv/bin/python scripts/audit_questions.py` (lee `DATABASE_URL`
   o --db-url; para la base local:
   `DATABASE_URL='postgresql+psycopg2://oftallearn:****@localhost:5433/oftallearn'`).
   Luego `scripts/cleanup_placeholder_questions.py` (dry-run) y si decide --apply con respaldo.
3. **Fase 3**: entrar a un subtema, fallar un repaso: la correcta queda verde sólida; con
   preguntas de la unidad 9 (sin explicación) se ve el texto de respaldo.
4. **Fase 4**: ver `GUIA_DE_PRUEBAS.md §10`. Unit-level: `cd frontend && npm test`.
5. **Fase 5**: `docs` en DEPLOY.md; local: `npm run build` pasa, banner se activa excediendo
   5 s (parar `docker compose stop backend` mientras el frontend intenta una petición).

---

## Pasos manuales para mí

1. **PRs**: `gh pr create --repo sebasssruizz/INSOFT --base main --head <rama>` para cada rama
   (o merge directo): `chore/quitar-tiempos`, `fix/repaso-ui`, `feat/agregar-preguntas-ajustes`,
   `chore/auditoria-preguntas`, `chore/deploy-config`, `docs/reporte-sesion`.
2. **Workflow de CI**: hace falta un token con scope `workflow`:
   `cd INSOFT && git add .github/workflows/tests.yml && git commit -m "ci(actions): pytest+build en PRs"
   && git push` (el archivo ya está en disco en tu working tree tras esta sesión).
3. **Limpieza del banco**: decidir y, si aceptas limpiar las ~34 filas de relleno:
   ```bash
   cd INSOFT/backend
   set -a && . ../.env && set +a
   DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT:-5433}/${POSTGRES_DB}" \
     .venv/bin/python scripts/cleanup_placeholder_questions.py --apply
   ```
   (respaldo JSON automático en `docs/` antes del cambio).
4. **Rol docente local**: `TEACHER_EMAILS=profesora@correo.com` en `.env` + `docker compose
   down -v && docker compose up --build` (o cambiar rol desde `/perfil`),
   `DEV_AUTH_ENABLED=true` para el login dev.
5. **Cuentas/paneles** (ruta A): crear Neon/Render/Vercel, conectar repo, definir variables de
   los pasos 2-5 y añadir orígenes de Google OAuth; cargar `VITE_GOOGLE_CLIENT_ID` en Vercel
   vía el panel.
6. **Chequeo secreto**: confirmado que no hay secretos en el repo; rotate secretos si los
   pegaste en este archivo o su .env (el detalle está en DEPLOY.md §9).
7. **Revisar capturas** de layout tras quitar tiempos (Fase 1) y del repaso verde (Fase 3):
   son cambios visuales, un par de screenshoots tuyos validan el resultado final.
