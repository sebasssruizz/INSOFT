import { apiFetch } from './api'

/**
 * Respuestas de quiz calificadas en el servidor.
 *
 * El cliente no conoce la respuesta correcta: envía la opción elegida y
 * recibe is_correct, correct_index y la explicación.
 */

export const submitQuizAnswer = ({ questionId, selectedIndex, attemptId }) =>
  apiFetch('/quiz/answers', {
    method: 'POST',
    body: {
      question_id: questionId,
      selected_index: selectedIndex,
      attempt_id: attemptId,
    },
  })

export const newQuizAttemptId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
