import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faBookOpen, faCircleCheck } from '@fortawesome/free-solid-svg-icons'
import JoinCourseForm from '../components/JoinCourseForm'
import ProgressBar from '../components/ProgressBar'
import { useAuth } from '../hooks/useAuth'
import { listCourses } from '../services/courseService'

function CourseCard({ course, index }) {
  const isGeneral = course.type === 'GENERAL'
  return (
    <article
      className="animate-fade-in-up group bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-lg hover:shadow-oft-100 hover:border-oft-300 hover:-translate-y-1 transition-all duration-200 overflow-hidden flex flex-col"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div
        className={`h-1 ${
          isGeneral ? 'bg-ins-500' : 'bg-oft-500'
        } group-hover:h-1.5 transition-all duration-200`}
      />
      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-slate-900 text-sm leading-snug">{course.name}</h3>
          {isGeneral && (
            <span className="shrink-0 text-[10px] font-semibold bg-ins-50 text-ins-700 border border-ins-200 rounded-full px-2 py-0.5">
              Oficial
            </span>
          )}
        </div>

        <div className="mt-3 flex-1 flex flex-col justify-end gap-2">
          <ProgressBar percentage={course.progress_percentage} />
          <p className="text-[11px] text-slate-400 flex items-center gap-1">
            <FontAwesomeIcon icon={faCircleCheck} className="text-ins-500" />
            {course.completed_subtopics} de {course.total_subtopics} subtemas
          </p>
          <Link
            to={`/courses/${course.id}`}
            className="mt-1 inline-flex items-center justify-center gap-1.5 bg-ins-600 group-hover:bg-ins-700 text-white text-xs font-medium rounded-lg px-3 py-2 transition-all shadow-sm"
          >
            <FontAwesomeIcon icon={faBookOpen} />
            Continuar estudiando
            <FontAwesomeIcon
              icon={faArrowRight}
              className="transition-transform duration-200 group-hover:translate-x-1"
            />
          </Link>
        </div>
      </div>
    </article>
  )
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadCourses = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setCourses(await listCourses())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCourses()
  }, [loadCourses])

  return (
    <div className="animate-fade-in-up">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Bienvenido, <span className="text-oft-600">{user?.name}</span>
          </h1>
          <p className="text-slate-500 mt-1 text-sm">Estos son tus cursos de Oftalmología.</p>
        </div>
      </header>

      <div className="mt-6 grid lg:grid-cols-3 gap-6 items-start">
        {/* Cursos: ocupan 2/3 del ancho */}
        <section className="lg:col-span-2">
          <h2 className="text-base font-semibold text-slate-900 mb-3">Mis cursos</h2>

          {loading && <p className="text-slate-500 text-sm">Cargando cursos…</p>}
          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="grid sm:grid-cols-2 gap-4">
            {courses.map((course, i) => (
              <CourseCard key={course.id} course={course} index={i} />
            ))}
          </div>
        </section>

        {/* Barra lateral: unirse a un curso */}
        <aside className="lg:sticky lg:top-24">
          <JoinCourseForm onJoined={loadCourses} />
        </aside>
      </div>
    </div>
  )
}
