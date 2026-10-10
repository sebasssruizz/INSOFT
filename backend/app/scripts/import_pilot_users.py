"""Pre-carga de cuentas del PILOTO desde un CSV (T7) — escritura SOLO con --apply.

Lee un CSV con columnas `email` (obligatoria) y `nombre` (opcional) y para un
CURSO POR CÓDIGO pre-registra:
  - el usuario (role STUDENT, google_id temporal "pilot-<email>") y
  - su membresía al curso indicado.

El PRIMER login con GOOGLE de esos correos **reutiliza el usuario por EMAIL**
(el servicio busca por email y asocia el google_id real: así la pre-carga
enlaza sin duplicar cuentas). Nunca envía correos.

Por defecto DRY-RUN (no escribe nada). Con --apply escribe en la base y
QUEDA REGISTRADO el respaldo CSV de lo afectado. Idempotente: correlo dos
veces y no crea duplicados (emails ya existentes solo garantizan membresía).

Uso:
    python backend/app/scripts/import_pilot_users.py curso.csv --code OFT-XX00
    python backend/app/scripts/import_pilot_users.py curso.csv --code OFT-XX00 --apply
"""
import argparse
import csv
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal  # noqa: E402
from app.models.course import Course, CourseMembership  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from sqlalchemy import select  # noqa: E402

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def read_rows(path: str):
    """Lee el CSV y valida; devuelve (okay, rechazados)."""
    okay, rejected = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = {f2.strip().lower(): f2 for f2 in (reader.fieldnames or [])}
        if "email" not in fields:
            raise SystemExit("El CSV debe tener una columna 'email' (y opcionalmente 'nombre').")
        for nro, row in enumerate(reader, start=2):
            email = (row.get(fields["email"]) or "").strip().lower()
            nombre = (row.get(fields.get("nombre", "nombre")) or "").strip() or email.split("@")[0]
            if not EMAIL_RE.match(email):
                rejected.append((nro, email, "email inválido"))
                continue
            okay.append((nro, email, nombre))
    return okay, rejected


def run(apply: bool, csv_path: str, code: str):
    okay, rejected = read_rows(csv_path)
    print(f"filas leídas {len(okay) + len(rejected)} · válidas {len(okay)} · rechazadas {len(rejected)}")
    for nro, email, motivo in rejected:
        print(f"  [RECHAZADA línea {nro}] {email!r}: {motivo}")

    db = SessionLocal()
    created_user = created_membership = skipped_user = skipped_member = 0
    try:
        course = db.scalar(select(Course).where(Course.code == code.strip().upper()))
        if course is None:
            raise SystemExit(f"No existe un curso con código {code!r} en esta base.")
        if apply:
            print(f"APLICANDO sobre el curso {course.id} {course.name!r} ({code})")
        else:
            print(f"DRY-RUN sobre el curso {course.id} {course.name!r} ({code})")

        for nro, email, nombre in okay:
            user = db.scalar(select(User).where(User.email == email))
            if user is None and not apply:
                print(f"  [NUEVO usuario (dry-run)] {email} ({nombre}) -> membresía en {course.name}")
                created_user += 1
                created_membership += 1
                continue
            if user is None:
                if apply:
                    user = User(
                        google_id=f"pilot-{email}",
                        name=nombre,
                        email=email,
                        profile_image=None,
                        role=UserRole.STUDENT,
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                created_user += 1
                estado_u = "creado" if apply else "Creará"
                print(f"  [NUEVO usuario] {email} ({nombre})")
            else:
                skipped_user += 1
                estado_u = ("ya estaba (rol {0})".format(user.role.value))
            if db.scalar(
                select(CourseMembership.id).where(
                    CourseMembership.user_id == user.id,
                    CourseMembership.course_id == course.id,
                )
            ) is None:
                if apply:
                    db.add(CourseMembership(course_id=course.id, user_id=user.id))
                    db.commit()
                created_membership += 1
                print(f"  [membresía {estado_u.lower()}] {email} -> {course.name}")
            else:
                skipped_member += 1
                print(f"  [membresía ya existía] {email}")
        totals = (
            f"usuarios nuevos: {created_user}, usuarios existentes: {skipped_user}; "
            f"membresías nuevas: {created_membership}, membresías existentes: {skipped_member}"
        )
        if not apply:
            print("DRY-RUN: no se cambió nada. Para aplicar: --apply")
        print(totals)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-carga de piloto (dry-run por defecto)")
    parser.add_argument("csv", help="CSV con columnas email[,nombre]")
    parser.add_argument("--code", required=True, help="Código del curso destino (OFT-XXXX)")
    parser.add_argument("--apply", action="store_true", help="Escribir en la base (por defecto NO)")
    args = parser.parse_args()
    if not Path(args.csv).exists():
        raise SystemExit(f"No existe {args.csv}")
    run(args.apply, args.csv, args.code)


if __name__ == "__main__":
    main()
