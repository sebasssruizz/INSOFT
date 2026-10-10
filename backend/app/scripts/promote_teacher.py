"""Promueve una cuenta a TEACHER — por defecto DRY-RUN (T-fix rol).

TEACHER_EMAILS solamente actúa al CREAR una cuenta: para cuentas ya
existentes usa este script. NO se ejecutó --apply en esta sesión.

Uso:
    python backend/app/scripts/promote_teacher.py --email x@dominio
    python backend/app/scripts/promote_teacher.py --email x@dominio --apply
    python backend/app/scripts/promote_teacher.py --email x@dominio --demote --apply  # reversa
"""
import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def run(email, apply, demote):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            raise SystemExit(f"No existe un usuario con el correo {email!r} en esta base.")
        rol_actual = user.role.value
        desired = UserRole.STUDENT if demote else UserRole.TEACHER
        accion = "bajar" if demote else "PROMOVER"

        print(f"Usuario #{user.id} {user.email} · rol actual = {rol_actual}")
        if user.role == desired:
            print(f"Ya tiene el rol {desired.value}; nada que cambiar.")
            return
        print(f"DRY-RUN: {accion} el rol a {desired.value}. Para aplicar añade --apply"
              if not apply else f"APLICANDO: rol → {desired.value}")

        if apply:
            user.role = desired
            db.commit()
            db.refresh(user)
            print(f"Listo. {user.email} ahora es {user.role.value}.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Asigna rol docente estable (dry-run por defecto)")
    parser.add_argument("--email", required=True)
    parser.add_argument("--apply", action="store_true", help="Escribir el cambio (default: no)")
    parser.add_argument("--demote", action="store_true", help="Bajar a STUDENT en vez de promover")
    args = parser.parse_args()
    run(args.email, args.apply, args.demote)


if __name__ == "__main__":
    main()
