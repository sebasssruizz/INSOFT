# Endpoints sin autenticación

Generado desde la aplicación (rutas y dependencias de FastAPI), no a mano.
Cualquier ruta nueva **sin** `get_current_user`, `require_student` o `require_teacher` debe
aparecer aquí y justificarse.

| Método | Ruta | Por qué es pública | Protección |
|---|---|---|---|
| GET | `/health` | Comprobación de vida para el túnel y el compose. | No expone datos. |
| GET | `/ready` | Comprobación de base de datos y pgvector. | Devuelve solo estado, sin detalles internos. |
| POST | `/api/auth/google` | Inicio de sesión con Google. | ID token verificado (firma, audiencia, emisor, expiración, correo verificado). Rate limit `AUTH_RATE_LIMIT` (60/h en compose). |
| POST | `/api/auth/dev` | Login de desarrollo. | Solo con `DEV_AUTH_ENABLED=true`; si no, **403** sin crear usuario ni sesión. |

Documentación OpenAPI (`/docs`, `/redoc`, `/openapi.json`): **desactivada por defecto**
(`DOCS_ENABLED=false`). Solo se sirve si se activa explícitamente.

## Cabeceras de seguridad (middleware)

`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`,
`Cross-Origin-Opener-Policy: same-origin`. HSTS no se fija aquí: HTTPS lo termina el proxy o el túnel.

## Exposición de red (compose)

- `db`, `backend` y `frontend` publican solo en `127.0.0.1` (el túnel llega desde el propio PC).
- `POSTGRES_PASSWORD` y `BACKEND_CORS_ORIGINS` son obligatorias (`:?` en compose): sin ellas no se levanta.
- `DOCS_ENABLED` y `DEV_AUTH_ENABLED` valen `false` salvo que se fijen.
- Logs con rotación (`max-size: 10m`, `max-file: 3`) y `restart: unless-stopped`.
