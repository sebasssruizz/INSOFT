# 3.6 — Humo del LLM: plan y script (sin ejecutar)

**Fecha**: 2026-10-15 · **Rama**: `feat/eval-recuperacion`

## Qué es

El script existente `backend/scripts/test_openrouter_models.py` funciona
como **humo del proveedor**: toma las preguntas del banco, normaliza y
recupera top-3 por similitud (misma mecánica que `/rag/search`) pide
respuesta con `minimax/minimax-m2:free` y `liquid/lfm-2.5-2.6b:free`, y
imprime latencia+chunks+respuesta. Todo auto-contenida, sin tocar datos
de producción (es para el DEV) y NO se ejecuta en esta sesión por
decisión de la tarea.

## Cómo correrlo (paso manual, cuando toque)

```bash
# 1) Trabajando en local, con la key en archivo .env real (nunca versionada):
#   OPENROUTER_API_KEY=sk-or-v1-XXXXX  (solo en tu .env local)
cd backend && source .venv/bin/activate
python scripts/test_openrouter_models.py
```

Qué se espera: 3 preguntas con 3 chunks relevantes cada una; mínimo 1
respuesta usable sin alucinación grave en el banco pterigión. Costo: 2
modelos gratuitos, ~10 llamadas; ninguna operación de escritura.

## Qué mantiene la sesión esta rama

- Compilación verificada del script (`py_compile` OK) y SIN llamadas al
  proveedor (la prueba NO se corrió; el script exige key en .env y no corre sin ella).
- Complemento: `evaluar_recuperacion_offline.py` (3.7) mide la
  recuperación SIN proveedor (TF-IDF local): es el humo "frío" que ya
  corregas sin API ni créditos.
