import { apiFetch } from './api'

export const listCourses = () => apiFetch('/courses')

export const getCourse = (courseId) => apiFetch(`/courses/${courseId}`)

export const createCourse = (name, description) =>
  apiFetch('/courses', { method: 'POST', body: { name, description } })

export const joinCourse = (code) => apiFetch('/courses/join', { method: 'POST', body: { code } })

export const getCourseStudents = (courseId) => apiFetch(`/courses/${courseId}/students`)
