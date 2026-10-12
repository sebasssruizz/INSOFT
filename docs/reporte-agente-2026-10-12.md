# Reporte del agente · 11–12 oct 2026

Estado detallado por tarea: [`docs/estado-agente.md`](estado-agente.md). Decisiones abiertas:
[`docs/preguntas-pendientes.md`](preguntas-pendientes.md). Bitácora (fuera del repo): `~/Documentos/INSOFT-evidencias/bitacora-agente.md`.

## 1. Resumen

- **Hecho y en PR**: rondas 0 a 2, salvo el ensayo local (2.8). Todo en ramas nuevas, apiladas cuando dependen de otra. **Ningún PR mergeado por el agente.**
- **Pendiente sin empezar**: ensayo local (2.8), rondas 3 (contenido, IA, piloto) y 4 (recorridos, auditoría, carga, datos demo, F8), salvo los parciales marcados.
- **Hallazgos graves corregidos**: el arranque **sobrescribía** contenido editado y **borraba** subtemas (ahora `SEED_MODE`); el JWT **no exigía** expiración; el login de Google **no exigía** correo verificado; `/docs` estaba **abierto por defecto** en código; un respaldo fallido **dejaba un archivo vacío** que parecía válido; el `api.js` podía **apuntar a un host equivocado** en producción.

## 2. Tabla por tarea

| Tarea | Estado | Rama | PR | Pruebas |
|---|---|---|---|---|
| R0 Inventario | hecho | — | — | Stack real intacto. |
| 1.1 #41 orden de tests | PR abierto | `test/aislamiento` | #41 | 203/203 por lotes. |
| 1.2 Frontend producción | PR abierto | `fix/frontend-produccion` | #43 | `npm test` 21/21, build, `check-dist`. |
| 1.3 Errores API y ejemplos | PR abierto | `docs/api-frontend` | #44 | 29 ejemplos reales (PG desechable). |
| 2.1 L1 Migraciones | PR abierto | `feat/migraciones-versionadas` | #45 | SQLite 5/5, PG 2/2. |
| 2.2 L2 Semilla segura | PR abierto | `fix/semilla-segura` | #46 | 9/9. |
| 2.3 L3 Auth endurecido | PR abierto | `feat/auth-endurecido` | #47 | 25/25. |
| 2.4 F4 Bootstrap | PR abierto (sobre #45) | `chore/bootstrap-remoto-v2` | #49 | Dry-run, negativas, apply, idempotencia, docente (PG). |
| 2.5 F5b Compose | PR abierto | `chore/endurecer-compose` | #48 | Compose válido; endpoints públicos medidos. |
| 2.6 Interruptores | PR abierto (sobre #45, con #46) | `feat/interruptores-operativos` | #50 | 26/26; IA vecina 66/66. |
| 2.7 Respaldos | PR abierto (sobre #48) | `chore/respaldos` | #51 | PASA / FALLA comprobados; retención. |
| 2.8 Ensayo local | **no iniciado** | — | — | Ver §6. |
| 2.9 Guía de pruebas | PR abierto | `docs/paso-a-paso-staging-v2` | #52 | Cifras contrastadas con documentación. |
| 3.x Contenido, IA, piloto | **no iniciados** (3.4 parcial: diseño #30) | — | — | — |
| 4.x Calidad y docs | parciales (4.4, 4.7); resto no iniciado | — | — | — |
| 5 Cierre | hecho (este reporte) | `docs/reporte-agente` | este PR | merge-tree (§4). |

## 3. Hallazgos importantes

1. **Semilla destructiva en cada arranque** (`seed_official_content` con `prune=True`). Corregido con `SEED_MODE`. Además, la comparación por número de orden podía **sobrescribir** una unidad importada: ahora se compara por nombre.
2. **JWT sin expiración posible**: `jose` acepta tokens sin `exp`. Ahora se exige `exp` y `sub`, y se fija el algoritmo.
3. **Login de Google sin correo verificado**: se podía vincular una cuenta existente por correo no verificado. Ahora se rechaza.
4. **Migraciones: el orden importaba mal**. Antes las migraciones corrían antes de `create_all`; una migración sobre una tabla nueva se habría registrado sin efecto. Orden fijado.
5. **SQLite no admite** `ADD COLUMN … NOT NULL DEFAULT CURRENT_TIMESTAMP` (el código anterior tenía el mismo límite; no afecta a PostgreSQL).
6. **Límite diario del asistente en SQLite**: `CAST(fecha)` no compara bien. Producción usa PostgreSQL, así que los ejemplos y las migraciones se verificaron allí.
7. **Respaldo que dejaba archivos vacíos** al fallar `pg_dump`. Corregido con una trampa de salida.
8. **El límite de tasa (slowapi) responde `{"error": …}` sin `Retry-After`**: el resto de la API usa `detail`. Documentado; corrección propuesta.
9. **El asistente no devuelve 503/429 ante fallos del proveedor**: responde 200 en modo respaldo. El frontend debe leer `degraded`.
10. **La API sigue exponiendo `estimated_minutes`** (aunque la UI no lo muestre) y dos nombres para el porcentaje de progreso.
11. **Guía de #39**: decía que el interstitial de ngrok solo afectaba sin cabecera; la documentación lo sitúa en el plan Free. Corregido en #52.
12. **Tests dependientes del orden** en `test/aislamiento` (dos más de los conocidos). Parche aplicado en #41.
13. **El `pg_dump`/`pg_restore` del host no existe**: los respaldos y verificaciones corren en contenedores efímeros.
14. **Repo público**: no se versiona contenido de `docs/importacion/`.
15. **Conflicto entre ramas**: solo un par (`interruptores` ↔ `semilla`) en `config.py`. Resuelto en la rama de interruptores.

## 4. Orden de merge recomendado

`git merge-tree` no muestra conflictos entre ninguna rama y `origin/staging`. Entre pares, solo había un conflicto (`interruptores` ↔ `semilla`), ya resuelto.

Orden sugerido (las dependencias van indicadas):

1. **#41** `test/aislamiento` (tests; independiente)
2. **#43** `fix/frontend-produccion` (independiente; toca `docker-compose.yml` con el mismo cambio que #48)
3. **#44** `docs/api-frontend` (solo docs y script)
4. **#45** `feat/migraciones-versionadas` (base de #49 y #50)
5. **#46** `fix/semilla-segura`
6. **#47** `feat/auth-endurecido`
7. **#48** `chore/endurecer-compose` (base de #51)
8. **#49** `chore/bootstrap-remoto-v2` (requiere #45; reemplaza a #37)
9. **#50** `feat/interruptores-operativos` (requiere #45; incluye #46)
10. **#51** `chore/respaldos` (requiere #48)
11. **#52** `docs/paso-a-paso-staging-v2` (reemplaza a #39)
12. Cerrar **#37, #38 y #39** cuando se mergeen #49, #48 y #52 (ya comentadas como reemplazadas).

PRs anteriores abiertos sin revisar: **#23** (despliegue consolidado), **#26** (carga ligera), **#27** (banco de pterigión), **#30** (diseño de práctica colectiva), **#31** (reporte de la noche), **#40** (cifras de memoria). Conviene revisarlos antes de mezclarlos.

## 5. Decisiones que tomé (por defecto)

Las decisiones con alternativa están en `docs/preguntas-pendientes.md`. Principales:

- `SEED_MODE=if_empty` fuera de desarrollo. El arranque no modifica contenido existente.
- Modo respaldo del asistente (200 `degraded`) en vez de error cuando la IA está apagada o agotada, si hay fragmentos.
- El tope global cuenta **llamadas**, no créditos. Sin tope por defecto.
- `ProgressRing` se hizo accesible; `ProgressBar` sigue sin usarse (no se eliminó).
- Compose local con `ALLOW_LOCAL_API=1`; el build de Vercel exige `VITE_API_URL` y rechaza `localhost`.
- `DOCS_ENABLED=false` también en el código.
- `VITE_DEV_AUTH` eliminado: el acceso de desarrollo solo existe con `import.meta.env.DEV`.
- Repositorio público: no se versiona material de la docente.

## 6. No hecho y por qué

- **2.8 Ensayo local tipo Neon**: requiere Postgres con SSL, un pgbouncer y el build de producción servido desde otro origen. No se empezó para no bloquear el resto; es el siguiente paso natural.
- **Rondas 3 y 4**: son funcionalidades completas (medios, validación de contenido, piloto anonimizado, práctica colectiva, recorridos de contrato, auditoría de seguridad, carga ligera, datos demo, migración de `google-genai`). Cada una necesita su propia rama, pruebas y revisión. Ninguna se hizo a medias.
- **Ejecuciones con `--apply`** contra Neon o el PC: no se ejecutaron. Solo se probaron en Postgres desechable.
- **Llamadas reales** a la IA, Google, Vercel o Neon: no se hicieron.

## 7. Pasos manuales para ti

1. **Revisar y mergear** los PRs en el orden de la §4. El agente no mergea.
2. **Cerrar #37, #38 y #39** después de mergear sus reemplazos.
3. **Neon**: crear o usar el proyecto de pruebas; activar la extensión `vector`; guardar las cadenas directa y agrupada en tu gestor de secretos. **Antes del primer arranque con migraciones nuevas, hacer un respaldo** (`docs/operacion/RESPALDOS.md`).
4. **Bootstrap en Neon** (manual, con dry-run primero): `python -m app.scripts.bootstrap_remote` y luego `--apply --confirm-host <host completo>`.
5. **Vercel**: Root Directory `frontend`; Production Branch `staging`; variables `VITE_API_URL` (obligatoria) y `VITE_GOOGLE_CLIENT_ID`.
6. **Túnel**: elegir uno (§5 de la guía). Para Funnel: `tailscale funnel --bg --https=443 3000` y `--https=8443 8000`; aprobar el atributo `funnel` en la política.
7. **Google Cloud**: credencial de tipo **aplicación web**; orígenes de JavaScript exactos (Vercel y, si aplica, el túnel).
8. **PC**: `.env` con `POSTGRES_PASSWORD`, `SECRET_KEY`, `BACKEND_CORS_ORIGINS`, `DOCS_ENABLED=false`, `DEV_AUTH_ENABLED=false`. Arrancar con `docker compose up -d --build`.
9. **Respaldos**: decidir destino y programar cron o systemd (ejemplos en el doc, sin instalar).
10. **Samuel**: pedirle que rebase sobre staging antes de seguir (su commit en `main` reintroduce tiempos). Entregarle `docs/api/ERRORES_PARA_FRONTEND.md` y `docs/reporte-sync-samuel.md`.
11. **Responder** a las preguntas de `docs/preguntas-pendientes.md`, sobre todo la 1 (túnel) y la 5 (número del tope).

## 8. Riesgos

- Un **merge de `main` en `staging`** traería de vuelta los tiempos de la UI. No hacerlo sin antes corregir `main`.
- **La migración sobre Neon** es aditiva, pero no se ha probado contra una copia de la base real. Hacer respaldo y probar en una copia primero.
- **El acceso de desarrollo** queda fuera del build de producción, pero `/auth/dev` sigue siendo un endpoint del backend (responde 403 sin `DEV_AUTH_ENABLED`).
- **Tope de IA** sin valor configurado: sin límite de gasto hasta que se fije `AI_GLOBAL_DAILY_CALLS`.
- **Tailscale Funnel está en beta** según su documentación.
- **Datos personales**: los respaldos y los `.meta` contienen datos de estudiantes; tratarlos como sensibles.
- Varias **pruebas de la suite dependen del orden** en ramas que aún no están en staging. Hasta mergear #41, la suite de staging puede fallar con algunas semillas.

## 9. Verificación de entorno

- Contenedores de prueba creados por el agente: todos eliminados.
- Stack real (`insoft-db`, `insoft-backend`, `insoft-frontend`): sin cambios.
- Volúmenes: ninguno eliminado ni modificado. `insoft_postgres_data` no se leyó ni se modificó: todos los respaldos y pruebas usaron bases desechables.
- Procesos del agente (servidores, navegador de pruebas): detenidos.
- Árbol de trabajo del usuario (`INSOFT-deploy` y el repositorio principal): sin archivos no rastreados tocados.
