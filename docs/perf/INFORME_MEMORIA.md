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
  proveedores tipo OpenAI embeddings o Gemini
  text-embedding-004: depende de cuota y SLA, agrega latencia por llamada y
  **requeriría reindexado** si el modelo es distinto. Para el piloto la
  recomendación es la ruta local = no llamada API externa.

## 4. Recomendación de despliegue

| Decisión | Pro | Contra |
|---|---|---|
| **A. PC local + Docker + túnel** (Cloudflare/Tailscale), como en `feat/deploy-prod` | costo 0, sin límites de RAM, ya probado — **recomendado para el MVP** | depende del PC encendido | 
| **B. DigitalOcean VM 1 GB/$6 o similar** (pricing Render 1c-2g = $25) puede ser excesivo | estable, IP fija | $6-12/mes; requiere admin de Linux |
| **C. Render free 512 MB** | 0 | **No aguanta ni onnx (666 MB)**; solo útil si se pasa el RAG fuera (pro). No se recomienda para el MVP |

**Config por env recomendada para producción (VM o PC):**

```env
EMBEDDINGS_BACKEND=onnx   # -40% de RAM frente a torch; misma calidad y sin reindexar
```

En `DEPLOY.md` se actualiza la sección "Plan gratis" con estas cifras.

**Reindexado al cambiar de backend:** `torch → onnx` con el mismo modelo
(`paraphrase-multilingual-MiniLM-L12-v2`) **NO obliga a reindexar**: mismo
modelo 384d, vectores idénticos (coseno 1.0000). Solo hay que reindexar si
cambia el modelo (p. ej. potion, 256 dims): en ese caso vaciar la columna
`embedding` de los chunks y regenerarla con `embed_batch` (el pipeline de
ingesta existente; script único de reindexado queda como deuda definida),
sin tocar los datos de la base real (trabajar sobre una base desechable).

**Horneado del modelo en la imagen (2026-10-09):** el Dockerfile ahora fija
`HF_HOME=/app/hf-cache` y precarga el modelo en build tanto para torch como
para onnx, de modo que no hay descargas en el arranque (el disco de Render
free es efímero y cada cold start re-descargaría ~220 MB).

## 5. Conciliación de cifras (2026-10-10, mismos condiciones)

Para comparar de verdad, se midieron torch y onnx CON EL BACKEND COMPLETO
(uvicorn + FastAPI + SQLAlchemy + RAG con pgvector) via `docker stats` de
contenedor, contra el mismo Postgres desechable, mismo seed (contenido
oficial: 26 subtemas / 128 chunks), LLM simulado sin red (modo degradado) y
10 consultas RAG secuenciales.

| métrica (contenedor docker, docker stats) | torch | onnx |
|---|---|---|
| reposo ANTES de la primera consulta (modelo lazy, no cargado) | 147 MB | 103 MB |
| RAM estable tras la carga del modelo (1ª consulta) | 1 054 MB | **697 MB** |
| RAM tras 10 consultas RAG | 1 053 MB | 697 MB (sin fuga) |
| 10 consultas totales | 42.1 s | 23.5 s |
| imagen (docker, on-disk) | ~2.9 GB | 1.27 GB |

(Anteriores cifras del propio informe —torch 1 121 MB / onnx 666 MB— se
midiaron sobre procesos python en un script de medición: la diferencia con
la tabla se explica porque acá el backend HTTP y las librerías están cargadas
también inmediatamente del modelo; de cuidado comparar processes vs docker
stats: esta tabla es LA referencia común para ambas plataformas.)

### ¿Por qué onnx marca ~697 MB en reposo si el ahorro era del 40 %?

1. El 40 % del informe (torch 1 121 → onnx 666 MB) comparó **RSS del
   proceso python**, no todo el contenedor. Con backend completo el
   ahorro real medido es torch 1 054 GB → onnx 697 = **−34 %**: mismo orden
   de magnitud, se sostiene la recomendación.
2. La RAM de la app NO depende del backend: FastAPI+SQLAlchemy+pgvector
   ponen ~105-147 MB de piso en ambos cases; se suman por encima del motor
   del embeddings y no desaparecen con onnx.
3. El peso del ahorro está en el STACK torch-vs-onnx: torch carga
   pytorch + sentence-transformers (runtime pesado, ~900 MB sobre el piso);
   onnxruntime carga el mismo modelo 384d con ~600 MB de runtime. Los propios
    pesos del modelo pesan casi lo mismo (~130 MB en ambos): el ahorro
   grande no viene del modelo, sino de librar menos pytorch.
4. El dato "reposo ~697 MB" CONSISTE con modelo YA CARGADO (carga perezosa
   en la primera consulta). Antes de la primera consulta hay solo los
   103-147 MB de piso.

### Backend recomendado por ruta de despliegue

| Ruta | backend | Motivo |
|---|---|---|
| PC compose (MVP, PRI línea) | `onnx` (default del compose, PR #38) | −35 % RAM y boot 10 veces más rápido para las consultas; ocupa Postgres	Default convive en la misma máquina |
| VM producción final (≥2 GB) | `onnx` | misma razón; deja margen para Postgres y picos |
| Render pago (≥1c-2g) | `onnx` | menos RAM ocupada; imagen más pequeña que build más corto |
| Tests/CI local con venv | `torch` (default en config.py) | entorno prep validado; no tocar si no hay necesidad |
