# Guía de despliegue de INSOFT

Dos rutas soportadas. Elige **una** como principal; la otra queda documentada
como alternativa.

| Ruta | Frontend | Backend | Base de datos | Costo |
|------|----------|---------|---------------|-------|
| **A (recomendada)** | Vercel (gratis) | Render (plan gratis, Docker) | Neon Postgres con pgvector | 0 |
| **B (alternativa)** | PC del equipo con Docker Compose | PC del equipo con Docker Compose | Postgres con pgvector en el mismo Compose | 0 (requiere que el PC esté encendido) |

---

## Ruta A — Vercel + Render + Neon

### 1. Crea las cuentas/proyectos

1. **Neon** (neon.tech): crea proyecto → región cercana (ej. `aws-us-east-1`).
   En la pantalla de conexiones copia la **passwordless connection string**.
2. **Render** (render.com): conecta el repo de GitHub (nuevo servicio de Blueprint).
3. **Vercel** (vercel.com): conecta el mismo repo para el frontend (`frontend/`).
4. **Google Cloud Console**: reutiliza/crea el proyecto OAuth (paso 4 según viene).

### 2. Base de datos: Neon

```text
DATABASE_URL (para la APP del backend, Render):
postgresql+psycopg2://USUARIO:PASSWORD@ep-xxxx-xxxx-123456.us-east-1.aws.neon.tech/DB?sslmode=require

DATABASE_URL (para MIGRACIONES — la misma, es la "directa"):
USAR la conexión SIN el sufijo `-pooler`. En Neon hay dos cadenas:
- Directa (soporta DDL/CREATE EXTENSION):  ep-xxx-123456.aws.neon.tech/DB
- Pooler (no soporta DDL confiable):       ep-xxx-123456-pooler.aws.neon.tech/DB
```

Reglas:

- La app de INSOFT lee `DATABASE_URL` desde el entorno (backend/app/core/config.py).
- Desde el PR de Neon (chore/neon-conexion): puedes apuntar `DATABASE_URL` a la
  cadena AGRUPADA (`-pooler`) — el backend la usa con un pool pequeño
  (`DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=2`, `pool_pre_ping`, `pool_recycle=1800`),
  y las migraciones/create_all van solas por la conexión directa para DDL:
  se deriva de `DATABASE_URL` quitando `-pooler`, o se fija explícita con
  `DATABASE_URL_DDL`. El primer arranque tras suspensión de Neon reintenta
  30 veces (1 s por intento) antes de fallar.
- Las migraciones corren automáticamente al arrancar el backend (`lifespan` ->
  `ensure_schema_compatibility`), que además ejecuta:
  `CREATE EXTENSION IF NOT EXISTS vector` (necesario para el RAG).
  En Neon el usuario del proyecto es dueño de la DB y puede crearla; si un
  rol restringido no puede, el comando exacto es:
  `psql "<DATABASE_URL_DDL>" -c "CREATE EXTENSION IF NOT EXISTS vector;"`
- SSL: se activa solo si el host contiene `neon.tech`, o forzándolo con
  la variable `DATABASE_SSL=true`. El driver añade `sslmode=require`.
- Alembic: este repo NO usa Alembic (migraciones ligeras aditivas idempotentes
  internas en app/database/migrations.py). Si se introduce Alembic en el futuro,
  apuntar `alembic.ini` a la URL directa.

> **ADVERTENCIA seguridad — login de desarrollo**
> - `DEV_AUTH_ENABLED` debe ser `false` (o no definirse) en producción. Render y
>   docker-compose ya lo dejan `false` por defecto.
> - Con `DEV_AUTH_ENABLED=false`, `POST /api/auth/dev` responde **403** sin crear
>   usuario ni sesión, y el build de producción del frontend **no contiene** la
>   tarjeta "Acceso de desarrollo" (depende de `import.meta.env.DEV` o de
>   `VITE_DEV_AUTH=true`, que en Vercel no se define).
> - Además, si `DEV_AUTH_ENABLED=false` y `SECRET_KEY` está vacía o es el
>   placeholder "change-me-in-production", el backend **se niega a arrancar**.

### 3. Backend en Render (Docker, plan free)

1. Render → *New Blueprint* → selecciona el repo. Usage de `render.yaml`
   (services/type web, runtime docker, healthCheckPath `/health`, plan free).
2. En el panel del servicio, agrega las variables con :key: sync:false
   (NO van al repo, son sensibles):

| Variable | Valor de ejemplo |
|---|---|
| DATABASE_URL | URL directa de Neon (ver tabla anterior) |
| SECRET_KEY | `openssl rand -hex 32` |
| GOOGLE_CLIENT_ID | `<client-id>.apps.googleusercontent.com` |
| TEACHER_EMAILS | `profesora@correo.com` |
| BACKEND_CORS_ORIGINS | `https://tu-app.vercel.app` (comas para varios) |
| AI_PROVIDER | `openrouter` |
| OPENROUTER_API_KEY / GEMINI_API_KEY | de la plataforma elegida |
| DEV_AUTH_ENABLED | `false` (SIEMPRE en producción) |

3. Deploy. Verifica `https://insoft-backend.onrender.com/health` (sin auth).

**Nota de plan gratis:** Render duerme el servicio (~15 min inactivo). La
primera petición tarda 30-60 s y el frontend muestra el aviso
"El servidor se está despertando, un momento…" (componente
`SlowServerBanner`).

**RAM y plan gratis (medido 7-oct-2026, ver `docs/perf/INFORME_MEMORIA.md`):**
Render free = 0.1 CPU / **512 MB**. El backend NO cabe continuo ni con
`EMBEDDINGS_BACKEND=torch` (~1,1 GB) ni con `onnx` (~0,67 GB). Opciones:
1. **PC local + túnel** (ruta B) — costo 0, sin límites de RAM (recomendado).
2. **VM ≥ 1 GB RAM** (DigitalOcean $6/$12, Render `1c-2g` $25) con
   `EMBEDDINGS_BACKEND=onnx` y build-arg del Dockerfile de la misma vara.
3. Ejecutar el RAG fuera del MVP (no recomendado para el piloto).

### 4. Google OAuth (para Google Cloud Console)

En *APIs & Services → Credentials → OAuth 2.0 Client ID* agrega los
**Authorized origins** y **redirect URIs**:

- Orígenes autorizados (origins):
  - `http://localhost:5173` (desarrollo)
  - `https://tu-app.vercel.app` (producción)
  - URLs de los previews de Vercel `https://<pr-n>.vercel.app` cuando hagas QA
    por PR (o confía en el regex de CORS; el login de Google exige origen
    exacto, actualízalo a mano).
- Redirect URIs: la app usa **login por botón de Google One-Tap/Botón** y NO
  hace redirect: solo se precisan orígenes. Si cambias a flujo redirect,
  agrega `https://tu-app.vercel.app/auth/callback`.

Copia el **CLIENT ID** en Vercel: variable `VITE_GOOGLE_CLIENT_ID`.

### 5. Frontend en Vercel

*Root directory:* `frontend` (en el dashboard de Vercel).

Variables (Project Settings → Environment Variables):

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://insoft-backend.onrender.com` |
| `VITE_GOOGLE_CLIENT_ID` | `<client-id>.apps.googleusercontent.com` |
| `VITE_DEV_AUTH` | `false` |

La reescritura SPA ya está en `frontend/vercel.json`:

```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

CORS en el backend ya acepta `https://*\.vercel.app` (previews).

### 6. Carga inicial de la base y primer docente

1. Con el backend de Render encendido (o `docker compose up` en local apuntado
   a Neon con la URL directa en DATABASE_URL):
   - El seed oficial sube automáticamente 9 unidades / 22 subtemas / ~85
     preguntas al primer arranque (`app/seed/`).
2. Crea el usuario docente:
   - Inicia sesión con Google con el correo que pusiste en `TEACHER_EMAILS`
     (el rol se asigna al CREAR la cuenta; si la cuenta ya existía con otro
     rol, cambia el rol desde el panel: `/perfil` -> "Cambiar a docente").
3. Si quieres importar contenido extra (Markdown con imágenes) con el rol
   docente:
   - `/teacher/import` -> carga del documento (endpoint `POST /api/content/import`).

### 7. Flujo de ramas

- **main** = producción (URL estable para Google: la del dominio de Vercel).
- **staging** = pruebas; su deploy de Vercel/Render es BAJA ESTABLE con URL
  fija. Regístrala en Google Cloud como origen permitido.
- **feature/*** → PR -> Vercel Preview por PR (URL efímera). El backend no
  hace deploy automático en los previews.

---

## Ruta B — PC del equipo + Docker Compose + túnel

1. Requisitos: Docker + docker compose VPN/túnel.
2. Variables: copia `.env.example` a `.env` (raíz) y rellena:

```text
POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT
SECRET_KEY=<openssl rand -hex 32>
GOOGLE_CLIENT_ID=...
TEACHER_EMAILS=profesora@correo.com
DEV_AUTH_ENABLED=false
VITE_API_URL=https://<dominio-del-tunel>   # ej. https://x.trycloudflare.com
```

3. Sube la pila (Postgres pgvector + backend + frontend nginx):

```bash
docker compose up --build -d
```

- Datos persistentes en el volumen `postgres_data`.
- Healthchecks de DB y backend incluidos; `restart: unless-stopped`.
- Migraciones + `CREATE EXTENSION IF NOT EXISTS vector` al arrancar el backend.

4. Cambia el login de Google al dominio del túnel (Google Cloud -> origins):
   `https://<dominio-del-tunel>`.
5. Exposición con túnel (elige uno):

| Tunnel | Comando | URL |
|---|---|---|
| Cloudflare Tunnel (recomendado) | `cloudflared tunnel --url http://localhost:3000` | `https://xxx.trycloudflare.com` |
| Tailscale Funnel | `tailscale funnel 3000` (requiere HTTPS en el cliente Tailscale) | `https://<machine>.<tailnet>.ts.net` |
| ngrok (rápido) | `ngrok http 3000` | `https://xxxx.ngrok-free.app` |

- Si cambia el dominio del túnel: actualiza `BACKEND_CORS_ORIGINS` del backend
  para sumar el dominio del túnel, y el `VITE_API_URL` del frontend (rebuild).

---

## Variables de entorno (todas, por servicio)

**Backend (Render o Compose):** `DATABASE_URL`, `DATABASE_SSL`,
`SECRET_KEY`, `GOOGLE_CLIENT_ID`, `BACKEND_CORS_ORIGINS`,
`TEACHER_EMAILS`, `DEV_AUTH_ENABLED`, `AI_PROVIDER`,
`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_*`,
`AI_*_RATE_LIMIT`, `QUIZ_MAX_QUESTIONS`, `PRACTICE_*` (ver .env.example
en la carpeta raíz del proyecto).

**Frontend (Vercel / build args):** `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`,
`VITE_DEV_AUTH`.

**Neon:** no hay ninguna administración manual salvo la URL directa vs pooler.

---

## Checklist post-despliegue

- [ ] `GET https://<backend>/health` devuelve `{"status": "ok"}` sin autenticación.
- [ ] Login con Google funciona desde el domain de Vercel.
- [ ] Un estudiante nuevo se ve inscrito el curso "General".
- [ ] "Agregar preguntas" visible solo para docente; las 4 opciones A-D.
- [ ] El récord del asistente IA responde sobre el contenido importado.
- [ ] `docker compose` (ruta B) revive si se cae y la base persiste.
