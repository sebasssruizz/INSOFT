# Informe de pruebas del backend (4.2)

Generado por `backend/scripts/correr_pruebas.py` el 2026-10-15 00:08.
Corrida por lotes (presupuesto de RAM); JUnit por lote en `backend/.pruebas/junit/`.

## Resumen

| pasó | falló | error | saltado | tiempo total |
|---|---|---|---|---|
| 247 | 1 | 0 | 2 | 339 s |

## Detalle por lote

| lote | archivos | pasó | falló | error | s |
|---|---|---|---|---|---|
| lote-000 | test_ai_ask.py, test_ai_history.py, test_ai_robustez.py, test_ai_stats.py, test_auth_end | 67 | 0 | 0 | 76.5 |
| lote-001 | test_embeddings_backend.py, test_embeddings_service.py, test_flows.py, test_gemini_provi | 34 | 0 | 0 | 92.6 |
| lote-002 | test_observability.py, test_pilot_import.py, test_practice_mode.py, test_question_genera | 76 | 1 | 0 | 98.2 |
| lote-003 | test_rag_global_scope.py, test_role_matrix.py, test_score_sus.py, test_semilla_segura.py | 70 | 0 | 0 | 72.0 |

Cobertura: ver `backend/.pruebas/cobertura.txt` (generar con: pytest --cov ... --cov-report=term-missing).

## Cobertura global

`pytest-cov --cov=app` con la misma corrida por lotes: **88 %** de la app
(3368 sentencias / 412 omitidas). JSON completo en
`backend/.pruebas/cobertura.json` (no versionado).

## Único fallo y su arreglo

`test_question_migration.py::test_migracion_idempotente` importaba
`ensure_schema_compatibility`, función eliminada al versionar migraciones
(PR #45). Corregido en esta misma rama: ahora llama `run_migrations()` dos
veces (6/6 tests del archivo tras el arreglo).

## Cómo reproducir

```bash
python backend/scripts/correr_pruebas.py            # por lotes + junit + informe
python backend/scripts/correr_pruebas.py --cov      # + cobertura pytest-cov
python backend/scripts/correr_pruebas.py --lote 4   # lotes más pequeños (RAM justa)
python backend/scripts/correr_pruebas.py --solo "test_rag_auth.py"   # subset
```

- Cada lote es un PROCESO pytest independiente: la RAM no se acumula (el
  lote con más pico consumió < 400 MB; host vigilado en 7.8 GB no llegó a
  swap). RAM disponible impresa por lote.
- JUnit: `backend/.pruebas/junit/lote-XXX.xml` — CI puede consumirlos un
  por uno sin reejecutar nada.
- La semilla de orden es fija (`-p no:randomly`): reproducción determinista.
  La suite sigue estando independiente del orden (pytest-randomly queda en
  requirements-dev para auditorías puntuales).
