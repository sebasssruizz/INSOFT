// Configuración de las vistas interactivas de mesas quirúrgicas (GLB).
//
// Cada mesa se carga desde /models/mesas y sus instrumentos se pueden inspeccionar
// cargando el GLB individual desde /models/instrumentos. La identificación de cada
// instrumento dentro de la mesa se hace por el nombre de malla (`node.name` del GLB),
// que es estable y compartido entre el catálogo y las mesas. Algunas mallas traen un
// sufijo de copia (`.001`, p. ej. dos bowls); se normaliza antes de comparar.

/** `/models/instrumentos/...` · GLB del catálogo que se muestra al inspeccionar. */
const catalogo = (file) => `/models/instrumentos/${file}`

/**
 * Catálogo central de instrumentos.
 *
 * `meshNames` son los nombres de malla (`node.name`) de cada instrumento dentro de
 * los GLB de las mesas. Se comparan normalizados (ver `instrumentForMesh`).
 */
export const INSTRUMENTOS = {
  b001: {
    title: 'Blefaróstato de colibrí',
    eyebrow: 'Separador palpebral',
    description:
      'Separador autoestático de Barraquer-Colibrí que mantiene los párpados abiertos y despeja el campo quirúrgico. Se usa en la inyección intravítrea y en los procedimientos que necesitan una exposición estable del globo.',
    details: [
      'Mantiene los párpados abiertos sin ayuda del asistente',
      'Colocarlo sin ejercer presión excesiva sobre el globo',
      'Revisar limpieza y articulación antes del montaje',
    ],
    modelUrl: catalogo('b001_blefarostato-colibri.glb'),
    meshNames: ['tripo_86f46718_43c0_4911_b705_7fa8cf1c9a43'],
  },
  b002: {
    title: 'Pinza conjuntiva',
    eyebrow: 'Instrumental de disección',
    description:
      'Pinza delicada para sujetar y manipular la conjuntiva y los tejidos superficiales con precisión durante la cirugía oftalmológica.',
    details: [
      'Permite una sujeción atraumática',
      'Sus puntas deben estar alineadas',
      'Se utiliza con movimientos firmes y controlados',
    ],
    modelUrl: catalogo('b002_pinza-conjuntiva.glb'),
    meshNames: ['tripo_36b1b19c_4880_454a_866f_5fec877cdb5b'],
  },
  b003: {
    title: 'Blefaróstato de Castroviejo',
    eyebrow: 'Separador palpebral',
    description:
      'Separador palpebral autoestático, el más versátil de la mesa. Mantiene los párpados abiertos durante la mayor parte de los procedimientos palpebrales e intraoculares.',
    details: [
      'Separador habitual en las mesas de oftalmología',
      'Alternativa al colibrí en cirugía palpebral',
      'Verificar el muelle y las puntas antes de usarlo',
    ],
    modelUrl: catalogo('b003_blefarostato-castroviejo.glb'),
    meshNames: ['tripo_192a5e63_ebd2_4ce2_87a6_2a7094a0ebdf'],
  },
  b004: {
    title: 'Mango de bisturí nº 3',
    eyebrow: 'Corte',
    description:
      'Mango Bard Parker nº 3 que monta la hoja 15 para queratectomías e incisiones esclerocorneales, o la hoja 11 para paracentesis e incisión de chalazión.',
    details: [
      'Monta la hoja 15 para la mayoría de las incisiones',
      'Monta la hoja 11 para chalazión y limbo',
      'Entregarlo con la hoja ya fijada y protegida',
    ],
    modelUrl: catalogo('b004_mango-bisturi.glb'),
    meshNames: ['tripo_60353c9e_5dd0_4345_a05c_f480be1a2ffe'],
  },
  b005: {
    title: 'Tijera de Westcott',
    eyebrow: 'Corte',
    description:
      'Tijera microquirúrgica para disecar la conjuntiva y la cápsula de Tenon. Es la tijera de disección más usada de la mesa.',
    details: [
      'Diseca conjuntiva y cápsula de Tenon',
      'Mantener el filo limpio y alineado',
      'Cortar con la punta, no con la base',
    ],
    modelUrl: catalogo('b005_tijera-westcott.glb'),
    meshNames: ['tripo_61a4233c_293b_4114_8d6e_acbce26c1604'],
  },
  b006: {
    title: 'Tijera de enucleación',
    eyebrow: 'Corte',
    description:
      'Tijera de hojas fuertes y curvas, diseñada para seccionar las inserciones musculares y el nervio óptico en la enucleación del globo.',
    details: [
      'Uso dedicado en la enucleación',
      'Hojas robustas para tejido profundo',
      'Revisar el filo y la articulación',
    ],
    modelUrl: catalogo('b006_tijera-enucleacion.glb'),
    meshNames: ['ac06c18a_c2ce_40e6_a870_d7eaaf638f31'],
  },
  b007: {
    title: 'Aplicadores',
    eyebrow: 'Auxiliar de mesa',
    description:
      'Aplicadores para hemostasia y presión sobre el tejido. Auxiliares de la mesa para controlar el sangrado y sostener material de consumo.',
    details: [
      'Hemostasia por presión',
      'Uso junto a gasas y material de consumo',
      'Mantenerlos limpios y secos',
    ],
    modelUrl: catalogo('b007_aplicadores.glb'),
    meshNames: ['tripo_7d0a42de_aaa3_48e6_960b_5ff6902d0edf'],
  },
  b009: {
    title: 'Pinza de disección sin dientes',
    eyebrow: 'Instrumental de disección',
    description:
      'Pinza de puntas finas sin dientes para manipular tejidos delicados sin dañarlos.',
    details: [
      'Sujeción atraumática de tejido fino',
      'Puntas alineadas y sin mordida',
      'Uso en disección fina',
    ],
    modelUrl: catalogo('b009_pinza-disecion-sin-garra.glb'),
    meshNames: ['tripo_77d16a77_3f30_45fb_a977_b4add6de72af'],
  },
  b010: {
    title: 'Pinza de Bishop con dientes',
    eyebrow: 'Instrumental de disección',
    description:
      'Pinza de Bishop con dientes para sujetar tejidos firmes con seguridad. Sin dientes se reserva para el tejido delicado.',
    details: [
      'Sujeción firme de tejido resistente',
      'Los dientes evitan el deslizamiento',
      'Reservada para tejido no delicado',
    ],
    modelUrl: catalogo('b010_pinza-bishop.glb'),
    meshNames: ['ced2312c_aec0_4927_8cee_373e69285293'],
  },
  b011: {
    title: 'Porta agujas fino',
    eyebrow: 'Suturas',
    description:
      'Porta agujas Castroviejo fino, estándar para suturas 10/0 y 9/0 en córnea; el de Barraquer se usa en evisceración, enucleación y cierres conjuntivales.',
    details: [
      'Montar la aguja a dos tercios de la punta',
      'Orientar el filo hacia el tejido',
      'Entregar con la hebra extendida y sin nudos',
    ],
    modelUrl: catalogo('b011_porta-agujas-fino.glb'),
    meshNames: ['tripo_09c7957d_af79_40f1_a1d5_48114a0e27c9'],
  },
  b012: {
    title: 'Cureta de evisceración (cucharilla)',
    eyebrow: 'Auxiliar de mesa',
    description:
      'Cureta o cucharilla (legra) para el curetaje de cavidades: vacía el contenido en el chalazión y en la evisceración hasta dejar la cavidad limpia.',
    details: [
      'Curetaje hasta dejar limpia la cavidad',
      'También de uso en chalazión (legra)',
      'Mantener el borde sin mellas',
    ],
    modelUrl: catalogo('b012_cureta-evisceracion.glb'),
    meshNames: ['tripo_4869c0d2_a02c_4161_a10b_ef80ef26f5bd'],
  },
  b013: {
    title: 'Quemador',
    eyebrow: 'Equipos biomédicos',
    description:
      'Quemador (cauterio) para la hemostasia por calor. Cuando no hay coagulador bipolar se verifica su funcionamiento con alcohol absoluto y encendedor.',
    details: [
      'Hemostasia térmica',
      'Verificar la llama y el reservorio antes de usarlo',
      'Alternativa al coagulador bipolar',
    ],
    modelUrl: catalogo('b013_quemador.glb'),
    meshNames: ['tripo_0c164d59_5ef7_4b8a_a035_a4aee08e29a8'],
  },
  b014: {
    title: 'Compás de Castroviejo',
    eyebrow: 'Medición',
    description:
      'Compás de precisión para medir la pars plana, las distancias desde el limbo y los retroimplantes musculares.',
    details: [
      'Mide 3.5 mm (pseudofáquico) o 4 mm (fáquico) desde el limbo',
      'Marcación de esclerotomías',
      'Puntas finas y calibradas',
    ],
    modelUrl: catalogo('b014_compas.glb'),
    meshNames: ['tripo_34614668_7543_4f6a_9a79_f0d51d6cf809'],
  },
  b015: {
    title: 'Jeringas',
    eyebrow: 'Material de consumo',
    description:
      'Jeringas de distintos volúmenes (3 cc, insulina, 20/10 cc) para anestesia, irrigación y administración de fármacos.',
    details: [
      'Jeringa de 3 cc para anestesia local',
      'Jeringa de insulina para infiltración fina',
      'Purgar y etiquetar según el fármaco',
    ],
    modelUrl: catalogo('b015_jeringas.glb'),
    meshNames: ['tripo_078562c3_2d6d_49c6_aabd_1d652724d06c'],
  },
  b016: {
    title: 'Iniciador y sondas lagrimales',
    eyebrow: 'Vía lagrimal',
    description:
      'Iniciador (dilatador) que abre el punto lagrimal, seguido de sondas de calibre progresivo para permeabilizar el conducto nasolagrimal.',
    details: [
      'Dilatar primero el punto lagrimal con el iniciador',
      'Sondas de calibre creciente, sin forzar',
      'Verificar la permeabilidad con irrigación',
    ],
    modelUrl: catalogo('b016_iniciador-sonda-lagrimal.glb'),
    meshNames: ['d8128891_710c_4206_9b57_3af7ade633ed'],
  },
  b017: {
    title: 'Pinza de mosquito',
    eyebrow: 'Hemostasia',
    description: 'Pinza de mosquito para la hemostasia por pinzamiento de vasos pequeños.',
    details: [
      'Pinzamiento de vasos finos',
      'Puntas firmes y alineadas',
      'Uso rápido ante un sangrado',
    ],
    modelUrl: catalogo('b017_pinza-mosquito.glb'),
    meshNames: ['tripo_6d190b05_aa8c_4499_8071_b29b33364cc8'],
  },
  b018: {
    title: 'Adson con garra',
    eyebrow: 'Instrumental de disección',
    description:
      'Pinza Adson con garra para sujetar tejido firme. De uso en la enucleación y en disecciones amplias.',
    details: [
      'Sujeción con dientes para tejido resistente',
      'Uso en enucleación y disección amplia',
      'Alternativa a la Bishop con dientes',
    ],
    modelUrl: catalogo('b018_adson-con-garra.glb'),
    meshNames: ['tripo_1dfb8d08_f13d_440d_84e0_a39bb89123bb'],
  },
  b019: {
    title: 'Adson sin garra',
    eyebrow: 'Instrumental de disección',
    description: 'Pinza Adson sin garra para tejidos delicados; de manejo atraumático.',
    details: ['Sujeción atraumática', 'Puntas finas', 'Uso en tejido delicado'],
    modelUrl: catalogo('b019_adson-sin-garra.glb'),
    meshNames: ['cac08242_4e0c_4320_b613_468a4092e4ba'],
  },
  b020: {
    title: 'Gancho de músculo',
    eyebrow: 'Auxiliar de mesa',
    description:
      'Gancho (de estrabismo o de Jameson) para localizar y manipular los músculos extraoculares.',
    details: [
      'Localización de los músculos rectos',
      'Reparación muscular',
      'Manipulación delicada, sin forzar el tejido',
    ],
    modelUrl: catalogo('b020_gancho-musculo.glb'),
    meshNames: ['a12741bc_acc1_4e59_8792_c6e09de9ccf0'],
  },
  b021: {
    title: 'Cable de pinza bipolar',
    eyebrow: 'Equipos biomédicos',
    description:
      'Cable que conecta la pinza bipolar al coagulador para la hemostasia por corriente en vasos pequeños.',
    details: [
      'Conexión al coagulador bipolar',
      'Corte y hemostasia simultáneos',
      'Verificar las conexiones antes del uso',
    ],
    modelUrl: catalogo('b021_cable-pinza-bipolar.glb'),
    meshNames: ['c18285f0_10d3_41c3_a3ca_44bf9b8907c4'],
  },
  b022: {
    title: 'Campo de ojo',
    eyebrow: 'Ropa quirúrgica',
    description:
      'Paño o campo de ojo para exponer y delimitar el campo quirúrgico sobre el globo.',
    details: [
      'Exposición del área quirúrgica',
      'Uso junto a pinzas de campo',
      'Mantenerlo estéril y sin pliegues',
    ],
    modelUrl: catalogo('b022_campo-de-ojo.glb'),
    meshNames: ['a5a3364d_5ed6_4941_a0de_37f623da12f0'],
  },
  b023: {
    title: 'Apósito ocular',
    eyebrow: 'Material de consumo',
    description: 'Apósito (parche) ocular para proteger el ojo al final del procedimiento.',
    details: [
      'Protección posoperatoria',
      'Fijación con micropore',
      'Colocarlo sin presión sobre el globo',
    ],
    modelUrl: catalogo('b023_aposito-ocular.glb'),
    meshNames: ['tripo_8b049f27_e3e4_4d7d_9dd5_a31abea077a2'],
  },
  b024: {
    title: 'Mesa quirúrgica',
    eyebrow: 'Mobiliario',
    description:
      'Camilla o mesa quirúrgica sobre la que se organiza el instrumental por tiempos.',
    details: [
      'Superficie de montaje del instrumental',
      'Organización por tiempos quirúrgicos',
      'Mantener el orden y la asepsia',
    ],
    modelUrl: catalogo('b024_mesa-quirurgica.glb'),
    meshNames: ['tripo_1cad7936_90cf_4282_9c05_2305c3211be6'],
  },
  b025: {
    title: 'Mesa auxiliar metálica',
    eyebrow: 'Mobiliario',
    description: 'Carro o mesa auxiliar metálica para soportar equipos y material.',
    details: ['Soporte de equipos biomédicos', 'Estructura estable', 'Limpiarla antes y después'],
    modelUrl: catalogo('b025_mesa-quirurgica-metalica.glb'),
    meshNames: ['ae7dfdda_3741_4789_8738_d19100101512'],
  },
  b026: {
    title: 'Bowl metálico',
    eyebrow: 'Material de consumo',
    description: 'Bol metálico para soluciones y lavados durante el procedimiento.',
    details: ['Contenedor de soluciones estériles', 'Uso con irrigación y lavado', 'Mantenerlo estéril'],
    modelUrl: catalogo('b026_bowl-metalico.glb'),
    meshNames: ['d50f887c_2eb7_4dfc_8fad_975cde87b881'],
  },
  b027: {
    title: 'Bandeja metálica',
    eyebrow: 'Mobiliario',
    description: 'Bandeja metálica donde se dispone el instrumental del procedimiento.',
    details: ['Disposición del instrumental', 'Organización por tiempos', 'Superficie estéril'],
    modelUrl: catalogo('b027_bandeja-metalica.glb'),
    meshNames: ['dc4653b7_ad30_4d28_b9bd_4b496ceff43a'],
  },
}

/**
 * Mesas quirúrgicas por procedimiento.
 *
 * `subtopicNames` enlaza cada mesa con los subtemas oficiales donde se ofrece la
 * vista interactiva. Un subtema puede tener varias mesas (p. ej. U8).
 * `instruments` lista los id del catálogo presentes en esa mesa.
 */
export const MESAS = {
  pterigium: {
    title: 'Mesa de resección de pterigión',
    eyebrow: 'Unidad 2 · Procedimientos generales',
    description:
      'Montaje del instrumental para la resección de pterigión con plastía conjuntival: disección, extracción de tenón, confección de la plastía y sutura.',
    modelUrl: '/models/mesas/mesa_pterigium.glb',
    subtopicNames: ['Resección de pterigión'],
    instruments: ['b003', 'b004', 'b005', 'b007', 'b009', 'b011', 'b015', 'b019', 'b024', 'b026', 'b027'],
  },
  chalazium: {
    title: 'Mesa de drenaje de chalazión',
    eyebrow: 'Unidad 2 · Procedimientos generales',
    description:
      'Equipo de chalazión: delimitación, incisión, curetaje y resección de la cápsula con compresión hemostática.',
    modelUrl: '/models/mesas/mesa_chalazium.glb',
    subtopicNames: ['Drenaje de chalazión'],
    instruments: ['b004', 'b005', 'b007', 'b009', 'b010', 'b012', 'b013', 'b015', 'b022', 'b024', 'b026', 'b027'],
  },
  inyeccion_intravitrea: {
    title: 'Mesa de inyección intravítrea',
    eyebrow: 'Unidad 2 · Procedimientos generales',
    description:
      'Montaje para la inyección intravítrea: anestesia tópica estéril, asepsia estricta y administración del fármaco en el humor vítreo.',
    modelUrl: '/models/mesas/mesa_inyeccion_intravitrea.glb',
    subtopicNames: ['Inyecciones intravítreas'],
    instruments: ['b001', 'b007', 'b014', 'b015', 'b022', 'b024', 'b026', 'b027'],
  },
  vias_lagrimales: {
    title: 'Mesa de dilatación de vías lagrimales',
    eyebrow: 'Unidad 2 · Procedimientos generales',
    description:
      'Set de sondaje lagrimal: iniciador, sondas de calibre progresivo y verificación de permeabilidad por irrigación.',
    modelUrl: '/models/mesas/mesa_vias_lagrimales.glb',
    subtopicNames: ['Dilatación de vías lagrimales'],
    instruments: ['b007', 'b013', 'b015', 'b016', 'b022', 'b024', 'b026', 'b027'],
  },
  evisceracion: {
    title: 'Mesa de evisceración',
    eyebrow: 'Unidad 8 · Oculoplastia',
    description:
      'Instrumental para la evisceración del contenido ocular, con control de la hemostasia y cierre de la esclera.',
    modelUrl: '/models/mesas/mesa_evisceracion.glb',
    subtopicNames: ['Cirugía en Párpados'],
    instruments: [
      'b003', 'b004', 'b005', 'b007', 'b010', 'b011', 'b012', 'b015',
      'b017', 'b018', 'b021', 'b022', 'b023', 'b024', 'b026', 'b027',
    ],
  },
  enucleacion: {
    title: 'Mesa de enucleación',
    eyebrow: 'Unidad 8 · Oculoplastia',
    description:
      'Instrumental para la enucleación del globo ocular: sección de inserciones musculares y del nervio óptico, hemostasia y cierre.',
    modelUrl: '/models/mesas/mesa_enucleacion.glb',
    subtopicNames: ['Cirugía en Párpados'],
    instruments: [
      'b003', 'b004', 'b005', 'b006', 'b007', 'b010', 'b011', 'b015', 'b017',
      'b018', 'b020', 'b021', 'b022', 'b023', 'b024', 'b026', 'b027',
    ],
  },
}

/** Clave de mesa válida o `null`. */
export function resolveMesa(key) {
  return MESAS[key] ?? null
}

/** Mesas asociadas a un subtema oficial (puede haber más de una). */
export function mesasForSubtopic(name = '') {
  return Object.keys(MESAS).filter((key) => MESAS[key].subtopicNames.includes(name))
}

/** ¿Tiene vista interactiva este subtema? */
export function hasMesaSubtopic(name = '') {
  return mesasForSubtopic(name).length > 0
}

/** Instrumentos resueltos de una mesa, en el orden de montaje. */
export function instrumentsForMesa(key) {
  const mesa = MESAS[key]
  if (!mesa) return []
  return mesa.instruments.map((id) => ({ id, ...INSTRUMENTOS[id] })).filter((item) => item.title)
}

/**
 * Devuelve el instrumento cuya malla coincide con `objectName` dentro de una mesa.
 * Compara el nombre base, ignorando el sufijo de copia (`.001`, `.002`, …) que
 * añade Blender/GLB a las instancias repetidas del mismo objeto.
 */
export function instrumentForMesh(key, objectName = '') {
  const base = objectName.replace(/\.\d+$/, '')
  for (const item of instrumentsForMesa(key)) {
    if (item.meshNames.includes(base)) return item
  }
  return null
}
