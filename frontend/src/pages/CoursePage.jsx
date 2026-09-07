import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getCourseTopics } from '../services/contentService'
import { getCourse } from '../services/courseService'

export default function CoursePage() {
  const { courseId } = useParams()
  const { user } = useAuth()
  const [course, setCourse] = useState(null)
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [courseData, topicsData] = await Promise.all([getCourse(courseId), getCourseTopics(courseId)])
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

  if (loading) return <p className="text-slate-500">Cargando curso…</p>
  if (error) return <p className="text-red-600">{error}</p>

  return (
    <div>
      <Link to="/dashboard" className="text-sm font-medium text-oft-600 hover:text-oft-800">
        ← Volver a mis cursos
      </Link>

      <header className="mt-5">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-oft-600">Contenido del curso</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{course?.name}</h1>
        {course?.description && <p className="mt-1 text-slate-500">{course.description}</p>}
      </header>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {topics.map((topic) => (
          <Link
            key={topic.id}
            to={`/courses/${courseId}/units/${topic.id}`}
            aria-label={`Abrir ${topic.name}`}
            className="group flex aspect-square items-center justify-center rounded-xl border border-surgery-200 bg-white p-5 text-center shadow-ins-sm transition-all duration-200 hover:-translate-y-1 hover:border-oft-300 hover:bg-oft-50 hover:shadow-ins-md focus:outline-none focus-visible:ring-2 focus-visible:ring-oft-500 focus-visible:ring-offset-2"
          >
            <h2 className="text-base font-semibold leading-snug text-slate-800 transition-colors group-hover:text-oft-800 sm:text-lg">
              {topic.name}
            </h2>
          </Link>
        ))}
      </div>

      {user?.role === 'TEACHER' && topics.length === 0 && (
        <p className="mt-6 text-sm text-slate-500">Este curso todavía no tiene unidades disponibles.</p>
      )}
    </div>
  )
}
