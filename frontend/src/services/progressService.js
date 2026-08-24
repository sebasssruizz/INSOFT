import { apiFetch } from './api'

export const setProgress = (courseId, subtopicId, completed) =>
  apiFetch('/progress', {
    method: 'POST',
    body: { course_id: courseId, subtopic_id: subtopicId, completed },
  })

export const getCourseProgress = (courseId) => apiFetch(`/progress/course?course_id=${courseId}`)

export const getAllProgress = () => apiFetch('/progress')
