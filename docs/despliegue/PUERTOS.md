# Estado de los puertos (verificación 2026-10-14)

## Compose (histórico #48, ya mergeado en staging) — CORRECTO

El `docker-compose.yml` enlaza los tres servicios en loopback:

- db: `127.0.0.1:${POSTGRES_PORT:-5433}:5432`
- backend: `127.0.0.1:${BACKEND_PORT:-8000}:8000`
- frontend: `127.0.0.1:${FRONTEND_PORT:-3000}:80`

Comentario de cabecera del compose: nada escucha en 0.0.0.0; la exposición
pública es solo por túnel (ver §1 de `docs/preguntas-pendientes.md`).

## Stack en ejecución hoy (arrancado ANTES del endurecimiento)

`docker ps` sigue mostrando publicación en 0.0.0.0:

```
insoft-db        0.0.0.0:5433->5432
insoft-backend   0.0.0.0:8000->8000
insoft-frontend  0.0.0.0:3000->80
```

**Riesgo**: en una LAN, cualquier equipo alcanzable puede tocar Postgres y el
backend de desarrollo (`0.0.0.0:5433/8000/3000`), incluso con
`VITE_MODE=dev` o credenciales demo si `POSTGRES_PASSWORD` no está definida.

**No se recrearon contenedores** (cambio operativo, se deja como paso manual).
Cuando corresponda, bastará:

```bash
docker compose up -d
```

que reconstruye los tres con los binds 127.0.0.1 ya presentes en el compose.
El `docker compose up -d` no borra volúmenes: los datos persisten.

## Uvicorn de desarrollo en 0.0.0.0:8000 — observado, no intervenido

- El único `uvicorn` es el del contenedor `insoft-backend`
  (`--host 0.0.0.0`), visible por el docker-proxy de Ejecución.
- No hay ningún proceso host adicional del usuario (`uvicorn`, `vite`).
- **Instrucción: no matarlo.** Riesgo documentado: todo lo que escucha en
  0.0.0.0 y acepta tokens de demo debería restringirse a 127.0.0.1 antes de
  abrir un túnel estable (PASO_A_PASO_STAGING v2, PR #52). El cambio futuro
  sería `--host 127.0.0.1` en el comando del servicio o recrear con el
  compose endurecido.

## Comprobaciones de hoy

- `curl http://localhost:8000/health` → `{"status":"ok","service":"INSOFT"}` (stack vivo).
- `curl http://localhost:3000` → HTML del frontend (funciona en desarrollo).
