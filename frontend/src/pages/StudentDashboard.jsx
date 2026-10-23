import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight,
  faCheck,
  faChevronRight,
  faKey,
  faListCheck,
  faPlus,
} from '@fortawesome/free-solid-svg-icons'

import JoinCourseForm from '../components/JoinCourseForm'
import { Badge } from '../components/ui/Meta'
import { Button } from '../components/ui/Button'
import { IrisMark } from '../components/ui/IrisMark'
import { ProgressBar, ProgressRing } from '../components/ui/Progress'
import { splitUnitName, unitIdentity } from '../lib/curriculum'
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

/** Temario completo del curso en foco: unidades, subtemas y su estado. */
function useFocusTopics(course) {
  const [state, setState] = useState({ loading: true, topics: [] })
  const courseId = course?.id
  const completed = course?.completed_subtopics

  useEffect(() => {
    if (!courseId) {
      setState({ loading: false, topics: [] })
      return undefined
    }
    let cancelled = false
    setState((previous) => ({ ...previous, loading: true }))
    getCourseTopics(courseId)
      .then((topics) => !cancelled && setState({ loading: false, topics }))
      .catch(() => !cancelled && setState({ loading: false, topics: [] }))
    return () => {
      cancelled = true
    }
  }, [courseId, completed])

  return state
}

/** Unidad en curso (la primera con algo pendiente) y su siguiente subtema. */
function locate(topics) {
  for (let index = 0; index < topics.length; index += 1) {
    const next = topics[index].subtopics.find((subtopic) => !subtopic.completed)
    if (next) return { index, topic: topics[index], next }
  }
  const last = topics.length - 1
  return { index: Math.max(0, last), topic: topics[last] || null, next: null }
}

/* ------------------------------------------------------------------------ */
/* Portada del panel                                                         */
/* ------------------------------------------------------------------------ */

function headline(course) {
  const done = course?.completed_subtopics || 0
  const total = course?.total_subtopics || 0
  if (total && done >= total) return ['Completaste', 'todo el', 'temario']
  if (done === 0) return ['Tu primera', 'unidad te', 'está esperando']
  return [`Llevas ${done} de ${total}`, 'subtemas', 'completados']
}

/**
 * Tarjeta de unidad, alta y de color, con su icono grande recortado en la
 * esquina a modo de ilustración. La unidad en curso va en azul de acción.
 */
function UnitCard({ topic, courseId, current, index }) {
  const { number, title } = splitUnitName(topic.name)
  const identity = unitIdentity(topic.order ?? index)
  const done = topic.subtopics.filter((subtopic) => subtopic.completed).length
  const total = topic.subtopics.length
  const complete = total > 0 && done === total

  return (
    <Link
      to={`/courses/${courseId}/units/${topic.id}`}
      className={cn(
        'group relative flex h-[13.5rem] w-[11.5rem] shrink-0 snap-start flex-col overflow-hidden rounded-2xl p-5 sm:h-[15rem] sm:w-[12.5rem] xl:w-[10.5rem] 2xl:w-[12.5rem]',
        'animate-rise-in transition-[transform,box-shadow] duration-300 ease-out hover:-translate-y-1 hover:shadow-e3',
        current ? 'bg-blue-900 text-white' : identity.classes.soft,
      )}
      style={{ animationDelay: `${120 + index * 80}ms` }}
    >
      <span
        className={cn(
          'tabular flex items-center justify-between text-[0.8125rem] font-bold',
          current ? 'text-blue-200' : identity.classes.text,
        )}
      >
        {String(number ?? index + 1).padStart(2, '0')}
        {complete ? (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-[0.65rem] text-correct-700">
            <FontAwesomeIcon icon={faCheck} aria-hidden="true" />
          </span>
        ) : (
          current && (
            <span className="rounded-full bg-white/15 px-2 py-0.5 text-[0.625rem] uppercase tracking-[0.08em] text-white">
              En curso
            </span>
          )
        )}
      </span>
      <span
        className={cn(
          'relative z-10 mt-3 line-clamp-3 text-[1.0625rem] font-semibold leading-[1.2] tracking-[-0.01em] sm:text-[1.1875rem]',
          current ? 'text-white' : 'text-ink-900',
        )}
      >
        {title}
      </span>
      <span
        className={cn(
          'tabular relative z-10 mt-auto text-xs font-medium',
          current ? 'text-blue-100' : 'text-ink-600',
        )}
      >
        {done}/{total} subtemas
      </span>

      {/* Ilustración: el icono de la unidad, grande y recortado. */}
      <FontAwesomeIcon
        icon={identity.icon}
        aria-hidden="true"
        className={cn(
          'absolute -bottom-5 -right-5 text-[7.5rem] transition-transform duration-500 ease-out group-hover:-rotate-6 group-hover:scale-105',
          current ? 'text-white/[0.12]' : cn(identity.classes.text, 'opacity-[0.16]'),
        )}
      />
      {current && <IrisMark className="-left-10 -top-10 h-32 w-32 text-white/[0.06]" />}
    </Link>
  )
}

function Hero({ user, course, topics, loading }) {
  const { index, next } = locate(topics)
  // La unidad en curso y las dos siguientes; al final del temario, las tres últimas.
  const start = Math.max(0, Math.min(index, topics.length - 3))
  const strip = topics.slice(start, start + 3)
  const lines = headline(course)
  const done =
    course && course.total_subtopics && course.completed_subtopics >= course.total_subtopics

  return (
    <section
      aria-labelledby="hero-title"
      className="relative overflow-hidden rounded-2xl bg-ink-100 xl:grid xl:grid-cols-[minmax(0,1fr)_auto]"
    >
      <div className="relative flex flex-col p-6 sm:p-8 xl:py-10 xl:pl-10">
        <p className="animate-fade-in text-[0.9375rem] font-medium text-ink-700">
          {greeting()}, {user?.name?.split(' ')[0]}
        </p>
        <h1
          id="hero-title"
          className="mt-4 animate-rise-in text-[1.75rem] font-semibold min-[375px]:text-[2rem] leading-[1.08] tracking-[-0.03em] text-ink-900 sm:text-[2.5rem] 2xl:text-[2.875rem]"
        >
          {lines.map((line) => (
            <span key={line} className="block">
              {line}
            </span>
          ))}
        </h1>

        {course && (
          <div className="mt-7 xl:mt-auto xl:pt-8">
            {next && !done && (
<>{/* Conserva el próximo contenido y sus preguntas de repaso. */}
              <p className="mb-3 max-w-[34ch] text-[0.8125rem] leading-snug text-ink-600">
                Sigue: <span className="font-semibold text-ink-900">{next.name}</span>
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-600">
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
</>
            )}
            <Button
              as={Link}
              to={
                next && !done
                  ? `/courses/${course.id}/subtopics/${next.id}`
                  : `/courses/${course.id}`
              }
              size="lg"
              iconRight={faArrowRight}
              className="group/btn w-full sm:w-auto"
            >
              {done ? 'Repasar el curso' : course.completed_subtopics > 0 ? 'Continuar' : 'Empezar'}
            </Button>
          </div>
        )}
      </div>

      {/* Tira de unidades. En móvil se desliza con el dedo; en escritorio
          sangra hasta el borde derecho como en un tablero de lecciones. */}
      <div className="no-scrollbar -mt-1 flex snap-x snap-mandatory scroll-px-6 gap-3 overflow-x-auto overscroll-x-contain px-6 pb-6 sm:scroll-px-8 sm:px-8 sm:pb-8 xl:mt-0 xl:items-center xl:overflow-visible xl:py-8 xl:pl-0 xl:pr-8">
        {loading
          ? [0, 1, 2].map((i) => (
              <div
                key={i}
                className="skeleton h-[13.5rem] w-[11.5rem] shrink-0 rounded-2xl sm:h-[15rem] sm:w-[12.5rem] xl:w-[10.5rem] 2xl:w-[12.5rem]"
              />
            ))
          : strip.map((topic, i) => (
              <UnitCard
                key={topic.id}
                topic={topic}
                courseId={course.id}
                index={i}
                current={start + i === index && !done}
              />
            ))}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------------ */
/* Unidad en curso                                                           */
/* ------------------------------------------------------------------------ */

/**
 * Subtemas de la unidad en curso como un recorrido vertical: cuadros unidos
 * por una línea, con un sello de completado y el siguiente resaltado.
 */
function CurrentUnit({ course, topics, loading }) {
  const { topic, next } = locate(topics)

  if (loading) {
    return (
      <div aria-hidden="true" className="space-y-4">
        <div className="skeleton h-4 w-24 rounded" />
        <div className="skeleton h-7 w-2/3 rounded" />
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="skeleton h-12 w-12 rounded-xl" />
            <div className="skeleton h-4 flex-1 rounded" />
          </div>
        ))}
      </div>
    )
  }
  if (!topic) return null

  const { number, title } = splitUnitName(topic.name)
  const done = topic.subtopics.filter((subtopic) => subtopic.completed).length
  const total = topic.subtopics.length
  const percentage = total ? Math.round((done / total) * 100) : 0

  return (
    <section
      aria-labelledby="unit-title"
      className="animate-rise-in"
      style={{ animationDelay: '160ms' }}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-8">
        <div className="min-w-0">
          <p className="text-[0.8125rem] font-medium text-ink-500">Unidad {number}</p>
          <h2
            id="unit-title"
            className="mt-1 text-[1.375rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900 sm:text-[1.625rem]"
          >
            {title}
          </h2>
        </div>
        <ProgressBar
          value={percentage}
          size="lg"
          showValue
          className="w-full shrink-0 sm:w-[15rem]"
          ariaLabel={`Progreso de la unidad ${number}`}
        />
      </div>

      <ol className="mt-7">
        {topic.subtopics.map((subtopic, i) => {
          const isNext = next?.id === subtopic.id
          const isLast = i === topic.subtopics.length - 1
          return (
            <li key={subtopic.id} className="relative">
              {/* Tramo de línea hasta el siguiente cuadro. */}
              {!isLast && (
                <span
                  aria-hidden="true"
                  className={cn(
                    'absolute left-6 top-12 h-[calc(100%-3rem)] w-px -translate-x-1/2',
                    subtopic.completed ? 'bg-blue-900' : 'bg-ink-300',
                  )}
                />
              )}
              <Link
                to={`/courses/${course.id}/subtopics/${subtopic.id}`}
                className="group grid grid-cols-[3rem_minmax(0,1fr)_auto] items-center gap-x-4 rounded-xl py-3 pr-2 transition-colors duration-150 hover:bg-white sm:grid-cols-[3rem_minmax(0,1fr)_12rem_auto] sm:pr-3"
              >
                <span
                  className={cn(
                    'tabular relative flex h-12 w-12 items-center justify-center rounded-xl text-sm font-bold transition-transform duration-200 ease-out group-hover:scale-105',
                    isNext
                      ? 'bg-blue-900 text-white shadow-blue-glow'
                      : subtopic.completed
                        ? 'border border-blue-900/20 bg-white text-blue-900'
                        : 'border border-ink-200 bg-white text-ink-400',
                  )}
                >
                  {String(i + 1).padStart(2, '0')}
                  {subtopic.completed && (
                    <span className="absolute -bottom-2 left-1/2 flex h-5 w-5 -translate-x-1/2 items-center justify-center rounded-full bg-blue-900 text-[0.55rem] text-white ring-2 ring-ink-50">
                      <FontAwesomeIcon icon={faCheck} aria-hidden="true" />
                    </span>
                  )}
                  {isNext && (
                    <span className="absolute -inset-1 rounded-[0.9rem] ring-4 ring-blue-100" />
                  )}
                </span>

                <span className="min-w-0">
                  <span
                    className={cn(
                      'block text-[0.9375rem] font-semibold leading-snug',
                      subtopic.completed || isNext ? 'text-ink-900' : 'text-ink-600',
                    )}
                  >
                    {subtopic.name}
                  </span>
                  {isNext && (
                    <span className="mt-0.5 block text-xs font-semibold text-blue-800">
                      Tu siguiente lectura
                    </span>
                  )}
                </span>

                <span className="hidden flex-col gap-0.5 text-[0.8125rem] text-ink-500 sm:flex">
                  {subtopic.question_count > 0 && (
                    <span className="tabular inline-flex items-center gap-1.5">
                      <FontAwesomeIcon icon={faListCheck} className="text-[0.65rem] text-ink-400" />
                      {subtopic.question_count} preguntas
                    </span>
                  )}
                </span>

                <FontAwesomeIcon
                  icon={faChevronRight}
                  aria-hidden="true"
                  className="text-xs text-ink-300 transition-[transform,color] duration-200 ease-out group-hover:translate-x-1 group-hover:text-blue-800"
                />
              </Link>
            </li>
          )
        })}
      </ol>

      <Link
        to={`/courses/${course.id}/units/${topic.id}`}
        className="mt-4 inline-flex items-center gap-2 text-[0.8125rem] font-semibold text-blue-800 transition-colors duration-150 hover:text-blue-900"
      >
        Ver la unidad completa
        <FontAwesomeIcon icon={faArrowRight} className="text-[0.7rem]" aria-hidden="true" />
      </Link>
    </section>
  )
}

/* ------------------------------------------------------------------------ */
/* Columna lateral                                                           */
/* ------------------------------------------------------------------------ */

/** Repaso de la unidad en curso: la llamada destacada de la columna. */
function QuizCallout({ course, topics }) {
  const { topic } = locate(topics)
  if (!topic || !topic.question_count) return null
  const { number } = splitUnitName(topic.name)

  return (
    <section
      className="relative animate-rise-in overflow-hidden rounded-2xl bg-soft-butter p-6"
      style={{ animationDelay: '220ms' }}
    >
      <span
        aria-hidden="true"
        className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-deep-butter shadow-e1"
      >
        <FontAwesomeIcon icon={faListCheck} />
      </span>
      <h2 className="mt-4 text-[1.25rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
        Ponte a prueba con la Unidad {number}
      </h2>
      <p className="tabular mt-1.5 text-[0.8125rem] text-ink-600">
        {topic.question_count} preguntas de repaso con respuesta inmediata.
      </p>
      <Button
        as={Link}
        to={`/courses/${course.id}/units/${topic.id}/quiz`}
        variant="secondary"
        size="sm"
        iconRight={faArrowRight}
        className="group/btn mt-5 w-full justify-between"
      >
        Hacer el repaso
      </Button>
    </section>
  )
}

function CourseItem({ course, index }) {
  const percentage = Math.round(course.progress_percentage || 0)
  const isDone = percentage >= 100
  return (
    <li className="animate-rise-in" style={{ animationDelay: `${260 + index * 60}ms` }}>
      <Link
        to={`/courses/${course.id}`}
        className="group block rounded-xl bg-ink-100 p-4 transition-[background-color,transform] duration-200 ease-out hover:-translate-y-0.5 hover:bg-white hover:shadow-e2"
      >
        <span className="mb-3 flex items-center gap-3">
          {isDone ? (
            <span aria-label="Curso completado" className="flex h-11 w-11 items-center justify-center rounded-full bg-correct-50 text-correct-700">
              <FontAwesomeIcon icon={faCheck} aria-hidden="true" />
            </span>
          ) : (
            <ProgressRing value={percentage} size={44} stroke={4} className="shrink-0" />
          )}
          <span className="tabular text-xs text-ink-500">
            {course.total_units} unidades · {course.total_subtopics} subtemas
          </span>
        </span>
        <span className="flex items-start justify-between gap-3">
          <span className="text-[0.9375rem] font-semibold leading-snug text-ink-900">
            {course.name}
          </span>
          {course.type === 'GENERAL' ? (
            <Badge tone="official" className="shrink-0">
              Oficial
            </Badge>
          ) : (
            course.code && (
              <Badge tone="quiet" className="shrink-0">
                {course.code}
              </Badge>
            )
          )}
        </span>
        <span className="tabular mt-1.5 block text-[0.8125rem] text-ink-500">
          {course.completed_subtopics} de {course.total_subtopics} subtemas
        </span>
        <ProgressBar value={percentage} size="sm" className="mt-3" />
      </Link>
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
      className="group flex w-full items-center gap-3.5 rounded-xl border border-dashed border-ink-300 px-4 py-3.5 text-left transition-[border-color,background-color] duration-200 hover:border-blue-300 hover:bg-white"
    >
      <span
        aria-hidden="true"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-soft-lavender text-sm text-deep-lavender"
      >
        <FontAwesomeIcon icon={faKey} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-ink-900">¿Tienes un código?</span>
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
  const focus = pickFocusCourse(courses)
  const { loading: topicsLoading, topics } = useFocusTopics(focus)
  const busy = loading || (focus && topicsLoading && topics.length === 0)

  return (
    // pb generoso: el botón flotante de Sofía no debe tapar el último elemento.
    <div className="mx-auto max-w-[78rem] px-4 pb-28 pt-5 sm:px-6 sm:pt-8 lg:px-10 lg:pb-16 lg:pt-10">
      {error && (
        <p className="mb-6 rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
          {error}
        </p>
      )}

      {!loading && courses.length === 0 && !error ? (
        <div className="rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
          <h1 className="text-lg font-semibold text-ink-900">Todavía no tienes cursos</h1>
          <p className="mx-auto mt-2 max-w-[42ch] text-sm leading-relaxed text-ink-500">
            Al registrarte deberías tener acceso al Curso General de Oftalmología. Si no aparece,
            vuelve a cargar la página o únete con el código de tu facultad.
          </p>
          <Button onClick={refresh} variant="secondary" size="sm" className="mt-5">
            Volver a cargar
          </Button>
          <div className="mx-auto mt-6 max-w-sm text-left">
            <JoinCourse onJoined={refresh} />
          </div>
        </div>
      ) : (
        <>
          <Hero user={user} course={focus} topics={topics} loading={busy} />

          <div className="mt-8 grid gap-10 lg:mt-10 xl:grid-cols-[minmax(0,1fr)_20rem] xl:gap-0">
            <div className="min-w-0 xl:border-r xl:border-ink-200 xl:pr-10">
              {focus && <CurrentUnit course={focus} topics={topics} loading={busy} />}
            </div>

            <aside className="grid gap-8 md:grid-cols-2 md:items-start xl:block xl:space-y-8 xl:pl-10">
              {focus && !busy && <QuizCallout course={focus} topics={topics} />}

              <section aria-labelledby="courses-title">
                <h2
                  id="courses-title"
                  className="text-[1.25rem] font-semibold tracking-[-0.02em] text-ink-900"
                >
                  Mis cursos
                </h2>
                <ul className="mt-4 space-y-3">
                  {loading
                    ? [0, 1].map((i) => <li key={i} className="skeleton h-28 rounded-xl" />)
                    : courses.map((course, index) => (
                        <CourseItem key={course.id} course={course} index={index} />
                      ))}
                </ul>
                <div className="mt-3">
                  <JoinCourse onJoined={refresh} />
                </div>
              </section>
            </aside>
          </div>
        </>
      )}
    </div>
  )
}
