import { useCallback, useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faChevronDown,
  faCircleCheck,
  faEye,
  faRobot,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { IrisSpinner } from '../ui/EyeLoader'
import { ApiError } from '../../services/api'
import {
  createTeacherQuestion,
  removeCourseQuestion,
  getSubtopicQuestionBank,
  getTopicQuestionSummary,
  reviewPendingQuestion,
  updateQuestion,
} from '../../services/questionService'
import QuestionCard from './QuestionCard'
import QuestionForm from './QuestionForm'
import { cn } from '../../lib/utils'
import { splitUnitName } from '../../lib/curriculum'

/**
 * Banco de preguntas del curso: navegación unidad → subtema, listado con
 * filtros, creación/edición manual, cola de revisión IA y generación IA.
 *
 * Las preguntas IA nacen pendientes: no llegan a los estudiantes hasta que
 * el profesor las aprueba aquí.
 */
export default function QuestionBank({
  courseId,
  topics,
  refreshSignal = 0,
  onSelectedSubtopicChange,
}) {
  const [expandedTopicId, setExpandedTopicId] = useState(null)
  const [summaries, setSummaries] = useState({})
  const [selectedSubtopic, setSelectedSubtopic] = useState(null)
  const [bankOpen, setBankOpen] = useState(false)
  const dialogRef = useRef(null)
  const closeButtonRef = useRef(null)
  const bankContentRef = useRef(null)
  const [questions, setQuestions] = useState([])
  const [loadingBank, setLoadingBank] = useState(false)
  const [bankError, setBankError] = useState(null)
  const [editing, setEditing] = useState(null) // null | {} (nueva) | question (editar)
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [actionMessage, setActionMessage] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewItems, setReviewItems] = useState([])
  const [reviewLoading, setReviewLoading] = useState(false)

  useEffect(() => {
    if (!bankOpen) return
    const dialog = dialogRef.current
    const trigger = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.showModal()
    closeButtonRef.current?.focus()
    return () => {
      dialog.close()
      document.body.style.overflow = previousOverflow
      trigger?.focus()
    }
  }, [bankOpen])

  const closeBank = () => {
    if (editing && !window.confirm('¿Cerrar el panel? Los cambios sin guardar se perderán.')) return
    setEditing(null)
    setBankOpen(false)
  }

  // Resumen de conteos por unidad (para badges de pendientes en la navegación)
  const loadSummaries = useCallback(
    async (cancelledRef) => {
      if (!topics?.length) return
      const results = {}
      for (const topic of topics) {
        try {
          results[topic.id] = await getTopicQuestionSummary(topic.id, courseId)
        } catch {
          results[topic.id] = []
        }
      }
      if (!cancelledRef?.cancelled) setSummaries(results)
    },
    [topics, courseId],
  )

  useEffect(() => {
    let cancelled = { cancelled: false }
    loadSummaries(cancelled)
    return () => {
      cancelled.cancelled = true
    }
  }, [loadSummaries])

  // El asistente "Agregar pregunta" guarda: refresca lista y conteos si hay subtema abierto.
  useEffect(() => {
    if (!refreshSignal) return
    if (selectedSubtopic) loadBank(selectedSubtopic)
    loadSummaries()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshSignal])

  const loadBank = useCallback(
    async (subtopicId) => {
      setLoadingBank(true)
      setBankError(null)
      try {
        const data = await getSubtopicQuestionBank(subtopicId, {
          courseId,
        })
        setQuestions(data.filter((question) => ['approved', 'practice'].includes(question.status)))
      } catch (error) {
        setQuestions([])
        setBankError(error instanceof ApiError ? error.message : 'Error al cargar el banco.')
      } finally {
        setLoadingBank(false)
      }
    },
    [courseId],
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
      const summary = await getTopicQuestionSummary(topicId, courseId)
      setSummaries((current) => ({ ...current, [topicId]: summary }))
    } catch {
      /* el resumen es informativo; el banco ya se refrescó */
    }
  }

  const selectSubtopic = (subtopicId) => {
    if (selectedSubtopic !== subtopicId) {
      setQuestions([])
      setLoadingBank(true)
    }
    setActionError(null)
    setSelectedSubtopic(subtopicId)
    setBankOpen(true)
    onSelectedSubtopicChange?.(subtopicId)
    setEditing(null)
    setFormError(null)
    setActionMessage(null)
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
    setBusy(true)
    setActionMessage(null)
    setActionError(null)
    try {
      const result = await removeCourseQuestion(courseId, question.id)
      setQuestions((current) => current.filter((q) => q.id !== question.id))
      if (editing?.id === question.id) setEditing(null)
      setActionMessage(result.detail)
      refreshSummary()
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : 'No se pudo retirar la pregunta.')
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
          getSubtopicQuestionBank(subtopicId, { status: 'pending', source: 'ai', courseId }),
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
        Consulta y administra las preguntas disponibles para tus estudiantes en cada subtema.
      </p>
      <p className="mt-2 text-sm text-ink-600">
        El botón del ojo abre las preguntas y sus respuestas correctas de cada subtema.
      </p>

      {reviewOpen && (
        <div className="mt-5 rounded-2xl border border-deep-butter/40 bg-soft-butter/40 p-5">
          <h3 className="flex items-center gap-2 text-base font-semibold text-ink-900">
            <FontAwesomeIcon icon={faRobot} className="text-deep-butter" aria-hidden="true" />
            Cola de revisión IA
          </h3>
          {reviewLoading ? (
            <p className="mt-4 flex items-center gap-2 text-sm text-ink-500" aria-live="polite">
              <IrisSpinner className="text-blue-900" /> Cargando pendientes…
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
                {/* Mismo formato que el índice del curso: número de unidad en
                    versalita y el título debajo, sin el "UNIDAD N." en bruto. */}
                <span className="min-w-0">
                  <span className="eyebrow block text-blue-900">
                    Unidad {splitUnitName(topic.name).number ?? topic.order + 1}
                  </span>
                  <span className="mt-1 block font-semibold leading-snug text-ink-900">
                    {splitUnitName(topic.name).title}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  {pendingInTopic > 0 && (
                    <span className="tabular rounded-full bg-soft-butter px-2.5 py-0.5 text-[0.6875rem] font-bold text-deep-butter">
                      {pendingInTopic} pendientes
                    </span>
                  )}
                  <FontAwesomeIcon
                    icon={faChevronDown}
                    className={cn('text-[0.7rem] text-ink-400 transition-transform duration-200 ease-out', expanded && 'rotate-180')}
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
                        total: subtopic.question_count ?? 0,
                        pending: 0,
                      }))
                  ).map((item) => (
                    <li key={item.subtopic_id}>
                      <div
                        className={cn(
                          'flex items-center justify-between gap-3 px-4 py-3 text-sm sm:px-5',
                          bankOpen && selectedSubtopic === item.subtopic_id && 'bg-soft-sky',
                        )}
                      >
                        <span className="min-w-0 flex-1">
                          <span className="block break-words font-medium leading-relaxed text-ink-700">{item.title}</span>
                          <span className="tabular mt-1 block text-xs text-ink-500">
                          {(item.approved ?? item.total) + (item.practice ?? 0)} {(item.approved ?? item.total) + (item.practice ?? 0) === 1 ? 'pregunta disponible' : 'preguntas disponibles'}
                          </span>
                        </span>
                        <Button
                          type="button"
                          variant="secondary"
                          size="icon"
                          icon={faEye}
                          className="h-11 w-11 shrink-0"
                          aria-label={`Ver preguntas y respuestas de ${item.title}`}
                          title="Ver preguntas y respuestas"
                          aria-haspopup="dialog"
                          aria-controls="question-bank-dialog"
                          onClick={() => selectSubtopic(item.subtopic_id)}
                        />
                      </div>
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
        <dialog
          ref={dialogRef}
          id="question-bank-dialog"
          aria-labelledby="question-bank-title"
          aria-describedby="question-bank-subtopic"
          onCancel={(event) => { event.preventDefault(); closeBank() }}
          onClick={(event) => { if (event.target === event.currentTarget) closeBank() }}
          className="m-auto max-h-[100dvh] w-full max-w-3xl overflow-hidden border-0 bg-white p-0 text-ink-900 shadow-e4 backdrop:bg-ink-950/40 sm:max-h-[calc(100dvh-3rem)] sm:w-[calc(100%-3rem)] sm:rounded-xl"
        >
          <div className="flex max-h-[100dvh] flex-col sm:max-h-[calc(100dvh-3rem)]">
            <header className="flex shrink-0 items-start justify-between gap-3 border-b border-ink-200 bg-white p-4 sm:px-6 sm:py-5">
              <div className="min-w-0">
                <h2 id="question-bank-title" className="text-lg font-semibold sm:text-xl">Preguntas y respuestas</h2>
                <p id="question-bank-subtopic" className="mt-1 break-words text-sm text-ink-600">{selectedSubtopicName}</p>
              </div>
              <Button ref={closeButtonRef} type="button" variant="ghost" size="icon" icon={faXmark} className="h-11 w-11 shrink-0" aria-label="Cerrar preguntas y respuestas" onClick={closeBank} />
            </header>
            <div ref={bankContentRef} className="min-h-0 overflow-y-auto overscroll-contain bg-ink-50 p-4 sm:p-6">
              <p className="text-sm text-ink-600">
                Preguntas disponibles para los estudiantes de este curso.
              </p>

              <p aria-live="polite" className="sr-only">
                {actionMessage ?? ''}
              </p>

              {actionError && (
                <p role="alert" className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-3.5 py-2.5 text-sm text-wrong-700">
                  {actionError}
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
                    Este subtema no tiene preguntas disponibles en este curso.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {questions.map((question) => (
                      <div key={question.id}>
                        <QuestionCard
                          question={question}
                          busy={busy}
                          onEdit={(q) => { setEditing(q); setFormError(null); bankContentRef.current?.scrollTo({ top: 0 }) }}
                          onDelete={handleDelete}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </dialog>
      )}
    </section>
  )
}
