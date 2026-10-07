# INFORME_MEMORIA — tamaño de imagen y RAM del modelo de embeddings (T1)

Fecha: 7-oct-2026. Scope: backend `app/services/embeddings_service.py`
(modelo `paraphrase-multilingual-MiniLM-L12-v2`, 384 dims). **Nada de esto
tocó la base de datos real** (solo consultas de lectura y una imagen de prueba
desechable `insoft-backend-onnx-test`, que se puede eliminar con
`docker rmi insoft-backend-onnx-test`).

## 1. Línea base (backend actual, EMBEDDINGS_BACKEND=torch)

| Métrica | Valor |
|---|---|
| RSS en reposo (proceso python, modelo cargado) | **1 121 MB** |
| RSS pico armado con índice + 20 búsquedas | ~1 300 MB |
| Carga inicial del modelo | 21–29 s (frío) |
| 20 embeds de pregunta | ~21,8 s
| Tamaño de imagen `insoft-backend:latest` | **3,57 GB** |

## 2. Alternativa implementada: ONNX por fastembed (EMBEDDINGS_BACKEND=onnx)

fastembed 0.7.3 soporta **exactamente el mismo modelo** en ONNX. Con el modelo
por defecto:

| Métrica | torch (actual) | onnx (fastembed) | Δ |
|---|---|---|---|
| RSS tras 20 embeds de pregunta | 1 121 MB | **666 MB** | **−40%** |
| Tiempo 20 embeds de pregunta | 21,8 s (incluye carga) | **0,17 s** | ~128x |
| Carga del modelo | ~22 s | ~17 s | similar |
| Tamaño de imagen | 3,57 GB | **0,78 GB** | **−78%** |
| Cosine(torch, onnx) del mismo texto | — | **1.0000** | idéntico |
| top-1 / top-3 (165 preguntas etiquetadas, 128 chunks) | 29,7% / 57,6% | 29,7% / **58,8%** | **+1,2 pts top-3** |
| Dimensiones | 384 | 384 | **sin reindexar** |

**Decisión aplicada (reversible)**: se implementa `EMBEDDINGS_BACKEND`
(config) con por defecto `torch`. Con `onnx` se usa fastembed: mismas dimensiones,
sin reindexado; si alguien cambia a un modelo no-384 se lanza un error claro
(`_validate_onnx_dimensions`). Añade `backend/requirements-onnx.txt`
(sin torch) y el Dockerfile elige paquetes por build-arg. Quizá la forma más
segura de probar en local: `docker build --build-arg EMBEDDINGS_BACKEND=onnx -t
insoft-backend ./backend`.

**Deuda conocida**: no alcanza ≤400 MB en reposo (666 MB): el runtime de ONNX,
tokenizador y stack HTTP del backend consumen lo que queda. Con el plan gratuito de
Render (0.1 CPU / **512 MB**) ni torch ni ONNX aguantan con el modelo cargado.

## 3. Alternativas descartadas o solo diseño

- **`minishlab/potion-multilingual-128M`** (0.5 GB, static embeddings): produce
  dimensiones **256** → obligaría a reindexar todo el corpus (×2 riesgo para
  MVP del 15-oct); se reevalúa si el MVP exige <400 MB; hoy no aplica.
- **API externa de embeddings** (solo diseño, NO implementado): cambiar
  `EMBEDDINGS_BACKEND` a modo "api" (env `EMBEDDINGS_API_URL` + auth) para
  terceros con imágenes/tiernancia tipo OpenAI embeddings o Gemini
  text-embedding-004: depende de cuota y SLA, agrega latencia por llamada y
  **requeriría reindexado** si el modelo es distinto. Para el piloto la
  recomendación es la ruta local = no llamada API externa.

## 4. Recomendación de despliegue

| Decisión |Ⴉ Pro | Contra |
|---|---|---|
| **A. PC local + Docker + túnel** (Cloudflare/Tailscale), como en `feat/deploy-prod` | costo 0, sin límites de RAM, ya probado — **recomendado para el MVP** | depende del PC encendido | 
| **B. DigitalOcean VM 1 GB/$6 o similar** (pricing Render 1c-2g = $25) puede ser excesivo | estable, IP fija | $6-12/mes; requiere admin de Linux |
| **C. Render free 512 MB** | 0 | **No aguanta ni onnx (666 MB)**; solo útil si se pasa el RAG fuera (pro). No se recomienda para el MVP |

**Config por env recomendada para producción (VM o PC):**

```env
EMBEDDINGS_BACKEND=onnx   # -40% de RAM frente a torch; misma calidad y sin reindexar
```

En `DEPLOY.md` se actualiza la sección "Plan gratis" con estas cifras.

*A todas luces*: con `EMBEDDINGS_BACKEND=onnx` no se reindexa; si
universitariamente se adota potion (256 dims), correr el script que debe
quedar pendiente: (no incluido — ver §3).
