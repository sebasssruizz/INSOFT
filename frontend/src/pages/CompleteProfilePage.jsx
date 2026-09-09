import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faCakeCandles, faGlobe } from '@fortawesome/free-solid-svg-icons'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
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

  const fieldError = (field) => {
    if (!touched[field]) return null
    if (field === 'country') {
      if (!form.country.trim()) return 'Indica tu país.'
      if (form.country.trim().length < 2) return 'Escribe al menos dos caracteres.'
      return null
    }
    if (!form.age) return 'Indica tu edad.'
    const age = Number(form.age)
    if (Number.isNaN(age) || age < 10 || age > 110) return 'La edad debe estar entre 10 y 110.'
    return null
  }

  const countryError = fieldError('country')
  const ageError = fieldError('age')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setTouched({ country: true, age: true })
    if (
      !form.country.trim() ||
      form.country.trim().length < 2 ||
      !form.age ||
      Number(form.age) < 10 ||
      Number(form.age) > 110
    ) {
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

  const inputClass = (hasError) =>
    `w-full rounded-xl border bg-ink-50 py-2.5 pl-10 pr-3.5 text-sm text-ink-900 placeholder:text-ink-400 ` +
    `transition-colors duration-150 focus:bg-white ${
      hasError ? 'border-wrong-500 focus:border-wrong-500' : 'border-ink-300 focus:border-blue-500'
    }`

  return (
    <main className="flex min-h-screen items-center justify-center bg-ink-50 px-6 py-12">
      <div className="w-full max-w-md">
        <Logo size="lg" className="mx-auto" />

        <div className="animate-rise-in mt-8 rounded-2xl border border-ink-200 bg-white p-8 shadow-e2">
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
          >
            <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
            Salir
          </button>

          <h1 className="mt-6 text-[1.625rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
            Un par de datos y listo
          </h1>
          <p className="mt-2.5 text-sm leading-relaxed text-ink-500">
            Hola <span className="font-semibold text-ink-800">{user?.name}</span>. Solo usamos esto
            para conocer el perfil de quienes estudian en INSOFT.
          </p>

          <form onSubmit={handleSubmit} className="mt-7 space-y-5" noValidate>
            <div>
              <label htmlFor="country" className="mb-1.5 block text-xs font-semibold text-ink-600">
                País
              </label>
              <div className="relative">
                <span
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400"
                  aria-hidden="true"
                >
                  <FontAwesomeIcon icon={faGlobe} className="text-[0.8rem]" />
                </span>
                <input
                  id="country"
                  type="text"
                  value={form.country}
                  onChange={(event) => setForm({ ...form, country: event.target.value })}
                  onBlur={() => setTouched((prev) => ({ ...prev, country: true }))}
                  placeholder="Colombia"
                  aria-invalid={Boolean(countryError)}
                  className={inputClass(countryError)}
                />
              </div>
              {countryError && <p className="mt-1.5 text-xs text-wrong-700">{countryError}</p>}
            </div>

            <div>
              <label htmlFor="age" className="mb-1.5 block text-xs font-semibold text-ink-600">
                Edad
              </label>
              <div className="relative">
                <span
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400"
                  aria-hidden="true"
                >
                  <FontAwesomeIcon icon={faCakeCandles} className="text-[0.8rem]" />
                </span>
                <input
                  id="age"
                  type="number"
                  min={10}
                  max={110}
                  value={form.age}
                  onChange={(event) => setForm({ ...form, age: event.target.value })}
                  onBlur={() => setTouched((prev) => ({ ...prev, age: true }))}
                  placeholder="22"
                  aria-invalid={Boolean(ageError)}
                  className={inputClass(ageError)}
                />
              </div>
              {ageError && <p className="mt-1.5 text-xs text-wrong-700">{ageError}</p>}
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700"
              >
                {error}
              </p>
            )}

            <Button type="submit" loading={loading} className="w-full">
              Guardar y entrar
            </Button>
          </form>
        </div>
      </div>
    </main>
  )
}
