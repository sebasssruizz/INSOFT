"""Tests de la búsqueda RAG (/api/rag/search) y su autorización.

Usan SQLite en memoria de fichero temporal, el login de desarrollo y el modelo
local de embeddings (ya cacheado). No requieren PostgreSQL ni OAuth.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Subtopic
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.services.embeddings_service import embed_text


@pytest.fixture(scope="module")
def client():
    # El archivo SQLite es compartido por toda la suite y ya viene sembrado por
    # test_flows/test_index_content (no borrarlo: el pool del engine mantiene
    # conexiones abiertas al inode y eliminarlo rompe las demás inspecciones).
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def indexed_subtopic_id():
    """Indexa un chunk de prueba y devuelve su subtopic_id."""
    content = "el ojo duele mucho y puede indicar glaucoma"
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
        chunk_repo.create(
            s, subtopic_id=subtopic_id, content=content, embedding=embed_text(content)
        )
        return subtopic_id


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_search_sin_token_401(client: TestClient):
    resp = client.post("/api/rag/search", json={"query": "glaucoma", "limit": 3})
    assert resp.status_code == 401


def test_search_sin_subtopic_id_devuelve_resultados(client: TestClient, indexed_subtopic_id):
    student = auth_headers(client, "rag-est@example.com", "Rag Est", "STUDENT")
    resp = client.post(
        "/api/rag/search", json={"query": "dolor ocular intenso", "limit": 5}, headers=student
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["query"] == "dolor ocular intenso"
    assert data["results"]
    assert data["results"][0]["content"] == "el ojo duele mucho y puede indicar glaucoma"
    assert data["results"][0]["similarity"] is not None


def test_search_con_subtopic_permitido_solo_devuelve_ese_subtema(
    client: TestClient, indexed_subtopic_id
):
    student = auth_headers(client, "rag-est2@example.com", "Rag Est 2", "STUDENT")
    resp = client.post(
        "/api/rag/search",
        json={"query": "glaucoma presión intraocular", "limit": 5, "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["results"]
    assert all(r["subtopic_id"] == indexed_subtopic_id for r in data["results"])


def test_search_con_subtopic_sin_acceso_403(client: TestClient, indexed_subtopic_id):
    # Profesor sin cursos: ni la posee ni está inscrito -> no tiene acceso.
    teacher = auth_headers(client, "rag-profe@example.com", "Rag Profe", "TEACHER")
    resp = client.post(
        "/api/rag/search",
        json={"query": "glaucoma", "limit": 5, "subtopic_id": indexed_subtopic_id},
        headers=teacher,
    )
    assert resp.status_code == 403, resp.text


def test_search_con_subtopic_inexistente_404(client: TestClient):
    student = auth_headers(client, "rag-est3@example.com", "Rag Est 3", "STUDENT")
    resp = client.post(
        "/api/rag/search",
        json={"query": "glaucoma", "limit": 5, "subtopic_id": 999999},
        headers=student,
    )
    assert resp.status_code == 404, resp.text


def test_search_query_mas_largo_que_1000_422(client: TestClient):
    student = auth_headers(client, "rag-est4@example.com", "Rag Est 4", "STUDENT")
    resp = client.post(
        "/api/rag/search",
        json={"query": "a" * 1001, "limit": 5},
        headers=student,
    )
    assert resp.status_code == 422, resp.text