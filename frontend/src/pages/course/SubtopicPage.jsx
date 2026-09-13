import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowLeft,
  faArrowRight,
  faCheck,
  faClock,
  faCube,
  faLayerGroup,
  faListCheck,
} from '@fortawesome/free-solid-svg-icons'

import Quiz from '../../components/course/Quiz'
import { Button } from '../../components/ui/Button'
import { Meta } from '../../components/ui/Meta'
import { cn } from '../../lib/utils'
import { formatDuration, splitUnitName } from '../../lib/curriculum'
import { getSubtopic } from '../../services/contentService'
import { useAuth } from '../../hooks/useAuth'
import { useCourse } from '../../hooks/useCourse'

/** Contenido oficial: párrafos, listas con "- " o "1." y **negritas**. */
function LessonContent({ content }) {
  const blocks = useMemo(() => {
    const renderInline = (text, key) =>
      text
        .split(/(\*\*[^*]+\*\*)/g)
        .map((part, i) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={`${key}-${i}`}>{part.slice(2, -2)}</strong>
          ) : (
            <span key={`${key}-${i}`}>{part}</span>
          ),
        )

    return content
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => {
        if (/^[-•]\s+/.test(line)) {
          return (
            <li key={index} className="mb-2.5 ml-1 list-none pl-6 -indent-6">
              <span className="mr-3 font-sans text-sm text-blue-800">—</span>
              {renderInline(line.replace(/^[-•]\s+/, ''), index)}
            </li>
          )
        }
        if (/^\d+\.\s+/.test(line)) {
          return (
            <li key={index} className="mb-2.5 ml-1 list-none pl-8 -indent-8">
              <span className="tabular mr-3 font-sans text-sm font-bold text-blue-800">
                {line.match(/^\d+\./)[0]}
              </span>
              {renderInline(line.replace(/^\d+\.\s+/, ''), index)}
            </li>
          )
        }
        return <p key={index}>{renderInline(line, index)}</p>
      })
  }, [content])

  return <div className="prose-lesson">{blocks}</div>
}

export default function SubtopicPage() {
  const { courseId, subtopicId } = useParams()
  const { user } = useAuth()
  const isStudent = user?.role === 'STUDENT'
  const { topics, flatSubtopics, markSubtopic } = useCourse()

  const [subtopic, setSubtopic] = useState(null)
  const [completed, setCompleted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [quizOpen, setQuizOpen] = useState(false)
  const [quizScore, setQuizScore] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setQuizOpen(false)
    setQuizScore(null)
    try {
      const data = await getSubtopic(subtopicId, courseId)
      setSubtopic(data)
      setCompleted(data.completed)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [courseId, subtopicId])

  useEffect(() => {
    load()
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [load])

  const toggleCompleted = async () => {
    setSaving(true)
    setError(null)
    try {
      const record = await markSubtopic(subtopicId, !completed)
      setCompleted(record.completed)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const topic = topics.find((item) => item.id === subtopic?.topic_id)
  const { number: unitNumber, title: unitTitle } = splitUnitName(topic?.name || '')
  const position = flatSubtopics.findIndex((item) => String(item.id) === String(subtopicId))
  const previous = position > 0 ? flatSubtopics[position - 1] : null
  const next =
    position >= 0 && position < flatSubtopics.length - 1 ? flatSubtopics[position + 1] : null
  const hasInteractiveView = subtopic?.name === 'Inyecciones intravítreas'
  const questions = subtopic?.questions || []

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-4 w-40 rounded" />
        <div className="skeleton h-10 w-3/4 rounded" />
        <div className="skeleton h-56 w-full rounded-2xl" />
      </div>
    )
  }

  if (error && !subtopic) {
    return (
      <div className="rounded-2xl border border-wrong-200 bg-wrong-50 px-6 py-10 text-center">
        <p className="text-sm text-wrong-700">{error}</p>
        <Button onClick={load} variant="secondary" size="sm" className="mt-4">
          Reintentar
        </Button>
      </div>
    )
  }

  return (
    <article className="animate-fade-in">
      {topic && (
        <Link
          to={`/courses/${courseId}/units/${topic.id}`}
          className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
        >
          <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
          {unitTitle || 'Volver a la unidad'}
        </Link>
      )}

      <header className="mt-4">
        <p className="eyebrow text-blue-800">
          Unidad {unitNumber ?? ''} · Subtema {position + 1} de {flatSubtopics.length}
        </p>
        <h1 className="mt-2 max-w-[22ch] text-[2rem] font-semibold leading-[1.15] tracking-[-0.02em] text-ink-900 lg:text-[2.375rem]">
          {subtopic?.name}
        </h1>
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5">
          <Meta icon={faClock}>{formatDuration(subtopic?.estimated_minutes)} de estudio</Meta>
          {questions.length > 0 && (
            <Meta icon={faListCheck}>{questions.length} preguntas de repaso</Meta>
          )}
          {completed && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-800">
              <FontAwesomeIcon icon={faCheck} aria-hidden="true" />
              Completado
            </span>
          )}
        </div>
      </header>

      <div className="mt-8 rounded-2xl border border-ink-200 bg-white p-7 shadow-e1 lg:p-10">
        <LessonContent content={subtopic?.content || ''} />

        {hasInteractiveView && (
          <div className="mt-8 flex flex-wrap items-center gap-4 rounded-2xl bg-blue-950 p-6">
            <span
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-900 text-white"
              aria-hidden="true"
            >
              <FontAwesomeIcon icon={faCube} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-display text-base font-semibold text-white">
                Mesa quirúrgica en 3D
              </span>
              <span className="mt-0.5 block text-[0.8125rem] text-blue-200">
                Explora el montaje del instrumental girando el modelo.
              </span>
            </span>
            <Button
              as={Link}
              to={`/courses/${courseId}/subtopics/${subtopicId}/interactive`}
              variant="inverse"
              size="sm"
            >
              Abrir vista interactiva
            </Button>
          </div>
        )}
      </div>

      {/* Repaso del subtema */}
      {questions.length > 0 && (
        <section className="mt-8">
          {!quizOpen ? (
            <div className="flex flex-wrap items-center gap-5 rounded-2xl border border-soft-sky bg-soft-sky p-7">
              <span
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white text-blue-900 shadow-e1"
                aria-hidden="true"
              >
                <FontAwesomeIcon icon={faListCheck} />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-semibold tracking-[-0.01em] text-ink-900">
                  Comprueba lo que acabas de leer
                </h2>
                <p className="tabular mt-1 text-sm text-ink-600">
                  {questions.length} preguntas sobre este subtema, con explicación en cada una.
                </p>
              </div>
              <Button onClick={() => setQuizOpen(true)}>Empezar el repaso</Button>
            </div>
          ) : (
            <div className="rounded-2xl border border-ink-200 bg-white p-6 lg:p-8">
              <h2 className="mb-6 text-lg font-semibold tracking-[-0.01em] text-ink-900">
                Repaso de {subtopic?.name}
              </h2>
              <Quiz
                questions={questions}
                onFinish={(result) => setQuizScore(result.score)}
                exit={
                  <span className="flex shrink-0 items-center gap-4">
                    <button
                      type="button"
                      onClick={() => setQuizOpen(false)}
                      className="text-xs font-semibold text-ink-500 transition-colors duration-150 hover:text-blue-800"
                    >
                      Volver a la lectura
                    </button>
                    <Link
                      to={`/courses/${courseId}`}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-ink-500 transition-colors duration-150 hover:text-blue-800"
                    >
                      <FontAwesomeIcon
                        icon={faLayerGroup}
                        className="text-[0.65rem]"
                        aria-hidden="true"
                      />
                      Todas las unidades
                    </Link>
                  </span>
                }
                footer={
                  isStudent && !completed ? (
                    <Button onClick={toggleCompleted} loading={saving} icon={faCheck}>
                      Marcar como completado
                    </Button>
                  ) : null
                }
              />
            </div>
          )}
        </section>
      )}

      {/* Acciones de progreso y navegación entre subtemas */}
      {isStudent && (
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Button
            onClick={toggleCompleted}
            loading={saving}
            variant={completed ? 'secondary' : 'primary'}
            icon={completed ? faCheck : undefined}
          >
            {completed ? 'Completado · pulsa para desmarcar' : 'Marcar como completado'}
          </Button>
          {quizScore !== null && (
            <span className="tabular text-sm text-ink-500">
              Último repaso: <span className="font-semibold text-blue-800">{quizScore}%</span>
            </span>
          )}
          {error && (
            <span role="alert" className="text-sm text-wrong-700">
              {error}
            </span>
          )}
        </div>
      )}

      <nav className="mt-10 grid gap-3 border-t border-ink-200 pt-6 sm:grid-cols-2">
        {previous ? (
          <Link
            to={`/courses/${courseId}/subtopics/${previous.id}`}
            className="group rounded-xl border border-ink-200 bg-white px-5 py-4 transition-[border-color,box-shadow] duration-150 hover:border-blue-300 hover:shadow-e2"
          >
            <span className="flex items-center gap-2 text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-ink-400">
              <FontAwesomeIcon
                icon={faArrowLeft}
                className="text-[0.6rem] transition-transform duration-200 group-hover:-translate-x-1"
                aria-hidden="true"
              />
              Anterior
            </span>
            <span className="mt-1.5 block text-[0.9375rem] font-medium leading-snug text-ink-900">
              {previous.name}
            </span>
          </Link>
        ) : (
          <span />
        )}

        {next && (
          <Link
            to={`/courses/${courseId}/subtopics/${next.id}`}
            className={cn(
              'group rounded-xl border border-ink-200 bg-white px-5 py-4 text-right',
              'transition-[border-color,box-shadow] duration-150 hover:border-blue-300 hover:shadow-e2',
              !previous && 'sm:col-start-2',
            )}
          >
            <span className="flex items-center justify-end gap-2 text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-ink-400">
              Siguiente
              <FontAwesomeIcon
                icon={faArrowRight}
                className="text-[0.6rem] transition-transform duration-200 group-hover:translate-x-1"
                aria-hidden="true"
              />
            </span>
            <span className="mt-1.5 block text-[0.9375rem] font-medium leading-snug text-ink-900">
              {next.name}
            </span>
          </Link>
        )}
      </nav>
    </article>
  )
}
