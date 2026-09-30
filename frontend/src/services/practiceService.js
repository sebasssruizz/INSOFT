import { apiFetch } from './api'

/**
 * Modo práctica: sesiones cortas de banco + IA reutilizable.
 *
 * El servidor genera `attempt_id` y devuelve las preguntas SIN la respuesta
 * correcta; la calificación sigue ocurriendo en POST /quiz/answers.
 */

export const startPracticeSession = ({ subtopicId, topicId, count } = {}) =>
  apiFetch('/practice/sessions', {
    method: 'POST',
    body: {
      subtopic_id: subtopicId ?? null,
      topic_id: topicId ?? null,
      count: count ?? undefined,
    },
  })
