import { Link, Outlet, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faClock, faLayerGroup, faListCheck } from '@fortawesome/free-solid-svg-icons'

import ContentRail from '../../components/course/ContentRail'
import CourseProgress from '../../components/course/CourseProgress'
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
  } = useCourse()

  return (
    // Anclada solo en escritorio: en móvil la cabecera ocupa media pantalla y
    // quedaría además debajo de la barra superior de la aplicación.
    <header className="relative z-10 border-b border-ink-200 bg-white/95 backdrop-blur lg:sticky lg:top-0">
      <div className="mx-auto max-w-[82rem] px-5 pb-4 pt-4 sm:px-6 lg:px-10 lg:pb-5 lg:pt-5">
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
            <h1 className="mt-2.5 text-[1.375rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900 sm:text-[1.75rem] lg:text-[2rem]">
              {course?.name}
            </h1>
            <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 sm:gap-x-5">
              <Meta icon={faLayerGroup}>{topics.length} unidades</Meta>
              <Meta icon={faListCheck}>{totalSubtopics} subtemas</Meta>
              <Meta icon={faClock}>{formatDuration(totalMinutes)}</Meta>
              {totalQuestions > 0 && <Meta>{totalQuestions} preguntas de repaso</Meta>}
            </div>
          </div>

          {nextSubtopic && (
            <Button
              as={Link}
              to={`/courses/${courseId}/subtopics/${nextSubtopic.id}`}
              size="md"
              className="group/btn w-full sm:w-auto"
            >
              {!isStudent ? 'Ver contenido' : completedSubtopics > 0 ? 'Continuar' : 'Empezar'}
            </Button>
          )}
        </div>

        {isStudent && topics.length > 0 && (
          <CourseProgress
            className="mt-4"
            topics={topics}
            courseId={courseId}
            percentage={percentage}
            completed={completedSubtopics}
            total={totalSubtopics}
            nextSubtopic={nextSubtopic}
          />
        )}
      </div>
    </header>
  )
}

function CourseBody() {
  const { loading, error, refresh } = useCourse()

  if (error) {
    return (
      <div className="mx-auto max-w-[82rem] px-5 py-16 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-md rounded-2xl border border-wrong-200 bg-wrong-50 px-5 py-8 text-center sm:px-6">
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
      <div className="mx-auto max-w-[82rem] px-5 py-10 sm:px-6 lg:px-10">
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
      <div className="mx-auto max-w-[82rem] px-5 py-7 pb-28 sm:px-6 lg:px-10 lg:py-8 lg:pb-12">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_21rem] lg:items-start">
          <main className="min-w-0">
            <Outlet />
          </main>
          <ContentRail className="lg:sticky lg:top-[16.5rem]" />
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
