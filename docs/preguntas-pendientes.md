# Preguntas pendientes de decisión

Cada decisión incluye la opción que el agente aplicó por defecto. Esa opción es la más conservadora y
reversible. Si prefieres otra, dilo y se cambia en un commit pequeño.

## 1. Túnel definitivo para las pruebas en internet

- **Opciones**: Tailscale Funnel, ngrok con dominio, Cloudflare con túnel nombrado (requiere dominio), Cloudflare quick tunnel (URL cambiante).
- **Por defecto aplicado**: se documenta **Tailscale Funnel** como recomendado (URL fija `*.ts.net`, sin dominio propio, sin pago). Los demás quedan como alternativa en `docs/despliegue/PASO_A_PASO_STAGING.md`.
- **Qué falta decidir**: si se acepta Funnel (beta según su documentación) o se prefiere ngrok Hobbyist ($10/mes, sin interstitial).

## 2. Acceso de desarrollo en el build de Vercel

- **Por defecto aplicado**: el acceso de desarrollo solo existe con `import.meta.env.DEV`. Se eliminó `VITE_DEV_AUTH`.
- **Consecuencia**: para probar con cuentas de demostración en la URL pública no hay forma; hay que usar `npm run dev` en local.
- **Alternativa**: mantener una variable de build explícita y prohibida en Vercel. Es más fácil de olvidar; no se recomienda.

## 3. `localhost:8000` en el bundle del stack local de Docker

- **Por defecto aplicado**: el compose local fija `ALLOW_LOCAL_API=1`; el build de Vercel no lo define, y entonces `localhost:8000` falla el `check-dist`.
- **Alternativa**: servir la API por el mismo origen con nginx como proxy (sin URL absoluta). Requiere cambiar `api.js` y `nginx.conf`.

## 4. Comportamiento del asistente cuando la IA está apagada o agotada

- **Por defecto aplicado**: con fragmentos oficiales, respuesta **200 con `degraded: true`** (no es un error para el estudiante). Sin fragmentos, **503** (IA apagada) o **429** (tope agotado).
- **Alternativa**: responder siempre 503. Más simple para el frontend, pero el estudiante pierde la respuesta de respaldo.

## 5. Qué cuenta el tope global diario de IA

- **Por defecto aplicado**: cuenta **llamadas** al proveedor (normalización, respuesta y generación), no créditos ni tokens. El valor por defecto es `0` (sin tope).
- **Qué falta decidir**: un número concreto para `AI_GLOBAL_DAILY_CALLS` y si el coste por llamada justifica medir tokens.

## 6. Sistema de semilla fuera de desarrollo

- **Por defecto aplicado**: `SEED_MODE=if_empty` fuera de desarrollo. Añade unidades oficiales que falten y **no** actualiza ni borra nada existente.
- **Consecuencia**: no se puede "restaurar" una unidad oficial editada sin hacerlo a mano.
- **Alternativa**: `off` después del primer arranque, para que nada toque el contenido.

## 7. Migraciones: adopción de bases existentes

- **Por defecto aplicado**: la primera ejecución registra la línea base (`linea_base`) sobre la base existente y ejecuta el DDL idempotente de la versión anterior. No borra nada.
- **Pendiente**: revisar en la base de Neon antes del primer arranque con esta versión, con una copia (respaldo) previa.

## 8. Repositorio público y materiales de la docente

- **Por defecto aplicado**: no se versiona ningún documento de `docs/importacion/` ni se crea `content/` (el repo es **público**). El contenido oficial sigue en `seed_content.py`.
- **Pendiente**: si el repositorio pasa a privado, decidir si se versionan los `.md` de contenido.

## 9. Respaldos: programación

- **Por defecto aplicado**: los ejemplos de cron y systemd están en `docs/operacion/RESPALDOS.md` **sin instalar**.
- **Pendiente**: decidir dónde guardar los respaldos (disco externo u otro equipo) y el periodo de retención (por defecto 14 días, mínimo 3 copias).

## 10. Credenciales y datos personales

- **Por defecto aplicado**: los ejemplos de `docs/api/ejemplos/` usan datos ficticios (`@example.com`, nombres genéricos). Los tokens están redactados.
- **Pendiente**: confirmar que los nombres de ejemplo y la estructura no permiten identificar a nadie real.

## 11. Orden de merge

- **Por defecto aplicado**: ninguna rama se ha mergeado. El orden recomendado está en `docs/reporte-agente-2026-10-12.md`.
- **Pendiente**: tu aprobación de cada PR. El agente no mergea.

## 12. Patch de tests en `test/aislamiento`

- **Por defecto aplicado**: el parche se aplicó en la rama de #41 (commits `84249f2` y `bc17bd0`).
- **Pendiente**: revisar que los dos cambios de test son correctos (`QUIZ_MAX_QUESTIONS` y la pregunta docente propia).
## 13. Peticiones colgadas si la base se congela

- **Por defecto aplicado**: queda documentado (hallazgo del ensayo). Sin un límite de espera,
  una base suspendida deja las peticiones colgadas hasta el timeout del cliente. No cambié código.
- **Propuesta**: `query_wait_timeout=15` en pgbouncer y/o `statement_timeout` en la app.
- **Pendiente**: decidir si se aplica (requiere cambios en el pooler desplegado y en la app).
