"""Contenido académico oficial de Oftalmología.

Fuente única y centralizada: todos los cursos referencian estas mismas
unidades y subtemas mediante CourseTopic, sin duplicar contenido.
"""
from sqlalchemy.orm import Session

from app.seed.seed_questions import OFFICIAL_QUESTIONS
from app.services import course_service
from app.services.content_import import sync_topic
OFFICIAL_CONTENT = [
    {
        "name": 'UNIDAD 1. Generalidades en Cirugía Oftalmológica',
        "description": 'Bases anatómicas, técnicas, materiales y protocolos del entorno quirúrgico oftalmológico.',
        "subtopics": [
            {
                "name": 'Anatomía del Globo Ocular y estructuras anexas',
                "content": """### Introducción
El globo ocular es el órgano receptor de la visión y contiene más de la mitad de los receptores sensoriales del cuerpo humano. El instrumentador quirúrgico debe conocer su anatomía con precisión milimétrica, porque cada cirugía oftalmológica se juega en estructuras de décimas de milímetro: un error de 1 mm al medir la pars plana o al colocar una sutura corneal puede significar la diferencia entre el éxito y una complicación grave.

### Datos clave
- **Forma y tamaño:** esfera de aproximadamente 24 a 25 mm de diámetro y unos 7.5 g de peso, con un abombamiento anterior que forma la córnea.
- **Tres capas:** externa (córnea y esclerótica), media o vascular (iris, cuerpo ciliar y coroides) e interna (retina).
- **Tres cámaras:** anterior (entre córnea e iris), posterior (entre iris y cristalino) y vítrea (detrás del cristalino, la de mayor volumen).
- **Humores:** el humor acuoso llena las cámaras anterior y posterior; el humor vítreo, un gel transparente, ocupa la cavidad vítrea y mantiene la forma del globo.
- **Presión intraocular:** depende del equilibrio entre producción y drenaje del humor acuoso; su control es el objetivo de la cirugía de glaucoma.

### Las tres capas del globo ocular
La capa externa está formada por la esclerótica y la córnea. La esclerótica es un tejido fibroso, blanco y resistente que rodea tres cuartas partes del globo y le da sostén; se continúa por delante con la córnea y por detrás con la vaina del nervio óptico. La córnea es una membrana delgada, transparente y avascular que cubre la porción anterior del ojo y es responsable de la mayor parte de la refracción de la luz. La córnea posee cinco capas: epitelio, capa de Bowman, estroma, membrana de Descemet y endotelio, y su transparencia depende de que se mantenga deshidratada y protegida durante toda la cirugía.

La capa media o vascular comprende el iris, el cuerpo ciliar y la coroides. El iris es la parte coloreada del ojo, un diafragma muscular con una abertura central llamada pupila que regula la entrada de luz. El cuerpo ciliar contiene los procesos ciliares que producen el humor acuoso y los ligamentos suspensorios que sostienen al cristalino y permiten la acomodación. La coroides es un tejido ricamente vascularizado y pigmentado que nutre la capa externa de la retina y evita los reflejos internos de luz.

La capa interna es la retina, la membrana fotorreceptora donde la luz se transforma en impulsos nerviosos que viajan por el nervio óptico hasta el cerebro. La retina posee diez capas sucesivas, desde el epitelio pigmentario hasta la membrana limitante interna, y en su centro se encuentra la mácula, responsable de la visión de detalle. La retina descansa sobre la coroides por fuera y está en contacto con el humor vítreo por dentro.

### Cámaras, humores y drenaje del humor acuoso
La cámara anterior está limitada por la cara interna de la córnea y el iris; en ella se produce el drenaje del humor acuoso a través de la malla trabecular, que desemboca en el canal de Schlemm y de allí al sistema venoso. La cámara posterior se encuentra entre el iris, el cristalino y el cuerpo vítreo; allí están los procesos ciliares que producen el humor acuoso, el cual pasa por la pupila hacia la cámara anterior para ser drenado por el ángulo iridocorneal. La cámara vítrea ocupa el mayor volumen del globo y contiene el cuerpo vítreo, un gel de alto contenido en agua con ácido hialurónico y colágeno que mantiene la forma ocular.

El cristalino es una estructura biconvexa y transparente ubicada detrás del iris, sostenida por los ligamentos suspensorios; cambia de forma para enfocar y con la edad pierde esa capacidad, lo que se conoce como presbicia. Comprender este circuito de producción y drenaje del humor acuoso es indispensable para el instrumentador, porque es la base anatómica de toda la cirugía de glaucoma de la Unidad 3.

### Anexos: órbita, músculos, párpados, conjuntiva y aparato lagrimal
Los anexos del globo ocular incluyen la órbita, los músculos extraoculares, los párpados, la conjuntiva, el aparato lagrimal, las cejas y las pestañas. La órbita es una cavidad ósea en forma de pirámide que aloja al globo, los músculos, el nervio óptico y los vasos. Los seis músculos extrínsecos (rectos superior, inferior, interno y externo, y oblicuos superior e inferior) mueven el globo de forma coordinada; reciben inervación de los pares craneales III (motor ocular común), IV (patético, oblicuo superior) y VI (motor ocular externo), mientras el facial (VII) inerva el orbicular de los párpados y el trigémino (V) da la sensibilidad.

Los párpados son pliegues músculo-mucosos que protegen el ojo y distribuyen la lágrima con cada parpadeo; contienen la placa tarsal y las glándulas de Meibomio, cuya obstrucción crónica origina el chalazión de la Unidad 2. La conjuntiva es una mucosa transparente que tapiza la esclerótica (conjuntiva bulbar) y la cara interna de los párpados (conjuntiva palpebral). El aparato lagrimal produce la lágrima en la glándula lagrimal y la drena por los puntos y canalículos lagrimales hacia el saco lagrimal y el conducto nasolagrimal hasta las fosas nasales.

### Nervio óptico y vascularización
El nervio óptico es el segundo par craneal y transmite la información visual desde la retina hasta el cerebro. Mide unos 4 cm y tiene cuatro segmentos: intraocular (en la papila óptica), intraorbitario, intracanalicular (por el foramen óptico, vulnerable en fracturas de base de cráneo) e intracraneal hasta el quiasma. La arteria oftálmica, rama de la carótida interna, irriga la órbita, y las venas oftálmicas superior e inferior drenan el ojo. El instrumentador debe recordar esta vascularización porque explica el riesgo de hemorragia en cirugías como la enucleación y la importancia de la hemostasia con bipolar o quemador en cada procedimiento.

### Puntos críticos para el instrumentador
El instrumentador usa la anatomía todos los días: mide 3.5 mm desde el limbo en ojos pseudofáquicos y 4 mm en ojos fáquicos para ubicar la pars plana en la inyección intravítrea; reconoce el limbo esclerocorneal como referencia para incisiones y trepanaciones; sabe que la córnea es avascular y debe mantenerse irrigada con solución salina balanceada durante toda la cirugía para proteger el endotelio; y entiende que la conjuntiva y la cápsula de Tenon son los planos de disección en pterigión, estrabismo y cirugía de glaucoma.

### ⚠️ Alertas y perlas del instrumentador
- **Nunca dejes secar la córnea:** mantén irrigación con solución salina balanceada y ofrece hisopos húmedos peinados durante todo el acto quirúrgico.
- **Limbo como punto cero:** casi todas las mediciones (pars plana, colgajos, trepanaciones) se miden desde el limbo; confirma con el cirujano si el ojo es fáquico o pseudofáquico.
- **Conjuntiva = plano de trabajo:** la mayoría de abordajes disecan conjuntiva y Tenon; ten listas tijeras Westcott y pinza Bishop sin garra.
- **Músculos rectos como referencia:** en retina y estrabismo los músculos se reparan con seda para traccionar el globo; no los confundas con la conjuntiva.

### Términos clave
- **Limbo:** zona de transición entre la córnea transparente y la esclerótica blanca; referencia para mediciones quirúrgicas.
- **Pars plana:** porción posterior del cuerpo ciliar, zona segura de entrada a la cavidad vítrea a 3.5-4 mm del limbo.
- **Humor acuoso:** líquido producido por los procesos ciliares que mantiene la presión intraocular.
- **Canal de Schlemm:** vía de drenaje del humor acuoso hacia el sistema venoso.
- **Cápsula de Tenon:** membrana fibrosa que envuelve la esclerótica desde el nervio óptico hasta la córnea; plano de disección.
- **Mácula:** zona central de la retina responsable de la visión de detalle.
- **Papila óptica:** punto donde las fibras de la retina forman el nervio óptico; carece de fotorreceptores.
- **Presbicia:** pérdida de la capacidad de acomodación del cristalino con la edad.""",
            },
            {
                "name": 'Tipos de Anestesia para Cirugía Oftalmológica',
                "content": """### Introducción
La anestesia en cirugía oftalmológica va desde una simple gota de colirio hasta la anestesia general, y el instrumentador participa en todas: instila gotas, prepara jeringas rotuladas, verifica ayuno y alergias, y vigila al paciente. Elegir el tipo correcto depende del procedimiento, la edad, la cooperación del paciente y sus enfermedades de base.

### Datos clave
- **Tópica:** gotas o jalea sobre la superficie ocular (Alcaine, Miraxyl, Roxicaina jalea); para procedimientos cortos de superficie.
- **Local infiltrativa:** xilocaína simple al 2% con aguja fina alrededor de la lesión o subconjuntival.
- **Retrobulbar/peribulbar:** bloqueo detrás o alrededor del globo para cirugía intraocular en adultos colaboradores.
- **General:** niños, pacientes hipertensos no controlados, cirugías largas o evisceración/enucleación.
- **Regla de oro:** verifica alergias, ayuno y ojo a operar antes de administrar cualquier anestésico.

### Anestesia tópica
La anestesia tópica se aplica en forma de gotas o jalea directamente sobre la superficie ocular y es la base de la cirugía de pterigión, la inyección intravítrea y la dilatación de vías lagrimales. Los fármacos más usados son el Alcaine (proximetacaína 0.5%, de 3 a 5 gotas), el Miraxyl (proparacaína, 1 a 2 gotas, útil también para retirar suturas o cuerpos extraños) y la Roxicaina en jalea (lidocaína al 2%, unos 2 cc). En la inyección intravítrea la anestesia tópica debe ser estéril, como la lidocaína al 2% o los colirios de tetracaína estériles. El instrumentador instila las gotas, controla los tiempos de latencia y tiene presente que algunos pacientes necesitan refuerzo con infiltración.

### Anestesia local infiltrativa y bloqueos
La anestesia local infiltrativa con xilocaína simple al 2% (sin epinefrina) se usa en chalazión, pterigión y cirugía palpebral, infiltrando alrededor de la lesión con jeringa de 3 cc y aguja 27Gx1/2". La xilocaína con epinefrina al 2% produce vasoconstricción local y se reserva para casos con mayor sangrado esperado, en volúmenes de 3 a 5 ml. El bloqueo retrobulbar deposita anestésico detrás del globo para cirugía intraocular como catarata y trasplante de córnea en adultos, y la anestesia general se indica en niños, pacientes hipertensos, cirugías largas (vitrectomía, cerclaje de retina) y evisceración o enucleación. En estos casos el instrumentador verifica ayuno, retira prótesis y maquillaje, y confirma la valoración preanestésica.

### Puntos críticos para el instrumentador
El instrumentador nunca administra anestesia sin orden y verificación: confirma el ojo a operar con el paciente y la programación, pregunta por alergias a anestésicos y por ayuno (si la anestesia es local con sedación o general, el ayuno es obligatorio; en tópica pura se acepta un desayuno ligero según protocolo). Rotula toda jeringa cargada con nombre del fármaco y concentración, diferencia la xilocaína con y sin epinefrina por el color del frasco (la de 20 ml es de color azul para la simple), y tiene a mano el equipo de reanimación y la succión cuando hay sedación o anestesia general.

### ⚠️ Alertas y perlas del instrumentador
- **Ojo correcto, siempre:** verifica nombre, ojo a operar y cirujano con el paciente despierto antes de la anestesia; el error de lateralidad es el evento adverso más grave.
- **Con o sin epinefrina:** confirma cuál pidió el cirujano; la epinefrina ayuda con el sangrado pero está contraindicada en pacientes con riesgo cardiovascular según criterio médico.
- **Jeringa rotulada o no existe:** toda jeringa cargada lleva etiqueta con fármaco y concentración; nunca pases una jeringa anónima.
- **Midriasis a tiempo:** si el procedimiento requiere pupila dilatada, inicia el Mydriacyl con antelación (3 gotas separadas por 5 minutos); la fenilefrina es el refuerzo si no dilata.

### Términos clave
- **Anestesia tópica:** bloqueo de la sensibilidad de la superficie ocular con gotas o jalea.
- **Anestesia infiltrativa:** inyección de anestésico local alrededor de la zona a operar.
- **Bloqueo retrobulbar:** inyección de anestésico detrás del globo ocular para cirugía intraocular.
- **Midriasis:** dilatación de la pupila, necesaria para operar el segmento posterior y el cristalino.
- **Miosis:** contracción de la pupila, útil al final de la cirugía de catarata.
- **Epinefrina:** vasoconstrictor que se asocia a la lidocaína para reducir el sangrado local.""",
            },
            {
                "name": 'Instrumental para cirugía Oftalmológica',
                "content": """### Introducción
El instrumental de oftalmología es microquirúrgico: delicado, costoso y específico para cada tiempo quirúrgico. El instrumentador debe reconocer cada pieza por su nombre, saber en qué momento se entrega y cuidarlo como si fuera propio, porque una pinza 0.12 con la punta doblada o unas tijeras Vannas sin filo arruinan el procedimiento. Este subtema reúne el instrumental que aparece en todos los procedimientos de las Unidades 2 a 5.

### Datos clave
- **Exposición:** blefaróstatos de Castroviejo, Colibrí-Barraquer y McNeil-Goldman para separar los párpados.
- **Prensión fina:** pinzas 0.12, Bishop con y sin garra, Jaffe para hilos, mosquito y Adson.
- **Corte:** tijeras Westcott, Vannas, Stevens, corneales derecha e izquierda, de iris y de enucleación.
- **Sutura:** porta agujas Castroviejo fino y de Barraquer; mangos de bisturí 3, 7 y 9 con hojas 11 y 15.
- **Medición y tracción:** compás Castroviejo, ganchos de estrabismo y de Jameson, curetas, trépanos y espátula de ciclodiálisis.

### Separadores, pinzas y tijeras
El blefaróstato mantiene los párpados abiertos durante toda la cirugía: el de Castroviejo es el más versátil, el de Colibrí-Barraquer se usa en inyección intravítrea y el de McNeil-Goldman en trasplante de córnea. Las pinzas 0.12 (con dientes de 0.12 mm) son las pinzas corneales por excelencia; las Bishop con garra sujetan tejidos firmes y sin garra los delicados; las Jaffe manipulan hilos de sutura; las de mosquito hacen hemostasia por pinzamiento y las Adson con o sin garra sirven en enucleación y disecciones amplias. En tijeras, la Westcott diseca conjuntiva y Tenon, la Vannas corta tejidos finos intraoculares, la Stevens diseca planos blandos, las corneales derecha e izquierda completan la trepanación, y las de iris y de enucleación tienen sus usos dedicados.

### Porta agujas, bisturíes y auxiliares
El porta agujas Castroviejo fino es el estándar para suturas 10/0 y 9/0 en córnea, y el de Barraquer se usa en evisceración, enucleación y cierres conjuntivales. Los mangos de bisturí Bard Parker 3, 7 y 9 montan hojas 15 (queratectomía, incisiones esclerocorneales) y 11 (paracentesis, incisión de chalazión, incisión del limbo). Los auxiliares completan la mesa: compás Castroviejo para medir la pars plana y los retroimplantes musculares, ganchos de estrabismo y de Jameson para localizar músculos, curetas 1 y 2 para chalazión y evisceración, trépanos de 7 a 8.5 mm y de succión para córnea, espátula de ciclodiálisis para liberar el pterigión y aplicadores para hemostasia y presión. Las pinzas de campo, el campo hendido y el campo de ojo completan el set de exposición.

### Puntos críticos para el instrumentador
El instrumentador acomoda el instrumental por tiempos quirúrgicos en la mesa de Mayo y de riñón: exposición a la izquierda, corte y disección al centro, sutura a la derecha, o el orden que el cirujano prefiera, pero siempre el mismo. Lava el instrumental con solución salina, lo seca y verifica filos y puntas antes de vestir la mesa. Las piezas de microcirugía nunca se golpean ni se dejan caer; se entregan con la punta hacia el cirujano y el mango orientado a su mano dominante. Al terminar, el instrumental contaminado (como en chalazión) se sumerge 1 minuto en detergente enzimático, se enjuaga, se seca y se lleva cubierto a la central de esterilización.

### ⚠️ Alertas y perlas del instrumentador
- **Revisa antes de vestir:** puntas dobladas, tijeras sin filo y porta agujas flojos se detectan en la mesa, no en mitad de la cirugía.
- **Microcirugía se entrega en mano:** acerca cada instrumento al campo con decisión y anuncia el nombre; el cirujano no debe mirar la mesa.
- **El bipolar siempre listo:** en oftalmología la hemostasia es con bipolar, quemador o mechero; verifica que funcione antes de la incisión.
- **Cuenta todo:** agujas, hojas, esponjas y microesponjas se cuentan al inicio y al final; lo que entra al campo sale del campo.

### Términos clave
- **Blefaróstato:** separador que mantiene los párpados abiertos durante la cirugía.
- **Pinza 0.12:** pinza corneal fina con dientes de 0.12 mm para tejidos delicados.
- **Tijera Westcott:** tijera de disección conjuntival y de Tenon.
- **Porta agujas Castroviejo:** porta agujas fino para micro sutura corneal.
- **Cureta:** instrumento en forma de cucharilla para legrar cavidades como el chalazión.
- **Trépano:** cilindro cortante circular para cortar botones corneales del donante y el receptor.
- **Aplicador:** hisopo estéril para hemostasia por presión y limpieza del campo.""",
            },
            {
                "name": 'Equipos Biomédicos',
                "content": """### Introducción
Los equipos biomédicos son el corazón tecnológico del quirófano oftalmológico: microscopio, facoemulsificador, vitrector, láseres y coaguladores. El instrumentador no los opera, pero verifica que funcionen, los monta, los ceba y responde ante fallas. Un facoemulsificador mal purgado o un microscopio desenfocado detienen la cirugía, por eso este subtema enseña a dejarlos listos antes de que el paciente entre.

### Datos clave
- **Microscopio quirúrgico:** aumento de las estructuras del globo; lentes f: 200, 250 o 300 mm y forro estéril.
- **Facoemulsificadores:** Sovereign, Signature y Stellaris para catarata y vitrectomía anterior.
- **Coagulador/bipolar:** electrocauterización para detener hemorragias de vasos pequeños.
- **Láseres:** Excimer para cirugía refractiva y córnea; Iridex IQ 810 para retina y glaucoma.
- **Criocoagulador:** genera frío para adherir la retina (criopexia transescleral).

### Microscopio y facoemulsificadores
El microscopio quirúrgico aumenta las estructuras anatómicas del globo ocular y se usa en todos los procedimientos; el instrumentador verifica su disponibilidad, su buen estado, la lente adecuada (f: 200, 250 o 300 mm según la cirugía) y coloca el forro estéril del microscopio antes de iniciar. Los facoemulsificadores Sovereign, Signature y Stellaris fragmentan y aspiran el cristalino en la cirugía de catarata; el Stellaris además corta y aspira vítreo en vitrectomías anteriores y posteriores. El montaje incluye conectar líneas de irrigación y aspiración, purgar el sistema para eliminar burbujas, calibrar parámetros según el cirujano y probar el pedal antes de la incisión. El equipo de venoclisis macro y micro se usa para la irrigación en facoemulsificación y catarata extracapsular.

### Coagulación, láser y frío
El coagulador y la pinza bipolar detienen hemorragias en vasos pequeños y cortan tejido blando; si no hay bipolar disponible, se verifica el mechero con alcohol absoluto y encendedor. El láser Excimer realiza cortes micrométricos en la córnea para cirugía refractiva y queratotomías. El láser Iridex IQ 810 es una consola infrarroja para fotocoagulación de retina y procedimientos de glaucoma por vía transescleral. El criocoagulador genera frío para producir una inflamación intencional que adhiere la retina en la criopexia transescleral. El vitrector con fuente de iluminación, el aparato de endoláser de diodos y el electrocauterio completan el arsenal de la cirugía vitreorretinal de la Unidad 5.

### Puntos críticos para el instrumentador
El protocolo exige verificar el funcionamiento de los equipos biomédicos antes de cada cirugía: microscopio enfocado e iluminado, facoemulsificador purgado y calibrado, bipolar con pedal funcional, láser programado y criocoagulador con gas suficiente. Todo equipo que falle se reporta y se reemplaza antes de anestesiar al paciente, nunca durante. El instrumentador conoce la ubicación de interruptores, pedales y conexiones para asistir sin titubeos, protege las fibras ópticas de dobleces bruscos y mantiene secas las conexiones eléctricas. Al terminar, limpia superficies, enrolla cables sin tensarlos y reporta cualquier anomalía para mantenimiento.

### ⚠️ Alertas y perlas del instrumentador
- **Purgar antes de incidir:** el facoemulsificador y las líneas de infusión se ceban y se prueban con el pedal antes de que el cirujano tome el bisturí.
- **Forro estéril siempre:** el microscopio entra al campo solo con su forro; un microscopio sin forro contamina todo.
- **Plan B listo:** si el bipolar falla, mechero, alcohol y encendedor deben estar en la sala; verifica su disponibilidad en el prequirúrgico.
- **Nada de burbujas:** el aire en las líneas de irrigación o infusión causa fluctuaciones de cámara; purga hasta ver flujo continuo.

### Términos clave
- **Facoemulsificador:** equipo que fragmenta con ultrasonido y aspira el cristalino cataratoso.
- **Vitrector:** sistema de corte y aspiración del humor vítreo con iluminación incorporada.
- **Fotocoagulación:** quemadura controlada con láser para sellar desgarros o destruir tejido anormal.
- **Criopexia:** adherencia de la retina mediante aplicación de frío transescleral.
- **Bipolar:** pinza de electrocoagulación que controla sangrados puntuales con corriente entre sus puntas.
- **Pedal:** control de pie que regula potencia y funciones del facoemulsificador, el microscopio y el bipolar.""",
            },
            {
                "name": 'Material de Suturas',
                "content": """### Introducción
En oftalmología se sutura córnea transparente, conjuntiva delgada, músculo y esclera, cada tejido con su calibre y su aguja. El instrumentador monta la sutura en el porta agujas correcto, la entrega sin enredos y corta los cabos a la medida justa. Este subtema ordena las suturas de la tabla de la guía de Claudia por tejido y por cirugía para que nunca dudes cuál pedir.

### Datos clave
- **Calibre:** a mayor número antes del /0, más fina (10/0 es más fina que 6/0); en córnea se usa 10/0.
- **Monofilamento vs multifilamento:** el monofilamento (nylon, polipropileno) desliza y genera menos reacción; el multifilamento trenzado (seda, vicryl) anuda más fácil.
- **Absorbible vs no absorbible:** el vicryl se absorbe solo; el nylon, la seda y el mersilene requieren control o retiro.
- **Aguja corneal:** espatulada 3/8 de círculo para controlar la profundidad sin perforar.
- **Regla práctica:** córnea con nylon 10/0, conjuntiva con vicryl o seda 7/0, músculo con 6/0, control y riendas con seda 4/0.

### Suturas no absorbibles
El nylon 10/0 monofilamento negro de 15 o 30 cm con aguja espatulada es la sutura corneal universal: trasplante de córnea, catarata, trabeculectomía y pterigión con injerto. El nylon 9/0 se usa en pterigión. La seda negra trenzada se usa en varios calibres: 7/0 para conjuntiva e injertos (pterigión, válvula de Ahmed), 6/0 para músculo y esclera (estrabismo, trabeculectomía), 5/0 para reparación muscular y 4/0 para suturas de control, riendas palpebrales y fijación en catarata. El poliéster verde o blanco 5/0 (Dacron, Mersilene) de 45 cm fija bandas en cirugía de retina por su alta resistencia. El polipropileno azul 10/0 fija lentes intraoculares a la esclera con agujas recta, curva o espatulada según la técnica.

### Suturas absorbibles y agujas
La poliglactina 910 violeta (Vicryl) 6/0 de 45 cm con aguja espatulada cierra conjuntiva, Tenon y esclera en enucleación, evisceración, retina y estrabismo sin necesidad de retiro. Las agujas espatuladas de 3/8 de círculo y 6 a 6.5 mm son las corneales: cortan y separan láminas sin perforar la cámara. Las agujas lancet de 13 mm sirven para suturas de control gruesas como la seda 4/0, y las RB-1 para músculo. El instrumentador monta la aguja a dos tercios de la punta del porta agujas, con el filo orientado al tejido, y entrega el conjunto con la hebra extendida y sin nudos.

### Puntos críticos para el instrumentador
El instrumentador prepara las suturas antes de que se pidan según la cirugía programada: nylon 10/0 montado en Castroviejo fino para córnea, seda o vicryl 7/0 para conjuntiva, seda 6/0 para músculo. Corta la hebra a la longitud útil (las de 45 cm se cortan por la mitad para riendas y controles) y mantiene húmeda la seda para que deslice. Al entregar, anuncia calibre y tejido ("nylon 10/0 corneal montado"), y al cortar cabos deja la longitud que el cirujano indique: al ras en córnea, un poco más largos en conjuntiva para que no se entierren. Cuenta agujas al inicio y al final como parte del conteo.

### ⚠️ Alertas y perlas del instrumentador
- **Aguja espatulada en córnea, siempre:** una aguja redonda o cortante común perfora la cámara; verifica el sobre antes de montar.
- **No toques la aguja con la pinza:** sujetar la aguja con pinza de disección la despunta; usa solo el porta agujas.
- **Hebras separadas:** dos suturas iguales sobre la mesa se enredan; monta una a la vez y mantén la otra en su empaque.
- **Vicryl húmedo, nylon seco:** humedece el vicryl y la seda para anudar mejor; el nylon se maneja seco y sin aplastar el monofilamento.

### Términos clave
- **Monofilamento:** hebra única y lisa que genera mínima reacción tisular, como el nylon.
- **Multifilamento:** hebra trenzada de varias fibras que anuda con facilidad, como la seda y el vicryl.
- **Aguja espatulada:** aguja de bordes planos que separa láminas corneales sin perforar.
- **Súrgete:** sutura continua en espiral para cierres conjuntivales y de Tenon.
- **Riendas:** suturas de tracción en músculo o párpado para posicionar el globo.
- **Calibre:** grosor de la sutura; en oftalmología se trabaja entre 4/0 y 10/0.""",
            },
            {
                "name": 'Medicación en Cirugía Oftalmológica',
                "content": """### Introducción
El instrumentador maneja anestésicos, midriáticos, antibióticos, antisépticos y viscoelásticos en cada cirugía: los carga, los rotula, controla dosis y tiempos, y advierte interacciones. Un frasco confundido o una dosis mal cargada pueden arruinar el procedimiento o dañar el ojo, por eso este subtema reúne todos los fármacos de las tablas de la guía de Claudia con su presentación, indicación y dosis de uso.

### Datos clave
- **Anestésicos:** Alcaine, Miraxyl y Roxicaina jalea (tópicos); xilocaína 2% con o sin epinefrina (infiltrativa).
- **Midriasis:** Mydriacyl 1%, fenilefrina 2.5% y 10%, adrenalina; vasoconstricción con Naphcon.
- **Antibióticos y desinflamatorios:** Amikin, Vigamox, Vigadexa, Tobradex, Altracine y dexametasona.
- **Antisepsia e irrigación:** yodopovidona al 5% en saco conjuntival y al 10% en piel; solución salina balanceada de 500 ml.
- **Especiales:** viscoelástico, azul de tripán, mióticos y fármacos intravítreos antiangiogénicos.

### Anestésicos, midriáticos y vasoconstrictores
Los anestésicos tópicos son el Alcaine (proximetacaína 0.5% en gotero de 15 ml, de 3 a 5 gotas), la Roxicaina en jalea (lidocaína al 2% en tubo de 30 ml, unos 2 cc) y el Miraxyl (proparacaína en gotero de 15 ml, 1 a 2 gotas, también para retiro de suturas y cuerpos extraños). La xilocaína simple al 2% sin epinefrina (ampollas de 10 ml y frasco azul de 20 ml) es la infiltrativa estándar, y con epinefrina (frasco de 50 ml, 3 a 5 ml) añade vasoconstricción. Para dilatar la pupila se usa Mydriacyl (tropicamida 1%, 1 a 2 gotas; en protocolo 3 gotas separadas por 5 minutos), fenilefrina 2.5% o 10% (2 a 3 gotas de acción rápida) y adrenalina (ampolla de 1 mg) como dilatador pupilar, además del Naphcon (nafazolina, 1 a 2 gotas) para vasoconstricción previa.

### Antibióticos, antiinflamatorios, antisépticos e irrigación
Los antibióticos incluyen Amikin (amicacina 100 mg en 2 ml, 15 mg por kg), Vigamox (moxifloxacino 5 mg por ml, 1 gota) y Vigadexa o Tobradex (tobramicina con dexametasona, antibiótico y desinflamatorio en gotero o ungüento). La dexametasona inyectable (4 mg) es el desinflamatorio intra y posoperatorio, y el Altracine A en ungüento de 5 g se aplica cada 3 a 4 horas como profiláctico. La antisepsia se hace con OQ Septic (yodopovidona al 5% en solución oftálmica, 1 a 2 gotas en el saco conjuntival) y yodopovidona al 10% para piel de párpados y pestañas. La irrigación usa solución salina balanceada (OQ Balance, 500 ml con bicarbonato) y agua estéril inyectable, con bicarbonato de sodio para midriasis en casos con adherencias.

### Viscoelásticos, colorantes, mióticos e intravítreos
El viscoelástico (como el Healón) protege las células del endotelio corneal y mantiene formada la cámara anterior en catarata y trasplante de córnea. El azul de tripán tiñe de forma reversible la cápsula anterior para visualizarla en facoemulsificación y extracapsular. Los mióticos contraen la pupila: OQ-Miot (acetilcolina intraocular) e Isopto Carpiña (pilocarpina 2%, también para glaucoma y cirugía de catarata). Los fármacos intravítreos antiangiogénicos son Avastin (bevacizumab 25 mg por ml, en vial de 4 o 16 ml), Lucentis (ranibizumab 0.3 mg en 0.23 ml; dosis 0.5 mg en 0.05 ml) y Macugen (pegaptanib en jeringa precargada), con técnica aséptica estricta y vigilancia de endoftalmitis la semana posterior.

### Puntos críticos para el instrumentador
El instrumentador verifica cada fármaco por sus cinco correctos adaptados: paciente, ojo, medicamento, dosis y momento. Rotula jeringas y copas con nombre y concentración, separa la xilocaína con y sin epinefrina, controla los tiempos de las gotas midriáticas y prepara con antelación lo que lleva tiempo: la mitomicina para pterigión se prepara 15 minutos antes de la cirugía. Mantiene la cadena de frío si el fármaco la exige, revisa vencimientos al abrir cada frasco y nunca usa un colirio abierto sin verificar su rotulado y su fecha. Los antibióticos subconjuntivales (amicacina con dexametasona y xilocaína) se cargan en jeringa de insulina con aguja fina justo antes de infiltrar.

### ⚠️ Alertas y perlas del instrumentador
- **Yodopovidona correcta en cada zona:** 10% para piel y pestañas, 5% para el saco conjuntival dejándola actuar 3 minutos; nunca al revés.
- **Frascos que se parecen:** guarda separados los colirios midriáticos, anestésicos y antibióticos; lee la etiqueta en voz alta al cargar.
- **Mitomicina con tiempo:** es citotóxica y se prepara 15 minutos antes; usa guantes y jeringa de insulina con suero según indicación.
- **Vencido = descartado:** revisa la fecha de todo colirio y ampolla al abrirlo; un midriático vencido no dilata y arruina el tiempo quirúrgico.

### Términos clave
- **Midriático:** fármaco que dilata la pupila, como la tropicamida y la fenilefrina.
- **Miótico:** fármaco que contrae la pupila, como la pilocarpina y la acetilcolina.
- **Viscoelástico:** gel que protege el endotelio y mantiene la cámara anterior durante la cirugía.
- **Antiangiogénico:** fármaco que frena el crecimiento de vasos anormales en la retina.
- **Profiláctico:** medicamento preventivo, como el ungüento antibiótico al final de la cirugía.
- **Vasoconstrictor:** fármaco que contrae los vasos y reduce el sangrado, como la nafazolina y la epinefrina.""",
            },
            {
                "name": 'Protocolos del Instrumentador Quirúrgico en cirugía oftalmológica',
                "content": """### Introducción
El protocolo es la coreografía que garantiza que cada cirugía empiece a tiempo, transcurra sin contaminaciones y termine con el paciente seguro. El instrumentador quirúrgico llega al quirófano 20 a 30 minutos antes de la intervención y ejecuta actividades prequirúrgicas, transquirúrgicas y posquirúrgicas verificadas. Este subtema convierte el protocolo general de la guía de Claudia en la lista de trabajo diaria del instrumentador oftalmológico.

### Datos clave
- **Llegada:** 20 a 30 minutos antes; lavado clínico de manos al entrar.
- **Verificación triple:** nombre del paciente, ojo a operar y procedimiento contra la programación.
- **Signos vitales:** tensión arterial apta, glucometría si es diabético, ayuno según anestesia.
- **Campo:** apertura estéril, mesa de Mayo y de reserva por tiempos quirúrgicos, circuito estéril cerrado.
- **Cierre:** conteo final, apósito y cono ocular, limpieza y esterilización del instrumental.

### Actividades prequirúrgicas
El instrumentador constata en recuperación la llegada del paciente y verifica nombre, edad y ojo a operar contra la programación, explicándole en qué consiste el procedimiento. Pregunta por secreciones recientes en los ojos (proceso infeccioso que puede suspender la cirugía), confirma ayuno si habrá sedación o anestesia general, verifica tensión arterial y glucometría en diabéticos junto con su medicación habitual. Prepara al paciente según el procedimiento: midriasis con 3 gotas de Mydriacyl separadas por 5 minutos (con fenilefrina si no dilata), vasoconstricción con Naphcon, inicio de anestesia con Alcaine y xilocaína en jalea si es local. Revisa microscopio y lente (f: 200, 250 o 300 mm), verifica el lente intraocular contra la biometría, solicita instrumental y paquete de ropa en central de esterilización, pide dispositivos en farmacia, confirma mechero con alcohol y encendedor si no hay bipolar, y verifica el funcionamiento de facoemulsificador, bipolar, microscopio, vitrector y láser. Finalmente recibe al paciente en sala con el equipo quirúrgico.

### Actividades transquirúrgicas y posquirúrgicas
En la fase transquirúrgica el instrumentador abre el paquete de ropa de oftalmología, prepara la solución balanceada si se necesita y monta los equipos biomédicos. Realiza el lavado quirúrgico de manos, el secado con compresa estéril, se coloca bata y guantes estériles, arregla la mesa de Mayo y la de reserva según la cirugía, viste al cirujano, lo asiste durante el procedimiento y al final coloca el apósito y el cono ocular. Antes de la incisión repite la verificación del ojo y del lente o fármaco. En la fase posquirúrgica limpia y desinfecta el instrumental, lo envía a esterilización y deja todo preparado para el siguiente procedimiento, incluyendo el conteo final y el registro de lo utilizado.

### Puntos críticos para el instrumentador
La técnica aséptica se sostiene con el circuito estéril: campos colocados sin contaminar, cierre del circuito al delimitar, cambio de guantes si se rompe la barrera y prohibición de pasar material no estéril al campo. El conteo de instrumentos, agujas, hojas, gasas y esponjas se hace al inicio y al final de cada cirugía; toda discrepancia se reporta de inmediato al equipo. La trazabilidad exige registrar suturas, lentes y fármacos con lote y fecha. Ante una complicación (hemorragia, ruptura de cápsula, aumento de presión), el instrumentador mantiene la calma, ofrece lo que el protocolo de cada cirugía indica y nunca abandona el campo. La entrega del paciente incluye revisar conciencia, dolor, sangrado y oclusión antes de trasladarlo a recuperación.

### ⚠️ Alertas y perlas del instrumentador
- **El tiempo es seguridad:** llegar 30 minutos antes no es puntualidad, es el margen para detectar el equipo dañado, el LIO equivocado o el paciente sin ayuno.
- **Verificación en voz alta:** paciente, ojo, procedimiento, lente y fármaco se confirman hablando, con el equipo escuchando.
- **Campo contaminado = campo nuevo:** si algo no estéril toca la mesa, se cambia sin discutir; la infección intraocular (endoftalmitis) es devastadora.
- **Sala lista para el siguiente:** el protocolo termina cuando el quirófano queda montado para la próxima cirugía, no cuando sale el paciente.

### Términos clave
- **Circuito estéril:** área delimitada por los campos donde solo circula material estéril.
- **Tiempo quirúrgico:** cada fase ordenada de la cirugía que define qué instrumental debe estar listo.
- **Conteo:** verificación de instrumentos y materiales al inicio y al final para evitar retenciones.
- **Trazabilidad:** registro de lotes y fechas de cada material implantado o aplicado.
- **Asepsia:** conjunto de medidas para impedir la llegada de microorganismos al campo.
- **Antisepsia:** desinfección de piel y mucosas con yodopovidona antes de la incisión.""",
            },
        ],
    },
    {
        "name": 'UNIDAD 2. Procedimientos Quirúrgicos de oftalmológica generales',
        "description": 'Procedimientos ambulatorios frecuentes y sus cuidados de instrumentación.',
        "subtopics": [
            {
                "name": 'Resección de pterigión',
                "content": """### Introducción
El pterigión, conocido como carnosidad, es el procedimiento ambulatorio más frecuente en la consulta oftalmológica y el instrumentador lo asiste casi a diario. La resección de pterigión exige una mesa de Mayo precisa, control absoluto de la hemostasia y una queratectomía limpia, porque cualquier resto sobre la córnea o un lecho mal preparado aumenta la recidiva. Este subtema cubre la resección simple y sus variantes con plastia.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** tópica con Alcaine y xilocaína en jalea; infiltración opcional con 1 cc de xilocaína simple al 2%.
- **Duración aproximada:** 20 a 40 minutos según la técnica.
- **Instrumental clave:** blefaróstato de Castroviejo, mango de bisturí 3 o 9 con hoja 15, tijeras de Westcott, pinzas Bishop con y sin garra, porta agujas fino, espátula de ciclodiálisis.
- **Suturas:** seda 7/0 o nylon 10/0 o 9/0 para injerto o colgajo.
- **Equipo biomédico:** microscopio con lente f: 200 o 300 mm, bipolar o mechero.

### Concepto e indicaciones
El pterigión es la hiperplasia del tejido conjuntival que invade la córnea; es vascularizado y está compuesto por tres partes: vértice o cabeza (sobre la córnea), cuello (en el limbo) y cuerpo o base (en la conjuntiva). Se clasifica en cuatro grados según la invasión de la curvatura corneal (I a IV) y por ubicación en nasal, temporal, bilateral o en ambos ojos; el nasal es el más frecuente porque los rayos solares se refractan en la nariz. Su causa es multifactorial: exposición mantenida a polvo, calor, viento, radiación ultravioleta y químicos, más predisposición hereditaria; afecta sobre todo a habitantes de zona tropical que trabajan al sol sin protección.

Los signos y síntomas incluyen crecimiento progresivo que invade el limbo y puede llegar al eje visual, ardor, sensación de cuerpo extraño, picazón, resequedad, enrojecimiento y crecimiento anormal de la conjuntiva. El tratamiento inicial con lubricantes, vasoconstrictores y ciclos cortos de esteroides solo alivia síntomas: ningún tratamiento tópico hace desaparecer la lesión y el tratamiento definitivo es quirúrgico. La resección de pterigión está indicada por invasión excesiva del eje visual, estética o persistencia de síntomas, y puede realizarse como resección simple, con plastia de injerto libre o con colgajo rotado; algunos cirujanos aplican mitomicina intraoperatoria como antimitótico.

### Anatomía aplicada y puntos críticos
El pterigión crece desde la conjuntiva bulbar, cruza el limbo esclerocorneal y se adhiere firmemente a la córnea; entre la conjuntiva y la esclera está la cápsula de Tenon, que sirve de referencia para delimitar la disección del injerto. Cuando el pterigión es antiguo deteriora el estroma corneal y deja una mancha blanca llamada leucoma. El instrumentador debe conocer estos planos porque entrega la espátula de ciclodiálisis para liberar la cabeza, las tijeras de Westcott para desprender cuerpo y cola, y el mango de bisturí 15 para la queratectomía que retira los restos sobre la córnea sin dejar rugosidades que favorezcan la recidiva.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** blefaróstato de Castroviejo, mango de bisturí 3 o 9, tijeras de Westcott, aplicadores, pinzas de disección Bishop con y sin garra, porta agujas fino, espátula de ciclodiálisis, pinza de bipolar.
- **Dispositivos y material:** guantes, gasas, apósito ocular, jeringa de vidrio de 10 cc para irrigar, jeringa de 3 cc con aguja 27Gx1/2" para infiltrar, hoja de bisturí 15, campo de ojo, forro del microscopio.
- **Suturas:** seda 7/0 o nylon 10/0 o 9/0 montados en porta agujas fino para injerto o colgajo.
- **Medicamentos:** Alcaine, xilocaína en jalea y simple al 2%, Naphcon para vasoconstricción, ungüento oftálmico Altracine o Tobradex, mitomicina preparada 15 minutos antes si el cirujano la indica.

### Técnica quirúrgica paso a paso
1. Paciente en decúbito dorsal; asepsia y antisepsia de la región.
2. Anestesia tópica con Alcaine y xilocaína en jalea, más gotas de Naphcon para vasoconstricción; infiltración opcional con 1 cc de xilocaína simple al 2%.
3. Colocación del campo de ojo y del forro del microscopio; colocación del blefaróstato de Castroviejo.
4. Liberación de la cabeza del pterigión con espátula de ciclodiálisis y pinza Bishop con garra.
5. Desprendimiento de la cola y el cuerpo con tijeras de Westcott y pinza Bishop con garra.
6. Hemostasia con quemador o bipolar y aplicador, irrigando agua estéril gota a gota con jeringa de 10 cc.
7. Queratectomía: resección de los restos sobre la córnea con mango de bisturí 3 y hoja 15.
8. En plastia con injerto libre: corte longitudinal de conjuntiva sana respetando la cápsula de Tenon, colocación del injerto con dos pinzas Bishop y fijación con puntos separados de seda 7/0 o nylon 10/0.
9. En plastia con colgajo rotado: corte en U invertida sin desprender totalmente, rotación hasta el lecho resecado con pinza 0.12 y fijación con puntos separados.
10. Corte de suturas con tijeras de Westcott, irrigación abundante con jeringa de 5 o 10 cc y cánula.
11. Aplicación de ungüento Altracine o Tobradex, retiro del blefaróstato y oclusión con apósito fijado con micropore.

### Complicaciones y respuesta del instrumentador
- **Perforación de córnea o esclera:** intraoperatorias; el instrumentador mantiene el campo seco, ofrece magnificación y tiene listas las suturas de reparación.
- **Recidiva:** la complicación posoperatoria más temida; se previene con queratectomía completa, lecho limpio e injerto bien fijado.
- **Úlcera corneal o dellen:** por desecación; el instrumentador asegura la oclusión y el ungüento al final.
- **Sangrado excesivo:** tener bipolar funcional y aplicadores a la mano desde el inicio.

### Manejo posoperatorio
El paciente puede sentir molestia el primer día; recibe gotas y ungüento antibiótico con desinflamatorio para cicatrizar rápido, con oclusión inicial según el cirujano. El instrumentador explica los signos de alarma (dolor intenso, pérdida visual, secreción purulenta) y la importancia de no frotarse el ojo, usar protección solar y asistir a los controles para detectar recidiva temprana.

### ⚠️ Alertas y perlas del instrumentador
- **Mitomicina con 15 minutos:** si el cirujano la usa, se prepara 15 minutos antes en jeringa de insulina con suero; es citotóxica, usa guantes.
- **Queratectomía completa:** insiste en ofrecer el mango con hoja 15 hasta que el cirujano confirme lecho limpio; los restos son recidiva futura.
- **Vasoconstricción previa:** las gotas de Naphcon antes de incidir reducen el sangrado y dan un campo limpio.
- **Injerto sin Tenon grueso:** al tomar el injerto libre respeta la cápsula de Tenon como referencia y evita manipular su zona central.

### Términos clave
- **Pterigión:** hiperplasia fibrovascular de la conjuntiva que invade la córnea.
- **Queratectomía:** resección de los restos de pterigión sobre la córnea con hoja de bisturí.
- **Leucoma:** mancha blanca corneal que deja un pterigión antiguo al deteriorar el estroma.
- **Recidiva:** reaparición del pterigión después de la cirugía.
- **Plastia:** reconstrucción del lecho con injerto libre de conjuntiva o colgajo rotado.
- **Mitomicina:** fármaco antimitótico intraoperatorio que reduce la recidiva.""",
            },
            {
                "name": 'Drenaje de chalazión',
                "content": """### Introducción
El drenaje de chalazión es un procedimiento corto y ambulatorio en el que el instrumentador maneja un set pequeño pero muy específico: pinza de chalazión, curetas y quemador. Aunque dura minutos, es una cirugía contaminada por definición (material purulento), así que el protocolo de aislamiento del instrumental y el manejo posquirúrgico son tan importantes como la técnica misma.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** local con infiltración de 1 cc de xilocaína simple al 2% alrededor del chalazión.
- **Duración aproximada:** 10 a 20 minutos.
- **Instrumental clave:** pinza de chalazión (Desmarres o Lampert), set de curetas 1 y 2, mango de bisturí 3, 7 o 9 con hoja 11, tijeras de Westcott, quemador o pinza bipolar.
- **Suturas:** no requiere sutura de rutina.
- **Equipo biomédico:** microscopio con lente f: 200 o 300 mm, bipolar o mechero con encendedor.

### Concepto e indicaciones
Chalazión viene del griego "pequeño bulto": es la inflamación crónica de una glándula de Meibomio por retención de su secreción sebácea, que forma un quiste de bordes nítidos, esférico y generalmente indoloro que eleva la piel del párpado. Se diferencia del orzuelo en que el chalazión aparece más lejos del borde palpebral y responde al bloqueo graso, mientras el orzuelo es una infección aguda del borde. Los signos incluyen irritación, hinchazón e hipersensibilidad, con dolor y picazón como síntomas; la causa es un germen (típicamente estafilococo) que penetra la glándula y genera tejido granular.

El chalazión pequeño puede resolverse solo, y el grande se trata primero con antibióticos orales (doxiciclina 100 mg cada 12 horas por 14 días) y antiinflamatorios tópicos (neomicina con dexametasona o tobramicina con dexametasona), además de recomendaciones dietéticas como evitar grasas saturadas, refrescos de color y exceso de azúcar. Si persiste, crece o distorsiona la visión por compresión corneal, se indica el drenaje quirúrgico con curetaje y resección de la cápsula.

### Anatomía aplicada y puntos críticos
El chalazión nace en las glándulas de Meibomio, glándulas sebáceas alargadas dentro de la placa tarsal del párpado que secretan el componente graso de la lágrima e impiden que los párpados se adhieran. El abordaje se hace por la conjuntiva tarsal (cara interna del párpado) para no dejar cicatriz visible en la piel. El instrumentador retrae el párpado con gasa según la ubicación de la lesión, coloca la pinza de chalazión que comprime y delimita la tumoración con hemostasia incluida, y ofrece la hoja 11 para la incisión vertical sobre la conjuntiva tarsal.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** pinza de chalazión, mango de bisturí 3 con hoja 11, set de curetas 1 y 2, quemador o pinza bipolar, pinza de disección, tijeras de Westcott.
- **Dispositivos y material:** guantes, gasas, aplicadores, campo de ojo, 1 jeringa de 3 cc con aguja 27Gx1/2", jeringa de insulina opcional.
- **Medicamentos:** xilocaína simple al 2% para infiltrar, Naphcon en recuperación para vasoconstricción.

### Técnica quirúrgica paso a paso
1. Paciente en decúbito dorsal; en recuperación se aplican gotas de Naphcon para vasoconstricción y se rotula al paciente con nombre, tensión, ojo, cirujano.
2. Se aplica el protocolo de cirugía contaminada y se retiran los elementos e instrumentos que no se usarán.
3. Asepsia y antisepsia; colocación del campo de ojo y del forro del microscopio.
4. Infiltración local con 1 cc de xilocaína simple al 2% en jeringa de 3 cc con aguja 27Gx1/2" alrededor del chalazión.
5. Retracción del párpado con gasa según la ubicación de la lesión.
6. Colocación de la pinza de chalazión que comprime y delimita la tumoración.
7. Incisión sobre la conjuntiva tarsal con mango de bisturí y hoja 11.
8. Curetaje con curetas de chalazión y retiro del material purulento con aplicador hasta limpiar la cavidad.
9. Hemostasia con bipolar o quemador y aplicador; resección opcional de la cápsula con tijeras Westcott y pinza Bishop.
10. Retiro de la pinza de chalazión, compresión con gasas y oclusión opcional con apósito y micropore.

### Complicaciones y respuesta del instrumentador
- **Sangrado del lecho:** responde con compresión de 3 minutos y quemador o bipolar con aplicador siempre a la mano.
- **Vaciado incompleto y recidiva:** ofrece curetas de ambos tamaños y aplicadores hasta que el cirujano confirme cavidad limpia.
- **Infección posoperatoria:** al ser cirugía contaminada, el instrumentador extrema el aislamiento del material purulento y descarta todo lo usado.

### Manejo posoperatorio
Se sumerge el instrumental en detergente enzimático durante 1 minuto, se enjuaga y se seca en sala; se desecha todo el material utilizado, el equipo se cambia pijama, gorro y mascarilla para salir, y el instrumental se lleva cubierto a la central de esterilización. Al paciente se le indica higiene palpebral, no maquillaje hasta control y vigilancia de aumento de dolor, enrojecimiento o secreción.

### ⚠️ Alertas y perlas del instrumentador
- **Es cirugía contaminada:** activa el protocolo desde el inicio (aislar, desechar, detergente enzimático 1 minuto) sin excepciones.
- **Pinza bien centrada:** la pinza de chalazión debe delimitar toda la tumoración; mal centrada deja bordes sin curetear.
- **Hoja 11, no 15:** la incisión conjuntival tarsal se hace con hoja 11 para un corte preciso y corto.
- **Compresión final de 3 minutos:** no omitas la compresión con gasa seca antes de dar por terminado el procedimiento.

### Términos clave
- **Chalazión:** quiste palpebral por obstrucción crónica de una glándula de Meibomio.
- **Glándula de Meibomio:** glándula sebácea tarsal que aporta el componente graso de la lágrima.
- **Orzuelo:** infección aguda del borde palpebral, diferente del chalazión en ubicación y curso.
- **Curetaje:** legrado de la cavidad del quiste con cureta hasta dejarla limpia.
- **Cirugía contaminada:** procedimiento con material purulento que exige protocolo de aislamiento y descarte.
- **Pinza de chalazión:** pinza que fija, delimita y comprime la tumoración dando hemostasia.""",
            },
            {
                "name": 'Dilatación de vías lagrimales',
                "content": """### Introducción
El lagrimeo persistente con secreción suele deberse a una vía lagrimal obstruida, y la dilatación con sondas es el procedimiento que la permeabiliza. El instrumentador maneja un set delicado de sondas de calibres progresivos y verifica la permeabilidad con irrigación, todo con manos suaves porque el canalículo se perfora con facilidad. Este subtema incluye también la dacriocistorrinostomía como referencia avanzada de la misma vía anatómica.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** tópica con Alcaine; general en niños.
- **Duración aproximada:** 15 a 25 minutos.
- **Instrumental clave:** dilatador o iniciador, sondas lagrimales de calibres 00-0, 1-2, 3-4, 5-6 y 7-8, cánula de irrigación.
- **Suturas:** no requiere en la dilatación simple (en dacriocistorrinostomía: seda o prolene 7/0 y vicryl 6/0).
- **Equipo biomédico:** microscopio con lente f: 200 o 300 mm.

### Concepto e indicaciones
La dilatación de vías lagrimales es el procedimiento quirúrgico mediante el cual se sondea el conducto lagrimal obstruido con dilatadores y sondas de calibre progresivo. Los signos y síntomas incluyen conducto nasolagrimal obstruido con lagrimeo constante y pus en la comisura del ojo; el bloqueo aumenta el riesgo de infecciones oculares. Cuando la obstrucción es completa o crónica del saco y el conducto nasolagrimal, el tratamiento definitivo es la dacriocistorrinostomía: una operación que drena el conducto lagrimal hacia la nariz construyendo un nuevo sistema de drenaje de las lágrimas, indicada en dacriocistitis aguda (típicamente por estafilococo beta hemolítico) o crónica (estreptococo pneumoniae), con lagrimeo, secreción, inflamación y dolor al presionar el saco lagrimal.

### Anatomía aplicada y puntos críticos
La lágrima drena por el punto lagrimal del canto interno hacia los canalículos superior e inferior, que desembocan en el saco lagrimal y de allí al conducto nasolagrimal hasta el meato inferior nasal. El sondaje sigue exactamente esa ruta: punto, canalículo, saco y conducto. El instrumentador presenta primero el iniciador para dilatar el punto, luego las sondas en orden creciente de calibre sin forzar, y finalmente la jeringa de 3 cc con solución estéril para comprobar que el líquido pasa a la nariz, que es la prueba de permeabilidad.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** dilatador o iniciador, sondas lagrimales 00-0, 1-2, 3-4, 5-6 y 7-8, cánula de irrigación.
- **Dispositivos y material:** guantes, gasas, jeringa de 3 cc con solución estéril, campo de ojo, forro del microscopio.
- **Medicamentos:** Alcaine tópico; en dacriocistorrinostomía además anestesia general, antibióticos y gasa para taponamiento nasal.

### Técnica quirúrgica paso a paso
1. Paciente en decúbito dorsal; asepsia y antisepsia.
2. Anestesia tópica con Alcaine (general en niños).
3. Colocación del campo de ojo y del forro del microscopio.
4. Dilatación inicial del punto y conducto lagrimal con el iniciador.
5. Sondaje progresivo con sondas de calibres crecientes, de la más fina a la más gruesa, sin forzar el paso.
6. Verificación de la permeabilidad irrigando solución estéril con jeringa de 3 cc y cánula: el paso del líquido a la nariz confirma la vía libre.
7. En dacriocistorrinostomía (técnica avanzada de referencia): incisión de piel junto al canto interno, disección hasta el hueso nasal, trepanación ósea con irrigación continua, colgajos del saco lagrimal y de la mucosa nasal unidos con vicryl 6/0, cierre de piel con prolene o seda 7/0 y apósito pequeño.

### Complicaciones y respuesta del instrumentador
- **Perforación del conducto o del canalículo:** por forzar la sonda; el instrumentador ofrece los calibres en orden y nunca presiona al cirujano a avanzar.
- **Falsa vía y sangrado:** ante sangrado, ofrece gasas, vasoconstrictor y pausa; verifica que la sonda sigue la ruta anatómica.
- **Reestenosis posoperatoria:** se previene con sondaje completo de todos los calibres y verificación final de permeabilidad.
- **En dacriocistorrinostomía:** hemorragia, infección, cierre de la anastomosis y dehiscencia; tener electrocauterio y material de sutura completo.

### Manejo posoperatorio
Tras la dilatación simple no se ocluye de rutina; se indican gotas antibióticas y control del lagrimeo. En dacriocistorrinostomía se mantiene taponamiento nasal según indicación, antibióticos sistémicos y vigilancia de sangrado nasal, infección y permeabilidad de la anastomosis en los controles.

### ⚠️ Alertas y perlas del instrumentador
- **Orden de calibres sagrado:** iniciador primero y sondas de fina a gruesa; saltarse un calibre perfora el canalículo.
- **La prueba es la irrigación:** el procedimiento solo termina cuando la solución pasa a la nariz; prepara la jeringa de 3 cc desde el inicio.
- **Tacto, no fuerza:** las sondas lagrimales se sostienen con los dedos, nunca con el puño; si no pasa, se cambia de ángulo, no de fuerza.
- **Niños = general:** la dilatación en niños se hace con anestesia general; verifica ayuno y valoración preanestésica.

### Términos clave
- **Sondaje lagrimal:** paso de sondas por la vía lagrimal para permeabilizarla.
- **Iniciador:** dilatador inicial que abre el punto lagrimal para el sondaje.
- **Dacriocistitis:** infección del saco lagrimal, aguda o crónica.
- **Dacriocistorrinostomía:** cirugía que crea un drenaje nuevo del saco lagrimal hacia la nariz.
- **Permeabilidad:** comprobación de que el líquido irrigado pasa hasta la nariz.
- **Canalículo:** conducto fino que lleva la lágrima del punto lagrimal al saco.""",
            },
            {
                "name": 'Inyecciones intravítreas',
                "content": """### Introducción
La inyección intravítrea aplica el fármaco directamente en el humor vítreo para maximizar el efecto local y minimizar los efectos adversos sistémicos. Es un procedimiento de minutos pero de exigencia máxima en asepsia: una contaminación produce endoftalmitis y ceguera. El instrumentador domina la secuencia de 11 pasos, las medidas exactas y el control del fármaco, porque aquí cada milímetro y cada décima de mililitro cuentan.

### Ficha técnica rápida
- **Posición:** decúbito dorsal, paciente mirando arriba y al lado contrario del punto de inyección.
- **Anestesia:** tópica estéril (lidocaína al 2% o colirio de tetracaína) más antiséptico.
- **Duración aproximada:** 5 a 15 minutos por ojo.
- **Instrumental clave:** blefaróstato de Colibrí-Barraquer, compás de medición, aplicador o pinza para movilizar la conjuntiva.
- **Dispositivos:** jeringa de insulina con aguja 27Gx1/2" (o jeringa de 1 cc con aguja 30G) con 0.05 a 0.1 ml de fármaco; jeringa de vidrio de 5 o 10 cc para el lavado.
- **Equipo biomédico:** microscopio o lámpara de hendidura con lente de no contacto para el control final.

### Concepto e indicaciones
La inyección intravítrea consiste en depositar el medicamento en la cavidad vítrea, detrás del cristalino, y es la vía de administración para la degeneración macular asociada a la edad (DMAE) húmeda, el edema macular diabético y quístico, las oclusiones venosas de la retina, la uveítis, la retinitis vírica, la neovascularización coroidea del miope y la endoftalmitis, entre otros. La DMAE húmeda es la indicación emblemática: en ella crecen vasos anormales bajo la mácula que sangran y pierden visión central en semanas, y los fármacos antiangiogénicos (Avastin o bevacizumab, Lucentis o ranibizumab 0.5 mg en 0.05 ml, Macugen o pegaptanib) frenan ese crecimiento; el Lucentis se inicia con una inyección mensual por tres meses y luego mantenimiento con vigilancia de agudeza visual. Las contraindicaciones incluyen hipersensibilidad al fármaco e infección o inflamación ocular activa, y toda inyección exige técnica aséptica con vigilancia del paciente durante la semana posterior por el riesgo de endoftalmitis, desprendimiento de retina y catarata traumática.

### Anatomía aplicada y puntos críticos
El punto de entrada es la pars plana, medida con compás desde el limbo hacia atrás: aproximadamente 3.5 mm en ojos afáquicos o pseudofáquicos y 4 mm en ojos fáquicos, porque el cristalino presente exige entrar más atrás. La aplicación se realiza en el cuadrante temporal inferior (algunos prefieren cuadrantes inferiores por el fenómeno de Bell) y se evitan las 3 y las 9 por las arterias ciliares. Antes de pinchar se moviliza la conjuntiva unos milímetros con aplicador o pinza para que no coincidan el orificio conjuntival y el escleral, con máximo cuidado en pacientes anticoagulados para evitar hemorragia subconjuntival.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** blefaróstato de Colibrí, compás de medición, aplicador estéril, pinza conjuntival y cánulas de irrigación.
- **Dispositivos y material:** guantes, gasas, jeringa de vidrio de 5 o 10 cc para el lavado del globo, 2 jeringas de insulina (una puede usarse para aspirar 0.4 ml de humor acuoso si el protocolo lo indica), aguja de filtro para cargar el vial cuando aplique.
- **Medicamentos:** anestésico tópico estéril, yodopovidona al 10% para piel y párpados y al 5% para el saco conjuntival, solución con antibiótico para el lavado, fármaco intravítreo purgado dejando 0.05 ml en la jeringa, colirio antibiótico de amplio espectro (ofloxacina o ciprofloxacino) para después.

### Técnica quirúrgica paso a paso
1. Dilatación pupilar para visualizar el fondo y controlar latido venoso y palidez papilar.
2. Anestesia tópica estéril con lidocaína al 2% o tetracaína, más gotas de Alcaine según protocolo.
3. Limpieza ocular con yodopovidona: al 10% en piel de párpados, borde palpebral y pestañas; al 5% en el saco conjuntival dejándola actuar 3 minutos.
4. Colocación del blefaróstato de Colibrí-Barraquer y lavado del globo con jeringa de 5 o 10 cc con solución antibiótica.
5. Medición con el compás desde el limbo hacia la pars plana: 3.5 mm en pseudofáquicos y 4 mm en fáquicos.
6. Indicación al paciente de mirar arriba y al lado contrario; inyección en el cuadrante temporal inferior evitando las 3 y las 9.
7. Movilización de la conjuntiva en el punto con aplicador o pinza para desplazar el orificio.
8. Inserción de la aguja perpendicular a la esclera con la punta hacia el centro del globo, sin contaminarla por contacto.
9. Inyección suave de 0.05 a máximo 0.1 ml del fármaco para evitar efecto difusor.
10. Extracción suave de la aguja presionando con el aplicador para prevenir reflujo y sangrado.
11. Colirio antibiótico de amplio espectro (2 gotas cada 8 horas por 3 a 5 días) y exploración de percepción luminosa y visión de objetos, valorando la perfusión de la arteria central de la retina. No se ocluye el ojo.

### Complicaciones y respuesta del instrumentador
- **Endoftalmitis:** la más grave; se previene con asepsia total, yodopovidona correcta y fármaco estéril; ante dolor intenso y pérdida visual posoperatoria se alerta de inmediato.
- **Aumento de presión intraocular y oclusión vascular:** vigilar perfusión papilar con oftalmoscopio o lámpara tras la inyección.
- **Hemorragia subconjuntival o vítrea, desgarro y desprendimiento de retina, catarata traumática:** técnica perpendicular al centro del globo y volumen mínimo los previenen.
- **Reflujo del fármaco:** presión con aplicador al extraer la aguja.

### Manejo posoperatorio
No se ocluye el ojo. El paciente recibe colirio antibiótico por 3 a 5 días, se le enseña a instilarlo él mismo y se le cita a control en la primera semana para detectar infección temprana. Se advierte no frotarse el ojo, consultar por dolor, enrojecimiento progresivo, destellos o cortina visual, y no conducir si persiste visión borrosa.

### ⚠️ Alertas y perlas del instrumentador
- **Asepsia de quirófano en consulta:** aunque se haga fuera del quirófano, la técnica es la misma: campo, blefaróstato, antiséptico y nada toca la aguja.
- **Purgar dejando 0.05 ml:** la jeringa se carga y se ajusta a la dosis exacta antes de entrar; nunca purgues dentro del ojo.
- **Fármaco y ojo verificados:** confirma principio activo, dosis y lateralidad en voz alta; un vial equivocado no tiene corrección.
- **Sin oclusión:** a diferencia de casi toda la cirugía oftalmológica, tras la inyección intravítrea el ojo NO se ocluye.

### Términos clave
- **Pars plana:** zona de entrada segura a la cavidad vítrea, a 3.5-4 mm del limbo.
- **DMAE húmeda:** degeneración macular con vasos anormales que pierden visión central rápidamente.
- **Antiangiogénico:** fármaco que frena el crecimiento de vasos anormales (bevacizumab, ranibizumab, pegaptanib).
- **Endoftalmitis:** infección dentro del globo ocular; la complicación más temida.
- **Fenómeno de Bell:** rotación refleja del ojo hacia arriba que se previene inyectando en cuadrantes inferiores.
- **Afáquico/pseudofáquico/fáquico:** ojo sin cristalino, con lente intraocular o con cristalino propio.""",
            },
        ],
    },
    {
        "name": 'UNIDAD 3. Glaucoma',
        "description": 'Procedimientos para favorecer el drenaje del humor acuoso y controlar la presión intraocular.',
        "subtopics": [
            {
                "name": 'Trabeculotomía más iridectomía periférica',
                "content": """### Introducción
La cirugía filtrante del glaucoma crea una salida nueva para el humor acuoso cuando los fármacos ya no controlan la presión intraocular. Para el instrumentador es una microcirugía de precisión: colgajo escleral tallado a mano, penetración a cámara anterior y suturas 10/0 que regulan cuánta agua sale. Un colgajo mal suturado deja el ojo hipotónico, por eso cada paso de esta técnica exige instrumental exacto y campo impecable.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** local.
- **Duración aproximada:** 30 a 60 minutos.
- **Instrumental clave:** equipo de glaucoma, trabeculótomo, cuchillete de Wheeler o Ziegler, tijeras Vannas y Wescott, pinzas 0.12 y Jaffe para hilos, porta agujas Castroviejo fino, separadores Jaffe, pinzas de mosquito rectas.
- **Suturas:** seda atraumática 4/0, vicryl 7/0 y nylon 10/0.
- **Equipo biomédico:** microscopio quirúrgico, electrocauterio.

### Concepto e indicaciones
La trabeculectomía es el procedimiento filtrante de referencia: disminuye la presión intraocular al crear un canal nuevo para la salida del humor acuoso entre la cámara anterior y el espacio bajo la cápsula de Tenon, descomprimiendo la retina y los vasos del interior del ojo y mejorando la visión. La trabeculotomía asociada a iridectomía periférica suma la apertura de la malla trabecular y una pequeña resección del iris en su base para garantizar el paso del acuoso y evitar el bloqueo pupilar. Se indica en glaucoma no controlado con tratamiento médico o láser, y su éxito depende tanto del tallado del colgajo como del control posoperatorio de la ampolla filtrante.

### Anatomía aplicada y puntos críticos
El humor acuoso se produce en los procesos ciliares, circula de la cámara posterior a la anterior por la pupila y drena por la malla trabecular hacia el canal de Schlemm. En el glaucoma esa vía está obstruida y la presión daña el nervio óptico. La cirugía actúa justo allí: peritomía conjuntival a 5 mm del limbo, colgajo escleral con base en el limbo, penetración a cámara anterior por vía corneal, resección del fragmento corneoescleral que incluye el trabéculo e iridectomía basal periférica. El instrumentador reconoce cada plano y entrega el cuchillete correcto para cada uno: hoja 15 para el tallado, hoja 11 para la penetración y Vannas para la resección.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** equipo de glaucoma, separadores Jaffe, pinzas 0.12, tijeras Wescott, trabeculótomo, cuchillete de Wheeler o Ziegler, tijeras Vannas, pinzas Jaffe para hilos, porta agujas Castroviejo fino, pinzas de mosquito rectas, pinza Halsted, pinza Bishop con dientes.
- **Dispositivos y material:** solución salina balanceada, gasas 10x10, jeringas de insulina, equipo de venopack, agujas 20 y 22, hisopos, micropore, hojas de bisturí 15 y 11.
- **Suturas:** seda atraumática 4/0 para la rienda muscular, vicryl 7/0 para conjuntiva, nylon 10/0 para el colgajo escleral.
- **Medicamentos:** anestésico local, dexametasona 0.5 ml y gentamicina 0.5 ml para aplicar en el piso de la órbita, isodine para antisepsia.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, bata y guantes con técnica cerrada; vestir mesas de riñón y de Mayo y acomodar el instrumental por tiempos.
2. Antisepsia de la región operatoria con vaso de asepsia, torunda y pinza de anillos; colocación de campos y cierre del circuito estéril.
3. Separación de párpados con blefaróstato de Castroviejo, lavado de fondos de saco con solución salina balanceada e irrigación y secado.
4. Rienda del músculo recto superior con seda 4/0 montada en pinza Halsted y pinza Bishop con dientes.
5. Peritomía conjuntival a 5 mm de la base del limbo en los meridianos 12 y 1 con tijeras Wescott, limpieza escleral y hemostasia con electrocauterio, secando con hisopos húmedos.
6. Tallado del rectángulo escleral con base en el limbo usando bisturí con hoja 15.
7. Penetración a cámara anterior por vía corneal debajo del colgajo con hoja 11.
8. Resección del fragmento corneoescleral que incluye el trabéculo con tijeras Vannas y pinza colibrí, más iridectomía basal periférica.
9. Sutura del colgajo escleral con nylon 10/0 en porta agujas de microcirugía, corte de cabos y súrgete conjuntival.
10. Limpieza del área con solución salina y cánula de irrigación; aplicación de dexametasona y gentamicina en el piso de la órbita con jeringa de 3 cc y aguja 25.
11. Apósito ocular con gasa doblada fijado con micropore y fin del acto quirúrgico.

### Complicaciones y respuesta del instrumentador
- **Hipotonía ocular:** por filtración excesiva; el instrumentador ofrece sutura adicional de inmediato y verifica el sellado conjuntival.
- **Infección de la ampolla:** la complicación tardía más grave; se previene con antisepsia estricta y técnica sin tocamientos.
- **Dehiscencia de herida y catarata:** ante dehiscencia se re-sutura; la progresión de catarata se vigila en controles.
- **Hemorragia intraoperatoria:** hemostasia inmediata con cauterio y campo seco con hisopos.

### Manejo posoperatorio
Reposo absoluto por 24 horas con oclusión compresiva, midriáticos, prednisolona y cloranfenicol tópicos según indicación. El instrumentador explica que el ojo quedará con una ampolla filtrante bajo el párpado superior, que no debe frotarse ni recibir golpes, y que la visión borrosa inicial es esperable mientras la cámara se estabiliza.

### ⚠️ Alertas y perlas del instrumentador
- **Hojas en orden:** 15 para tallar, 11 para penetrar; tener ambas montadas antes de la peritomía ahorra minutos críticos.
- **Nylon 10/0 tenso pero no estrangulante:** el colgajo regula la filtración; un punto flojo hipotónico y uno apretado no filtra.
- **Hisopos húmedos siempre:** el sangrado escleral se seca, no se frota; ofrece hisopos húmedos peinados de forma continua.
- **Antibiótico más antiinflamatorio al final:** carga la jeringa de 3 cc con 0.5 ml de dexametasona y 0.5 ml de gentamicina antes del cierre.

### Términos clave
- **Trabeculectomía:** cirugía filtrante que crea un canal de drenaje del humor acuoso bajo la Tenon.
- **Malla trabecular:** tejido filtrante del ángulo por donde drena el humor acuoso.
- **Iridectomía periférica:** resección de un fragmento de iris en su base para facilitar el paso del acuoso.
- **Ampolla filtrante:** reservorio subconjuntival donde se acumula el humor drenado.
- **Hipotonía ocular:** presión intraocular anormalmente baja, riesgo de la sobre-filtración.
- **Peritomía:** incisión y disección de la conjuntiva alrededor del limbo.""",
            },
            {
                "name": 'Colocación de implantes para Drenaje de Humor acuoso',
                "content": """### Introducción
Cuando la cirugía filtrante convencional falla o el glaucoma es refractario, se implanta un dispositivo de drenaje que deriva el humor acuoso a un reservorio ecuatorial. Para el instrumentador es una cirugía de componentes: placa, tubo y parche que deben llegar estériles, verificados y en el orden de montaje, porque el tubo se corta a medida dentro del quirófano y no hay repuestos a mitad del procedimiento.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** local retrobulbar o peribulbar; general en casos seleccionados.
- **Duración aproximada:** 45 a 75 minutos.
- **Instrumental clave:** equipo básico de oftalmología, tijeras Westcott y Stevens, pinzas Bishop con y sin garra, porta agujas Castroviejo, calibrador para el tubo.
- **Suturas:** seda 6/0 para músculo y esclera, seda o vicryl 7/0 para conjuntiva y fijación del tubo.
- **Equipo biomédico:** microscopio quirúrgico, electrocauterio o bipolar.

### Concepto e indicaciones
Los implantes de drenaje del humor acuoso (válvula de Ahmed, Baerveldt y similares) constan de una placa de silicona que se fija a la esclera en el ecuador y un tubo fino que se introduce en la cámara anterior para derivar el acuoso hacia la placa, donde se forma una cápsula filtrante. Los modelos valvulados regulan el flujo y reducen la hipotonía temprana; los no valvulados requieren ligadura temporal del tubo. Se indican en glaucoma refractario, neovascular, post-quirúrgico fallido, traumático y en ojos con conjuntiva cicatrizada donde la trabeculectomía no es viable. La selección del modelo y del cuadrante (habitualmente supero-temporal) la define el cirujano según la anatomía y las cirugías previas.

### Anatomía aplicada y puntos críticos
El tubo debe entrar a la cámara anterior por delante del iris y por detrás de la córnea, paralelo al plano del iris, sin tocar el endotelio corneal ni el cristalino; por eso el instrumentador conoce la profundidad de la cámara y ofrece el calibrador para cortar el tubo a la medida exacta. La placa se aloja entre los músculos rectos a 8 o 10 mm del limbo, bajo la Tenon, y el tubo se cubre con parche escleral o pericárdico donante para evitar su exposición. Cada estructura que el tubo roza (endotelio, iris, cristalino) es una complicación potencial que el instrumentador ayuda a prevenir con una presentación ordenada de los componentes.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** equipo básico de oftalmología, tijeras Westcott y Stevens, pinzas Bishop con y sin garra, pinza de disección fina, porta agujas Castroviejo, gancho de estrabismo para reparar músculos.
- **Dispositivos y material:** implante de drenaje verificado (placa y tubo íntegros), parche escleral o pericárdico si se usa, gasas, hisopos, solución salina balanceada, hojas 15 y aguja de acceso a cámara.
- **Suturas:** seda 6/0 para fijación de la placa y reparos musculares, seda o vicryl 7/0 para tubo y conjuntiva.
- **Medicamentos:** anestésico local, antibiótico y antiinflamatorio para el final, isodine para antisepsia.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, vestimenta estéril y mesas acomodadas por tiempos; verificación del implante (placa y tubo íntegros) antes de anestesiar.
2. Antisepsia, campos y cierre del circuito estéril; blefaróstato y lavado de fondos de saco.
3. Peritomía conjuntival amplia en el cuadrante elegido con tijeras Westcott y disección de la Tenon.
4. Reparación de los músculos rectos adyacentes con seda para exponer el ecuador escleral.
5. Fijación de la placa a la esclera a 8 o 10 mm del limbo con seda 6/0, verificando que asiente plana.
6. Preparación del tubo: purga o ligadura según el modelo y corte a la medida con el calibrador.
7. Paracentesis auxiliar y entrada del tubo a la cámara anterior paralelo al iris, sin tocar endotelio ni cristalino.
8. Cobertura del tubo con parche escleral o pericárdico y fijación con sutura.
9. Cierre de Tenon y conjuntiva con vicryl o seda 7/0, verificando que el tubo quede totalmente cubierto.
10. Antibiótico y antiinflamatorio, apósito oclusivo y fin del procedimiento.

### Complicaciones y respuesta del instrumentador
- **Hipotonía temprana o hipertensión tardía:** tener disponible material de revisión y midriáticos o hipotensores según la fase.
- **Exposición o migración del tubo:** urgencia; se prepara set de revisión con parche nuevo y suturas finas.
- **Bloqueo del tubo por vítreo, sangre o iris:** ofrecer cánula de irrigación y viscoelástico para reposicionar.
- **Diplopía, hemorragia y endoftalmitis:** vigilancia posoperatoria dirigida a cada una.

### Manejo posoperatorio
Oclusión inicial, antibióticos y esteroides tópicos en pauta descendente, reposo relativo y protección contra golpes. El instrumentador advierte que la visión fluctuará mientras la presión se estabiliza, que el ojo puede verse enrojecido varias semanas y que todo dolor intenso, pérdida visual brusca o exposición visible del tubo obliga a consulta inmediata.

### ⚠️ Alertas y perlas del instrumentador
- **Verifica el implante antes de anestesiar:** placa fisurada o tubo obstruido se detectan fuera del campo, nunca con el ojo abierto.
- **El tubo se corta una sola vez:** confirma la medida con el cirujano antes de cortar; un tubo corto no se alarga.
- **Cobertura total del tubo:** ningún milímetro de tubo queda expuesto bajo la conjuntiva; prepara parche de reserva.
- **Ligadura según modelo:** pregunta si el implante es valvulado o no antes de iniciar, porque cambia el montaje.

### Términos clave
- **Implante de drenaje:** dispositivo placa-tubo que deriva el humor acuoso al ecuador.
- **Válvula de Ahmed:** implante valvulado que regula el flujo y reduce la hipotonía temprana.
- **Ecuador:** zona media del globo donde se fija la placa del implante.
- **Parche:** injerto escleral o pericárdico que cubre el tubo para evitar su exposición.
- **Glaucoma refractario:** glaucoma no controlado con fármacos, láser ni cirugía filtrante previa.
- **Cápsula filtrante:** tejido que se forma alrededor de la placa y regula la absorción del acuoso.""",
            },
            {
                "name": 'Iridectomía con Láser',
                "content": """### Introducción
La iridectomía con láser abre un orificio microscópico en el iris para igualar la presión entre la cámara posterior y la anterior, y se realiza sentando al paciente en la lámpara de hendidura, sin bisturí ni suturas. El instrumentador prepara el láser, el lente de contacto y las gotas en secuencia exacta, porque el procedimiento dura minutos y no admite improvisación: miosis previa, energía calibrada y verificación de permeabilidad.

### Ficha técnica rápida
- **Posición:** sentado frente a la lámpara de hendidura, mentón y frente apoyados.
- **Anestesia:** tópica con Alcaine u otro anestésico de superficie.
- **Duración aproximada:** 5 a 15 minutos por ojo.
- **Instrumental clave:** lente de contacto para iridotomía (Abraham o Goldmann), jeringa de gotas, gasas.
- **Suturas:** no requiere.
- **Equipo biomédico:** láser YAG o consola infrarroja Iridex IQ 810 para procedimientos de glaucoma, lámpara de hendidura acoplada.

### Concepto e indicaciones
La iridectomía periférica con láser (iridotomía) crea una comunicación directa entre la cámara posterior y la anterior a través del iris periférico, eliminando el bloqueo pupilar que cierra el ángulo iridocorneal y eleva la presión. Se indica en glaucoma de ángulo estrecho o cerrado, como profilaxis del ojo contralateral tras una crisis aguda, y en iris en meseta o bloqueo pupilar por diversas causas. Es un procedimiento ambulatorio de bajo riesgo que muchas veces evita o pospone la cirugía filtrante, y su éxito se confirma viendo transiluminación y flujo a través del orificio creado.

### Anatomía aplicada y puntos críticos
El iris divide la cámara anterior de la posterior; cuando la pupila se adhiere al cristalino (bloqueo pupilar), el acuoso queda atrapado atrás, bombea el iris hacia adelante y cierra el ángulo donde está la malla trabecular. El disparo láser se dirige al iris periférico superior, habitualmente bajo el párpado para evitar diplopía por imagen fantasma, en una zona de cripta donde el iris es más delgado. El instrumentador coloca el lente de contacto con gel sobre la córnea para enfocar y estabilizar, y sabe que detrás del iris están el cristalino y la cápsula: la energía debe abrir iris sin lesionarlos.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** lente de contacto de Abraham o Goldmann, gasas, pañuelos, espejo de verificación.
- **Dispositivos y material:** gel oftálmico para el lente, gotas en orden de aplicación.
- **Medicamentos:** anestésico tópico, miótico (pilocarpina) previo para adelgazar y tensar el iris, hipotensor y esteroide tópico para después, apraclonidina o similar si el protocolo la incluye.

### Técnica quirúrgica paso a paso
1. Verificación de paciente, ojo e indicación; explicación del procedimiento y de los destellos que verá.
2. Aplicación de pilocarpina para miosis: el iris tenso y delgado se perfora con menos energía.
3. Anestesia tópica y colocación del lente de contacto con gel sobre la córnea.
4. Localización del cuadrante superior periférico en una cripta del iris.
5. Calibración del láser según el grosor del iris y aplicación de disparos hasta lograr la perforación completa.
6. Verificación de permeabilidad por transiluminación y observación de flujo de pigmento.
7. Retiro del lente, limpieza del gel e instilación de hipotensor y esteroide.
8. Medición de la presión intraocular a la hora y programación del control; indicación de profilaxis en el ojo contralateral cuando corresponda.

### Complicaciones y respuesta del instrumentador
- **Pico de presión intraocular:** el más frecuente en la primera hora; tener midriáticos a la mano y контролировать la presión antes del alta.
- **Hemorragia del iris:** leve y autolimitada; compresión con el lente y pausa antes de continuar.
- **Inflamación anterior y cierre del orificio:** esteroide tópico y verificación de permeabilidad en el control.
- **Lesión inadvertida de cristalino o córnea:** calibración cuidadosa de la energía y lente bien centrado.

### Manejo posoperatorio
Esteroides e hipotensores tópicos por pocos días, control de presión en 1 hora, 1 día y 1 semana, y educación sobre síntomas de crisis de ángulo (dolor ocular intenso, halos, náusea y visión borrosa) que obligan a urgencias. El instrumentador confirma que el paciente entendió las gotas y la cita antes de darle el alta.

### ⚠️ Alertas y perlas del instrumentador
- **Miosis primero:** sin pilocarpina previa el iris grueso exige más energía y más complicaciones.
- **Lente con gel suficiente:** un lente seco se mueve y desenfoca el disparo; aplica gel generoso.
- **Presión antes del alta:** ningún paciente se va sin control de presión a la hora del láser.
- **Ojo contralateral en agenda:** el ángulo estrecho suele ser bilateral; deja programada la profilaxis.

### Términos clave
- **Iridotomía:** orificio en el iris creado con láser para comunicar ambas cámaras.
- **Bloqueo pupilar:** atrapamiento del humor acuoso detrás del iris que cierra el ángulo.
- **Ángulo iridocorneal:** zona de drenaje del humor acuoso entre iris y córnea.
- **Miosis:** contracción pupilar que adelgaza el iris para el disparo láser.
- **Transiluminación:** paso de luz por el orificio que confirma su permeabilidad.
- **Glaucoma de ángulo cerrado:** crisis por cierre brusco del drenaje con presión muy alta.""",
            },
        ],
    },
    {
        "name": 'UNIDAD 4. Cirugías del segmento anterior',
        "description": 'Técnicas de microcirugía para el cristalino y la córnea.',
        "subtopics": [
            {
                "name": 'Facoemulsificación',
                "content": """### Introducción
La facoemulsificación es la técnica moderna de la catarata: fragmenta el cristalino opaco con ultrasonido por una incisión de poco más de 2 mm e implanta un lente plegable, con recuperación visual en días. Para el instrumentador es la cirugía del equipo: montar, purgar y calibrar el facoemulsificador, verificar el lente contra la biometría y anticipar viscoelástico, azul de tripán y cada cuchillete en su momento exacto.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** tópica con intracameral; sedación leve según el paciente.
- **Duración aproximada:** 15 a 30 minutos.
- **Instrumental clave:** cuchilletes de faco de 1.2 a 3.2 mm, cuchillete de implantación angulado de 5.2 mm y recto de 15 grados, pinza de capsulorrexis, manipulador o chopper, sistema de irrigación-aspiración, inyector de lente.
- **Suturas:** habitualmente no requiere por incisión autosellante; nylon 10/0 disponible si hay fuga.
- **Equipo biomédico:** facoemulsificador (Sovereign, Signature o Stellaris) purgado y calibrado, microscopio quirúrgico.

### Concepto e indicaciones
La facoemulsificación extrae el cristalino cataratoso emulsionándolo con ultrasonido y aspirando los fragmentos, para implantar un lente intraocular plegable en el saco capsular. Se indica en catarata con pérdida visual que limita la vida diaria, en catarata que compromete la salud ocular (glaucoma facolítico, retinopatía que exige ver el fondo) y por estética para recuperar la pupila negra. Frente a la técnica extracapsular manual, la faco ofrece incisión mínima, astigmatismo inducido casi nulo y rehabilitación inmediata, pero exige equipo funcional, midriasis amplia y un endotelio corneal sano que el instrumentador ayuda a proteger en cada paso.

### Anatomía aplicada y puntos críticos
El cristalino opaco está dentro del saco capsular: la capsulorrexis abre la cápsula anterior en un círculo continuo, la hidrodisección separa el núcleo de la corteza con líquido, y el saco con su cápsula posterior intacta recibirá el lente. La cámara anterior se mantiene formada con viscoelástico que protege el endotelio, la capa corneal más interna que no se regenera. El instrumentador ofrece el azul de tripán para teñir la cápsula anterior cuando la catarata es blanca y no se ve el borde, entrega el viscoelástico antes de cada entrada de instrumental y mantiene la irrigación continua para que la cámara nunca se colapse.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** cuchilletes de faco, pinza de capsulorrexis, chopper o manipulador, cánulas de irrigación-aspiración, inyector de lente intraocular, pinza 0.12.
- **Dispositivos y material:** equipo de venoclisis macro y micro para irrigación, jeringas de 3, 5 y 10 cc, jeringas de insulina, solución salina balanceada, microesponjas, hisopos, gasas.
- **Suturas:** nylon 10/0 montado como reserva para fugas de la incisión.
- **Medicamentos:** midriáticos (Mydriacyl y fenilefrina), anestésico tópico, viscoelástico (Healón o similar), azul de tripán, miótico (acetilcolina o pilocarpina) para el final, antibiótico intracameral según protocolo, ungüento y apósito.

### Técnica quirúrgica paso a paso
1. Verificación triple (paciente, ojo, lente contra la biometría) antes de abrir el lente; el lente solo se abre cuando su potencia está confirmada.
2. Midriasis máxima, anestesia tópica, antisepsia con yodopovidona y colocación de campo y blefaróstato.
3. Incisión principal con cuchillete de faco y paracentesis auxiliar con cuchillete de 15 grados.
4. Tinción de la cápsula anterior con azul de tripán si la catarata es blanca, y llenado de la cámara con viscoelástico.
5. Capsulorrexis circular continua con pinza dedicada, de unos 5 mm de diámetro.
6. Hidrodisección e hidrodelaminación para movilizar el núcleo dentro del saco.
7. Facoemulsificación del núcleo por cuadrantes con el handpiece, alternando ultrasonido e irrigación-aspiración.
8. Aspiración de los restos corticales con irrigación-aspiración hasta dejar el saco limpio.
9. Implante del lente intraocular plegable con el inyector y centrado con manipulador.
10. Aspiración del viscoelástico, hidratación de las incisiones para sellarlas y miótico para contraer la pupila.
11. Antibiótico, verificación de cámara formada y Seidel negativo, apósito y fin del procedimiento.

### Complicaciones y respuesta del instrumentador
- **Ruptura de cápsula posterior con pérdida vítrea:** la complicación clave; el instrumentador tiene listo el vitrector de segmento anterior y triamcinolona para visualizar el vítreo.
- **Lesión endotelial y edema corneal:** se previene con viscoelástico generoso y parámetros de ultrasonido moderados.
- **Prolapso de iris y fuga de incisión:** ofrecer miótico, viscoelástico y la sutura 10/0 de reserva.
- **Endoftalmitis:** asepsia total y antibiótico intracameral según protocolo.

### Manejo posoperatorio
Oclusión breve, gotas antibióticas con esteroide en pauta descendente por semanas, protección nocturna y control al día siguiente para medir presión y estado de la cámara. El instrumentador explica no frotarse, no cargar peso, usar gafas de sol y consultar por dolor intenso, enrojecimiento progresivo o pérdida visual súbita.

### ⚠️ Alertas y perlas del instrumentador
- **Biometría antes de abrir:** el lente se abre solo con potencia confirmada contra la biometría; un lente equivocado abierto es un lente perdido.
- **Viscoelástico antes de cada entrada:** ningún instrumento entra a la cámara sin viscoelástico previo que proteja el endotelio.
- **Purgar y probar el pedal:** el facoemulsificador se ceba y se prueba antes de la incisión; sin reflujo ni ultrasonido probados no se empieza.
- **Azul de tripán en catarata blanca:** sin tinción no hay borde visible de capsulorrexis; ofrécelo antes de que lo pidan.

### Términos clave
- **Facoemulsificación:** fragmentación del cristalino con ultrasonido y aspiración por incisión mínima.
- **Capsulorrexis:** apertura circular continua de la cápsula anterior del cristalino.
- **Hidrodisección:** separación del núcleo con líquido para movilizarlo dentro del saco.
- **Endotelio:** capa interna de la córnea que no se regenera y debe protegerse siempre.
- **Lente intraocular:** prótesis óptica que reemplaza al cristalino dentro del saco capsular.
- **Biometría:** medición preoperatoria que define la potencia del lente a implantar.""",
            },
            {
                "name": 'Extracción extracapsular',
                "content": """### Introducción
La extracción extracapsular del cristalino es la técnica manual de la catarata: sin ultrasonido, extrae el núcleo entero por una incisión amplia y conserva la cápsula posterior para el lente. Sigue vigente para cataratas duras, subluxadas o sin facoemulsificador disponible, y para el instrumentador es la escuela de la catarata clásica: rienda muscular, surco esclerocorneal, cistotomo de jeringa de insulina y cierre con nylon 10/0 punto por punto.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** bloqueo retrobulbar.
- **Duración aproximada:** 30 a 50 minutos.
- **Instrumental clave:** equipo de catarata, tijeras de Wescott, pinza Hartmann Bishop con y sin dientes, pinza de mosquito curva, hoja 15 y 11 en mango Bard Parker 3, asa de Lewis, gancho de estrabismo, pinza colibrí, pinza McPherson, gancho Sinskey, pinza Lester, tijera corneal.
- **Suturas:** seda 5/0 para control, vicryl 6/0 para rienda, nylon 10/0 para el cierre esclerocorneal.
- **Equipo biomédico:** microscopio quirúrgico, electrocauterio.

### Concepto e indicaciones
La extracción extracapsular consiste en extirpar el cristalino opaco junto con la cápsula anterior, dejando intacta la cápsula posterior para apoyar el lente intraocular en la cámara posterior; se realiza una capsulotomía anterior amplia para evitar opacidades en el posoperatorio. Sus indicaciones son la reducción de la agudeza visual por catarata, la catarata que afecta la salud ocular (glaucoma facolítico, retinopatía diabética que exige visualizar el fondo), la estética para recuperar la pupila negra y todos los casos donde la dureza del núcleo o la falta de equipo contraindican el faco. Las contraindicaciones incluyen el mal estado general del paciente y el desprendimiento de retina o de coroides asociado.

### Anatomía aplicada y puntos críticos
El núcleo cataratoso ocupa todo el saco capsular y sale entero por el surco esclerocorneal; la cápsula posterior que queda es el diafragma donde descansará el lente, por eso cada maniobra la respeta. La rienda del recto superior con vicryl 6/0 fija el globo para trabajar la incisión superior de 180 grados, y la cámara se reforma con Healón antes de cada tiempo intraocular. El instrumentador entrega el cistotomo (aguja de insulina adaptada en jeringa) para la capsulotomía, el asa de Lewis con el gancho de estrabismo para luxar el núcleo y la cánula de doble vía para la irrigación-succión de restos corticales.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** equipo de catarata, mango Bard Parker 3 con hojas 15 y 11, tijeras de Wescott, pinzas Hartmann Bishop con y sin dientes, pinza de mosquito curva, asa de Lewis, gancho de estrabismo, pinza colibrí, pinza McPherson, gancho Sinskey, pinza Lester, tijera corneal, cánula oftálmica y de doble vía.
- **Dispositivos y material:** solución Hartmann y salina balanceada, jeringas de 5 y 3 cc, jeringas de insulina, equipo de venoclisis purgado, electrocauterio, hisopos húmedos peinados, gasas, microesponjas, agujas 20 y 25, micropore, lente intraocular en su estuche.
- **Suturas:** seda 5/0 para control, vicryl 6/0 cortado para la rienda del recto superior, nylon 10/0 cortado a la mitad para el cierre.
- **Medicamentos:** anestésico para el bloqueo, Healón, mezcla subconjuntival final de amicacina con dexametasona y xilocaína al 2% en jeringa de insulina.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, bata y guantes con técnica cerrada; mesas vestidas e instrumental acomodado por tiempos.
2. Antisepsia de la región con torundas e isodine, lavado de guantes, colocación de campos y cierre del circuito estéril.
3. Separación de párpados con blefaróstato y gasa, y aseo de pestañas y fondos de saco con Hartmann y cánula oftálmica.
4. Rienda del recto superior con vicryl 6/0 montado en Castroviejo, fijada al campo con pinza de mosquito; peritomía superior perilímbica de 180 grados.
5. Hemostasia con cauterio y surco esclerocorneal con hoja 15 en mango Bard Parker 3.
6. Paracentesis con aguja de insulina, ampliación con hoja 11, reformación de cámara con Healón y capsulotomía con el cistotomo.
7. Hidrodisección con Hartmann, rotación del núcleo con tijera corneal y pinza colibrí, ampliación de la incisión y luxación-extracción del núcleo con asa de Lewis y gancho.
8. Presutura con 2 puntos de nylon 10/0 a cada lado de la herida y extracción de restos corticales con irrigación-succión.
9. Implante del lente en cámara posterior con pinzas McPherson y colibrí, rotación y acomodo con gancho Sinskey, y cierre completo con nylon 10/0.
10. Corte de la rienda con tijera Wescott, infiltración subconjuntival de amicacina con dexametasona y xilocaína, limpieza del isodine y apósito monocular oclusivo con micropore.

### Complicaciones y respuesta del instrumentador
- **Ruptura de cápsula posterior y pérdida vítrea:** ofrecer vitrector de segmento anterior y viscoelástico de inmediato.
- **Hemorragia expulsiva:** urgencia extrema; campo cerrado, hipotensores y sutura rápida según orden médica.
- **Luxación del núcleo a vítreo:** se convierte en caso vitreorretinal; tener listo el set de vitrectomía posterior.
- **Infección y dehiscencia del cierre:** conteo de puntos, nudos seguros y antibiótico final.

### Manejo posoperatorio
Apósito oclusivo inicial, antibióticos con esteroides en pauta descendente, control de presión al día siguiente y retiro selectivo de puntos de nylon según el astigmatismo. El instrumentador refuerza no frotarse, dormir con protector, evitar esfuerzos y consultar por dolor, secreción o baja visual brusca.

### ⚠️ Alertas y perlas del instrumentador
- **Córnea siempre irrigada:** durante todo el procedimiento ofrece hisopos húmedos peinados y Hartmann en jeringa de 10 ml con cánula; la observación del manual es innegociable.
- **Nylon cortado a la mitad:** el 10/0 se corta para el cierre y se monta en porta agujas fino con pinza colibrí; prepara varios montados.
- **Lente localizado antes de abrir:** el LIO viaja en su estuche con una gota de agua para ubicarlo; se toma con McPherson sin tocar la óptica.
- **Riendas bajo control:** la rienda del recto superior se corta y retira con mosquito al final; confirma que no quede tracción.

### Términos clave
- **Extracción extracapsular:** extracción manual del núcleo conservando la cápsula posterior.
- **Cistotomo:** aguja adaptada para abrir la cápsula anterior del cristalino.
- **Hidrodisección:** inyección de líquido que separa el núcleo de la corteza.
- **Surco esclerocorneal:** incisión en la unión córnea-esclera para extraer el núcleo entero.
- **Asa de Lewis:** instrumento para luxar y extraer el núcleo del cristalino.
- **Cámara posterior:** espacio detrás del iris donde se apoya el lente intraocular.""",
            },
            {
                "name": 'Trasplante de córnea',
                "content": """### Introducción
El trasplante de córnea reemplaza el tejido corneal enfermo por un botón donante sano y devuelve la visión a ojos con queratocono, leucomas o traumas. Para el instrumentador es la cirugía de la precisión circular: trépanos del calibre exacto, injerto mantenido húmedo con el endotelio protegido y sutura continua con nylon 10/0. Aquí el tejido donante es irreemplazable y cada gesto lo cuida.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** general.
- **Duración aproximada:** 45 a 90 minutos.
- **Instrumental clave:** juego de anillos de Flieringa, juego de trépanos de 7, 7.5, 8 y 8.5 mm, trépano de Troutman y de succión, tijeras corneales derecha e izquierda, tijeras Vannas y Stevens recta, pinzas 0.12 (2 unidades), pinzas Jaffe para hilos, porta agujas fino.
- **Suturas:** nylon 10/0 para el injerto; seda 9/0 para fijación provisional; seda 4/0 para anillo y músculo.
- **Equipo biomédico:** microscopio quirúrgico.

### Concepto e indicaciones
La queratoplastia penetrante, también llamada trasplante de córnea, sustituye el espesor total de la córnea anormal del receptor por tejido corneal sano del donante, con el objetivo de que el tejido sea aceptado al máximo. Sus causas incluyen traumatismos, defectos congénitos, heridas corneales, queratocono, leucomas congénitos, degeneración y distrofias corneales. El éxito depende de tres factores que el instrumentador controla en parte: el calibre exacto del trépano (el botón donante debe calzar perfecto en el lecho receptor), la protección del endotelio donante con viscoelástico y humedad permanente, y una sutura hermética y simétrica que evite astigmatismos altos y filtraciones.

### Anatomía aplicada y puntos críticos
La córnea receptora se trepana en un botón circular de 7.5 a 8.5 mm de diámetro que incluye todo su espesor; el anillo de Flieringa suturado a la esclera fija el globo e impide su colapso al abrir la cámara. El botón donante se corta sobre el bloque de teflón con el trépano correspondiente y se manipula solo por el borde con pinza 0.12, con el lado endotelial hacia arriba cubierto de viscoelástico. La iridectomía periférica previa evita el bloqueo pupilar posoperatorio. El instrumentador guarda el tejido trepanado del receptor como muestra, mantiene el injerto tapado con el recipiente de cristal y ofrece las tijeras corneales derecha e izquierda según el lado del corte.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** blefaróstato, juego de anillos de Flieringa, juego de trépanos, trépano de Troutman y de succión, tijeras corneales derecha e izquierda, tijeras Vannas y Stevens recta, pinzas 0.12, pinzas Jaffe, porta agujas fino y Castroviejo, recipiente de cristal.
- **Dispositivos y material:** córnea donante verificada con su documentación, Healón o viscoelástico, solución salina balanceada en jeringa de 3 cc con cánula 27, aire en jeringa de 3 cc, gasas 10x10, jeringas de 10 ml y de insulina, agujas 20 y 22, micropore.
- **Suturas:** nylon 10/0 para la sutura continua del injerto, seda 9/0 para la fijación provisional de 8 puntos, seda 4/0 para anillo y fijaciones.
- **Medicamentos:** anestésicos generales según anestesiología, antibiótico tópico (cloranfenicol en gotas), midriáticos si se indican.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, vestimenta estéril y mesas por tiempos; verificación de la córnea donante y su documentación de trazabilidad.
2. Preparación del tejido donante: pinza 0.12 y trépano del calibre indicado sobre el bloque de teflón, viscoelástico encima con el endotelio hacia arriba y reserva tapada con el recipiente de cristal.
3. Apertura palpebral con blefaróstato y fijación ocular con anillo de Flieringa en porta agujas con seda.
4. Trepanación corneal superficial del receptor de 7.5 a 8.5 mm con trépano de Troutman.
5. Corte completo con tijeras corneales derecha e izquierda; el tejido trepanado se guarda como muestra.
6. Iridectomía periférica y colocación del injerto donante con pinzas 0.12.
7. Fijación provisional con 8 puntos separados de seda 9/0.
8. Sutura continua del injerto con nylon 10/0 en porta agujas fino, con pinzas 0.12 y Jaffe y tijeras Stevens recta.
9. Reformación de la cámara anterior con solución salina balanceada y aire con cánula 27.
10. Limpieza del área, antibiótico tópico y oclusión con gasa y micropore.

### Complicaciones y respuesta del instrumentador
- **Rechazo del trasplante:** el riesgo mayor; se previene con trazabilidad, asepsia y medicación inmunosupresora tópica indicada.
- **Hemorragia e infección:** hemostasia rigurosa y campo estéril permanente; todo material que toca el injerto es de un solo uso por tiempo.
- **Filtración por la sutura y astigmatismo alto:** sutura simétrica y verificación de hermetismo antes del parche.
- **Pérdida endotelial:** manipulación mínima del botón y viscoelástico constante.

### Manejo posoperatorio
Reposo absoluto inicial evitando golpes y esfuerzos, apósito oclusivo por 24 a 48 horas según indicación, antiinflamatorios y antibioterapia tópica prolongada, y controles frecuentes para detectar signos de rechazo (enrojecimiento, dolor, baja visual, edema del injerto). El instrumentador explica que el rechazo puede aparecer meses después y que cualquier síntoma obliga a consulta inmediata sin automedicarse.

### ⚠️ Alertas y perlas del instrumentador
- **Donante verificado por escrito:** confirma identidad del tejido, vigencia y serologías antes de anestesiar; sin papeles no hay trasplante.
- **Endotelio hacia arriba y húmedo:** el botón donante nunca se seca ni se apoya por su cara endotelial; viscoelástico y recipiente siempre.
- **Trépano exacto:** el calibre lo define el cirujano según el lecho; ten el juego completo de 7 a 8.5 mm en la mesa.
- **Muestra del receptor:** el botón enfermo se guarda y rotula para patología; prepara el frasco desde el inicio.

### Términos clave
- **Queratoplastia penetrante:** trasplante de espesor total de la córnea.
- **Botón corneal:** disco circular de córnea del donante o del receptor.
- **Anillo de Flieringa:** anillo escleral que fija el globo e impide su colapso.
- **Endotelio:** capa interna de la córnea, irremplazable y vital para la transparencia del injerto.
- **Rechazo:** respuesta inmune contra el tejido donante que puede opacarlo.
- **Trazabilidad:** documentación completa del origen y manejo del tejido donante.""",
            },
        ],
    },
    {
        "name": 'UNIDAD 5. Cirugías vitreorretinales',
        "description": 'Procedimientos sobre el vítreo y la retina, con énfasis en equipos y seguridad intraocular.',
        "subtopics": [
            {
                "name": 'Vitrectomías del segmento anterior y posterior',
                "content": """### Introducción
La vitrectomía extrae el humor vítreo opaco o traccionante y lo reemplaza con solución, gas o aceite de silicona para salvar la retina y la visión. Es la cirugía de los equipos: vitrector, endoiluminación, endoláser y líneas de infusión que el instrumentador monta, purga y vigila sin parpadear, porque una infusión cerrada colapsa el globo en segundos. Este subtema cubre la vitrectomía posterior y sus principios aplicables al segmento anterior.

### Ficha técnica rápida
- **Posición:** decúbito dorsal.
- **Anestesia:** general.
- **Duración aproximada:** 45 a 120 minutos según la complejidad.
- **Instrumental clave:** blefaróstato, tijeras Wescott, compás Castroviejo, cánula de perfusión larga o mediana, estilete para vitrectomía, cortador vítreo, sonda de endoiluminación calibre 20, sonda de endoláser calibre 20, lente de contacto, cuchillete lanceta MVR para esclerotomías, porta agujas fino.
- **Suturas:** vicryl 7/0 para el cierre de esclerotomías.
- **Equipo biomédico:** vitrector con fuente de iluminación, microscopio con pedal, aparato de endoláser de diodos, electrocauterio; facoemulsificador Stellaris apto para vitrectomía anterior y posterior.

### Concepto e indicaciones
La vitrectomía posterior es un procedimiento microquirúrgico diseñado para extraer opacidades del humor vítreo y eliminar sus tracciones sobre la retina, mejorando la visión y evitando la hemorragia vítrea. Su indicación más común es la hemorragia del vítreo por retinopatía diabética proliferativa, seguida del desprendimiento de retina traccional, regmatógeno y mixto, y la neovascularización del segmento anterior con opacidad del posterior. Las contraindicaciones incluyen la ausencia total de percepción de luz e infecciones activas palpebrales, corneales o conjuntivales. La vitrectomía del segmento anterior sigue los mismos principios en la cámara anterior y el vítreo prolapsado, típicamente durante una complicación de catarata.

### Anatomía aplicada y puntos críticos
El vítreo ocupa la cavidad posterior entre el cristalino y la retina, adherido con fuerza en la base vítrea, la ora serrata, la mácula y el nervio óptico; esas adherencias explican los desgarros cuando el vítreo tracciona. Las esclerotomías se practican en la pars plana a 3.5 mm del limbo (posiciones horarias 10 y 2, más la infusión inferotemporal), y la cánula de infusión conectada a solución salina balanceada mantiene el tono ocular mientras el cortador aspira. El instrumentador verifica que la llave de paso de la infusión esté totalmente abierta antes de que el cortador entre al ojo, porque sin infusión el globo se colapsa con la primera aspiración.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** blefaróstato, tijeras Wescott, compás Castroviejo, estilete para vitrectomía, cánula de perfusión con su equipo de venoclisis, cortador vítreo, sonda de endoiluminación 20G, sonda de endoláser 20G, lente de contacto, cuchillete lanceta MVR, porta agujas fino, equipo de catarata como apoyo.
- **Dispositivos y material:** hoja de bisturí 15, solución salina balanceada en volumen suficiente, equipo de venoclisis, gasas, metilcelulosa al 2% como lubricante de la lente, taponadores según el caso (aceite de silicona RS Oil 1000 o 5000, gases SF6, C2F6 o C3F8, perfluorocarbonos HPF-10 intraoperatorios).
- **Suturas:** vicryl 7/0 para esclerotomías y conjuntiva.
- **Medicamentos:** anestésicos generales, antibiótico y antiinflamatorio para el final.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, vestimenta estéril y mesas por tiempos; montaje y purga del vitrector, la infusión y el endoláser con prueba de pedal.
2. Apertura palpebral con blefaróstato e incisión conjuntival con mango de bisturí 15 y tijeras Wescott.
3. Marcación con compás Castroviejo y dos esclerotomías con estilete en las posiciones de las 10 y las 2.
4. Colocación de la cánula de infusión en la esclera a 3.5 mm por detrás del limbo, conectada al equipo con solución salina balanceada y llave totalmente abierta.
5. Colocación de la lente de contacto sobre la córnea con metilcelulosa al 2% como lubricante y enfoque del microscopio.
6. Inserción del cortador vítreo y la sonda de endoiluminación por las esclerotomías bajo visión de la lente.
7. Extracción del vítreo central y de todas las opacidades, reemplazando lo extraído con solución salina balanceada.
8. Endofotocoagulación con la sonda de endoláser calibre 20 cuando hay neovasos que eliminar o sellar.
9. Intercambio por el taponador indicado (aire, gas expansible o aceite de silicona) según el caso.
10. Cierre de las esclerotomías con vicryl 7/0 en porta agujas fino, parche ocular y fin del procedimiento.

### Complicaciones y respuesta del instrumentador
- **Hemorragia intraoperatoria:** elevar la infusión según orden médica y ofrecer endoláser o cauterio de inmediato.
- **Desgarro retiniano iatrogénico:** tener disponible criocoagulador o endoláser y taponador para sellarlo en el acto.
- **Hipotonía por fuga de esclerotomías:** verificar el sellado de cada puerto y ofrecer sutura adicional.
- **Aumento de presión por gas expansible:** confirmar el gas y la concentración correctos; el paciente no debe volar ni recibir óxido nitroso con gas intraocular.

### Manejo posoperatorio
Parche inicial, antibióticos con esteroides, analgesia y posicionamiento cefálico estricto cuando hay gas o aceite (boca abajo según indicación) para que el taponador comprima la zona tratada. El instrumentador explica la importancia del posicionamiento, la prohibición de vuelos y de buceo con gas intraocular, y los signos de alarma: dolor intenso, pérdida visual súbita, destellos nuevos o cortina visual.

### ⚠️ Alertas y perlas del instrumentador
- **Infusión abierta antes del cortador:** la llave de paso totalmente abierta es la regla de oro; verifícala en voz alta con el cirujano.
- **Gas correcto y anotado:** confirma tipo y concentración del gas y regístralo; un gas equivocado ciega por hiperpresión.
- **Lente con metilcelulosa:** sin lubricante la lente de contacto raya la córnea y pierde visión; aplica el 2% generoso.
- **Aceite y gas no se mezclan:** pregunta desde el inicio cuál taponador usará el cirujano y ten solo ese en el campo.

### Términos clave
- **Vitrectomía:** extracción microquirúrgica del humor vítreo y sus opacidades.
- **Esclerotomía:** puerto escleral en pars plana para el cortador, la luz y la infusión.
- **Endoiluminación:** fibra óptica intraocular que ilumina la cavidad vítrea.
- **Endofotocoagulación:** aplicación de láser dentro del ojo para sellar o destruir tejido.
- **Taponador:** gas expansible o aceite de silicona que mantiene la retina aplicada.
- **Perfluorocarbono:** líquido pesado intraoperatorio que aplana la retina desprendida.""",
            },
            {
                "name": 'Retinopatía simple',
                "content": """### Introducción
La retinopatía simple agrupa el desprendimiento regmatógeno de la retina y su tratamiento clásico: cerclaje escleral con banda de silicona, criopexia y drenaje del líquido subretiniano. Para el instrumentador es la cirugía del montaje externo: bandas, mersilene y oftalmoscopio indirecto listos antes de que el cirujano localice el desgarro, porque una vez identificada la rotura todo ocurre rápido y no hay pausa para buscar material.

### Ficha técnica rápida
- **Posición:** decúbito dorsal con leve Trendelenburg invertido.
- **Anestesia:** general.
- **Duración aproximada:** 60 a 120 minutos.
- **Instrumental clave:** equipo de retina, ganchos de Jameson, tijeras Wescott y Stevens, pinzas de disección con y sin dientes, pinza de joyero, mango Bard Parker 3 con hoja 15, tenómetro, oftalmoscopio indirecto con lámpara frontal y lupa.
- **Suturas:** seda atraumática 4/0, mersilene 5/0 para la banda, vicryl 7/0 con aguja micropoint para esclera y conjuntiva.
- **Equipo biomédico:** electrocauterio, criocoagulador para criopexia, láser Iridex IQ 810 para fotocoagulación cuando se indica.

### Concepto e indicaciones
El desprendimiento de retina es la separación de la retina de la coroides. El desprendimiento simple o regmatógeno se debe a un orificio en la retina por donde pasa líquido del vítreo y la separa de su lecho; el secundario ocurre cuando la retina es rechazada mecánicamente por contracción de tejido fibroso y del vítreo. El objetivo quirúrgico es devolver la retina a su posición mediante cerclaje (banda que indenta la esclera), criopexia (frío que adhiere) y drenaje del líquido subretiniano, esperando buena evolución y mejoría visual. Se indica ante desgarros sintomáticos con destellos, moscas volantes y cortina visual, y su pronóstico depende de operar antes de que se desprenda la mácula.

### Anatomía aplicada y puntos críticos
La retina se nutre de la coroides que tiene debajo; al desprenderse pierde nutrición y muere en días, por eso la cirugía es urgente. El líquido subretiniano se acumula entre ambas y se drena perforando la esclera en el punto marcado. La banda de silastic (números 40 y 240) rodea el globo a la altura del ecuador y se fija con mersilene 5/0 para indentar la pared contra el desgarro. El instrumentador pasa la banda por debajo de los músculos rectos previamente reparados con seda, ofrece el tenómetro para medir la presión tras ajustar la banda y tiene lista la aguja micropoint de vicryl 7/0 para la perforación de drenaje.

### Lista de chequeo – Mesa de Mayo
- **Instrumental:** equipo de retina, equipo de asepsia, ganchos de Jameson, tijeras Wescott y Stevens, pinzas de disección con y sin dientes, pinza de joyero, pinzas Halsted, mango Bard Parker 3 con hoja 15, tenómetro, oftalmoscopio indirecto.
- **Dispositivos y material:** bandas de silastic 40 y 240 verificadas, jeringas de 20, 10 y 3 cc, agujas 20 y 25, gasas 10x10, solución salina balanceada, micropore, ropa A y B.
- **Suturas:** seda atraumática 4/0 para fijación palpebral y controles, mersilene 5/0 para la banda, vicryl 7/0 para esclera y conjuntiva, seda libre del 0 para reparar músculos.
- **Medicamentos:** dexametasona 0.5 ml y gentamicina 0.5 ml para el piso de la órbita, cloranfenicol en gotas, anestésicos generales.

### Técnica quirúrgica paso a paso
1. Lavado quirúrgico, vestimenta estéril y mesas por tiempos; verificación de bandas, suturas y oftalmoscopio antes de anestesiar.
2. Fijación de párpados superior e inferior con seda 4/0 y lavado del fondo de saco con solución salina balanceada.
3. Incisión y perilimbotomía en 360 grados con tijera Wescott y disección conjuntival con Stevens.
4. Localización de los músculos rectos con ganchos de Jameson y reparación con seda libre del 0.
5. Localización del desgarro con oftalmoscopia indirecta, lámpara frontal y lupa.
6. Paso de la banda de silastic 240 por debajo de los músculos rectos con pinza de joyero.
7. Fijación de la banda en el ecuador con mersilene 5/0 en Castroviejo y corte de cabos; medición de la presión con el tenómetro.
8. Marcación del sitio de drenaje con hoja 15 y perforación de la esclera con aguja micropoint de vicryl 7/0 para drenar el líquido subretiniano.
9. Reajuste de la banda, corte del sobrante con tijera de iris y sutura de conjuntiva con vicryl 7/0.
10. Aplicación de gentamicina con dexametasona en el piso de la órbita, limpieza del área, gotas de cloranfenicol y apósito con gasa doblada y micropore.

### Complicaciones y respuesta del instrumentador
- **Rechazo o extrusión de la banda de silastic:** vigilar en controles y tener set de revisión con banda nueva.
- **Infección y dehiscencia de la herida:** asepsia estricta y cierre conjuntival hermético con vicryl 7/0.
- **Hipertensión ocular por cerclaje apretado:** tenómetro disponible y midriáticos o hipotensores a la mano.
- **Redesprendimiento:** ante cortina visual nueva se reopera; prepara el mismo set completo.

### Manejo posoperatorio
Reposo absoluto inicial, antibioterapia, analgésicos y antieméticos, cambio de apósito según necesidad y posicionamiento indicado. El instrumentador explica que el ojo quedará rojo e inflamado semanas, que la visión mejora lentamente, y que destellos nuevos, aumento de moscas o cortina visual obligan a urgencias inmediatas.

### ⚠️ Alertas y perlas del instrumentador
- **Bandas verificadas antes de anestesiar:** la 240 y la 40 sin fisuras ni deformaciones; una banda rota a mitad del cerclaje no tiene reemplazo inmediato.
- **Seda del 0 para los músculos:** repara los cuatro rectos antes de pasar la banda; sin reparos no hay tracción segura del globo.
- **Tenómetro a la mano:** cada ajuste de la banda cambia la presión; mídelo antes del drenaje y después del cierre.
- **Drenaje con campo seco:** la perforación escleral sangra; ofrece la micropoint montada y gasas en el mismo movimiento.

### Términos clave
- **Desprendimiento regmatógeno:** separación de la retina por un orificio que deja pasar líquido del vítreo.
- **Cerclaje:** banda circular que indenta la esclera para aplicar la retina.
- **Criopexia:** adherencia de la retina mediante frío aplicado por fuera de la esclera.
- **Líquido subretiniano:** fluido acumulado entre la retina desprendida y la coroides.
- **Ecuador:** perímetro medio del globo donde se fija la banda del cerclaje.
- **Tenómetro:** instrumento que mide la presión intraocular durante la cirugía.""",
            },
        ],
    },
{'name': 'UNIDAD 6. Corrección de estrabismo',
     'description': 'Preparación e instrumentación de las técnicas de cirugía de estrabismo: '
                    'debilitamiento y refuerzo de los músculos extraoculares, con el instrumental, las '
                    'suturas y los cuidados que exige cada paso.',
     'subtopics': [{'name': 'Técnicas para Corrección de estrabismo',
                    'content': '### Introducción\n'
                               'La cirugía de estrabismo corrige el alineamiento incorrecto de los '
                               'ojos actuando directamente sobre los músculos extraoculares. Para el '
                               'instrumentador es una cirugía de mediciones milimétricas: el cirujano '
                               'mide con compás cuánto retrocede o reinserta cada músculo, y esa '
                               'precisión depende de recibir la sutura correcta montada en el porta '
                               'agujas exacto en el momento exacto. Esta subunidad resume el concepto, '
                               'las indicaciones, la mesa y la técnica completa descritas en el manual '
                               'de técnicas quirúrgicas.\n'
                               '\n'
                               '### Ficha técnica rápida\n'
                               '- **Posición:** decúbito dorsal.\n'
                               '- **Anestesia:** local.\n'
                               '- **Instrumental:** equipo de estrabismo, equipo básico de '
                               'oftalmología, cable de electrocauterio y cuchillo cabeza de bronce, '
                               'equipo de asepsia.\n'
                               '- **Ropa:** bulto de ropa A y B.\n'
                               '- **Material de consumo:** hoja de bisturí n.º 15, gasas 10x10, '
                               'jeringas desechables de 5 cm, agujas desechables 20 y 25, hisopos.\n'
                               '- **Suturas:** vicryl 6/0 y vicryl 7/0.\n'
                               '\n'
                               '### Concepto e indicaciones\n'
                               'El propósito de la cirugía de músculos es corregir el alineamiento '
                               'incorrecto de los ojos; su corrección mejora la estética y la visión. '
                               'Las técnicas para el tratamiento del estrabismo se agrupan en tres '
                               'grandes grupos: cirugía de **músculos horizontales**, cirugía de '
                               '**músculos verticales** y cirugía de **músculos oblicuos**.\n'
                               '\n'
                               'Dos maniobras básicas definen la cirugía de los rectos:\n'
                               '- **Resección del recto externo:** se extirpa una porción del músculo '
                               'y el extremo seccionado se vuelve a insertar en el punto original de '
                               'inserción (efecto de refuerzo).\n'
                               '- **Retroinserción del recto interno:** el músculo se secciona en su '
                               'sitio de inserción y luego se sutura en un punto más posterior (efecto '
                               'de debilitamiento).\n'
                               '\n'
                               '**Indicaciones:** endotropía no acomodativa; parálisis de los pares '
                               'craneales III, IV y VI; hiperfunción del oblicuo inferior derecho o '
                               'izquierdo; hiperfunción de oblicuos superiores.\n'
                               '\n'
                               '**Contraindicaciones:** mal estado general del paciente y '
                               'conjuntivitis.\n'
                               '\n'
                               '### Anatomía aplicada y puntos críticos\n'
                               'El globo ocular se mueve por seis músculos extraoculares: los rectos '
                               'superior, inferior, externo e interno, y los oblicuos superior e '
                               'inferior, inervados por los pares craneales III, IV y VI. Por ejemplo, '
                               'para mirar a la derecha se contraen el recto externo derecho y el '
                               'recto interno izquierdo, mientras se relajan sus antagonistas. Dos '
                               'planos condicionan el trabajo quirúrgico: la **conjuntiva**, que se '
                               'abre mediante peritomía, y la **cápsula de Tenón**, que se diseca '
                               'hasta visualizar el músculo. Los puntos críticos para el '
                               'instrumentador son la medición con compás de la distancia final de '
                               'inserción respecto al limbo y el manejo de las suturas de vicryl 6/0 '
                               '(músculo) y 7/0 (conjuntiva).\n'
                               '\n'
                               '### Lista de chequeo – Mesa de Mayo\n'
                               '- **Instrumental:** equipo de estrabismo, equipo básico de '
                               'oftalmología (incluye blefaróstato, tijeras de Wescott, pinzas Bishop '
                               'con y sin dientes, pinza de anillos, gancho de estrabismo, compás de '
                               'Castroviejo, porta agujas de Castroviejo), cable de electrocauterio y '
                               'cuchillo cabeza de bronce, equipo de asepsia (vaso de asepsia).\n'
                               '- **Ropa:** bulto de ropa A y B; campo al tercio, campo triangular, '
                               'sábana de pie, tres campos sencillos.\n'
                               '- **Material de consumo:** hoja de bisturí n.º 15, gasas 10x10, '
                               'jeringas desechables de 5 cm, jeringa desechable de 10 ml con solución '
                               'Hartmann y cánula oftálmica, agujas desechables 20 y 25, hisopos, '
                               'isodine solución, torundas de gasa, micropore, apósito.\n'
                               '- **Suturas:** vicryl 6/0 (doble armada para el músculo), vicryl 7/0 '
                               '(conjuntiva).\n'
                               '- **Medicamentos:** gotas de prednisolona, cloranfenicol en gotas y '
                               'ungüento.\n'
                               '\n'
                               '### Técnica quirúrgica paso a paso\n'
                               '1. Recepción del paciente en sala de quirófano y colocación en mesa '
                               'quirúrgica en posición de cúbito dorsal; inicio de la anestesia '
                               'local.\n'
                               '2. Lavado mecánico y quirúrgico de manos, bata estéril y guantes con '
                               'técnica cerrada; vestido de mesas de riñón y de Mayo y acomodo del '
                               'instrumental por tiempos quirúrgicos.\n'
                               '3. Antisepsia de la región operatoria: vaso de asepsia con isodine '
                               'solución, torunda de gasa y pinza de anillos.\n'
                               '4. Colocación de campos: campo al tercio y triangular, pinza de campo, '
                               'sábana de pie, tres campos sencillos y dos pinzas de campo; '
                               'delimitación del campo operatorio y cierre del circuito estéril.\n'
                               '5. Separación de párpados con blefaróstato y gasa doblada, '
                               'posicionando el separador en el ángulo externo del ojo.\n'
                               '6. Irrigación de la córnea con jeringa desechable de 10 ml con '
                               'solución Hartmann y cánula oftálmica.\n'
                               '7. Peritomía de base fornix del meridiano 1 al meridiano 5 con tijera '
                               'de Wescott, pinza Bishop con dientes e hisopo húmedo peinado; '
                               'disección de conjuntiva y Tenón hasta visualizar el músculo recto '
                               'externo.\n'
                               '8. Localización del recto externo desde su sitio de inserción con '
                               'gancho de estrabismo, tijera de Wescott y pinza Bishop con dientes.\n'
                               '9. Medición del retroimplante con compás de Castroviejo con graduación '
                               '5.5.\n'
                               '10. Retroimplante del recto externo a 9 mm del limbo con vicryl 6/0 en '
                               'porta agujas de Castroviejo y pinza Bishop sin dientes; corte de cabos '
                               'con tijera de Wescott.\n'
                               '11. Sutura de conjuntiva externa con puntos separados de vicryl 7/0 '
                               'montado en porta agujas de Castroviejo, y corte de cabos.\n'
                               '12. Peritomía del sector nasal (meridianos 7 a 11), disección de '
                               'conjuntiva liberando las adherencias fibrosas y secado del sangrado '
                               'con hisopo hasta visualizar el recto interno.\n'
                               '13. Tracción y liberación del recto interno con gancho de estrabismo; '
                               'reimplante y fijación a 5.5 mm del limbo con vicryl 6/0 doble armada '
                               'en porta agujas de Castroviejo y pinza Bishop con dientes; anudado y '
                               'corte de cabos.\n'
                               '14. Sutura conjuntival con puntos separados de vicryl 7/0; anudado y '
                               'corte de cabos; corte y retiro del vicryl de rienda.\n'
                               '15. Administración del medicamento separando digitalmente los '
                               'párpados: gotas de prednisolona, cloranfenicol en gotas y ungüento.\n'
                               '16. Limpieza y secado del exceso de isodine con gasa seca; colocación '
                               'y fijación del apósito con micropore.\n'
                               '17. Conclusión del acto quirúrgico, ruptura del circuito estéril, '
                               'cuidados posteriores del instrumental y entrega al servicio de CEyE; '
                               'preparación de la sala para el siguiente procedimiento.\n'
                               '\n'
                               '### Complicaciones\n'
                               '> [PENDIENTE CLAUDIA: el manual de técnicas quirúrgicas no lista '
                               'complicaciones para la cirugía de estrabismo (a diferencia de otras '
                               'secciones). ¿Cuáles complicaciones intra y posoperatorias deben '
                               'incluirse en el compendio?]\n'
                               '\n'
                               '### Manejo posoperatorio\n'
                               'El cierre del procedimiento incluye la instilación de prednisolona y '
                               'cloranfenicol (en gotas y ungüento), la limpieza del exceso de '
                               'antiséptico y la oclusión con apósito fijado con micropore. El '
                               'instrumental se entrega con sus cuidados posteriores al servicio de '
                               'CEyE.\n'
                               '\n'
                               '### Alertas y perlas del instrumentador\n'
                               '- **Córnea siempre irrigada:** durante todo el transoperatorio se '
                               'mantiene la córnea con solución Hartmann en jeringa de 10 ml con '
                               'cánulas oftálmicas.\n'
                               '- **Hisopos húmedos peinados:** se proporcionan de forma continua; el '
                               'sangrado se seca, no se frota.\n'
                               '- **Medición antes de suturar:** el compás de Castroviejo con '
                               'graduación 5.5 debe estar disponible antes de decidir la posición de '
                               'reimplante.\n'
                               '- **Dos vicryl preparados:** 6/0 (doble armada, para el músculo) y 7/0 '
                               '(para la conjuntiva) montadas en porta agujas de Castroviejo según el '
                               'paso.\n'
                               '\n'
                               '### Términos clave\n'
                               '- **Resección:** extirpación de una porción del músculo con '
                               'reinserción del extremo en el punto original.\n'
                               '- **Retroinserción (retroimplante):** sección del músculo en su '
                               'inserción y nueva sutura en un punto más posterior.\n'
                               '- **Peritomía de base fornix:** apertura de la conjuntiva en su base '
                               'para acceder al músculo.\n'
                               '- **Rienda:** sutura de tracción que se corta y retira al final del '
                               'procedimiento.\n'
                               '\n'
                               'Fuente: docs/Manual-de-tecnicas-quirurgicas-de-oftalmologia.pdf, págs. '
                               '13–16 (y p. 5 para la musculatura extraocular).'}]},
{'name': 'UNIDAD 7. Cirugía para corrección de patologías refractivas',
     'description': 'Criterios generales de valoración y opciones de corrección refractiva: '
                    'preparación del equipo láser, seguridad del paciente y cuidados posteriores.',
     'subtopics': [{'name': 'Miopía, Hipermetropía y Astigmatismo',
                    'content': '### Introducción\n'
                               'Los errores de refracción son la causa más frecuente de consulta '
                               'oftalmológica, y la cirugía refractiva ofrece una alternativa '
                               'quirúrgica a los lentes. Para el instrumentador es un procedimiento '
                               'distinto a las demás cirugías del compendio: el protagonista es el '
                               'sistema láser excimer, cuya calibración, programación y manipulación '
                               'dependen del equipo de sala. Esta subunidad presenta la cirugía '
                               'refractiva tipo LASIK según el manual de técnicas quirúrgicas: qué '
                               'corrige, a quiénes, con qué instrumental y cómo se desarrolla la '
                               'técnica.\n'
                               '\n'
                               '### Ficha técnica rápida\n'
                               '- **Posición:** decúbito dorsal.\n'
                               '- **Anestesia:** tópica (gotas de tetracaína, según la técnica).\n'
                               '- **Instrumental:** microquerátomo con platinas de 160 y 180 micras, '
                               'anillos corneales 8.5 y 9.5, marcador corneal, blefaróstato, equipo de '
                               'pterigión.\n'
                               '- **Material de consumo:** solución salina balanceada, solución de '
                               'yodopovidona, agua inyectable, esponjas oftálmicas, micropore de 1 '
                               'pulg y de ½ pulg, gasas.\n'
                               '- **Equipos y aparatos:** sistema láser excimer, aparato de solución '
                               'oftálmica.\n'
                               '\n'
                               '### Concepto e indicaciones\n'
                               'La cirugía refractiva con LASIK corrige errores visuales de refracción '
                               'mediante la aplicación quirúrgica del **láser excimer** directamente '
                               'sobre el estroma corneal. Como marco anatómico, la mayor parte de la '
                               'refracción ocurre en la córnea, que tiene una curvatura fija, y otra '
                               'parte se da en el cristalino, que cambia de forma para ajustar el '
                               'enfoque (al perderse esa capacidad de ajuste aparece la presbicia o '
                               'vista cansada).\n'
                               '\n'
                               '**Indicaciones:** pacientes de 20 a 50 años de edad con defecto visual '
                               'refractivo estable.\n'
                               '\n'
                               '**Refracciones corregibles según el manual:**\n'
                               '- Miopía de 2 a −12 dioptrías.\n'
                               '- Astigmatismo de 1 a 6 dioptrías.\n'
                               '- Hipermetropía de +1 a +5 dioptrías (en el manual aparece con errata '
                               'como "hipertropías").\n'
                               '\n'
                               '> [PENDIENTE CLAUDIA: las fuentes listan las refracciones corregibles '
                               'y el concepto general de refracción, pero no definen la fisiopatología '
                               'de cada ametropía (miopía, hipermetropía, astigmatismo). ¿Se agregan '
                               'esas definiciones al compendio y a partir de qué fuente?]\n'
                               '\n'
                               '**Contraindicaciones:** infecciones del segmento anterior, '
                               'desprendimiento de retina, glaucoma, queratocono, herpes simple, '
                               'vascularización corneal, diabetes, lactancia y embarazo.\n'
                               '\n'
                               '### Lista de chequeo – Mesa de Mayo\n'
                               '- **Instrumental:** microquerátomo con platinas de 160 y 180 micras '
                               '(según paquimetría del paciente), anillos corneales 8.5 y 9.5, '
                               'marcador corneal, blefaróstato, equipo de pterigión, espátula.\n'
                               '- **Dispositivos y material:** solución salina balanceada, '
                               'yodopovidona, agua inyectable, esponjas oftálmicas (húmedas y secas), '
                               'frascos de irrigación con cánula oftálmica calibre 27, micropore '
                               'estéril de 1 pulg y de ½ pulg, gasas para la oclusión.\n'
                               '- **Equipos biomédicos:** sistema láser excimer calibrado y programado '
                               'antes del acto quirúrgico, succionador oftálmico con pedales, aparato '
                               'de solución oftálmica.\n'
                               '\n'
                               '### Cuidados específicos de enfermería\n'
                               '**Preoperatorios:**\n'
                               '- 15 días antes de la cirugía, dejar de usar lentes de contacto '
                               'blandos; un mes antes si son duros.\n'
                               '- Verificar que el paciente ingrese al quirófano sin maquillaje y con '
                               'ropa gruesa térmica.\n'
                               '- Verificar que el paciente lleve los resultados de dos de los '
                               'estudios: queratometría, topografía corneal y paquimetría.\n'
                               '\n'
                               '**Posoperatorios:**\n'
                               '- Oclusión del ojo intervenido.\n'
                               '- Informar al paciente los síntomas que presentará: lagrimeo, '
                               'sensación de basura dentro del ojo y ardor.\n'
                               '\n'
                               '### Técnica quirúrgica paso a paso\n'
                               '1. Lavado mecánico y quirúrgico de manos, bata estéril y guantes con '
                               'técnica cerrada; vestido de mesas de riñón y de Mayo y acomodo del '
                               'instrumental por tiempos.\n'
                               '2. **Calibración y programación del sistema láser** antes del acto '
                               'quirúrgico, introduciendo los datos del paciente, tipos de '
                               'padecimientos y refracciones.\n'
                               '3. Aplicación de gotas de tetracaína oftálmica; fijación del párpado '
                               'superior con cinta de micropore estéril.\n'
                               '4. Colocación del separador ocular (blefaróstato).\n'
                               '5. Preparación de las platinas de 160 a 180 micras; el cirujano '
                               'verifica el centrado del láser.\n'
                               '6. Marcación corneal con el marcador impregnado en azul de metileno.\n'
                               '7. Colocación del anillo corneal 8.5 o 9.5 ensamblado al succionador '
                               'oftálmico y presión del pedal para la fijación del globo ocular.\n'
                               '8. Montaje del microquerátomo con la platina de 160 a 180 micras según '
                               'la paquimetría del paciente, ensamblado al anillo corneal, y '
                               'realización de la incisión corneal.\n'
                               '9. La enfermera retrae el párpado inferior, irriga con solución salina '
                               'balanceada y presiona el pedal del microquerátomo; también presiona '
                               'los pedales del succionador y del microquerátomo.\n'
                               '10. Retiro del succionador y del microquerátomo; se proporcionan '
                               'espátula y esponja oftálmica y el cirujano levanta el colgajo '
                               'corneal.\n'
                               '11. Verificación de las refracciones a corregir; la enfermera indica a '
                               'tiempo la aplicación del láser.\n'
                               '12. Colocación del rastreador láser e indicación del tiempo '
                               'transcurrido de aplicación; el cirujano aplica el láser excimer.\n'
                               '13. Preparación de esponja húmeda con solución salina balanceada y '
                               'frascos de irrigación con cánula oftálmica calibre 27; el cirujano '
                               'remueve el residuo de estroma y efectúa la recolocación del colgajo.\n'
                               '14. Se proporciona esponja oftálmica seca; el cirujano verifica la '
                               'posición del colgajo corneal y retira el blefaróstato.\n'
                               '15. Instilación de antibiótico y antiinflamatorio ocular y oclusión '
                               'con gasa.\n'
                               '\n'
                               '### Rol del instrumentador y alertas\n'
                               '- **Pedales:** en esta técnica el equipo de enfermería opera los '
                               'pedales del succionador y del microquerátomo; conocer su ubicación y '
                               'secuencia evita interrupciones del corte.\n'
                               '- **Programación previa:** el láser se calibra y programa con los '
                               'datos del paciente antes de iniciar; la enfermera además indica a '
                               'tiempo el momento de la aplicación del láser.\n'
                               '- **Platinas según paquimetría:** tener disponibles las platinas de '
                               '160 y 180 micras; la elección depende de la paquimetría del paciente.\n'
                               '- **Irrigación continua:** esponjas húmedas con solución salina '
                               'balanceada y frascos de irrigación con cánula calibre 27 listos '
                               'durante toda la aplicación.\n'
                               '\n'
                               '### Términos clave\n'
                               '- **Láser excimer:** sistema que aplica energía sobre el estroma '
                               'corneal para corregir la refracción.\n'
                               '- **Microquerátomo:** instrumento con platinas de 160 y 180 micras que '
                               'realiza el corte del colgajo corneal.\n'
                               '- **Paquimetría:** medición del espesor corneal que determina la '
                               'platina a usar.\n'
                               '- **Colgajo corneal:** capa de córnea que se levanta para aplicar el '
                               'láser y se recoloca al final.\n'
                               '\n'
                               'Fuente: docs/Manual-de-tecnicas-quirurgicas-de-oftalmologia.pdf, págs. '
                               '39–41 (marco de refracción: docs/GUIA TECNICAS QUIRURGICAS DE '
                               'OFTALMOLOGIA PARA ESTUDIANTES.docx, sección Anatomía y fisiología).'}]},
{'name': 'UNIDAD 8. Oculoplastia',
     'description': 'Preparación e instrumentación para la cirugía palpebral: anatomía aplicada de los '
                    'párpados, instrumental específico y técnica de referencia para los procedimientos '
                    'de esta región.',
     'subtopics': [{'name': 'Cirugía en Párpados',
                    'content': '### Introducción\n'
                               'La oculoplastia agrupa los procedimientos quirúrgicos de las '
                               'estructuras anexas del ojo, y los párpados son su escenario más '
                               'frecuente: son pliegues de piel, musculomucosos y móviles que protegen '
                               'el globo ocular, distribuyen las secreciones lubricantes y participan '
                               'en la producción y el drenaje de la lágrima. Operar un párpado exige '
                               'respetar su arquitectura por capas y controlar el sangrado en un '
                               'tejido muy vascularizado. Esta subunidad recoge la anatomía palpebral '
                               'aplicada y el procedimiento palpebral descrito en detalle en las '
                               'fuentes: el drenaje de chalazión, tomado como técnica de referencia de '
                               'la cirugía palpebral.\n'
                               '\n'
                               '### Ficha técnica rápida (procedimiento de referencia: chalazión)\n'
                               '- **Posición:** decúbito dorsal.\n'
                               '- **Anestesia:** local (infiltración del borde del párpado con '
                               'xilocaína al 2%).\n'
                               '- **Instrumental:** equipo de chalazión.\n'
                               '- **Ropa:** campo hendido; equipo C.\n'
                               '- **Material de consumo:** hoja de bisturí n.º 15, jeringa de 3 cc, '
                               'jeringa de insulina, agujas 20 y 22, hisopos, gasas, cloranfenicol '
                               'ungüento.\n'
                               '\n'
                               '### Anatomía palpebral aplicada\n'
                               'Los párpados son los pliegues cutáneos superior e inferior que cubren '
                               'los ojos durante el sueño, los protegen contra la luz excesiva y los '
                               'cuerpos extraños, y distribuyen secreciones lubricantes sobre los '
                               'globos oculares. El párpado superior, de mayor movilidad que el '
                               'inferior, comprende en su porción superior el músculo elevador del '
                               'párpado superior. El espacio entre ambos pliegues es la **hendidura '
                               'palpebral**, cuyos ángulos se llaman **canto externo** (más angosto, '
                               'cercano al temporal) y **canto interno** (más ancho, próximo a los '
                               'huesos nasales); en el canto interno se encuentra la carúncula '
                               'lagrimal, una eminencia rojiza con glándulas sebáceas y sudoríparas.\n'
                               '\n'
                               'De la parte superficial a la profunda, cada párpado consiste en: '
                               'epidermis, dermis, tejido subcutáneo, fibras del músculo orbicular de '
                               'los párpados, placa tarsal, glándulas tarsales y conjuntiva. La '
                               '**placa tarsal** (el tarso) es un pliegue grueso de tejido conectivo '
                               'que confiere forma y sostén al párpado. Cada placa alberga una fila de '
                               'glándulas sebáceas modificadas y alargadas, las **glándulas tarsales o '
                               'de Meibomio**, que secretan un líquido que impide que los párpados se '
                               'adhieran entre sí.\n'
                               '\n'
                               'El parpadeo cumple funciones que la cirugía palpebral debe preservar: '
                               'distribuir la lágrima en forma homogénea sobre la superficie ocular, '
                               'favorecer su circulación, evitar el deslumbramiento, proteger el ojo '
                               'de proyectiles y evitar su desecación por exposición al aire.\n'
                               '\n'
                               '### Concepto e indicaciones (procedimiento de referencia)\n'
                               'El **chalazión** es el quiste de una glándula de Meibomio: una bolita '
                               'dura e indolora en el párpado como consecuencia de la infección '
                               'crónica de dicha glándula cuando se obstruye su orificio de '
                               'desembocadura en el borde palpebral. Su etiología es la obstrucción y '
                               'acumulación en la glándula de Meibomio que produce una infección '
                               '(estafilococo).\n'
                               '\n'
                               'El objetivo quirúrgico es **debridar al máximo la glándula para evitar '
                               'una posible infección y mejorar la estética**.\n'
                               '\n'
                               '> [PENDIENTE CLAUDIA: las fuentes disponibles no describen técnicas '
                               'palpebrales distintas del chalazión (blefaroplastia, corrección de '
                               'ptosis, entropión o ectropión). El compendio contempla "cirugía en '
                               'párpados" en general: ¿qué técnicas adicionales debe cubrir la unidad '
                               'y con qué fuente se redactan?]\n'
                               '\n'
                               '### Lista de chequeo – Mesa de Mayo\n'
                               '- **Instrumental (equipo de chalazión):** pinza de chalazión de '
                               'Lampert, mango de bisturí Bard Parker n.º 3 con hoja 15, cucharilla '
                               'para chalazión (legra), tijeras de Wescott, pinza de disección Bishop '
                               'con dientes, jeringa de 3 cc, jeringa de insulina.\n'
                               '- **Ropa:** campo hendido; campo al tercio triangular, turbante, pinza '
                               'de campo.\n'
                               '- **Material de consumo:** agujas 20 y 22, hisopos, gasas secas, '
                               'cloranfenicol ungüento.\n'
                               '- **Medicamentos:** xilocaína al 2% para la infiltración del borde '
                               'palpebral.\n'
                               '\n'
                               '### Técnica quirúrgica paso a paso\n'
                               '1. Lavado mecánico y quirúrgico de manos con secado; vestido con bata '
                               'y guantes estériles.\n'
                               '2. Se proporciona campo al tercio triangular y pinza de campo; el '
                               'cirujano coloca el turbante y otro en la cabecera.\n'
                               '3. Colocación del campo hendido para delimitar el área quirúrgica.\n'
                               '4. Infiltración del borde del párpado afectado con jeringa de 3 cc, '
                               'aguja de insulina y xilocaína al 2%, secando el área húmeda con gasa '
                               'seca.\n'
                               '5. Se proporciona la **pinza de chalazión de Lampert** y se coloca '
                               'para delimitar la tumoración.\n'
                               '6. Con mango de bisturí Bard Parker n.º 3 con hoja 15 se efectúa la '
                               'incisión en el borde del párpado y la incisión vertical conjuntival.\n'
                               '7. Con cucharilla para chalazión (legra) se realiza el curetaje hasta '
                               'que la cavidad queda limpia.\n'
                               '8. Se proporcionan tijeras de Wescott y pinza de disección Bishop con '
                               'dientes para la resección de la cápsula.\n'
                               '9. Se retira la pinza de chalazión y se realiza compresión con gasa '
                               'seca por **tres minutos**.\n'
                               '10. Se da por terminado el acto quirúrgico.\n'
                               '\n'
                               '### Manejo posoperatorio\n'
                               'La fuente indica cloranfenicol ungüento en el material de consumo del '
                               'procedimiento y compresión hemostática con gasa seca durante tres '
                               'minutos al cierre.\n'
                               '\n'
                               '### Alertas y perlas del instrumentador\n'
                               '- **Pinza de chalazión antes del bisturí:** delimita la tumoración y '
                               'facilita la incisión; tenerla lista en el paso previo.\n'
                               '- **Compresión de tres minutos:** tras retirar la pinza, la hemostasia '
                               'es por compresión con gasa seca; cronometrarla.\n'
                               '- **Ungüento disponible:** el cloranfenicol ungüento forma parte de la '
                               'mesa del procedimiento.\n'
                               '- **Protección de la superficie ocular:** en los procedimientos '
                               'palpebrales el blefaróstato de Castroviejo es el separador habitual en '
                               'las mesas de oftalmología y las riendas palpebrales se fijan con seda '
                               'al campo.\n'
                               '\n'
                               '### Términos clave\n'
                               '- **Chalazión:** quiste de una glándula de Meibomio palpebral por '
                               'obstrucción e infección crónica.\n'
                               '- **Placa tarsal (tarso):** esqueleto fibroso del párpado que le da '
                               'forma y sostén.\n'
                               '- **Curetaje (legrado):** vaciado del contenido del quiste con '
                               'cucharilla hasta dejar limpia la cavidad.\n'
                               '- **Blefaróstato:** separador que mantiene abiertos los párpados '
                               'durante el procedimiento.\n'
                               '\n'
                               'Fuente: docs/Manual-de-tecnicas-quirurgicas-de-oftalmologia.pdf, págs. '
                               '58–59 (chalazión) y 5–6 (anatomía palpebral); docs/GUIA TECNICAS '
                               'QUIRURGICAS DE OFTALMOLOGIA PARA ESTUDIANTES.docx, secciones '
                               '"PARPADOS" y mesas con blefaróstato de Castroviejo.'}]},
]

def seed_official_content(db: Session) -> None:
    """Sincroniza las 8 unidades oficiales y asegura el Curso General."""
    for topic_order, topic_data in enumerate(OFFICIAL_CONTENT):
        with_questions = {
            **topic_data,
            "subtopics": [
                {**subtopic, "questions": OFFICIAL_QUESTIONS.get(subtopic["name"], [])}
                for subtopic in topic_data["subtopics"]
            ],
        }
        sync_topic(db, with_questions, topic_order)
    db.commit()

    # Asegurar que el Curso General y los cursos de profesores tengan todo el contenido.
    course_service.ensure_general_course(db)


def run_seed_by_mode(db: Session, mode: str) -> dict | None:
    """Corre el seed oficial según SEED_MODE y devuelve un resumen (o None).

    - "always": seed completo en cada arranque (histórico de desarrollo).
    - "if_empty": solo carga el contenido si no existe ninguna unidad
      (default en producción): un reinicio nunca modifica contenido existente,
      incluidas las unidades importadas fuera del seed (p. ej. 6–9).
    - "never": no toca la base de datos.
    """
    if mode == "always":
        seed_official_content(db)
        return {"seed": "always"}
    if mode == "if_empty":
        from sqlalchemy import func, select

        from app.models.content import Topic

        n_topics = db.scalar(select(func.count(Topic.id))) or 0
        if n_topics == 0:
            seed_official_content(db)
            return {"seed": "if_empty", "cargado": True}
        return {"seed": "if_empty", "cargado": False, "unidades_existentes": n_topics}
    return {"seed": "never"}
