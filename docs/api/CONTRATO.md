# Contrato de la API (4.1): OpenAPI congelado + recorridos 22/22

**Fecha**: 2026-10-15 · **Rama**: `feat/contrato-openapi`

## Piezas

1. **`docs/api/openapi.json`** — snapshot del contrato generado desde la app
   (38 rutas, `sort_keys` para diffs estables). Se exporta/verifica con:

   ```bash
   python backend/scripts/exportar_openapi.py --exportar   # regenerar
   python backend/scripts/exportar_openapi.py              # verificar (exit 1 si difiere)
   ```

   NO requiere servidor ni base de datos: importa `create_app()` y llama
   `app.openapi()`. En CI puede correrse como guard de "contrato cambiado".

2. **Recorridos de contrato (`backend/scripts/recorridos_api.py`)** — reutiliza
   sin cambios los mismos comprobantes del ensayo local 2.8 (PR #54):
   recorridos `estudiante`, `docente`, `anonimo` (22 pasos). Aclara expectativa
   por pasos y sale con código 1 al primer desacuerdo con el contrato.

   ```bash
   backend/scripts/ensayo_tokens.py --base http://127.0.0.1:8010 > /tmp/tokens.json
   backend/scripts/recorridos_api.py --base http://127.0.0.1:8010 --tokens /tmp/tokens.json --out /tmp/recorridos.json
   ```

   Requiere el stack del ensayo (2.8, PR #54: backend mock-IA en 127.0.0.1:8010
   con DEV_AUTH_ENABLED=true). El reporte JSON de salida no contiene tokens
   (solo rutas, esperado/obtenido y latencia de cada paso).

## Registrados

- `openapi.json` ha validado con `exportar_openapi.py`, 38 rutas.
- Recorridos 22/22 con el ensayo local 2.8 (evidencia del PR #54; el stack
  desechable se creó y destruyó en esa corrida, sin datos productivos).
