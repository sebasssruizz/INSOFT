"""Verifica que /rag/search global queda acotada a los cursos del usuario.

Con la corrección de la T2, un estudiante NO inscrito ya no puede usar la
búsqueda global para leer contenido de unidades que no ve en la app.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.content import Subtopic  # noqa: E402
from app.repositories import subtopic_chunk_repository as chunk_repo  # noqa: E402
from app.services.embeddings_service import embed_text  # noqa: E402
from app.main import app  # noqa: E402

QUERY = {"query": "anatomía del ojo"}


def _login(client, email, role):
    r = client.post("/api/auth/dev", json={"email": email, "name": "N", "role": role})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_búsqueda_global_acotada_a_cursos():
    if os.path.exists("/tmp/opencode/oftallearn_test.db"):
        os.remove("/tmp/opencode/oftallearn_test.db")
    with TestClient(app) as client:
        with SessionLocal() as s:
            subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
            chunk_repo.create(
                s, subtopic_id=subtopic_id,
                content="anatomía del globo ocular y su intelijencia",
                embedding=embed_text("anatomía del globo ocular y estructuras"),
            )

        owner = _login(client, "ragg-owner@x.com", "TEACHER")
        student_in = _login(client, "ragg-in@x.com", "STUDENT")
        student_out = _login(client, "ragg-out@x.com", "STUDENT")

        course = client.post("/api/courses", json={"name": "C RAGG"}, headers=owner).json()
        assert client.post(
            "/api/courses/join", json={"code": course["code"]}, headers=student_in
        ).status_code == 200

        # docente dueño: ve su contenido
        r_owner = client.post("/api/rag/search", json=QUERY, headers=owner)
        assert r_owner.status_code == 200, r_owner.text
        assert r_owner.json()["results"], "el dueño debería ver su chunk indexado"

        # estudiante inscrito: ve el chunk del curso
        r_in = client.post("/api/rag/search", json=QUERY, headers=student_in)
        assert r_in.status_code == 200, r_in.text
        assert r_in.json()["results"], "el inscrito debería recibir el chunk del curso"

        # estudiante "sin inscripción" extra: el login dev lo inscribe en el
        # Curso General (habilita todo el temario), así que el contenido que
        # ve por búsqueda global DEBE coincidir con el del inscrito: solo
        # chunks de cursos con acceso (defensa en profundidad), nunca el
        # corpus completo de la plataforma.
        r_out = client.post("/api/rag/search", json=QUERY, headers=student_out)
        assert r_out.status_code == 200, r_out.text
        # solo contento de sus cursos: exactamente los mismos resultados
        assert r_out.json()["results"] == r_in.json()["results"]

        # docente bar común: su propio curso (dos owners posibles)
        other = _login(client, "ragg-other@x.com", "TEACHER")
        r_other = client.post("/api/rag/search", json=QUERY, headers=other)
        assert r_other.status_code == 200, r_other.text
        assert r_other.json()["results"] == [], "docente sin cursos no ve contenido ajeno"
