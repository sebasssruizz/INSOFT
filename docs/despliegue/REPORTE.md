# REPORTE — Despliegue de producción de INSOFT (listo para VM)

Fecha: 2026-10-03 · Rama: `feat/deploy-prod` (merge normal con
`feat/contenido-unidades-restantes` para incorporar la unidad 9 rehecha).
Incluye la corrección posterior de la unidad 9 (texto rehecho, sin preguntas
nuevas ni banco docente; sus 11 preguntas intactas y seed sincronizado).

## 1. Qué se construyó

| Archivo | Función |
|---|---|
| `docker-compose.prod.yml` | stack de producción: db (sin puertos), backend, frontend nginx, caddy (80/443); red interna, volúmenes nombrados `*_prod`, healthchecks, límites de memoria, logs con rotación 10m×3 |
| `backend/Dockerfile.prod` | python-slim + torch CPU + usuario no-root + modelo embeddings precargado en build + HEALTHCHECK + uvicorn con `--workers WEB_CONCURRENCY --proxy-headers --forwarded-allow-ips` |
| `frontend/Dockerfile.prod` + `frontend/nginx.prod.conf` | build Vite (`VITE_API_URL=/` = rutas relativas) → nginx **sin privilegios** en 8080, SPA fallback, gzip, caché 30d para assets con hash (.glb incluidos), `no-cache` para index.html, cabeceras de seguridad |
| `deploy/Caddyfile` | HTTPS automático por `DOMAIN` (Let's Encrypt; `localhost` → cert interno), HSTS, gzip, límite 10MB, logs JSON a stdout; enruta `/api/*` y `/health` al backend, el resto al frontend |
| `.env.prod.example` | todas las variables documentadas con cómo generar secretos |
| `deploy/smoke.sh` | verificación sin LLM apuntando a cualquier URL (9 comprobaciones) |
| `deploy/backup.sh` | `pg_dump -Fc` + sha256, retención 7 diarios + 4 semanales, `rclone` opcional a Spaces/B2 con aviso si falta |
| `deploy/restore.sh` | verificación de hash, BD previa renombrada (no destructiva), `pg_restore` con conteos |
| `deploy/insoft-backup.{service,timer}` + `deploy/crontab-ejemplo.txt` | respaldo diario 03:00 (systemd o cron) |
| `docs/despliegue/RUNBOOK_DIGITALOCEAN.md` | manual paso a paso con comandos copiables |

Endurecimiento del backend (Fase 1): guardas de arranque con `ENV=production`
(dev-auth, `SECRET_KEY` débil, OAuth ausente, CORS `*`/vacío → **RuntimeError
con el detalle de cada problema**), `SEED_MODE` (`always|if_empty|never`, auto
→ `if_empty` en producción) + reseed manual
(`python -m app.scripts.seed_content --force`), `/docs|/redoc|/openapi.json`
cerrados salvo `EXPOSE_DOCS=true`, `WEB_CONCURRENCY` (default 1) y carga
perezosa/única del modelo de embeddings (ya existente, `lru_cache`).

## 2. Verificación local (stack `-p insoft_prod_test`, DOMAIN=localhost)

- Build sin errores y los 4 servicios **healthy**.
- `./deploy/smoke.sh https://localhost` → **9/9 OK**: `/health` 200, openapi
  404, `/docs` sin Swagger, dev-login deshabilitado (400), HSTS y nosniff
  presentes, index carga app, fallback SPA OK, API protegida (401).
- Boot equivalente de producción: seed `if_empty` carga **9 unidades /
  26 subtemas / 85 preguntas** en BD vacía; indexación RAG con
  `python -m app.seed.index_content` → 26 subtemas / 128 chunks; **reiniciar
  el backend no revierte contenido** ni borra chunks (md5 verificado).
- Prueba negativa: `run -e SECRET_KEY=change-me...` → el proceso muere con el
  RuntimeError esperado.
- Ensayo de restauración: backup (96 KB, sha256 verificado) → restauración
  a BD limpia → conteos idénticos (usuarios 2, unidades 9, subtemas 26,
  preguntas 85, respuestas 3). Bug encontrado y corregido en el ensayo: el
  `pg_restore` leía una ruta de host que no existe en el contenedor → ahora
  el dump va por **stdin**; el nombre de la BD de emergencia usa timestamp
  completo para evitar colisiones.

## 3. Métricas medidas

| Métrica | Valor |
|---|---|
| Imagen backend (prod) | **3.21 GB** (torch CPU ~2.5 GB domina; la de desarrollo pesa 3.57 GB) |
| Imagen frontend (prod) | **467 MB** (nginx-alpine + dist; la de desarrollo 271 MB) |
| RAM en reposo (todo el stack) | **~175 MB** (backend 115 MB —el modelo carga perezosamente solo al usar RAG/IA—, db 26 MB, caddy 29 MB, frontend 6 MB) |
| RAM bajo ráfaga (600 req.) | **~155 MB** (endpoints sin LLM) |
| Reserva esperada con modelo cargado | +~500 MB en el proceso backend → ~0.7 GB total; holgura amplia en 8 GB |
| Arranque hasta `/health` 200 | **~17 s** tras `restart backend` |

**Recomendación de VM:** el piloto funciona con **4 GB** (~USD 24/mes), pero
se recomienda **8 GB** (~USD 48/mes) por margen ante crecimiento de datos,
rebuilds en vivo y uso simultáneo del asistente; el runbook sugiere 8 GB.

## 4. Decisiones destacadas

1. **Merge normal** (no ff) al actualizar la rama: `feat/deploy-prod` tenía
   commits propios sobre la misma base; el merge automático conservó
   `run_seed_by_mode` (Fase 1) y la unidad 9 en el seed (contenido). Suite
   íntegra en el worktree: **157 passed** (147 de contenido + 10 de guardas).
2. **API relativa:** el frontend infería `hostname:8000` en producción
   (exigiría publicar el 8000). Se agregó el valor centinela `VITE_API_URL=/`
   en `api.js` → rutas `/api` por Caddy; desarrollo intacto.
3. **Nginx sin privilegios:** escucha 8080 interno (Caddy manda), pid y
   temporales en `/tmp`, USER nginx.
4. **Seed en producción:** `if_empty` hace que un reinicio jamás modifique
   contenido; para despliegues "desde cero el seed ya incluye la unidad 9
   (26/85) con sus 11 preguntas verbatim.
5. **Backups no destructivos:** `restore.sh` nunca borra: renombra la BD
   actual y deja la restaurada; la lista de conteos permite comparar.

## 5. Bloqueos y lo que no se pudo verificar sin VM real

- **No se pudo verificar con una VM real:** emisión de certificado real de
  Let's Encrypt (con `DOMAIN=localhost` Caddy usa certificado interno,
  verificado con `-k`), flujo completo de Google OAuth con credenciales
  reales, comportamiento de `X-Forwarded-For` desde un cliente externo real
  (la guarda `FORWARDED_ALLOW_IPS` está configurada y `--proxy-headers`
  activo, y el smoke valida API/health por HTTPS), y carga multivolumen real.
- El login con Google requiere credenciales de Google Cloud en el build del
  frontend (build-args recargan la imagen); documentado en el runbook.
- Sin rclone configurado, el backup queda solo local (comportamiento
  documentado y avisado en el log).

## 6. Acciones manuales para quien despliega (resumen)

1. Crear droplet Ubuntu 24.04 (8 GB recomendado) + alerta de facturación.
2. Endurecer (runbook §2) e instalar Docker (§3).
3. DNS: registro A → IP del droplet.
4. Crear `.env.prod` con secretos (`openssl rand`).
5. Google Cloud Console: Client ID + orígenes `https://tudominio.com`.
6. `TEACHER_EMAILS` con el correo de la docente (rol profesor al primer login).
7. Primer despliegue + indexación RAG + smoke + checklist del navegador.
8. Activar timer de backups y cuenta de respaldo en Spaces/B2 (rclone).
9. Monitoreo gratuito sobre `/health` (UptimeRobot) + instantáneas de DO.

## 7. Estado final

- Suite de tests: **157 passed**; stack de desarrollo del usuario intacto
  (`docker ps`: solo `insoft-backend/frontend/db`), `stash@{0}` existe.
- Proyecto de prueba `-p insoft_prod_test` eliminado por completo
  (`down -v`; `docker ps` y `docker volume ls` no muestran nada ajeno).
- Sin push, sin tocar `main`, sin secretos en el repo (`.env.prod` y
  `*.env.prod` en `.gitignore`; solo `*.example` commiteados).
