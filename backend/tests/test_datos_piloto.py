"""3.5 — datos del piloto: exporte anonimizado, baja con anonimización y retención.

Sin red: sqlite + dev-auth (superficie de prueba consolidada).
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.ai_query import AiQuery  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import datos_piloto  # noqa: E402


EMAIL = "piloto3dot5@example.com"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    r = client.post("/api/auth/dev", json={"email": EMAIL, "name": "Piloto", "role": "STUDENT"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_exporte_sin_pii_de_contacto(client, auth):
    r = client.get("/api/users/me/export", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["pseudonimo"]) == 16
    assert "email" not in body and "google_id" not in body
    assert "email" not in body["perfil"] and "google_id" not in body["perfil"]
    assert set(body) >= {"generado", "perfil", "progreso", "consultas_ia", "respuestas_practica"}


def test_baja_anonimiza_manteniendo_integridad(client, auth):
    db = SessionLocal()
    pseudonimo_esperado = datos_piloto.pseudonimo(
        db.query(User).filter(User.email == EMAIL).first().id
    )
    db.close()

    r = client.delete("/api/users/me", headers=auth)
    assert r.status_code == 204, r.text

    db = SessionLocal()
    assert db.query(User).filter(User.email == EMAIL).first() is None
    anon = (
        db.query(User)
        .filter(User.email == f"eliminado-{pseudonimo_esperado}@ejemplo.invalid")
        .first()
    )
    assert anon is not None
    assert anon.name == "Estudiante eliminado"
    assert anon.country is None and anon.age is None
    assert anon.profile_image is None
    # segunda pasada idempotente
    datos_piloto.anonimizar_user(db, anon)
    db.close()


def test_retencion_purga_consultas_antiguas():
    settings.AI_QUERY_RETENTION_DAYS = 30
    db = SessionLocal()
    u = db.query(User).order_by(User.id.desc()).first()
    assert u is not None
    for dias in (45, 1):
        db.add(
            AiQuery(
                user_id=u.id,
                question_original="¿pterigión?",
                created_at=datetime.now(timezone.utc) - timedelta(days=dias),
            )
        )
    db.commit()
    antes = db.query(AiQuery).filter(AiQuery.user_id == u.id).count()
    assert antes >= 2
    eliminadas = datos_piloto.purgar_ai_anteriores(db)
    despues = db.query(AiQuery).filter(AiQuery.user_id == u.id).count()
    assert despues == antes - eliminadas
    assert despues >= 1  # la consulta de 1 día queda
    db.close()


def test_retencion_cero_desactivada():
    settings.AI_QUERY_RETENTION_DAYS = 0
    db = SessionLocal()
    assert datos_piloto.purgar_ai_anteriores(db) == 0
    db.close()
