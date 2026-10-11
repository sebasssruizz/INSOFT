# Reporte: sincronización del trabajo de Samuel (frontend) a staging

Fecha: 10-oct-2026 · Rama: `chore/sync-samuel` (desde `origin/staging`) · Destino: PR a `staging` (no se mergea)

## 1. Resumen

- El único trabajo de Samuel subido a un remoto es **`b7dd00c` "Responsive hecho"** (8-oct, 25 archivos, +2053/-555), commiteado **directo en `main`**. No hay PRs ni otras ramas suyas.
- Su contenido **ya estaba en `staging`** desde el 9-oct (`2f413c0`, un commit de un solo padre que reaplicó su diff). Lo que faltaba era solo la genealogía: `main` tenía `b7dd00c` y `staging` no.
- Al integrar con `origin/main`, aparecieron **7 bloques de conflicto en 3 archivos**, todos porque Samuel **reintroducía tiempos y duraciones** en la interfaz (regla de staging: cero tiempos). Se resolvió a favor de staging. El árbol final es idéntico a `origin/staging`.
- `main` contiene **35 referencias de tiempo en la UI** (`formatDuration`, `estimated_minutes`, `faClock`, "tiempo estimado"); `staging` tiene **0** (la única coincidencia es un comentario CSS). **No se debe fusionar `main` en `staging` tal cual.**
- Verificado: `npm test` 10/10, `npm run build` OK, capturas responsive en 360/390/768/1024/1280 sin desborde horizontal, y bundle de producción sin la tarjeta de acceso de desarrollo.
- Pendiente de decisión: la sesión de Samuel que menciona manejo 401/403 **no está en ningún remoto**.

## 2. Estado de ramas y commits (desde 8-oct)

| Elemento | Estado |
|---|---|
| `origin/main` | `b7dd00c` (Samuel) es el último commit de Samuel. Divergencia: `staging` tiene 51 commits que `main` no; `main` tiene 1 que `staging` no (`b7dd00c`). |
| `origin/staging` | Contiene el contenido de Samuel (vía `2f413c0`) y todas las reglas posteriores (sin tiempos, verde sólido en la respuesta correcta, 4 opciones). |
| Ramas de Samuel en remoto | Ninguna. `gh pr list --state all` no muestra PRs de Samuel (todos los PRs son de la cuenta `sebasssruizz`). |
| Trabajo de Samuel no subido | No verificable desde aquí. Si tiene cambios locales (p. ej. 401/403), no están en ningún remoto. |
| Commits de Sebastián desde 8-oct | Trabajo de test (`da4827f`, PR #41 abierto), despliegue y documentación (PRs #35–#41). |

## 3. Trabajo de Samuel: qué cambió

Commit `b7dd00c` "Responsive hecho" (autor Samuel Muñiz):

| Archivo | Cambio | Riesgo | Cumple reglas |
|---|---|---|---|
| `DESIGN.md` | +62/-5, documentación de diseño | Bajo | Sí |
| `frontend/package.json` (+lock) | Añade `gsap@^3.15.0` | Bajo, justificado (animación de `Timeline`) | Sí |
| `App.jsx` | +8/-1, ajustes de shell | Bajo | Sí |
| `components/Layout.jsx` | +84/-19, navegación responsive (menú hamburguesa) | Medio: revisar en móvil | Sí (validado en capturas) |
| `components/course/ContentRail.jsx` | Muestra duración por tema/subtema | **Alto: tiempos en UI** | **No en `main`; corregido en staging** |
| `components/course/Quiz.jsx` | Verde suave en respuesta correcta | Bajo (conflicto resuelto a favor del verde sólido de staging) | Sí |
| `components/course/PracticeQuiz.jsx` | Ajustes menores | Bajo | Sí |
| `components/teacher/QuestionBank.jsx` | Ajustes de layout | Bajo | Sí |
| `components/ui/Button.jsx` | Estilos | Bajo | Sí |
| `components/ui/EyeLoader.jsx` (nuevo) | Loader animado del ojo | Bajo (125 líneas) | Sí |
| `components/ui/IrisMark.jsx` (nuevo) | Logo SVG | Bajo | Sí |
| `components/ui/Progress.jsx` | Barra y anillo de progreso | Medio: ver sección 5 | Sí |
| `components/ui/Timeline.jsx` (nuevo) | Línea de tiempo animada con gsap (348 líneas) | Medio: añade gsap | Sí (solo animación, sin tiempos) |
| `index.css`, `tailwind.config.js` | Tokens y utilidades | Bajo | Sí |
| `lib/curriculum.js` | `formatDuration` / `formatDurationShort` | **Alto: helpers de tiempo** | **No en `main`; eliminado en staging** |
| `pages/LandingPage.jsx` | Rediseño (+587/-160) con textos de tiempo | **Alto: "tiempo estimado" en 2 textos** | **No en `main`; corregido en staging** |
| `pages/StudentDashboard.jsx` | Rediseño (+378/-158) con duración de lectura y `faClock` | **Alto: 4 bloques de tiempo** | **No en `main`; corregido en staging** |
| `pages/TeacherDashboard.jsx` | Rediseño (+139/-133) | Medio | Sí |
| `pages/TeacherCoursePage.jsx` | +32/-26 | Bajo | Sí |
| `pages/NotFoundPage.jsx` | Rediseño 404 | Bajo | Sí |
| `pages/InteractiveViewPage.jsx`, `pages/course/CourseShell.jsx`, `pages/course/SubtopicPage.jsx` | Ajustes menores | Bajo | Sí |

Notas de la auditoría del diff:
- **Sin** `console.log`, claves, tokens ni binarios nuevos (solo SVG/JSX/CSS).
- **Lógica de roles**: sin cambios.
- **Dependencia nueva**: `gsap` (justificada). Las dependencias de test (`vitest`, `@testing-library/*`, `jsdom`) vienen de staging, no de Samuel.
- **Fetch**: `fetch` crudo solo dentro de `services/api.js` (implementación de `apiFetch`).

## 4. Integración en `chore/sync-samuel`

- Merge de `origin/main` en `origin/staging`-based branch. 3 archivos en conflicto:
  - `Quiz.jsx`: se conserva el verde sólido de PR #10 (staging).
  - `LandingPage.jsx`: 2 bloques, se conserva el texto sin tiempos (staging).
  - `StudentDashboard.jsx`: 4 bloques, se conserva el texto y los imports sin tiempos (staging).
- Resultado: `git diff origin/staging HEAD` **vacío** (sin cambios de contenido respecto a staging).
- La rama aporta solo la genealogía del merge y este reporte.

## 5. Barra de progreso y accesibilidad

- **Fuente del dato**: subtemas completados, no tiempo. Backend `course_service._student_course_summary`: `completed / total * 100` sobre subtemas. Frontend: `course.progress_percentage` y `totals.completed / totals.subtopics`. **Cumple.**
- **Accesibilidad**:
  - `ProgressBar` (`components/ui/Progress.jsx`) tiene `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`. **Pero no se usa en ninguna pantalla** (código muerto).
  - La barra que el usuario ve (`ProgressRing`, en panel de estudiante y "Tu avance") usa un `<svg aria-hidden="true">` sin `role` ni nombre. La información sí llega como texto visible ("0 de 26 subtemas completados"), pero un lector de pantalla no anuncia el porcentaje como progreso.
  - **Recomendación**: añadir `role="progressbar"`, `aria-valuenow/min/max` y `aria-label` a `ProgressRing`, o reutilizar `ProgressBar`.

## 6. Errores 401/403

- **401**: un único lugar, `services/api.js` (`apiFetch`): si la respuesta es 401, limpia la sesión (`session.clear()`) y redirige a `/`. No hay duplicación.
- **403**: manejo contextual por componente (p. ej. `PracticeQuiz`: "No tienes acceso a la práctica de este tema.", `QuestionBank`). Es razonable porque un 403 no siempre significa sesión vencida.
- **Banner de servidor lento**: usa `notifySlowCount` en el mismo `api.js`, en un contador separado. **No hay choque** con el manejo de 401.
- **Lo que dijo Samuel**: su commit en `main` **no toca `services/`**. El manejo de 401 ya existía antes de su trabajo. Si tiene un cambio adicional de 401/403 para Vercel, no está en ningún remoto.
- **Recomendación**: mantener el 401 centralizado en `api.js`. No hace falta unificar el 403, pero sí conviene un helper que mapee códigos a mensajes para no repetir strings.

## 7. Responsive (verificación visual y medida)

Método: Chromium headless (con WebGL por software) contra el frontend de staging (`vite dev`) y backend desechable (SQLite temporal, sin APIs externas, sin tocar la base real). Viewport a 360, 390, 768, 1024 y 1280 px.

| Pantalla | 360 | 390 | 768 | 1024 | 1280 | Desborde horizontal (medido) |
|---|---|---|---|---|---|---|
| Login | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px en todos los anchos |
| Landing | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Panel de estudiante | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Curso | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Unidad | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Subtema | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Quiz de unidad / repaso | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Vista 3D (instrucciones) | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Panel de docente | ✓ | ✓ | ✓ | ✓ | ✓ | 0 px |
| Asistente de preguntas (wizard) | ✓ | — | — | — | ✓ | Verificado en 360 y 1280 |
| Chat (asistente de IA) | ✓ | — | — | — | ✓ | Verificado en 360 y 1280 |

- Los valores de `-15` en 1024 y 1280 son la barra de scroll, no desborde.
- Capturas (49 PNG): `/tmp/opencode/shots-sync/` (no se commitean por ser binarios).
- Observaciones visuales:
  - A 360 px el panel de chat cubre buena parte de la pantalla (es un overlay; revisar si es el comportamiento deseado).
  - El botón flotante del chat se superpone al contenido inferior en móvil.
  - El wizard "Agregar preguntas" muestra exactamente **4 opciones A–D** (cumple la regla).
  - El panel de docente muestra el código de acceso y el estado vacío "Nadie se ha unido todavía" correctamente.

## 8. Verificaciones ejecutadas

| Comando | Resultado |
|---|---|
| `npm test` | 10/10 (2 archivos) |
| `npm run build` | OK, 9.7 s. Aviso de chunk >500 kB (preexistente; three.js va separado). Bundle principal 474 kB (135 kB gzip). |
| Bundle de producción | `"Acceso de desarrollo"` **0 coincidencias** (tarjeta fuera del build). `/auth/dev` sigue en el JS (función no alcanzable desde la UI). `localhost:8000` aparece como fallback en `api.js`. |
| `pytest` backend (staging, orden aleatorio) | 202 passed, 1 failed (`test_composition_reuses_pool_without_llm`, dependencia de orden ya documentada en PR #41). |
| `pytest` backend (`test/aislamiento` = PR #41, semilla 1234) | 203 passed (con parche de la sección 9). Sin parche: 1 falla (`test_bank_devuelve_todos_los_estados`). |

## 9. Hallazgos en la suite (fuera del alcance de Samuel)

En `test/aislamiento` (PR #41, aún no mergeado) quedan **dos tests con dependencia de orden** que no se habían detectado:

1. `test_bank_devuelve_todos_los_estados` asume que otro test creó una pregunta docente (`TEACHER in sources`). Falla si se ejecuta aislado o primero.
2. `test_pregunta_creada_visible_en_quiz` no fija `QUIZ_MAX_QUESTIONS`, así que el muestreo puede excluir la pregunta (intermitente). `test_review_aprobar_hace_visible` ya tenía este parche.

Ambos se corrigieron en un worktree temporal (sin commit en `test/aislamiento`). El parche está en `/tmp/opencode/fix-crud-order.patch` (30 líneas). Verificado: archivo completo verde con semillas 1–6 y suite completa 203/203 con semilla 1234. **Decisión pendiente**: aplicarlo a `test/aislamiento` (PR #41) o en una rama nueva.

## 10. No verificado

- Dispositivos físicos reales (solo emulación de viewport con Chromium).
- Despliegue real en Vercel; 401 con sesión vencida en producción.
- Google OAuth y flujo real de login.
- Trabajo local no subido de Samuel (401/403 "para Vercel").
- Accesibilidad con herramienta automática (axe) y navegación por teclado.
- Rendimiento en red móvil (chunk principal >500 kB).
- Base de datos real (`insoft_postgres_data`): no se tocó; las pruebas usaron SQLite temporal.

## 11. Recomendaciones para Samuel

1. **Rebasar sobre `staging`** antes de seguir: su commit en `main` reintroduce tiempos (35 referencias). Cualquier merge de `main` a `staging` los traería de vuelta.
2. Quitar las duraciones de `ContentRail`, `LandingPage`, `StudentDashboard`, `curriculum.js` (ya eliminadas en staging, usar esa versión).
3. Hacer accesible la barra de progreso del panel: `role="progressbar"`, `aria-valuenow/min/max` y `aria-label` en `ProgressRing`, o usar `ProgressBar`. Eliminar `ProgressBar` si no se usa.
4. Si tiene cambios de 401/403 para Vercel, **subirlos a una rama** y abrir PR a staging. Hoy no existen en el remoto.
5. Mantener el manejo de 401 en `api.js`; los componentes solo deben manejar 403 contextual.
6. Verificar en un móvil real el overlay del chat (360 px).

## 12. Ajustes para el equipo (no de Samuel)

- `api.js`: quitar el fallback a `:8000` del mismo host y el literal `localhost:8000`. Si falta `VITE_API_URL` en Vercel, debe fallar de forma explícita y no apuntar a un host equivocado.
- Excluir `/auth/dev` del bundle de producción (igual que la tarjeta), o confirmar que el backend lo rechaza fuera de desarrollo (ya lo hace con `DEV_AUTH_ENABLED=false`).
- Aplicar el parche de la sección 9 a PR #41.
- Considerar carga diferida de `LandingPage` y `Timeline` para bajar el chunk principal.
