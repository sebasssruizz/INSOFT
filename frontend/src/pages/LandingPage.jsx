import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowDown, faBookOpen, faChartLine, faEye, faKey } from '@fortawesome/free-solid-svg-icons'
import AnimatedEye from '../components/AnimatedEye'
import ImageCarousel from '../components/ImageCarousel'
import Logo from '../components/Logo'
import { SLIDESHOW_IMAGES } from '../data/slideshow'
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
  const [devForm, setDevForm] = useState({ email: '', name: '', role: 'STUDENT' })

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

  const handleDevSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await loginDevelopment(devForm.email, devForm.name || devForm.email, devForm.role)
    } catch (err) {
      setError(err.message || 'Login de desarrollo no disponible.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Cabecera flotante sobre el hero */}
      <header className="absolute top-0 inset-x-0 z-20">
        <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
          <Logo size="text-2xl" light />
          <a
            href="#acceso"
            className="text-sm font-semibold text-white bg-white/15 hover:bg-white/25 backdrop-blur-sm border border-white/30 rounded-lg px-4 py-2 transition-colors"
          >
            Acceder
          </a>
        </div>
      </header>

      {/* Hero: carrusel a todo el ancho */}
      <section className="relative w-full h-[82vh] min-h-[500px]">
        <ImageCarousel images={SLIDESHOW_IMAGES} interval={6000} className="absolute inset-0 w-full h-full" />
        <div className="absolute inset-0 bg-slate-900/55" />

        <div className="relative z-10 h-full max-w-6xl mx-auto px-4 flex flex-col items-center justify-center text-center">
          <div className="flex gap-2 mb-5 flex-wrap justify-center animate-fade-in-up">
            <span className="text-xs font-semibold bg-ins-600/90 text-white rounded-full px-3 py-1">
              INS · Instrumentación Quirúrgica
            </span>
            <span className="text-xs font-semibold bg-oft-600/90 text-white rounded-full px-3 py-1">
              OFT · Oftalmología
            </span>
          </div>

          <h1
            className="text-4xl md:text-6xl font-extrabold text-white leading-tight drop-shadow-lg animate-fade-in-up"
            style={{ animationDelay: '100ms' }}
          >
            Aprende <span className="text-oft-300">Oftalmología</span>
            <br />
            a tu ritmo
          </h1>
          <p
            className="mt-4 text-lg md:text-xl text-slate-200 max-w-xl animate-fade-in-up"
            style={{ animationDelay: '200ms' }}
          >
            Sistema web de apoyo al aprendizaje de Oftalmología. Estudia el contenido oficial y sigue tu
            progreso.
          </p>
          <a
            href="#acceso"
            className="mt-8 inline-flex items-center gap-2 bg-oft-600 hover:bg-oft-700 text-white font-semibold rounded-xl px-8 py-3.5 text-base transition-colors shadow-lg shadow-black/30 animate-fade-in-up"
            style={{ animationDelay: '300ms' }}
          >
            Comenzar ahora
            <FontAwesomeIcon icon={faArrowDown} />
          </a>
        </div>
      </section>

      {/* Características + acceso */}
      <section id="acceso" className="max-w-6xl w-full mx-auto px-4 py-16 grid md:grid-cols-2 gap-10 items-start">
        <div>
          <div className="flex justify-center md:justify-start mb-8">
            <AnimatedEye />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Todo lo que necesitas para estudiar</h2>
          <div className="mt-6 grid sm:grid-cols-2 gap-4">
            {FEATURES.map((f, i) => (
              <article
                key={f.title}
                className="animate-fade-in-up bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-slate-300 hover:-translate-y-0.5 transition-all duration-200"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span className={`inline-flex w-9 h-9 rounded-lg ${f.color} text-white items-center justify-center text-sm shadow-sm`}>
                  <FontAwesomeIcon icon={f.icon} />
                </span>
                <h3 className="mt-3 font-semibold text-slate-900 text-sm">{f.title}</h3>
                <p className="mt-1 text-xs text-slate-500 leading-relaxed">{f.text}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200 border border-slate-100 p-8 md:sticky md:top-8">
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

            {devLoginEnabled && (
              <form onSubmit={handleDevSubmit} className="w-full border-t border-slate-200 pt-4 mt-2 space-y-3">
                <p className="text-xs text-slate-400 text-center uppercase tracking-wide">
                  Acceso de desarrollo
                </p>
                <input
                  type="email"
                  required
                  placeholder="correo@ejemplo.com"
                  value={devForm.email}
                  onChange={(e) => setDevForm({ ...devForm, email: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500"
                />
                <input
                  type="text"
                  placeholder="Nombre (opcional)"
                  value={devForm.name}
                  onChange={(e) => setDevForm({ ...devForm, name: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500"
                />
                <select
                  value={devForm.role}
                  onChange={(e) => setDevForm({ ...devForm, role: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500"
                >
                  <option value="STUDENT">Estudiante</option>
                  <option value="TEACHER">Profesor</option>
                </select>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-ins-600 hover:bg-ins-700 text-white font-medium rounded-lg py-2 text-sm transition-colors shadow-md disabled:opacity-50"
                >
                  Entrar (desarrollo)
                </button>
              </form>
            )}
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
