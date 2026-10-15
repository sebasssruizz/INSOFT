"""Bootstrap desechable para la simulación del plan gratis de Render (F2).

Crea el esquema completo (create_all, igual que el lifespan), extiende
pgvector y siembra contenido de RELLENO NO MÉDICO (neutral, sin información
clínica inventada) con embeddings generados en local con el backend ONNX.
El entorno es un Postgres desechable aparte del volumen real
insoft_postgres_data (red docker own: sim-perf, volumen sim-pgdata).

Ejecución desde un contenedor con la imagen del backend
(docker build --build-arg EMBEDDINGS_BACKEND=onnx -t insoft-backend-sim ./backend):

    docker run --rm --network sim-perf \\
      -v "$PWD/backend/sim/bootstrap_rag_sim.py":/app/bootstrap_rag_sim.py:ro \\
      -e DATABASE_URL=postgresql+psycopg2://sim:sim@sim-pg:5432/sim \\
      -e SECRET_KEY=<valor-aleatorio-local> -e DEV_AUTH_ENABLED=false \\
      -e AI_PROVIDER=openrouter \\
      insoft-backend-sim python bootstrap_rag_sim.py

El valor de SECRET_KEY es un literal local de prueba (no es un secreto real);
DEV_AUTH_ENABLED se mantiene en false y la autenticación se resuelve con un
JWT firmado en local con esa SECRET_KEY, vía app.auth.jwt.create_access_token.
"""
from __future__ import annotations

import sys

from sqlalchemy import text

from app.auth.jwt import create_access_token
from app.database.session import SessionLocal, engine
from app.models.content import Subtopic
from app.models.course import Course, CourseMembership, CourseType
from app.models.content import CourseTopic, Topic
from app.models.user import User, UserRole
from app.services.embeddings_service import embed_batch, embed_text

CHUNK_WORDS = ["Texto", "de", "relleno", "para", "la", "simulación", "de", "carga",
               "del", "backend", "con", "el", "plan", "gratuito", "de", "Render",
               "(datos", "neutros;", "sin", "contenido", "clínico)."]


def filler_text(index: int, words: int = 220) -> str:
    """Texto neutro de relleno (~200-300 palabras como los chunks reales)."""
    base = f"Chunk {index}: simulación de rendimiento, {CHUNK_WORDS} "
    return (base * 12)[: words * 7]


def main(chunks_per_subtopic: int = 50, subtopics: int = 3) -> int:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Importa todos los modelos tras la extensión para el create_all.
    import app.models  # noqa: F401  (registro de tablas)
    from app.database.base import Base
    Base.metadata.create_all(engine)

    db = SessionLocal()
    # Limpieza idempotente de restos de corridas previas (esquema desechable).
    db.execute(text("DELETE FROM subtopic_chunks"))
    db.execute(text("DELETE FROM course_memberships"))
    db.execute(text("DELETE FROM course_topics"))
    db.execute(text("DELETE FROM subtopics"))
    db.execute(text("DELETE FROM topics"))
    db.execute(text("DELETE FROM courses"))
    db.execute(text("DELETE FROM ai_queries"))
    db.execute(text("DELETE FROM users"))
    db.commit()

    student = User(
        google_id="sim-google-id-1",
        name="Estudiante Sim",
        email="sim-estudiante@example.invalid",
        role=UserRole.STUDENT,
    )
    teacher = User(
        google_id="sim-google-id-2",
        name="Docente Sim",
        email="sim-docente@example.invalid",
        role=UserRole.TEACHER,
    )
    db.add_all([student, teacher])
    db.commit()

    course = Course(
        name="Curso de pruebas de carga (relleno)",
        description="Curso desechable de simulación; contenido neutro de prueba.",
        code=None,
        type=CourseType.TEACHER,
        teacher_id=teacher.id,
    )
    db.add(course)
    db.commit()
    db.add(CourseMembership(course_id=course.id, user_id=student.id))
    db.commit()

    topic = Topic(name="Tema de relleno", description="Contenido neutro de simulación", order=1)
    db.add(topic)
    db.commit()
    db.add(CourseTopic(course_id=course.id, topic_id=topic.id, enabled=True))
    db.commit()

    texts: list[str] = []
    sub_ids: list[int] = []
    for s in range(subtopics):
        sub = Subtopic(topic_id=topic.id, name=f"Subtema {s + 1} (relleno)",
                       content="Contenido neutro de simulación " * 100, order=s + 1)
        db.add(sub)
        db.commit()
        sub_ids.append(sub.id)
        for c in range(chunks_per_subtopic):
            texts.append(filler_text(s * chunks_per_subtopic + c))

    # Embeddings por lotes con el backend activo (onnx en esta simulación).
    vectors = embed_batch(texts)
    from app.repositories.subtopic_chunk_repository import create as chunk_create
    for (sub_idx, sub_id) in enumerate(sub_ids):
        start = sub_idx * chunks_per_subtopic
        for c in range(chunks_per_subtopic):
            chunk_create(db, subtopic_id=sub_id, content=texts[start + c],
                         embedding=list(map(float, vectors[start + c])))

    probe = next(iter(embed_batch(["pregunta de prueba"])))
    print(f"SEED OK chunks={len(texts)} dims_probe={len(probe)}")
    print(f"SEED student_id={student.id}")
    token = create_access_token(student.id, "STUDENT")
    print("JWT de prueba emitido por stdout (usar solo contra la base desechable);",
          "pásalo al header Authorization: Bearer <token>.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
