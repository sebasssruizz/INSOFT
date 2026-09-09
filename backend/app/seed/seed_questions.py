"""Banco de preguntas de repaso del contenido oficial de Oftalmología.

Se indexa por el nombre del subtema al que pertenece cada pregunta. Igual que
el temario, es fuente única: los cursos no duplican preguntas, las comparten a
través del subtema.

Cada pregunta declara: enunciado, opciones, índice de la opción correcta y una
explicación que se muestra tras responder (el valor formativo está ahí, no en
el acierto).
"""

# subtema -> [(enunciado, [opciones], índice correcto, explicación)]
OFFICIAL_QUESTIONS: dict[str, list[dict]] = {
    # ── UNIDAD 1 ────────────────────────────────────────────────────────────
    "Anatomía del Globo Ocular y estructuras anexas": [
        {
            "prompt": "¿Cuántos músculos extraoculares mueven cada globo ocular?",
            "options": ["Cuatro", "Seis", "Ocho", "Doce"],
            "correct_index": 1,
            "explanation": (
                "Son seis: cuatro rectos (superior, inferior, medial y lateral) y dos oblicuos "
                "(superior e inferior). Conocer su inserción es clave en la cirugía de estrabismo."
            ),
        },
        {
            "prompt": "El aparato lagrimal drena la lágrima hacia la cavidad nasal a través de:",
            "options": [
                "El conducto nasolagrimal",
                "El nervio óptico",
                "La cámara anterior",
                "El cuerpo ciliar",
            ],
            "correct_index": 0,
            "explanation": (
                "La lágrima pasa por los puntos y canalículos lagrimales, el saco lagrimal y "
                "finalmente el conducto nasolagrimal hasta el meato inferior de la nariz."
            ),
        },
        {
            "prompt": "¿Por qué importa la anatomía orbitaria al preparar un abordaje quirúrgico seguro?",
            "options": [
                "Solo determina el color del campo estéril",
                "Define relaciones con nervios y vasos que condicionan el acceso",
                "Únicamente influye en la elección del anestésico tópico",
                "No tiene relación con la técnica quirúrgica",
            ],
            "correct_index": 1,
            "explanation": (
                "La órbita aloja estructuras vasculonerviosas cuya posición condiciona el abordaje, "
                "la profundidad segura de trabajo y la prevención de lesiones."
            ),
        },
    ],
    "Tipos de Anestesia para Cirugía Oftalmológica": [
        {
            "prompt": "¿Qué tipo de anestesia se emplea con más frecuencia en la cirugía de catarata no complicada?",
            "options": ["General", "Tópica", "Raquídea", "Epidural"],
            "correct_index": 1,
            "explanation": (
                "La anestesia tópica permite una recuperación rápida y evita los riesgos de la "
                "inyección periocular, siempre que el paciente colabore."
            ),
        },
        {
            "prompt": "La selección del tipo de anestesia depende principalmente de:",
            "options": [
                "La marca del instrumental disponible",
                "El procedimiento, la cooperación del paciente y la valoración del equipo",
                "La hora de la cirugía",
                "El número de instrumentadores en sala",
            ],
            "correct_index": 1,
            "explanation": (
                "Se combinan la complejidad y duración del procedimiento, la capacidad de "
                "colaboración del paciente y la valoración clínica del equipo."
            ),
        },
        {
            "prompt": "¿Cuál es una indicación habitual de anestesia general en oftalmología?",
            "options": [
                "Paciente pediátrico o sin capacidad de colaborar",
                "Cualquier cirugía ambulatoria",
                "Retirada de suturas",
                "Exploración con lámpara de hendidura",
            ],
            "correct_index": 0,
            "explanation": (
                "En pacientes pediátricos, con discapacidad o incapaces de mantener la inmovilidad "
                "se prefiere anestesia general para garantizar seguridad y precisión."
            ),
        },
    ],
    "Instrumental para cirugía Oftalmológica": [
        {
            "prompt": "¿Cuál es la función del blefaróstato?",
            "options": [
                "Sujetar la aguja de sutura",
                "Mantener los párpados separados durante la cirugía",
                "Cortar tejido corneal",
                "Irrigar la cámara anterior",
            ],
            "correct_index": 1,
            "explanation": (
                "El blefaróstato o separador palpebral mantiene la hendidura abierta y libera las "
                "manos del equipo, exponiendo el campo quirúrgico."
            ),
        },
        {
            "prompt": "El instrumental de microcirugía oftalmológica se caracteriza por:",
            "options": [
                "Ser más pesado que el instrumental general",
                "Tener puntas finas y delicadas que exigen manipulación cuidadosa",
                "No requerir esterilización",
                "Usarse siempre sin microscopio",
            ],
            "correct_index": 1,
            "explanation": (
                "Sus puntas son extremadamente finas: un golpe o un apilamiento incorrecto las "
                "inutiliza, por eso se manipulan y almacenan de forma individual y protegida."
            ),
        },
        {
            "prompt": "Al recibir el instrumental antes de la cirugía, el instrumentador debe:",
            "options": [
                "Verificar integridad, limpieza, montaje y funcionamiento",
                "Abrirlo solo cuando el cirujano lo solicite",
                "Contarlo únicamente al finalizar",
                "Confiar en la revisión de central de esterilización",
            ],
            "correct_index": 0,
            "explanation": (
                "La verificación previa detecta puntas dañadas, articulaciones defectuosas o "
                "material incompleto antes de que el problema aparezca en pleno acto quirúrgico."
            ),
        },
    ],
    "Equipos Biomédicos": [
        {
            "prompt": "¿Qué equipo se emplea para fragmentar y aspirar el cristalino mediante ultrasonido?",
            "options": ["Vitrector", "Facoemulsificador", "Electrobisturí", "Trépano"],
            "correct_index": 1,
            "explanation": (
                "El facoemulsificador emite ultrasonido a través de una punta que fragmenta el "
                "núcleo del cristalino, mientras irriga y aspira el material."
            ),
        },
        {
            "prompt": "La revisión preoperatoria de los equipos biomédicos busca principalmente:",
            "options": [
                "Reducir el consumo eléctrico del quirófano",
                "Confirmar funcionamiento y parámetros antes de iniciar la cirugía",
                "Justificar la compra de equipos nuevos",
                "Acortar el tiempo de anestesia",
            ],
            "correct_index": 1,
            "explanation": (
                "Comprobar calibración, conexiones, líneas y parámetros evita interrupciones "
                "críticas y errores durante el procedimiento."
            ),
        },
        {
            "prompt": "Ante una falla del microscopio quirúrgico en pleno procedimiento, lo correcto es:",
            "options": [
                "Continuar sin visualización adecuada",
                "Avisar de inmediato y activar el plan de contingencia del servicio",
                "Reparar el equipo dentro del campo estéril",
                "Retirar el campo estéril y dar por terminada la cirugía",
            ],
            "correct_index": 1,
            "explanation": (
                "La comunicación inmediata y el protocolo de respaldo permiten mantener la "
                "seguridad del paciente sin improvisar dentro del campo estéril."
            ),
        },
    ],
    "Material de Suturas": [
        {
            "prompt": "En cirugía oftalmológica, ¿qué calibre de sutura es habitual para el cierre corneal?",
            "options": ["2-0", "4-0", "10-0", "0"],
            "correct_index": 2,
            "explanation": (
                "El nylon 10-0 es el estándar en córnea: su diámetro mínimo reduce el trauma y el "
                "astigmatismo inducido en un tejido transparente y delgado."
            ),
        },
        {
            "prompt": "Una sutura absorbible se caracteriza por:",
            "options": [
                "Permanecer indefinidamente en el tejido",
                "Degradarse por el organismo sin necesidad de retirarla",
                "Ser siempre metálica",
                "No poder utilizarse en oftalmología",
            ],
            "correct_index": 1,
            "explanation": (
                "El organismo la degrada por hidrólisis o proteólisis, lo que evita una segunda "
                "intervención para retirarla."
            ),
        },
        {
            "prompt": "¿Qué ventaja tiene el monofilamento frente al multifilamento?",
            "options": [
                "Mayor capilaridad y retención bacteriana",
                "Menor riesgo de albergar microorganismos y menor fricción al pasar por el tejido",
                "Siempre es más fácil de anudar",
                "Es más económico en todos los casos",
            ],
            "correct_index": 1,
            "explanation": (
                "Al ser un solo filamento liso no tiene intersticios donde alojar bacterias y "
                "atraviesa el tejido con menos fricción, aunque exige más nudos."
            ),
        },
    ],
    "Medicación en Cirugía Oftalmológica": [
        {
            "prompt": "¿Qué efecto produce un midriático?",
            "options": [
                "Contrae la pupila",
                "Dilata la pupila",
                "Reduce la presión arterial",
                "Anestesia la córnea",
            ],
            "correct_index": 1,
            "explanation": (
                "Los midriáticos dilatan la pupila para permitir el acceso al cristalino y la "
                "visualización del segmento posterior."
            ),
        },
        {
            "prompt": "El rotulado de los medicamentos en la mesa quirúrgica sirve para:",
            "options": [
                "Cumplir un trámite administrativo",
                "Prevenir errores de identificación y administración",
                "Acelerar el conteo de gasas",
                "Sustituir la verificación verbal con el cirujano",
            ],
            "correct_index": 1,
            "explanation": (
                "Varios fármacos oftálmicos son incoloros y de aspecto idéntico: el rótulo es la "
                "barrera principal frente a una administración equivocada."
            ),
        },
        {
            "prompt": "Un fármaco miótico se emplea en cirugía oftalmológica para:",
            "options": [
                "Contraer la pupila al final del procedimiento",
                "Dilatar la pupila antes de la incisión",
                "Producir anestesia regional",
                "Aumentar la presión intraocular",
            ],
            "correct_index": 0,
            "explanation": (
                "La miosis al cierre ayuda a reposicionar el iris y comprobar la correcta posición "
                "de la lente intraocular."
            ),
        },
    ],
    "Protocolos del Instrumentador Quirúrgico en cirugía oftalmológica": [
        {
            "prompt": "¿En qué momento se realizan los conteos de material?",
            "options": [
                "Solo al finalizar la cirugía",
                "Antes de iniciar, durante el procedimiento y antes del cierre",
                "Únicamente si el cirujano lo solicita",
                "Solo en cirugías mayores",
            ],
            "correct_index": 1,
            "explanation": (
                "El conteo es sistemático y repetido: inicial, intraoperatorio y de cierre, para "
                "garantizar que no queda material retenido."
            ),
        },
        {
            "prompt": "La fase preoperatoria del instrumentador incluye:",
            "options": [
                "Redactar el informe quirúrgico",
                "Verificar equipos e instrumental y preparar el campo estéril",
                "Indicar la anestesia",
                "Dar el alta al paciente",
            ],
            "correct_index": 1,
            "explanation": (
                "Antes de la incisión el instrumentador asegura disponibilidad, esterilidad y "
                "funcionamiento de todo lo que la cirugía va a necesitar."
            ),
        },
        {
            "prompt": "La trazabilidad del material implantado busca:",
            "options": [
                "Registrar qué se implantó, en quién y con qué lote",
                "Reducir el coste del implante",
                "Sustituir el consentimiento informado",
                "Acortar el tiempo quirúrgico",
            ],
            "correct_index": 0,
            "explanation": (
                "Dejar constancia de lote y referencia permite responder ante alertas sanitarias o "
                "complicaciones tardías asociadas al implante."
            ),
        },
    ],
    # ── UNIDAD 2 ────────────────────────────────────────────────────────────
    "Resección de pterigión": [
        {
            "prompt": "El pterigión es un crecimiento anómalo de tejido que invade principalmente:",
            "options": ["La retina", "La córnea desde la conjuntiva", "El cristalino", "El nervio óptico"],
            "correct_index": 1,
            "explanation": (
                "Es una proliferación fibrovascular de la conjuntiva bulbar que avanza sobre la "
                "córnea y puede afectar el eje visual."
            ),
        },
        {
            "prompt": "¿Qué técnica reduce de forma significativa la recurrencia tras la resección?",
            "options": [
                "Cierre por segunda intención",
                "Injerto conjuntival autólogo",
                "Dejar la esclera desnuda sin cobertura",
                "Sutura corneal continua",
            ],
            "correct_index": 1,
            "explanation": (
                "El autoinjerto conjuntival cubre el lecho escleral y disminuye claramente la tasa "
                "de recidiva frente a la esclera desnuda."
            ),
        },
        {
            "prompt": "Durante el procedimiento, la protección corneal busca evitar:",
            "options": [
                "La desecación y el trauma del epitelio",
                "El sangrado conjuntival",
                "La dilatación pupilar",
                "El aumento de la presión arterial",
            ],
            "correct_index": 0,
            "explanation": (
                "La córnea expuesta se deseca con rapidez; la irrigación y protección mantienen la "
                "transparencia y evitan defectos epiteliales."
            ),
        },
    ],
    "Drenaje de chalazión": [
        {
            "prompt": "Un chalazión se origina por:",
            "options": [
                "Infección aguda del saco lagrimal",
                "Obstrucción e inflamación crónica de una glándula de Meibomio",
                "Desprendimiento de retina",
                "Opacidad del cristalino",
            ],
            "correct_index": 1,
            "explanation": (
                "Es una inflamación granulomatosa crónica secundaria a la obstrucción de una "
                "glándula de Meibomio del párpado."
            ),
        },
        {
            "prompt": "¿Cuál es la función del clamp de chalazión?",
            "options": [
                "Dilatar la vía lagrimal",
                "Fijar el párpado y controlar el sangrado durante la incisión",
                "Separar los músculos extraoculares",
                "Sujetar la lente intraocular",
            ],
            "correct_index": 1,
            "explanation": (
                "El clamp estabiliza el párpado, evierte la lesión y comprime los bordes, lo que "
                "limita el sangrado durante la incisión y el legrado."
            ),
        },
        {
            "prompt": "El abordaje conjuntival del chalazión se prefiere porque:",
            "options": [
                "Evita una cicatriz cutánea visible",
                "Es más rápido de suturar",
                "Permite usar anestesia general",
                "No requiere antisepsia",
            ],
            "correct_index": 0,
            "explanation": (
                "Al incidir por la cara tarsal interna no queda cicatriz en la piel del párpado, "
                "un resultado estético relevante en oculoplastia."
            ),
        },
    ],
    "Dilatación de vías lagrimales": [
        {
            "prompt": "La principal precaución al sondar los canalículos es:",
            "options": [
                "Aplicar la máxima fuerza posible",
                "Evitar falsas vías y desgarros por manipulación brusca",
                "Trabajar sin anestesia",
                "Usar sondas de gran calibre desde el inicio",
            ],
            "correct_index": 1,
            "explanation": (
                "El canalículo es delicado: una maniobra forzada crea una falsa vía que agrava la "
                "obstrucción que se pretendía tratar."
            ),
        },
        {
            "prompt": "La irrigación de la vía lagrimal permite comprobar:",
            "options": [
                "La agudeza visual",
                "La permeabilidad del sistema de drenaje",
                "La presión intraocular",
                "La curvatura corneal",
            ],
            "correct_index": 1,
            "explanation": (
                "Si el suero pasa a la nasofaringe la vía está permeable; el reflujo indica el "
                "nivel de la obstrucción."
            ),
        },
        {
            "prompt": "El instrumental básico para este procedimiento incluye:",
            "options": [
                "Dilatadores de punto lagrimal y sondas",
                "Trépano corneal y facoemulsificador",
                "Vitrector y trocares",
                "Blefaróstato y viscoelástico",
            ],
            "correct_index": 0,
            "explanation": (
                "El dilatador abre el punto lagrimal y las sondas de calibre progresivo exploran y "
                "permeabilizan el trayecto."
            ),
        },
    ],
    "Inyecciones intravítreas": [
        {
            "prompt": "¿Cuál es la complicación más temida de una inyección intravítrea?",
            "options": ["Endoftalmitis", "Conjuntivitis alérgica", "Blefaritis", "Ojo seco"],
            "correct_index": 0,
            "explanation": (
                "La endoftalmitis es infrecuente pero devastadora: de ahí la exigencia extrema de "
                "técnica estéril y antisepsia con povidona yodada."
            ),
        },
        {
            "prompt": "Antes de administrar el fármaco es imprescindible:",
            "options": [
                "Verificar identidad del paciente, ojo a tratar y fármaco",
                "Retirar el blefaróstato",
                "Dilatar la vía lagrimal",
                "Medir la longitud axial",
            ],
            "correct_index": 0,
            "explanation": (
                "La verificación cruzada de paciente, lateralidad y medicamento previene el error "
                "de ojo o de fármaco, un evento centinela evitable."
            ),
        },
        {
            "prompt": "¿Qué signo de alarma debe explicarse al paciente tras la inyección?",
            "options": [
                "Dolor intenso creciente, enrojecimiento y pérdida de visión",
                "Ligera sensación de cuerpo extraño el primer día",
                "Pequeña hemorragia subconjuntival",
                "Visión de alguna miodesopsia puntual",
            ],
            "correct_index": 0,
            "explanation": (
                "Ese conjunto sugiere endoftalmitis y obliga a consulta urgente; los demás son "
                "hallazgos leves y esperables."
            ),
        },
    ],
    # ── UNIDAD 3 ────────────────────────────────────────────────────────────
    "Trabeculotomía más iridectomía periférica": [
        {
            "prompt": "El objetivo de la cirugía de glaucoma es:",
            "options": [
                "Aumentar la producción de humor acuoso",
                "Facilitar el drenaje del humor acuoso y reducir la presión intraocular",
                "Opacificar el cristalino",
                "Corregir el astigmatismo",
            ],
            "correct_index": 1,
            "explanation": (
                "Al mejorar la salida del humor acuoso desciende la presión intraocular y se frena "
                "el daño del nervio óptico."
            ),
        },
        {
            "prompt": "La iridectomía periférica evita:",
            "options": [
                "El bloqueo pupilar",
                "La catarata secundaria",
                "El desprendimiento de retina",
                "La queratitis",
            ],
            "correct_index": 0,
            "explanation": (
                "Crea una comunicación entre cámara posterior y anterior que impide el bloqueo "
                "pupilar y el cierre angular."
            ),
        },
        {
            "prompt": "Durante la microcirugía del ángulo, la precaución esencial es:",
            "options": [
                "Proteger las estructuras intraoculares y mantener la cámara formada",
                "Trabajar sin viscoelástico",
                "Elevar la presión intraocular",
                "Prescindir del microscopio",
            ],
            "correct_index": 0,
            "explanation": (
                "El viscoelástico mantiene el espacio y protege endotelio e iris mientras se "
                "trabaja en estructuras milimétricas."
            ),
        },
    ],
    "Colocación de implantes para Drenaje de Humor acuoso": [
        {
            "prompt": "Un implante valvulado de drenaje sirve para:",
            "options": [
                "Derivar el humor acuoso a un reservorio subconjuntival de forma controlada",
                "Sustituir el cristalino",
                "Corregir la miopía",
                "Reemplazar la córnea",
            ],
            "correct_index": 0,
            "explanation": (
                "El tubo conduce el humor acuoso desde la cámara anterior hasta un plato posterior "
                "donde se reabsorbe, regulando el flujo."
            ),
        },
        {
            "prompt": "Estos implantes se indican habitualmente en:",
            "options": [
                "Primer episodio de conjuntivitis",
                "Glaucomas refractarios o con cirugía filtrante previa fallida",
                "Cualquier catarata",
                "Astigmatismo leve",
            ],
            "correct_index": 1,
            "explanation": (
                "Se reservan para casos en que la trabeculectomía ha fracasado o el pronóstico de "
                "la filtrante es malo."
            ),
        },
        {
            "prompt": "La cobertura del tubo con injerto (esclera o pericardio) busca:",
            "options": [
                "Evitar la erosión de la conjuntiva y la exposición del tubo",
                "Aumentar el flujo de drenaje",
                "Reducir el tiempo quirúrgico",
                "Facilitar la dilatación pupilar",
            ],
            "correct_index": 0,
            "explanation": (
                "El parche protege el tubo: sin él, la conjuntiva se adelgaza, se erosiona y se "
                "abre una puerta de entrada a la infección."
            ),
        },
    ],
    "Iridectomía con Láser": [
        {
            "prompt": "La iridotomía con láser Nd:YAG está indicada principalmente en:",
            "options": [
                "Glaucoma de ángulo cerrado o riesgo de cierre angular",
                "Glaucoma congénito",
                "Retinopatía diabética",
                "Queratocono",
            ],
            "correct_index": 0,
            "explanation": (
                "Abre una comunicación en el iris periférico que iguala presiones y previene o "
                "resuelve el bloqueo pupilar."
            ),
        },
        {
            "prompt": "Una ventaja del procedimiento con láser frente al quirúrgico es:",
            "options": [
                "No requiere incisión ni entrada al quirófano",
                "Elimina la necesidad de seguimiento",
                "Sustituye la medicación de por vida siempre",
                "No necesita anestesia de ningún tipo",
            ],
            "correct_index": 0,
            "explanation": (
                "Se realiza de forma ambulatoria con anestesia tópica y lente de contacto, sin "
                "abrir el globo ocular."
            ),
        },
        {
            "prompt": "La preparación del paciente incluye la administración de:",
            "options": [
                "Un miótico como la pilocarpina para tensar el iris",
                "Un midriático potente",
                "Un anestésico general",
                "Un anticoagulante",
            ],
            "correct_index": 0,
            "explanation": (
                "La miosis adelgaza y tensa el iris periférico, lo que facilita la perforación con "
                "menos energía."
            ),
        },
    ],
    # ── UNIDAD 4 ────────────────────────────────────────────────────────────
    "Facoemulsificación": [
        {
            "prompt": "¿Qué función cumple el viscoelástico durante la facoemulsificación?",
            "options": [
                "Anestesiar la córnea",
                "Mantener el espacio de la cámara y proteger el endotelio corneal",
                "Fragmentar el núcleo",
                "Dilatar la pupila de forma permanente",
            ],
            "correct_index": 1,
            "explanation": (
                "El viscoelástico sostiene la cámara anterior y actúa como escudo mecánico del "
                "endotelio, cuyas células no se regeneran."
            ),
        },
        {
            "prompt": "La capsulorrexis circular continua tiene como objetivo:",
            "options": [
                "Abrir la cápsula anterior de forma controlada para alojar la lente",
                "Extraer el vítreo",
                "Suturar la córnea",
                "Medir la presión intraocular",
            ],
            "correct_index": 0,
            "explanation": (
                "Un borde continuo y regular resiste la tracción y permite implantar la lente "
                "intraocular estable dentro del saco capsular."
            ),
        },
        {
            "prompt": "¿Qué estructura debe conservarse íntegra para implantar la lente en el saco?",
            "options": ["La cápsula posterior", "La retina", "La esclera", "El iris"],
            "correct_index": 0,
            "explanation": (
                "Su rotura obliga a cambiar de plan quirúrgico, con vitrectomía anterior y otra "
                "posición para la lente."
            ),
        },
    ],
    "Extracción extracapsular": [
        {
            "prompt": "La diferencia esencial de la extracción extracapsular frente a la intracapsular es que:",
            "options": [
                "Conserva la cápsula posterior del cristalino",
                "Extrae el cristalino con toda su cápsula",
                "No requiere incisión",
                "No permite implantar lente intraocular",
            ],
            "correct_index": 0,
            "explanation": (
                "Al preservar la cápsula posterior se mantiene la barrera con el vítreo y se puede "
                "implantar la lente en el saco."
            ),
        },
        {
            "prompt": "Frente a la facoemulsificación, la extracción extracapsular requiere:",
            "options": [
                "Una incisión mayor y sutura del cierre",
                "Menor tiempo de recuperación",
                "Menos instrumental",
                "Ausencia de anestesia",
            ],
            "correct_index": 0,
            "explanation": (
                "La salida del núcleo entero exige una incisión amplia, que se cierra con sutura y "
                "prolonga la rehabilitación visual."
            ),
        },
        {
            "prompt": "Sigue siendo una técnica indicada en:",
            "options": [
                "Cataratas muy duras o maduras y contextos sin facoemulsificador",
                "Todas las cataratas iniciales",
                "Cirugía refractiva",
                "Cirugía de párpados",
            ],
            "correct_index": 0,
            "explanation": (
                "En núcleos muy densos la energía de ultrasonido necesaria sería excesiva, y en "
                "muchos entornos no se dispone del equipo."
            ),
        },
    ],
    "Trasplante de córnea": [
        {
            "prompt": "El instrumento que realiza el corte circular del tejido corneal se denomina:",
            "options": ["Trépano", "Blefaróstato", "Vitrector", "Cánula de irrigación"],
            "correct_index": 0,
            "explanation": (
                "El trépano corta un disco corneal de diámetro exacto, tanto en el receptor como "
                "en el botón donante."
            ),
        },
        {
            "prompt": "Al recibir el tejido donante, el instrumentador debe verificar:",
            "options": [
                "Identificación, fecha de vigencia y condiciones de conservación",
                "Únicamente el color del medio de cultivo",
                "El precio del tejido",
                "El grupo sanguíneo del receptor",
            ],
            "correct_index": 0,
            "explanation": (
                "La trazabilidad del injerto es obligatoria: identificación del banco, caducidad e "
                "integridad de la cadena de frío."
            ),
        },
        {
            "prompt": "La sutura del injerto corneal se realiza habitualmente con:",
            "options": ["Nylon 10-0", "Seda 3-0", "Catgut 2-0", "Grapas metálicas"],
            "correct_index": 0,
            "explanation": (
                "El nylon 10-0 monofilamento minimiza el trauma y el astigmatismo del injerto, y "
                "se retira de forma escalonada meses después."
            ),
        },
    ],
    # ── UNIDAD 5 ────────────────────────────────────────────────────────────
    "Vitrectomías del segmento anterior y posterior": [
        {
            "prompt": "El vitrector combina en una sola punta:",
            "options": [
                "Corte y aspiración del vítreo",
                "Ultrasonido e irrigación",
                "Láser y sutura",
                "Iluminación y anestesia",
            ],
            "correct_index": 0,
            "explanation": (
                "La guillotina interna corta el gel vítreo en fragmentos pequeños que se aspiran, "
                "evitando tracción sobre la retina."
            ),
        },
        {
            "prompt": "En la vitrectomía posterior, la línea de infusión sirve para:",
            "options": [
                "Mantener el volumen y la presión del globo mientras se extrae vítreo",
                "Administrar anestesia general",
                "Iluminar el campo",
                "Medir la agudeza visual",
            ],
            "correct_index": 0,
            "explanation": (
                "Sin reposición de volumen el ojo colapsaría al aspirar; la infusión sostiene la "
                "presión intraocular durante todo el procedimiento."
            ),
        },
        {
            "prompt": "Los intercambios de líquidos y gases al final del procedimiento buscan:",
            "options": [
                "Taponar la retina y favorecer su reaplicación",
                "Aumentar la presión de forma permanente",
                "Sustituir el cristalino",
                "Reducir el astigmatismo",
            ],
            "correct_index": 0,
            "explanation": (
                "El gas o el aceite de silicona empujan la retina contra la pared ocular mientras "
                "cicatriza la rotura."
            ),
        },
    ],
    "Retinopatía simple": [
        {
            "prompt": "La fotocoagulación con láser en la retina busca:",
            "options": [
                "Sellar lesiones y frenar la proliferación de vasos anómalos",
                "Corregir la refracción",
                "Extraer el vítreo",
                "Dilatar la pupila",
            ],
            "correct_index": 0,
            "explanation": (
                "Las quemaduras controladas reducen el estímulo isquémico y refuerzan las zonas "
                "de riesgo de desgarro."
            ),
        },
        {
            "prompt": "Para valorar el fondo de ojo es necesario:",
            "options": [
                "Dilatar la pupila previamente",
                "Contraer la pupila",
                "Anestesia general siempre",
                "Suspender la iluminación",
            ],
            "correct_index": 0,
            "explanation": (
                "La midriasis amplía la ventana de observación y permite explorar la periferia "
                "retiniana."
            ),
        },
        {
            "prompt": "El seguimiento periódico de estos pacientes es esencial porque:",
            "options": [
                "La progresión puede ser asintomática hasta fases avanzadas",
                "El tratamiento es siempre definitivo",
                "La retina se regenera sola",
                "Solo importa la presión intraocular",
            ],
            "correct_index": 0,
            "explanation": (
                "El paciente puede mantener buena visión central mientras la enfermedad avanza en "
                "la periferia: solo el control programado lo detecta a tiempo."
            ),
        },
    ],
    # ── UNIDAD 6 ────────────────────────────────────────────────────────────
    "Técnicas para Corrección de estrabismo": [
        {
            "prompt": "Una técnica de debilitamiento muscular consiste en:",
            "options": [
                "Retroceder la inserción del músculo",
                "Resecar una porción del músculo",
                "Suturar el párpado",
                "Extraer el cristalino",
            ],
            "correct_index": 0,
            "explanation": (
                "La retroinserción desplaza el músculo hacia atrás y reduce su fuerza de tracción "
                "sobre el globo."
            ),
        },
        {
            "prompt": "La resección de un músculo extraocular produce:",
            "options": [
                "Refuerzo de su acción",
                "Debilitamiento de su acción",
                "Parálisis definitiva",
                "Ningún cambio en la alineación",
            ],
            "correct_index": 0,
            "explanation": (
                "Al acortar el músculo aumenta su tensión y su efecto sobre el ojo, corrigiendo la "
                "desviación en sentido contrario."
            ),
        },
        {
            "prompt": "La sutura ajustable aporta la ventaja de:",
            "options": [
                "Permitir corregir la alineación en el posoperatorio inmediato",
                "Eliminar la necesidad de anestesia",
                "Acortar la cirugía a la mitad",
                "Evitar cualquier reintervención futura",
            ],
            "correct_index": 0,
            "explanation": (
                "Con el paciente despierto y colaborador se afina la posición horas después, "
                "mejorando la precisión del resultado."
            ),
        },
    ],
    # ── UNIDAD 7 ────────────────────────────────────────────────────────────
    "Miopía, Hipermetropía y Astigmatismo": [
        {
            "prompt": "En la miopía, la imagen se enfoca:",
            "options": [
                "Delante de la retina",
                "Detrás de la retina",
                "Exactamente sobre la retina",
                "Sobre el cristalino",
            ],
            "correct_index": 0,
            "explanation": (
                "El ojo es demasiado largo o el sistema óptico demasiado potente, de modo que el "
                "foco cae por delante de la retina y la visión lejana se vuelve borrosa."
            ),
        },
        {
            "prompt": "El astigmatismo se debe principalmente a:",
            "options": [
                "Una curvatura corneal irregular en distintos meridianos",
                "Una longitud axial excesiva",
                "Una opacidad del cristalino",
                "Una presión intraocular elevada",
            ],
            "correct_index": 0,
            "explanation": (
                "La córnea no es esférica: cada meridiano enfoca en un plano distinto, lo que "
                "distorsiona la imagen a todas las distancias."
            ),
        },
        {
            "prompt": "Antes de una cirugía refractiva con láser es imprescindible:",
            "options": [
                "Comprobar el espesor corneal y la estabilidad de la graduación",
                "Dilatar la vía lagrimal",
                "Realizar una vitrectomía",
                "Implantar una lente intraocular",
            ],
            "correct_index": 0,
            "explanation": (
                "Un lecho corneal insuficiente o una refracción no estabilizada contraindican el "
                "procedimiento por riesgo de ectasia y de resultado inestable."
            ),
        },
    ],
    # ── UNIDAD 8 ────────────────────────────────────────────────────────────
    "Cirugía en Párpados": [
        {
            "prompt": "La blefaroplastia consiste en:",
            "options": [
                "Resecar piel y grasa redundante del párpado",
                "Extraer el cristalino",
                "Reparar la retina",
                "Dilatar la vía lagrimal",
            ],
            "correct_index": 0,
            "explanation": (
                "Se retira el exceso de piel, músculo o grasa para corregir la función palpebral y "
                "el aspecto del párpado."
            ),
        },
        {
            "prompt": "La marcación previa del párpado se realiza:",
            "options": [
                "Con el paciente sentado y antes de infiltrar el anestésico",
                "Después de infiltrar, para mayor comodidad",
                "Al finalizar la cirugía",
                "Solo si el paciente lo solicita",
            ],
            "correct_index": 0,
            "explanation": (
                "La infiltración deforma el tejido y la posición tumbada cambia la caída de la "
                "piel: marcar antes y sentado preserva la simetría."
            ),
        },
        {
            "prompt": "Durante la cirugía palpebral, la protección de la superficie ocular se logra con:",
            "options": [
                "Protectores corneales y lubricación",
                "Midriáticos en dosis altas",
                "Compresión del globo",
                "Retirada del blefaróstato",
            ],
            "correct_index": 0,
            "explanation": (
                "El concha o protector corneal aísla la córnea del instrumental y del cauterio "
                "mientras se trabaja sobre el párpado."
            ),
        },
    ],
}
