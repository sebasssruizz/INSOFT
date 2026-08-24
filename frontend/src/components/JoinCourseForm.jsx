import { useState } from 'react'
import { joinCourse } from '../services/courseService'

export default function JoinCourseForm({ onJoined }) {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!code.trim()) return
    setLoading(true)
    setMessage(null)
    setError(null)
    try {
      const data = await joinCourse(code.trim())
      setMessage(data.message)
      setCode('')
      onJoined?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-dashed border-oft-300 p-5">
      <h3 className="font-semibold text-slate-900">Unirse a un curso</h3>
      <p className="text-sm text-slate-500 mt-1">Introduce el código que te ha compartido tu profesor.</p>
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="OFT-A72K"
          maxLength={12}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tracking-widest uppercase focus:outline-none focus:ring-2 focus:ring-oft-500"
        />
        <button
          type="submit"
          disabled={loading || !code.trim()}
          className="bg-ins-600 hover:bg-ins-700 text-white text-sm font-medium rounded-lg px-4 py-2 transition-all shadow-md shadow-oft-200 disabled:opacity-50"
        >
          {loading ? 'Uniéndote…' : 'Unirse'}
        </button>
      </div>
      {message && <p className="mt-2 text-sm text-green-600">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </form>
  )
}
