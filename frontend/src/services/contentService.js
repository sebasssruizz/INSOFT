import { apiFetch } from './api'

export const getCourseTopics = (courseId) => apiFetch(`/courses/${courseId}/topics`)

export const getSubtopic = (subtopicId, courseId) =>
  apiFetch(`/subtopics/${subtopicId}?course_id=${courseId}`)
