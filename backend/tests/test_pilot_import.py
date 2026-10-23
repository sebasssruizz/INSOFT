"""Test del cargador del piloto (T7): idempotencia y validación con SQLite temporal.

El script NO corre contra la base real aquí: usa la DB temporal de la suite.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import csv  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models.course import Course, CourseMembership  # noqa: E402
from app.models.user import User  # noqa: E402
from sqlalchemy import func, select  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

CSV = Path(__file__).resolve().parent.parent.parent / "docs" / "piloto" / "plantilla_estudiantes.csv"


@pytest.fixture(scope="module")
def curso_code():
    with TestClient(app) as c:
        r = c.post("/api/auth/dev", json={"email": "piloto-owner@x.com", "name": "N", "role": "TEACHER"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        course = c.post(
            "/api/courses", json={"name": "Curso Piloto"}, headers={"Authorization": f"Bearer {token}"}
        ).json()
        yield course["code"]


def _counts():
    with SessionLocal() as s:
        users = s.scalar(select(func.count(User.id)))
        memberships = s.scalar(select(func.count(CourseMembership.id)))
    return users, memberships


def test_import_piloto_idempotente_con_rechazados(curso_code):
    from app.scripts.import_pilot_users import run

    assert CSV.exists(), "falta docs/piloto/plantilla_estudiantes.csv"

    run(False, str(CSV), curso_code)  # dry-run
    users0, memb0 = _counts()

    run(True, str(CSV), curso_code)  # aplica
    users1, memb1 = _counts()
    with SessionLocal() as s:
        course = s.scalar(select(Course).where(Course.code == curso_code))
        nuevos = [u for u in s.scalars(select(User)).all() if u.google_id.startswith("pilot-")]
    assert len(nuevos) == 3, "3 emails válidos (uno del CSV es inválido)"
    assert all(u.role.value == "STUDENT" for u in nuevos)
    assert memb1 > memb0

    # correr de nuevo -> idempotencia (cero usuarios nuevos)
    run(True, str(CSV), curso_code)
    users2, memb2 = _counts()
    assert users2 == users1 and memb2 == memb1
