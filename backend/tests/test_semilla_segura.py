"""SEED_MODE: un reinicio no debe pisar contenido editado ni importado.

Usa SQLite desechable (archivo temporal) y la misma función de semilla del arranque.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.base import Base
import app.models  # noqa: F401
from app.models.content import Subtopic, Topic
from app.seed import seed_content
from app.seed.seed_content import OFFICIAL_CONTENT, seed_official_content


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'semilla.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _topic(db, name):
    return db.scalar(select(Topic).where(Topic.name == name))


def _official_name(i):
    return OFFICIAL_CONTENT[i]["name"]


def test_primer_arranque_siembra_todas_las_unidades(db):
    assert seed_official_content(db, mode="if_empty") == "if_empty"
    assert len(db.scalars(select(Topic)).all()) == len(OFFICIAL_CONTENT)


def test_reinicio_no_pisa_contenido_editado_ni_importado(db):
    seed_official_content(db, mode="if_empty")

    primera = _topic(db, _official_name(0))
    primera.subtopics[0].content = "TEXTO EDITADO POR LA DOCENTE"
    primera.subtopics.append(Subtopic(name="Subtema propio", content="x", order=99))
    db.add(Topic(name="Unidad importada", description="d", order=0))
    db.commit()
    total_antes = len(db.scalars(select(Topic)).all())

    seed_official_content(db, mode="if_empty")  # reinicio del backend
    db.expire_all()

    primera = _topic(db, _official_name(0))
    assert primera.subtopics[0].content == "TEXTO EDITADO POR LA DOCENTE"
    assert "Subtema propio" in {s.name for s in primera.subtopics}
    assert _topic(db, "Unidad importada") is not None
    assert len(db.scalars(select(Topic)).all()) == total_antes


def test_unidad_importada_con_el_mismo_numero_no_se_sobrescribe(db):
    """Caso peligroso: una unidad oficial falta y otra ocupa su número de orden."""
    seed_official_content(db, mode="if_empty")
    oficial_3 = _topic(db, _official_name(2))
    oficial_3.name = "Unidad importada por el docente"  # ya no coincide con la oficial
    db.commit()

    seed_official_content(db, mode="if_empty")
    db.expire_all()

    importada = _topic(db, "Unidad importada por el docente")
    assert importada is not None, "la unidad importada no debe ser renombrada ni sobrescrita"
    assert importada.order == 2
    # La oficial que faltaba se crea como unidad nueva, sin reemplazar a la importada.
    assert _topic(db, _official_name(2)) is not None
    assert _topic(db, _official_name(2)).id != importada.id


def test_if_empty_agrega_unidades_oficiales_que_falten(db):
    seed_official_content(db, mode="if_empty")
    ultima = _topic(db, _official_name(len(OFFICIAL_CONTENT) - 1))
    ultima.name = "Unidad antigua"
    db.commit()
    antes = len(db.scalars(select(Topic)).all())

    seed_official_content(db, mode="if_empty")
    db.expire_all()

    assert len(db.scalars(select(Topic)).all()) == antes + 1
    assert _topic(db, "Unidad antigua") is not None


def test_always_restaura_la_semilla_y_borra_sobrantes_solo_en_desarrollo(db):
    """Comportamiento de desarrollo (SEED_MODE=always): demuestra por qué no es el valor de producción."""
    seed_official_content(db, mode="if_empty")
    primera = _topic(db, _official_name(0))
    primera.subtopics[0].content = "EDITADO"
    primera.subtopics.append(Subtopic(name="Sobrante", content="x", order=99))
    db.commit()

    seed_official_content(db, mode="always")
    db.expire_all()

    primera = _topic(db, _official_name(0))
    assert primera.subtopics[0].content != "EDITADO"
    assert "Sobrante" not in {s.name for s in primera.subtopics}


def test_off_no_toca_el_contenido(db):
    seed_official_content(db, mode="if_empty")
    primera = _topic(db, _official_name(0))
    primera.subtopics[0].content = "EDITADO"
    db.commit()

    assert seed_official_content(db, mode="off") == "off"
    db.expire_all()
    assert _topic(db, _official_name(0)).subtopics[0].content == "EDITADO"


def test_modo_por_defecto_depende_de_desarrollo():
    base = dict(SECRET_KEY="clave-de-prueba-suficientemente-larga-0123456789")
    assert Settings(DEV_AUTH_ENABLED=False, **base).seed_mode_efectivo == "if_empty"
    assert Settings(DEV_AUTH_ENABLED=True, **base).seed_mode_efectivo == "always"
    assert Settings(DEV_AUTH_ENABLED=False, SEED_MODE="off", **base).seed_mode_efectivo == "off"


def test_modo_invalido_se_rechaza():
    with pytest.raises(ValueError):
        Settings(DEV_AUTH_ENABLED=False, SECRET_KEY="clave-de-prueba-suficientemente-larga-0123456789",
                 SEED_MODE="borrar_todo").seed_mode_efectivo


def test_helper_no_cambia_la_semilla_original():
    """La función auxiliar no modifica el diccionario de la semilla (sin efectos colaterales)."""
    original = OFFICIAL_CONTENT[0]["subtopics"][0].copy()
    seed_content._with_questions(OFFICIAL_CONTENT[0])
    assert OFFICIAL_CONTENT[0]["subtopics"][0] == original
