import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck, faClock, faListCheck } from '@fortawesome/free-solid-svg-icons'

import { Meta } from '../../components/ui/Meta'
import { cn } from '../../lib/utils'
import { formatDuration, splitUnitName, unitIdentity } from '../../lib/curriculum'
import { useAuth } from '../../hooks/useAuth'
import { useCourse } from '../../hooks/useCourse'

function UnitCard({ topic, courseId, index, isStudent }) {
  const { number, title } = splitUnitName(topic.name)
  const identity = unitIdentity(topic.order)
  const total = topic.subtopics.length
  const done = topic.subtopics.filter((subtopic) => subtopic.completed).length
  const percentage = total ? Math.round((done / total) * 100) : 0
  const isComplete = total > 0 && done === total
  const isStarted = done > 0

  return (
    <Link
      to={`/courses/${courseId}/units/${topic.id}`}
      className={cn(
        'group animate-rise-in relative flex flex-col rounded-2xl border border-ink-200 bg-white p-6',
        'shadow-e1 transition-[transform,box-shadow,border-color] duration-200 ease-out',
        'hover:-translate-y-1 hover:border-blue-300 hover:shadow-e3',
      )}
      style={{ animationDelay: `${index * 55}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <span
          className={cn(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-transform duration-200 ease-out group-hover:scale-105',
            identity.classes.soft,
            identity.classes.text,
          )}
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={identity.icon} />
        </span>

        {isStudent && isComplete ? (
          <span
            className="flex h-6 w-6 items-center justify-center rounded-full bg-deep-mint text-[0.6rem] text-white"
            aria-label="Unidad completada"
          >
            <FontAwesomeIcon icon={faCheck} />
          </span>
        ) : (
          <span className="tabular font-sans text-xs font-bold text-ink-300">
            {String(number ?? index + 1).padStart(2, '0')}
          </span>
        )}
      </div>

      <h3 className="mt-4 text-[1.0625rem] font-semibold leading-snug tracking-[-0.01em] text-ink-900">
        {title}
      </h3>

      {topic.description && (
        <p className="mt-2.5 line-clamp-3 text-[0.8125rem] leading-relaxed text-ink-500">
          {topic.description}
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1">
        <Meta icon={faListCheck}>{total} subtemas</Meta>
        <Meta icon={faClock}>{formatDuration(topic.estimated_minutes)}</Meta>
      </div>

      <div className="mt-auto pt-5">
        {isStudent && (
          <div className="flex items-center gap-3">
            <span className="h-1 flex-1 overflow-hidden rounded-full bg-ink-200">
              <span
                className="block h-full w-full origin-left rounded-full bg-blue-900 transition-transform duration-700 ease-out"
                style={{ transform: `scaleX(${percentage / 100})` }}
              />
            </span>
            <span className="tabular text-[0.6875rem] font-bold text-blue-800">{percentage}%</span>
          </div>
        )}

        <span className="mt-3 inline-flex items-center gap-1.5 text-[0.8125rem] font-semibold text-blue-800">
          {!isStudent
            ? 'Abrir unidad'
            : isComplete
              ? 'Repasar'
              : isStarted
                ? 'Continuar'
                : 'Abrir unidad'}
          <FontAwesomeIcon
            icon={faArrowRight}
            className="text-[0.7rem] transition-transform duration-200 ease-out group-hover:translate-x-1"
            aria-hidden="true"
          />
        </span>
      </div>
    </Link>
  )
}

export default function CourseOverview() {
  const { courseId } = useParams()
  const { user } = useAuth()
  const { course, topics, totalQuestions } = useCourse()
  const isStudent = user?.role === 'STUDENT'

  return (
    <div>
      {course?.description && (
        <p className="prose-lesson text-[1.0625rem] leading-[1.65] text-ink-600">
          {course.description}
        </p>
      )}

      <div className="mt-10 flex items-baseline justify-between gap-4">
        <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink-900">Unidades</h2>
        {totalQuestions > 0 && (
          <span className="tabular text-xs text-ink-500">
            {totalQuestions} preguntas de repaso en total
          </span>
        )}
      </div>

      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        {topics.map((topic, index) => (
          <UnitCard
            key={topic.id}
            topic={topic}
            courseId={courseId}
            index={index}
            isStudent={isStudent}
          />
        ))}
      </div>

      {topics.length === 0 && (
        <div className="mt-5 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
          <h3 className="text-lg font-semibold text-ink-900">Este curso aún no tiene unidades</h3>
          <p className="mx-auto mt-2 max-w-[42ch] text-sm text-ink-500">
            El contenido oficial se carga automáticamente. Si no aparece nada, vuelve a intentarlo
            en unos minutos.
          </p>
        </div>
      )}
    </div>
  )
}
