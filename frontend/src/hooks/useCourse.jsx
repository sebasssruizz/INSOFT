import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { getCourseTopics } from '../services/contentService'
import { getCourse } from '../services/courseService'
import { setProgress } from '../services/progressService'
import { useCourses } from './useCourses'

const CourseContext = createContext(null)

/**
 * Estado de un curso abierto: su ficha, sus unidades y el progreso del
 * estudiante.
 *
 * Vive en el contenedor del curso y no en cada pantalla, de modo que al marcar
 * un subtema desde dentro la cabecera, el índice lateral y la barra lateral de
 * la aplicación reflejan el avance sin recargar nada.
 */
export function CourseProvider({ courseId, children }) {
  const { refresh: refreshCourseList } = useCourses()
  const [course, setCourse] = useState(null)
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [courseData, topicsData] = await Promise.all([
        getCourse(courseId),
        getCourseTopics(courseId),
      ])
      setCourse(courseData)
      setTopics(topicsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    load()
  }, [load])

  /**
   * Marca o desmarca un subtema. Actualiza el estado local de inmediato para
   * que la barra de progreso responda al instante, y sincroniza después la
   * lista global de cursos.
   */
  const markSubtopic = useCallback(
    async (subtopicId, completed) => {
      const record = await setProgress(Number(courseId), Number(subtopicId), completed)

      setTopics((previous) =>
        previous.map((topic) => {
          if (!topic.subtopics.some((sub) => sub.id === Number(subtopicId))) return topic
          const subtopics = topic.subtopics.map((sub) =>
            sub.id === Number(subtopicId) ? { ...sub, completed: record.completed } : sub,
          )
          return {
            ...topic,
            subtopics,
            completed_subtopics: subtopics.filter((sub) => sub.completed).length,
          }
        }),
      )

      refreshCourseList()
      return record
    },
    [courseId, refreshCourseList],
  )

  const derived = useMemo(() => {
    const flat = topics.flatMap((topic) =>
      topic.subtopics.map((subtopic) => ({ ...subtopic, topic })),
    )
    const completed = flat.filter((subtopic) => subtopic.completed).length
    const remainingMinutes = flat
      .filter((subtopic) => !subtopic.completed)
      .reduce((sum, subtopic) => sum + (subtopic.estimated_minutes || 0), 0)

    return {
      flatSubtopics: flat,
      totalSubtopics: flat.length,
      completedSubtopics: completed,
      percentage: flat.length ? Math.round((completed / flat.length) * 100) : 0,
      totalMinutes: flat.reduce((sum, subtopic) => sum + (subtopic.estimated_minutes || 0), 0),
      remainingMinutes,
      totalQuestions: topics.reduce((sum, topic) => sum + (topic.question_count || 0), 0),
      /** Primer subtema sin completar: destino del botón "continuar". */
      nextSubtopic: flat.find((subtopic) => !subtopic.completed) || null,
    }
  }, [topics])

  const value = useMemo(
    () => ({
      courseId,
      course,
      topics,
      loading,
      error,
      refresh: load,
      markSubtopic,
      ...derived,
    }),
    [courseId, course, topics, loading, error, load, markSubtopic, derived],
  )

  return <CourseContext.Provider value={value}>{children}</CourseContext.Provider>
}

export function useCourse() {
  const context = useContext(CourseContext)
  if (!context) throw new Error('useCourse debe usarse dentro de CourseProvider')
  return context
}
