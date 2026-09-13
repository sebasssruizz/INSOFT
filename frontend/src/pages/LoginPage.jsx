import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faGraduationCap, faUserGraduate } from '@fortawesome/free-solid-svg-icons'
import { Link } from 'react-router-dom'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
import { CURRICULUM_FACTS } from '../lib/curriculum'
import { useAuth } from '../hooks/useAuth'

const googleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)
const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true'

export default function LoginPage() {
  const { loginGoogle, loginDevelopment } = useAuth()
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(null)

  const handleGoogleSuccess = async (response) => {
    setError(null)
    setLoading('google')
    try {
      await loginGoogle(response.credential)
    } catch (err) {
      setError(err.message || 'No se pudo iniciar sesión con Google.')
    } finally {
      setLoading(null)
    }
  }

  const handleDevLogin = async (role) => {
    setError(null)
    setLoading(role)
    const isTeacher = role === 'TEACHER'
    try {
      await loginDevelopment(
        isTeacher ? 'profesor@demo.com' : 'estudiante@demo.com',
        isTeacher ? 'Dra. Rojas' : 'Ana García',
        role,
      )
    } catch (err) {
      setError(err.message || 'El acceso de desarrollo no está disponible.')
    } finally {
      setLoading(null)
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1fr_minmax(0,30rem)]">
      {/* Lado editorial: solo en pantallas anchas */}
      <section className="relative hidden overflow-hidden bg-ink-900 lg:block">
        <img
          src="/images/slideshow/wall2.webp"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-gradient-to-t from-ink-950/85 via-ink-950/45 to-ink-950/35"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-32 -left-24 h-[32rem] w-[32rem] rounded-full bg-blue-800/20 blur-3xl"
        />

        <div className="relative z-10 flex h-full flex-col justify-between p-12">
          <Logo light size="lg" />

          <div>
            <h1 className="max-w-[14ch] text-[3rem] font-semibold leading-[1.06] tracking-[-0.03em] text-white">
              Todo el temario, en un solo sitio.
            </h1>
            <dl className="mt-10 flex gap-12 border-t border-white/15 pt-8">
              <div>
                <dd className="tabular font-display text-4xl font-semibold text-white">
                  {CURRICULUM_FACTS.units}
                </dd>
                <dt className="mt-1.5 text-[0.8125rem] text-white/70">Unidades</dt>
              </div>
              <div>
                <dd className="tabular font-display text-4xl font-semibold text-white">
                  {CURRICULUM_FACTS.subtopics}
                </dd>
                <dt className="mt-1.5 text-[0.8125rem] text-white/70">Subtemas</dt>
              </div>
              <div>
                <dd className="tabular font-display text-4xl font-semibold text-white">
                  {CURRICULUM_FACTS.questions}
                </dd>
                <dt className="mt-1.5 text-[0.8125rem] text-white/70">Preguntas</dt>
              </div>
            </dl>
          </div>
        </div>
      </section>

      {/* Lado de acceso */}
      <section className="flex flex-col justify-center bg-white px-6 py-12 sm:px-12">
        <div className="mx-auto w-full max-w-sm">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
          >
            <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
            Volver al inicio
          </Link>

          <div className="mt-10 lg:hidden">
            <Logo size="lg" />
          </div>

          <h2 className="mt-8 text-[2rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
            Iniciar sesión
          </h2>
          <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-500">
            Accede al Curso General y a los cursos de tus profesores.
          </p>

          <div className="mt-8 space-y-4">
            {googleConfigured ? (
              <div className="flex justify-center [color-scheme:light]">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError('Error al autenticar con Google.')}
                  text="continue_with"
                  shape="rectangular"
                  size="large"
                  width="360"
                  locale="es"
                />
              </div>
            ) : (
              !devLoginEnabled && (
                <p className="rounded-xl border border-ink-200 bg-ink-50 px-4 py-3 text-center text-sm text-ink-600">
                  Google OAuth todavía no está configurado en este entorno.
                </p>
              )
            )}

            {error && (
              <p
                role="alert"
                className="rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-center text-sm text-wrong-700"
              >
                {error}
              </p>
            )}

            {(devLoginEnabled || !googleConfigured) && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-4">
                  <span className="h-px flex-1 bg-ink-200" />
                  <span className="eyebrow text-ink-400">Acceso de desarrollo</span>
                  <span className="h-px flex-1 bg-ink-200" />
                </div>

                <Button
                  type="button"
                  onClick={() => handleDevLogin('STUDENT')}
                  loading={loading === 'STUDENT'}
                  disabled={Boolean(loading)}
                  icon={faUserGraduate}
                  className="w-full"
                >
                  Entrar como estudiante
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => handleDevLogin('TEACHER')}
                  loading={loading === 'TEACHER'}
                  disabled={Boolean(loading)}
                  icon={faGraduationCap}
                  className="w-full"
                >
                  Entrar como profesor
                </Button>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}
