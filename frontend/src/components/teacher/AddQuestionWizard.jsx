import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faXmark } from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'
import { optionDraftError, validateQuestionDraft } from '../../lib/questionValidation'
import { createTeacherQuestion } from '../../services/questionService'

const LETTERS = ['A', 'B', 'C', 'D']
const EMPTY_OPTIONS = ['', '', '', '']

function splitUnitName(name) {
  const match = (name ?? '').match(/^(?:Unidad|M[oó]dulo)\s*(\d+)\s*[-—–:]?\s*(.*)$/i)
  if (!match) return { number: null, title: name ?? '' }
  return { number: Number(match[1]), title: match[2] || name }
}

/**
 * Asistente "Agregar preguntas": carga rápida de muchas preguntas seguidas.
 *
 * Un solo formulario: unidad → subtema (selectores dependientes) → enunciado →
 * 4 opciones A–D con la correcta marcada → explicación opcional.
 *
 * Dos botones de guardado:
 * - "Guardar y agregar otra": conserva unidad y subtema, limpia enunciado,
 *   opciones, correcta y explicación, muestra confirmación y devuelve el
 *   foco al enunciado.
 * - "Guardar y salir": guarda y cierra el asistente.
 */
export default function AddQuestionWizard({
  topics,
  initialSubtopicId = null,
  onClose,
  onSaved,
}) {
  const topicsList = topics ?? []
  const subtopicById = new Map(
    topicsList.flatMap((topic) =>
      (topic.subtopics ?? []).map((subtopic) => [subtopic.id, { topic, subtopic }]),
    ),
  )

  const initial = initialSubtopicId != null ? subtopicById.get(initialSubtopicId) : null

  const [topicId, setTopicId] = useState(initial?.topic.id ?? null)
  const [subtopicId, setSubtopicId] = useState(initial?.subtopic.id ?? null)
  const [prompt, setPrompt] = useState('')
  const [options, setOptions] = useState([...EMPTY_OPTIONS])
  const [correctIndex, setCorrectIndex] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [explanation, setExplanation] = useState('')
  const [saving, setSaving] = useState(false)
  const [serverError, setServerError] = useState(null)
  const [savedCount, setSavedCount] = useState(0)

  const dialogRef = useRef(null)
  const promptRef = useRef(null)

  const validation = validateQuestionDraft({ prompt, options, correctIndex })
  const canSave = validation.valid && subtopicId != null

  // Foco al abrir: el enunciado si ya viene con subtema precargado, si no
  // el select de unidad.
  useEffect(() => {
    const target = subtopicId != null && topicId != null ? promptRef.current : dialogRef.current
    target?.focus?.()
  }, [])

  const dirty =
    prompt.trim() !== '' ||
    options.some((option) => option.trim() !== '') ||
    correctIndex !== null ||
    explanation.trim() !== ''

  const requestClose = () => {
    if (savedCount > 0 || !dirty) {
      onClose()
      return
    }
    if (window.confirm('Tienes una pregunta sin guardar. ¿Cerrar de todas formas?')) {
      onClose()
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      event.stopPropagation()
      requestClose()
    }
  }

  const selected = subtopicId != null ? subtopicById.get(subtopicId) : null

  /** Conserva unidad y subtema; limpia solo el contenido de la pregunta. */
  const resetQuestion = () => {
    setPrompt('')
    setOptions([...EMPTY_OPTIONS])
    setCorrectIndex(null)
    setExplanation('')
    setShowExplanation(false)
    setServerError(null)
  }

  const focusPrompt = () => promptRef.current?.focus?.()

  const save = async ({ exit }) => {
    setSaving(true)
    setServerError(null)
    try {
      await createTeacherQuestion(subtopicId, {
        prompt: validation.trimmed,
        options: validation.cleaned,
        correct_index: correctIndex,
        explanation: explanation.trim(),
      })
      setSavedCount((count) => count + 1)
      onSaved?.(subtopicId)
      if (!exit) {
        // Conserva unidad/subtema, limpia el resto y devuelve el foco al enunciado.
        resetQuestion()
        focusPrompt()
      }
      return true
    } catch (error) {
      // 409 duplicado / 422 / 403: conserva lo escrito y muestra el motivo.
      setServerError(error.message || 'No se pudo guardar la pregunta.')
      focusPrompt()
      return false
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAndAdd = async () => {
    await save({ exit: false })
  }

  const handleSaveAndExit = async () => {
    const ok = await save({ exit: true })
    if (ok) onClose()
  }

  const advanced = savedCount > 0

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-ink-950/40 p-0 sm:items-center sm:p-6"
      onClick={(event) => {
        if (event.target === event.currentTarget) requestClose()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Agregar preguntas"
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="max-h-[92dvh] w-full max-w-[36rem] animate-scale-in overflow-y-auto rounded-t-2xl border border-ink-200 bg-white shadow-e4 sm:rounded-2xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-ink-200 px-5 py-4">
          <h2 className="text-base font-semibold text-ink-900">Agregar preguntas</h2>
          <button
            type="button"
            onClick={requestClose}
            aria-label="Cerrar el asistente"
            className="rounded-lg p-1.5 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-700"
          >
            <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
          </button>
        </header>

        <div className="space-y-4 px-5 py-4">
          {/* Confirmación tras guardar: no bloquea, no roba el foco. */}
          {advanced && !serverError && !saving && (
            <p
              role="status"
              aria-live="polite"
              className="rounded-xl border border-correct-200 bg-correct-50 px-3.5 py-2.5 text-sm font-medium text-correct-700"
            >
              <FontAwesomeIcon icon={faCheck} className="mr-1.5" aria-hidden="true" />
              Pregunta guardada{selected ? ` en ${selected.subtopic.name}` : ''}.
              {savedCount > 1 && (
                <span className="tabular ml-1">({savedCount} en esta sesión)</span>
              )}
            </p>
          )}

          {serverError && (
            <p
              role="alert"
              aria-live="assertive"
              className="rounded-xl border border-wrong-200 bg-wrong-50 px-3.5 py-2.5 text-sm text-wrong-700"
            >
              {serverError}
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="wizard-topic" className="text-sm font-semibold text-ink-700">
                Unidad
              </label>
              <select
                id="wizard-topic"
                value={topicId ?? ''}
                onChange={(event) => {
                  setTopicId(Number(event.target.value))
                  setSubtopicId(null)
                }}
                className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3 py-2 text-[0.9375rem] text-ink-900 outline-none transition-colors focus:border-blue-400"
              >
                <option value="" disabled>
                  Elegir unidad…
                </option>
                {topicsList.map((topic) => {
                  const { number, title } = splitUnitName(topic.name)
                  return (
                    <option key={topic.id} value={topic.id}>
                      {number != null ? `Unidad ${number} — ${title}` : topic.name}
                    </option>
                  )
                })}
              </select>
            </div>
            <div>
              <label htmlFor="wizard-subtopic" className="text-sm font-semibold text-ink-700">
                Subtema
              </label>
              <select
                id="wizard-subtopic"
                value={subtopicId ?? ''}
                onChange={(event) => setSubtopicId(Number(event.target.value))}
                disabled={topicId == null}
                className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3 py-2 text-[0.9375rem] text-ink-900 outline-none transition-colors focus:border-blue-400 disabled:bg-ink-50 disabled:text-ink-400"
              >
                <option value="" disabled>
                  {topicId == null ? 'Elige una unidad primero' : 'Elegir subtema…'}
                </option>
                {(topicsList.find((topic) => topic.id === topicId)?.subtopics ?? []).map(
                  (subtopic) => (
                    <option key={subtopic.id} value={subtopic.id}>
                      {subtopic.name}
                    </option>
                  ),
                )}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="wizard-prompt" className="text-sm font-semibold text-ink-700">
              Enunciado
            </label>
            <textarea
              id="wizard-prompt"
              ref={promptRef}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={2}
              maxLength={500}
              className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[0.9375rem] leading-relaxed text-ink-900 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              placeholder="Escribe la pregunta tal como la verán los estudiantes…"
            />
            <p className="mt-1 text-[0.75rem] text-ink-400">
              Entre 5 y 500 caracteres.
              {prompt.length > 0 && !validation.promptOk && (
                <span className="font-semibold text-wrong-700">
                  {prompt.trim().length < 5 ? ' Muy corta.' : ' Muy larga.'}
                </span>
              )}
            </p>
          </div>

          <fieldset>
            <legend className="text-sm font-semibold text-ink-700">
              Respuestas <span className="font-normal text-ink-400">(marca la correcta)</span>
            </legend>
            <div className="mt-2 space-y-2.5">
              {options.map((option, index) => {
                const error = optionDraftError(options, index)
                return (
                  <div key={index} className="flex items-start gap-2.5">
                    <label
                      className={cn(
                        'mt-2 flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-xl border text-xs font-bold transition-colors duration-150',
                        correctIndex === index
                          ? 'border-correct-500 bg-correct-500 text-white'
                          : 'border-ink-200 bg-white text-ink-500 hover:border-blue-300',
                      )}
                      title="Marcar como respuesta correcta"
                    >
                      <input
                        type="radio"
                        name="wizard-correct-option"
                        className="sr-only"
                        checked={correctIndex === index}
                        onChange={() => setCorrectIndex(index)}
                        aria-label={`Opción ${LETTERS[index]} es la correcta`}
                      />
                      {LETTERS[index]}
                    </label>
                    <div className="min-w-0 flex-1">
                      <input
                        type="text"
                        value={option}
                        onChange={(event) =>
                          setOptions((current) =>
                            current.map((o, i) => (i === index ? event.target.value : o)),
                          )
                        }
                        maxLength={300}
                        className={cn(
                          'w-full rounded-xl border bg-white px-3.5 py-2 text-[0.9375rem] text-ink-900 outline-none transition-colors focus:ring-2',
                          error
                            ? 'border-wrong-500 focus:ring-wrong-100'
                            : 'border-ink-200 focus:border-blue-400 focus:ring-blue-100',
                        )}
                        placeholder={`Respuesta ${LETTERS[index]}`}
                        aria-label={`Texto de la respuesta ${LETTERS[index]}`}
                      />
                      {error && (
                        <p className="mt-1 text-[0.75rem] font-medium text-wrong-700">{error}</p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
            {!validation.hasCorrect && (
              <p className="mt-2 text-[0.75rem] font-medium text-wrong-700">
                Marca cuál de las cuatro respuestas es la correcta.
              </p>
            )}
          </fieldset>

          <div>
            <button
              type="button"
              onClick={() => setShowExplanation((visible) => !visible)}
              className="text-sm font-semibold text-blue-800 underline"
              aria-expanded={showExplanation}
            >
              {showExplanation ? 'Quitar explicación' : 'Agregar explicación (opcional)'}
            </button>
            {showExplanation && (
              <textarea
                value={explanation}
                onChange={(event) => setExplanation(event.target.value)}
                rows={2}
                maxLength={1000}
                className="mt-2 w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[0.9375rem] leading-relaxed text-ink-900 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                placeholder="¿Por qué esa es la respuesta correcta?"
                aria-label="Explicación (opcional)"
              />
            )}
          </div>

          <div className="flex flex-col gap-2.5 border-t border-ink-100 pt-4 sm:flex-row sm:justify-end">
            <Button
              variant="primary"
              onClick={handleSaveAndAdd}
              disabled={!canSave || saving}
            >
              Guardar y agregar otra
            </Button>
            <Button
              variant="secondary"
              onClick={handleSaveAndExit}
              disabled={!canSave || saving}
            >
              {saving ? 'Guardando…' : 'Guardar y salir'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
