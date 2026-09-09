import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faArrowRight, faLayerGroup } from '@fortawesome/free-solid-svg-icons'

import Quiz from '../../components/course/Quiz'
import { Button } from '../../components/ui/Button'
import { splitUnitName } from '../../lib/curriculum'
import { getTopicQuestions } from '../../services/contentService'
import { useCourse } from '../../hooks/useCourse'

export default function UnitQuizPage() {
  const { courseId, topicId } = useParams()
  const { topics } = useCourse()
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const topic = topics.find((item) => String(item.id) === String(topicId))
  const { number, title } = splitUnitName(topic?.name || '')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setQuestions(await getTopicQuestions(topicId, courseId))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [topicId, courseId])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="animate-fade-in">
      <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[0.8125rem] font-medium">
        <Link
          to={`/courses/${courseId}/units/${topicId}`}
          className="inline-flex items-center gap-2 text-ink-500 transition-colors duration-150 hover:text-blue-800"
        >
          <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
          Volver a la unidad
        </Link>
        <span aria-hidden="true" className="text-ink-300">
          ·
        </span>
        <Link
          to={`/courses/${courseId}`}
          className="inline-flex items-center gap-2 text-ink-500 transition-colors duration-150 hover:text-blue-800"
        >
          <FontAwesomeIcon icon={faLayerGroup} className="text-[0.7rem]" aria-hidden="true" />
          Todas las unidades
        </Link>
      </nav>

      <header className="mt-4">
        <p className="eyebrow text-blue-700">
          Repaso · Unidad {number ?? (topic ? topic.order + 1 : '')}
        </p>
        <h1 className="mt-1.5 text-[1.75rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
          {title || 'Repaso de la unidad'}
        </h1>
        <p className="mt-2 max-w-[58ch] text-sm leading-relaxed text-ink-500">
          Preguntas de todos los subtemas de la unidad. Tras cada respuesta verás por qué es
          correcta: esa explicación es la parte que se queda.
        </p>
      </header>

      <div className="mt-8 rounded-2xl border border-ink-200 bg-white p-6 lg:p-8">
        {loading && (
          <div className="space-y-3">
            <div className="skeleton h-6 w-3/4 rounded" />
            <div className="skeleton h-14 w-full rounded-xl" />
            <div className="skeleton h-14 w-full rounded-xl" />
            <div className="skeleton h-14 w-full rounded-xl" />
          </div>
        )}

        {error && (
          <div className="text-center">
            <p className="text-sm text-wrong-700">{error}</p>
            <Button onClick={load} variant="secondary" size="sm" className="mt-4">
              Reintentar
            </Button>
          </div>
        )}

        {!loading && !error && (
          <Quiz
            questions={questions}
            exit={
              <Link
                to={`/courses/${courseId}`}
                className="inline-flex shrink-0 items-center gap-1.5 text-xs font-semibold text-ink-500 transition-colors duration-150 hover:text-blue-800"
              >
                <FontAwesomeIcon
                  icon={faLayerGroup}
                  className="text-[0.65rem]"
                  aria-hidden="true"
                />
                Salir a las unidades
              </Link>
            }
            footer={
              <Button
                as={Link}
                to={`/courses/${courseId}`}
                variant="primary"
                className="group/btn"
                iconRight={faArrowRight}
              >
                Seguir con el curso
              </Button>
            }
          />
        )}
      </div>
    </div>
  )
}
