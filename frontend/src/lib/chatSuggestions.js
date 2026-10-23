/**
 * Preguntas sugeridas para Sofía según la unidad en la que está el estudiante.
 * Se indexan por el número de la unidad del temario oficial ("UNIDAD 3." → 3).
 * Son preguntas que el contenido del curso responde, no preguntas abiertas.
 */
const BY_UNIT = {
  1: [
    '¿Qué estructuras forman el globo ocular?',
    '¿Qué tipos de anestesia se usan en cirugía oftalmológica?',
    '¿Cómo se organiza el instrumental en la mesa?',
  ],
  2: [
    '¿En qué consiste la resección de pterigión?',
    '¿Cómo se instrumenta un drenaje de chalazión?',
    '¿Qué cuidados lleva una inyección intravítrea?',
  ],
  3: [
    '¿Qué es el glaucoma y por qué se opera?',
    '¿Cuáles son los pasos de la trabeculotomía?',
    '¿Para qué sirve un implante de drenaje?',
  ],
  4: [
    '¿Cuáles son los pasos de la facoemulsificación?',
    '¿En qué se diferencia la extracción extracapsular?',
    '¿Qué se prepara para un trasplante de córnea?',
  ],
  5: [
    '¿Qué es una vitrectomía?',
    '¿Qué equipos se usan en cirugía vitreorretinal?',
    '¿Qué complicaciones pueden aparecer?',
  ],
  6: [
    '¿Qué es el estrabismo y cómo se corrige?',
    '¿Qué músculos se intervienen?',
    '¿Qué instrumental lleva la cirugía de estrabismo?',
  ],
  7: [
    '¿Qué patologías refractivas se operan?',
    '¿En qué se diferencian las técnicas refractivas?',
    '¿Qué cuidados tiene el instrumentador aquí?',
  ],
  8: [
    '¿Qué abarca la oculoplastia?',
    '¿Qué procedimientos de párpado se ven?',
    '¿Qué suturas se usan en oculoplastia?',
  ],
  9: [
    '¿Cuáles son los pasos de la cirugía de pterigión?',
    '¿Qué es el autoinjerto conjuntival?',
    '¿Qué complicaciones puede haber después?',
  ],
}

const GENERAL = [
  '¿Qué voy a aprender en el curso?',
  '¿Qué es un pterigión?',
  '¿Qué tipos de anestesia existen?',
]

/**
 * unitNumber: número de la unidad actual, o null fuera de una unidad.
 * subtopicName: si está en un subtema, la primera sugerencia es sobre él.
 */
export function suggestionsFor(unitNumber, subtopicName) {
  const base = BY_UNIT[unitNumber] || GENERAL
  if (!subtopicName) return base
  return [`Resúmeme «${subtopicName}»`, ...base.slice(0, 2)]
}
