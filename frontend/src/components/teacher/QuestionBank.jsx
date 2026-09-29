import { useCallback, useEffect, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faChevronLeft,
  faCircleCheck,
  faRobot,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { ApiError } from '../../services/api'
import {
  createTeacherQuestion,
  deleteQuestion,
  generateAiQuestions,
  getSubtopicQuestionBank,
  getTopicQuestionSummary,
  reviewPendingQuestion,
  updateQuestion,
} from '../../services/questionService'
import QuestionCard from './QuestionCard'
import QuestionForm from './QuestionForm'
import { cn } from '../../lib/utils'

const STATUS_FILTERS = [
  { value: '', label: 'Todas' },
  { value: 'approved', label: 'Aprobadas' },
  { value: 'pending', label: 'Pendientes' },
  { value: 'rejected', label: 'Rechazadas' },
]

const SOURCE_LABELS = { official: 'Oficial', teacher: 'Docente', ai: 'IA' }

/**
 * Banco de preguntas del curso: navegación unidad → subtema, listado con
 * filtros, creación/edición manual, cola de revisión IA y generación IA.
 *
 * Las preguntas IA nacen pendientes: no llegan a los estudiantes hasta que
 * el profesor las aprueba aquí.
 */
export default function QuestionBank({ courseId, topics }) {
  const [expandedTopicId, setExpandedTopicId] = useState(null)
  const [summaries, setSummaries] = useState({})
  const [selectedSubtopic, setSelectedSubtopic] = useState(null)
  const [questions, setQuestions] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [loadingBank, setLoadingBank] = useState(false)
  const [bankError, setBankError] = useState(null)
  const [editing, setEditing] = useState(null) // null | {} (nueva) | question (editar)
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [actionMessage, setActionMessage] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [countChoice, setCountChoice] = useState(3)
  const [generateError, setGenerateError] = useState(null)
  const [highlightIds, setHighlightIds] = useState([])
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewItems, setReviewItems] = useState([])
  const [reviewLoading, setReviewLoading] = useState(false)

  // Resumen de conteos por unidad (para badges de pendientes en la navegación)
  useEffect(() => {
    let cancelled = false
    async function loadSummaries() {
      const results = {}
      for (const topic of topics ?? []) {
        try {
          results[topic.id] = await getTopicQuestionSummary(topic.id)
        } catch {
          results[topic.id] = []
        }
      }
      if (!cancelled) setSummaries(results)
    }
    if (topics?.length) loadSummaries()
    return () => {
      cancelled = true
    }
  }, [topics])

  const loadBank = useCallback(
    async (subtopicId) => {
      setLoadingBank(true)
      setBankError(null)
      try {
        const data = await getSubtopicQuestionBank(subtopicId, {
          status: statusFilter || undefined,
          source: sourceFilter || undefined,
        })
        setQuestions(data)
      } catch (error) {
        setQuestions([])
        setBankError(error instanceof ApiError ? error.message : 'Error al cargar el banco.')
      } finally {
        setLoadingBank(false)
      }
    },
    [statusFilter, sourceFilter],
  )

  useEffect(() => {
    if (selectedSubtopic) loadBank(selectedSubtopic)
  }, [selectedSubtopic, loadBank])

  const refreshSummary = async () => {
    if (!selectedSubtopic) return
    const topicId = topics?.find((topic) =>
      topic.subtopics?.some((subtopic) => subtopic.id === selectedSubtopic),
    )?.id
    if (!topicId) return
    try {
      const summary = await getTopicQuestionSummary(topicId)
      setSummaries((current) => ({ ...current, [topicId]: summary }))
    } catch {
      /* el resumen es informativo; el banco ya se refrescó */
    }
  }

  const selectSubtopic = (subtopicId) => {
    setSelectedSubtopic(subtopicId)
    setEditing(null)
    setFormError(null)
    setActionMessage(null)
    setGenerateError(null)
  }

  const handleSubmitQuestion = async (payload) => {
    setBusy(true)
    setFormError(null)
    try {
      if (editing?.id) {
        const updated = await updateQuestion(editing.id, payload)
        setQuestions((current) => current.map((q) => (q.id === updated.id ? updated : q)))
        setActionMessage('Pregunta actualizada.')
      } else {
        const created = await createTeacherQuestion(selectedSubtopic, payload)
        setQuestions((current) => [...current, created])
        setActionMessage('Pregunta agregada: ya está visible para tus estudiantes.')
      }
      setEditing(null)
      refreshSummary()
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : 'No se pudo guardar la pregunta.')
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async (question) => {
    if (!window.confirm('¿Eliminar esta pregunta? Esta acción no se puede deshacer.')) return
    setBusy(true)
    setActionMessage(null)
    try {
      const result = await deleteQuestion(question.id)
      if (result.deleted) {
        setQuestions((current) => current.filter((q) => q.id !== question.id))
        setActionMessage('Pregunta eliminada.')
      } else {
        setQuestions((current) =>
          current.map((q) => (q.id === question.id ? { ...q, status: 'rejected' } : q)),
        )
        setActionMessage(result.detail)
      }
      refreshSummary()
    } catch (error) {
      setActionMessage(error instanceof ApiError ? error.message : 'No se pudo eliminar.')
    } finally {
      setBusy(false)
    }
  }

  const handleReview = async (question, action) => {
    setBusy(true)
    setActionMessage(null)
    try {
      const updated = await reviewPendingQuestion(question.id, action)
      setQuestions((current) => current.map((q) => (q.id === updated.id ? updated : q)))
      setReviewItems((current) => current.filter((q) => q.id !== updated.id))
      setActionMessage(action === 'approve' ? 'Pregunta aprobada: ya la ven tus estudiantes.' : 'Pregunta rechazada.')
      refreshSummary()
    } catch (error) {
      setActionMessage(error instanceof ApiError ? error.message : 'No se pudo revisar la pregunta.')
    } finally {
      setBusy(false)
    }
  }

  const handleGenerate = async (count) => {
    setGenerating(true)
    setGenerateError(null)
    setActionMessage(null)
    try {
      const data = await generateAiQuestions({ subtopicId: selectedSubtopic, count })
      const newIds = data.generated.map((q) => q.id)
      setQuestions((current) => [...current, ...data.generated])
      setHighlightIds(newIds)
      setActionMessage(
        data.warning ??
          `Se generaron ${data.created} preguntas. Quedan pendientes hasta que las apruebes.`,
      )
      setTimeout(() => setHighlightIds([]), 4000)
      refreshSummary()
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 429) setGenerateError('Alcanzaste el límite de generaciones por hora. Intenta más tarde.')
        else if (error.status === 422) setGenerateError(error.message)
        else if (error.status === 502) setGenerateError('La IA no devolvió preguntas válidas. Intenta de nuevo en unos minutos.')
        else setGenerateError(error.message)
      } else {
        setGenerateError('No se pudieron generar preguntas.')
      }
    } finally {
      setGenerating(false)
    }
  }

  const openReviewQueue = async () => {
    if (reviewOpen) {
      setReviewOpen(false)
      return
    }
    setReviewOpen(true)
    setReviewLoading(true)
    try {
      // Carga las pendientes de todos los subtemas del curso con pendientes.
      const pendingBySubtopic = []
      for (const topic of topics ?? []) {
        for (const item of summaries[topic.id] ?? []) {
          if (item.pending > 0) pendingBySubtopic.push(item.subtopic_id)
        }
      }
      const batches = await Promise.all(
        pendingBySubtopic.map((subtopicId) =>
          getSubtopicQuestionBank(subtopicId, { status: 'pending', source: 'ai' }),
        ),
      )
      setReviewItems(batches.flat())
    } catch {
      setReviewItems([])
    } finally {
      setReviewLoading(false)
    }
  }

  const totalPending = Object.values(summaries).reduce(
    (acc, summary) => acc + summary.reduce((sum, item) => sum + item.pending, 0),
    0,
  )

  if (!topics?.length) {
    return (
      <section className="mt-12">
        <h2 className="text-xl font-semibold text-ink-900">Banco de preguntas</h2>
        <p className="mt-3 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-8 text-center text-sm text-ink-500">
          Este curso aún no tiene unidades con contenido. Importa el compendio para crear preguntas.
        </p>
      </section>
    )
  }

  const selectedTopic = topics.find((topic) =>
    topic.subtopics?.some((subtopic) => subtopic.id === selectedSubtopic),
  )
  const selectedSubtopicName = selectedTopic?.subtopics?.find(
    (subtopic) => subtopic.id === selectedSubtopic,
  )?.name

  return (
    <section className="mt-12">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink-900">Banco de preguntas</h2>
        <Button
          variant={reviewOpen ? 'primary' : 'secondary'}
          size="sm"
          icon={faCircleCheck}
          onClick={openReviewQueue}
        >
          Pendientes de revisión
          {totalPending > 0 && (
            <span className="tabular ml-1.5 rounded-full bg-wrong-500 px-2 py-0.5 text-[0.6875rem] font-bold text-white">
              {totalPending}
            </span>
          )}
        </Button>
      </div>
      <p className="mt-1.5 max-w-[62ch] text-[0.875rem] leading-relaxed text-ink-500">
        Crea preguntas a mano, genera con IA y revisa lo que verán tus estudiantes en los cuestionarios.
      </p>

      {reviewOpen && (
        <div className="mt-5 rounded-2xl border border-deep-butter/40 bg-soft-butter/40 p-5">
          <h3 className="flex items-center gap-2 text-base font-semibold text-ink-900">
            <FontAwesomeIcon icon={faRobot} className="text-deep-butter" aria-hidden="true" />
            Cola de revisión IA
          </h3>
          {reviewLoading ? (
            <p className="mt-4 flex items-center gap-2 text-sm text-ink-500" aria-live="polite">
              <FontAwesomeIcon icon={faSpinner} spin aria-hidden="true" /> Cargando pendientes…
            </p>
          ) : reviewItems.length === 0 ? (
            <p className="mt-3 text-sm text-ink-500">No hay preguntas IA pendientes. ¡Todo al día!</p>
          ) : (
            <div className="mt-4 space-y-4">
              {reviewItems.map((question) => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  busy={busy}
                  onEdit={() => {
                    setReviewOpen(false)
                    selectSubtopic(question.subtopic_id)
                    setEditing(question)
                  }}
                  onReview={handleReview}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Navegación unidad → subtema */}
      <div className="mt-5 space-y-3">
        {topics.map((topic) => {
          const summary = summaries[topic.id] ?? []
          const pendingInTopic = summary.reduce((sum, item) => sum + item.pending, 0)
          const expanded = expandedTopicId === topic.id
          return (
            <div key={topic.id} className="overflow-hidden rounded-2xl border border-ink-200 bg-white">
              <button
                type="button"
                onClick={() => setExpandedTopicId(expanded ? null : topic.id)}
                aria-expanded={expanded}
                className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors duration-150 hover:bg-ink-50"
              >
                <span className="font-semibold text-ink-900">{topic.name}</span>
                <span className="flex items-center gap-2">
                  {pendingInTopic > 0 && (
                    <span className="tabular rounded-full bg-soft-butter px-2.5 py-0.5 text-[0.6875rem] font-bold text-deep-butter">
                      {pendingInTopic} pendientes
                    </span>
                  )}
                  <FontAwesomeIcon
                    icon={faChevronLeft}
                    className={cn('text-[0.7rem] text-ink-400 transition-transform duration-150', expanded && '-rotate-90')}
                    aria-hidden="true"
                  />
                </span>
              </button>
              {expanded && (
                <ul className="divide-y divide-ink-100 border-t border-ink-100">
                  {(summary.length
                    ? summary
                    : topic.subtopics.map((subtopic) => ({
                        subtopic_id: subtopic.id,
                        title: subtopic.name,
                        total: 0,
                        pending: 0,
                      }))
                  ).map((item) => (
                    <li key={item.subtopic_id}>
                      <button
                        type="button"
                        onClick={() => selectSubtopic(item.subtopic_id)}
                        className={cn(
                          'flex w-full items-center justify-between gap-3 px-5 py-3 text-left text-sm transition-colors duration-150 hover:bg-soft-sky/60',
                          selectedSubtopic === item.subtopic_id && 'bg-soft-sky font-semibold text-blue-900',
                        )}
                      >
                        <span className="min-w-0 truncate text-ink-700">{item.title}</span>
                        <span className="tabular shrink-0 text-[0.75rem] text-ink-400">
                          {item.total} pregunta{item.total === 1 ? '' : 's'}
                          {item.pending > 0 && (
                            <span className="ml-2 font-bold text-deep-butter">{item.pending} IA pend.</span>
                          )}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </div>

      {/* Panel del subtema seleccionado */}
      {selectedSubtopic && (
        <div className="mt-6 rounded-2xl border border-ink-200 bg-ink-50/50 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-base font-semibold text-ink-900">{selectedSubtopicName}</h3>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={countChoice}
                onChange={(event) => setCountChoice(Number(event.target.value))}
                aria-label="Cantidad de preguntas a generar"
                className="h-9 rounded-xl border border-ink-200 bg-white px-2.5 text-[0.8125rem] text-ink-700"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <Button
                variant="secondary"
                size="sm"
                icon={generating ? faSpinner : faRobot}
                onClick={() => handleGenerate(countChoice)}
                disabled={generating}
              >
                {generating ? 'Generando…' : 'Generar con IA'}
              </Button>
              <Button variant="primary" size="sm" onClick={() => { setEditing({}); setFormError(null) }} disabled={busy}>
                Nueva pregunta
              </Button>
            </div>
          </div>
          <p className="mt-2 text-[0.75rem] leading-relaxed text-ink-400">
            Las preguntas generadas con IA quedan pendientes y no se muestran a los estudiantes hasta que las apruebes.
          </p>

          <p aria-live="polite" className="sr-only">
            {actionMessage ?? ''}
          </p>

          {generateError && (
            <p role="alert" className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-3.5 py-2.5 text-sm text-wrong-700">
              {generateError}
            </p>
          )}
          {actionMessage && (
            <p className="mt-4 rounded-xl border border-correct-200 bg-correct-50 px-3.5 py-2.5 text-sm text-correct-700">
              {actionMessage}
            </p>
          )}

          {editing && (
            <div className="mt-5">
              <QuestionForm
                initial={editing.id ? editing : undefined}
                onSubmit={handleSubmitQuestion}
                onCancel={() => { setEditing(null); setFormError(null) }}
                submitting={busy}
                serverError={formError}
              />
            </div>
          )}

          {/* Filtros */}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.value}
                type="button"
                onClick={() => setStatusFilter(filter.value)}
                className={cn(
                  'rounded-full px-3.5 py-1.5 text-[0.8125rem] font-semibold transition-colors duration-150',
                  statusFilter === filter.value
                    ? 'bg-blue-900 text-white'
                    : 'bg-white text-ink-600 hover:bg-ink-100',
                )}
              >
                {filter.label}
              </button>
            ))}
            <span className="mx-1 h-5 w-px bg-ink-200" aria-hidden="true" />
            {['', ...Object.keys(SOURCE_LABELS)].map((source) => (
              <button
                key={source || 'all'}
                type="button"
                onClick={() => setSourceFilter(source)}
                className={cn(
                  'rounded-full px-3.5 py-1.5 text-[0.8125rem] font-semibold transition-colors duration-150',
                  sourceFilter === source
                    ? 'bg-blue-900 text-white'
                    : 'bg-white text-ink-600 hover:bg-ink-100',
                )}
              >
                {source ? SOURCE_LABELS[source] : 'Todos los orígenes'}
              </button>
            ))}
          </div>

          {/* Listado */}
          <div className="mt-5" aria-live="polite">
            {loadingBank ? (
              <div className="space-y-3">
                <div className="skeleton h-32 w-full rounded-2xl" />
                <div className="skeleton h-32 w-full rounded-2xl" />
              </div>
            ) : bankError ? (
              <div className="rounded-2xl border border-wrong-200 bg-wrong-50 px-6 py-8 text-center">
                <p className="text-sm text-wrong-700">{bankError}</p>
                <Button variant="secondary" size="sm" className="mt-4" onClick={() => loadBank(selectedSubtopic)}>
                  Reintentar
                </Button>
              </div>
            ) : questions.length === 0 ? (
              <p className="rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-10 text-center text-sm text-ink-500">
                Este subtema aún no tiene preguntas{statusFilter || sourceFilter ? ' con esos filtros' : ''}.
              </p>
            ) : (
              <div className="space-y-4">
                {questions.map((question) => (
                  <div
                    key={question.id}
                    className={cn(
                      'rounded-2xl transition-shadow duration-500',
                      highlightIds.includes(question.id) && 'ring-2 ring-deep-butter ring-offset-2',
                    )}
                  >
                    <QuestionCard
                      question={question}
                      busy={busy}
                      onEdit={(q) => { setEditing(q); setFormError(null); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                      onDelete={handleDelete}
                      onReview={handleReview}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
