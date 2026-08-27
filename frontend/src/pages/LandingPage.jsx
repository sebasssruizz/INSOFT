import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowDown, faBookOpen, faChartLine, faEye, faKey } from '@fortawesome/free-solid-svg-icons'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'

const googleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)
const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true'

const FEATURES = [
  { icon: faBookOpen, color: 'bg-ins-600', title: 'Contenido oficial', text: 'Temas y subtemas de Oftalmología estructurados y verificados.' },
  { icon: faEye, color: 'bg-oft-600', title: 'Curso General', text: 'Acceso automático al Curso General de Oftalmología al registrarte.' },
  { icon: faKey, color: 'bg-ins-600', title: 'Cursos con código', text: 'Únete a los cursos de tus profesores con un código único.' },
  { icon: faChartLine, color: 'bg-oft-600', title: 'Tu progreso', text: 'Marca subtemas completados y visualiza tu avance.' },
]

export default function LandingPage() {
  const { loginGoogle, loginDevelopment } = useAuth()
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleGoogleSuccess = async (response) => {
    setError(null)
    setLoading(true)
    try {
      await loginGoogle(response.credential)
    } catch (err) {
      setError(err.message || 'No se pudo iniciar sesión con Google.')
    } finally {
      setLoading(false)
    }
  }

  const handleDevLogin = async (role) => {
    setError(null)
    setLoading(true)
    const isTeacher = role === 'TEACHER'
    const email = isTeacher ? 'profesor@demo.com' : 'estudiante@demo.com'
    const name = isTeacher ? 'Dr. Pérez' : 'Ana García'
    try {
      await loginDevelopment(email, name, role)
    } catch (err) {
      setError(err.message || 'Login de desarrollo no disponible.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Cabecera */}
      <header className="bg-white border-b border-slate-200">
        <div className="h-1 flex">
          <div className="w-1/2 bg-ins-500" />
          <div className="w-1/2 bg-oft-500" />
        </div>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Logo size="text-2xl" />
          <a
            href="#acceso"
            className="text-sm font-semibold text-ins-700 bg-ins-50 hover:bg-ins-100 border border-ins-200 rounded-lg px-4 py-2 transition-colors"
          >
            Acceder
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-16 md:py-24">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="flex gap-2 mb-6 flex-wrap justify-center">
            <span className="text-xs font-semibold bg-ins-600/90 text-white rounded-full px-3 py-1">
              INS · Instrumentación Quirúrgica
            </span>
            <span className="text-xs font-semibold bg-oft-600/90 text-white rounded-full px-3 py-1">
              OFT · Oftalmología
            </span>
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold text-white leading-tight">
            Aprende <span className="text-oft-300">Oftalmología</span> a tu ritmo
          </h1>
          <p className="mt-4 text-lg text-slate-300 max-w-2xl mx-auto">
            Sistema web de apoyo al aprendizaje de Oftalmología. Estudia el contenido oficial y sigue tu progreso.
          </p>
          <a
            href="#acceso"
            className="mt-8 inline-flex items-center gap-2 bg-oft-600 hover:bg-oft-700 text-white font-semibold rounded-xl px-8 py-3 text-base transition-colors shadow-lg shadow-black/30"
          >
            Comenzar ahora
            <FontAwesomeIcon icon={faArrowDown} />
          </a>
        </div>
      </section>

      {/* Características */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
            Todo lo que necesitas para estudiar
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {FEATURES.map((f) => (
              <article
                key={f.title}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <span className={`inline-flex w-10 h-10 rounded-lg ${f.color} text-white items-center justify-center text-base shadow-sm`}>
                  <FontAwesomeIcon icon={f.icon} />
                </span>
                <h3 className="mt-3 font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-1.5 text-sm text-slate-500 leading-relaxed">{f.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Acceso */}
      <section id="acceso" className="py-16 bg-slate-100">
        <div className="max-w-md mx-auto px-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
            <div className="h-1 flex rounded-full overflow-hidden mb-6">
              <div className="w-1/2 bg-ins-500" />
              <div className="w-1/2 bg-oft-500" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 text-center">Comienza ahora</h2>
            <p className="mt-2 text-sm text-slate-500 text-center">
              Inicia sesión con tu cuenta de Google para acceder a la plataforma.
            </p>

            <div className="mt-6 flex flex-col items-center gap-4">
              {googleConfigured ? (
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError('Error al autenticar con Google.')}
                  text="continue_with"
                  shape="rectangular"
                  size="large"
                  width="320"
                  locale="es"
                />
              ) : (
                !devLoginEnabled && (
                  <p className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                    Google OAuth no está configurado. Define <code>VITE_GOOGLE_CLIENT_ID</code> en el frontend y{' '}
                    <code>GOOGLE_CLIENT_ID</code> en el backend.
                  </p>
                )
              )}

              {loading && <p className="text-sm text-slate-500">Iniciando sesión…</p>}
              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3 w-full text-center">
                  {error}
                </p>
              )}

              {(devLoginEnabled || !googleConfigured) && (
                <div className="w-full border-t border-slate-200 pt-4 mt-2 space-y-3">
                  <p className="text-xs text-slate-400 text-center uppercase tracking-wide">
                    Acceso de desarrollo
                  </p>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => handleDevLogin('STUDENT')}
                    className="w-full bg-ins-600 hover:bg-ins-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors shadow-md disabled:opacity-50"
                  >
                    {loading ? 'Entrando…' : 'Entrar como Estudiante'}
                  </button>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => handleDevLogin('TEACHER')}
                    className="w-full bg-oft-600 hover:bg-oft-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors shadow-md disabled:opacity-50"
                  >
                    {loading ? 'Entrando…' : 'Entrar como Profesor'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        <span className="font-semibold">
          <span className="text-ins-600">INS</span>
          <span className="text-oft-600">OFT</span>
        </span>{' '}
        — Sistema web de apoyo al aprendizaje de Oftalmología
      </footer>
    </div>
  )
}
