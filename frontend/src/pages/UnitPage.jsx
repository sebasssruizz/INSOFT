import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCircleCheck } from '@fortawesome/free-solid-svg-icons'
import { useAuth } from '../hooks/useAuth'
import { getCourseTopics } from '../services/contentService'
import { getCourse } from '../services/courseService'

export default function UnitPage() {
  const { courseId, topicId } = useParams()
  const { user } = useAuth()
  const isStudent = user?.role === 'STUDENT'
  const [course, setCourse] = useState(null)
  const [topic, setTopic] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [courseData, topicsData] = await Promise.all([getCourse(courseId), getCourseTopics(courseId)])
      setCourse(courseData)
      setTopic(topicsData.find((item) => String(item.id) === String(topicId)) || null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [courseId, topicId])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <p className="text-slate-500">Cargando unidad…</p>
  if (error) return <p className="text-red-600">{error}</p>
  if (!topic) return <p className="text-red-600">Unidad no encontrada.</p>

  const unitNumber = topic.order + 1

  return (
    <div>
      <Link to={`/courses/${courseId}`} className="text-sm font-medium text-oft-600 hover:text-oft-800">
        ← Volver a las unidades
      </Link>

      <header className="mt-5 border-b border-surgery-200 pb-6">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-oft-600">
          {course?.name} · Unidad {unitNumber}
        </p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{topic.name}</h1>
        {topic.description && <p className="mt-2 max-w-3xl text-slate-500">{topic.description}</p>}
      </header>

      <div className="mt-6 grid gap-3">
        {topic.subtopics.map((sub) => (
          <Link
            key={sub.id}
            to={`/courses/${courseId}/subtopics/${sub.id}`}
            aria-label={`Abrir subtema ${sub.name}`}
            className="group flex min-h-[68px] items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-ins-sm transition-all hover:border-oft-300 hover:bg-oft-50 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-oft-500 focus-visible:ring-offset-1"
          >
            <span className="flex min-w-0 items-center gap-4">
              <span className="text-xs font-bold text-oft-500">{String(sub.order + 1).padStart(2, '0')}</span>
              <span className="text-sm font-medium text-slate-700 group-hover:text-oft-800">{sub.name}</span>
            </span>
            <span className="flex shrink-0 items-center gap-3">
              {isStudent &&
                (sub.completed ? (
                  <span className="flex items-center gap-1 text-xs font-medium text-ins-600">
                    <FontAwesomeIcon icon={faCircleCheck} />
                    Completado
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">Pendiente</span>
                ))}
              <FontAwesomeIcon
                icon={faArrowRight}
                className="text-xs text-slate-300 transition-transform group-hover:translate-x-1 group-hover:text-oft-600"
              />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
