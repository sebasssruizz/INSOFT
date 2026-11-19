import { apiFetch } from './api'

export const askAi = (question, courseId, subtopicId, context = {}) =>
  apiFetch('/ai/ask', {
    method: 'POST',
    body: {
      question,
      course_id: courseId ?? null,
      subtopic_id: subtopicId ?? null,
      ...context,
    },
  })

export const getAiConversation = (sessionId, courseId) =>
  apiFetch(`/ai/history?session_id=${encodeURIComponent(sessionId)}&limit=50&${courseId == null ? 'global_only=true' : `course_id=${courseId}`}`)

export const rateAiAnswer = (queryId, feedback) =>
  apiFetch(`/ai/answers/${queryId}/feedback`, { method: 'PUT', body: feedback })
