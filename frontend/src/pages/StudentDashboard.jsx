import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight,
  faCheck,
  faChevronRight,
  faClock,
  faKey,
  faLayerGroup,
  faListCheck,
  faPlus,
} from '@fortawesome/free-solid-svg-icons'

import EyeScene from '../components/three/LazyEyeScene'
import JoinCourseForm from '../components/JoinCourseForm'
import { Badge, Meta } from '../components/ui/Meta'
import { Button } from '../components/ui/Button'
import { Counter } from '../components/ui/Counter'
import { IrisMark } from '../components/ui/IrisMark'
import { ProgressRing } from '../components/ui/Progress'
import { formatDuration, splitUnitName } from '../lib/curriculum'
import { cn } from '../lib/utils'
import { getCourseTopics } from '../services/contentService'
import { useAuth } from '../hooks/useAuth'
import { useCourses } from '../hooks/useCourses'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Buenos días'
  if (hour < 20) return 'Buenas tardes'
  return 'Buenas noches'
}

/** Una frase que acompaña según el punto del temario en que esté. */
function encouragement(overall, remaining) {
  if (overall >= 100) return 'Completaste todo el temario disponible. Repasa cuando quieras.'
  if (overall === 0) return 'La primera unidad está lista para ti. Empieza cuando quieras.'
  const left = `Te ${remaining === 1 ? 'queda' : 'quedan'} ${remaining} ${remaining === 1 ? 'subtema' : 'subtemas'}`
  if (overall >= 50) return `Ya pasaste la mitad del camino. ${left}.`
  return `Vas por buen camino. ${left}.`
}

/**
 * Curso en el que poner el foco: el que se dejó a medias; si no hay, el
 * primero sin empezar; si todo está hecho, el primero.
 */
function pickFocusCourse(courses) {
  const pct = (course) => course.progress_percentage || 0
  return (
    courses.find((course) => pct(course) > 0 && pct(course) < 100) ||
    courses.find((course) => pct(course) < 100) ||
    courses[0] ||
    null
  )
}

/** Siguiente subtema del curso en foco, pedido a la API de temario. */
function useNextSubtopic(course) {
  const [state, setState] = useState({ loading: true, next: null, unit: null })
  const courseId = course?.id
  const completed = course?.completed_subtopics

  useEffect(() => {
    if (!courseId) {
      setState({ loading: false, next: null, unit: null })
      return undefined
    }
    let cancelled = false
    setState((previous) => ({ ...previous, loading: true }))
    getCourseTopics(courseId)
      .then((topics) => {
        if (cancelled) return
        for (const topic of topics) {
          const next = topic.subtopics.find((subtopic) => !subtopic.completed)
          if (next) {
            setState({ loading: false, next, unit: splitUnitName(topic.name) })
            return
          }
        }
        setState({ loading: false, next: null, unit: null })
      })
      .catch(() => {
        if (!cancelled) setState({ loading: false, next: null, unit: null })
      })
    return () => {
      cancelled = true
    }
  }, [courseId, completed])

  return state
}

/**
 * Lo primero que se ve: a dónde ir ahora. Un solo destino y un solo botón,
 * en la superficie azul de la marca para que no compita con nada más.
 */
function ContinueCard({ course }) {
  const { loading, next, unit } = useNextSubtopic(course)
  const percentage = Math.round(course.progress_percentage || 0)
  const started = percentage > 0
  const done = percentage >= 100

  return (
    <section
      aria-labelledby="continue-title"
      className="relative animate-rise-in overflow-hidden rounded-2xl bg-blue-900 p-6 text-white shadow-e3 sm:p-8"
    >
      <IrisMark className="-right-16 -top-16 h-64 w-64 text-white/[0.06] sm:-right-10 sm:h-72 sm:w-72" />

      <div className="relative">
        <p className="eyebrow text-blue-200">
          {done
            ? 'Temario completado'
            : started
              ? 'Continúa donde lo dejaste'
              : 'Tu siguiente paso'}
        </p>

        {loading ? (
          <div aria-hidden="true" className="mt-4 space-y-3">
            <div className="h-3.5 w-40 rounded bg-white/15" />
            <div className="h-7 w-4/5 rounded bg-white/20" />
            <div className="h-3 w-32 rounded bg-white/15" />
          </div>
        ) : (
          <div className="animate-fade-in">
            <p className="mt-3 text-[0.8125rem] text-blue-100">
              {course.name}
              {unit?.title && ` · Unidad ${unit.number ?? ''}`}
            </p>
            <h2
              id="continue-title"
              className="mt-2 max-w-[28ch] text-[1.375rem] font-bold leading-[1.2] tracking-[-0.02em] text-white sm:text-[1.75rem]"
            >
              {done ? 'Repasa lo que ya dominas' : next?.name || 'Abre el curso para empezar'}
            </h2>
            {next && !done && (
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-blue-100">
                {next.estimated_minutes > 0 && (
                  <span className="inline-flex items-center gap-1.5">
                    <FontAwesomeIcon icon={faClock} className="text-[0.65rem]" aria-hidden="true" />
                    {formatDuration(next.estimated_minutes)} de lectura
                  </span>
                )}
                {next.question_count > 0 && (
                  <span className="inline-flex items-center gap-1.5">
                    <FontAwesomeIcon
                      icon={faListCheck}
                      className="text-[0.65rem]"
                      aria-hidden="true"
                    />
                    {next.question_count} preguntas de repaso
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        <div className="mt-7 flex flex-wrap items-center justify-between gap-5 border-t border-white/15 pt-6">
          <div className="flex items-center gap-3.5">
            <ProgressRing value={percentage} size={52} stroke={5} tone="inverse" />
            <p className="text-[0.8125rem] leading-snug text-blue-100">
              <span className="tabular font-semibold text-white">
                {course.completed_subtopics} de {course.total_subtopics}
              </span>{' '}
              subtemas
              <br />
              del curso
            </p>
          </div>
          <Button
            as={Link}
            to={
              next && !done ? `/courses/${course.id}/subtopics/${next.id}` : `/courses/${course.id}`
            }
            variant="inverse"
            className="group/btn w-full sm:w-auto"
            iconRight={faArrowRight}
          >
            {done ? 'Repasar el curso' : started ? 'Continuar' : 'Empezar'}
          </Button>
        </div>
      </div>
    </section>
  )
}

function ContinueCardSkeleton() {
  return (
    <div aria-hidden="true" className="rounded-2xl bg-blue-900 p-6 sm:p-8">
      <div className="h-2.5 w-36 rounded bg-white/15" />
      <div className="mt-5 h-7 w-3/4 rounded bg-white/20" />
      <div className="mt-3 h-3 w-1/3 rounded bg-white/15" />
      <div className="mt-8 h-12 w-full rounded-xl bg-white/10" />
    </div>
  )
}

/** Resumen de avance: un anillo y tres cifras, sin más. */
function ProgressSummary({ overall, completed, total, courseCount }) {
  return (
    <section
      aria-labelledby="progress-title"
      className="animate-rise-in rounded-2xl border border-ink-200 bg-white p-6 shadow-e1"
      style={{ animationDelay: '80ms' }}
    >
      <h2 id="progress-title" className="text-base font-semibold tracking-[-0.01em] text-ink-900">
        Tu avance
      </h2>
      <div className="mt-5 flex items-center gap-5">
        <ProgressRing value={overall} size={84} stroke={7}>
          <span className="text-lg font-bold text-blue-900">
            <Counter to={overall} suffix="%" />
          </span>
        </ProgressRing>
        <p className="text-sm leading-relaxed text-ink-600">
          <span className="tabular font-semibold text-ink-900">
            {completed} de {total}
          </span>{' '}
          subtemas completados en {courseCount === 1 ? 'tu curso' : 'tus cursos'}.
        </p>
      </div>
      <dl className="mt-6 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-ink-50 px-4 py-3">
          <dt className="text-xs text-ink-500">Pendientes</dt>
          <dd className="tabular mt-1 text-xl font-bold text-ink-900">{total - completed}</dd>
        </div>
        <div className="rounded-xl bg-ink-50 px-4 py-3">
          <dt className="text-xs text-ink-500">{courseCount === 1 ? 'Curso' : 'Cursos'}</dt>
          <dd className="tabular mt-1 text-xl font-bold text-ink-900">{courseCount}</dd>
        </div>
      </dl>
    </section>
  )
}

/** Fila de curso: sobria, en lista, con el progreso como anillo a la izquierda. */
function CourseRow({ course, index }) {
  const percentage = Math.round(course.progress_percentage || 0)
  const isDone = percentage >= 100
  const isStarted = percentage > 0

  return (
    <li className="animate-rise-in" style={{ animationDelay: `${120 + index * 60}ms` }}>
      <Link
        to={`/courses/${course.id}`}
        className="group flex items-center gap-4 px-4 py-4 transition-colors duration-150 hover:bg-ink-50 sm:px-5"
      >
        {isDone ? (
          <span
            aria-hidden="true"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-correct-50 text-correct-700 ring-1 ring-inset ring-correct-200"
          >
            <FontAwesomeIcon icon={faCheck} />
          </span>
        ) : (
          <ProgressRing value={percentage} size={44} stroke={4} className="shrink-0" />
        )}

        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
            <span className="text-[0.9375rem] font-semibold leading-snug text-ink-900">
              {course.name}
            </span>
            {course.type === 'GENERAL' ? (
              <Badge tone="official">Oficial</Badge>
            ) : (
              course.code && <Badge tone="quiet">{course.code}</Badge>
            )}
          </span>
          <span className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1">
            <Meta icon={faLayerGroup}>{course.total_units} unidades</Meta>
            <Meta icon={faListCheck}>{course.total_subtopics} subtemas</Meta>
            {course.estimated_minutes > 0 && (
              <Meta icon={faClock}>{formatDuration(course.estimated_minutes)}</Meta>
            )}
          </span>
        </span>

        <span className="hidden shrink-0 text-[0.8125rem] font-semibold text-blue-800 sm:inline">
          {isDone ? 'Repasar' : isStarted ? 'Continuar' : 'Empezar'}
        </span>
        <FontAwesomeIcon
          icon={faChevronRight}
          aria-hidden="true"
          className="shrink-0 text-xs text-ink-300 transition-[transform,color] duration-200 ease-out group-hover:translate-x-1 group-hover:text-blue-800"
        />
      </Link>
    </li>
  )
}

function CourseRowSkeleton() {
  return (
    <li aria-hidden="true" className="flex items-center gap-4 px-4 py-4 sm:px-5">
      <div className="skeleton h-11 w-11 shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-4 w-1/2 rounded" />
        <div className="skeleton h-3 w-1/3 rounded" />
      </div>
    </li>
  )
}

/**
 * Unirse con código: es una acción ocasional, así que queda plegada en una
 * línea y se despliega en el sitio al pulsarla, sin modales.
 */
function JoinCourse({ onJoined }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (open) document.getElementById('course-code')?.focus()
  }, [open])

  if (open) {
    return (
      <div className="animate-scale-in">
        <JoinCourseForm onJoined={onJoined} />
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="mt-2 w-full rounded-lg py-2 text-xs font-semibold text-ink-500 transition-colors duration-150 hover:text-ink-900"
        >
          Ahora no
        </button>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setOpen(true)}
      className="group flex w-full items-center gap-3.5 rounded-2xl border border-dashed border-ink-300 bg-white/60 px-5 py-4 text-left transition-[border-color,background-color] duration-200 hover:border-blue-300 hover:bg-white"
    >
      <span
        aria-hidden="true"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-soft-lavender text-deep-lavender"
      >
        <FontAwesomeIcon icon={faKey} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-ink-900">
          ¿Tienes un código de curso?
        </span>
        <span className="block text-xs text-ink-500">Únete al curso de tu profesor</span>
      </span>
      <FontAwesomeIcon
        icon={faPlus}
        aria-hidden="true"
        className="text-sm text-ink-400 transition-[transform,color] duration-300 ease-out group-hover:rotate-90 group-hover:text-blue-800"
      />
    </button>
  )
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const { courses, loading, error, refresh } = useCourses()

  const totals = courses.reduce(
    (acc, course) => ({
      completed: acc.completed + (course.completed_subtopics || 0),
      subtopics: acc.subtopics + (course.total_subtopics || 0),
    }),
    { completed: 0, subtopics: 0 },
  )
  const overall = totals.subtopics ? Math.round((totals.completed / totals.subtopics) * 100) : 0
  const remaining = Math.max(0, totals.subtopics - totals.completed)
  const focus = pickFocusCourse(courses)

  return (
    // pb generoso: el botón flotante del asistente no debe tapar la última fila.
    <div className="mx-auto max-w-[72rem] px-5 pb-28 pt-8 sm:px-6 lg:px-10 lg:pb-16 lg:pt-12">
      <header className="flex items-center justify-between gap-8">
        <div className="min-w-0">
          <p className="eyebrow animate-fade-in text-ink-400">Panel del estudiante</p>
          <h1 className="mt-2.5 animate-rise-in text-[1.625rem] font-semibold leading-[1.15] tracking-[-0.02em] text-ink-900 sm:text-[2rem]">
            {greeting()}, {user?.name?.split(' ')[0]}
          </h1>
          {!loading && totals.subtopics > 0 && (
            <p className="mt-2 animate-fade-in text-[0.9375rem] leading-relaxed text-ink-600">
              {encouragement(overall, remaining)}
            </p>
          )}
        </div>

        {/* El ojo 3D solo cuando sobra ancho; por debajo de xl estorba. */}
        <div className="relative -my-6 hidden h-36 w-36 shrink-0 xl:block">
          <EyeScene className="h-full w-full" />
        </div>
      </header>

      {error && (
        <p className="mt-6 rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
          {error}
        </p>
      )}

      {/* En móvil el orden es el del DOM: continuar, avance, cursos, código.
          En escritorio el avance y el código se van a la columna derecha. */}
      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-8">
        <div className="min-w-0 lg:col-start-1 lg:row-start-1">
          {loading ? <ContinueCardSkeleton /> : focus && <ContinueCard course={focus} />}
        </div>

        {!loading && totals.subtopics > 0 && (
          <div className="lg:col-start-2 lg:row-start-1">
            <ProgressSummary
              overall={overall}
              completed={totals.completed}
              total={totals.subtopics}
              courseCount={courses.length}
            />
          </div>
        )}

        <section aria-labelledby="courses-title" className="min-w-0 lg:col-start-1 lg:row-start-2">
          <h2 id="courses-title" className="text-lg font-semibold tracking-[-0.01em] text-ink-900">
            Mis cursos
          </h2>

          {!loading && courses.length === 0 && !error ? (
            <div className="mt-4 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
              <h3 className="text-lg font-semibold text-ink-900">Todavía no tienes cursos</h3>
              <p className="mx-auto mt-2 max-w-[42ch] text-sm leading-relaxed text-ink-500">
                Al registrarte deberías tener acceso al Curso General de Oftalmología. Si no
                aparece, vuelve a cargar la página o únete con el código de tu facultad.
              </p>
              <Button onClick={refresh} variant="secondary" size="sm" className="mt-5">
                Volver a cargar
              </Button>
            </div>
          ) : (
            <ul className="mt-4 divide-y divide-ink-200 overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-e1">
              {loading
                ? [0, 1].map((i) => <CourseRowSkeleton key={i} />)
                : courses.map((course, index) => (
                    <CourseRow key={course.id} course={course} index={index} />
                  ))}
            </ul>
          )}
        </section>

        <div className={cn('lg:col-start-2 lg:row-start-2 lg:self-start', 'lg:pt-[2.625rem]')}>
          <JoinCourse onJoined={refresh} />
        </div>
      </div>
    </div>
  )
}
