import { useState } from 'react'
import { rateAiAnswer } from '../services/aiService'

export default function AiAnswerFeedback({ queryId, initialFeedback }) {
  const [feedback, setFeedback] = useState(initialFeedback)
  const [editing, setEditing] = useState(false)
  const [reason, setReason] = useState(initialFeedback?.reason || 'context')
  const [comment, setComment] = useState(initialFeedback?.comment || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const save = async (helpful) => {
    setSaving(true)
    setError('')
    try {
      const result = await rateAiAnswer(queryId, { helpful, reason: helpful ? null : reason, comment: helpful ? null : comment })
      setFeedback(result.feedback)
      setEditing(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-3 border-t border-ink-200 pt-2 text-xs">
      <div className="flex flex-wrap gap-3">
        <button type="button" disabled={saving} aria-pressed={feedback?.helpful === true}
          className="font-semibold text-blue-900 disabled:opacity-50" onClick={() => save(true)}>
          {feedback?.helpful === true ? '✓ Me sirvió' : 'Me sirvió'}
        </button>
        <button type="button" disabled={saving} aria-pressed={feedback?.helpful === false}
          className="font-semibold text-blue-900 disabled:opacity-50" onClick={() => setEditing(!editing)}>
          {feedback?.helpful === false ? '✓ No me sirvió' : 'No me sirvió'}
        </button>
      </div>
      {editing && (
        <div className="mt-2 space-y-2 whitespace-normal">
          <label className="block">¿Qué podemos mejorar?
            <select aria-label="Motivo de la valoración" value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1 block w-full rounded border bg-white p-2">
              <option value="context">No entendió el contexto</option>
              <option value="incomplete">Respuesta incompleta</option>
              <option value="incorrect">Información incorrecta</option>
              <option value="other">Otro</option>
            </select>
          </label>
          <textarea aria-label="Comentario de la valoración" placeholder="Comentario opcional" maxLength={1000}
            value={comment} onChange={(e) => setComment(e.target.value)} className="block w-full rounded border bg-white p-2" />
          <button type="button" disabled={saving} onClick={() => save(false)} className="font-semibold text-blue-900">Guardar valoración</button>
        </div>
      )}
      {feedback && !editing && <p role="status" className="mt-1 text-ink-500">Valoración guardada. Puedes cambiarla.</p>}
      {error && <p role="alert" className="mt-1 text-wrong-700">{error}</p>}
    </div>
  )
}
