import { useMemo, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

const LETTERS = ['A', 'B', 'C', 'D']
const EMPTY_OPTIONS = ['', '', '', '']

/**
 * Formulario de creación/edición manual de preguntas del profesor.
 *
 * Reglas: enunciado no vacío, las 4 opciones (A-D) obligatorias y no
 * repetidas, y una correcta marcada. Sin eso, el botón de enviar queda
 * deshabilitado. Incluye vista previa en vivo como la verá el estudiante.
 */
export default function QuestionForm({ initial, onSubmit, onCancel, submitting, serverError }) {
  const editing = Boolean(initial?.id)
  const [prompt, setPrompt] = useState(initial?.prompt ?? '')
  const [options, setOptions] = useState(
    initial?.options?.length === 4 ? [...initial.options] : [...EMPTY_OPTIONS],
  )
  const [correctIndex, setCorrectIndex] = useState(initial?.correct_index ?? null)
  const [explanation, setExplanation] = useState(initial?.explanation ?? '')
  const [showPreview, setShowPreview] = useState(false)

  const validation = useMemo(() => {
    const trimmed = prompt.trim()
    const cleaned = options.map((option) => option.trim())
    const filled = cleaned.every((option) => option.length > 0)
    const unique = new Set(cleaned.map((option) => option.toLowerCase())).size === 4
    const hasCorrect = correctIndex !== null
    return {
      trimmed,
      cleaned,
      promptOk: trimmed.length >= 5 && trimmed.length <= 500,
      optionsOk: filled && unique,
      hasCorrect,
      valid: trimmed.length >= 5 && trimmed.length <= 500 && filled && unique && hasCorrect,
    }
  }, [prompt, options, correctIndex])

  const setOption = (index, value) => {
    setOptions((current) => current.map((option, i) => (i === index ? value : option)))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!validation.valid || submitting) return
    onSubmit({
      prompt: validation.trimmed,
      options: validation.cleaned,
      correct_index: correctIndex,
      explanation: explanation.trim(),
    })
  }

  const optionError = (index) => {
    const value = options[index]?.trim() ?? ''
    if (!value) return 'Esta opción es obligatoria.'
    const duplicate = options.some(
      (option, i) => i !== index && option.trim().toLowerCase() === value.toLowerCase(),
    )
    if (duplicate) return 'Esta opción está repetida.'
    return null
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-ink-200 bg-white p-5 sm:p-6"
      aria-busy={submitting}
    >
      <h3 className="text-lg font-semibold text-ink-900">
        {editing ? 'Editar pregunta' : 'Nueva pregunta'}
      </h3>

      <div className="mt-4">
        <label htmlFor="question-prompt" className="text-sm font-semibold text-ink-700">
          Enunciado
        </label>
        <textarea
          id="question-prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={2}
          required
          minLength={5}
          maxLength={500}
          className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[0.9375rem] leading-relaxed text-ink-900 outline-none transition-colors duration-150 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          placeholder="Escribe la pregunta tal como la verán los estudiantes…"
        />
        <p className="mt-1 text-[0.75rem] text-ink-400">
          Entre 5 y 500 caracteres.{' '}
          {prompt.length > 0 && !validation.promptOk && (
            <span className="font-semibold text-wrong-700">
              {prompt.trim().length < 5 ? 'Muy corto.' : 'Muy largo.'}
            </span>
          )}
        </p>
      </div>

      <fieldset className="mt-4">
        <legend className="text-sm font-semibold text-ink-700">
          Opciones de respuesta <span className="font-normal text-ink-400">(marca la correcta)</span>
        </legend>
        <div className="mt-2 space-y-2.5">
          {options.map((option, index) => {
            const error = optionError(index)
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
                    name="correct-option"
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
                    onChange={(event) => setOption(index, event.target.value)}
                    maxLength={300}
                    className={cn(
                      'w-full rounded-xl border bg-white px-3.5 py-2 text-[0.9375rem] text-ink-900 outline-none transition-colors duration-150 focus:ring-2',
                      error
                        ? 'border-wrong-500 focus:ring-wrong-100'
                        : 'border-ink-200 focus:border-blue-400 focus:ring-blue-100',
                    )}
                    placeholder={`Opción ${LETTERS[index]}`}
                    aria-label={`Texto de la opción ${LETTERS[index]}`}
                  />
                  {error && <p className="mt-1 text-[0.75rem] font-medium text-wrong-700">{error}</p>}
                </div>
              </div>
            )
          })}
        </div>
        {!validation.hasCorrect && (
          <p className="mt-2 text-[0.75rem] font-medium text-wrong-700">
            Marca cuál de las cuatro opciones es la correcta.
          </p>
        )}
      </fieldset>

      <div className="mt-4">
        <label htmlFor="question-explanation" className="text-sm font-semibold text-ink-700">
          Explicación <span className="font-normal text-ink-400">(opcional)</span>
        </label>
        <textarea
          id="question-explanation"
          value={explanation}
          onChange={(event) => setExplanation(event.target.value)}
          rows={2}
          maxLength={1000}
          className="mt-1.5 w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[0.9375rem] leading-relaxed text-ink-900 outline-none transition-colors duration-150 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          placeholder="¿Por qué esa es la respuesta correcta?"
        />
      </div>

      {serverError && (
        <p
          role="alert"
          aria-live="assertive"
          className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-3.5 py-2.5 text-sm text-wrong-700"
        >
          {serverError}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2.5">
        <Button type="submit" variant="primary" disabled={!validation.valid || submitting}>
          {submitting ? 'Guardando…' : editing ? 'Guardar cambios' : 'Agregar pregunta'}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
            Cancelar
          </Button>
        )}
        <Button
          type="button"
          variant="ghost"
          icon={showPreview ? faEyeSlash : faEye}
          onClick={() => setShowPreview((visible) => !visible)}
        >
          {showPreview ? 'Ocultar vista previa' : 'Vista previa'}
        </Button>
      </div>

      {showPreview && (
        <div className="mt-5 rounded-2xl border border-dashed border-ink-300 bg-ink-50 p-5">
          <p className="eyebrow text-ink-400">Así la verá el estudiante</p>
          <p className="mt-2 text-[0.9375rem] font-medium leading-relaxed text-ink-900">
            {validation.trimmed || '…'}
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
                <span className="pt-0.5 text-ink-700">{option || `Opción ${LETTERS[index]}`}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </form>
  )
}
