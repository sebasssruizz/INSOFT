"""Contenido académico oficial de Oftalmología.

Fuente ÚNICA y centralizada: todos los cursos (general y de profesores)
referencian estos mismos temas/subtemas mediante CourseTopic, sin duplicarlos.

El seed es idempotente: solo crea lo que no exista.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Subtopic, Topic
from app.services import course_service

OFFICIAL_CONTENT = [
    {
        "name": "Anatomía ocular",
        "description": "Estructuras fundamentales del ojo y su función en la visión.",
        "subtopics": [
            {
                "name": "Globo ocular",
                "content": (
                    "El globo ocular es una estructura esférica de aproximadamente 24 mm de diámetro "
                    "alojada en la órbita. Está formado por tres capas concéntricas:\n\n"
                    "1. **Capa externa (fibrosa):** córnea y esclerótica. Proporciona protección y mantiene "
                    "la forma del ojo.\n"
                    "2. **Capa media (vascular o úvea):** iris, cuerpo ciliar y coroides. Aporta nutrición y "
                    "regula la entrada de luz.\n"
                    "3. **Capa interna (nerviosa):** la retina, encargada de la fototransducción.\n\n"
                    "En su interior se distinguen el humor acuoso (cámaras anterior y posterior), el cristalino "
                    "y el humor vítreo, que mantienen la presión y la transparencia óptica del globo."
                ),
            },
            {
                "name": "Córnea",
                "content": (
                    "La córnea es la estructura transparente anterior del ojo y la principal lente del sistema "
                    "óptico, con unas 43 dioptrías de potencia. Consta de cinco capas: epitelio, membrana de "
                    "Bowman, estroma, membrana de Descemet y endotelio.\n\n"
                    "Es avascular y se nutre del humor acuoso y de las lágrimas. El endotelio corneal mantiene "
                    "su deshidratación y transparencia; su daño produce edema corneal y pérdida de visión. "
                    "Es una de las estructuras con mayor densidad de terminaciones nerviosas del cuerpo."
                ),
            },
            {
                "name": "Cristalino",
                "content": (
                    "El cristalino es una lente biconvexa, transparente y avascular situada detrás del iris. "
                    "Aporta unas 15-20 dioptrías y, gracias a la acomodación, modifica su potencia para enfocar "
                    "objetos a distintas distancias.\n\n"
                    "Con la edad pierde elasticidad (presbicia) y puede perder transparencia (catarata), "
                    "constituyendo una de las principales causas de ceguera reversible en el mundo."
                ),
            },
            {
                "name": "Retina",
                "content": (
                    "La retina es la capa nerviosa interna del ojo, responsable de transformar la luz en señales "
                    "eléctricas que viajan por el nervio óptico hasta la corteza visual.\n\n"
                    "Contiene dos tipos de fotorreceptores: conos (visión central, color y alta agudeza, "
                    "concentrados en la mácula) y bastones (visión periférica y nocturna). La fóvea, en el centro "
                    "de la mácula, es la zona de máxima agudeza visual.\n\n"
                    "Su exploración mediante oftalmoscopia es fundamental en el diagnóstico de glaucoma, "
                    "retinopatía diabética y degeneración macular."
                ),
            },
        ],
    },
    {
        "name": "Glaucoma",
        "description": "Neuropatía óptica progresiva asociada habitualmente a presión intraocular elevada.",
        "subtopics": [
            {
                "name": "Conceptos generales",
                "content": (
                    "El glaucoma es un grupo de neuropatías ópticas caracterizadas por la pérdida progresiva de "
                    "fibras ganglionares de la retina, con alteraciones típicas del campo visual y de la papila.\n\n"
                    "Es la primera causa de ceguera irreversible mundial. El principal factor de riesgo es la "
                    "presión intraocular (PIO) elevada, aunque existen glaucomas de tensión normal.\n\n"
                    "Se clasifica en glaucoma de ángulo abierto (el más frecuente, crónico e indoloro) y glaucoma "
                    "de cierre angular (puede ser agudo, doloroso y una urgencia oftalmológica)."
                ),
            },
            {
                "name": "Fisiopatología",
                "content": (
                    "La PIO depende del equilibrio entre producción y drenaje del humor acuoso, que se produce "
                    "en los procesos ciliares y se drena por la malla trabecular y el canal de Schlemm.\n\n"
                    "Cuando el drenaje se obstruye, la PIO aumenta y daña las fibras ganglionares en la cabeza "
                    "del nervio óptico, produciendo la excavación papilar característica y defectos del campo "
                    "visual que comienzan en la periferia y avanzan hacia el centro."
                ),
            },
            {
                "name": "Diagnóstico",
                "content": (
                    "El diagnóstico del glaucoma se basa en la combinación de:\n\n"
                    "- **Tonometría:** medición de la PIO (normal: 10-21 mmHg).\n"
                    "- **Oftalmoscopia:** evaluación de la excavación papilar (relación excavación/disco).\n"
                    "- **Campimetría:** detección de defectos del campo visual.\n"
                    "- **Gonioscopia:** evaluación del ángulo iridocorneal para clasificar el glaucoma.\n"
                    "- **Paquimetría y OCT:** espesor corneal central y análisis de la capa de fibras nerviosas.\n\n"
                    "Ninguna prueba aislada es suficiente; el diagnóstico integra todos estos hallazgos."
                ),
            },
            {
                "name": "Tratamiento",
                "content": (
                    "El objetivo del tratamiento es reducir la PIO para frenar la progresión del daño, ya que "
                    "la pérdida visual establecida es irreversible.\n\n"
                    "- **Tratamiento médico:** análogos de prostaglandinas (primera línea), betabloqueantes, "
                    "agonistas alfa-2 e inhibidores de la anhidrasa carbónica.\n"
                    "- **Láser:** trabeculoplastia selectiva en glaucoma de ángulo abierto; iridotomía en cierre "
                    "angular.\n"
                    "- **Cirugía:** trabeculectomía y dispositivos de drenaje cuando el tratamiento médico y "
                    "láser no controlan la PIO.\n\n"
                    "El glaucoma agudo de cierre angular es una urgencia que requiere reducir la PIO de forma "
                    "inmediata."
                ),
            },
        ],
    },
    {
        "name": "Catarata",
        "description": "Opacificación del cristalino, principal causa de ceguera reversible en el mundo.",
        "subtopics": [
            {
                "name": "Conceptos generales",
                "content": (
                    "La catarata es la pérdida de transparencia del cristalino, que provoca disminución progresiva "
                    "e indolora de la visión.\n\n"
                    "La causa más frecuente es la edad (catarata senil). Otros factores: diabetes, corticoides, "
                    "traumatismos, radiación UV y causas congénitas.\n\n"
                    "Según su localización se clasifican en nucleares, corticales y subcapsulares posteriores, "
                    "cada una con síntomas característicos."
                ),
            },
            {
                "name": "Diagnóstico",
                "content": (
                    "El paciente refiere visión borrosa, deslumbramiento, miopización progresiva y alteración de "
                    "la percepción de colores.\n\n"
                    "El diagnóstico es clínico, mediante exploración con lámpara de hendidura con la pupila "
                    "dilatada, que permite visualizar la opacidad del cristalino. Se evalúa la agudeza visual y "
                    "el reflejo rojo.\n\n"
                    "Antes de la cirugía se realiza biometría ocular para calcular la potencia de la lente "
                    "intraocular a implantar."
                ),
            },
            {
                "name": "Tratamiento",
                "content": (
                    "El único tratamiento eficaz de la catarata es quirúrgico; no existe tratamiento médico que "
                    "revierta la opacificación.\n\n"
                    "La técnica estándar es la **facoemulsificación**: fragmentación y aspiración del cristalino "
                    "a través de una incisión mínima, con implante de lente intraocular. Es una de las cirugías "
                    "más frecuentes y seguras de la medicina.\n\n"
                    "La indicación depende del impacto funcional en la vida del paciente, no solo de la agudeza "
                    "visual."
                ),
            },
        ],
    },
    {
        "name": "Patologías de la retina",
        "description": "Principales enfermedades de la retina y su abordaje.",
        "subtopics": [
            {
                "name": "Retinopatía diabética",
                "content": (
                    "La retinopatía diabética es una microangiopatía de la retina y la principal causa de pérdida "
                    "visual en adultos en edad laboral.\n\n"
                    "Se clasifica en no proliferativa (microaneurismas, hemorragias, exudados) y proliferativa "
                    "(neovascularización, con riesgo de hemorragia vítrea y desprendimiento traccional de retina). "
                    "El edema macular diabético puede aparecer en cualquier estadio.\n\n"
                    "El cribado periódico con fondo de ojo es esencial en todos los pacientes diabéticos."
                ),
            },
            {
                "name": "Degeneración macular asociada a la edad",
                "content": (
                    "La DMAE es la principal causa de ceguera irreversible en mayores de 60 años en países "
                    "desarrollados. Afecta a la mácula y, por tanto, a la visión central.\n\n"
                    "- **Forma seca (atrófica):** drusas y atrofia geográfica, de evolución lenta.\n"
                    "- **Forma húmeda (exudativa):** membrana neovascular coroidea, de progresión rápida, tratable "
                    "con antiangiogénicos intravítreos (anti-VEGF).\n\n"
                    "La metamorfopsia (visión distorsionada de líneas rectas) es un síntoma de alarma típico."
                ),
            },
            {
                "name": "Desprendimiento de retina",
                "content": (
                    "El desprendimiento de retina es la separación de la retina neurosensorial del epitelio "
                    "pigmentario. Es una urgencia oftalmológica.\n\n"
                    "El tipo más frecuente es el regmatógeno, causado por una rotura retiniana que permite el paso "
                    "de vítreo licuado bajo la retina.\n\n"
                    "Síntomas: miodesopsias y fotopsias (moscas volantes y destellos) seguidas de un defecto "
                    "visual tipo cortina. El tratamiento es quirúrgico (vitrectomía, cerclaje escleral o "
                    "retinopexia neumática)."
                ),
            },
        ],
    },
]


def seed_official_content(db: Session) -> None:
    """Crea el contenido oficial si no existe y asegura el Curso General."""
    for topic_order, topic_data in enumerate(OFFICIAL_CONTENT):
        topic = db.scalar(select(Topic).where(Topic.name == topic_data["name"]))
        if topic is None:
            topic = Topic(
                name=topic_data["name"],
                description=topic_data["description"],
                order=topic_order,
            )
            db.add(topic)
            db.flush()
        for sub_order, sub_data in enumerate(topic_data["subtopics"]):
            exists = db.scalar(
                select(Subtopic).where(
                    Subtopic.topic_id == topic.id, Subtopic.name == sub_data["name"]
                )
            )
            if exists is None:
                db.add(
                    Subtopic(
                        topic_id=topic.id,
                        name=sub_data["name"],
                        content=sub_data["content"],
                        order=sub_order,
                    )
                )
    db.commit()

    # Asegurar que el Curso General existe y tiene vinculado todo el contenido.
    course_service.ensure_general_course(db)
