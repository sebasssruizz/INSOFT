import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowDown, faBookOpen, faChartLine, faEye, faKey, faShieldHalved,
  faMicroscope, faStethoscope, faLaptopMedical, faUsers, faGraduationCap,
  faHeartPulse, faCheckCircle, faDesktop, faSyringe, faHandHoldingMedical,
} from '@fortawesome/free-solid-svg-icons'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'
import { useInView } from '../hooks/useInView'

const googleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)
const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true'

const FEATURES = [
  { icon: faBookOpen, title: 'Contenido oficial', text: 'Temas y subtemas de Oftalmología estructurados y verificados por expertos.' },
  { icon: faEye, title: 'Curso General', text: 'Acceso automático al Curso General de Oftalmología al registrarte.' },
  { icon: faKey, title: 'Cursos con código', text: 'Únete a los cursos de tus profesores con un código único de acceso.' },
  { icon: faChartLine, title: 'Tu progreso', text: 'Marca subtemas completados y visualiza tu avance en tiempo real.' },
  { icon: faLaptopMedical, title: 'Aprende a tu ritmo', text: 'Estudia desde cualquier dispositivo, cuando quieras y donde quieras.' },
  { icon: faShieldHalved, title: 'Plataforma segura', text: 'Autenticación con Google OAuth para proteger tu información.' },
]

const STATS = [
  { icon: faMicroscope, value: '14+', label: 'Subtemas oficiales' },
  { icon: faUsers, value: '2', label: 'Roles de usuario' },
  { icon: faGraduationCap, value: '∞', label: 'Cursos disponibles' },
  { icon: faHeartPulse, value: '24/7', label: 'Acceso continuo' },
]

const STEPS = [
  { icon: faCheckCircle, title: 'Regístrate', text: 'Inicia sesión con tu cuenta de Google o con el acceso de desarrollo.' },
  { icon: faLaptopMedical, title: 'Completa tu perfil', text: 'Indica tu país y edad para personalizar tu experiencia.' },
  { icon: faBookOpen, title: 'Estudia', text: 'Accede al Curso General o únete a cursos de tus profesores con un código.' },
  { icon: faChartLine, title: 'Avanza', text: 'Marca subtemas completados y sigue tu progreso visual.' },
]

function RevealSection({ children, className = '', animation = 'reveal-up', delay = 0 }) {
  const [ref, inView] = useInView(0.1)
  return (
    <div
      ref={ref}
      className={className}
      style={{ animationDelay: `${delay}ms` }}
    >
      {inView ? (
        <div className={`animate-${animation}`}>{children}</div>
      ) : (
        <div className="opacity-0">{children}</div>
      )}
    </div>
  )
}

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
    <div className="w-full min-h-screen bg-surgery-50">
      {/* Cabecera quirúrgica */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-surgery-200 shadow-sm">
        <div className="h-1 w-full bg-gradient-to-r from-ins-500 via-ins-400 to-oft-500" />
        <div className="w-full px-6 lg:px-12 py-3 flex items-center justify-between">
          <Logo size="text-2xl" />
          <a
            href="#acceso"
            className="text-sm font-semibold text-ins-700 bg-ins-50 hover:bg-ins-100 border border-ins-200 rounded-lg px-5 py-2 transition-all hover:shadow-md"
          >
            Acceder
          </a>
        </div>
      </header>

      {/* Hero — Estilo quirófano limpio */}
      <section className="w-full bg-gradient-to-b from-white via-ins-50/50 to-surgery-50 py-24 lg:py-36">
        <div className="w-full px-6 lg:px-12 text-center">
          <RevealSection animation="reveal-scale">
            <div className="inline-flex items-center gap-2 bg-ins-100 text-ins-700 rounded-full px-4 py-1.5 text-xs font-semibold mb-6">
              <FontAwesomeIcon icon={faMicroscope} className="text-sm" />
              Plataforma educativa de Oftalmología
            </div>
          </RevealSection>

          <RevealSection delay={150}>
            <h1 className="text-5xl lg:text-7xl font-extrabold text-slate-900 leading-tight tracking-tight">
              Aprende{' '}
              <span className="bg-gradient-to-r from-ins-500 to-oft-500 bg-clip-text text-transparent">
                Oftalmología
              </span>
              <br />
              a tu ritmo
            </h1>
          </RevealSection>

          <RevealSection delay={300}>
            <p className="mt-6 text-xl lg:text-2xl text-slate-500 max-w-3xl mx-auto leading-relaxed">
              Sistema web de apoyo al aprendizaje de Oftalmología e Instrumentación Quirúrgica.
              Estudia el contenido oficial y sigue tu progreso.
            </p>
          </RevealSection>

          <RevealSection delay={450}>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <a
                href="#acceso"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-ins-500 to-ins-600 hover:from-ins-600 hover:to-ins-700 text-white font-semibold rounded-xl px-8 py-4 text-lg transition-all shadow-lg shadow-ins-500/25 hover:shadow-xl hover:shadow-ins-500/30 hover:-translate-y-0.5"
              >
                Comenzar ahora
                <FontAwesomeIcon icon={faArrowDown} />
              </a>
              <a
                href="#features"
                className="inline-flex items-center gap-2 bg-white hover:bg-surgery-50 text-slate-700 font-semibold rounded-xl px-8 py-4 text-lg border border-surgery-200 transition-all hover:shadow-md hover:-translate-y-0.5"
              >
                Saber más
              </a>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Estadísticas */}
      <section className="w-full bg-white border-y border-surgery-200 py-12">
        <div className="w-full px-6 lg:px-12 grid grid-cols-2 lg:grid-cols-4 gap-8">
          {STATS.map((s, i) => (
            <RevealSection key={s.label} delay={i * 100}>
              <div className="text-center">
                <div className="inline-flex w-14 h-14 rounded-2xl bg-ins-50 text-ins-500 items-center justify-center text-xl mb-3 shadow-sm">
                  <FontAwesomeIcon icon={s.icon} />
                </div>
                <p className="text-3xl font-extrabold text-slate-900">{s.value}</p>
                <p className="text-sm text-slate-500 mt-1">{s.label}</p>
              </div>
            </RevealSection>
          ))}
        </div>
      </section>

      {/* Características */}
      <section id="features" className="w-full py-20 lg:py-28 bg-surgery-50">
        <div className="w-full px-6 lg:px-12">
          <RevealSection>
            <div className="text-center mb-14">
              <div className="inline-flex items-center gap-2 bg-oft-50 text-oft-600 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
                <FontAwesomeIcon icon={faStethoscope} className="text-sm" />
                Herramientas de estudio
              </div>
              <h2 className="text-3xl lg:text-4xl font-extrabold text-slate-900">
                Todo lo que necesitas para estudiar
              </h2>
              <p className="mt-3 text-lg text-slate-500 max-w-2xl mx-auto">
                Una plataforma completa diseñada para estudiantes y profesores de Oftalmología.
              </p>
            </div>
          </RevealSection>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <RevealSection key={f.title} delay={i * 80}>
                <article className="group h-full bg-white rounded-2xl border border-surgery-200 p-6 shadow-sm hover:shadow-lg hover:border-ins-300 hover:-translate-y-1 transition-all duration-300">
                  <span className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-br from-ins-500 to-oft-500 text-white items-center justify-center text-lg shadow-md group-hover:scale-110 transition-transform duration-300">
                    <FontAwesomeIcon icon={f.icon} />
                  </span>
                  <h3 className="mt-4 font-bold text-slate-900 text-lg">{f.title}</h3>
                  <p className="mt-2 text-sm text-slate-500 leading-relaxed">{f.text}</p>
                </article>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section className="w-full py-20 lg:py-28 bg-white">
        <div className="w-full px-6 lg:px-12">
          <RevealSection>
            <div className="text-center mb-14">
              <div className="inline-flex items-center gap-2 bg-ins-50 text-ins-600 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
                <FontAwesomeIcon icon={faDesktop} className="text-sm" />
                Proceso simple
              </div>
              <h2 className="text-3xl lg:text-4xl font-extrabold text-slate-900">
                ¿Cómo funciona?
              </h2>
            </div>
          </RevealSection>

          <div className="grid md:grid-cols-4 gap-8">
            {STEPS.map((s, i) => (
              <RevealSection key={s.title} delay={i * 120}>
                <div className="text-center">
                  <div className="relative inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-ins-500 to-ins-600 text-white text-2xl mb-5 shadow-lg shadow-ins-500/20">
                    <FontAwesomeIcon icon={s.icon} />
                    <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-oft-500 text-white text-xs font-bold flex items-center justify-center shadow-md">
                      {i + 1}
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-lg">{s.title}</h3>
                  <p className="mt-2 text-sm text-slate-500 leading-relaxed">{s.text}</p>
                </div>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* Contenido académico */}
      <section className="w-full py-20 lg:py-28 bg-gradient-to-b from-surgery-50 to-white">
        <div className="w-full px-6 lg:px-12 grid lg:grid-cols-2 gap-16 items-center">
          <RevealSection animation="reveal-left">
            <div>
              <div className="inline-flex items-center gap-2 bg-oft-50 text-oft-600 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
                <FontAwesomeIcon icon={faSyringe} className="text-sm" />
                Contenido académico
              </div>
              <h2 className="text-3xl lg:text-4xl font-extrabold text-slate-900">
                Contenido oficial de Oftalmología
              </h2>
              <p className="mt-4 text-lg text-slate-500 leading-relaxed">
                Accede a temas y subtemas verificados por expertos: Anatomía ocular, Glaucoma,
                Catarata, Patologías de la retina y más.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  'Temas estructurados con subtemas detallados',
                  'Contenido verificado y actualizado',
                  'Seguimiento de progreso individual',
                  'Acceso desde cualquier dispositivo',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <FontAwesomeIcon icon={faCheckCircle} className="text-ins-500 mt-1 shrink-0" />
                    <span className="text-slate-600">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </RevealSection>

          <RevealSection animation="reveal-right" delay={200}>
            <div className="grid grid-cols-2 gap-4">
              {[
                { icon: faEye, label: 'Anatomía ocular', color: 'from-ins-400 to-ins-600' },
                { icon: faHandHoldingMedical, label: 'Glaucoma', color: 'from-oft-400 to-oft-600' },
                { icon: faMicroscope, label: 'Catarata', color: 'from-ins-500 to-oft-500' },
                { icon: faHeartPulse, label: 'Patologías retina', color: 'from-oft-500 to-ins-500' },
              ].map((item) => (
                <div
                  key={item.label}
                  className={`bg-gradient-to-br ${item.color} rounded-2xl p-6 text-white shadow-lg hover:scale-105 transition-transform`}
                >
                  <FontAwesomeIcon icon={item.icon} className="text-3xl mb-3" />
                  <p className="font-semibold">{item.label}</p>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Acceso */}
      <section id="acceso" className="w-full py-20 lg:py-28 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="w-full px-6 lg:px-12 grid lg:grid-cols-2 gap-16 items-center">
          <RevealSection animation="reveal-left">
            <div className="text-white">
              <div className="inline-flex items-center gap-2 bg-ins-500/20 text-ins-300 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
                <FontAwesomeIcon icon={faUsers} className="text-sm" />
                Únete a INSOFT
              </div>
              <h2 className="text-3xl lg:text-4xl font-extrabold">
                Comienza a estudiar hoy
              </h2>
              <p className="mt-4 text-lg text-slate-300 leading-relaxed">
                Inicia sesión con tu cuenta de Google para acceder a la plataforma completa.
                O usa el acceso de desarrollo para explorar.
              </p>
            </div>
          </RevealSection>

          <RevealSection animation="reveal-right" delay={200}>
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <div className="h-1 w-full rounded-full overflow-hidden mb-6 surgical-line" />
              <h3 className="text-xl font-bold text-slate-900 text-center">Iniciar sesión</h3>

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
                      Google OAuth no está configurado.
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
                  <div className="w-full border-t border-surgery-200 pt-4 mt-2 space-y-3">
                    <p className="text-xs text-slate-400 text-center uppercase tracking-wide">
                      Acceso de desarrollo
                    </p>
                    <button
                      type="button"
                      disabled={loading}
                      onClick={() => handleDevLogin('STUDENT')}
                      className="w-full bg-ins-600 hover:bg-ins-700 text-white font-medium rounded-lg py-3 text-sm transition-all shadow-md disabled:opacity-50 hover:shadow-lg"
                    >
                      {loading ? 'Entrando…' : 'Entrar como Estudiante'}
                    </button>
                    <button
                      type="button"
                      disabled={loading}
                      onClick={() => handleDevLogin('TEACHER')}
                      className="w-full bg-oft-600 hover:bg-oft-700 text-white font-medium rounded-lg py-3 text-sm transition-all shadow-md disabled:opacity-50 hover:shadow-lg"
                    >
                      {loading ? 'Entrando…' : 'Entrar como Profesor'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full bg-slate-900 text-slate-400 py-10 border-t border-slate-800">
        <div className="w-full px-6 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo size="text-xl" withIcon />
            <span className="text-sm ml-3">
              — Sistema web de apoyo al aprendizaje de Oftalmología
            </span>
          </div>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} INSOFT. Todos los derechos reservados.
          </p>
        </div>
      </footer>
    </div>
  )
}
