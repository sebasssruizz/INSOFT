import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
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
      const [courseData, studentsData] = await Promise.all([getCourse(courseId), getCourseStudents(courseId)])
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

  if (loading) return <p className="text-slate-500">Cargando curso…</p>
  if (error) return <p className="text-red-600">{error}</p>

  return (
    <div>
      <Link to="/dashboard" className="text-sm text-oft-600 hover:text-oft-800 font-medium">
        ← Volver a mis cursos
      </Link>

      <h1 className="text-2xl font-bold text-slate-900 mt-3">{course?.name}</h1>
      {course?.description && <p className="text-slate-500 mt-1">{course.description}</p>}

      <div className="mt-6 bg-oft-50 border border-oft-200 rounded-xl p-5 flex flex-wrap items-center gap-4">
        <div>
          <p className="text-xs text-oft-700 uppercase tracking-wide">Código de acceso</p>
          <code className="font-mono text-xl font-bold text-oft-800">{course?.code}</code>
        </div>
        <button
          onClick={copyCode}
          className="bg-ins-600 hover:bg-ins-700 text-white text-sm font-medium rounded-lg px-4 py-2 transition-all shadow-md shadow-oft-200"
        >
          {copied ? '¡Copiado!' : 'Copiar código'}
        </button>
        <p className="text-sm text-oft-700">Comparte este código con tus estudiantes para que se unan.</p>
      </div>

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">
          Estudiantes inscritos ({students.length})
        </h2>
        <Link to={`/courses/${courseId}`} className="text-sm text-oft-600 hover:text-oft-800 font-medium">
          Ver contenido del curso →
        </Link>
      </div>

      {students.length === 0 ? (
        <p className="text-slate-500 mt-4">
          Aún no hay estudiantes inscritos. Comparte el código del curso para que puedan unirse.
        </p>
      ) : (
        <div className="mt-4 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Estudiante</th>
                <th className="px-4 py-3 font-medium">Correo</th>
                <th className="px-4 py-3 font-medium">Se unió el</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.map((student) => (
                <tr key={student.id}>
                  <td className="px-4 py-3 flex items-center gap-2">
                    {student.profile_image ? (
                      <img src={student.profile_image} alt="" className="w-7 h-7 rounded-full" referrerPolicy="no-referrer" />
                    ) : (
                      <span className="w-7 h-7 rounded-full bg-oft-600 text-white flex items-center justify-center text-xs font-semibold">
                        {student.name?.[0]?.toUpperCase()}
                      </span>
                    )}
                    <span className="font-medium text-slate-800">{student.name}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{student.email}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(student.joined_at).toLocaleDateString('es-ES')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
