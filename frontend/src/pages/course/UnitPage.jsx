import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faArrowRight, faCheck, faListCheck } from '@fortawesome/free-solid-svg-icons'

import { Button } from '../../components/ui/Button'
import { ProgressRing } from '../../components/ui/Progress'
import { cn } from '../../lib/utils'
import {
  formatDuration,
  formatDurationShort,
  splitUnitName,
  unitIdentity,
} from '../../lib/curriculum'
import { useCourse } from '../../hooks/useCourse'

export default function UnitPage() {
  const { courseId, topicId } = useParams()
  const { topics } = useCourse()

  const topic = topics.find((item) => String(item.id) === String(topicId))
  if (!topic) {
    return (
      <div className="rounded-2xl border border-ink-200 bg-white px-6 py-12 text-center">
        <h2 className="text-lg font-semibold text-ink-900">Unidad no encontrada</h2>
        <Button
          as={Link}
          to={`/courses/${courseId}`}
          variant="secondary"
          size="sm"
          className="mt-4"
        >
          Volver al curso
        </Button>
      </div>
    )
  }

  const { number, title } = splitUnitName(topic.name)
  const identity = unitIdentity(topic.order)
  const total = topic.subtopics.length
  const done = topic.subtopics.filter((subtopic) => subtopic.completed).length
  const percentage = total ? Math.round((done / total) * 100) : 0
  const nextSubtopic = topic.subtopics.find((subtopic) => !subtopic.completed)

  return (
    <div className="animate-fade-in">
      <Link
        to={`/courses/${courseId}`}
        className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
      >
        <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
        Todas las unidades
      </Link>

      <header className="mt-4 flex items-start gap-4 sm:gap-5">
        <span
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white sm:h-14 sm:w-14 sm:text-xl',
            identity.classes.bg,
          )}
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={identity.icon} />
        </span>

        <div className="min-w-0 flex-1">
          <p className="eyebrow text-blue-800">Unidad {number ?? topic.order + 1}</p>
          <h1 className="mt-1.5 text-[1.375rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900 sm:text-[1.75rem]">
            {title}
          </h1>
          <p className="tabular mt-2 text-xs text-ink-500">
            {total} subtemas · {formatDuration(topic.estimated_minutes)} · {topic.question_count}{' '}
            preguntas
          </p>
        </div>

        <ProgressRing value={percentage} size={62} className="hidden shrink-0 sm:inline-flex" />
      </header>

      {topic.description && (
        <p className="prose-lesson mt-6 text-[1.0625rem] leading-[1.7] text-ink-600">
          {topic.description}
        </p>
      )}

      <h2 className="mt-9 text-lg font-semibold tracking-[-0.01em] text-ink-900">Subtemas</h2>

      <ol className="mt-4 overflow-hidden rounded-2xl border border-ink-200 bg-white">
        {topic.subtopics.map((subtopic, index) => (
          <li key={subtopic.id} className="border-b border-ink-200 last:border-b-0">
            <Link
              to={`/courses/${courseId}/subtopics/${subtopic.id}`}
              className="group flex items-center gap-3 px-4 py-3.5 transition-colors duration-150 hover:bg-blue-50 sm:gap-4 sm:px-5 sm:py-4"
            >
              <span
                className={cn(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs transition-colors duration-200',
                  subtopic.completed
                    ? 'bg-blue-900 text-white'
                    : 'bg-ink-100 font-sans font-bold text-ink-500 group-hover:bg-blue-100 group-hover:text-blue-800',
                )}
                aria-hidden="true"
              >
                {subtopic.completed ? (
                  <FontAwesomeIcon icon={faCheck} />
                ) : (
                  <span className="tabular">{String(index + 1).padStart(2, '0')}</span>
                )}
              </span>

              <span className="min-w-0 flex-1">
                <span className="block text-[0.9375rem] font-medium leading-snug text-ink-900">
                  {subtopic.name}
                </span>
                <span className="tabular mt-0.5 block text-xs text-ink-500">
                  {formatDurationShort(subtopic.estimated_minutes)}
                  {subtopic.question_count > 0 && ` · ${subtopic.question_count} preguntas`}
                </span>
              </span>

              {/* El estado ya lo dice el círculo de la izquierda: en móvil la
                  etiqueta solo roba ancho al nombre del subtema. */}
              <span
                className={cn(
                  'hidden shrink-0 text-[0.6875rem] font-semibold uppercase tracking-[0.08em] sm:inline',
                  subtopic.completed ? 'text-blue-800' : 'text-ink-400',
                )}
              >
                {subtopic.completed ? 'Hecho' : 'Pendiente'}
              </span>

              <FontAwesomeIcon
                icon={faArrowRight}
                aria-hidden="true"
                className="shrink-0 text-xs text-ink-300 transition-all duration-200 ease-out group-hover:translate-x-1 group-hover:text-blue-800"
              />
            </Link>
          </li>
        ))}
      </ol>

      {/* En móvil los botones ocupan el ancho completo: el rótulo del repaso es
          largo y dentro de un botón de altura fija se cortaría al plegarse. */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        {nextSubtopic && (
          <Button
            as={Link}
            to={`/courses/${courseId}/subtopics/${nextSubtopic.id}`}
            className="group/btn w-full sm:w-auto"
            iconRight={faArrowRight}
          >
            {done > 0 ? 'Continuar la unidad' : 'Empezar la unidad'}
          </Button>
        )}
        {topic.question_count > 0 && (
          <Button
            as={Link}
            to={`/courses/${courseId}/units/${topic.id}/quiz`}
            variant={nextSubtopic ? 'secondary' : 'primary'}
            icon={faListCheck}
            className="w-full sm:w-auto"
          >
            Repasar la unidad · {topic.question_count} preguntas
          </Button>
        )}
      </div>
    </div>
  )
}
