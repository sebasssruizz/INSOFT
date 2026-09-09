import { Link, Outlet, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faClock, faLayerGroup, faListCheck } from '@fortawesome/free-solid-svg-icons'

import ContentRail from '../../components/course/ContentRail'
import { Badge, Meta } from '../../components/ui/Meta'
import { Button } from '../../components/ui/Button'
import { formatDuration } from '../../lib/curriculum'
import { useAuth } from '../../hooks/useAuth'
import { CourseProvider, useCourse } from '../../hooks/useCourse'

function CourseHeader() {
  const { user } = useAuth()
  const isStudent = user?.role === 'STUDENT'
  const {
    course,
    courseId,
    percentage,
    totalSubtopics,
    completedSubtopics,
    totalMinutes,
    topics,
    totalQuestions,
    nextSubtopic,
    remainingMinutes,
  } = useCourse()

  return (
    <header className="sticky top-0 z-10 border-b border-ink-200 bg-white/95 backdrop-blur">
      <div className="mx-auto max-w-[82rem] px-6 pb-5 pt-5 lg:px-10">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
        >
          <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
          Mis cursos
        </Link>

        <div className="mt-3 flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2.5">
              {course?.type === 'GENERAL' ? (
                <Badge tone="official">Contenido oficial</Badge>
              ) : (
                course?.code && <Badge tone="quiet">{course.code}</Badge>
              )}
            </div>
            <h1 className="mt-2.5 text-[1.75rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900 lg:text-[2rem]">
              {course?.name}
            </h1>
            <div className="mt-2.5 flex flex-wrap items-center gap-x-5 gap-y-1.5">
              <Meta icon={faLayerGroup}>{topics.length} unidades</Meta>
              <Meta icon={faListCheck}>{totalSubtopics} subtemas</Meta>
              <Meta icon={faClock}>{formatDuration(totalMinutes)}</Meta>
              {totalQuestions > 0 && <Meta>{totalQuestions} preguntas de repaso</Meta>}
            </div>
          </div>

          <div className="flex items-center gap-5">
            {isStudent && (
              <div className="text-right">
                <p className="tabular font-display text-[2rem] font-semibold leading-none text-blue-800">
                  {percentage}%
                </p>
                <p className="tabular mt-1 text-xs text-ink-500">
                  {completedSubtopics} de {totalSubtopics}
                </p>
              </div>
            )}

            {nextSubtopic && (
              <Button
                as={Link}
                to={`/courses/${courseId}/subtopics/${nextSubtopic.id}`}
                size="md"
                className="group/btn"
              >
                {!isStudent ? 'Ver contenido' : completedSubtopics > 0 ? 'Continuar' : 'Empezar'}
              </Button>
            )}
          </div>
        </div>

        {isStudent && remainingMinutes > 0 && completedSubtopics > 0 && (
          <p className="tabular mt-3 text-xs text-ink-500">
            Te quedan unos {formatDuration(remainingMinutes)} de estudio.
          </p>
        )}
      </div>

      {/* El borde inferior de la cabecera ES la barra de progreso del curso:
          se llena a medida que se completan subtemas dentro. */}
      {isStudent && (
        <div className="h-[3px] w-full bg-ink-200">
          <div
            role="progressbar"
            aria-label="Progreso del curso"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            className="h-full w-full origin-left bg-blue-900 transition-transform duration-700 ease-out"
            style={{ transform: `scaleX(${percentage / 100})` }}
          />
        </div>
      )}
    </header>
  )
}

function CourseBody() {
  const { loading, error, refresh } = useCourse()

  if (error) {
    return (
      <div className="mx-auto max-w-[82rem] px-6 py-16 lg:px-10">
        <div className="mx-auto max-w-md rounded-2xl border border-wrong-200 bg-wrong-50 px-6 py-8 text-center">
          <h2 className="text-lg font-semibold text-wrong-700">No se pudo abrir el curso</h2>
          <p className="mt-2 text-sm text-wrong-700/80">{error}</p>
          <Button onClick={refresh} variant="secondary" size="sm" className="mt-5">
            Reintentar
          </Button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-[82rem] px-6 py-10 lg:px-10">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_21rem]">
          <div className="space-y-4">
            <div className="skeleton h-8 w-1/2 rounded" />
            <div className="skeleton h-64 w-full rounded-2xl" />
          </div>
          <div className="skeleton h-96 w-full rounded-2xl" />
        </div>
      </div>
    )
  }

  return (
    <>
      <CourseHeader />
      <div className="mx-auto max-w-[82rem] px-6 py-8 lg:px-10">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_21rem] lg:items-start">
          <main className="min-w-0">
            <Outlet />
          </main>
          <ContentRail className="lg:sticky lg:top-[13.5rem]" />
        </div>
      </div>
    </>
  )
}

export default function CourseShell() {
  const { courseId } = useParams()
  return (
    <CourseProvider courseId={courseId}>
      <CourseBody />
    </CourseProvider>
  )
}
