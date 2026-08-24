import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCakeCandles, faGlobe, faPhone, faUserCheck } from '@fortawesome/free-solid-svg-icons'
import Logo from '../components/Logo'
import UniversityAutocomplete from '../components/UniversityAutocomplete'
import { useAuth } from '../hooks/useAuth'

export default function CompleteProfilePage() {
  const { user, completeProfile } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ country: '', age: '', phone: '', university: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await completeProfile({
        country: form.country.trim(),
        age: Number(form.age),
        phone: form.phone.trim() || null,
        university: form.university.trim(),
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-slate-300 pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500'

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-6">
          <Logo size="text-2xl" />
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-oft-100 border border-slate-100 p-8 animate-fade-in-up">
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
                  required
                  minLength={2}
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  placeholder="México, Colombia, España…"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Edad *</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <FontAwesomeIcon icon={faCakeCandles} />
                </span>
                <input
                  type="number"
                  required
                  min={10}
                  max={110}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: e.target.value })}
                  placeholder="22"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Teléfono (opcional)</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <FontAwesomeIcon icon={faPhone} />
                </span>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="+52 555 123 4567"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Universidad *</label>
              <UniversityAutocomplete
                value={form.university}
                onChange={(university) => setForm({ ...form, university })}
                required
              />
              <p className="mt-1 text-xs text-slate-400">
                Escribe al menos 3 letras y elige tu universidad de la lista.
              </p>
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
