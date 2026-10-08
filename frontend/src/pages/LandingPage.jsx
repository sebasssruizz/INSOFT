import { Suspense, lazy, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight,
  faBars,
  faBookOpen,
  faCube,
  faListCheck,
  faRobot,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
import { IrisMark } from '../components/ui/IrisMark'
import { CURRICULUM_FACTS } from '../lib/curriculum'
import { useReveal } from '../hooks/useReveal'
import { cn } from '../lib/utils'

// Cifras del temario, sin porcentajes inventados: solo lo que se puede contar
// en app/seed/seed_content.py y seed_questions.py.
const FACTS = [
  { value: CURRICULUM_FACTS.units, label: 'unidades' },
  { value: CURRICULUM_FACTS.subtopics, label: 'subtemas' },
  { value: CURRICULUM_FACTS.questions, label: 'preguntas' },
]

// GSAP solo lo usa el temario de la portada: entra en diferido para que no
// viaje en el paquete de la aplicación de quien ya inició sesión.
const Timeline = lazy(() => import('../components/ui/Timeline'))

const NAV_LINKS = [
  { href: '#temario', label: 'Temario' },
  { href: '#plataforma', label: 'Plataforma' },
  { href: '#como-funciona', label: 'Cómo funciona' },
]

// Una entrada por unidad del seed oficial. La descripción nombra los subtemas
// reales de cada unidad: es lo que el estudiante va a encontrar dentro.
const UNITS = [
  {
    id: 'u1',
    title: 'Generalidades en cirugía oftalmológica',
    description:
      'Anatomía del globo ocular, anestesia, instrumental, equipos, suturas, medicación y protocolos del instrumentador.',
    meta: '7 subtemas',
  },
  {
    id: 'u2',
    title: 'Procedimientos generales',
    description:
      'Resección de pterigión, drenaje de chalazión, dilatación de vías lagrimales e inyecciones intravítreas.',
    meta: '4 subtemas',
  },
  {
    id: 'u3',
    title: 'Glaucoma',
    description:
      'Trabeculotomía con iridectomía periférica, implantes de drenaje del humor acuoso e iridectomía con láser.',
    meta: '3 subtemas',
  },
  {
    id: 'u4',
    title: 'Cirugías del segmento anterior',
    description: 'Facoemulsificación, extracción extracapsular y trasplante de córnea.',
    meta: '3 subtemas',
  },
  {
    id: 'u5',
    title: 'Cirugías vitreorretinales',
    description: 'Vitrectomías del segmento anterior y posterior, y manejo de la retinopatía.',
    meta: '2 subtemas',
  },
  {
    id: 'u6',
    title: 'Corrección de estrabismo',
    description: 'Técnicas de debilitamiento y refuerzo de los músculos extraoculares.',
    meta: '1 subtema',
  },
  {
    id: 'u7',
    title: 'Patologías refractivas',
    description:
      'Valoración y corrección de miopía, hipermetropía y astigmatismo, con preparación del equipo láser.',
    meta: '1 subtema',
  },
  {
    id: 'u8',
    title: 'Oculoplastia',
    description: 'Cirugía de párpados: anatomía aplicada, instrumental específico y cuidados.',
    meta: '1 subtema',
  },
  {
    id: 'u9',
    title: 'Pterigión, paso a paso',
    description:
      'Definición, indicaciones, técnica quirúrgica con su instrumentación y complicaciones.',
    meta: '4 subtemas',
  },
]

const FEATURES = [
  {
    icon: faBookOpen,
    title: 'Un solo temario oficial',
    body: 'Todos los cursos comparten el mismo contenido: nada de apuntes duplicados ni versiones que no coinciden.',
  },
  {
    icon: faListCheck,
    title: 'Repasos que explican',
    body: 'Cada pregunta te dice por qué la respuesta es la correcta, aciertes o no. Esa explicación es lo que se queda.',
  },
  {
    icon: faRobot,
    title: 'Un asistente para tus dudas',
    body: 'Pregunta lo que no te quedó claro y responde con base en el contenido de tu curso.',
  },
  {
    icon: faCube,
    title: 'Quirófano en 3D',
    body: 'Recorre una sala quirúrgica e inspecciona el instrumental antes de verlo en prácticas.',
  },
]

const STEPS = [
  {
    title: 'Entra con tu cuenta',
    body: 'Accedes con Google y el Curso General de Oftalmología aparece listo, sin configurar nada.',
  },
  {
    title: 'Estudia a tu ritmo',
    body: 'Cada subtema trae su lectura, su tiempo estimado y un repaso corto al terminar.',
  },
  {
    title: 'Pregunta y avanza',
    body: 'El asistente resuelve tus dudas y tu progreso se guarda subtema a subtema.',
  },
]

function Reveal({ children, delay = 0, className, as: Component = 'div', ...props }) {
  const [ref, revealed] = useReveal({ amount: 0.2 })
  return (
    <Component
      ref={ref}
      className={cn(
        'transition-[opacity,transform] duration-700 ease-out',
        revealed ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0',
        className,
      )}
      style={{ transitionDelay: `${delay}ms` }}
      {...props}
    >
      {children}
    </Component>
  )
}

/** Cabecera de sección: versalita, titular y una regla fina. Sin adornos. */
function SectionTitle({ eyebrow, children, className }) {
  return (
    <div className={cn('border-t border-ink-300 pt-6', className)}>
      <p className="eyebrow text-blue-900">{eyebrow}</p>
      <h2 className="mt-3 max-w-[22ch] text-[1.75rem] font-bold leading-[1.15] tracking-[-0.02em] text-ink-900 sm:text-[2.125rem] lg:text-[2.5rem]">
        {children}
      </h2>
    </div>
  )
}

/**
 * Navegación de la portada. Transparente sobre el vídeo; al bajar de la
 * portada pasa a fondo papel con borde, para seguir legible sobre el
 * contenido. En móvil los enlaces viven en un panel desplegable.
 */
function LandingNav() {
  // 'top': sobre el vídeo, sin fondo. 'hero': ya se bajó algo pero sigue sobre
  // el vídeo, con un velo oscuro para que los enlaces no se mezclen con el
  // contenido de la portada. 'page': pasada la portada, fondo papel.
  const [stage, setStage] = useState('top')
  const [open, setOpen] = useState(false)

  useEffect(() => {
    let frame = 0
    const hero = document.getElementById('inicio')
    const update = () => {
      const limit = (hero?.offsetHeight ?? window.innerHeight) - 72
      setStage(window.scrollY > limit ? 'page' : window.scrollY > 24 ? 'hero' : 'top')
    }
    const onScroll = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
    }
  }, [])

  const solid = stage === 'page' || open

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 border-b transition-[background-color,border-color,box-shadow] duration-300 ease-out',
        solid
          ? 'border-ink-200 bg-ink-50/90 shadow-e1 backdrop-blur-md'
          : stage === 'hero'
            ? 'border-white/10 bg-ink-950/45 backdrop-blur-md'
            : 'border-transparent',
      )}
    >
      <nav
        aria-label="Navegación principal"
        className="mx-auto flex h-16 max-w-[78rem] items-center justify-between gap-6 px-5 sm:px-6 lg:h-20 lg:px-10"
      >
        <a href="#inicio" aria-label="INSOFT, volver arriba" onClick={() => setOpen(false)}>
          <Logo light={!solid} size="md" />
        </a>

        <ul className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className={cn(
                  'group relative py-2 text-sm font-medium transition-colors duration-200',
                  solid ? 'text-ink-600 hover:text-ink-900' : 'text-white/80 hover:text-white',
                )}
              >
                {link.label}
                <span
                  aria-hidden="true"
                  className={cn(
                    'absolute inset-x-0 -bottom-0.5 h-px origin-left scale-x-0 transition-transform duration-300 ease-out group-hover:scale-x-100',
                    solid ? 'bg-blue-900' : 'bg-white',
                  )}
                />
              </a>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <Button
            as={Link}
            to="/login"
            variant={solid ? 'primary' : 'outline'}
            size="sm"
            className="hidden sm:inline-flex"
          >
            Acceder
          </Button>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            aria-controls="landing-menu"
            aria-label={open ? 'Cerrar el menú' : 'Abrir el menú'}
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg transition-colors duration-150 md:hidden',
              solid ? 'text-ink-700 hover:bg-ink-100' : 'text-white hover:bg-white/10',
            )}
          >
            <FontAwesomeIcon icon={open ? faXmark : faBars} />
          </button>
        </div>
      </nav>

      {open && (
        <div
          id="landing-menu"
          className="animate-fade-in border-t border-ink-200 bg-ink-50 px-5 pb-6 pt-2 sm:px-6 md:hidden"
        >
          <ul className="divide-y divide-ink-200">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center justify-between py-4 text-base font-medium text-ink-800"
                >
                  {link.label}
                  <FontAwesomeIcon
                    icon={faArrowRight}
                    className="text-xs text-ink-400"
                    aria-hidden="true"
                  />
                </a>
              </li>
            ))}
          </ul>
          <Button as={Link} to="/login" className="mt-4 w-full">
            Acceder
          </Button>
        </div>
      )}
    </header>
  )
}

/**
 * Cómo funciona: tres pasos unidos por una línea que se dibuja al entrar en
 * pantalla, mientras cada número se rellena por turno.
 */
function Steps() {
  const [ref, revealed] = useReveal({ amount: 0.35 })

  return (
    <ol ref={ref} className="relative mt-10 grid gap-9 sm:grid-cols-3 sm:gap-8 lg:mt-14">
      {/* Línea que une los pasos: horizontal desde sm, vertical en móvil. */}
      <span
        aria-hidden="true"
        className="absolute bottom-6 left-6 top-6 w-px bg-ink-200 sm:bottom-auto sm:left-[calc((100%-4rem)/6)] sm:right-[calc((100%-4rem)/6)] sm:top-6 sm:h-px sm:w-auto"
      >
        <span
          className={cn(
            'block h-full w-full origin-top bg-blue-900 transition-transform duration-[1200ms] ease-out sm:origin-left',
            revealed ? 'scale-100' : 'scale-y-0 sm:scale-x-0 sm:scale-y-100',
          )}
        />
      </span>

      {STEPS.map((step, index) => (
        <li
          key={step.title}
          className="relative flex gap-5 sm:flex-col sm:items-center sm:text-center"
        >
          <span
            className={cn(
              'tabular relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border text-[0.9375rem] font-bold transition-[background-color,border-color,color] duration-500 ease-out',
              revealed
                ? 'border-blue-900 bg-blue-900 text-white'
                : 'border-ink-300 bg-ink-50 text-ink-500',
            )}
            style={{ transitionDelay: revealed ? `${250 + index * 350}ms` : '0ms' }}
          >
            {String(index + 1).padStart(2, '0')}
          </span>
          <div
            className={cn(
              'pt-1 transition-[opacity,transform] duration-700 ease-out sm:pt-0',
              revealed ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0',
            )}
            style={{ transitionDelay: `${300 + index * 350}ms` }}
          >
            <h3 className="text-lg font-bold tracking-[-0.01em] text-ink-900 sm:mt-5">
              {step.title}
            </h3>
            <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-600 sm:mx-auto sm:max-w-[30ch]">
              {step.body}
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}

/**
 * Vista previa del primer día: lo que el estudiante verá al entrar. Al llegar
 * a pantalla, el asistente "escribe" y responde una duda real del temario.
 */
function StudyPreview() {
  const [ref, revealed] = useReveal({ amount: 0.45 })
  const [answered, setAnswered] = useState(false)

  useEffect(() => {
    if (!revealed) return undefined
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const timer = setTimeout(() => setAnswered(true), reduce ? 0 : 1700)
    return () => clearTimeout(timer)
  }, [revealed])

  return (
    <div ref={ref} aria-hidden="true" className="relative space-y-3">
      <div className="rounded-xl bg-white p-4 shadow-e3 sm:p-5">
        <p className="eyebrow text-ink-400">Siguiente subtema</p>
        <p className="mt-2 font-bold leading-snug text-ink-900">
          Anatomía del globo ocular y estructuras anexas
        </p>
        <p className="mt-1 text-xs text-ink-500">Unidad 1 · 3 preguntas de repaso</p>
        <div className="mt-4 flex items-center gap-3">
          <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink-200">
            <span
              className="block h-full w-full origin-left rounded-full bg-blue-900 transition-transform duration-[1400ms] ease-out"
              style={{ transform: `scaleX(${revealed ? 1 / 7 : 0})`, transitionDelay: '300ms' }}
            />
          </span>
          <span className="tabular text-[0.6875rem] font-bold text-blue-900">1 de 7</span>
        </div>
      </div>

      <div
        className={cn(
          'ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-blue-700 px-4 py-2.5 text-[0.8125rem] leading-relaxed text-white transition-[opacity,transform] duration-500 ease-out',
          revealed ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0',
        )}
        style={{ transitionDelay: '500ms' }}
      >
        ¿Qué diferencia hay entre la esclera y la córnea?
      </div>

      <div
        className={cn(
          'flex items-start gap-2.5 transition-[opacity,transform] duration-500 ease-out',
          revealed ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0',
        )}
        style={{ transitionDelay: '900ms' }}
      >
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-[0.7rem] text-blue-900">
          <FontAwesomeIcon icon={faRobot} />
        </span>
        <div className="max-w-[88%] rounded-2xl rounded-bl-md bg-white/95 px-4 py-2.5 text-[0.8125rem] leading-relaxed text-ink-800">
          {answered ? (
            <span className="block animate-fade-in">
              Las dos forman la capa externa del ojo. La <strong>córnea</strong> es transparente y
              está delante; la <strong>esclera</strong> es blanca y opaca, y recubre el resto del
              globo.
            </span>
          ) : (
            <span className="flex h-5 items-center gap-1">
              {[0, 1, 2].map((dot) => (
                <span
                  key={dot}
                  className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400"
                  style={{ animationDelay: `${dot * 0.15}s` }}
                />
              ))}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const year = new Date().getFullYear()

  return (
    <div className="bg-ink-50">
      <LandingNav />

      {/* ── Portada: el vídeo es el protagonista ─────────────────────── */}
      <section
        id="inicio"
        className="relative flex min-h-[36rem] flex-col overflow-hidden sm:min-h-[42rem] lg:min-h-screen"
      >
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          aria-hidden="true"
          className="absolute inset-0 h-full w-full object-cover"
        >
          <source src="/videos/Modern_hospital_room_interior_202609061543.mp4" type="video/mp4" />
        </video>

        {/* Velo mínimo: se concentra detrás del texto y deja los bordes del
            vídeo casi limpios. */}
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-gradient-to-b from-ink-950/50 via-ink-950/20 to-ink-950/70"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[radial-gradient(60%_55%_at_50%_52%,rgb(14_14_13_/_0.62)_0%,rgb(14_14_13_/_0.34)_55%,transparent_100%)]"
        />

        <div className="relative z-10 mx-auto flex w-full max-w-[52rem] flex-1 flex-col items-center justify-center px-5 pb-16 pt-24 text-center sm:px-6 lg:pb-24">
          <p className="eyebrow animate-rise-in text-white/75">
            Plataforma académica de oftalmología
          </p>

          <h1
            className="animate-rise-in mt-5 text-[2rem] font-bold leading-[1.1] tracking-[-0.025em] text-white sm:text-[2.75rem] lg:text-[3.75rem] lg:leading-[1.05]"
            style={{ animationDelay: '80ms' }}
          >
            Estudia oftalmología e instrumentación quirúrgica con IA
          </h1>

          <p
            className="animate-rise-in mt-6 max-w-[50ch] text-[0.9375rem] leading-relaxed text-white/85 sm:text-[1.0625rem]"
            style={{ animationDelay: '160ms' }}
          >
            Contenido oficial en nueve unidades, repasos con explicación en cada pregunta y un
            asistente que responde sobre el temario de tu curso.
          </p>

          <div
            className="animate-rise-in mt-8 flex w-full flex-col items-center gap-3 sm:w-auto sm:flex-row lg:mt-10"
            style={{ animationDelay: '240ms' }}
          >
            <Button
              as={Link}
              to="/login"
              variant="inverse"
              size="lg"
              className="group/btn w-full sm:w-auto"
              iconRight={faArrowRight}
            >
              Empezar a estudiar
            </Button>
            <Button as="a" href="#temario" variant="outline" size="lg" className="w-full sm:w-auto">
              Ver el temario
            </Button>
          </div>

          {/* Ficha del temario: tres datos que se pueden contar, en una línea. */}
          <dl
            className="animate-rise-in mt-12 grid w-full max-w-md grid-cols-3 border-t border-white/25 pt-6 lg:mt-14"
            style={{ animationDelay: '320ms' }}
          >
            {FACTS.map((fact, index) => (
              <div
                key={fact.label}
                className={cn('px-2 text-center', index > 0 && 'border-l border-white/20')}
              >
                <dd className="tabular text-[1.5rem] font-bold leading-none text-white">
                  {fact.value}
                </dd>
                <dt className="mt-1.5 text-[0.75rem] font-medium text-white/70 sm:text-[0.8125rem]">
                  {fact.label}
                </dt>
              </div>
            ))}
          </dl>
        </div>

        {/* Indicador de scroll: un ratón con su rueda que baja. */}
        <a
          href="#temario"
          aria-label="Bajar al temario"
          className="absolute bottom-6 left-1/2 z-10 hidden -translate-x-1/2 sm:block"
        >
          <span className="flex h-9 w-6 justify-center rounded-full border-2 border-white/50 pt-2 transition-colors duration-200 hover:border-white">
            <span className="h-1.5 w-1 animate-scroll-cue rounded-full bg-white" />
          </span>
        </a>
      </section>

      {/* ── El temario: recorrido horizontal anclado ─────────────────── */}
      <div id="temario" className="scroll-mt-0">
        <Suspense fallback={<div className="h-[100svh] bg-white" />}>
          <Timeline
            eyebrow="El temario"
            title="Nueve unidades, de la anatomía al pterigión"
            intro="El mismo contenido para todos los cursos: una sola fuente académica, ordenada para que cada unidad se apoye en la anterior."
            imageUrl="/images/slideshow/slide-3.jpg"
            imageAlt="Equipo quirúrgico en torno al microscopio durante una intervención ocular"
            items={UNITS}
          />
        </Suspense>
      </div>

      {/* ── Sobre la plataforma ──────────────────────────────────────── */}
      <section id="plataforma" className="scroll-mt-16 py-16 lg:scroll-mt-20 lg:py-28">
        <div className="mx-auto grid max-w-[78rem] gap-12 px-5 sm:px-6 lg:grid-cols-12 lg:gap-16 lg:px-10">
          <div className="lg:col-span-5">
            <Reveal>
              <SectionTitle eyebrow="Sobre INSOFT">
                Estudiar cirugía ocular sin perderse en el camino
              </SectionTitle>
              <p className="mt-5 max-w-[46ch] text-[0.9375rem] leading-relaxed text-ink-600">
                Pensado para instrumentación quirúrgica: el orden del temario, el tiempo que lleva
                cada parte y la comprobación de que de verdad se ha entendido.
              </p>
            </Reveal>

            <ul className="mt-8 divide-y divide-ink-200 border-y border-ink-200">
              {FEATURES.map((feature, index) => (
                <Reveal
                  as="li"
                  key={feature.title}
                  delay={index * 90}
                  className="group flex gap-4 py-5"
                >
                  <span
                    aria-hidden="true"
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-soft-sky text-[0.9375rem] text-blue-900 transition-[background-color,color,transform] duration-300 ease-out group-hover:-rotate-6 group-hover:bg-blue-900 group-hover:text-white"
                  >
                    <FontAwesomeIcon icon={feature.icon} />
                  </span>
                  <div className="min-w-0">
                    <h3 className="text-base font-bold tracking-[-0.01em] text-ink-900">
                      {feature.title}
                    </h3>
                    <p className="mt-1 text-[0.875rem] leading-relaxed text-ink-600">
                      {feature.body}
                    </p>
                  </div>
                </Reveal>
              ))}
            </ul>
          </div>

          {/* Mosaico: una imagen protagonista y dos de apoyo. */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:col-span-7 lg:grid-rows-2">
            <Reveal className="group relative col-span-2 overflow-hidden rounded-xl sm:col-span-1 sm:row-span-2">
              <img
                src="/images/slideshow/slide-1.jpg"
                alt="Manos enguantadas aplicando instrumental sobre el globo ocular"
                loading="lazy"
                className="h-64 w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04] sm:absolute sm:inset-0 sm:h-full"
              />
              <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink-950/75 to-transparent p-5 pt-16">
                <span className="eyebrow text-white/70">Unidad 2</span>
                <span className="mt-1 block text-[0.9375rem] font-bold text-white">
                  Inyecciones intravítreas
                </span>
              </span>
            </Reveal>
            <Reveal delay={90} className="group relative overflow-hidden rounded-xl">
              <img
                src="/images/slideshow/slide-2.jpg"
                alt="Exploración de una paciente en la lámpara de hendidura"
                loading="lazy"
                className="aspect-[4/3] w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04] lg:absolute lg:inset-0 lg:aspect-auto lg:h-full"
              />
            </Reveal>
            <Reveal delay={180} className="group relative overflow-hidden rounded-xl">
              <img
                src="/images/slideshow/slide-4.jpg"
                alt="Hojas de bisturí oftálmico alineadas sobre el paño estéril"
                loading="lazy"
                className="aspect-[4/3] w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04] lg:absolute lg:inset-0 lg:aspect-auto lg:h-full"
              />
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── Cómo funciona ────────────────────────────────────────────── */}
      <section id="como-funciona" className="scroll-mt-16 bg-white py-16 lg:scroll-mt-20 lg:py-28">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal>
            <SectionTitle eyebrow="Cómo funciona">Tres pasos y ya estás estudiando</SectionTitle>
          </Reveal>
          <Steps />
        </div>
      </section>

      {/* ── Cierre: el primer día, concreto ──────────────────────────── */}
      <section className="py-16 lg:py-28">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal className="grid overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-e2 lg:grid-cols-2">
            <div className="flex flex-col justify-center px-6 py-10 sm:px-10 sm:py-14 lg:px-14">
              <p className="eyebrow text-blue-900">Tu primer día en INSOFT</p>
              <h2 className="mt-3 max-w-[18ch] text-[1.75rem] font-bold leading-[1.15] tracking-[-0.02em] text-ink-900 sm:text-[2.125rem] lg:text-[2.5rem]">
                Empieza por la anatomía del globo ocular
              </h2>
              <p className="mt-4 max-w-[44ch] text-[0.9375rem] leading-relaxed text-ink-600">
                El Curso General te espera con la unidad 1 lista para leer. Si algo no queda claro,
                el asistente está a una pregunta de distancia.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  as={Link}
                  to="/login"
                  size="lg"
                  className="group/btn w-full sm:w-auto"
                  iconRight={faArrowRight}
                >
                  Empezar a estudiar
                </Button>
                <Button
                  as="a"
                  href="#temario"
                  variant="ghost"
                  size="lg"
                  className="w-full sm:w-auto"
                >
                  Ver las nueve unidades
                </Button>
              </div>
              <p className="mt-5 text-xs text-ink-500">
                Entras con tu cuenta de Google. Solo te pediremos tu país y tu edad.
              </p>
            </div>

            <div className="relative overflow-hidden bg-blue-900 px-6 py-10 sm:px-10 sm:py-14 lg:px-12">
              <IrisMark className="-right-20 -top-20 h-80 w-80 text-white/[0.07]" />
              <div className="relative mx-auto max-w-sm">
                <StudyPreview />
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="border-t border-ink-200 bg-white">
        <div className="mx-auto grid max-w-[78rem] gap-10 px-5 py-12 sm:grid-cols-2 sm:px-6 lg:grid-cols-[2fr_1fr_1fr] lg:px-10">
          <div>
            <Logo size="md" />
            <p className="mt-4 max-w-[36ch] text-sm leading-relaxed text-ink-500">
              Sistema web de apoyo al aprendizaje de oftalmología para estudiantes de
              instrumentación quirúrgica.
            </p>
          </div>
          <div>
            <p className="eyebrow text-ink-400">Explora</p>
            <ul className="mt-4 space-y-2.5">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-ink-600 transition-colors duration-150 hover:text-blue-900"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="eyebrow text-ink-400">Tu cuenta</p>
            <ul className="mt-4 space-y-2.5">
              <li>
                <Link
                  to="/login"
                  className="text-sm text-ink-600 transition-colors duration-150 hover:text-blue-900"
                >
                  Acceder
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-ink-200">
          <p className="mx-auto max-w-[78rem] px-5 py-5 text-xs text-ink-400 sm:px-6 lg:px-10">
            © {year} INSOFT · Plataforma académica de oftalmología
          </p>
        </div>
      </footer>
    </div>
  )
}
