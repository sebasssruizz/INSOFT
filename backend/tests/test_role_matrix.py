"""Matriz de roles y permisos (T2).

Cubre la autorización de los endpoints sensibles con 5 sujetos:
anónimo / estudiante inscrito / estudiante NO inscrito / docente dueño del
curso / docente de otro curso. Comparar el código HTTP real con lo esperado
definido aquí: los DESCUADRE revelan huecos de autorización.

Notas de diseño:
- El contenido es centralizado/compartido: CUALQUIER docente con el tema
  habilitado en un curso propio puede leer el banco y crear preguntas. La
  matriz lo refleja; el pedazo fino lo imponen los servicios (404/403 de
  owner en update/delete/review, cubiertos en test_teacher_questions_crud).
- Nada de estas pruebas llama a OpenRouter/Gemini: las rutas de IA generativa
  se resuelven con doble mock del servicio y los proveedores (ver
  `_mock_providers`), de modo que solo se mide la AUTORIZACIÓN.
- El PATCH de rol propio usa un docente desechable y va AL FINAL: cambiar el
  rol contaminaría a otros sujetos.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DB_FILE = "/tmp/opencode/oftallearn_test.db"
ANON, IN, NO_IN, OWNER_T, OTHER_T, TMP_T = "anon", "student_in", "student_out", "owner", "other", "tmp_t"


_FAKE_Q_STATE = {"n": 0}


@pytest.fixture(scope="module", autouse=True)
def _mock_providers():
    """Nada de red: el generador devuelve payload válido y el resto falla."""
    import json as _json
    from unittest.mock import AsyncMock

    from app.services import ai_service

    async def fake_llm(*args, **kwargs):
        _FAKE_Q_STATE["n"] += 1
        n = _FAKE_Q_STATE["n"]
        return _json.dumps(
            {
                "questions": [
                    {
                        "prompt": f"¿Pregunta IA generada {n}.{i}?",
                        "options": ["a", "b", "c", "d"],
                        "correct_index": i % 4,
                        "explanation": "El contenido oficial lo declara.",
                    }
                    for i in range(2)
                ]
            },
            ensure_ascii=False,
        )

    ai_service._call_llm_for_questions = AsyncMock(side_effect=fake_llm)
    ai_service.call_openrouter = AsyncMock(side_effect=RuntimeError("red bloqueada en pruebas"))
    yield


@pytest.fixture(scope="module")
def data():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    with TestClient(app) as client:
        def login(email, role, name="N"):
            r = client.post(
                "/api/auth/dev", json={"email": email, "name": name, "role": role}
            )
            assert r.status_code == 200, r.text
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        owner = login("owner_mas@example.com", "TEACHER", "Owner")
        other = login("other_mas@example.com", "TEACHER", "Other")
        student_in = login("alumno_in_mas@example.com", "STUDENT", "In")
        student_out = login("alumno_out_mas@example.com", "STUDENT", "Out")
        tmp_t = login("tmp_mas@example.com", "TEACHER", "Tmp")

        course = client.post(
            "/api/courses", json={"name": "Curso Owner M"}, headers=owner
        ).json()
        assert client.post(
            "/api/courses/join", json={"code": course["code"]}, headers=student_in
        ).status_code == 200

        topics = client.get(
            f"/api/courses/{course['id']}/topics", headers=owner
        ).json()
        topic_id = topics[0]["id"]
        subtopic_id = topics[0]["subtopics"][0]["id"]

        import uuid
        attempt_id = str(uuid.uuid4())
        reps = client.get(
            f"/api/topics/{topic_id}/questions", params={"course_id": course["id"]},
            headers=student_in,
        ).json()
        question_id = reps[0]["id"] if reps else None

        # pregunta docente real (owner) para matrix de edición; se borra al final
        q = client.post(
            f"/api/content/subtopics/{subtopic_id}/questions",
            json={"prompt": "¿Pregunta matriz rol owner para edición?",
                  "options": ["a", "b", "c", "d"], "correct_index": 0},
            headers=owner,
        ).json()
        teacher_question_id = q.get("id")

        yield {
            "client": client,
            "owner": owner,
            "other": other,
            "student_in": student_in,
            "student_out": student_out,
            "tmp_t": tmp_t,
            "course_id": course["id"],
            "code": course["code"],
            "subtopic_id": subtopic_id,
            "topic_id": topic_id,
            "attempt_id": attempt_id,
            "question_id": question_id,
            "teacher_question_id": teacher_question_id,
        }


def _fmt_rows(data):
    """(método, path, json, esperados {sujeto: código}, descripción)."""
    ids = {
        "id": data["course_id"],
        "subtopic_id": data["subtopic_id"],
        "topic_id": data["topic_id"],
        "attempt_id": data["attempt_id"],
        "question_id": data["question_id"],
        "tqid": data["teacher_question_id"],
        "code": data["code"],
    }

    def fmt(v):
        if isinstance(v, dict):
            return {k: fmt(x) for k, x in v.items()}
        if isinstance(v, str):
            out = v
            for k, val in ids.items():
                if val is not None:
                    out = out.replace("{" + k + "}", str(val))
            return out
        return v

    return [
        # ── auth/perfil: solo autenticación ──
        ("users/me", "GET", "/api/users/me", None,
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        ("perfil propio", "PATCH", "/api/users/me/profile", {"country": "Colombia", "age": 25},
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        # ── cursos ──
        ("crear curso (solo docente)", "POST", "/api/courses", {"name": "Curso Otra X M"},
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 201, OTHER_T: 201}),
        ("ver curso", "GET", "/api/courses/{id}", None,
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        ("estudiantes (solo dueño docente)", "GET", "/api/courses/{id}/students", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        # ── contenido ──
        ("importar contenido (solo docente)", "POST", "/api/content/import", {},
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 422, OTHER_T: 422}),
        ("temas del curso", "GET", "/api/courses/{id}/topics", None,
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        ("repaso de unidad", "GET", "/api/topics/{topic_id}/questions?course_id={id}", None,
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        ("detalle subtema", "GET", "/api/subtopics/{subtopic_id}?course_id={id}", None,
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        ("resumen unidad (solo docente)", "GET",
         "/api/content/topics/{topic_id}/questions/summary", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        ("banco del subtema (docente con tema habilitado)", "GET",
         "/api/content/subtopics/{subtopic_id}/questions/bank", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        ("crear pregunta (docente con tema habilitado)", "POST",
         "/api/content/subtopics/{subtopic_id}/questions",
         {"prompt": "¿Pregunta matriz única {subject}x8?", "options": ["a", "b", "c", "d"],
          "correct_index": 0},
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 201, OTHER_T: 201}),
        ("editar pregunta (solo autor)", "PATCH", "/api/content/questions/{tqid}",
         {"prompt": "¿Pregunta matriz editada unica y9?"},
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        ("borrar pregunta (solo autor)", "DELETE", "/api/content/questions/999999", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 404, OTHER_T: 404}),
        # ── quiz ──
        # El acceso a quiz/práctica se valida POR SUBTEMA (contenido compartido):
        # cualquier estudiante (incluido uno "no inscrito" al curso X) accede al
        # contenido oficial vía su membresía del Curso General. NO es un hueco.
        ("responder quiz (subtema compartido)", "POST", "/api/quiz/answers",
         {"question_id": "{question_id}", "selected_index": 0, "attempt_id": "{attempt_id}"},
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        ("quiz stats (solo docente)", "GET", "/api/quiz/stats/overview", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        ("quiz stats export (solo docente)", "GET", "/api/quiz/stats/export.csv", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        # ── IA ── (nockeado: no llama a proveedores)
        ("historial IA propio", "GET", "/api/ai/history", None,
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        ("historial IA completo (solo docente)", "GET", "/api/ai/history/all", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        ("stats IA overview (solo docente)", "GET", "/api/ai/stats/overview", None,
         {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 200, OTHER_T: 200}),
        # ── rag (embeddings local; no toca proveedores) ──
        ("rag search global (acotada a cursos con acceso)", "POST", "/api/rag/search",
         {"query": "pterigión"},
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        ("rag search subtema", "POST", "/api/rag/search",
         {"query": "pterigión", "subtopic_id": "{subtopic_id}", "course_id": "{id}"},
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 200, OTHER_T: 403}),
        # ── práctica ── (nockeada: no llama a proveedores)
        ("sesión práctica (subtema compartido)", "POST", "/api/practice/sessions",
         {"subtopic_id": "{subtopic_id}", "count": 3},
         {ANON: 401, IN: 200, NO_IN: 200, OWNER_T: 200, OTHER_T: 200}),
        # ── progreso ──
        ("marcar progreso", "POST", "/api/progress",
         {"course_id": "{id}", "subtopic_id": "{subtopic_id}", "completed": True},
         {ANON: 401, IN: 200, NO_IN: 403, OWNER_T: 403, OTHER_T: 403}),
    ]


# Al final: cambian estado que las filas previas asumen distinto.
# - join: enrolla student_out (después de eso los checks de "no inscrito" no valen).
# - generar IA: exige chunks indexados (no hay en esta DB -> 422 con authz ok).
# - PATCH de rol: docente desechable, para no contaminar a los otros sujetos.
ROWS_LAST = [
    ("unirse al curso", "POST", "/api/courses/join", {"code": "{code}"},
     {ANON: 401, IN: 409, NO_IN: 200, OWNER_T: 403, OTHER_T: 403}),
    ("generar preguntas IA (solo docente, sin chunks indexados -> 422)", "POST",
     "/api/ai/questions/generate", {"subtopic_id": "{subtopic_id}", "count": 2},
     {ANON: 401, IN: 403, NO_IN: 403, OWNER_T: 422, OTHER_T: 422}),
    ("cambiar rol propio (docente desechable)", "PATCH", "/api/users/me/role", {"role": "STUDENT"},
     {TMP_T: 200}),
]


def fmt_path(data, path):
    for k, v in (("id", data["course_id"]), ("subtopic_id", data["subtopic_id"]),
                 ("topic_id", data["topic_id"]), ("tqid", data["teacher_question_id"])):
        if v is not None:
            path = path.replace("{%s}" % k, str(v))
    return path


def fmt_body(data, body, subject=""):
    """Sustituye {marcadores} en el body y convierte *_id a int cuando cabe."""
    if not isinstance(body, dict):
        return body
    replacements = {
        "id": data["course_id"], "subtopic_id": data["subtopic_id"],
        "attempt_id": data["attempt_id"], "question_id": data["question_id"],
        "code": data["code"], "subject": subject,
    }
    out = {}
    for k, v in body.items():
        if isinstance(v, str) and "{" in v:
            for k2, v2 in replacements.items():
                v = v.replace("{%s}" % k2, "" if v2 is None else str(v2))
            if str(k).endswith("_id"):
                try:
                    v = int(v)
                except ValueError:
                    pass
        out[k] = v
    return out


@pytest.fixture(scope="module")
def results(data):
    all_rows = _fmt_rows(data) + ROWS_LAST
    out = []
    for desc, method, path, json_body, expected in all_rows:
        for subject, want in expected.items():
            url = fmt_path(data, path)
            body = fmt_body(data, json_body, subject)
            headers = data.get(subject)
            resp = data["client"].request(method, url, json=body, headers=headers or {})
            out.append((desc, subject, url, want, resp.status_code, resp.text[:100]))
    return out


_STUB = {"course_id": 0, "subtopic_id": 0, "topic_id": 0, "attempt_id": "0",
          "question_id": 0, "teacher_question_id": 0, "code": "X"}
DESCS = [row[0] for row in _fmt_rows(_STUB)]


@pytest.mark.parametrize("desc", DESCS)
def test_matrix(results, desc):
    rows = [r for r in results if r[0] == desc]
    assert rows, desc
    for desc_, subject, _url, want, got, body in rows:
        assert got == want, (
            f"DESCUADRE en {desc_} con sujeto {subject}: "
            f"esperado {want}, real {got} · body={body}"
        )
