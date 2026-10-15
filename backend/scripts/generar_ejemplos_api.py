"""Genera ejemplos REALES de respuestas de la API para el frontend.

Recorre la API con TestClient sobre una base SQLite DESECHABLE (se borra al
terminar) y con el proveedor de IA MOCKEADO: no sale ninguna llamada a red.
Guarda cada respuesta en docs/api/ejemplos/<nombre>.json con datos ficticios
(correos *.ejemplo.test, nombres genéricos, tokens redactados).

Uso (desde backend/, con el venv del proyecto):
    PYTHONPATH=. .venv/bin/python scripts/generar_ejemplos_api.py

Nunca apunta a la base real: fuerza DATABASE_URL a un archivo temporal.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "api" / "ejemplos"

# --- entorno desechable (ANTES de importar la app) ---------------------------
# Recomendado: Postgres pgvector DESECHABLE (EJEMPLOS_DATABASE_URL). Es el motor
# de producción: el tope diario de IA usa CAST(fecha) que en SQLite no compara bien.
_TMP = tempfile.mkdtemp(prefix="insoft-ejemplos-")
_DB = Path(_TMP) / "ejemplos.db"
if os.environ.get("EJEMPLOS_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["EJEMPLOS_DATABASE_URL"]
else:
    os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"
os.environ["SECRET_KEY"] = "ejemplos-desechables-no-es-un-secreto-0123456789abcdef"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-falsa-solo-ejemplos"
os.environ["AI_ASK_RATE_LIMIT"] = "1000/hour"
os.environ["AI_DAILY_LIMIT_PER_USER"] = "0"
os.environ["PRACTICE_RATE_LIMIT"] = "1000/hour"
os.environ["EMBEDDINGS_BACKEND"] = "onnx"

sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.openrouter_client import OpenRouterCallError, OpenRouterSaturatedError  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.content import Question, Subtopic  # noqa: E402
from app.models.question_meta import QuestionSource, QuestionStatus  # noqa: E402
from app.repositories import subtopic_chunk_repository as chunk_repo  # noqa: E402
from app.services.embeddings_service import embed_text  # noqa: E402

REDACT = {"access_token": "<JWT-REDACTADO>"}


def _fake_llm(*args, **kwargs):
    """Proveedor falso: la normalización devuelve la pregunta; la respuesta, texto."""
    if kwargs.get("model") == settings.OPENROUTER_NORMALIZE_MODEL:
        return "¿Qué es el glaucoma de ángulo cerrado?"
    return (
        "El glaucoma de ángulo cerrado eleva la presión intraocular y es una urgencia. "
        "Consulta el protocolo del curso."
    )
EXAMPLES: list[dict] = []


def _clean(obj):
    """Redacta tokens y deja solo datos ficticios."""
    if isinstance(obj, dict):
        return {k: (REDACT.get(k, _clean(v)) if k in REDACT else _clean(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, str) and obj.startswith("eyJ"):
        return "<JWT-REDACTADO>"
    return obj


def record(name: str, description: str, method: str, path: str, resp, body=None, headers_note=None):
    """Guarda una respuesta real (sanitizada) como ejemplo."""
    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text
    doc = {
        "nombre": name,
        "descripcion": description,
        "peticion": {"metodo": method, "ruta": path, **({"cuerpo": body} if body is not None else {})},
        "respuesta": {
            "status": resp.status_code,
            **({"cabeceras": {k: v for k, v in resp.headers.items() if k.lower() in ("retry-after", "content-type")}}),
            "cuerpo": _clean(payload),
        },
    }
    if headers_note:
        doc["nota"] = headers_note
    EXAMPLES.append(doc)
    return resp


def auth(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as client:
        # ---------- datos base: docente, curso propio, estudiante inscrito ----------
        docente = auth(client, "docente@example.com", "Docente Ejemplo", "TEACHER")
        estudiante = auth(client, "estudiante@example.com", "Estudiante Ejemplo", "STUDENT")
        otro = auth(client, "otro@example.com", "Otro Estudiante", "STUDENT")

        curso = client.post(
            "/api/courses",
            json={"name": "Curso de ejemplo", "description": "Datos ficticios"},
            headers=docente,
        )
        record("crear_curso_docente", "Docente crea un curso y recibe el código de acceso.",
               "POST", "/api/courses", curso, body={"name": "Curso de ejemplo", "description": "Datos ficticios"})
        curso = curso.json()

        join = client.post("/api/courses/join", json={"code": curso["code"]}, headers=estudiante)
        record("unirse_con_codigo", "Estudiante se une a un curso con el código.",
               "POST", "/api/courses/join", join, body={"code": "<CODIGO>"})

        general = next(c for c in client.get("/api/courses", headers=estudiante).json() if c["type"] == "GENERAL")
        gid = general["id"]

        # Indexa un fragmento del subtema 1 (lo necesita el asistente RAG).
        with SessionLocal() as s:
            sub_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
            texto = "El glaucoma de ángulo cerrado aumenta la presión intraocular y requiere valoración urgente."
            chunk_repo.create(s, subtopic_id=sub_id, content=texto, embedding=embed_text(texto))
            s.commit()

        # ---------- panel del estudiante ----------
        record("usuario_actual", "Perfil del usuario autenticado (panel y cabecera).",
               "GET", "/api/users/me", client.get("/api/users/me", headers=estudiante))
        record("lista_cursos_estudiante", "Cursos del estudiante con progreso por subtemas. Alimenta la barra de progreso.",
               "GET", "/api/courses", client.get("/api/courses", headers=estudiante))

        # ---------- curso, unidad, subtema ----------
        record("curso_detalle", "Detalle del Curso General con totales de unidades y subtemas.",
               "GET", f"/api/courses/{gid}", client.get(f"/api/courses/{gid}", headers=estudiante))
        topics = client.get(f"/api/courses/{gid}/topics", headers=estudiante)
        record("unidades_del_curso", "Unidades con sus subtemas y estado de completado de cada uno.",
               "GET", f"/api/courses/{gid}/topics", topics)
        topic_id = topics.json()[0]["id"]

        record("preguntas_repaso_unidad", "Preguntas de repaso de una unidad (sin clave de respuesta).",
               "GET", f"/api/topics/{topic_id}/questions?course_id={gid}",
               client.get(f"/api/topics/{topic_id}/questions", params={"course_id": gid}, headers=estudiante))

        sub = client.get(f"/api/subtopics/{sub_id}", params={"course_id": gid}, headers=estudiante)
        record("subtema_detalle", "Subtema con contenido y preguntas visibles para el estudiante.",
               "GET", f"/api/subtopics/{sub_id}?course_id={gid}", sub)
        questions = sub.json().get("questions", [])

        # ---------- quiz y progreso ----------
        if questions:
            qid = questions[0]["id"]
            ans = client.post("/api/quiz/answers",
                              json={"question_id": qid, "selected_index": 0, "attempt_id": str(uuid.uuid4())},
                              headers=estudiante)
            record("responder_pregunta", "Respuesta a una pregunta de quiz. Devuelve si es correcta y la explicación.",
                   "POST", "/api/quiz/answers",
                   ans, body={"question_id": qid, "selected_index": 0, "attempt_id": "<UUID>"})

        marca = client.post("/api/progress", json={"course_id": gid, "subtopic_id": sub_id, "completed": True},
                            headers=estudiante)
        record("marcar_subtema_completado", "Marca un subtema como completado. Cambia la barra de progreso.",
               "POST", "/api/progress", marca, body={"course_id": gid, "subtopic_id": sub_id, "completed": True})
        record("progreso_del_curso", "Resumen de progreso: subtemas completados entre total. Fuente de la barra.",
               "GET", f"/api/progress/course?course_id={gid}",
               client.get("/api/progress/course", params={"course_id": gid}, headers=estudiante))

        # ---------- práctica (banco oficial, sin LLM) ----------
        practica = client.post("/api/practice/sessions",
                               json={"subtopic_id": sub_id, "count": 3}, headers=estudiante)
        record("sesion_practica", "Sesión de práctica: composición banco/IA. Las preguntas no traen respuesta correcta.",
               "POST", "/api/practice/sessions", practica, body={"subtopic_id": sub_id, "count": 3})

        # ---------- asistente de IA: éxito, degradado, saturado ----------
        with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
            llm.side_effect = _fake_llm
            ok = client.post("/api/ai/ask",
                             json={"question": "¿qué es el glaucoma de ángulo cerrado?", "subtopic_id": sub_id,
                                   "course_id": gid},
                             headers=estudiante)
            record("chat_ia_exito", "Respuesta del asistente con RAG sobre el contenido oficial.",
                   "POST", "/api/ai/ask", ok,
                   body={"question": "¿qué es el glaucoma de ángulo cerrado?", "subtopic_id": sub_id,
                         "course_id": gid})

        with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
            llm.side_effect = OpenRouterCallError("Timeout llamando al proveedor")
            degr = client.post("/api/ai/ask",
                               json={"question": "otra consulta", "subtopic_id": sub_id, "course_id": gid},
                               headers=otro)
            record("chat_ia_degradado", "El proveedor de IA falla: 200 con degraded=true y fragmentos del contenido oficial (modo respaldo). No devuelve 503.",
                   "POST", "/api/ai/ask", degr, body={"question": "otra consulta", "subtopic_id": sub_id,
                                                      "course_id": gid})

        with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
            llm.side_effect = OpenRouterSaturatedError("Límite global del proveedor alcanzado")
            sat = client.post("/api/ai/ask",
                              json={"question": "consulta saturada", "subtopic_id": sub_id, "course_id": gid},
                              headers=otro)
            record("chat_ia_saturado", "Proveedor saturado: igual que el fallo, 200 con degraded=true (modo respaldo). No devuelve 429.",
                   "POST", "/api/ai/ask", sat, body={"question": "consulta saturada", "subtopic_id": sub_id,
                                                     "course_id": gid})

        # Límite diario por usuario (activado solo en esta fase)
        previo = settings.AI_DAILY_LIMIT_PER_USER
        settings.AI_DAILY_LIMIT_PER_USER = 1
        try:
            with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
                llm.side_effect = _fake_llm
                client.post("/api/ai/ask", json={"question": "primera del día", "subtopic_id": sub_id,
                                                 "course_id": gid}, headers=otro)
                lim = client.post("/api/ai/ask", json={"question": "segunda del día", "subtopic_id": sub_id,
                                                       "course_id": gid}, headers=otro)
            record("chat_ia_limite_diario", "Tope diario por usuario: 429 con Retry-After de 3600 s.",
                   "POST", "/api/ai/ask", lim, body={"question": "segunda del día", "subtopic_id": sub_id,
                                                     "course_id": gid})
        finally:
            settings.AI_DAILY_LIMIT_PER_USER = previo

        record("historial_ia_estudiante", "Historial propio de consultas al asistente.",
               "GET", "/api/ai/history", client.get("/api/ai/history", headers=estudiante))

        # ---------- errores comunes ----------
        record("error_sin_token", "Sin cabecera Authorization: 401.",
               "GET", "/api/users/me", client.get("/api/users/me"))
        record("error_estudiante_en_panel_docente", "Estudiante consulta una ruta de docente: 403.",
               "GET", f"/api/courses/{curso['id']}/students", client.get(f"/api/courses/{curso['id']}/students", headers=estudiante))
        record("error_subtema_inexistente", "Subtema que no existe (con course_id válido): 404.",
               "GET", f"/api/subtopics/999999?course_id={gid}",
               client.get("/api/subtopics/999999", params={"course_id": gid}, headers=estudiante))

        # ---------- panel del docente ----------
        record("alumnos_del_curso", "Alumnos inscritos en el curso del docente.",
               "GET", f"/api/courses/{curso['id']}/students",
               client.get(f"/api/courses/{curso['id']}/students", headers=docente))

        crear = client.post(f"/api/content/subtopics/{sub_id}/questions", headers=docente, json={
            "prompt": "¿Cuál es la presión intraocular normal aproximada?",
            "options": ["10 mmHg", "15 mmHg", "21 mmHg", "40 mmHg"],
            "correct_index": 2,
            "explanation": "Valor de referencia habitual; confirma con el protocolo del curso.",
        })
        record("crear_pregunta_docente", "Docente crea una pregunta: exactamente 4 opciones A-D y una correcta.",
               "POST", f"/api/content/subtopics/{sub_id}/questions",
               crear, body={"prompt": "¿Cuál es la presión intraocular normal aproximada?",
                            "options": ["10 mmHg", "15 mmHg", "21 mmHg", "40 mmHg"],
                            "correct_index": 2, "explanation": "…"})

        malas = client.post(f"/api/content/subtopics/{sub_id}/questions", headers=docente, json={
            "prompt": "Pregunta con tres opciones", "options": ["a", "b", "c"], "correct_index": 0,
        })
        record("error_pregunta_sin_4_opciones", "Pregunta con 3 opciones: 422 (la regla exige A-D).",
               "POST", f"/api/content/subtopics/{sub_id}/questions", malas,
               body={"prompt": "Pregunta con tres opciones", "options": ["a", "b", "c"], "correct_index": 0})

        duplicada = client.post(f"/api/content/subtopics/{sub_id}/questions", headers=docente, json={
            "prompt": "¿Cuál es la presión intraocular normal aproximada?",
            "options": ["10 mmHg", "15 mmHg", "21 mmHg", "40 mmHg"], "correct_index": 2,
        })
        record("error_enunciado_duplicado", "Enunciado repetido en el subtema: 409.",
               "POST", f"/api/content/subtopics/{sub_id}/questions", duplicada, body={"prompt": "…"})

        with SessionLocal() as s:
            autor = client.get("/api/users/me", headers=docente).json()["id"]
            pendiente = Question(subtopic_id=sub_id, created_by=autor, prompt="¿Qué protege la córnea del ojo?",
                                 options=["Esclera", "Córnea", "Iris", "Retina"], correct_index=1,
                                 explanation="Capa transparente externa.", order=900,
                                 source=QuestionSource.AI, status=QuestionStatus.PENDING)
            s.add(pendiente)
            s.commit()
            pid = pendiente.id
        revisa = client.post(f"/api/content/questions/{pid}/review", json={"action": "approve"}, headers=docente)
        record("aprobar_pregunta_ia", "Docente aprueba una pregunta generada por IA (pendiente → aprobada).",
               "POST", f"/api/content/questions/{pid}/review", revisa, body={"action": "approve"})

        record("banco_preguntas_subtema", "Banco de preguntas del subtema con origen y estado (vista docente).",
               "GET", f"/api/content/subtopics/{sub_id}/questions/bank",
               client.get(f"/api/content/subtopics/{sub_id}/questions/bank", headers=docente))

        record("estadisticas_resumen", "Resumen de estadísticas de quiz del docente.",
               "GET", "/api/quiz/stats/overview", client.get("/api/quiz/stats/overview", headers=docente))
        record("estadisticas_preguntas", "Acierto por pregunta del docente.",
               "GET", "/api/quiz/stats/questions", client.get("/api/quiz/stats/questions", headers=docente))
        csv = client.get("/api/quiz/stats/export.csv", headers=docente)
        record("exportar_csv", "Exportación CSV de respuestas (solo cabecera de ejemplo; el cuerpo es texto).",
               "GET", "/api/quiz/stats/export.csv",
               csv, headers_note="El cuerpo es CSV; aquí se guarda como texto.")

    for doc in EXAMPLES:
        (OUT / f"{doc['nombre']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    indice = [{"nombre": d["nombre"], "status": d["respuesta"]["status"], "descripcion": d["descripcion"]}
              for d in EXAMPLES]
    (OUT / "INDICE.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(EXAMPLES)} ejemplos escritos en {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        # Base desechable: se elimina siempre.
        for f in Path(_TMP).glob("*"):
            f.unlink(missing_ok=True)
        Path(_TMP).rmdir()
