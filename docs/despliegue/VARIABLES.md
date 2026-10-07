# VARIABLES — fuente única de verdad (backend + frontend + despliegue)

Tabla consolidada: si una variable aparece distinta en DEPLOY.md, README,
render.yaml o docker-compose, MANDA esta tabla (reporta la desviación).

| Variable | ¿Obligatoria? | Ejemplo ficticio | ¿Dónde se coloca? | ¿Sensible? |
|---|---|---|---|---|
| `DATABASE_URL` | Sí (prod) | `postgresql+psycopg2://usuario:clave@host/db` | Backend (Render env / compose prod) | **Sí** |
| `DATABASE_SSL` | No | `true` | Backend (Neon sin host neon.tech) | No |
| `SECRET_KEY` | **Sí en prod** | `openssl rand -hex 32` | Backend | **Sí** |
| `DEV_AUTH_ENABLED` | No (default `false`) | `false` | Backend + frontend `VITE_DEV_AUTH` derivado | No |
| `GOOGLE_CLIENT_ID` | Sí si login Google | `123.apps.googleusercontent.com` | Backend y frontend | No (público) |
| `TEACHER_EMAILS` | Sí (pilot) | `profesora@correo.com` | Backend | No |
| `BACKEND_CORS_ORIGINS` | Sí en prod | `https://insoft.edu.co` | Backend | No |
| `BACKEND_CORS_ORIGIN_REGEX` | No | regex vercel.app | Backend | No |
| `AI_PROVIDER` | No | `openrouter` (`gemini` alterna) | Backend | No |
| `OPENROUTER_API_KEY` | Sí si provider=openrouter | `sk-or-...` | Backend | **Sí** |
| `GEMINI_API_KEY` | Sí si provider=gemini | `AIza-...` | Backend | **Sí** |
| `AI_MODEL_CHAIN` | No | `m1,m2,m3` | Backend | No |
| `AI_DAILY_LIMIT_PER_USER` | No | `50` | Backend | No |
| `AI_ASK_RATE_LIMIT` / `AI_QUESTION_RATE_LIMIT` | No | `60/hour`, `5/hour` | Backend | No |
| `EMBEDDINGS_BACKEND` | No (default `torch`) | `onnx` (prod ligera) | Backend + build-arg Docker | No |
| `EMBEDDING_MODEL` | No | MiniLM-L12-v2 | Backend | No |
| `QUIZ_MAX_QUESTIONS` | No | `10` | Backend | No |
| `PRACTICE_*`, `AI_*_RATE_LIMIT` | No | ver `.env.example` | Backend | No |
| `VITE_API_URL` | Sí en frontend prod | `https://api.insoft.edu.co` | Frontend (Vercel/build-arg) | No |
| `VITE_GOOGLE_CLIENT_ID` | Sí si Google | mismo CLIENT_ID | Frontend | No |
| `VITE_DEV_AUTH` | **No en prod** (default false) | `false` | Frontend | No |
| `PORT` | Sí en Render/VM | `8000` | Backend (Dockerfile) | No |
| `POSTGRES_USER/PASSWORD/DB/PORT` | Sí (compose local/VM) | `oftallearn` | Compose | **Sí PASSWORD** |
| `SEED_MODE` (solo rama deploy-prod) | No | `auto` | Backend prod | No |

Reglas (ya implementadas; romperlas bloquea backup o arranque):
- Con `DEV_AUTH_ENABLED=false` y `SECRET_KEY` vacía/placeholder → el backend
  NO arranca (`config.py` validator).
- `POST /api/auth/dev` con dev off → 403 sin crear usuario.
- El bundle de producción NO incluye la tarjeta de acceso dev.
