import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faCakeCandles, faGlobe, faUserCheck } from '@fortawesome/free-solid-svg-icons'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'

export default function CompleteProfilePage() {
  const { user, completeProfile, logout } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ country: '', age: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [touched, setTouched] = useState({ country: false, age: false })

  const handleBack = () => {
    logout()
    navigate('/')
  }

  const validate = () => {
    const errors = []
    if (!form.country.trim()) errors.push('El país es obligatorio.')
    if (form.country.trim().length < 2) errors.push('El país debe tener al menos 2 caracteres.')
    if (!form.age) errors.push('La edad es obligatoria.')
    const age = Number(form.age)
    if (isNaN(age) || age < 10 || age > 110) errors.push('La edad debe ser un número entre 10 y 110.')
    return errors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ country: true, age: true })
    const errors = validate()
    if (errors.length > 0) {
      setError(errors.join(' '))
      return
    }

    setLoading(true)
    setError(null)
    try {
      await completeProfile({
        country: form.country.trim(),
        age: Number(form.age),
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleBlur = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }))
  }

  const inputClass = (field) =>
    `w-full rounded-lg border pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500 ${
      touched[field] && !form[field].trim() ? 'border-red-300' : 'border-slate-300'
    }`

  const showError = (field) => touched[field] && !form[field].trim()

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-6">
          <Logo size="text-2xl" />
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-oft-100 border border-slate-100 p-8 animate-fade-in-up">
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-ins-600 mb-4 transition-colors"
          >
            <FontAwesomeIcon icon={faArrowLeft} />
            Atrás
          </button>

          <div className="text-center">
            <span className="inline-flex w-12 h-12 rounded-full bg-oft-600 text-white items-center justify-center text-lg shadow-md">
              <FontAwesomeIcon icon={faUserCheck} />
            </span>
            <h1 className="mt-3 text-xl font-bold text-slate-900">Completa tu perfil</h1>
            <p className="mt-1 text-sm text-slate-500">
              Hola <strong>{user?.name}</strong>, solo necesitamos algunos datos más para personalizar tu
              experiencia.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">País / Región *</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <FontAwesomeIcon icon={faGlobe} />
                </span>
                <input
                  type="text"
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  onBlur={() => handleBlur('country')}
                  placeholder="México, Colombia, España…"
                  className={inputClass('country')}
                />
              </div>
              {showError('country') && (
                <p className="mt-1 text-xs text-red-600">El país es obligatorio.</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Edad *</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <FontAwesomeIcon icon={faCakeCandles} />
                </span>
                <input
                  type="number"
                  min={10}
                  max={110}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: e.target.value })}
                  onBlur={() => handleBlur('age')}
                  placeholder="22"
                  className={inputClass('age')}
                />
              </div>
              {showError('age') && (
                <p className="mt-1 text-xs text-red-600">La edad es obligatoria.</p>
              )}
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-ins-600 hover:bg-ins-700 text-white font-medium rounded-lg py-2.5 text-sm transition-all shadow-md shadow-oft-200 disabled:opacity-50"
            >
              {loading ? 'Guardando…' : 'Guardar y continuar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
