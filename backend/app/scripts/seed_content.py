"""Reseed manual del contenido oficial.

Uso (desde backend/ o dentro del contenedor):

    python -m app.scripts.seed_content            # respeta SEED_MODE
    python -m app.scripts.seed_content --force    # seed completo sin importar SEED_MODE

Con --force recarga (por posición) las 8 unidades del seed y sus preguntas
oficiales; útil tras una corrección de contenido validada. Las unidades que
no están en el seed (p. ej. la unidad 9) no se ven afectadas.
"""
from __future__ import annotations

import argparse
import sys

from app.core.config import settings
from app.database.session import SessionLocal
from app.seed.seed_content import seed_official_content, run_seed_by_mode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Seed completo sin importar SEED_MODE (recarga por posición).",
    )
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if args.force:
            seed_official_content(db)
            summary = {"seed": "forced"}
        else:
            summary = run_seed_by_mode(db, settings.seed_mode_effective) or {}
    finally:
        db.close()

    print("[seed] LISTO:", summary)
    if summary.get("seed") == "if_empty" and not summary.get("cargado", True):
        print(
            "[seed] La BD ya tiene unidades: con SEED_MODE=if_empty el arranque "
            "no las modifica. Usa --force para recargar el contenido del seed."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
