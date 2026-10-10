"""Bootstrap remoto: deja una base NUEVA lista para servir (PC- compose o Neon).

Un solo comando para el arranque remoto del MVP:
    1. esquema (extension vector + migraciones aditivas + create_all),
    2. contenido oficial (8 unidades + preguntas + Curso General),
    3. indexación RAG de los chunks con el backend de embeddings configurado,
    4. (opcional) promover un correo docente ya creado por login.

Seguridad de ejecución:
    - DRY-RUN por defecto: no escribe nada sin `--apply`.
    - El host de destino se imprime ENMASCARADO y, para escribir, DEBE
      confirmarse con `--confirm-host <host-real>` (nombre exacto del host
      de la DATABASE_URL). Evita apuntar a la base equivocada.
    - Idempotente seed/migración/indexado: se puede relanzar sin errores
      (reindexado es delete+insert controlado, nunca toca otras tablas).

El repo es PÚBLICO: el contenido oficial ya está versionado dentro de
backend/app/seed/seed_content.py (no se añade contenido nuevo a content/;
no se commitean pdf/docx/pptx/mp4/zip).

No inventa contenido médico: todo el texto viene del seed oficial existente.

Ejemplos:
    # PC local con el compose (base del PC):
    DATABASE_URL=postgresql+psycopg2://USER:PASS@127.0.0.1:5433/DB \
      python -m app.scripts.bootstrap_remote

    # Neon (usa la URL DIRECTA sin -pooler; si das la agrupada, el script
    # deriva la directa para DDL automáticamente):
    DATABASE_URL=postgresql+psycopg2://...neon.tech/DB?sslmode=require \
      python -m app.scripts.bootstrap_remote

    python -m app.scripts.bootstrap_remote --apply --confirm-host <host> \
      --teacher-email docente@institucion.edu
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database.session import SessionLocal, ddl_engine, engine  # noqa: E402


def mask_host(url: str) -> str:
    """Enmascara el host de una URL: deja 2+2 caracteres y oculta el resto.

    Nunca imprime credenciales ni rutas de la base.
    """
    host = url.split("@")[-1].split("/")[0].split("?")[0].split(":")[0]
    if len(host) <= 4:
        return f"*({len(host)})*"
    return f"{host[:2]}{'*' * (len(host) - 4)}{host[-2:]}"


def expected_host() -> str:
    """Host real (sin enmascarar) de la URL configurada."""
    return settings.DATABASE_URL.split("@")[-1].split("/")[0].split("?")[0].split(":")[0]


def step_schema() -> str:
    """Extension vector + migraciones aditivas + create_all (todo idempotente).

    Va por ddl_engine (conexión directa necesaria en Neon para DDL).
    """
    from app.database.base import Base
    import app.models  # noqa: F401  (registra todas las tablas)
    from app.database.migrations import ensure_schema_compatibility

    ensure_schema_compatibility()
    Base.metadata.create_all(bind=ddl_engine)
    with ddl_engine.connect() as conn:
        n_tables = conn.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
        ).scalar()
    return f"esquema OK ({n_tables} tablas públicas)"


def step_content() -> str:
    """Importa el contenido oficial y asegura el Curso General (idempotente)."""
    from app.seed.seed_content import seed_official_content

    db = SessionLocal()
    try:
        seed_official_content(db)
        return "contenido oficial OK (8 unidades + Curso General)"
    finally:
        db.close()


def step_index() -> str:
    """Indexa (o reindexa) el RAG de todo el contenido (idempotente)."""
    from app.seed.index_content import index_all_content

    db = SessionLocal()
    try:
        n_subtopics, n_chunks = index_all_content(db)
        backend = settings.EMBEDDINGS_BACKEND
        return f"indexado OK ({n_subtopics} subtemas, {n_chunks} chunks, embeddings={backend})"
    finally:
        db.close()


def step_teacher(email: str) -> str:
    """Promueve un correo ya registrado a TEACHER (idempotente)."""
    from sqlalchemy import select

    from app.models.user import User, UserRole

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            return (
                f"docente SALTADO: {email} no está registrado todavía "
                "(inicia sesión primero con Google y relanza este paso)"
            )
        if user.role == UserRole.TEACHER:
            return f"docente OK: {email} ya es TEACHER"
        user.role = UserRole.TEACHER
        db.commit()
        return f"docente OK: {email} promovido a TEACHER"
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap de base remota (PC-compose o Neon). DRY-RUN por defecto."
    )
    parser.add_argument("--apply", action="store_true", help="Escribir cambios (default: no)")
    parser.add_argument(
        "--confirm-host",
        default="",
        metavar="HOST",
        help="Host exacto de DATABASE_URL para autorizar --apply (imprescindible)",
    )
    parser.add_argument(
        "--teacher-email",
        default="",
        help="Correo a promover a TEACHER si ya existe (opcional)",
    )
    parser.add_argument("--skip-index", action="store_true", help="No (re)indexar el RAG")
    args = parser.parse_args()

    url = settings.DATABASE_URL
    host_real = expected_host()
    pooled = "-pooler." in url
    print("Bootstrap de base remota")
    print(f"  backend de embeddings : {settings.EMBEDDINGS_BACKEND}")
    print(f"  host enmascarado      : {mask_host(url)}")

    if args.apply and not args.confirm_host:
        print(
            "\nNEGADO: --apply exige --confirm-host con el nombre completo del "
            "host de la DATABASE_URL (protege de apuntar a la base equivocada).\n"
            f"Sugerencia: --confirm-host '{mask_host(url)}' NO vale; usa el "
            f"nombre COMPLETO ({host_real[:2]}***{host_real[-2:]} sin máscara)."
        )
        return 2

    if args.apply and args.confirm_host != host_real:
        print(f"\nNEGADO: el host indicado ({args.confirm_host!r}) no coincide con la base configurada ({host_real!r}).")
        return 2

    plan = [
        "1. Esquema: extension vector + migraciones + create_all (por la URL directa para DDL)",
        "2. Contenido oficial + Curso General (seed ya versionado en el repo, no se inventa contenido)",
        "3. Indexado RAG de chunks (idempotente)" if not args.skip_index else "3. Indexado RAG: SALTADO (--skip-index)",
        f"4. docente: {args.teacher_email or '(no pedido; el usuario debe existir por login)'}",
    ]
    print(f"\nMODO: {'APPLY' if args.apply else 'DRY-RUN'} (idempotente; relanzable sin daño)")
    for item in plan:
        print(f"  - {item}")
    print(f"  - URL: {'AGRUPADA (-pooler): el DDL irá igual por la directa' if pooled else 'directa (sin -pooler): app y DDL por la misma'}")

    if not args.apply:
        print("\nDRY-RUN: nada se ha escrito. Repite con --apply --confirm-host para ejecutar "
              "realmente estos pasos contra la base configurada.")
        return 0

    try:
        print("\n[1/4] " + step_schema())
        print("[2/4] " + step_content())
        if not args.skip_index:
            print("[3/4] " + step_index())
        else:
            print("[3/4] saltado")
        if args.teacher_email:
            print("[4/4] " + step_teacher(args.teacher_email))
        else:
            print("[4/4] docente: no solicitado")
    except Exception as exc:  # noqa: BLE001 - CLI feedback
        print(f"\nERROR en el bootstrap: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print(
            "Pistas: si la caja es Neon acaba en -pooler, usa la URL DIRECTA "
            "(sin -pooler) o renombra DATABASE_URL de acuerdo; si suspendió el "
            "cómputo (primer arranque), reintenta en 30-60 s.",
            file=sys.stderr,
        )
        return 1

    print("\nBootstrap completado. Verificación rápida sugerida: curl /api/health "
          "y /api/ready del backend contra esa base.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
