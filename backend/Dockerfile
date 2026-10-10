FROM python:3.12-slim

WORKDIR /app

# Caché del modelo DENTRO de la imagen: el disco de Render libre es
# EFÍMERO, así que el modelo de embeddings queda horneado en la imagen
# (sin descargas en el arranque de cada cold start). fastembed 0.7.3
# resuelve su caché por FASTEMBED_CACHE_PATH (ignora HF_HOME y usa /tmp
# si no se fija, lo que quedaria en un dir efímero por contenedor).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/app/model-cache \
    HF_HOME=/app/model-cache/hf

# Motor de embeddings: "torch" (por defecto, como siempre) u "onnx" (fastembed,
# -40% de RAM y -~2.4 GB de imagen, vectores idénticos; ver
# docs/perf/INFORME_MEMORIA.md). Se elige con build-arg al construir:
#   docker build --build-arg EMBEDDINGS_BACKEND=onnx -t insoft-backend .
ARG EMBEDDINGS_BACKEND=torch
ENV EMBEDDINGS_BACKEND=${EMBEDDINGS_BACKEND}

RUN if [ "$EMBEDDINGS_BACKEND" = "onnx" ]; then \
        pip install --no-cache-dir fastembed==0.7.3; \
    else \
        # Torch CPU-only primero: evita que pip jale los wheels de CUDA (varios GB)
        # cuando sentence-transformers declare torch como dependencia.
        pip install torch --index-url https://download.pytorch.org/whl/cpu && \
        pip install --no-cache-dir sentence-transformers==6.0.1; \
    fi

COPY requirements.txt .
RUN if [ "$EMBEDDINGS_BACKEND" = "onnx" ]; then \
        grep -v sentence-transformers requirements.txt > /tmp/req.txt && pip install --no-cache-dir -r /tmp/req.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Precarga el modelo de embeddings en la imagen (sin esto se descargaría
# en el primer request del contenedor). Igual de obligatorio en ONNX: la
# descarga en runtime no sirve en Render (disco efímero = re-descarga en
# cada cold start y arranque de +minutos).
RUN if [ "$EMBEDDINGS_BACKEND" = "onnx" ]; then \
        python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"; \
    else \
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"; \
    fi

COPY app ./app

EXPOSE 8000

# El puerto lo decide la plataforma (PORT en Render); por defecto 8000.
# Sin --reload: imagen de producción.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
