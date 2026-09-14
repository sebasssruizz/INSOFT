"""Importa un documento Markdown como contenido y lo indexa en el RAG.

Uso (desde backend/, con el entorno de la app activo):

    python -m app.scripts.import_document ../docs/importacion/ejemplo_pterigion.md

O dentro del contenedor del backend:

    docker compose exec backend python -m app.scripts.import_document /docs/importacion/ejemplo_pterigion.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.database.session import SessionLocal
from app.services.content_import import import_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path, help="Ruta al documento Markdown (.md)")
    args = parser.parse_args(argv)

    if not args.archivo.exists():
        print(f"[import] ERROR: no existe el archivo {args.archivo}", file=sys.stderr)
        return 1

    text = args.archivo.read_text(encoding="utf-8")
    db = SessionLocal()
    try:
        summary = import_document(db, text)
    except ValueError as exc:
        print(f"[import] ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print("[import] LISTO:")
    for key, value in summary.items():
        print(f"  {key:24} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())