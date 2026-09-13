import {
  faArrowsLeftRight,
  faCircleDot,
  faDroplet,
  faGlasses,
  faMicroscope,
  faScissors,
  faSyringe,
  faWaveSquare,
} from '@fortawesome/free-solid-svg-icons'

/**
 * Identidad visual de cada unidad del temario oficial.
 *
 * Cada unidad tiene su propio tinte pastel, de modo que el estudiante reconoce
 * dónde está por el color antes de leer el título. Los tintes solo pintan
 * superficies; el texto y los iconos usan su contraparte legible.
 */
const UNIT_IDENTITY = [
  { icon: faMicroscope, tint: 'lavender', short: 'Generalidades' },
  { icon: faSyringe, tint: 'sky', short: 'Procedimientos generales' },
  { icon: faDroplet, tint: 'mint', short: 'Glaucoma' },
  { icon: faCircleDot, tint: 'butter', short: 'Segmento anterior' },
  { icon: faWaveSquare, tint: 'peach', short: 'Vitreorretinales' },
  { icon: faArrowsLeftRight, tint: 'rose', short: 'Estrabismo' },
  { icon: faGlasses, tint: 'lavender', short: 'Refractivas' },
  { icon: faScissors, tint: 'mint', short: 'Oculoplastia' },
]

// Clases completas y literales: Tailwind no puede resolver nombres compuestos
// en tiempo de compilación.
const TINT_CLASSES = {
  lavender: {
    soft: 'bg-soft-lavender',
    text: 'text-deep-lavender',
    bg: 'bg-deep-lavender',
    border: 'border-soft-lavender',
  },
  sky: {
    soft: 'bg-soft-sky',
    text: 'text-deep-sky',
    bg: 'bg-deep-sky',
    border: 'border-soft-sky',
  },
  mint: {
    soft: 'bg-soft-mint',
    text: 'text-deep-mint',
    bg: 'bg-deep-mint',
    border: 'border-soft-mint',
  },
  butter: {
    soft: 'bg-soft-butter',
    text: 'text-deep-butter',
    bg: 'bg-deep-butter',
    border: 'border-soft-butter',
  },
  peach: {
    soft: 'bg-soft-peach',
    text: 'text-deep-peach',
    bg: 'bg-deep-peach',
    border: 'border-soft-peach',
  },
  rose: {
    soft: 'bg-soft-rose',
    text: 'text-deep-rose',
    bg: 'bg-deep-rose',
    border: 'border-soft-rose',
  },
}

export function unitIdentity(order = 0) {
  const identity = UNIT_IDENTITY[order % UNIT_IDENTITY.length]
  return { ...identity, classes: TINT_CLASSES[identity.tint] }
}

/** "UNIDAD 3. Glaucoma" -> { number: 3, title: "Glaucoma" } */
export function splitUnitName(name = '') {
  const match = name.match(/^UNIDAD\s+(\d+)\.\s*(.+)$/i)
  if (!match) return { number: null, title: name }
  return { number: Number(match[1]), title: match[2] }
}

/** 95 -> "1 h 35 min" · 42 -> "42 min" */
export function formatDuration(minutes = 0) {
  const total = Math.max(0, Math.round(minutes))
  if (total < 60) return `${total} min`
  const hours = Math.floor(total / 60)
  const rest = total % 60
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`
}

/** Versión compacta para metadatos densos: "1h 35m" */
export function formatDurationShort(minutes = 0) {
  const total = Math.max(0, Math.round(minutes))
  if (total < 60) return `${total}m`
  const hours = Math.floor(total / 60)
  const rest = total % 60
  return rest === 0 ? `${hours}h` : `${hours}h ${rest}m`
}

/**
 * Cifras del temario oficial mostradas en la portada pública, donde todavía no
 * hay sesión para consultarlas por API. Reflejan app/seed/seed_content.py.
 */
export const CURRICULUM_FACTS = {
  units: 8,
  subtopics: 22,
  questions: 66,
  verified: 100,
}
