import { apiFetch } from './api'

/**
 * Servicio del banco de preguntas del profesor.
 *
 * Los errores propagan ApiError (status + detail del backend) para que la UI
 * muestre mensajes específicos (409 duplicado, 422 validación, 429 límite,
 * 502 IA sin respuesta válida, 503 cuota).
 */

export const getSubtopicQuestionBank = (subtopicId, { status, source } = {}) => {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (source) params.set('source', source)
  const query = params.toString() ? `?${params.toString()}` : ''
  return apiFetch(`/content/subtopics/${subtopicId}/questions/bank${query}`)
}

export const getTopicQuestionSummary = (topicId) =>
  apiFetch(`/content/topics/${topicId}/questions/summary`)

export const createTeacherQuestion = (subtopicId, payload) =>
  apiFetch(`/content/subtopics/${subtopicId}/questions`, { method: 'POST', body: payload })

export const updateQuestion = (questionId, payload) =>
  apiFetch(`/content/questions/${questionId}`, { method: 'PATCH', body: payload })

export const deleteQuestion = (questionId) =>
  apiFetch(`/content/questions/${questionId}`, { method: 'DELETE' })

export const reviewPendingQuestion = (questionId, action) =>
  apiFetch(`/content/questions/${questionId}/review`, { method: 'POST', body: { action } })

export const generateAiQuestions = ({ subtopicId, topicId, count }) =>
  apiFetch('/ai/questions/generate', {
    method: 'POST',
    body: {
      subtopic_id: subtopicId ?? null,
      topic_id: topicId ?? null,
      count,
    },
  })
