# ESTADO DE DESPLIEGUE — rutas GRATIS vs PROD (`feat/deploy-prod` no integrada)

7-oct-2026. **Nada de `feat/deploy-prod` está mergeado** y no se mergea en esta
tarea (decisión: content freezes cruzados). Comparación y plan de integración:

## 1. Lo que ya vive en staging (cubre ruta "gratis/pruebas")

- `DEPLOY.md`, `render.yaml` (Neon+Render+Vercel), `docker-compose.yml` local con
  `name:` fijo, banner "servidor despertando", `vercel.json`.
- Seguridad: dev login cerrado (403), SECRET_KEY requerida, sin tarjeta dev en
  el bundle (PR #15).
- Observabilidad: `/health`, `/ready`, X-Request-ID, logs json + rotación (T5, PR #22).
- Fix de memoria: `EMBEDDINGS_BACKEND=onnx` (T1, PR #19) — imagen 0.78 GB.
- `scripts/smoke_prod.sh` y esta carpeta `docs/despliegue/` (T6, este PR).

## 2. Qué aporta `feat/deploy-prod` (8 commits NO en staging)

| Artefacto | Valor | Riesgo de integración |
|---|---|---|
| `docker-compose.prod.yml` + `deploy/Caddyfile` (HTTPS auto, proxy) | es la forma de producción real** (VM con dominio) | MUY bajo: archivos nuevos |
| `deploy/backup.sh`, `restore.sh`, `crontab`, unidades systemd | backups + restauración probada | Bajo (nuevos) |
| `backend/Dockerfile.prod` + guardas `SEED_MODE` + `test_production_guards.py` | guardas de prod duras | MEDIO: toca `config.py`, `main.py`, `session.py`, `auth_service.py` que esta noche cambió en T3/T5 (main.py request-id + /ready) |
| `docs/DEPLOY_RUNBOOK_DIGITALOCEAN.md` etc. | runbook | Bajo |
| `smoke.sh` propio | redundante con `scripts/smoke_prod.sh` | Quedar con UNO |

## 3. Plan de integración recomendado (después de que los PRs de esta noche entren)

1. Merge a staging los PRs #19–#22 (y #16/#17 si siguen abiertos).
2. Crear rama `chore/integrar-deploy-prod` desde `origin/staging` y
   `git merge origin/feat/deploy-prod` resolviendo:
   - `backend/app/main.py`: conservar ambos (middleware request-id + /ready +
     guardas de prod de la rama).
   - `backend/app/core/config.py`: conservar guardas (SEED_MODE) y añadir
     LOG_LEVEL/LOG_FORMAT/AI_* (T3/T5; EMBEDDINGS_BACKEND de T1).
   - `backend/app/services/auth_service.py`: conservar `ForbiddenError` (403)
     del PR #15 (la rama vieja quizá mantenga 400).
   - `frontend/src/pages/*` y `api.js`: staging ya quitó los tiempos y cambió el
     asistente; mantener staging y revisar si la 3D vieja op `CourseShell` trae
     valores necesarios.
   - `backend/tests/`: traer `test_production_guards.py`, mantener los tests
     nuevos (matriz, robustez, dev-auth).
3. Correr suite + build + `smoke_prod.sh` contra VM local antes de merge.
4. Borrar `smoke.sh` de deploy-prod tras consolidar (solo un smoke).

## 4. Decisiones por si tiempo corto (regla conservadora)

- MVP 15-oct en VM: usar SOLO los archivos NUEVOS de deploy-prod
  (compose.prod + Caddyfile + backups), copiándolos a staging en rama
  `chore/prod-vm-light` sin volver su base de código. Los guardas de prod del
  código escalan a PR de la semana siguiente.
