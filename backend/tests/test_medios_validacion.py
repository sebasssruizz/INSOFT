"""3.1/3.2 — medios por subtema (lista blanca de hosts) y validación.

Sin red. El curso del docente se crea con filas directas + auth dev.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = "docente@example.com"

from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.content import CourseTopic, Subtopic, Topic  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.media_service import url_con_host_permitido  # noqa: E402


EMAIL = "docente3dot1@example.com"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _login(client):
    r = client.post("/api/auth/dev", json={"email": EMAIL, "name": "Docente 3.1", "role": "TEACHER"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def auth(client):
    return _login(client)


@pytest.fixture(scope="module")
def ids_module(client, auth):
    """Curso de docente + unidad + subtema borrador, creados con filas directas."""
    db = SessionLocal()
    t = db.query(User).filter(User.email == EMAIL).first()
    course = Course(name="Curso 3.1", type="TEACHER", teacher_id=t.id)
    topic = Topic(name="Unidad 3.1", order=1, validated=True)
    sub = Subtopic(topic=topic, name="Sub 3.1", content="contenido", order=1, validated=False)
    db.add_all([course, topic, sub])
    db.flush()
    db.add(CourseTopic(course_id=course.id, topic_id=topic.id, order=1))
    db.commit()
    ids = {"course": course.id, "topic": topic.id, "subtopic": sub.id}
    db.close()
    return ids


def test_lista_blanca_vacia_rechaza_todo(ids_module):
    assert url_con_host_permitido("https://www.youtube.com/watch?v=x") is False


def test_url_con_host_permitido():
    settings.MEDIA_ALLOWED_HOSTS = "www.youtube.com,*.example.org"
    try:
        assert url_con_host_permitido("https://www.youtube.com/watch?v=x") is True
        assert url_con_host_permitido("https://xyz.example.org/v.pdf") is True
        assert url_con_host_permitido("https://example.org.evil.com/") is False
        assert url_con_host_permitido("ftp://www.youtube.com/a") is False
    finally:
        settings.MEDIA_ALLOWED_HOSTS = ""


def test_agregar_medio_y_payload(auth, client, ids_module):
    settings.MEDIA_ALLOWED_HOSTS = "www.youtube.com,*.example.org"
    try:
        r = client.post(
            f"/api/content/subtopics/{ids_module['subtopic']}/media",
            json={"url": "https://www.youtube.com/watch?v=pterigion", "kind": "video"},
            headers=auth,
        )
        assert r.status_code == 200, r.text
        medio_id = r.json()["id"]
        # host fuera de la lista
        r2 = client.post(
            f"/api/content/subtopics/{ids_module['subtopic']}/media",
            json={"url": "https://malicioso.example.net/x.mp4", "kind": "video"},
            headers=auth,
        )
        assert r2.status_code == 400
        assert "MEDIA_ALLOWED_HOSTS" in r2.json()["detail"]
        # el payload del subtema trae los medios
        r3 = client.get(
            f"/api/subtopics/{ids_module['subtopic']}",
            params={"course_id": ids_module["course"]},
            headers=auth,
        )
        assert r3.status_code == 200, r3.text
        cuerpo = r3.json()
        urls = [m["url"] for m in cuerpo.get("media", [])]
        assert "https://www.youtube.com/watch?v=pterigion" in urls
        # borrar medio
        r4 = client.delete(
            f"/api/content/subtopics/{ids_module['subtopic']}/media/{medio_id}", headers=auth
        )
        assert r4.status_code == 200, r4.text
    finally:
        settings.MEDIA_ALLOWED_HOSTS = ""


def test_estudiante_no_puede_medios(client, ids_module):
    r = client.post("/api/auth/dev", json={"email": "alumno31@example.com", "name": "A", "role": "STUDENT"})
    assert r.status_code == 200, r.text
    est = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r2 = client.post(
        f"/api/content/subtopics/{ids_module['subtopic']}/media",
        json={"url": "https://www.youtube.com/watch?v=q", "kind": "video"},
        headers=est,
    )
    assert r2.status_code == 403, r2.text


def test_show_only_validated(client, auth, ids_module):
    settings.SHOW_ONLY_VALIDATED = False
    try:
        r = client.get(f"/api/courses/{ids_module['course']}/topics", headers=auth)
        subs = {s["id"] for t in r.json() for s in t["subtopics"]}
        assert ids_module["subtopic"] in subs  # flag apagado: todo visible
    finally:
        settings.SHOW_ONLY_VALIDATED = False

    # docente marca validado
    r2 = client.patch(
        f"/api/content/subtopics/{ids_module['subtopic']}/validated",
        json={"validated": True},
        headers=auth,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["validated"] is True
