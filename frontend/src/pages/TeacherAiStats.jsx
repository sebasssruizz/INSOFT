import { useEffect, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFilter } from '@fortawesome/free-solid-svg-icons'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { apiFetch } from '../services/api'

function TeacherAiStats() {
  const { user } = useAuth()
  const [historial, setHistorial] = useState([])
  const [filtrarSubtopic, setFiltrarSubtopic] = useState('')
  const [filtrarSession, setFiltrarSession] = useState('')
  const [conteoSubtopos, setConteoSubtopos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [sesiones, setSesiones] = useState([])

  const esProfesor = user && user.role === 'TEACHER'

  useEffect(() => {
    if (!esProfesor) {
      setHistorial([])
      return
    }

    const fetchHistorial = async () => {
      setCargando(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (filtrarSubtopic !== '') params.set('subtopic_id', String(Number(filtrarSubtopic)))
        if (filtrarSession) params.set('session_id', filtrarSession)
        params.set('limit', '100')
        params.set('offset', '0')
        const datos = await apiFetch(`/ai/history/all?${params.toString()}`)

        const nombres = {}
        try {
          const stats = await apiFetch('/ai/stats/subtopics')
          setConteoSubtopos(stats.subtopics || [])
          ;(stats.subtopics || []).forEach((st) => {
            nombres[st.subtopic_id] = st.nombre
          })
        } catch {
          setConteoSubtopos([])
        }
        const nombreDe = (sid) => nombres[sid] || `Subtema ${sid}`

        setHistorial(
          datos.map((item) => ({
            id: item.id,
            question:
              item.question.length > 80 ? item.question.substring(0, 80) + '...' : item.question,
            answer: item.answer
              ? item.answer.length > 120
                ? item.answer.substring(0, 120) + '...'
                : item.answer
              : 'Sin respuesta',
            subtitulo: item.subtopic_id ? nombreDe(item.subtopic_id) : '—',
            session_id: item.session_id || '',
            hour: new Date(item.created_at).toLocaleString(),
          })),
        )
        const ids = new Set(datos.map((d) => d.session_id).filter(Boolean))
        setSesiones(Array.from(ids))
      } catch (err) {
        console.error('Error al cargar historial de IA:', err)
        setHistorial([])
        setError('No se pudo cargar el historial de IA. Inténtalo de nuevo más tarde.')
      } finally {
        setCargando(false)
      }
    }

    fetchHistorial()
  }, [esProfesor, filtrarSubtopic, filtrarSession])

  if (!esProfesor) {
    return (
      <div className="p-6">
        <p className="text-sm text-wrong-700">Solo los profesores pueden ver esta página.</p>
        <Link to="/dashboard" className="mt-3 inline-block text-sm text-blue-800 underline">
          Volver al inicio
        </Link>
      </div>
    )
  }

  return (
    <div className="p-6">
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-ink-900">Estadísticas de IA</h2>
        <p className="text-sm text-ink-600">
          Consulta el historial de consultas a la IA y el conteo por subtema.
        </p>
      </header>

      <div className="mb-4 flex flex-wrap gap-4">
        <label className="mb-2 block text-sm text-ink-500">
          Filtrar por subtema:
          <select
            value={filtrarSubtopic}
            onChange={(e) => setFiltrarSubtopic(e.target.value)}
            className="w-56 rounded border"
          >
            <option value="">Todos</option>
            {conteoSubtopos.map((st) => (
              <option key={st.subtopic_id} value={st.subtopic_id}>
                {st.nombre}
              </option>
            ))}
          </select>
        </label>

        <label className="mb-2 block text-sm text-ink-500">
          Filtrar por sesión:
          <select
            value={filtrarSession}
            onChange={(e) => setFiltrarSession(e.target.value)}
            className="w-56 rounded border"
          >
            <option value="">Todas</option>
            {sesiones.map((sid) => (
              <option key={sid} value={sid}>
                {sid.slice(0, 8)}…
              </option>
            ))}
          </select>
        </label>
      </div>

      {conteoSubtopos.length > 0 && (
        <div className="mb-6">
          <p className="font-medium text-ink-600">Conteo por subtema:</p>
          <ul className="mt-2 space-y-1 text-sm text-ink-600">
            {conteoSubtopos.map((st) => (
              <li key={st.subtopic_id}>
                <span className="font-medium">{st.nombre}</span>: {st.total_preguntas}{' '}
                {st.total_preguntas === 1 ? 'pregunta' : 'preguntas'}
              </li>
            ))}
          </ul>
        </div>
      )}

      {cargando ? (
        <p className="text-ink-500">Cargando...</p>
      ) : error ? (
        <p className="rounded border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
          {error}
        </p>
      ) : historial.length === 0 ? (
        <p className="text-sm text-ink-500">No hay consultas de IA registradas.</p>
      ) : (
        <table className="mb-4 w-full rounded border border-ink-200">
          <thead>
            <tr>
              <th className="border border-ink-200 p-2 text-left text-sm text-ink-600">Pregunta</th>
              <th className="border border-ink-200 p-2 text-left text-sm text-ink-600">Subtema</th>
              <th className="border border-ink-200 p-2 text-left text-sm text-ink-600">Respuesta</th>
              <th className="border border-ink-200 p-2 text-left text-sm text-ink-600">Hora</th>
            </tr>
          </thead>
          <tbody>
            {historial.map((item) => (
              <tr key={item.id} className="border-b border-ink-100">
                <td className="border border-ink-200 p-2 text-sm text-ink-600">{item.question}</td>
                <td className="border border-ink-200 p-2 text-sm text-ink-600">{item.subtitulo}</td>
                <td className="border border-ink-200 p-2 text-sm text-ink-600">{item.answer}</td>
                <td className="border border-ink-200 p-2 text-sm text-ink-600">{item.hour}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="mt-6 flex items-center gap-2 text-sm text-ink-500">
        <FontAwesomeIcon icon={faFilter} aria-hidden="true" />
        {filtrarSession || filtrarSubtopic
          ? 'Filtros activos. Pulsa "Todos" en ambos para ver el historial completo.'
          : 'Sin filtros activos.'}
      </div>
    </div>
  )
}

export default TeacherAiStats
