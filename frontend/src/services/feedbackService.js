import { apiFetch } from './api'

export const sendEvaluation = (payload) => apiFetch('/feedback/evaluations', { method: 'POST', body: payload })
export const getFeedbackAccess = () => apiFetch('/feedback/access')
export const getFeedbackReviews = (kind, offset = 0) =>
  apiFetch(`/feedback/review?kind=${encodeURIComponent(kind)}&offset=${offset}&limit=20`)

export const sendFeedback = (feedback) =>
  apiFetch('/feedback', { method: 'POST', body: feedback })
