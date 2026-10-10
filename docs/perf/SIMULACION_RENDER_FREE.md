# SIMULACION_RENDER_FREE — ¿cabe el backend en el plan gratis de Render?

Fecha: 9-oct-2026. Scope: backend completo (uvicorn + RAG ONNX) contra un
Postgres **desechable** con pgvector (`pgvector/pgvector:pg16`) en red
Docker propia — **nada tocó la base real** (`insoft_postgres_data`; los
contenedores `sim-*` usan red `sim-perf` y volumen `sim-pgdata`, y pueden
borrarse con `docker rm -f sim-backend sim-pg && docker rm sim-pgdata && docker network rm sim-perf`)).
Imagen construida con `EMBEDDINGS_BACKEND=onnx` (rama #32; el modelo queda
horneado, 241 MB en `/app/model-cache` — sin descargas en el arranque).
El "LLM" es simulado: sin `OPENROUTER_API_KEY`, el cliente falla **sin salir
a la red** y el flujo de staging responde en modo degradado con los chunks
recuperados (HTTP 200, `"degraded": true`) — así el RAG completo (embed +
pgvector + ranking) se ejecuta de verdad con coste $0 y cuota 0.

## 1. Especificación oficial del plan Free (docs de Render, verificados hoy)

- Web service Free: **0.1 CPU / 512 MB RAM** (`free`).
- **Spin-down tras 15 min sin tráfico de entrada** (HTTP/WebSocket). El
  siguiente request paga un spin-up de **~1 minuto**; el sistema muestra una
  página de carga mientras despierta (`SlowServerBanner` del frontend cubre esto).
- Sistema de archivos **efímero** en cada redeploy/restart/spin-down (por eso
  el modelo de embeddings debe ir horneado en la imagen, ya resuelto en #32).
- Además: 750 free instance-hours/mes por workspace; Render puede reiniciar el
  servicio en cualquier momento; solo 1 instancia (sin réplicas).
- (El Postgres Free de Render expira a los 30 días — de ahí Neon para la base.)

## 2. Resultados medidos (backend ONNX, chunks de relleno ×150, LLM simulado)

| Métrica | Valor |
|---|---|
| Imagen `insoft-backend-sim` (compressed size en Docker) | 1.27 GB (241 MB = modelo horneado) |
| Arranque en frío→`/health` 200, **sin límites** | ~6 s |
| Arranque en frío→`/health` 200, **0.1 CPU** | **59–63 s** |
| RAM en reposo (pre-modelo, lazily cargado) | **103–105 MB** |
| RAM tras 1ª consulta RAG (carga perezosa del modelo en req#1) | **695 MB** (pico en la carga instancia) |
| RAM tras 10 RAG secuenciales | **~696.7 MB** (estable, sin fuga) |
| RAM tras 5 concurrentes | **697 MB** (sin inflación) |
| 10 RAG secuenciales, especial CPU ilimitada | 23.5 s total (1º incluye carga de modelo: 4.3 s) |
| 5 concurrentes (CPU ilimitada) | 0.87 s por petición |
| 1 RAG en caliente a **0.1 CPU** | **5.3 s** |
| Primer RAG *en frío* a 0.1 CPU (con modelo cargado ya en imagen) | **77 s** |
| Muerte del contenedor con `--memory=512m` | **Sí, OOM (exit 137, `oom_killed=true`)** — con y sin `OMP_NUM_THREADS=1` |

## 3. Batería de ajustes probados (regla del "si no cabe")

| Ajuste | Resultado |
|---|---|
| **512 MB, 0.1 CPU, tuneado estándar** | **OOM kill durante carga del modelo** (exit 137) |
| **+ `OMP_NUM_THREADS=1` + `MALLOC_ARENA_MAX=2`** (menos hilos ONNX Runtime, menos arenas glibc) | **Sigue OOM**: el ahorro no toca el pico dominante (instancia del modelo ONNX, ~600 MB) |
| 640 MB | Sin OOM pero queda PEGADO: RAM saturada 639.8/640 MB, la petición no completa (thrashing) |
| **768 MB** | **Funciona**: arranque 63 s, primer RAG 77 s, RAG en caliente 5.3 s a 0.1 CPU, estable en 693–711 MB |
| 1 worker | Ya es el default (1 solo proceso uvicorn; no hay margen extra) |
| Carga perezosa | Ya existe (singleton con `lru_cache`); solo traslada el pico al primer RAG, no lo elimina |
| Menos chunks por consulta | Indiferente para RAM: el coste dominante es el modelo ONNX residente, no la tabla de chunks (150 ≈ los 165 reales) |

## 4. Conclusión: **NO CABE en el plan Free (512 MB) — cabe a partir de ~768 MB**

El plan Free de Render mata el backend con OOM en el momento en que el modelo
de embeddings se instancia (primera consulta del asistente), incluso con los
ajustes de hilos/allocator. A 0.1 CPU (representativa del free real) ni a
640 MB completa la petición (quedan pegados con la RAM saturada); el mínimo
estable medido es **~768 MB** (692–711 MB residentes + margen). La CPU 0.1
solo agrava la latencia (59 s de arranque frío, 5.3 s por RAG en caliente).

Consecuencias directas:
- El plan *free* de Render (0.1 CPU / 512 MB): **no sirve para el backend**.
- El plan *paid* de $7 (0.5 CPU / 512 MB): **tampoco cabe** — el límite
  sigue siendo la RAM de 512 MB, y en exactamente ese pico muere.
- La prueba original de F2 pedía `--cpus=0.5`; como la CPU no afecta al pico
  de RAM, se documentó por separado ver también 0.1 CPU (el free real).

**Alternativa recomendada para el MVP del 15-oct** (mismo veredicto que el
informe de memoria de #32 y la sección "Plan gratis" de `DEPLOY.md`):
1. **PC local con Docker + túnel** (Cloudflare/Tailscale, ya probado en
   `feat/deploy-prod`): costo 0, sin límite de RAM, arranque instantáneo.
   Riesgo: el PC debe estar encendido; mitigable subiendo/apagando el túnel
   con coste nulo.
2. **VM de 1 GB** (DigitalOcean $6; Render `1c-2g` $25 es excesivo para el
   módulo de consultas RAG). Estable, IP fija, sin depender del PC.

Notas operativas del despliegue alternativo:
- El frontend en Vercel es estático (solo CDN) y puede ir al plan free sin
  problema; el problema de RAM es del backend, no del frontend.
- Con spin-down por inactividad: el primer request del día paga ~59 s de
  arranque (el banner "El servidor se está despertando…" ya existe) y, si
  nadie ha preguntado nada, el primer RAG suma hasta ~77 s por la carga
  perezosa del modelo (a 0.1 CPU). Servicio de pings cada 14 min o ping
  manual ejecutado en el arranque de la sesión evita la fricción del cold
  start; con backend local + túnel el reinicio desde el PC es inmediato.
- Para una demo real del 15-oct conviene deshabilitar el spin-down del
  servicio local levantándolo antes y dejándolo en marcha durante la sesión.

## 5. Reproducción

```bash
# 1. Postgres desechable con pgvector
docker network create sim-perf
docker volume create sim-pgdata
docker run -d --name sim-pg --network sim-perf -e POSTGRES_USER=sim \
  -e POSTGRES_PASSWORD=sim -e POSTGRES_DB=sim \
  -v sim-pgdata:/var/lib/postgresql/data pgvector/pgvector:pg16

# 2. Imagen con ONNX (rama ./backend de #32) y seed de relleno (no médico)
docker build --build-arg EMBEDDINGS_BACKEND=onnx -t insoft-backend-sim ./backend
docker run --rm --network sim-perf \
  -v "$PWD/backend/sim/bootstrap_rag_sim.py":/app/bootstrap_rag_sim.py:ro \
  -e DATABASE_URL=postgresql+psycopg2://sim:sim@sim-pg:5432/sim \
  -e SECRET_KEY=sim-only-disposable-key-dev-auth-false \
  -e DEV_AUTH_ENABLED=false -e AI_PROVIDER=openrouter \
  insoft-backend-sim python bootstrap_rag_sim.py   # imprime el JWT de prueba

# 3. Barrido de límites (memoria y arranque en frío)
bash backend/sim/try_limite.sh 512m
bash backend/sim/try_limite.sh 640m
bash backend/sim/try_limite.sh 768m

# 4. Limpieza (esquema desechable, real intacto)
docker rm -f sim-backend sim-pg && docker rm sim-pgdata && docker network rm sim-perf
```
