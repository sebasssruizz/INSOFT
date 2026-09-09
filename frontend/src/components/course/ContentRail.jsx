import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faChevronDown, faClock, faListCheck } from '@fortawesome/free-solid-svg-icons'

import { cn } from '../../lib/utils'
import {
  formatDuration,
  formatDurationShort,
  splitUnitName,
  unitIdentity,
} from '../../lib/curriculum'
import { useAuth } from '../../hooks/useAuth'
import { useCourse } from '../../hooks/useCourse'

function CompletionDot({ completed, active }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[0.5rem] transition-all duration-200 ease-out',
        completed
          ? 'border-blue-900 bg-blue-900 text-white'
          : active
            ? 'border-blue-500 bg-white'
            : 'border-ink-300 bg-white',
      )}
    >
      <FontAwesomeIcon
        icon={faCheck}
        className={cn('transition-opacity duration-200', completed ? 'opacity-100' : 'opacity-0')}
      />
    </span>
  )
}

function UnitSection({ topic, courseId, openId, setOpenId, activeSubtopicId, isStudent }) {
  const { number, title } = splitUnitName(topic.name)
  const identity = unitIdentity(topic.order)
  const isOpen = openId === topic.id
  const total = topic.subtopics.length
  const done = topic.subtopics.filter((subtopic) => subtopic.completed).length
  const percentage = total ? (done / total) * 100 : 0
  const isComplete = total > 0 && done === total

  return (
    <div className="border-b border-ink-200 last:border-b-0">
      <button
        onClick={() => setOpenId(isOpen ? null : topic.id)}
        aria-expanded={isOpen}
        className="flex w-full items-start gap-3 px-4 py-3.5 text-left transition-colors duration-150 hover:bg-ink-50"
      >
        <span
          className={cn(
            'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white',
            isStudent && isComplete ? 'bg-blue-900' : identity.classes.bg,
          )}
          aria-hidden="true"
        >
          {isStudent && isComplete ? (
            <FontAwesomeIcon icon={faCheck} className="text-xs" />
          ) : (
            <span className="tabular font-sans text-xs font-bold">{number ?? topic.order + 1}</span>
          )}
        </span>

        <span className="min-w-0 flex-1">
          <span className="block text-[0.8125rem] font-semibold leading-snug text-ink-900">
            {title}
          </span>
          <span className="tabular mt-1 block text-[0.6875rem] text-ink-500">
            {isStudent ? `${done}/${total}` : total} subtemas ·{' '}
            {formatDurationShort(topic.estimated_minutes)}
          </span>
          {isStudent && (
            <span className="mt-2 block h-0.5 w-full overflow-hidden rounded-full bg-ink-200">
              <span
                className="block h-full w-full origin-left rounded-full bg-blue-900 transition-transform duration-500 ease-out"
                style={{ transform: `scaleX(${percentage / 100})` }}
              />
            </span>
          )}
        </span>

        <FontAwesomeIcon
          icon={faChevronDown}
          aria-hidden="true"
          className={cn(
            'mt-1 text-[0.7rem] text-ink-400 transition-transform duration-200 ease-out',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="animate-fade-in px-2 pb-3">
          {topic.subtopics.map((subtopic) => {
            const active = String(subtopic.id) === String(activeSubtopicId)
            return (
              <Link
                key={subtopic.id}
                to={`/courses/${courseId}/subtopics/${subtopic.id}`}
                className={cn(
                  'flex items-center gap-2.5 rounded-lg px-2.5 py-2 transition-colors duration-150',
                  active ? 'bg-blue-50' : 'hover:bg-ink-50',
                )}
              >
                <CompletionDot completed={isStudent && subtopic.completed} active={active} />
                <span
                  className={cn(
                    'min-w-0 flex-1 truncate text-[0.8125rem] leading-snug',
                    active ? 'font-semibold text-blue-800' : 'text-ink-600',
                  )}
                >
                  {subtopic.name}
                </span>
                <span className="tabular shrink-0 text-[0.6875rem] text-ink-400">
                  {formatDurationShort(subtopic.estimated_minutes)}
                </span>
              </Link>
            )
          })}

          {topic.question_count > 0 && (
            <Link
              to={`/courses/${courseId}/units/${topic.id}/quiz`}
              className="mt-1.5 flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[0.8125rem] font-semibold text-blue-800 transition-colors duration-150 hover:bg-blue-50"
            >
              <span
                className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[0.55rem] text-blue-800"
                aria-hidden="true"
              >
                <FontAwesomeIcon icon={faListCheck} />
              </span>
              Repaso de la unidad
              <span className="tabular ml-auto text-[0.6875rem] font-medium text-ink-400">
                {topic.question_count} preguntas
              </span>
            </Link>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Índice del curso: unidades plegables con sus subtemas, el estado de cada uno
 * y el acceso al repaso. Se despliega sola la unidad en la que está el
 * estudiante.
 */
export default function ContentRail({ className }) {
  const { courseId, topicId, subtopicId } = useParams()
  const { user } = useAuth()
  const { topics, totalSubtopics, totalMinutes } = useCourse()
  const isStudent = user?.role === 'STUDENT'
  const [openId, setOpenId] = useState(null)

  // La unidad de la pantalla actual manda sobre el pliegue manual al navegar.
  useEffect(() => {
    if (topicId) {
      setOpenId(Number(topicId))
      return
    }
    if (subtopicId) {
      const owner = topics.find((topic) =>
        topic.subtopics.some((subtopic) => String(subtopic.id) === String(subtopicId)),
      )
      if (owner) setOpenId(owner.id)
      return
    }
    setOpenId((current) => current ?? topics[0]?.id ?? null)
  }, [topicId, subtopicId, topics])

  return (
    <div className={cn('overflow-hidden rounded-2xl border border-ink-200 bg-white', className)}>
      <div className="border-b border-ink-200 px-4 py-4">
        <h2 className="text-base font-semibold tracking-[-0.01em] text-ink-900">
          Contenido del curso
        </h2>
        <p className="tabular mt-1 flex items-center gap-3 text-xs text-ink-500">
          <span>{topics.length} unidades</span>
          <span aria-hidden="true">·</span>
          <span>{totalSubtopics} subtemas</span>
          <span aria-hidden="true">·</span>
          <span className="inline-flex items-center gap-1">
            <FontAwesomeIcon icon={faClock} className="text-[0.65rem]" aria-hidden="true" />
            {formatDuration(totalMinutes)}
          </span>
        </p>
      </div>

      <div className="max-h-[calc(100vh-16rem)] overflow-y-auto">
        {topics.map((topic) => (
          <UnitSection
            key={topic.id}
            topic={topic}
            courseId={courseId}
            openId={openId}
            setOpenId={setOpenId}
            activeSubtopicId={subtopicId}
            isStudent={isStudent}
          />
        ))}
      </div>
    </div>
  )
}
