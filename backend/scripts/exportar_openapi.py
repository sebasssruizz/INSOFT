#!/usr/bin/env python3
"""4.1 — Export y verificación del CONTRATO OpenAPI de la API (docs/api/openapi.json).

- `--exportar`  : genera/refresca docs/api/openapi.json a partir de la app
                  (sin arrancar servidores ni conectar a la base de datos).
- `--verificar` (default): sale con 1 si el openapi.json vive distinto de
                  lo que genera la app (cambio de contrato sin actualizar
                  el snapshot).

Uso:
  python backend/scripts/exportar_openapi.py --exportar
  python backend/scripts/exportar_openapi.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # backend/
DESTINO = RAIZ.parent / "docs" / "api" / "openapi.json"


def generar() -> dict:
    sys.path.insert(0, str(RAIZ))
    os_env = {"DOCS_ENABLED": "true", "ENVIRONMENT": ""}
    import os

    previo = {k: os.environ.get(k) for k in os_env}
    for k, v in os_env.items():
        if v:
            os.environ[k] = v
    try:
        from app.core.config import settings

        settings.DOCS_ENABLED = True
        from app.main import create_app

        app = create_app()
        esquema = app.openapi()
    finally:
        for k, v in previo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return esquema


def comparar(esquema: dict) -> bool:
    # Ignora diferencias de orden de claves (json canonical sort_keys).
    actual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""
    try:
        iguales = bool(actual) and json.loads(actual) == esquema
    except json.JSONDecodeError:
        iguales = False
    if iguales:
        rutas = len(esquema.get("paths", {}))
        print(f"OK: docs/api/openapi.json coincide con la app ({rutas} rutas documentadas)")
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exportar", action="store_true")
    args = ap.parse_args()

    esquema = generar()
    if args.exportar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(esquema, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        print(f"openapi.json escrito: {len(esquema.get('paths', {}))} rutas")
        return 0
    iguales = comparar(esquema)
    if not iguales:
        print("DESINCRONIZADO: el openapi.json no coincide con la app actual.")
        print("Regenera con: python backend/scripts/exportar_openapi.py --exportar")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
