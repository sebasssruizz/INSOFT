import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCheck,
  faPencil,
  faPlus,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

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
 * Asistente "Agregar pregunta": carga rápida de muchas preguntas seguidas.
 *
 * Paso 1: módulo → submódulo → enunciado → A–D + correcta → explicación (opcional).
 * Paso 2: resumen de solo lectura con "Editar" / "Confirmar y guardar".
 * Paso 3: éxito con "Agregar otra en este submódulo", "Agregar en otro submódulo"
 * y "Terminar", con contador de la sesión.
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

  const [step, setStep] = useState(1)
  const [topicId, setTopicId] = useState(initial?.topic.id ?? null)
  const [subtopicId, setSubtopicId] = useState(initial?.subtopic.id ?? null)
  const [prompt, setPrompt] = useState('')
  const [options, setOptions] = useState([...EMPTY_OPTIONS])
  const [correctIndex, setCorrectIndex] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [explanation, setExplanation] = useState('')
  const [saving, setSaving] = useState(false)
  const [serverError, setServerError] = useState(null)
  const [addedCount, setAddedCount] = useState(0)

  const dialogRef = useRef(null)
  const promptRef = useRef(null)
  const stepRef = useRef(1)

  const validation = validateQuestionDraft({ prompt, options, correctIndex })
  const canContinue = validation.valid && subtopicId != null

  // Foco al abrir y al cambiar de paso (el paso 1 enfoca el enunciado si ya
  // viene con submódulo precargado, si no el select de módulo).
  useEffect(() => {
    if (step === 1) {
      const target = subtopicId != null && topicId != null ? promptRef.current : dialogRef.current
      target?.focus?.()
    } else {
      dialogRef.current?.focus?.()
    }
    stepRef.current = step
  }, [step, subtopicId, topicId])

  const dirty =
    prompt.trim() !== '' ||
    options.some((option) => option.trim() !== '') ||
    correctIndex !== null ||
    explanation.trim() !== ''

  const requestClose = () => {
    if (step === 3 || !dirty) {
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

  const resetForm = ({ keepLocation }) => {
    setPrompt('')
    setOptions([...EMPTY_OPTIONS])
    setCorrectIndex(null)
    setExplanation('')
    setShowExplanation(false)
    setServerError(null)
    if (!keepLocation) {
      setTopicId(null)
      setSubtopicId(null)
    }
  }

  const confirmSave = async () => {
    setSaving(true)
    setServerError(null)
    try {
      const created = await createTeacherQuestion(subtopicId, {
        prompt: validation.trimmed,
        options: validation.cleaned,
        correct_index: correctIndex,
        explanation: explanation.trim(),
      })
      setAddedCount((count) => count + 1)
      onSaved?.(created, subtopicId)
      setStep(3)
    } catch (error) {
      // 409 duplicado / 422 / 403: vuelve al paso 1 conservando lo escrito.
      setServerError(error.message || 'No se pudo guardar la pregunta.')
      setStep(1)
    } finally {
      setSaving(false)
    }
  }

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
        aria-label="Agregar pregunta"
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="max-h-[92dvh] w-full max-w-[36rem] animate-scale-in overflow-y-auto rounded-t-2xl border border-ink-200 bg-white shadow-e4 sm:rounded-2xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-ink-200 px-5 py-4">
          <h2 className="text-base font-semibold text-ink-900">Agregar pregunta</h2>
          <button
            type="button"
            onClick={requestClose}
            aria-label="Cerrar el asistente"
            className="rounded-lg p-1.5 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-700"
          >
            <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
          </button>
        </header>

        {serverError && (
          <p
            role="alert"
            aria-live="assertive"
            className="mx-5 mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-3.5 py-2.5 text-sm text-wrong-700"
          >
            {serverError}
          </p>
        )}

        {/* Paso 1: formulario */}
        {step === 1 && (
          <div className="space-y-4 px-5 py-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="wizard-topic" className="text-sm font-semibold text-ink-700">
                  Módulo
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
                    Elegir módulo…
                  </option>
                  {topicsList.map((topic) => {
                    const { number, title } = splitUnitName(topic.name)
                    return (
                      <option key={topic.id} value={topic.id}>
                        {number != null ? `Módulo ${number} — ${title}` : topic.name}
                      </option>
                    )
                  })}
                </select>
              </div>
              <div>
                <label htmlFor="wizard-subtopic" className="text-sm font-semibold text-ink-700">
                  Submódulo
                </label>
                <select
                  id="wizard-subtopic"
                  value={subtopicId ?? ''}
                  onChange={(event) => setSubtopicId(Number(event.target.value))}
                  disabled={topicId == null}
                  className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3 py-2 text-[0.9375rem] text-ink-900 outline-none transition-colors focus:border-blue-400 disabled:bg-ink-50 disabled:text-ink-400"
                >
                  <option value="" disabled>
                    {topicId == null ? 'Elige un módulo primero' : 'Elegir submódulo…'}
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
                Pregunta
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

            <div className="flex justify-end gap-2.5 border-t border-ink-100 pt-4">
              <Button variant="secondary" onClick={requestClose}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={() => setStep(2)}
                disabled={!canContinue || saving}
              >
                Continuar
              </Button>
            </div>
          </div>
        )}

        {/* Paso 2: confirmación */}
        {step === 2 && (
          <div className="px-5 py-4">
            <p className="eyebrow text-ink-400">Así la verá el estudiante</p>
            <p className="mt-2 text-[0.75rem] font-semibold text-ink-500">
              {selected ? `${selected.topic.name} › ${selected.subtopic.name}` : ''}
            </p>
            <p className="mt-2 text-[0.9375rem] font-medium leading-relaxed text-ink-900">
              {validation.trimmed}
            </p>
            <ul className="mt-3 space-y-2">
              {validation.cleaned.map((option, index) => (
                <li
                  key={index}
                  className={cn(
                    'flex items-start gap-3 rounded-xl border bg-white px-3.5 py-2.5 text-sm',
                    correctIndex === index ? 'border-correct-300 bg-correct-50' : 'border-ink-200',
                  )}
                >
                  <span
                    className={cn(
                      'flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[0.6875rem] font-bold',
                      correctIndex === index ? 'bg-correct-500 text-white' : 'bg-ink-100 text-ink-600',
                    )}
                    aria-hidden="true"
                  >
                    {LETTERS[index]}
                  </span>
                  <span className="pt-0.5 text-ink-700">{option}</span>
                  {correctIndex === index && (
                    <FontAwesomeIcon
                      icon={faCheck}
                      className="ml-auto mt-1 text-correct-600"
                      aria-label="Respuesta correcta"
                    />
                  )}
                </li>
              ))}
            </ul>
            {explanation.trim() && (
              <p className="mt-3 rounded-xl bg-ink-50 px-3.5 py-2.5 text-sm text-ink-600">
                {explanation.trim()}
              </p>
            )}

            <div className="mt-5 flex flex-wrap justify-end gap-2.5 border-t border-ink-100 pt-4">
              <Button variant="secondary" icon={faPencil} onClick={() => setStep(1)} disabled={saving}>
                Editar
              </Button>
              <Button variant="primary" onClick={confirmSave} disabled={saving}>
                {saving ? 'Guardando…' : 'Confirmar y guardar'}
              </Button>
            </div>
          </div>
        )}

        {/* Paso 3: éxito */}
        {step === 3 && (
          <div className="px-5 py-6 text-center">
            <span
              className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-correct-50 text-correct-600"
              aria-hidden="true"
            >
              <FontAwesomeIcon icon={faCheck} className="text-lg" />
            </span>
            <h3 className="mt-3 text-lg font-semibold text-ink-900">Pregunta guardada</h3>
            <p className="mt-1.5 text-sm text-ink-500">
              Ya está visible para tus estudiantes.
              {addedCount > 0 && (
                <span className="block tabular mt-1 font-semibold text-ink-700">
                  Agregadas en esta sesión: {addedCount}
                </span>
              )}
            </p>
            <div className="mt-6 flex flex-col justify-center gap-2.5 sm:flex-row sm:flex-wrap">
              <Button
                variant="primary"
                icon={faPlus}
                onClick={() => {
                  resetForm({ keepLocation: true })
                  setStep(1)
                }}
              >
                Agregar otra en este submódulo
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  resetForm({ keepLocation: false })
                  setStep(1)
                }}
              >
                Agregar en otro submódulo
              </Button>
              <Button variant="ghost" onClick={onClose}>
                Terminar
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
