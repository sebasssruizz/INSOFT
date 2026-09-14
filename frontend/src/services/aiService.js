import { apiFetch } from './api'

export const askAi = (question, subtopicId) =>
  apiFetch('/ai/ask', {
    method: 'POST',
    body: { question, subtopic_id: subtopicId ?? null },
  })