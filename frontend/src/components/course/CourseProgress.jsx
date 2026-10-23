import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck, faXmark } from '@fortawesome/free-solid-svg-icons'

import { splitUnitName } from '../../lib/curriculum'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import { cn } from '../../lib/utils'

const EASE_OUT_EXPO = (t) => (t === 1 ? 1 : 1 - 2 ** (-10 * t))

/** Cifra que se desliza del valor anterior al nuevo, no desde cero. */
function useTweenedNumber(value, duration = 700) {
  const [shown, setShown] = useState(0)
  const from = useRef(0)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const start = from.current
    if (reduce || start === value) {
      from.current = value
      setShown(value)
      return undefined
    }
    const begin = performance.now()
    let frame = requestAnimationFrame(function step(now) {
      const t = Math.min(1, (now - begin) / duration)
      setShown(Math.round(start + (value - start) * EASE_OUT_EXPO(t)))
      if (t < 1) frame = requestAnimationFrame(step)
    })
    // Pestaña en segundo plano: rAF se congela, así que se fija el final.
    const safety = setTimeout(() => setShown(value), duration + 300)
    from.current = value
    return () => {
      cancelAnimationFrame(frame)
      clearTimeout(safety)
    }
  }, [value, duration])

  return shown
}

/** Primer fotograma vacío para que cada tramo se llene desde cero al aparecer. */
function useMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setMounted(true))
    return () => cancelAnimationFrame(frame)
  }, [])
  return mounted
}

function unitStats(topic, index) {
  const total = topic.subtopics.length
  const done = topic.subtopics.filter((sub) => sub.completed).length
  const { number, title } = splitUnitName(topic.name)
  return { total, done, complete: total > 0 && done === total, number: number ?? index + 1, title }
}

/**
 * Un tramo por unidad, de ancho proporcional a sus subtemas, que se llena con
 * lo completado. La unidad en curso lleva un brillo que avanza.
 *
 * Con ratón: al pasar el cursor enseña la ficha de la unidad y al pulsarlo
 * lleva a ella. En pantallas táctiles no hay cursor, así que tocarlo
 * selecciona la unidad y su ficha aparece debajo de la barra, con el enlace.
 */
function Segment({
  topic,
  courseId,
  index,
  alignEnd,
  current,
  mounted,
  touch,
  selected,
  onSelect,
}) {
  const { total, done, complete, number, title } = unitStats(topic, index)
  const ratio = total ? done / total : 0
  const label = `Unidad ${number}, ${title}: ${done} de ${total} subtemas`

  const bar = (
    <span
      className={cn(
        'relative block h-2 w-full overflow-hidden rounded-full bg-ink-200 transition-[height,box-shadow] duration-200 ease-out',
        'group-hover/seg:h-3 group-focus-visible/seg:h-3 group-focus-visible/seg:ring-2 group-focus-visible/seg:ring-blue-700 group-focus-visible/seg:ring-offset-2',
        current && 'ring-1 ring-blue-900/30 ring-offset-1',
        selected && 'h-3 ring-2 ring-blue-700 ring-offset-1',
      )}
    >
      <span
        className={cn(
          'absolute inset-0 origin-left rounded-full transition-transform duration-700 ease-out',
          complete ? 'bg-blue-900' : 'bg-blue-800',
        )}
        style={{
          transform: `scaleX(${mounted ? ratio : 0})`,
          transitionDelay: mounted ? `${index * 70}ms` : '0ms',
        }}
      />
      {current && (
        <span
          aria-hidden="true"
          className="absolute inset-y-0 left-0 w-1/3 animate-sheen bg-gradient-to-r from-transparent via-white/60 to-transparent"
        />
      )}
    </span>
  )

  const segmentClass = 'group/seg relative flex min-w-0 items-center focus-visible:outline-none'
  // Con ratón el ancho es proporcional a los subtemas; en táctil todos los
  // tramos miden lo mismo para que hasta la unidad más corta se pueda tocar.
  const segmentStyle = { flexGrow: touch ? 1 : Math.max(1, total), flexBasis: 0 }

  if (touch) {
    // Zona táctil alta (44px) aunque la barra visible sea fina.
    return (
      <button
        type="button"
        onClick={onSelect}
        aria-label={label}
        aria-pressed={selected}
        className={cn(segmentClass, 'h-11')}
        style={segmentStyle}
      >
        {bar}
      </button>
    )
  }

  return (
    <Link
      to={`/courses/${courseId}/units/${topic.id}`}
      aria-label={label}
      className={cn(segmentClass, 'h-6')}
      style={segmentStyle}
    >
      {bar}

      {/* Ficha de la unidad al pasar el cursor o enfocar con teclado. */}
      <span
        role="tooltip"
        className={cn(
          'pointer-events-none absolute bottom-full z-20 mb-2 w-max max-w-[min(15rem,70vw)] rounded-xl bg-ink-900 px-3 py-2 text-left text-white shadow-e3',
          'translate-y-1 opacity-0 transition-[opacity,transform] duration-150 ease-out',
          'group-hover/seg:translate-y-0 group-hover/seg:opacity-100 group-focus-visible/seg:translate-y-0 group-focus-visible/seg:opacity-100',
          // Hacia dentro: los de la mitad derecha se abren hacia la izquierda.
          alignEnd ? 'right-0' : 'left-0',
        )}
      >
        <span className="block text-[0.6875rem] font-semibold uppercase tracking-[0.08em] text-blue-200">
          Unidad {number}
        </span>
        <span className="mt-0.5 block text-[0.8125rem] font-medium leading-snug">{title}</span>
        <span className="tabular mt-1 flex items-center gap-1.5 text-[0.75rem] text-ink-300">
          {complete && (
            <FontAwesomeIcon icon={faCheck} className="text-[0.65rem] text-correct-200" />
          )}
          {done} de {total} subtemas
        </span>
      </span>
    </Link>
  )
}

/** Ficha de la unidad tocada, debajo de la barra (solo en pantallas táctiles). */
function SelectedUnit({ topic, index, courseId, onClose }) {
  const { total, done, complete, number, title } = unitStats(topic, index)
  return (
    <div className="mt-1 flex animate-rise-in items-center gap-3 rounded-xl bg-ink-900 py-2.5 pl-3.5 pr-1.5 text-white">
      <Link to={`/courses/${courseId}/units/${topic.id}`} className="min-w-0 flex-1">
        <span className="block text-[0.6875rem] font-semibold uppercase tracking-[0.08em] text-blue-200">
          Unidad {number}
          <span className="tabular ml-2 normal-case tracking-normal text-ink-300">
            {complete && <FontAwesomeIcon icon={faCheck} className="mr-1 text-correct-200" />}
            {done} de {total}
          </span>
        </span>
        <span className="mt-0.5 flex items-center gap-2 text-[0.875rem] font-medium leading-snug">
          <span className="truncate">{title}</span>
          <FontAwesomeIcon
            icon={faArrowRight}
            className="shrink-0 text-[0.7rem]"
            aria-hidden="true"
          />
        </span>
      </Link>
      <button
        type="button"
        onClick={onClose}
        aria-label="Cerrar la ficha de la unidad"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-ink-300 transition-colors duration-150 active:bg-white/10"
      >
        <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
      </button>
    </div>
  )
}

/**
 * Progreso del curso en la cabecera: la cifra, un tramo por unidad y en qué
 * unidad está el estudiante. Sin cuentas regresivas de tiempo: el avance se
 * cuenta en lo que ya se hizo, no en lo que falta.
 */
export default function CourseProgress({
  topics,
  courseId,
  percentage,
  completed,
  total,
  nextSubtopic,
  className,
}) {
  const mounted = useMounted()
  // Modo «tocar» en pantallas táctiles y en ventanas estrechas: ahí una ficha
  // flotante no tiene sitio a los lados del tramo.
  const touch = !useMediaQuery('(hover: hover) and (pointer: fine) and (min-width: 640px)')
  const [selectedId, setSelectedId] = useState(null)
  // Dónde empieza cada tramo sobre la barra (0 a 1): las fichas de los que
  // empiezan pasada la mitad se abren hacia la izquierda.
  const sizes = topics.map((topic) => Math.max(1, topic.subtopics.length))
  const sum = sizes.reduce((a, b) => a + b, 0) || 1
  const startsAt = sizes.map((_, i) => sizes.slice(0, i).reduce((a, b) => a + b, 0) / sum)
  const selectedIndex = touch ? topics.findIndex((topic) => topic.id === selectedId) : -1
  const shown = useTweenedNumber(percentage)
  const currentTopicId = nextSubtopic?.topic?.id ?? null
  const currentUnit = nextSubtopic ? splitUnitName(nextSubtopic.topic.name) : null

  // Un subtema recién completado se celebra con una ficha breve junto a la cifra.
  const previous = useRef(completed)
  const [gain, setGain] = useState(0)
  useEffect(() => {
    const delta = completed - previous.current
    previous.current = completed
    if (delta <= 0) return undefined
    setGain(delta)
    const timer = setTimeout(() => setGain(0), 2200)
    return () => clearTimeout(timer)
  }, [completed])

  const status =
    total > 0 && completed === total
      ? 'Curso completado'
      : completed === 0
        ? 'Listo para empezar'
        : currentUnit
          ? `En curso: Unidad ${currentUnit.number ?? ''} · ${currentUnit.title}`
          : null

  return (
    <div className={className}>
      <div className="flex items-end justify-between gap-4">
        <div className="flex items-baseline gap-2.5">
          <span
            role="progressbar"
            aria-label="Progreso del curso"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            className="tabular text-[1.5rem] font-semibold leading-none tracking-[-0.02em] text-blue-900"
          >
            {shown}%
          </span>
          <span className="tabular text-xs text-ink-500">
            {completed} de {total} subtemas
          </span>
          {gain > 0 && (
            <span
              key={completed}
              className="tabular animate-pop rounded-full bg-correct-50 px-2 py-0.5 text-[0.6875rem] font-bold text-correct-700 ring-1 ring-inset ring-correct-200"
            >
              +{gain}
            </span>
          )}
        </div>
        {status && (
          <span className="hidden min-w-0 truncate text-xs font-medium text-ink-500 sm:block">
            {status}
          </span>
        )}
      </div>

      <div className={cn('flex items-center gap-1 sm:gap-1.5', touch ? 'mt-0.5' : 'mt-2')}>
        {topics.map((topic, index) => (
          <Segment
            key={topic.id}
            topic={topic}
            courseId={courseId}
            index={index}
            alignEnd={startsAt[index] >= 0.5}
            current={topic.id === currentTopicId}
            mounted={mounted}
            touch={touch}
            selected={topic.id === selectedId}
            onSelect={() => setSelectedId((id) => (id === topic.id ? null : topic.id))}
          />
        ))}
      </div>

      {selectedIndex >= 0 ? (
        <SelectedUnit
          topic={topics[selectedIndex]}
          index={selectedIndex}
          courseId={courseId}
          onClose={() => setSelectedId(null)}
        />
      ) : (
        status && (
          <p className="flex gap-3 text-xs font-medium text-ink-500 sm:hidden">
            <span className="min-w-0 flex-1 truncate">{status}</span>
            {touch && <span className="shrink-0 text-ink-400">Toca una unidad</span>}
          </p>
        )
      )}
    </div>
  )
}
