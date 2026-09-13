import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faArrowRight, faCheck, faCopy } from '@fortawesome/free-solid-svg-icons'

import { Button } from '../components/ui/Button'

import { getCourse, getCourseStudents } from '../services/courseService'

export default function TeacherCoursePage() {
  const { courseId } = useParams()
  const [course, setCourse] = useState(null)
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [courseData, studentsData] = await Promise.all([
        getCourse(courseId),
        getCourseStudents(courseId),
      ])
      setCourse(courseData)
      setStudents(studentsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    load()
  }, [load])

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
    <div className="mx-auto max-w-[72rem] px-6 py-10 lg:px-10">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
      >
        <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
        Mis cursos
      </Link>

      {loading && (
        <div className="mt-6 space-y-4">
          <div className="skeleton h-10 w-1/2 rounded" />
          <div className="skeleton h-28 w-full rounded-2xl" />
          <div className="skeleton h-56 w-full rounded-2xl" />
        </div>
      )}

      {error && !loading && (
        <div className="mt-6 rounded-2xl border border-wrong-200 bg-wrong-50 px-6 py-8 text-center">
          <p className="text-sm text-wrong-700">{error}</p>
          <Button onClick={load} variant="secondary" size="sm" className="mt-4">
            Reintentar
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          <header className="mt-4">
            <h1 className="text-[2rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
              {course?.name}
            </h1>
            {course?.description && (
              <p className="mt-2.5 max-w-[62ch] text-[0.9375rem] leading-relaxed text-ink-500">
                {course.description}
              </p>
            )}
          </header>

          {/* Código de acceso: el dato que el profesor viene a buscar */}
          <div className="mt-7 flex flex-wrap items-center gap-x-8 gap-y-5 rounded-2xl bg-soft-lavender px-7 py-7">
            <div>
              <p className="eyebrow text-deep-lavender">Código de acceso</p>
              <p className="tabular mt-2 font-display text-[2.25rem] font-semibold leading-none tracking-[0.08em] text-ink-900">
                {course?.code}
              </p>
            </div>
            <Button onClick={copyCode} icon={copied ? faCheck : faCopy}>
              {copied ? 'Copiado' : 'Copiar código'}
            </Button>
            <p className="max-w-[32ch] text-[0.8125rem] leading-relaxed text-ink-600">
              Compártelo con tu grupo: con él se unen a este curso desde su panel.
            </p>
          </div>

          <div className="mt-10 flex flex-wrap items-baseline justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink-900">
              Estudiantes inscritos
              <span className="tabular ml-2 font-sans text-base font-medium text-ink-400">
                {students.length}
              </span>
            </h2>
            <Link
              to={`/courses/${courseId}`}
              className="inline-flex items-center gap-2 text-sm font-semibold text-blue-800 transition-colors duration-150 hover:text-blue-800"
            >
              Ver el contenido del curso
              <FontAwesomeIcon icon={faArrowRight} className="text-[0.7rem]" aria-hidden="true" />
            </Link>
          </div>

          {students.length === 0 ? (
            <div className="mt-5 rounded-2xl border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
              <h3 className="text-lg font-semibold text-ink-900">Nadie se ha unido todavía</h3>
              <p className="mx-auto mt-2 max-w-[44ch] text-sm leading-relaxed text-ink-500">
                Comparte el código{' '}
                <span className="font-semibold text-blue-800">{course?.code}</span> con tu grupo.
                Aparecerán aquí en cuanto entren.
              </p>
            </div>
          ) : (
            <div className="mt-5 overflow-hidden rounded-2xl border border-ink-200 bg-white">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-ink-200 bg-ink-50 text-left">
                      <th className="px-5 py-3 text-xs font-bold uppercase tracking-[0.08em] text-ink-500">
                        Estudiante
                      </th>
                      <th className="px-5 py-3 text-xs font-bold uppercase tracking-[0.08em] text-ink-500">
                        Correo
                      </th>
                      <th className="px-5 py-3 text-xs font-bold uppercase tracking-[0.08em] text-ink-500">
                        Se unió
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-200">
                    {students.map((student) => (
                      <tr
                        key={student.id}
                        className="transition-colors duration-150 hover:bg-ink-50"
                      >
                        <td className="px-5 py-3.5">
                          <span className="flex items-center gap-3">
                            {student.profile_image ? (
                              <img
                                src={student.profile_image}
                                alt=""
                                className="h-8 w-8 rounded-full"
                                referrerPolicy="no-referrer"
                              />
                            ) : (
                              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-soft-lavender text-xs font-bold text-deep-lavender">
                                {student.name?.[0]?.toUpperCase()}
                              </span>
                            )}
                            <span className="font-medium text-ink-900">{student.name}</span>
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-ink-600">{student.email}</td>
                        <td className="tabular px-5 py-3.5 text-ink-500">
                          {new Date(student.joined_at).toLocaleDateString('es-CO', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
