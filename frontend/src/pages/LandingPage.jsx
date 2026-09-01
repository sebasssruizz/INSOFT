import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { motion, useReducedMotion } from 'motion/react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight, faBookOpen, faChartLine, faKey, faShieldHalved,
  faLaptopMedical, faGraduationCap, faCircleCheck, faLayerGroup,
  faUserGraduate,
} from '@fortawesome/free-solid-svg-icons'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'
import { ProcessTimeline } from '../components/ui/process-timeline'
import { SectionHeading } from '../components/ui/section-heading'

const googleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)
const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true'

const TOPICS = [
  { name: 'Anatomía ocular', count: 4 },
  { name: 'Glaucoma', count: 4 },
  { name: 'Catarata', count: 3 },
  { name: 'Patologías de la retina', count: 3 },
]

const PROCESS_PHASES = [
  {
    id: 'paso-1',
    title: 'Accede a la plataforma',
    description:
      'Inicia sesión con tu cuenta de Google. No hay que crear ninguna contraseña nueva ni rellenar formularios largos.',
  },
  {
    id: 'paso-2',
    title: 'Completa tu perfil',
    description:
      'Indica tu país y tu edad una sola vez. Con eso ya tienes acceso al Curso General de Oftalmología.',
  },
  {
    id: 'paso-3',
    title: 'Estudia el temario',
    description:
      'Recorre los temas y subtemas del contenido oficial. Si tu profesor te pasa un código, únete también a su curso.',
  },
  {
    id: 'paso-4',
    title: 'Sigue tu avance',
    description:
      'Marca cada subtema cuando lo termines. La plataforma calcula tu progreso en cada curso automáticamente.',
  },
]

const EASE = [0.16, 1, 0.3, 1]

function Reveal({ children, className = '', delay = 0 }) {
  const reduce = useReducedMotion()
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.6, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  )
}

function FeatureIcon({ icon, variant = 'ins' }) {
  const styles = {
    ins: 'bg-ins-50 text-ins-700',
    oft: 'bg-oft-50 text-oft-600',
    onDark: 'bg-white/10 text-white backdrop-blur',
  }
  return (
    <span className={`inline-flex h-11 w-11 items-center justify-center rounded-xl text-lg ${styles[variant]}`}>
      <FontAwesomeIcon icon={icon} />
    </span>
  )
}

export default function LandingPage() {
  const { loginGoogle, loginDevelopment } = useAuth()
  const reduce = useReducedMotion()
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

  const heroStagger = reduce
    ? {}
    : { initial: 'hidden', animate: 'show', variants: { show: { transition: { staggerChildren: 0.09 } } } }
  const heroItem = reduce
    ? {}
    : { variants: { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } } } }

  return (
    <div className="w-full bg-white font-sans text-slate-700 antialiased">
      {/* Cabecera */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="h-1 w-full bg-ins-600" />
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Logo size="text-2xl" />
          <a
            href="#acceso"
            className="rounded-lg bg-ins-700 px-5 py-2 text-sm font-semibold text-white shadow-ins-sm transition-colors hover:bg-ins-800"
          >
            Acceder
          </a>
        </div>
      </header>

      {/* Hero — split asimétrico sobre un lavado verde suave */}
      <section className="bg-gradient-to-b from-ins-50 via-white to-white">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 pb-16 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pb-24 lg:pt-20">
          <motion.div {...heroStagger}>
            <motion.p
              {...heroItem}
              className="text-sm font-semibold uppercase tracking-[0.16em] text-ins-700"
            >
              Plataforma de aprendizaje de Oftalmología
            </motion.p>
            <motion.h1
              {...heroItem}
              className="mt-4 text-4xl font-extrabold leading-[1.08] tracking-tight text-slate-900 md:text-5xl lg:text-6xl"
            >
              Aprende <span className="text-ins-700">Oftalmología</span> con el contenido oficial
            </motion.h1>
            <motion.p
              {...heroItem}
              className="mt-5 max-w-[52ch] text-lg leading-relaxed text-slate-500"
            >
              Estudia temas verificados, únete a los cursos de tu facultad con un código y sigue tu
              progreso en cada subtema.
            </motion.p>
            <motion.div {...heroItem} className="mt-8 flex flex-wrap gap-3">
              <motion.a
                href="#acceso"
                whileHover={reduce ? undefined : { y: -2 }}
                whileTap={reduce ? undefined : { scale: 0.98 }}
                className="inline-flex items-center gap-2 rounded-xl bg-ins-700 px-7 py-3.5 text-base font-semibold text-white shadow-ins-md transition-colors hover:bg-ins-800"
              >
                Acceder
                <FontAwesomeIcon icon={faArrowRight} />
              </motion.a>
              <a
                href="#como-funciona"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-7 py-3.5 text-base font-semibold text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-50"
              >
                Ver cómo funciona
              </a>
            </motion.div>

            {/* Una sola cifra, integrada en el hero */}
            <motion.div {...heroItem} className="mt-10 flex items-center gap-4 border-t border-slate-200 pt-6">
              <span className="text-4xl font-extrabold tracking-tight text-slate-900">14</span>
              <span className="max-w-[22ch] text-sm leading-tight text-slate-500">
                subtemas del temario oficial de Oftalmología, disponibles desde el primer día
              </span>
            </motion.div>
          </motion.div>

          {/* Visual: foto real + tarjeta de progreso (vista de producto) */}
          <Reveal delay={0.15} className="relative">
            <div className="overflow-hidden rounded-3xl border border-slate-200 shadow-ins-lg">
              <img
                src="/images/slideshow/slide-2.jpg"
                alt="Profesional realizando una exploración oftalmológica con lámpara de hendidura"
                className="h-full w-full object-cover"
                loading="eager"
                width={1280}
                height={960}
              />
            </div>
            <div className="absolute -bottom-6 -left-4 hidden w-64 rounded-2xl border border-slate-200 bg-white p-4 shadow-ins-lg sm:block">
              <p className="text-xs font-semibold text-slate-900">Curso General de Oftalmología</p>
              {[
                { label: 'Anatomía ocular', value: 100 },
                { label: 'Glaucoma', value: 60 },
                { label: 'Catarata', value: 25 },
              ].map((row) => (
                <div key={row.label} className="mt-2.5">
                  <div className="flex justify-between text-[11px] text-slate-500">
                    <span>{row.label}</span>
                    <span className="font-semibold text-ins-700">{row.value}%</span>
                  </div>
                  <div className="mt-1 h-1.5 w-full rounded-full bg-slate-200">
                    <div className="h-1.5 rounded-full bg-ins-500" style={{ width: `${row.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* Lo que necesitas — bento sobre gris claro */}
      <section id="caracteristicas" className="border-y border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16 lg:py-24">
          <Reveal>
            <SectionHeading accent="ins" className="max-w-2xl">
              Lo que necesitas para estudiar, y nada más
            </SectionHeading>
            <p className="mt-4 max-w-xl text-lg text-slate-500">
              Una plataforma centrada en el contenido oficial y en tu progreso.
            </p>
          </Reveal>

          <div className="mt-12 grid gap-4 lg:grid-cols-12">
            {/* A — celda grande con imagen */}
            <Reveal className="lg:col-span-8">
              <article className="relative flex h-full min-h-[300px] flex-col justify-end overflow-hidden rounded-2xl border border-slate-200">
                <img
                  src="/images/slideshow/slide-5.jpg"
                  alt="Quirófano oftalmológico preparado"
                  className="absolute inset-0 h-full w-full object-cover"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/45 to-transparent" />
                <div className="relative p-7">
                  <FeatureIcon icon={faBookOpen} variant="onDark" />
                  <h3 className="mt-4 text-xl font-bold text-white">Contenido oficial</h3>
                  <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-200">
                    Temas y subtemas de Oftalmología estructurados y revisados. Una sola fuente,
                    compartida por todos los cursos sin duplicarse.
                  </p>
                </div>
              </article>
            </Reveal>

            {/* B — celda tintada de verde */}
            <Reveal delay={0.05} className="lg:col-span-4">
              <article className="flex h-full flex-col rounded-2xl border border-ins-100 bg-ins-50 p-6">
                <FeatureIcon icon={faGraduationCap} variant="ins" />
                <h3 className="mt-4 text-lg font-bold text-slate-900">Curso General</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  Acceso automático al registrarte, sin necesidad de código.
                </p>
              </article>
            </Reveal>

            {/* C — celda oscura */}
            <Reveal delay={0.05} className="lg:col-span-4">
              <article className="flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <FeatureIcon icon={faKey} variant="onDark" />
                <h3 className="mt-4 text-lg font-bold text-white">Cursos con código</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">
                  Únete a la clase de tu profesor con un código único OFT-XXXX.
                </p>
              </article>
            </Reveal>

            {/* D */}
            <Reveal delay={0.1} className="lg:col-span-4">
              <article className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-slate-300">
                <FeatureIcon icon={faChartLine} variant="oft" />
                <h3 className="mt-4 text-lg font-bold text-slate-900">Tu progreso</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Marca cada subtema completado y consulta tu porcentaje de avance.
                </p>
              </article>
            </Reveal>

            {/* E */}
            <Reveal delay={0.1} className="lg:col-span-4">
              <article className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-slate-300">
                <FeatureIcon icon={faLaptopMedical} variant="ins" />
                <h3 className="mt-4 text-lg font-bold text-slate-900">Multidispositivo</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Estudia desde el móvil, la tablet o el ordenador, a tu ritmo.
                </p>
              </article>
            </Reveal>

            {/* F — banda verde ancha */}
            <Reveal delay={0.15} className="lg:col-span-12">
              <article className="flex flex-col justify-between gap-4 rounded-2xl bg-ins-700 p-7 text-white sm:flex-row sm:items-center">
                <div className="flex items-start gap-4">
                  <FeatureIcon icon={faShieldHalved} variant="onDark" />
                  <div>
                    <h3 className="text-lg font-bold">Acceso con tu cuenta de Google</h3>
                    <p className="mt-1 max-w-lg text-sm leading-relaxed text-ins-50">
                      Autenticación verificada en el servidor. Sin contraseñas nuevas que recordar.
                    </p>
                  </div>
                </div>
                <a
                  href="#acceso"
                  className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-ins-800 transition-colors hover:bg-ins-50"
                >
                  Acceder
                  <FontAwesomeIcon icon={faArrowRight} />
                </a>
              </article>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Cómo funciona — sección oscura y compacta con timeline horizontal */}
      <section id="como-funciona" className="bg-slate-950">
        <ProcessTimeline
          phases={PROCESS_PHASES}
          title="¿Cómo funciona?"
          intro="Cuatro pasos desde que entras hasta que empiezas a seguir tu progreso."
        />
      </section>

      {/* Temario — imagen + texto sobre blanco */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:gap-16 lg:py-24">
        <Reveal className="order-2 lg:order-1">
          <div className="overflow-hidden rounded-3xl border border-slate-200 shadow-ins-lg">
            <img
              src="/images/slideshow/slide-3.jpg"
              alt="Equipo quirúrgico durante una intervención oftalmológica con microscopio"
              className="h-full w-full object-cover"
              loading="lazy"
            />
          </div>
        </Reveal>

        <div className="order-1 lg:order-2">
          <Reveal>
            <SectionHeading accent="ins">El temario oficial de Oftalmología</SectionHeading>
            <p className="mt-4 text-lg leading-relaxed text-slate-500">
              El contenido existe una sola vez y lo comparten todos los cursos. Estos son los temas
              que encontrarás al entrar:
            </p>
          </Reveal>
          <ul className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
            {TOPICS.map((topic, i) => (
              <Reveal key={topic.name} delay={i * 0.05}>
                <li className="flex items-center justify-between py-3.5">
                  <span className="flex items-center gap-3 font-medium text-slate-800">
                    <FontAwesomeIcon
                      icon={faLayerGroup}
                      className={i % 2 === 0 ? 'text-ins-600' : 'text-oft-500'}
                    />
                    {topic.name}
                  </span>
                  <span className="text-sm text-slate-400">{topic.count} subtemas</span>
                </li>
              </Reveal>
            ))}
          </ul>
        </div>
      </section>

      {/* Acceso — bloque oscuro de cierre */}
      <section id="acceso" className="bg-slate-950 py-16 lg:py-24">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 lg:grid-cols-2 lg:gap-16">
          <Reveal>
            <SectionHeading accent="oft" tone="dark">Empieza a estudiar hoy</SectionHeading>
            <p className="mt-4 max-w-md text-lg leading-relaxed text-slate-300">
              Inicia sesión con tu cuenta de Google para acceder al Curso General y a los cursos de
              tus profesores.
            </p>
            <ul className="mt-6 space-y-2.5">
              {['Sin coste para estudiantes', 'Acceso inmediato al Curso General', 'Tu progreso guardado en cada curso'].map((item) => (
                <li key={item} className="flex items-center gap-3 text-slate-200">
                  <FontAwesomeIcon icon={faCircleCheck} className="text-ins-400" />
                  {item}
                </li>
              ))}
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="rounded-2xl bg-white p-8 shadow-2xl">
              <div className="mb-6 h-1 w-full rounded-full bg-ins-600" />
              <h3 className="text-center text-xl font-bold text-slate-900">Iniciar sesión</h3>

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
                    <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-center text-sm text-amber-700">
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
                    <p className="text-center text-xs uppercase tracking-wide text-slate-400">
                      Acceso de desarrollo
                    </p>
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
            </div>
          </Reveal>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-10 text-slate-400">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 md:flex-row">
          <div className="flex items-center gap-3">
            <Logo size="text-lg" light />
            <span className="text-sm">Sistema web de apoyo al aprendizaje de Oftalmología</span>
          </div>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} INSOFT. Todos los derechos reservados.
          </p>
        </div>
      </footer>
    </div>
  )
}
