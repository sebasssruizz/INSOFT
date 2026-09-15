import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight,
  faCircleCheck,
  faClock,
  faLayerGroup,
  faListCheck,
} from '@fortawesome/free-solid-svg-icons'

import EyeScene from '../components/three/LazyEyeScene'
import JoinCourseForm from '../components/JoinCourseForm'
import { Badge, Meta } from '../components/ui/Meta'
import { Button } from '../components/ui/Button'
import { Counter } from '../components/ui/Counter'
import { ProgressBar } from '../components/ui/Progress'
import { formatDuration } from '../lib/curriculum'
import { cn } from '../lib/utils'
import { useAuth } from '../hooks/useAuth'
import { useCourses } from '../hooks/useCourses'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Buenos días'
  if (hour < 20) return 'Buenas tardes'
  return 'Buenas noches'
}

function CourseCard({ course, index }) {
  const percentage = Math.round(course.progress_percentage || 0)
  const isGeneral = course.type === 'GENERAL'
  const isDone = percentage >= 100
  const isStarted = percentage > 0

  return (
    <Link
      to={`/courses/${course.id}`}
      className={cn(
        'group animate-rise-in relative flex flex-col rounded-2xl border border-ink-200 bg-white p-5 sm:p-6',
        'shadow-e1 transition-[transform,box-shadow,border-color] duration-200 ease-out',
        'hover:-translate-y-1 hover:border-blue-300 hover:shadow-e3',
      )}
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div className="flex items-start justify-between gap-4">
        <span
          className={cn(
            'flex h-12 w-12 items-center justify-center rounded-2xl text-lg transition-transform duration-200 ease-out group-hover:scale-105',
            isDone ? 'bg-soft-mint text-deep-mint' : 'bg-soft-sky text-deep-sky',
          )}
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={isDone ? faCircleCheck : faLayerGroup} />
        </span>
        {isGeneral ? (
          <Badge tone="official">Oficial</Badge>
        ) : (
          course.code && <Badge tone="quiet">{course.code}</Badge>
        )}
      </div>

      <h3 className="mt-5 text-[1.375rem] font-semibold leading-snug tracking-[-0.01em] text-ink-900">
        {course.name}
      </h3>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
        <Meta icon={faLayerGroup}>{course.total_units} unidades</Meta>
        <Meta icon={faListCheck}>{course.total_subtopics} subtemas</Meta>
        <Meta icon={faClock}>{formatDuration(course.estimated_minutes)}</Meta>
      </div>

      <div className="mt-auto pt-6">
        {isDone ? (
          <p className="flex items-center gap-2 text-sm font-semibold text-deep-mint">
            <FontAwesomeIcon icon={faCircleCheck} aria-hidden="true" />
            Temario completado
          </p>
        ) : (
          <ProgressBar
            value={percentage}
            label={`${course.completed_subtopics} de ${course.total_subtopics} subtemas`}
          />
        )}

        <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-blue-800">
          {isDone ? 'Repasar el curso' : isStarted ? 'Continuar estudiando' : 'Empezar el curso'}
          <FontAwesomeIcon
            icon={faArrowRight}
            className="transition-transform duration-200 ease-out group-hover:translate-x-1"
            aria-hidden="true"
          />
        </span>
      </div>
    </Link>
  )
}

function CourseCardSkeleton() {
  return (
    <div className="rounded-2xl border border-ink-200 bg-white p-6">
      <div className="skeleton h-12 w-12 rounded-xl" />
      <div className="skeleton mt-5 h-6 w-3/4 rounded" />
      <div className="skeleton mt-3 h-3 w-1/2 rounded" />
      <div className="skeleton mt-10 h-1.5 w-full rounded-full" />
    </div>
  )
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const { courses, loading, error, refresh } = useCourses()

  const totals = courses.reduce(
    (acc, course) => ({
      completed: acc.completed + (course.completed_subtopics || 0),
      subtopics: acc.subtopics + (course.total_subtopics || 0),
      minutes: acc.minutes + (course.estimated_minutes || 0),
    }),
    { completed: 0, subtopics: 0, minutes: 0 },
  )
  const overall = totals.subtopics ? Math.round((totals.completed / totals.subtopics) * 100) : 0
  const remaining = Math.max(0, totals.subtopics - totals.completed)

  return (
    <div>
      {/* Cabecera: estado global de estudio sobre una superficie tranquila */}
      <header className="relative overflow-hidden border-b border-ink-200 bg-gradient-to-br from-soft-sky via-ink-50 to-soft-lavender">
        <div className="relative mx-auto flex max-w-[78rem] items-center gap-12 px-5 py-10 sm:px-6 lg:px-10 lg:py-16">
          <div className="min-w-0 flex-1">
            <p className="eyebrow text-deep-sky">Panel del estudiante</p>
            <h1 className="mt-3.5 text-[1.625rem] font-semibold leading-[1.12] tracking-[-0.02em] text-ink-900 sm:text-[2rem] lg:text-[2.75rem]">
              {greeting()}, {user?.name?.split(' ')[0]}
            </h1>

            {!loading && totals.subtopics > 0 && (
              <>
                <p className="mt-4 max-w-[46ch] text-[0.9375rem] leading-relaxed text-ink-600">
                  {remaining === 0
                    ? 'Has completado todo el temario disponible. Repasa cuando quieras.'
                    : `Te quedan ${remaining} ${remaining === 1 ? 'subtema' : 'subtemas'} por estudiar.`}
                </p>

                {/* Rejilla de tres, no fila flexible: en móvil las tres cifras
                    caben en una línea y no dejan una huérfana debajo. */}
                <dl className="mt-7 grid max-w-md grid-cols-3 gap-x-4 lg:mt-9 lg:max-w-2xl lg:gap-x-12">
                  {[
                    { value: overall, suffix: '%', label: 'Del temario', tone: 'text-blue-900' },
                    { value: totals.completed, label: 'Subtemas hechos', tone: 'text-deep-mint' },
                    {
                      value: courses.length,
                      label: courses.length === 1 ? 'Curso' : 'Cursos',
                      tone: 'text-deep-lavender',
                    },
                  ].map((stat) => (
                    <div key={stat.label} className="min-w-0">
                      <dd
                        className={cn(
                          'tabular text-[1.75rem] font-semibold leading-none sm:text-[2.25rem] lg:text-[2.75rem]',
                          stat.tone,
                        )}
                      >
                        <Counter to={stat.value} suffix={stat.suffix} />
                      </dd>
                      <dt className="eyebrow mt-2 text-ink-500">{stat.label}</dt>
                    </div>
                  ))}
                </dl>

                <ProgressBar value={overall} className="mt-7 max-w-md lg:mt-9" />
              </>
            )}
          </div>

          {/* Halo pastel: el ojo es casi blanco y necesita separarse del fondo.
              Solo aparece cuando sobra ancho de verdad; por debajo estorba. */}
          <div className="relative hidden h-64 w-64 shrink-0 xl:block xl:h-72 xl:w-72">
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgb(255_255_255_/_0.9)_38%,transparent_70%)]"
            />
            <EyeScene className="relative h-full w-full" />
          </div>
        </div>
      </header>

      {/* pb generoso: el botón flotante del asistente no debe tapar la última fila. */}
      <main className="mx-auto max-w-[78rem] px-5 py-10 pb-28 sm:px-6 lg:px-10 lg:py-16 lg:pb-20">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-12">
          <section>
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink-900">Mis cursos</h2>
              {!loading && courses.length > 0 && (
                <span className="tabular text-xs font-medium text-ink-500">
                  {formatDuration(totals.minutes)} de estudio en total
                </span>
              )}
            </div>

            {error && (
              <p className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
                {error}
              </p>
            )}

            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              {loading && [0, 1].map((i) => <CourseCardSkeleton key={i} />)}
              {!loading &&
                courses.map((course, index) => (
                  <CourseCard key={course.id} course={course} index={index} />
                ))}
            </div>

            {!loading && courses.length === 0 && !error && (
              <div className="mt-5 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
                <h3 className="text-lg font-semibold text-ink-900">Todavía no tienes cursos</h3>
                <p className="mx-auto mt-2 max-w-[42ch] text-sm leading-relaxed text-ink-500">
                  Al registrarte deberías tener acceso al Curso General de Oftalmología. Si no
                  aparece, vuelve a cargar la página o únete con el código de tu facultad.
                </p>
                <Button onClick={refresh} variant="secondary" size="sm" className="mt-5">
                  Volver a cargar
                </Button>
              </div>
            )}
          </section>

          <aside className="lg:sticky lg:top-8 lg:self-start">
            <JoinCourseForm onJoined={refresh} />
          </aside>
        </div>
      </main>
    </div>
  )
}
