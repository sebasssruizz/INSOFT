const LETTERS = ['A', 'B', 'C', 'D']

/**
 * Validación compartida de una pregunta manual (usada por QuestionForm y por
 * el asistente "Agregar pregunta"). Reglas del backend: enunciado 5–500,
 * 4 opciones obligatorias y no repetidas (insensible a mayúsculas), una
 * correcta marcada.
 */
export function validateQuestionDraft({ prompt, options, correctIndex }) {
  const trimmed = (prompt ?? '').trim()
  const cleaned = (options ?? []).map((option) => (option ?? '').trim())
  const filled = cleaned.every((option) => option.length > 0)
  const unique = new Set(cleaned.map((option) => option.toLowerCase())).size === 4
  const promptOk = trimmed.length >= 5 && trimmed.length <= 500
  const hasCorrect = correctIndex !== null && correctIndex !== undefined
  return {
    trimmed,
    cleaned,
    letters: LETTERS,
    promptOk,
    optionsOk: filled && unique,
    hasCorrect,
    valid: promptOk && filled && unique && hasCorrect,
  }
}

/** Error legible por campo para la opción i (obligatoria / repetida). */
export function optionDraftError(options, index) {
  const value = options[index]?.trim() ?? ''
  if (!value) return 'Esta opción es obligatoria.'
  const duplicate = options.some(
    (option, i) => i !== index && (option ?? '').trim().toLowerCase() === value.toLowerCase(),
  )
  if (duplicate) return 'Esta opción está repetida.'
  return null
}
