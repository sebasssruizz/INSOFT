# Bootstrap remoto (`bootstrap_remote.py`)

Deja una base **nueva** lista para servir: esquema, contenido oficial, RAG indexado y,
opcionalmente, un docente. Código: `backend/app/scripts/bootstrap_remote.py`.
Pruebas de los controles: `backend/tests/test_bootstrap_remote.py`.

## Uso

```bash
cd backend
# 1) Simulación (no escribe nada). Muestra el host ENMASCARADO.
DATABASE_URL=… PYTHONPATH=. .venv/bin/python -m app.scripts.bootstrap_remote

# 2) Ejecución real. El host de --confirm-host debe ser el host COMPLETO de DATABASE_URL.
DATABASE_URL=… PYTHONPATH=. .venv/bin/python -m app.scripts.bootstrap_remote \
  --apply --confirm-host <host-completo> [--teacher-email correo@institución] [--skip-index]
```

Pasos (idempotentes; relanzar no daña nada):

1. Esquema: `ensure_pgvector_extension` → `create_all` → `run_migrations` (ver `docs/database/MIGRACIONES.md`).
2. Contenido oficial y Curso General (`seed_official_content`).
3. Indexado RAG de los fragmentos con el backend de embeddings configurado (`EMBEDDINGS_BACKEND`).
4. Promoción de un correo ya registrado a `TEACHER` (opcional; el usuario debe haber entrado antes con Google).

## Controles de seguridad

- **Dry-run por defecto**: sin `--apply` no se escribe nada.
- `--apply` sin `--confirm-host`, o con un host distinto al de `DATABASE_URL`, se **niega** (exit 2).
  Enmascarar el host (`12*****.1`) no sirve como confirmación.
- Las credenciales nunca se imprimen.

## Verificación realizada (oct 2026)

Base desechable: contenedor `pgvector/pgvector:pg16` sin volumen, puerto solo en localhost,
destruido al terminar.

| Prueba | Resultado |
|---|---|
| Dry-run sobre base vacía | Sin escrituras (0 tablas). |
| `--apply` sin confirmación | Negado. |
| `--apply --confirm-host <host real>` | Esquema 12 tablas, 9 unidades + Curso General, 85 preguntas oficiales, 26 subtemas, 128 fragmentos indexados (embeddings `onnx`). |
| Relanzar | Sin cambios; migraciones registradas sin duplicar. |
| `--teacher-email` (usuario existente) | Promovido a `TEACHER`; relanzar: "ya es TEACHER". |
| Pruebas de controles (`test_bootstrap_remote.py`) | 6/6. |

## Repositorio público: decisión sobre el contenido

El repositorio es **público** (`gh repo view`). Por eso **no se versiona contenido de
`docs/importacion/`** (medios, documentos, PDFs) ni se copia a `content/`. El contenido oficial
ya vive en `backend/app/seed/seed_content.py`, que el script usa. Si el repositorio pasara a
privado, habría que revisar esta decisión antes de añadir materiales.
