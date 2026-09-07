import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faGraduationCap, faUserGraduate } from '@fortawesome/free-solid-svg-icons'
import { Link } from 'react-router-dom'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'

const googleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)
const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true'

export default function LoginPage() {
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
    const name = isTeacher ? 'Dra. Rojas' : 'Ana García'
    try {
      await loginDevelopment(email, name, role)
    } catch (err) {
      setError(err.message || 'El acceso de desarrollo no está disponible.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-5 py-10 font-sans antialiased">
      <img
        src="/images/slideshow/wall2.webp"
        alt=""
        aria-hidden="true"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-slate-950/65" />
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950/80 via-transparent to-slate-950/85" />

      <section className="relative z-10 w-full max-w-md rounded-3xl border border-white/20 bg-white/95 p-7 shadow-2xl backdrop-blur-md sm:p-9">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition-colors hover:text-ins-700"
        >
          <FontAwesomeIcon icon={faArrowLeft} />
          Volver al inicio
        </Link>

        <div className="mt-6 flex flex-col items-center text-center">
          <Logo size="text-2xl" />
          <h1 className="mt-6 text-2xl font-extrabold tracking-tight text-slate-900">Iniciar sesión</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Accede al Curso General y a los cursos de tus profesores.
          </p>
        </div>

        <div className="mt-7 flex flex-col items-center gap-4">
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
              <p className="w-full rounded-lg border border-amber-200 bg-amber-50 p-3 text-center text-sm text-amber-700">
                Google OAuth no está configurado.
              </p>
            )
          )}

          {loading && <p className="text-sm text-slate-500">Iniciando sesión…</p>}
          {error && (
            <p className="w-full rounded-lg border border-red-200 bg-red-50 p-3 text-center text-sm text-red-600">
              {error}
            </p>
          )}

          {(devLoginEnabled || !googleConfigured) && (
            <div className="mt-2 w-full space-y-3 border-t border-slate-200 pt-4">
              <p className="text-center text-xs uppercase tracking-wide text-slate-400">Acceso de desarrollo</p>
              <button
                type="button"
                disabled={loading}
                onClick={() => handleDevLogin('STUDENT')}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-ins-700 py-3 text-sm font-semibold text-white shadow-ins-sm transition-colors hover:bg-ins-800 disabled:opacity-50"
              >
                <FontAwesomeIcon icon={faUserGraduate} />
                {loading ? 'Entrando…' : 'Entrar como estudiante'}
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => handleDevLogin('TEACHER')}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-ins-300 py-3 text-sm font-semibold text-ins-800 transition-colors hover:bg-ins-50 disabled:opacity-50"
              >
                <FontAwesomeIcon icon={faGraduationCap} />
                {loading ? 'Entrando…' : 'Entrar como profesor'}
              </button>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
