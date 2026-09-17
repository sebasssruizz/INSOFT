import { apiFetch } from './api'

export const askAi = (question, courseId, subtopicId) =>
  apiFetch('/ai/ask', {
    method: 'POST',
    body: {
      question,
      course_id: courseId ?? null,
      subtopic_id: subtopicId ?? null,
    },
  })