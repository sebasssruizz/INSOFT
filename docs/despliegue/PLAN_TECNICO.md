# PLAN TÉCNICO — Despliegue de producción de INSOFT

Fecha: 2026-10-03 · Rama: `feat/deploy-prod` (traída al día con `feat/contenido-unidades-restantes`, fast-forward).

## Estado actual

- Solo existe `docker-compose.yml` de **desarrollo**: expone puertos 8000/3000/5433,
  sin HTTPS, sin límites de recursos, sin healthchecks del backend, imágenes de
  desarrollo (backend con `uvicorn` plano, root, modelo precargado pero sin usuario
  no-root; frontend con Nginx básico sin cabeceras de seguridad ni caché por hash).
- Backend: FastAPI + SQLAlchemy + JWT (Google OAuth) + RAG local
  (`sentence-transformers`, CPU). El seed oficial corre en **cada arranque**
  (`main.py` → `seed_official_content`) y sobrescribe contenido por posición:
  riesgo real de reversión en producción.
- `DEV_AUTH_ENABLED=true` permite login sin Google; el valor default de
  `SECRET_KEY` es `change-me-in-production`; CORS configurable.
- Límites de uso (slowapi): clave = user_id del JWT; para endpoints sin sesión
  usa IP (`get_remote_address`) → detrás de un proxy necesita `--proxy-headers`.
- Frontend: `VITE_API_URL`; en no-localhost infiere `hostname:8000` → hoy
  obligaría a publicar el 8000; hay que soportar API relativa (`/api`).

## Brechas hacia producción (objeto de las fases)

1. Guardas de configuración: negar arranque en producción con secretos
   inseguros, dev-auth activo, CORS `*`/vacío u OAuth incompleto.
2. Seed controlado (`SEED_MODE=always|if_empty|never`) + reseed manual explícito.
3. Proxy: `--proxy-headers` / `FORWARDED_ALLOW_IPS` para IP real y límites por IP.
4. Superficie pública: `/docs`, `/redoc`, `/openapi.json` cerrados salvo
   `EXPOSE_DOCS=true`; `/health` ligero y público.
5. Imágenes de producción: backend slim + torch CPU + no-root + modelo en build
   + HEALTHCHECK; frontend Nginx no-root, SPA fallback, gzip, caché larga para
   assets con hash y sin caché para `index.html`, cabeceras de seguridad.
6. Proxy inverso **Caddy** (80/443, HTTPS automático por `DOMAIN`; `localhost`
   con certificado interno), único servicio que publica puertos.
7. `docker-compose.prod.yml`: red interna, volúmenes nombrados, healthchecks con
   `depends_on: service_healthy`, límites de memoria, rotación de logs,
   `env_file: .env.prod`.
8. Backups (`pg_dump -Fc` + retención + rclone opcional a S3) con restore probado,
   timer systemd/cron, monitoreo gratuito sobre `/health`.
9. Runbook DigitalOcean paso a paso (droplet, endurecimiento, Docker, DNS,
   Google OAuth en Cloud Console, primer despliegue, smoke, actualizar/revertir/
   restaurar, costos).

## Decisiones

- **Caddy** como único punto de entrada (HTTPS automático, config simple); el
  Nginx del frontend sirve solo estáticos en la red interna.
- API **relativa** (`/api`) desde el frontend: se agrega soporte del valor
  `VITE_API_URL=/` en `api.js` (sentinel) para que Caddy enrute al backend sin
  exponer el 8000; en desarrollo no cambia nada.
- Backend con **1 worker** por defecto (`WEB_CONCURRENCY`) por la RAM del
  modelo de embeddings; carga perezosa y única del modelo ya existente
  (se medirá en la fase de verificación).
- El compose de **desarrollo no se toca**. Pruebas de producción en proyecto
  aislado `-p insoft_prod_test` con puertos/volúmenes propios.
- Sin servicios pagos: BD con volumen propio, backups con rclone opcional,
  monitoreo con UptimeRobot (gratis) + instantáneas de DO.
