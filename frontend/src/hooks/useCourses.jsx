import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { listCourses } from '../services/courseService'

const CoursesContext = createContext(null)

/**
 * Cursos del usuario, compartidos por toda la aplicación autenticada.
 *
 * Vive por encima de las páginas para que al completar un subtema el progreso
 * se actualice a la vez en la barra lateral, en la cabecera del curso y en el
 * panel de inicio, sin volver a pedir la lista en cada pantalla.
 */
export function CoursesProvider({ children }) {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      setError(null)
      setCourses(await listCourses())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = useMemo(
    () => ({ courses, loading, error, refresh }),
    [courses, loading, error, refresh],
  )

  return <CoursesContext.Provider value={value}>{children}</CoursesContext.Provider>
}

export function useCourses() {
  const context = useContext(CoursesContext)
  if (!context) throw new Error('useCourses debe usarse dentro de CoursesProvider')
  return context
}
