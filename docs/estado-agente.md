# Estado del trabajo del agente (INSOFT)

Actualizado: 12-oct-2026, ~00:50 (hora local). Fuente: `gh pr list --state all`, ramas remotas y pruebas
de cada rama. Estados: **mergeado** (en staging), **PR abierto** (listo para revisión), **rama sin PR**,
**parcial**, **no iniciado**, **bloqueado**.

Regla de integración: ningún PR se ha mergeado por el agente. Todas las ramas nuevas parten de
`origin/staging` o están apiladas sobre otra (se indica en cada una).

## Ronda 0 · Estado inicial

| Ítem | Estado | Detalle |
|---|---|---|
| Bitácora | hecha | `~/Documentos/INSOFT-evidencias/bitacora-agente.md` (fuera del repo). |
| Árbol de trabajo | limpio | Sin cambios rastreados sin commit al empezar. |
| Stack real (`insoft-db`, `insoft-backend`, `insoft-frontend`) | intacto | No se tocaron volúmenes ni datos. |
| Contenedores de prueba | limpiados | Se eliminaron `sim-torch`, `sim-pg`, `sim-pg2`, `sim-backend` (parados). Volúmenes `sim-pgdata*` no tocados. Otros contenedores `Exited` antiguos no son del agente: se dejaron. |

## Ronda 1 · Cierres pendientes

| Tarea | Estado | Rama | PR | Verificación |
|---|---|---|---|---|
| 1.1 Parche #41 (dos tests dependientes del orden) | PR abierto | `test/aislamiento` | #41 | `test_teacher_questions_crud.py` en 3 semillas; suite completa por lotes 203/203 (semilla 1234). `pytest-randomly` declarado en `requirements-dev.txt`. |
| 1.2 Frontend de producción (ProgressRing accesible, `api.js` sin `:8000`, build exige `VITE_API_URL`, `check-dist`, tests de `api.js`) | PR abierto | `fix/frontend-produccion` | #43 | `npm test` 21/21; build sin `VITE_API_URL` falla; con URL pasa; `dist/` sin `localhost:8000`, `/auth/dev` ni cuentas demo. |
| 1.3 Errores de la API y ejemplos reales | PR abierto | `docs/api-frontend` | #44 | 29 ejemplos generados contra Postgres pgvector desechable, LLM mockeado. |

## Ronda 2 · Listo para pruebas en internet

| Tarea | Estado | Rama | PR | Verificación |
|---|---|---|---|---|
| 2.1 L1 Migraciones versionadas | PR abierto | `feat/migraciones-versionadas` | #45 | SQLite 5/5; PostgreSQL desechable 2/2. |
| 2.2 L2 Semilla segura (`SEED_MODE`) | PR abierto | `fix/semilla-segura` | #46 | 9/9. |
| 2.3 L3 Autenticación endurecida | PR abierto | `feat/auth-endurecido` | #47 | 25/25 con tokens simulados. |
| 2.4 F4 Bootstrap remoto | PR abierto (apilado sobre #45; reemplaza a #37) | `chore/bootstrap-remoto-v2` | #49 | Dry-run, negativas, apply, relanzado y promoción de docente en Postgres desechable. Repo **público**: no se versionó contenido. |
| 2.5 F5b Compose endurecido | PR abierto (reemplaza a #38) | `chore/endurecer-compose` | #48 | `docker compose config --quiet` válido; `DOCS_ENABLED` por defecto `false`. |
| 2.6 Interruptores operativos | PR abierto (apilado sobre #45 y con #46 integrado) | `feat/interruptores-operativos` | #50 | 26/26 (interruptores, semilla, migraciones); IA vecina 66/66. |
| 2.7 Respaldos | PR abierto (apilado sobre #48) | `chore/respaldos` | #51 | Respaldo directo PASA verificación; recuento alterado FALLA; contraseña incorrecta no deja archivo; retención conserva 3. |
| 2.8 Ensayo local tipo Neon (SSL, pgbouncer, arranque en frío, CORS desde otro origen) | **no iniciado** | — | — | Requiere Postgres con SSL, pgbouncer y build de producción servido desde otro origen. Siguiente paso: `chore/ensayo-despliegue-local`. |
| 2.9 F5 Guía de pruebas en internet | PR abierto (reemplaza a #39) | `docs/paso-a-paso-staging-v2` | #52 | Cifras de túneles contrastadas con documentación pública (fechas en el texto). |

## Ronda 3 · Contenido, IA y piloto

| Tarea | Estado | Detalle |
|---|---|---|
| 3.1 L4 Medios por subtema | **no iniciado** | Requiere endpoints de docente, lista blanca de dominios y payload del subtema. |
| 3.2 L5 Validación de contenido | **no iniciado** | Estado borrador/validado por unidad y subtema. |
| 3.3 L6 Unidad 9 y banco de pterigión | **no validado** | Existe PR #27 (abierto, sin revisar). No se importó nada: no hay base desechable preparada para ello. |
| 3.4 L7 Práctica colectiva | **parcial** | Diseño en PR #30 (abierto). Implementación detrás de flag: **no iniciada**. |
| 3.5 L11 Datos del piloto anonimizados | **no iniciado** | Exportes con HMAC, `DELETE /api/users/me`, retención. |
| 3.6 L14 Script de humo del LLM | **no iniciado** | No se ejecuta nada contra el proveedor. |
| 3.7 Evaluación offline de la recuperación | **no iniciado** | Requiere la evaluación sobre las 85 preguntas oficiales. |

## Ronda 4 · Calidad, seguridad y documentación

| Tarea | Estado | Detalle |
|---|---|---|
| 4.1 L8 Recorridos de contrato y OpenAPI | **no iniciado** | |
| 4.2 Informe de pruebas del backend | **no iniciado** | |
| 4.3 L10 Auditoría de seguridad | **no iniciado** | pip-audit, npm audit, bandit y escaneo de secretos aún no ejecutados. |
| 4.4 Índices y consultas | **parcial** | Índice `ai_queries(user_id, created_at)` en la migración 3 (#50). Falta medir con `EXPLAIN` antes y después. |
| 4.5 L12 Datos de demostración | **no iniciado** | |
| 4.6 L8 Carga ligera (#26) | **no validado** | PR #26 abierto, sin rebasar sobre staging. |
| 4.7 L13 Documentación técnica | **parcial** | Hecho: `docs/api/`, `docs/database/`, `docs/operacion/`, `docs/seguridad/`. Falta: diagrama ER en Mermaid, `ARQUITECTURA.md` y `OPERACION.md` completos. |
| 4.8 F9 Cifras de memoria | **no validado** | PR #40 abierto, sin revisar. |
| 4.8 F8 Migrar a `google-genai` | **no iniciado** | |

## Samuel (frontend)

| Ítem | Estado |
|---|---|
| Trabajo "Responsive hecho" (commit `b7dd00c`, solo en `main`) | Integrado en staging (#42, mergeado por ti). |
| Reintroducción de tiempos en `main` | Corregida en staging. `main` **sigue** con 35 referencias: no mergear `main` en `staging`. |
| Barra de progreso accesible | Hecha en #43 (`ProgressRing`). |
| Manejo de 401/403 | Único lugar: `api.js`. Ver `docs/api/ERRORES_PARA_FRONTEND.md`. |
| Trabajo local de Samuel no subido | No verificable desde aquí. |

## Pruebas de control

| Prueba | Resultado |
|---|---|
| `npm test` (rama `fix/frontend-produccion`) | 21/21 |
| `npm run build` (con `VITE_API_URL`) | OK; `check-dist` sin cadenas prohibidas |
| Backend por lotes (rama `test/aislamiento`) | 203/203 |
| Pruebas nuevas en cada PR | Ver tabla de cada ronda |

## Contenedores y procesos

- Contenedores de prueba `tmp-*` creados por el agente: **todos detenidos y eliminados**.
- Contraseñas auxiliares de contenedores de prueba: borradas tras cada uso.
- Stack real: `insoft-db`, `insoft-backend`, `insoft-frontend`, sin cambios.
- Navegador headless y servidores de desarrollo lanzados en la sesión: **detenidos**.
