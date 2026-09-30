import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faDownload } from '@fortawesome/free-solid-svg-icons'
import { useAuth } from '../hooks/useAuth'
import { apiFetch, downloadCsv } from '../services/api'

function Bar({ value, max }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <span className="inline-flex min-w-[6rem] items-center gap-2">
      <span className="h-2 w-full max-w-[8rem] overflow-hidden rounded-full bg-ink-100">
        <span
          className="block h-full rounded-full bg-blue-800 transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className="tabular text-xs text-ink-500">{value}</span>
    </span>
  )
}

function AciertoBar({ pct }) {
  return (
    <span className="inline-flex min-w-[8rem] items-center gap-2">
      <span className="h-2 w-full max-w-[8rem] overflow-hidden rounded-full bg-ink-100">
        <span
          className={cn(
            'block h-full rounded-full transition-[width] duration-300',
            pct >= 70 ? 'bg-correct-500' : pct >= 40 ? 'bg-blue-600' : 'bg-wrong-500',
          )}
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className="tabular text-xs text-ink-500">{pct}%</span>
    </span>
  )
}

function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}

function Th({ children }) {
  return (
    <th className="border border-ink-200 p-2 text-left text-sm font-medium text-ink-600">
      {children}
    </th>
  )
}

function Td({ children }) {
  return <td className="border border-ink-200 p-2 text-sm text-ink-600">{children}</td>
}

function EstadoVacio({ mensaje }) {
  return <p className="rounded-xl border border-dashed border-ink-300 bg-white px-5 py-8 text-center text-sm text-ink-500">{mensaje}</p>
}

function ErrorBox({ mensaje, onRetry }) {
  return (
    <div className="rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3">
      <p className="text-sm text-wrong-700">{mensaje}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 text-sm font-semibold text-blue-800 underline"
        >
          Reintentar
        </button>
      )}
    </div>
  )
}

/* ── Pestaña: Uso de IA ───────────────────────────────────────────────────── */

function AiTab() {
  const [historial, setHistorial] = useState([])
  const [subtopics, setSubtopics] = useState([])
  const [students, setStudents] = useState([])
  const [overview, setOverview] = useState(null)
  const [filtroSubtopic, setFiltroSubtopic] = useState('')
  const [filtroSession, setFiltroSession] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [recarga, setRecarga] = useState(0)

  useEffect(() => {
    if (!recarga) return
    let cancelled = false
    const load = async () => {
      setCargando(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (filtroSubtopic) params.set('subtopic_id', filtroSubtopic)
        if (filtroSession) params.set('session_id', filtroSession)
        params.set('limit', '100')
        const data = await apiFetch(`/ai/history/all?${params.toString()}`)
        if (cancelled) return
        setHistorial(data)

        const stats = await apiFetch('/ai/stats/subtopics')
        if (cancelled) return
        setSubtopics(stats.subtopics || [])
        const names = {}
        ;(stats.subtopics || []).forEach((st) => {
          names[st.subtopic_id] = st.nombre
        })

        const [studentsData, overviewData] = await Promise.all([
          apiFetch('/ai/stats/students'),
          apiFetch('/ai/stats/overview'),
        ])
        if (cancelled) return
        setStudents(studentsData.students || [])
        setOverview(overviewData)
        setHistorial(
          data.map((item) => ({
            ...item,
            subtitulo: item.subtopic_id ? names[item.subtopic_id] || `Subtema ${item.subtopic_id}` : '—',
          })),
        )
      } catch (err) {
        if (!cancelled) setError('No se pudo cargar el uso de IA. Inténtalo de nuevo.')
      } finally {
        if (!cancelled) setCargando(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [recarga, filtroSubtopic, filtroSession])

  const sesiones = Array.from(
    new Set(historial.map((h) => h.session_id).filter(Boolean)),
  )

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-4">
        <label className="block text-sm text-ink-500">
          Subtema:
          <select
            value={filtroSubtopic}
            onChange={(e) => setFiltroSubtopic(e.target.value)}
            className="ml-2 w-56 rounded border"
          >
            <option value="">Todos</option>
            {subtopics.map((st) => (
              <option key={st.subtopic_id} value={st.subtopic_id}>
                {st.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm text-ink-500">
          Sesión:
          <select
            value={filtroSession}
            onChange={(e) => setFiltroSession(e.target.value)}
            className="ml-2 w-56 rounded border"
          >
            <option value="">Todas</option>
            {sesiones.map((sid) => (
              <option key={sid} value={sid}>
                {sid.slice(0, 8)}…
              </option>
            ))}
          </select>
        </label>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault()
            downloadCsv('/ai/stats/export.csv', 'estadisticas_ia.csv')
          }}
          className="self-end text-sm font-semibold text-blue-800 underline"
        >
          <FontAwesomeIcon icon={faDownload} className="mr-1" aria-hidden="true" />
          Exportar CSV
        </a>
      </div>

      {cargando && <p className="text-ink-500">Cargando…</p>}
      {error && <ErrorBox mensaje={error} onRetry={() => setRecarga((n) => n + 1)} />}

      {!cargando && !error && (
        <div className="space-y-8">
          {overview && (
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Preguntas totales</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.total_preguntas}
                </p>
              </div>
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Últimos 7 días</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.preguntas_ultimos_7_dias}
                </p>
              </div>
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Tiempo medio de respuesta</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.tiempo_respuesta_promedio_ms} ms
                </p>
              </div>
            </div>
          )}

          {subtopics.length > 0 && (
            <div>
              <h3 className="font-semibold text-ink-900">Preguntas por subtema</h3>
              <ul className="mt-3 space-y-2">
                {subtopics.map((st) => (
                  <li key={st.subtopic_id} className="flex items-center justify-between gap-4">
                    <span className="text-sm text-ink-700">{st.nombre}</span>
                    <Bar value={st.total_preguntas} max={subtopics[0].total_preguntas} />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {students.length > 0 && (
            <div className="overflow-x-auto">
              <h3 className="font-semibold text-ink-900">Por estudiante</h3>
              <table className="mt-3 w-full rounded border border-ink-200">
                <thead>
                  <tr>
                    <Th>Estudiante</Th>
                    <Th>Preguntas</Th>
                    <Th>Último uso</Th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.user_id} className="border-b border-ink-100">
                      <Td>{s.nombre}</Td>
                      <Td>{s.total_preguntas}</Td>
                      <Td>{s.ultima_consulta ? new Date(s.ultima_consulta).toLocaleString() : '—'}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {historial.length === 0 ? (
            <EstadoVacio mensaje="No hay consultas de IA registradas." />
          ) : (
            <div className="overflow-x-auto">
              <h3 className="font-semibold text-ink-900">Historial</h3>
              <table className="mt-3 w-full rounded border border-ink-200">
                <thead>
                  <tr>
                    <Th>Pregunta</Th>
                    <Th>Subtema</Th>
                    <Th>Respuesta</Th>
                    <Th>Fecha</Th>
                  </tr>
                </thead>
                <tbody>
                  {historial.map((item) => (
                    <tr key={item.id} className="border-b border-ink-100">
                      <Td>{item.question.length > 80 ? item.question.slice(0, 80) + '…' : item.question}</Td>
                      <Td>{item.subtitulo}</Td>
                      <Td>
                        {item.answer
                          ? item.answer.length > 120
                            ? item.answer.slice(0, 120) + '…'
                            : item.answer
                          : 'Sin respuesta'}
                      </Td>
                      <Td>{new Date(item.created_at).toLocaleString()}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Pestaña: Quizzes ─────────────────────────────────────────────────────── */

function QuizTab() {
  const [overview, setOverview] = useState(null)
  const [questions, setQuestions] = useState([])
  const [students, setStudents] = useState([])
  const [subtopics, setSubtopics] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [recarga, setRecarga] = useState(0)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setCargando(true)
      setError(null)
      try {
        const [o, q, s, st] = await Promise.all([
          apiFetch('/quiz/stats/overview'),
          apiFetch('/quiz/stats/questions'),
          apiFetch('/quiz/stats/students'),
          apiFetch('/quiz/stats/subtopics'),
        ])
        if (cancelled) return
        setOverview(o)
        setQuestions(q.questions || [])
        setStudents(s.students || [])
        setSubtopics(st)
      } catch {
        if (!cancelled) setError('No se pudo cargar el resumen de quizzes. Inténtalo de nuevo.')
      } finally {
        if (!cancelled) setCargando(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [recarga])

  return (
    <div>
      {cargando && <p className="text-ink-500">Cargando…</p>}
      {error && <ErrorBox mensaje={error} onRetry={() => setRecarga((n) => n + 1)} />}

      {!cargando && !error && (
        <div className="space-y-8">
          {overview && (
            <div className="grid gap-4 sm:grid-cols-4">
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Intentos</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.total_intentos}
                </p>
              </div>
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Respuestas</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.total_respuestas}
                </p>
              </div>
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">% acierto global</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.porcentaje_acierto}%
                </p>
              </div>
              <div className="rounded-2xl border border-ink-200 bg-white p-4">
                <p className="eyebrow text-ink-500">Estudiantes activos</p>
                <p className="tabular mt-1 text-2xl font-semibold text-ink-900">
                  {overview.estudiantes_activos}
                </p>
              </div>
            </div>
          )}

          <div className="overflow-x-auto">
            <h3 className="font-semibold text-ink-900">Por pregunta</h3>
            {questions.length === 0 ? (
              <EstadoVacio mensaje="Todavía no hay respuestas de estudiantes." />
            ) : (
              <table className="mt-3 w-full rounded border border-ink-200">
                <thead>
                  <tr>
                    <Th>Pregunta</Th>
                    <Th>Respuestas</Th>
                    <Th>% acierto</Th>
                    <Th>Error más común</Th>
                  </tr>
                </thead>
                <tbody>
                  {questions.map((q) => (
                    <tr key={q.question_id} className="border-b border-ink-100">
                      <Td>{q.prompt.length > 60 ? q.prompt.slice(0, 60) + '…' : q.prompt}</Td>
                      <Td>{q.respuestas}</Td>
                      <Td>
                        <AciertoBar pct={q.porcentaje_acierto} />
                      </Td>
                      <Td>
                        {q.opcion_incorrecta_mas_elegida === null
                          ? '—'
                          : String.fromCharCode(65 + q.opcion_incorrecta_mas_elegida)}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="overflow-x-auto">
            <h3 className="font-semibold text-ink-900">Por estudiante</h3>
            {students.length === 0 ? (
              <EstadoVacio mensaje="Sin actividad de estudiantes." />
            ) : (
              <table className="mt-3 w-full rounded border border-ink-200">
                <thead>
                  <tr>
                    <Th>Estudiante</Th>
                    <Th>Respuestas</Th>
                    <Th>% acierto</Th>
                    <Th>Última actividad</Th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.user_id} className="border-b border-ink-100">
                      <Td>{s.nombre}</Td>
                      <Td>{s.respuestas}</Td>
                      <Td>
                        <AciertoBar pct={s.porcentaje_acierto} />
                      </Td>
                      <Td>
                        {s.ultima_actividad ? new Date(s.ultima_actividad).toLocaleString() : '—'}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="overflow-x-auto">
            <h3 className="font-semibold text-ink-900">Acierto por subtema</h3>
            {subtopics.length === 0 ? (
              <EstadoVacio mensaje="Sin datos por subtema todavía." />
            ) : (
              <ul className="mt-3 space-y-2">
                {subtopics.map((st) => (
                  <li key={st.subtopic_id} className="flex items-center justify-between gap-4">
                    <span className="text-sm text-ink-700">{st.nombre}</span>
                    <AciertoBar pct={st.porcentaje_acierto} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              downloadCsv('/quiz/stats/export.csv', 'estadisticas_quiz.csv')
            }}
            className="inline-block text-sm font-semibold text-blue-800 underline"
          >
            <FontAwesomeIcon icon={faDownload} className="mr-1" aria-hidden="true" />
            Exportar CSV
          </a>
        </div>
      )}
    </div>
  )
}

/* ── Página ──────────────────────────────────────────────────────────────── */

const TABS = [
  { id: 'ia', label: 'Uso de IA' },
  { id: 'quiz', label: 'Quizzes' },
]

function TeacherAiStats() {
  const { user } = useAuth()
  const [tab, setTab] = useState('ia')
  const esProfesor = user && user.role === 'TEACHER'

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
    <div className="p-6 lg:p-10">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-sm text-ink-500 transition-colors hover:text-blue-800"
          >
            <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
            Volver al panel
          </Link>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Estadísticas</h2>
          <p className="text-sm text-ink-600">
            Uso del asistente de IA y resultados de los quizzes de tus estudiantes.
          </p>
        </div>
      </header>

      <div className="mb-6 flex gap-2 border-b border-ink-200" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              '-mb-px rounded-t-lg border-b-2 px-4 py-2 text-sm font-semibold transition-colors',
              tab === t.id
                ? 'border-blue-800 text-blue-800'
                : 'border-transparent text-ink-500 hover:text-ink-700',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'ia' ? <AiTab /> : <QuizTab />}
    </div>
  )
}

export default TeacherAiStats
