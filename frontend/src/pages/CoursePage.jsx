import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck } from '@fortawesome/free-solid-svg-icons'
import { useAuth } from '../hooks/useAuth'
import { getCourseTopics } from '../services/contentService'
import { getCourse } from '../services/courseService'

function TopicBlock({ topic, courseId, isStudent }) {
  const percentage =
    topic.total_subtopics > 0 ? Math.round((topic.completed_subtopics / topic.total_subtopics) * 100) : 0

  return (
    <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="font-semibold text-slate-900">{topic.name}</h3>
          {topic.description && <p className="text-sm text-slate-500 mt-1">{topic.description}</p>}
        </div>
        {isStudent && (
          <span className="text-sm font-medium text-oft-700 whitespace-nowrap">
            {topic.completed_subtopics}/{topic.total_subtopics} · {percentage}%
          </span>
        )}
      </div>

      <ul className="mt-4 divide-y divide-slate-100">
        {topic.subtopics.map((sub) => (
          <li key={sub.id}>
            <Link
              to={`/courses/${courseId}/subtopics/${sub.id}`}
              className="flex items-center justify-between py-2.5 px-2 rounded-lg hover:bg-oft-50 transition-colors group"
            >
              <span className="text-sm text-slate-700 group-hover:text-oft-800">{sub.name}</span>
              {isStudent &&
                (sub.completed ? (
                  <span className="text-xs font-medium text-ins-600 flex items-center gap-1">
                    <FontAwesomeIcon icon={faCircleCheck} />
                    Completado
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">Pendiente</span>
                ))}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function CoursePage() {
  const { courseId } = useParams()
  const { user } = useAuth()
  const isStudent = user?.role === 'STUDENT'
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
      <Link to="/dashboard" className="text-sm text-oft-600 hover:text-oft-800 font-medium">
        ← Volver a mis cursos
      </Link>

      <h1 className="text-2xl font-bold text-slate-900 mt-3">{course?.name}</h1>
      {course?.description && <p className="text-slate-500 mt-1">{course.description}</p>}

      <h2 className="text-lg font-semibold text-slate-900 mt-8 mb-4">Contenido oficial de Oftalmología</h2>

      <div className="space-y-4">
        {topics.map((topic) => (
          <TopicBlock key={topic.id} topic={topic} courseId={courseId} isStudent={isStudent} />
        ))}
      </div>
    </div>
  )
}
