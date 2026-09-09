import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck, faCopy, faPlus, faUsers } from '@fortawesome/free-solid-svg-icons'

import { Badge } from '../components/ui/Meta'
import { Button } from '../components/ui/Button'
import { CURRICULUM_FACTS } from '../lib/curriculum'
import { createCourse } from '../services/courseService'
import { useAuth } from '../hooks/useAuth'
import { useCourses } from '../hooks/useCourses'

function CreateCourseForm({ onCreated }) {
  const [form, setForm] = useState({ name: '', description: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
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

  const inputClass =
    'w-full rounded-xl border border-ink-300 bg-ink-50 px-3.5 py-2.5 text-sm text-ink-900 ' +
    'placeholder:text-ink-400 transition-colors duration-150 focus:border-blue-500 focus:bg-white'

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-ink-200 bg-white p-6 shadow-e1"
    >
      <span
        className="flex h-10 w-10 items-center justify-center rounded-2xl bg-soft-lavender text-deep-lavender"
        aria-hidden="true"
      >
        <FontAwesomeIcon icon={faPlus} />
      </span>

      <h3 className="mt-4 text-lg font-semibold tracking-[-0.01em] text-ink-900">Crear un curso</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-ink-500">
        Se genera un código único para tus estudiantes. El contenido es el oficial de INSOFT.
      </p>

      <div className="mt-5 space-y-3">
        <div>
          <label htmlFor="course-name" className="mb-1.5 block text-xs font-semibold text-ink-600">
            Nombre del curso
          </label>
          <input
            id="course-name"
            type="text"
            required
            minLength={3}
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Oftalmología · Grupo A"
            className={inputClass}
          />
        </div>

        <div>
          <label htmlFor="course-desc" className="mb-1.5 block text-xs font-semibold text-ink-600">
            Descripción <span className="font-normal text-ink-400">(opcional)</span>
          </label>
          <textarea
            id="course-desc"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            placeholder="Semestre y grupo, por ejemplo"
            rows={2}
            className={`${inputClass} resize-none`}
          />
        </div>

        <Button
          type="submit"
          loading={loading}
          disabled={form.name.trim().length < 3}
          className="w-full"
        >
          Crear curso
        </Button>

        {error && (
          <p role="alert" className="text-sm text-wrong-700">
            {error}
          </p>
        )}
      </div>
    </form>
  )
}

function TeacherCourseCard({ course, index }) {
  const [copied, setCopied] = useState(false)
  const navigate = useNavigate()

  const copyCode = async (event) => {
    event.stopPropagation()
    try {
      await navigator.clipboard.writeText(course.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* portapapeles no disponible */
    }
  }

  const openCourse = () => navigate(`/teacher/courses/${course.id}`)

  return (
    <article
      role="link"
      tabIndex="0"
      onClick={openCourse}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          openCourse()
        }
      }}
      aria-label={`Abrir el curso ${course.name}`}
      className="group animate-rise-in cursor-pointer rounded-2xl border border-ink-200 bg-white p-6 shadow-e1 transition-[transform,box-shadow,border-color] duration-200 ease-out hover:-translate-y-1 hover:border-blue-300 hover:shadow-e3"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <span
          className="flex h-12 w-12 items-center justify-center rounded-2xl bg-soft-mint text-deep-mint transition-transform duration-200 ease-out group-hover:scale-105"
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={faUsers} />
        </span>
        <Badge tone="quiet">{course.student_count} inscritos</Badge>
      </div>

      <h3 className="mt-5 text-[1.25rem] font-semibold leading-snug tracking-[-0.01em] text-ink-900">
        {course.name}
      </h3>

      <div className="mt-4 flex items-center gap-2">
        <code className="tabular rounded-lg bg-ink-100 px-2.5 py-1.5 font-sans text-sm font-bold tracking-[0.14em] text-blue-800 transition-colors duration-150 group-hover:bg-blue-100">
          {course.code}
        </code>
        <button
          type="button"
          onClick={copyCode}
          onKeyDown={(event) => event.stopPropagation()}
          className={`inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-semibold transition-colors duration-150 ${
            copied ? 'text-correct-700' : 'text-ink-500 hover:bg-ink-100 hover:text-blue-800'
          }`}
        >
          <FontAwesomeIcon icon={copied ? faCheck : faCopy} aria-hidden="true" />
          {copied ? 'Copiado' : 'Copiar'}
        </button>
      </div>

      <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-blue-800">
        Ver el curso
        <FontAwesomeIcon
          icon={faArrowRight}
          className="transition-transform duration-200 ease-out group-hover:translate-x-1"
          aria-hidden="true"
        />
      </span>
    </article>
  )
}

export default function TeacherDashboard() {
  const { user } = useAuth()
  const { courses, loading, error, refresh } = useCourses()

  const totalStudents = courses.reduce((sum, course) => sum + (course.student_count || 0), 0)

  return (
    <div>
      <header className="relative overflow-hidden border-b border-ink-200 bg-gradient-to-br from-soft-mint via-ink-50 to-soft-butter">
        <div className="relative mx-auto max-w-[78rem] px-6 py-12 lg:px-10 lg:py-16">
          <p className="eyebrow text-deep-mint">Panel del profesor</p>
          <h1 className="mt-3.5 text-[2rem] font-semibold leading-[1.12] tracking-[-0.02em] text-ink-900 lg:text-[2.75rem]">
            Hola, {user?.name?.split(' ').slice(0, 2).join(' ')}
          </h1>
          <p className="mt-4 max-w-[52ch] text-[0.9375rem] leading-relaxed text-ink-600">
            Crea cursos, comparte el código y sigue a tu grupo. El temario es el mismo contenido
            oficial en todos los cursos, así que no tienes que mantenerlo.
          </p>

          <div className="mt-9 flex flex-wrap items-end gap-x-12 gap-y-6">
            <div>
              <p className="tabular font-display text-[2.75rem] font-semibold leading-none text-blue-900">
                {courses.length}
              </p>
              <p className="eyebrow mt-2 text-ink-500">
                {courses.length === 1 ? 'Curso' : 'Cursos'}
              </p>
            </div>
            <div>
              <p className="tabular font-display text-[2.75rem] font-semibold leading-none text-deep-mint">
                {totalStudents}
              </p>
              <p className="eyebrow mt-2 text-ink-500">Estudiantes</p>
            </div>
            <div>
              <p className="tabular font-display text-[2.75rem] font-semibold leading-none text-deep-lavender">
                {CURRICULUM_FACTS.subtopics}
              </p>
              <p className="eyebrow mt-2 text-ink-500">Subtemas oficiales</p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[78rem] px-6 py-12 lg:px-10 lg:py-16">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <section>
            <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink-900">Mis cursos</h2>

            {error && (
              <p className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
                {error}
              </p>
            )}

            {loading && (
              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                {[0, 1].map((i) => (
                  <div key={i} className="rounded-2xl border border-ink-200 bg-white p-6">
                    <div className="skeleton h-12 w-12 rounded-xl" />
                    <div className="skeleton mt-5 h-6 w-3/4 rounded" />
                    <div className="skeleton mt-4 h-8 w-32 rounded-lg" />
                  </div>
                ))}
              </div>
            )}

            {!loading && courses.length === 0 && !error && (
              <div className="mt-5 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
                <h3 className="text-lg font-semibold text-ink-900">Todavía no has creado cursos</h3>
                <p className="mx-auto mt-2 max-w-[44ch] text-sm leading-relaxed text-ink-500">
                  Crea uno con el formulario de la derecha. Recibirás un código tipo OFT-A72K para
                  que tus estudiantes se unan.
                </p>
              </div>
            )}

            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              {!loading &&
                courses.map((course, index) => (
                  <TeacherCourseCard key={course.id} course={course} index={index} />
                ))}
            </div>
          </section>

          <aside className="lg:sticky lg:top-8 lg:self-start">
            <CreateCourseForm onCreated={refresh} />
          </aside>
        </div>
      </main>
    </div>
  )
}
