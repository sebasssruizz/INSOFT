"""Crea usuarios de ENSAYO y emite sus tokens (solo para el ensayo local tipo Neon).

Se ejecuta DENTRO del contenedor del backend del ensayo, que usa la misma
configuración de producción (sin login de desarrollo). Crea o reutiliza los
usuarios por correo y emite un JWT firmado con la SECRET_KEY del ensayo.
Imprime un JSON por stdout: el llamador lo guarda con permisos 600.

    docker exec tmp-ensayo-backend python scripts/ensayo_tokens.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.auth.jwt import create_access_token  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services import course_service  # noqa: E402

USUARIOS = {
    "estudiante": ("ensayo-estudiante@example.com", "Estudiante Ensayo", UserRole.STUDENT),
    "otro_estudiante": ("ensayo-otro@example.com", "Otro Estudiante", UserRole.STUDENT),
    "docente": ("ensayo-docente@example.com", "Docente Ensayo", UserRole.TEACHER),
}


def main() -> None:
    salida = {}
    with SessionLocal() as db:
        for clave, (email, nombre, rol) in USUARIOS.items():
            usuario = db.scalar(select(User).where(User.email == email))
            if usuario is None:
                usuario = User(google_id=f"ensayo-{clave}", email=email, name=nombre, role=rol)
                db.add(usuario)
                db.commit()
                db.refresh(usuario)
            if rol == UserRole.STUDENT:
                # Igual que el registro real (auth_service): todo estudiante entra al Curso General.
                course_service.enroll_student_in_general_course(db, usuario)
                db.commit()
            salida[clave] = {
                "id": usuario.id,
                "token": create_access_token(usuario.id, usuario.role.value),
            }
    print(json.dumps(salida))


if __name__ == "__main__":
    main()
