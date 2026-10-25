// Instrumento propio de INSOFT; no es un cuestionario validado de Nielsen ni SUS.
export const SURVEY_VERSION = 'insoft-nielsen-v1'
export const HEURISTICS = [
  { id: 'h01', title: 'Saber qué está pasando', statement: 'INSOFT me permite saber cuándo está cargando y cuál es mi avance en el curso.' },
  { id: 'h02', title: 'Entender el lenguaje', statement: 'Los nombres de las secciones y las instrucciones me resultan comprensibles para estudiar instrumentación quirúrgica.' },
  { id: 'h03', title: 'Tener el control', statement: 'Puedo salir de una práctica, cerrar el asistente o volver al contenido cuando lo necesito.' },
  { id: 'h04', title: 'Encontrar coherencia', statement: 'Los botones y menús funcionan de manera consistente entre las distintas secciones.' },
  { id: 'h05', title: 'Evitar equivocaciones', statement: 'Las indicaciones de INSOFT me ayudan a evitar acciones por error, como enviar una respuesta sin querer.' },
  { id: 'h06', title: 'Reconocer las opciones', statement: 'Encuentro los subtemas y las herramientas sin tener que recordar dónde estaban.' },
  { id: 'h07', title: 'Estudiar a mi ritmo', statement: 'Puedo retomar el estudio y llegar a las actividades que necesito sin pasos innecesarios.' },
  { id: 'h08', title: 'Concentrarme en el contenido', statement: 'La organización de la pantalla me permite leer y estudiar sin distracciones innecesarias.' },
  { id: 'h09', title: 'Resolver un problema', statement: 'Cuando algo falla, el mensaje me ayuda a entender qué pasó y qué puedo hacer para continuar.' },
  { id: 'h10', title: 'Encontrar orientación', statement: 'Cuando necesito ayuda para usar la plataforma, encuentro indicaciones útiles.' },
]

export const RATING_OPTIONS = [
  { value: 1, label: 'Totalmente en desacuerdo' },
  { value: 2, label: 'En desacuerdo' },
  { value: 3, label: 'Ni de acuerdo ni en desacuerdo' },
  { value: 4, label: 'De acuerdo' },
  { value: 5, label: 'Totalmente de acuerdo' },
  { value: 'na', label: 'No lo he probado / No aplica' },
]

export const ratingLabel = (value) => RATING_OPTIONS.find((item) => item.value === value)?.label
