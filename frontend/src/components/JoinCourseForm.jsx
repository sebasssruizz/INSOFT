import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faKey } from '@fortawesome/free-solid-svg-icons'

import { Button } from './ui/Button'
import { joinCourse } from '../services/courseService'

export default function JoinCourseForm({ onJoined }) {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
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
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-ink-200 bg-white p-6 shadow-e1"
    >
      <span
        className="flex h-10 w-10 items-center justify-center rounded-2xl bg-soft-lavender text-deep-lavender"
        aria-hidden="true"
      >
        <FontAwesomeIcon icon={faKey} />
      </span>

      <h3 className="mt-4 text-lg font-semibold tracking-[-0.01em] text-ink-900">
        Unirme a un curso
      </h3>
      <p className="mt-1.5 text-sm leading-relaxed text-ink-500">
        Con el código que te comparte tu profesor.
      </p>

      <label htmlFor="course-code" className="sr-only">
        Código del curso
      </label>
      <input
        id="course-code"
        type="text"
        value={code}
        onChange={(event) => setCode(event.target.value.toUpperCase())}
        placeholder="OFT-A72K"
        maxLength={12}
        autoComplete="off"
        className="mt-4 w-full rounded-xl border border-ink-300 bg-ink-50 px-3.5 py-2.5 text-center font-sans text-base font-bold uppercase tracking-[0.22em] text-ink-900 placeholder:font-medium placeholder:tracking-[0.22em] placeholder:text-ink-400 transition-colors duration-150 focus:border-blue-500 focus:bg-white"
      />

      <Button type="submit" loading={loading} disabled={!code.trim()} className="mt-3 w-full">
        {loading ? 'Uniéndote…' : 'Unirme'}
      </Button>

      {message && (
        <p className="mt-3 flex items-start gap-2 text-sm text-correct-700">
          <FontAwesomeIcon icon={faCircleCheck} className="mt-0.5 shrink-0" aria-hidden="true" />
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm text-wrong-700">
          {error}
        </p>
      )}
    </form>
  )
}
