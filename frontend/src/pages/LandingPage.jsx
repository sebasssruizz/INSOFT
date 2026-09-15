import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck } from '@fortawesome/free-solid-svg-icons'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
import { CURRICULUM_FACTS, splitUnitName } from '../lib/curriculum'
import { useReveal } from '../hooks/useReveal'
import { cn } from '../lib/utils'

// Cifras del temario, sin porcentajes inventados: solo lo que se puede contar.
const FACTS = [
  { value: CURRICULUM_FACTS.units, label: 'unidades' },
  { value: CURRICULUM_FACTS.subtopics, label: 'subtemas' },
  { value: CURRICULUM_FACTS.questions, label: 'preguntas' },
]

const UNITS = [
  [
    'UNIDAD 1. Generalidades en Cirugía Oftalmológica',
    'Anatomía, anestesia, instrumental y protocolos',
  ],
  ['UNIDAD 2. Procedimientos generales', 'Pterigión, chalazión, vías lagrimales, intravítreas'],
  ['UNIDAD 3. Glaucoma', 'Trabeculotomía, implantes de drenaje y láser'],
  ['UNIDAD 4. Segmento anterior', 'Facoemulsificación, extracapsular y córnea'],
  ['UNIDAD 5. Cirugías vitreorretinales', 'Vitrectomía anterior y posterior, retina'],
  ['UNIDAD 6. Corrección de estrabismo', 'Músculos extraoculares y suturas ajustables'],
  ['UNIDAD 7. Patologías refractivas', 'Miopía, hipermetropía y astigmatismo'],
  ['UNIDAD 8. Oculoplastia', 'Cirugía palpebral y cuidados perioculares'],
]

const STEPS = [
  {
    title: 'Entra con tu cuenta',
    body: 'Accedes con Google y el Curso General de Oftalmología aparece listo, sin configurar nada.',
  },
  {
    title: 'Estudia por unidades',
    body: 'Cada subtema trae su contenido, su tiempo estimado y un repaso al terminar.',
  },
  {
    title: 'Pregunta y avanza',
    body: 'El asistente responde sobre el temario y tu progreso se guarda subtema a subtema.',
  },
]

function Reveal({ children, delay = 0, className, as: Component = 'div' }) {
  const [ref, revealed] = useReveal({ amount: 0.25 })
  return (
    <Component
      ref={ref}
      className={cn(
        'transition-[opacity,transform] duration-700 ease-out',
        revealed ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0',
        className,
      )}
      style={{ transitionDelay: `${delay}ms` }}
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

export default function LandingPage() {
  return (
    <div className="bg-ink-50">
      {/* ── Portada: el vídeo es el protagonista ─────────────────────── */}
      <section className="relative flex min-h-[34rem] flex-col overflow-hidden sm:min-h-[40rem] lg:min-h-screen">
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
          className="absolute inset-0 bg-gradient-to-b from-ink-950/45 via-ink-950/20 to-ink-950/70"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[radial-gradient(60%_55%_at_50%_52%,rgb(14_14_13_/_0.62)_0%,rgb(14_14_13_/_0.34)_55%,transparent_100%)]"
        />

        <header className="relative z-10 mx-auto flex h-20 w-full max-w-[78rem] items-center justify-between px-5 sm:px-6 lg:h-24 lg:px-10">
          <Logo light size="md" className="lg:hidden" />
          <Logo light size="lg" className="hidden lg:inline-flex" />
          <Button as={Link} to="/login" variant="outline" size="sm">
            Acceder
          </Button>
        </header>

        <div className="relative z-10 mx-auto flex w-full max-w-[52rem] flex-1 flex-col items-center justify-center px-5 pb-14 text-center sm:px-6 lg:pb-20">
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
            Contenido oficial en ocho unidades, repasos con explicación en cada pregunta y un
            asistente que responde sobre el temario de tu curso.
          </p>

          <div className="animate-rise-in mt-8 lg:mt-10" style={{ animationDelay: '240ms' }}>
            <Button
              as={Link}
              to="/login"
              variant="inverse"
              size="lg"
              className="group/btn"
              iconRight={faArrowRight}
            >
              Acceder
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
                className={cn(
                  'px-2 text-center',
                  index > 0 && 'border-l border-white/20',
                )}
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
      </section>

      {/* ── El temario ───────────────────────────────────────────────── */}
      <section id="temario" className="py-14 lg:py-24">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal className="lg:flex lg:items-end lg:justify-between lg:gap-16">
            <SectionTitle eyebrow="El temario">
              Ocho unidades, de la anatomía a la oculoplastia
            </SectionTitle>
            <p className="mt-5 max-w-[46ch] text-[0.9375rem] leading-relaxed text-ink-600 lg:mt-0 lg:shrink-0 lg:pb-1">
              El mismo contenido para todos los cursos: una sola fuente académica que tu facultad
              no tiene que mantener por duplicado.
            </p>
          </Reveal>

          {/* Rejilla reglada: las celdas se separan por línea fina, no por
              tarjetas sueltas. Es un plan de estudios, no un escaparate. */}
          <Reveal className="mt-10 grid gap-px overflow-hidden rounded-lg border border-ink-200 bg-ink-200 sm:grid-cols-2 lg:mt-12 lg:grid-cols-4">
            {UNITS.map(([name, blurb], index) => {
              const { number, title } = splitUnitName(name)
              return (
                <div key={name} className="bg-white p-5 sm:p-6">
                  <p className="tabular text-xs font-bold tracking-[0.1em] text-ink-400">
                    {String(number ?? index + 1).padStart(2, '0')}
                  </p>
                  <h3 className="mt-3 text-base font-bold leading-snug tracking-[-0.01em] text-ink-900">
                    {title}
                  </h3>
                  <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-600">{blurb}</p>
                </div>
              )
            })}
          </Reveal>
        </div>
      </section>

      {/* ── Sobre la plataforma ──────────────────────────────────────── */}
      <section className="bg-white py-14 lg:py-24">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal className="lg:flex lg:items-end lg:justify-between lg:gap-16">
            <SectionTitle eyebrow="Sobre INSOFT">
              Estudiar cirugía ocular sin perderse en el camino
            </SectionTitle>
            <p className="mt-5 max-w-[46ch] text-[0.9375rem] leading-relaxed text-ink-600 lg:mt-0 lg:shrink-0 lg:pb-1">
              Pensado para instrumentación quirúrgica: el orden del temario, el tiempo que lleva
              cada parte y la comprobación de que de verdad se ha entendido.
            </p>
          </Reveal>

          <div className="mt-10 grid grid-cols-2 gap-3 sm:gap-4 lg:mt-12 lg:grid-cols-4">
            {[
              ['slide-1.jpg', 'Manos enguantadas aplicando instrumental sobre el globo ocular'],
              ['slide-2.jpg', 'Exploración de una paciente en la lámpara de hendidura'],
              ['slide-3.jpg', 'Equipo quirúrgico en torno al microscopio durante una intervención'],
              ['slide-4.jpg', 'Hojas de bisturí oftálmico alineadas sobre el paño estéril'],
            ].map(([file, alt], index) => (
              <Reveal key={file} delay={index * 80}>
                <img
                  src={`/images/slideshow/${file}`}
                  alt={alt}
                  loading="lazy"
                  className="aspect-[4/5] w-full rounded-lg object-cover"
                />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Cómo funciona ────────────────────────────────────────────── */}
      <section className="py-14 lg:py-24">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal>
            <SectionTitle eyebrow="Cómo funciona">Tres pasos y ya estás estudiando</SectionTitle>
          </Reveal>

          <div className="mt-10 grid gap-8 sm:grid-cols-3 sm:gap-8 lg:mt-14 lg:gap-12">
            {STEPS.map((step, index) => (
              <Reveal
                key={step.title}
                delay={index * 110}
                className="border-t border-ink-200 pt-5"
              >
                <span className="tabular text-[0.8125rem] font-bold tracking-[0.1em] text-blue-900">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <h3 className="mt-3 text-lg font-bold tracking-[-0.01em] text-ink-900">
                  {step.title}
                </h3>
                <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-600">{step.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Cierre ───────────────────────────────────────────────────── */}
      <section className="pb-14 lg:pb-24">
        <div className="mx-auto max-w-[78rem] px-5 sm:px-6 lg:px-10">
          <Reveal className="rounded-xl bg-blue-900 px-6 py-10 sm:px-10 sm:py-14 lg:px-14 lg:py-16">
            <div className="flex flex-col gap-y-9 lg:flex-row lg:items-end lg:justify-between lg:gap-x-12">
              <div className="min-w-0">
                <h2 className="max-w-[18ch] text-[1.75rem] font-bold leading-[1.15] tracking-[-0.02em] text-white sm:text-[2.125rem] lg:text-[2.5rem]">
                  Empieza por la unidad 1 hoy mismo
                </h2>
                <ul className="mt-7 space-y-3">
                  {[
                    'Acceso inmediato al Curso General',
                    'Repasos con explicación en cada pregunta',
                    'Tu progreso guardado subtema a subtema',
                  ].map((line) => (
                    <li
                      key={line}
                      className="flex items-start gap-3 text-[0.9375rem] leading-snug text-blue-100"
                    >
                      <span
                        className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white/20 text-[0.45rem] text-white"
                        aria-hidden="true"
                      >
                        <FontAwesomeIcon icon={faCheck} />
                      </span>
                      {line}
                    </li>
                  ))}
                </ul>
              </div>

              <Button
                as={Link}
                to="/login"
                variant="inverse"
                size="lg"
                className="group/btn w-full shrink-0 sm:w-auto"
                iconRight={faArrowRight}
              >
                Acceder
              </Button>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="border-t border-ink-200 py-10 text-center">
        <Logo size="sm" className="justify-center" />
        <p className="mt-3.5 px-5 text-xs text-ink-500">
          Sistema web de apoyo al aprendizaje de Oftalmología
        </p>
      </footer>
    </div>
  )
}
