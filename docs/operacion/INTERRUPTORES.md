# Interruptores operativos

Tres variables de entorno para operar la plataforma sin redesplegar. Código:
`backend/app/services/ai_budget.py`, `backend/app/services/ai_service.py`, `backend/app/main.py`
(middleware `modo_mantenimiento`). Pruebas: `backend/tests/test_interruptores.py` (12 pruebas, mocks).

| Variable | Valor por defecto | Efecto |
|---|---|---|
| `AI_ENABLED` | `true` | `false`: no se llama al proveedor de IA. |
| `AI_GLOBAL_DAILY_CALLS` | `0` (sin tope) | Tope **global** de llamadas al proveedor por día UTC. |
| `MAINTENANCE_MODE` | `false` | `true`: 503 para estudiantes; docentes, `/health`, `/ready` y `/api/auth/*` siguen funcionando. |

## IA apagada (`AI_ENABLED=false`)

- Con fragmentos oficiales disponibles: **200** con `degraded: true` (modo respaldo, sin llamadas).
- Sin fragmentos: **503** con `detail: "[asistente-desactivado] …"` y `Retry-After: 600`.
- La generación de preguntas (docente) responde **503** `[asistente-desactivado]`.

## Tope global diario (`AI_GLOBAL_DAILY_CALLS=N`)

- Cuenta **todas** las llamadas al proveedor: normalización, respuesta y generación de preguntas.
- El contador está en la tabla `ai_calls_daily` (migración 3), así que sobrevive a reinicios.
  La reserva es atómica en PostgreSQL y SQLite.
- Agotado el tope:
  - con fragmentos: **200** con `degraded: true`, sin gastar;
  - sin fragmentos: **429** con `detail: "[asistente-tope-global] …"` y `Retry-After` hasta medianoche UTC.
- La generación de preguntas responde **429** `[asistente-tope-global]`.
- Se reinicia a medianoche UTC (cambia de fila el día).

## Modo mantenimiento (`MAINTENANCE_MODE=true`)

- Estudiantes y peticiones sin token: **503** `[mantenimiento] …` con `Retry-After: 600`.
- Pasan: docentes (según el claim `role` del JWT), `/health`, `/ready`, `/api/auth/*` (para poder iniciar sesión) y las peticiones `OPTIONS` (CORS).
- Es una compuerta operativa, no un control de permisos: cada ruta sigue validando al usuario.

## Cómo activarlos

```bash
# en .env del PC de pruebas o en las variables de Neon/Render
AI_ENABLED=false
AI_GLOBAL_DAILY_CALLS=300
MAINTENANCE_MODE=true
```

Los cambios de variables requieren reiniciar el backend. No requieren migraciones.

## Límites conocidos

- El tope cuenta llamadas, no créditos: el coste real depende del modelo.
- El rol para el modo mantenimiento se lee del token. Un cambio de rol de docente solo aplica
  cuando el token se renueva.
- `/ask` degrada con fragmentos también cuando la IA está apagada o agotada. Si no hay
  fragmentos (tema sin contenido), responde 503 o 429 según el motivo.
