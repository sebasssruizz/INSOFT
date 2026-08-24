import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck, faCopy, faPlus, faUsers } from '@fortawesome/free-solid-svg-icons'
import ImageCarousel from '../components/ImageCarousel'
import { SLIDESHOW_IMAGES } from '../data/slideshow'
import { useAuth } from '../hooks/useAuth'
import { createCourse, listCourses } from '../services/courseService'

function CreateCourseForm({ onCreated }) {
  const [form, setForm] = useState({ name: '', description: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await createCourse(form.name, form.description)
      setForm({ name: '', description: '' })
      onCreated?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-dashed border-oft-300 p-5 shadow-sm">
      <h3 className="font-semibold text-slate-900 flex items-center gap-2">
        <FontAwesomeIcon icon={faPlus} className="text-oft-500" />
        Crear curso
      </h3>
      <p className="text-xs text-slate-500 mt-1">
        Se generará automáticamente un código único para compartir con tus estudiantes.
      </p>
      <div className="mt-3 space-y-3">
        <input
          type="text"
          required
          minLength={3}
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Nombre (p. ej. Oftalmología - Grupo A)"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-oft-500"
        />
        <textarea
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Descripción del curso"
          rows={2}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-oft-500"
        />
        <button
          type="submit"
          disabled={loading || form.name.trim().length < 3}
          className="w-full bg-ins-600 hover:bg-ins-700 text-white text-sm font-medium rounded-lg px-4 py-2 transition-all shadow-md shadow-oft-200 disabled:opacity-50"
        >
          {loading ? 'Creando…' : 'Crear curso'}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </form>
  )
}

function TeacherCourseCard({ course, index }) {
  const [copied, setCopied] = useState(false)

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(course.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* portapapeles no disponible */
    }
  }

  return (
    <article
      className="animate-fade-in-up group bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-lg hover:shadow-oft-100 hover:border-oft-300 hover:-translate-y-1 transition-all duration-200 p-4"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <h3 className="font-semibold text-slate-900 text-sm leading-snug">{course.name}</h3>

      <div className="mt-2 flex items-center gap-2 flex-wrap">
        <code className="font-mono text-xs font-bold bg-slate-100 group-hover:bg-oft-50 rounded px-2 py-1 text-oft-700 transition-colors">
          {course.code}
        </code>
        <button
          onClick={copyCode}
          className={`text-xs font-medium inline-flex items-center gap-1 transition-colors ${
            copied ? 'text-ins-600' : 'text-slate-400 hover:text-oft-600'
          }`}
        >
          <FontAwesomeIcon icon={copied ? faCheck : faCopy} />
          {copied ? '¡Copiado!' : 'Copiar'}
        </button>
      </div>

      <p className="text-xs text-slate-500 mt-2 flex items-center gap-1.5">
        <FontAwesomeIcon icon={faUsers} className="text-ins-500" />
        <strong className="text-slate-800">{course.student_count}</strong> estudiantes inscritos
      </p>

      <Link
        to={`/teacher/courses/${course.id}`}
        className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-oft-600 hover:text-oft-800 transition-colors"
      >
        Ver curso
        <FontAwesomeIcon icon={faArrowRight} className="transition-transform duration-200 group-hover:translate-x-1" />
      </Link>
    </article>
  )
}

export default function TeacherDashboard() {
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
      <h1 className="text-2xl font-bold text-slate-900">
        Bienvenido, <span className="text-oft-600">{user?.name}</span>
      </h1>
      <p className="text-slate-500 mt-1 text-sm">
        Gestiona tus cursos y comparte el código con tus estudiantes. El contenido académico es el oficial de
        INSOFT.
      </p>

      <ImageCarousel
        images={SLIDESHOW_IMAGES}
        interval={7000}
        className="mt-5 rounded-xl shadow-md h-36 md:h-44"
      />

      <div className="mt-6 grid lg:grid-cols-3 gap-6 items-start">
        <section className="lg:col-span-2">
          <h2 className="text-base font-semibold text-slate-900 mb-3">Mis cursos</h2>

          {loading && <p className="text-slate-500 text-sm">Cargando cursos…</p>}
          {error && <p className="text-red-600 text-sm">{error}</p>}
          {!loading && courses.length === 0 && (
            <p className="text-slate-500 text-sm mb-4">Todavía no has creado ningún curso.</p>
          )}

          <div className="grid sm:grid-cols-2 gap-4">
            {courses.map((course, i) => (
              <TeacherCourseCard key={course.id} course={course} index={i} />
            ))}
          </div>
        </section>

        <aside className="lg:sticky lg:top-24">
          <CreateCourseForm onCreated={loadCourses} />
        </aside>
      </div>
    </div>
  )
}
