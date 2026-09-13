"""Contenido académico oficial de Oftalmología.

Fuente única y centralizada: todos los cursos referencian estas mismas
unidades y subtemas mediante CourseTopic, sin duplicar contenido.
"""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.content import Question, Subtopic, Topic
from app.models.progress import Progress
from app.seed.seed_questions import OFFICIAL_QUESTIONS
from app.services import course_service


OFFICIAL_CONTENT = [
    {
        "name": "UNIDAD 1. Generalidades en Cirugía Oftalmológica",
        "description": "Bases anatómicas, técnicas, materiales y protocolos del entorno quirúrgico oftalmológico.",
        "subtopics": [
            {
                "name": "Anatomía del Globo Ocular y estructuras anexas",
                "content": "Estudio del globo ocular, órbita, párpados, conjuntiva, aparato lagrimal y músculos extraoculares. Se revisan sus relaciones anatómicas y su importancia para la preparación y el abordaje seguro de una cirugía oftalmológica.",
            },
            {
                "name": "Tipos de Anestesia para Cirugía Oftalmológica",
                "content": "Se describen la anestesia tópica, local, regional y general, junto con sus indicaciones, preparación del paciente, vigilancia y posibles complicaciones. La selección depende del procedimiento, la cooperación del paciente y la valoración del equipo médico.",
            },
            {
                "name": "Instrumental para cirugía Oftalmológica",
                "content": "Reconocimiento, montaje, manipulación y cuidado del instrumental básico y especializado para cirugía oftalmológica. Incluye pinzas, tijeras, separadores, blefaróstatos, portaagujas y material para microcirugía.",
            },
            {
                "name": "Equipos Biomédicos",
                "content": "Identificación y uso seguro del microscopio quirúrgico, facoemulsificador, vitrector, láser, electrobisturí y sistemas de irrigación y aspiración. Se enfatizan la revisión preoperatoria, la bioseguridad y la respuesta ante fallas.",
            },
            {
                "name": "Material de Suturas",
                "content": "Clasificación de suturas absorbibles y no absorbibles, monofilamento y multifilamento, calibres, agujas y criterios de selección. Se relacionan las características del material con la cicatrización y el tejido ocular intervenido.",
            },
            {
                "name": "Medicación en Cirugía Oftalmológica",
                "content": "Funciones y precauciones de los medicamentos empleados antes, durante y después de la cirugía: antibióticos, antiinflamatorios, midriáticos, mióticos, anestésicos y soluciones de irrigación. Se revisan identificación, rotulado y administración segura.",
            },
            {
                "name": "Protocolos del Instrumentador Quirúrgico en cirugía oftalmológica",
                "content": "Funciones del instrumentador en las fases preoperatoria, intraoperatoria y posoperatoria. Incluye verificación de equipos e instrumental, preparación del campo, conteos, técnica aséptica, trazabilidad y entrega segura del paciente.",
            },
        ],
    },
    {
        "name": "UNIDAD 2. Procedimientos Quirúrgicos de oftalmológica generales",
        "description": "Procedimientos ambulatorios frecuentes y sus cuidados de instrumentación.",
        "subtopics": [
            {
                "name": "Resección de pterigión",
                "content": "Indicaciones, preparación del campo, instrumental y pasos generales de la resección de pterigión, con o sin injerto conjuntival. Se consideran la protección corneal, la hemostasia y los cuidados del tejido para reducir recurrencias.",
            },
            {
                "name": "Drenaje de chalazión",
                "content": "Organización del procedimiento para incisión y drenaje de un chalazión. Se revisan la antisepsia, la anestesia local, el uso del clamp, el abordaje conjuntival y la disposición del material contaminado.",
            },
            {
                "name": "Dilatación de vías lagrimales",
                "content": "Valoración e instrumentación para la dilatación y exploración de las vías lagrimales. Incluye la preparación de dilatadores y sondas, la irrigación y las medidas para evitar trauma de los canalículos.",
            },
            {
                "name": "Inyecciones intravítreas",
                "content": "Preparación del paciente, antisepsia, instrumental y cuidados asociados a la administración intravítrea de medicamentos. Se resaltan la técnica estéril, la identificación del fármaco y la vigilancia de signos de alarma.",
            },
        ],
    },
    {
        "name": "UNIDAD 3. Glaucoma",
        "description": "Procedimientos para favorecer el drenaje del humor acuoso y controlar la presión intraocular.",
        "subtopics": [
            {
                "name": "Trabeculotomía más iridectomía periférica",
                "content": "Objetivos, indicaciones y organización quirúrgica de la trabeculotomía asociada a iridectomía periférica. Se revisan el instrumental de microcirugía, la secuencia del procedimiento y las precauciones para proteger las estructuras intraoculares.",
            },
            {
                "name": "Colocación de implantes para Drenaje de Humor acuoso",
                "content": "Preparación e instrumentación para la colocación de dispositivos de drenaje del humor acuoso. Incluye componentes del implante, selección del material, control de la cámara anterior y cuidados del dispositivo.",
            },
            {
                "name": "Iridectomía con Láser",
                "content": "Principios y preparación de la iridectomía periférica con láser para facilitar el paso del humor acuoso. Se describen la posición del paciente, la protección ocular, el equipo y la vigilancia posterior.",
            },
        ],
    },
    {
        "name": "UNIDAD 4. Cirugías del segmento anterior",
        "description": "Técnicas de microcirugía para el cristalino y la córnea.",
        "subtopics": [
            {
                "name": "Facoemulsificación",
                "content": "Fundamentos de la extracción del cristalino mediante ultrasonido, aspiración e implante de lente intraocular. Se revisan la preparación del facoemulsificador, el instrumental, los viscoelásticos y el control de parámetros.",
            },
            {
                "name": "Extracción extracapsular",
                "content": "Descripción de la extracción extracapsular del cristalino, sus indicaciones, instrumental y fases quirúrgicas. Se enfatizan la conservación de la cápsula posterior, la colocación de la lente y el cierre de la incisión.",
            },
            {
                "name": "Trasplante de córnea",
                "content": "Preparación e instrumentación del trasplante corneal, desde la recepción y verificación del tejido hasta la trepanación, colocación del injerto y sutura. Se incluyen principios de conservación, asepsia y trazabilidad.",
            },
        ],
    },
    {
        "name": "UNIDAD 5. Cirugías vitreorretinales",
        "description": "Procedimientos sobre el vítreo y la retina, con énfasis en equipos y seguridad intraocular.",
        "subtopics": [
            {
                "name": "Vitrectomías del segmento anterior y posterior",
                "content": "Principios de la vitrectomía anterior y posterior, selección de trocares, líneas de infusión, sistemas de corte y aspiración. Se revisan el montaje del equipo, los líquidos de intercambio y el control del campo quirúrgico.",
            },
            {
                "name": "Retinopatía simple",
                "content": "Abordaje general de la retinopatía simple y su relación con la valoración del fondo de ojo. Se estudian la preparación para procedimientos retinianos, la fotocoagulación, la medicación y el seguimiento indicado por el especialista.",
            },
        ],
    },
    {
        "name": "UNIDAD 6. Corrección de estrabismo",
        "description": "Principios de las técnicas quirúrgicas para recuperar la alineación ocular.",
        "subtopics": [
            {
                "name": "Técnicas para Corrección de estrabismo",
                "content": "Preparación e instrumentación de las principales técnicas de cirugía de estrabismo: debilitamiento y refuerzo de músculos extraoculares, suturas ajustables y cuidados del campo quirúrgico. Se relaciona cada técnica con el músculo y la desviación a corregir.",
            },
        ],
    },
    {
        "name": "UNIDAD 7. Cirugía para corrección de patologías refractivas",
        "description": "Alternativas quirúrgicas para corregir errores refractivos y sus cuidados asociados.",
        "subtopics": [
            {
                "name": "Miopía, Hipermetropía y Astigmatismo",
                "content": "Características de la miopía, la hipermetropía y el astigmatismo, criterios generales de valoración y opciones de corrección refractiva. Se revisan la preparación del equipo láser, la seguridad del paciente y los cuidados posteriores.",
            },
        ],
    },
    {
        "name": "UNIDAD 8. Oculoplastia",
        "description": "Procedimientos reconstructivos y estéticos de los párpados y estructuras perioculares.",
        "subtopics": [
            {
                "name": "Cirugía en Párpados",
                "content": "Preparación e instrumentación para cirugía palpebral, incluyendo valoración del tejido, marcación, hemostasia, suturas y protección de la superficie ocular. Se consideran los cuidados de la herida y la vigilancia de complicaciones.",
            },
        ],
    },
]


def _sync_questions(db: Session, subtopic: Subtopic) -> None:
    """Alinea las preguntas del subtema con el banco oficial, sin duplicar."""
    desired = OFFICIAL_QUESTIONS.get(subtopic.name, [])
    current = sorted(subtopic.questions, key=lambda question: question.order)

    for question_order, question_data in enumerate(desired):
        if question_order < len(current):
            question = current[question_order]
        else:
            question = Question(subtopic=subtopic)
            db.add(question)
        question.prompt = question_data["prompt"]
        question.options = question_data["options"]
        question.correct_index = question_data["correct_index"]
        question.explanation = question_data["explanation"]
        question.order = question_order

    for stale in current[len(desired):]:
        db.delete(stale)


def _sync_topic(db: Session, topic_data: dict, topic_order: int) -> Topic:
    """Actualiza una unidad existente o la crea, conservando sus relaciones."""
    topic = db.scalar(select(Topic).where(Topic.name == topic_data["name"]))
    if topic is None:
        topic = db.scalar(select(Topic).where(Topic.order == topic_order))
    if topic is None:
        topic = Topic(name=topic_data["name"], order=topic_order)
        db.add(topic)
        db.flush()

    topic.name = topic_data["name"]
    topic.description = topic_data["description"]
    topic.order = topic_order

    current_subtopics = sorted(topic.subtopics, key=lambda subtopic: subtopic.order)
    desired_subtopics = topic_data["subtopics"]
    for subtopic_order, subtopic_data in enumerate(desired_subtopics):
        if subtopic_order < len(current_subtopics):
            subtopic = current_subtopics[subtopic_order]
        else:
            subtopic = Subtopic(topic=topic)
            db.add(subtopic)
        subtopic.name = subtopic_data["name"]
        subtopic.content = subtopic_data["content"]
        subtopic.order = subtopic_order
        db.flush()
        _sync_questions(db, subtopic)

    stale_subtopics = current_subtopics[len(desired_subtopics):]
    stale_ids = [subtopic.id for subtopic in stale_subtopics if subtopic.id is not None]
    if stale_ids:
        db.execute(delete(Progress).where(Progress.subtopic_id.in_(stale_ids)))
        for subtopic in stale_subtopics:
            db.delete(subtopic)

    return topic


def seed_official_content(db: Session) -> None:
    """Sincroniza las 8 unidades oficiales y asegura el Curso General."""
    for topic_order, topic_data in enumerate(OFFICIAL_CONTENT):
        _sync_topic(db, topic_data, topic_order)
    db.commit()

    # Asegurar que el Curso General y los cursos de profesores tengan todo el contenido.
    course_service.ensure_general_course(db)
