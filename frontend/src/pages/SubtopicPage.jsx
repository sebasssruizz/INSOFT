import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck } from '@fortawesome/free-solid-svg-icons'
import { useAuth } from '../hooks/useAuth'
import { getSubtopic } from '../services/contentService'
import { setProgress } from '../services/progressService'

/** Render sencillo del contenido oficial: párrafos, listas con "- " y **negritas**. */
function ContentRenderer({ content }) {
  const renderInline = (text, keyPrefix) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) =>
      part.startsWith('**') && part.endsWith('**') ? (
        <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
      ) : (
        <span key={`${keyPrefix}-${i}`}>{part}</span>
      ),
    )
  }

  return (
    <div className="prose-content text-slate-700">
      {content.split('\n').map((line, idx) => {
        const trimmed = line.trim()
        if (!trimmed) return null
        if (/^[-•]\s+/.test(trimmed)) {
          return (
            <div key={idx} className="flex gap-2 mb-1.5 ml-2">
              <span className="text-oft-500">•</span>
              <span>{renderInline(trimmed.replace(/^[-•]\s+/, ''), idx)}</span>
            </div>
          )
        }
        if (/^\d+\.\s+/.test(trimmed)) {
          return (
            <div key={idx} className="flex gap-2 mb-1.5 ml-2">
              <span className="text-oft-600 font-semibold">{trimmed.match(/^\d+\./)[0]}</span>
              <span>{renderInline(trimmed.replace(/^\d+\.\s+/, ''), idx)}</span>
            </div>
          )
        }
        return <p key={idx}>{renderInline(trimmed, idx)}</p>
      })}
    </div>
  )
}

export default function SubtopicPage() {
  const { courseId, subtopicId } = useParams()
  const { user } = useAuth()
  const isStudent = user?.role === 'STUDENT'

  const [subtopic, setSubtopic] = useState(null)
  const [completed, setCompleted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSubtopic(subtopicId, courseId)
      setSubtopic(data)
      setCompleted(data.completed)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [courseId, subtopicId])

  useEffect(() => {
    load()
  }, [load])

  const toggleCompleted = async () => {
    setSaving(true)
    setError(null)
    try {
      const record = await setProgress(Number(courseId), Number(subtopicId), !completed)
      setCompleted(record.completed)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-slate-500">Cargando contenido…</p>
  if (error && !subtopic) return <p className="text-red-600">{error}</p>

  return (
    <div className="max-w-3xl">
      <Link to={`/courses/${courseId}`} className="text-sm text-oft-600 hover:text-oft-800 font-medium">
        ← Volver al curso
      </Link>

      <h1 className="text-2xl font-bold text-slate-900 mt-3">{subtopic?.name}</h1>

      <div className="mt-6 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <ContentRenderer content={subtopic?.content || ''} />
      </div>

      {isStudent && (
        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={toggleCompleted}
            disabled={saving}
            className={`inline-flex items-center gap-2 text-sm font-medium rounded-lg px-5 py-2.5 transition-all disabled:opacity-50 ${
              completed
                ? 'bg-ins-100 text-ins-700 hover:bg-ins-200'
                : 'bg-ins-600 hover:bg-ins-700 text-white shadow-md shadow-oft-200'
            }`}
          >
            {saving ? (
              'Guardando…'
            ) : completed ? (
              <>
                <FontAwesomeIcon icon={faCheck} /> Completado (pulsa para desmarcar)
              </>
            ) : (
              'Marcar como completado'
            )}
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}
    </div>
  )
}
