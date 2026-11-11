# PASO_A_PASO_STAGING — despliegue de pruebas con PC del equipo + túnel

Fecha: 10-oct-2026. Ruta principal elegida para el MVP (~15-oct):
**Vercel (frontend) + docker compose (backend + Postgres) en un PC siempre
encendido + túnel HTTPS con URL estable (Tailscale Funnel)**.

Razón: el plan gratis de Render (0.1 CPU / 512 MB) NO aguanta el backend
(see `docs/perf/SIMULACION_RENDER_FREE.md`: OOM con 512 MB; estable desde
~768 MB) y en un PC el coste es $0 sin límite de RAM.

Los nombres de variables son los REALES del repo (`docker-compose.yml` y
`.env.example`). `DEV_AUTH_ENABLED=false` SIEMPRE en este despliegue.

---

## 0. Resumen de la topología

```
Vercel (SPA React, plan gratis)
        │ fetch https://TU-MACHINE.tailnet.ts.net (443)
        ▼
Internet ──► Tailscale Funnel (relay TLS)
        ▼
PC del equipo (docker compose: insoft)
  ├─ frontend  127.0.0.1:3000  (nginx:80 - opcional, para demo local)
  ├─ backend   127.0.0.1:8000  (FastAPI + RAG ONNX)
  └─ db        127.0.0.1:5433  (pgvector/pg16, volumen insoft_postgres_data)
```

La SPA llama al backend por `VITE_API_URL` (https del funnel, puerto 8443
para el backend). Los dos puertos públicos del funnel: 443 → frontend del
compose (3000) y 8443 → backend (8000). Si solo se despliega el frontend en
Vercel, el funnel 443 sigue siendo útil para demo sin Vercel.

## 1. Preparar el PC

1. **Docker al arrancar**: Docker Desktop → Settings → "Start when you log
   in". En Linux: `sudo systemctl enable docker`.
2. **Apagado por inactividad DESACTIVADO**: Power settings → nunca dormir
   con el cable conectado. La suspensión del sistema SÍ corta el funnel y
   manda el backend abajo; el bloqueo de la pantalla NO (el proceso sigue).
3. **Internet**: el PC queda tras NAT; Funnel NO requiere abrir puertos.

## 2. Arrancar el stack

```bash
cd ~/Proyectos/INSOFT/INSOFT
# crea tu .env a partir de .env.example (no lo copies tal cual):
#   POSTGRES_PASSWORD   # openssl rand -hex 16
#   SECRET_KEY          # openssl rand -hex 32
#   BACKEND_CORS_ORIGINS=https://TU-MACHINE.tailnet.ts.net
#   VITE_API_URL=https://TU-MACHINE.tailnet.ts.net:8443
#   GOOGLE_CLIENT_ID=...
docker compose up -d --build
```

- Puertos: db/backend/frontend en **127.0.0.1** (5433/8000/3000): nada
  expuesto en la LAN.
- `POSTGRES_PASSWORD` en .env es la que usa la APP para conectarse. Si el
  volumen `insoft_postgres_data` ya existe con otra contraseña internamente,
  PONLA COMO ESTÁ (no se cambia con .env; si necesitas rotar la real:
  `ALTER USER` dentro del contenedor + .env a la vez).

## 3. Bootstrap de contenido (solo la primera vez o nueva base)

```bash
# base del compose (host = 127.0.0.1, puerto 5433 - se conecta desde el host):
cd backend
DATABASE_URL="postgresql+psycopg2://oftallearn:QUE_PUSISTE@127.0.0.1:5433/oftallearn" \
  SECRET_KEY=... \
  python -m app.scripts.bootstrap_remote --apply --confirm-host 127.0.0.1 \
  [--skip-index si ya hay chunks] [--teacher-email correo@institucion.edu]
```

- Dry-run por defecto. Jan --confirm-host debe coincidir con el host de la
  DATABASE_URL (protege de apuntar a otra base).
- Corre: extension vector + migraciones + contenido oficial + indexación RAG
  + (opcional) docente. Idempotente: re-lanzable sin daño.

## 4. Túnel con URL estable (Tailscale Funnel)

Requisitos vigentes (doc de Tailscale, validada 2026): MagicDNS on, HTTPS on,
certs válidos del tailnet; puertos permitidos para funnel: 443, 8443 y 10000.

```bash
sudo tailscale up --advertise-connector  # solo primera vez / equipo nuevo
tailscale funnel 3000   # frontend  → https://TU-MACHINE.tailnet.ts.net
tailscale funnel 8443   # backend   → https://TU-MACHINE.tailnet.ts.net:8443
```

- Cada comando pide aprobar en el navegador la primera vez (certs Let's
  Encrypt). NO pedir certs de más: rate limit de Let's Encrypt puede dejar
  sin cert 34 horas.
- La URL es estable (dominio del tailnet, no cambia por IP): ideal para
  VITE_API_URL del build de Vercel.
- Larga vida: lanzar los 2 funnels en un `tmux`/`systemd` para que no dependan
  de la ventana de terminal. Para correr en bg:
  `tailscale funnel --bg 3000` (o mismo el equivalente del doc si tu versión).
  Gestión: `tailscale serve status`, `tailscale funnel --root` no existe —
  reset con `tailscale funnel reset` (docs).

Alternativa (ngrok): la cuenta free incluye dominio estático (verifica el
número vigente de endpoints gratis en la doc de ngrok antes de depender):

```bash
ngrok http --domain=TU-DOMINIO.ngrok-free.app 3000   # frontend
ngrok http --domain=TU-DOMINIO2.ngrok-free.app 8000  # backend (segundo dominio
                                                     # o plan; si la cuenta free
                                                     # solo da 1 dominio, esa
                                                     # vía no cubre ambos: usa
                                                     # frontend por ngrok y
                                                     # backend por Funnel, p. ej.)
```

Advertencia ngrok: la página interstitial aparece para requests sin la
cabecera `ngrok-skip-browser-warning` (el frontend no la envía: usar Funnel
para el frontend visible).

## 5. Vercel (frontend)

New Project → repo INSOFT → **Root Directory: `frontend`**; Framework:
Vite (auto). Variables de entorno de producción (Project Settings):

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://TU-MACHINE.tailnet.ts.net:8443` |
| `VITE_GOOGLE_CLIENT_ID` | igual al del `.env` del PC |
| `VITE_DEV_AUTH` | `false` |

**Production Branch = `staging`** mientras dure la fase de pruebas
(Settings → Git → Production Branch). Redeploy tras cambiar el túnel o las
variables (Vite inyecta env al BUILD, no en runtime).

## 6. Backend: CORS + Google Cloud

- El ORIGEN que habla con la API es el de la PÁGINA que el navegador abre:
  si el usuario entra por Vercel, el origen es `https://TU-PROY.vercel.app`;
  si entra por el funnel, es `https://TU-MACHINE.tailnet.ts.net`. En
  `BACKEND_CORS_ORIGINS` van los dos, exactos y separados por coma:
  `https://TU-MACHINE.tailnet.ts.net,https://TU-PROY.vercel.app`
- Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client
  **tipo "Web application"** (es el tipo correcto para el flujo embedded de
  Google Identity Services que usa la app):
  - Authorized JavaScript origins (EXACTOS, sin slash final):
    `https://TU-MACHINE.tailnet.ts.net` y `https://TU-PROY.vercel.app`
  - Authorized redirect URIs: la app NO usa redirect con código; envía el
    `id_token` a `POST /api/auth/google`. Si la consola lo pide, agrega las
    dos URLs con `/`. El error `redirect_uri_mismatch` clásico viene de una
    credencial de tipo equivocado o de una origin que no figura exacta: agrega
    SOLO el origen del sitio que carga el botón de Google.
- `TEACHER_EMAILS=correo@institucion.edu` aplica SOLO al CREAR la cuenta.
  Si ya existe como student, usa:
  `python -m app.scripts.bootstrap_remote --apply --confirm-host 127.0.0.1 --skip-index --teacher-email correo@institucion.edu`

## 7. Verificación capa por capa (curl)

```bash
# 1) backend directamente (desde el PC):
curl -s http://127.0.0.1:8000/health | grep status
# 2) backend a través del túnel (desde cualquier internet):
curl -s https://TU-MACHINE.tailnet.ts.net:8443/health
# 3) RAG real (con un JWT de un login previo) — devuelve modo degradado sin IA:
curl -s -X POST https://TU-MACHINE.tailnet.ts.net:8443/api/ai/ask \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"prueba"}' | head -c 200
# 4) frontend en línea (Vercel o funnel):
curl -sI https://insoft-XX.vercel.app | head -3
```

## 8. Tabla de errores comunes

| Síntoma | Causa habitual | Arreglo |
|---|---|---|
| CORS error en consola (no CORS header) | `BACKEND_CORS_ORIGINS` no incluye el origen EXACTO de la página (vercel.app o del funnel) | Agregar el origen exacto (sin slash final), varios: separados por coma; `docker compose up -d` para cambiar ambiente |
| redirect_uri_mismatch (Google) | Credencial "Desktop app" o la origin no está en "JavaScript origins" | Credencial tipo **Web application**; añade la origin EXACTA del frontend que carga GIS |
| 401 en todas las llamadas tras el login con Google | El Jwt se firmó con otro `SECRET_KEY` (restart del cargar/backend con otra clave) | Mismo `SECRET_KEY` entre llamadas; cierra sesión y reingresa |
| La página "no carga, server se está despertando" | el backend compose se pausó (PC dormido) o el funnel cayó | Detección: `curl` 2) arriba desde otro equipo; wake del PC, relevertir funnel |
| 502/timeout vía túnel, pero backend OK local | funnel corrió en la misma MANCHA que otro puerto o cambia de máquina | un funnel por puerto y máquina; `tailscale serve status` |
| Asistente responde "MODO RESPALDO" siempre | `OPENROUTER_API_KEY` vacía (producación mock de LLM sin red) y simulación | Esto no es error: el RAG funciona; para IA real configura la clave (nunca en el repo) |
| in "El rol docente no se asigna" | TEACHER_EMAILS solo actúa al crear la cuenta | usar bootstrap_remote --teacher-email con el usuario ya logueado |
| `docker compose up` falla: "POSTGRES_PASSWORD not set" | .env vacío o con valores de ejemplo | completa .env (sin secretos de valor débil), luego re up |
| Vercel muestra la app sin API (todo vacío) | `VITE_API_URL` sin valor al BUILD | Hard redeploy de Vercel con las env vars (Vite las inyecta en build) |
| `400 idxJOINT no existe` o similar tras restore | restauraste a una DB nueva sin pgvector | `CREATE EXTENSION IF NOT EXISTS vector` (el bootstrap lo hace) |

## 9. Respaldo nocturno (PC)

```bash
crontab -e
0 3 * * * cd ~/Proyectos/INSOFT/INSOFT && BACKUP_DIR=~/insoft-backups BACKUP_RETENTION=7 bash backend/scripts/backup_db.sh >> backups/backup.log 2>&1
```

pg_dump es SOLO LECTURA por diseño; restauración probada (ver PR #38).
Verifica cada semana el .log por "integridad OK".

## 10. Rutas alternativas (resumen)

### Neon (base administrada opcional)
- Cadena: `<DATABASE_URL>` del repos con `-pooler` para la app y URL directa
  sin `-pooler` para DDL (el backend ya maneja ambas: PR #36 ch merge).
  SSL por defecto en neon.tech.
- Programa `bootstrap_remote --apply --confirm-host <host-neon>` (host REAL
  como está en DATABASE_URL).
- Límites del free de Neon warn: compute se suspende tras inactividad; el
  backend re-intenta 30s/1s al arrancar y `pool_pre_ping` ya cuida activa.

### Render de pago (no gratis)
- El plan gratis (0.1 CPU / 512 MB) NO aguanta el backend (ver
  `docs/perf/SIMULACION_RENDER_FREE.md`); `render.yaml` lo comenta.
- Mínimo viable según nuestra simulación: 1 CPU / 2 GB ('1c-2g', $25 según
  el pricing vigente de Render). No existe unidad intermedia de 1 GB para
  web services; los planes de $7 (0.5c-512mb) mueren igual que el free.

### VM de producción final (mínimo 2 GB)
- Recomendado 2 vCPU / 2-4 GB cuando backend y Postgres compartan máquina:
  el proceso backend con el modelo RAG residente reserva ~700 MB de RAM y el
  Postgres añade sus buffers; 2 GB es el mínimo razonable con margen.
  `docker compose up` + DNS/reverse propia del equipo o túnel permanente.
- Backups con el mismo script (BACKUP_DIR en disco externo o volumen).

## 11. DEV_AUTH

`DEV_AUTH_ENABLED=false` SIEMPRE en este despliegue (y en cualquier
exposición pública). Solo se pone true en pruebas locales puras.
