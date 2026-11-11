# REPORTE DE LA NOCHE — 7-oct-2026 (T0–T12)

Repo `sebasssruizz/INSOFT` · todas las ramas desde `origin/staging` actualizado;
**no se hizo push a main ni staging**; los PRs quedan ABIERTOS (los PRs NO se mergean
nuevos merges por decisión del equipo). Suite total al cierre: **157 tests**.

## Resumen por tarea

| Tarea | Rama | PR | Pruebas | Estado |
|---|---|---|---|---|
| T0 estado/plan | `docs/estado-vs-plan` | **#18** | docs | ✔ |
| T1 memoria embeddings | `perf/memoria-embeddings` | **#19** | 153 backend + build OK | ✔ (medido e implementado) |
| T2 matriz de roles | `test/matriz-roles` | **#20** | 178→157 después: OK, + fixes | ✔ (2 huecos corregidos) |
| T3 robustez IA | `feat/ia-robustez` | **#21** | 158 backend (7 nuevos mocks) + build | ✔ |
| T5 observabilidad | `chore/observabilidad` | **#22** | +5 tests (/ready, request-id) | ✔ |
| T6 despliegue | `chore/despliegue-consolidado` | **#23** | smoke script ejecutado local | ✔ (plan deploy-prod documentado) |
| T4 generador | `feat/generador-robusto` | **#24** | +4 ciclo completo con mocks | ✔ |
| T7 cuentas piloto | `feat/carga-cuentas-piloto` | **#25** | +idempotencia en SQLite | ✔ |
| T8 carga ligera | `test/carga-ligera` | **#26** | informe p50/p95 de stack desechable | ✔ (destruido al final) |
| T9 contenido pendiente | `chore/contenido-pendientes` | **#27** | (no toca BD real) | ✔ (80 preguntas abiertas listadas) |
| T10 docs piloto | `docs/piloto` | **#28** | +1 scorer SUS | ✔ (aviso legal = borrador) |
| T11 enlaces finales | `docs/enlaces-finales` | **#29** | docs | ✔ (tablero sin scope 'project') |
| T12 práctica colectiva | `docs/practica-colectiva` | **#30** | docs (flag apagado) | ✔ diseño; NO implemento |

Detalle de commits por rama: ver los PR (1–3 commits pequeños cada uno).

## Hallazgos de T0 (estado vs plan)

- Todas las ramas de funcionalidad viejas ya están integradas en staging:
  `preguntas-ia-banco`, `estadisticas-intentos-quiz`, `practica-y-agregar-pregunta`,
  `contenido-unidades-restantes` con 0 commits únicos.
- **`feat/deploy-prod` NO integrado** (8 commits: compose prod con Caddy, backups
  `backup.sh`/`restore.sh` probados, runbook DigitalOcean, guardas SEED_MODE y
  smoke). Plan de integración documentado en
  `docs/despliegue/ESTADO_DESPLIEGUE.md` con áreas de conflicto concretas
  (`main.py`, `config.py`, `auth_service.py`) y opción "prod-VM-light" para
  tiempo corto.
- `stash@{0}`: WIP de estadísticas IA sobre el main de mediados de sept (+744 líneas). Probablemente obsoleto por el PR de estadísticas ya integrado; no se
  aplicó. Revisar con Sebastián antes de soltar (`drop`).
- Plan real: `docs/PLAN_REV_2_SEMANAS.txt` + cronograma 8–30 oct por responsable
  en `docs/plan/ESTADO_VS_PLAN.md`.

## Hallazgos de T1 (memoria/RAG en plan gratis)

| Métrica | torch (actual) | **onnx/fastembed** |
|---|---|---|
| RAM tras modelo cargado | 1121 MB | **666 MB** |
| Imagen | 3,57 GB | **0,78 GB** (−78 %) |
| 20 embeds | 21,8 s (con carga) | **0,17 s** |
| top-1/top-3 (165 preguntas etiquetadas) | 29,7 % / 57,6 % | 29,7 % / **58,8 %** |
| Cosine torch↔onnx mismo texto | — | **1.0000** (sin reindexado) |

Decisiones: implementado `EMBEDDINGS_BACKEND=torch|onnx` (por defecto torch),
`requirements-onnx.txt` (sin torch) y Dockerfile condicional por build-arg.
Ningún plan gratis (Render 512 MB, Railway 512 MB) sostiene el backend con el
modelo cargado (y son MAX 0.67 GB): **para producción recomendamos VM ≥ 1 GB
($6/mes DO) o el PC del equipo + túnel (gratis)**. Detalle: `docs/perf/INFORME_MEMORIA.md`.
Potion descartada: 256 dims ≠ 384 → obligaría a reindexar (riesgo alto).
Embeddings por API externa: solo diseño (EMBEDDINGS_PROVIDER como idea en
informe); no implementado.

## Hallazgos de T2 (matriz de roles)

47 combinaciones (5 sujetos × ~26 endpoints) en `backend/tests/test_role_matrix.py`.

- **Hueco corregido 1**: `POST /api/rag/search` global (sin curso/subtema)
  buscaba sobre TODO el índice para cualquier usuario; ahora se acota a los
  cursos con acceso del usuario (el impacto actual es bajo porque todo
  estudiante queda en el Curso General, pero evita fugas si se deshabilitan
  unidades o se quita el auto-enroll).
- **Hueco corregido 2**: chunks duplicados en esa búsqueda (DISTINCT).
- Verificado: quiz/práctica se rigen por subtema compartido (diseño).
- Dahé `PATCH /api/users/me/role` permite cambiar el ROL PROPIO (200) —
  decisión a validar ANTES del piloto: quitarlo o protegerlo con env
  (recomendado que se pida confirmación legal/directiva).
- Endpoints SIN autenticación: no surgió ninguno excepto `/health` (ok).

## Administración de T3 (asistente robusto, todo con mocks)

- Cadena `AI_MODEL_CHAIN` (csv) con respaldo; backoff exponencial+jitter por
  modelo; timeout configurable; 402→`OpenRouterQuotaError` corta cadena al
  instante (502→503 estables). 429→HTTP 429 con `Retry-After`.
- Circuit breaker (`AI_CB_THRESHOLD/COOLDOWN`): al abrir, devuelve 503 respetando cooldown
  sin martillar al proveedor.
- Tope diario por usuario (`AI_DAILY_LIMIT_PER_USER`, 429 con Retry-After) y
  semáforo global de concurrencia (503 rápido).
- **modo degradado** con chunks oficiales `[MODO RESPALDO]` (ai_queries.status
  degraded / ok); sin chunks y sin IA → 503 limpio (sin stacktrace).
- Inyección: system defiende y el CONTEXTO está delimitado; el fallo del
  agarante va capturado por tests (7 nuevos).
- Frontend: widget con estilk degradado y errores claros con Retry-After.

## Notas T7 (cuentas) y T8 (carga)

- Importador del piloto: idempotente, dry-run default, `--apply` explícito
  (NO ejecutado), sin correos: el PRIMER login de Google enlaza la cuenta por
  EMAIL al usuario pre-creado (`docs/piloto/GUIA_CARGA_CUENTAS.md`).
- Carga: 60 usuarios simultáneos contra stack desechable con p95 ≤ 1 s y
  0 errores; recomendación de tamaño de VM 1–2 GB RAM/1 vCPU
  (`docs/perf/INFORME_CARGA.md`). Stack del test destruido.

## Decisiones que tomé sin preguntar (regla 7)

1. `EMBEDDINGS_BACKEND` default queda `torch` (cero comportamiento) —
   activar ONNX es una build-arg; solo lo recomiendo para prod.
2. Inner patch de `PATCH /api/users/me/role` APARCADO (se reporta) — tocarlo
   en la noche podría bloquear los flujos del docente.
3. No integré `feat/deploy-prod` ni borré el stash (no sabía si sobrevive algo
   del viejo chat de estadísticas).
4. Eliminé archivos `.env`-relacionados del loadtest stack local (desechable).
5. Adelanté el seeding de la unidad 9 (en `staging` ya está); solo listé el
   banco pterigión abierto (nada inventado).

## Fallas / pendientes

| Ítem | Estado |
|---|---|
| `read:project` de gh | falta: no puedo leer el tablero (T11; pasos en docs/ENLACES_FINALES.md) |
|Tabla (movimientos del tablero | pendiente del paso previos |
| `feat/deploy-prod` integration | propuesto (post PRs #19–#22) |
| Correo de contacto del aviso legal | POR COMPLETAR (Sebastián/Claudia) |
| Cargar CSV real del piloto | `--apply` manual cuando la docente envía correos |
| stash@{0} | decidir drop (con Sebastián) |

## Pasos manuales para mí

1. **PRs**: revisar y merge #18–#30 en el orden propuesto (abajo). Ningún push
   a staging/main se inventado: solo las ramas.
2. **Dominio + HTTPS**: con `feat/deploy-prod` (compose.prod + Caddy): dominio
   real, DNS, `SECRET_KEY`, `DEV_AUTH_ENABLED=false`, CORS, correo OAuth.
3. **Backups**: `deploy/backup.sh` + crontab y probar `restore.sh` (evidencia).
4. **Piloto**: correr `import_pilot_users.py --code OFT-XXXX --apply` con el
   CSV real de Claudia; validar los primeros logins.
5. **SUS**: guardar respuestas del CSV y correr `scripts/score_sus.py`.
6. **Tablero gh**: habilitar scope `read:project` para completo `T11`.
7. Correo de contacto real en `AVISO_DATOS_PERSONALES.md` + comunicación legal.
8. `DROP` del stash tras revisión (sugerido una vez cerrado el curso IA stats).

## Orden de merge propuesto (verificado con merge-tree)

El único choque real (merge-tree) es `feat/ia-robustez` + `test/carga-ligera`
(ambos tocan `ai_service.py` para AI_MOCK/Semaforo). Todo lo demás cruza limpio.

1. `docs/estado-vs-plan` (#18) — docs puros
2. `docs/practica-colectiva` (#30), `docs/piloto` (#28), `docs/enlaces-finales` (#29), `chore/contenido-pendientes` (#27) — docs
3. `test/matriz-roles` (#20) — tiene fix(rag) + test
4. `perf/memoria-embeddings` (#19) — embeddings + imagen
5. `feat/ia-robustez` (#21) — primero los cambios de ia_service
6. `chore/observabilidad` (#22) — logs/ready (independiente)
7. `feat/generador-robusto` (#24) — dedupe en ai_service (limpio sobre #5)
8. `feat/carga-cuentas-piloto` (#25) — script nuevo
9. `test/carga-ligera` (#26) — resolver el conflicto pequeño en `ai_service.py`
   (AI_MOCK además del semáforo/diario): ~10 líneas manuales + suite.
10. `chore/despliegue-consolidado` (#23) — docs de despliegue (último).

## Cómo probar cada cosa

- Matriz de roles: `cd backend && .venv/bin/python -m pytest tests/test_role_matrix.py -q`
- Robustez IA con mocks: `pytest tests/test_ai_robustez.py -q` (sin red).
- Degradado real: apagar `OPENROUTER_API_KEY` del entorno, y `/api/ai/ask`
  devuelve 200 con "[MODO RESPALDO]" si el subtema tiene chunks.
- Memoria: ` docker build --build-arg EMBEDDINGS_BACKEND=onnx -t insoft-backend ./backend`
  y arrancar con `EMBEDDINGS_BACKEND=onnx` (rss ~0.67 GB, imagen 0.78 GB).
- Carga: seguir `docs/perf/INFORME_CARGA.md` (compose desechable en /tmp).
- Piloto: la guía `docs/piloto/GUIA_CARGA_CUENTAS.md` (dry-run → `--apply`).
- Smoke de producción: `bash scripts/smoke_prod.sh https://dominio`.
- SUS: `python scripts/score_sus.py respuestas.csv`.

## Preguntas para el equipo/docente

1. ¿Retiramos/desactivamos `PATCH /api/users/me/role` para producción?
2. ¿Todo el contenido de Claude la unidad 9 quedará en seed (duplicate la
   importación de créditos)? ¿Consumar qué porcentajes del banco pterigión
   pasan a opción múltiple (60/80?) y quiénes lo transcriben?
3. ¿El aviso de datos se revisa con Bienestar antes del 16-oct? (URL y correo
   de contacto por completar).
4. ¿Alguien sobra el scope `read:project` para GitHub Projects (tablero)?
5. ¿La rama `feat/deploy-prod` integra después de los PRs de esta noche o
   copiamos "prod-VM-light"?
