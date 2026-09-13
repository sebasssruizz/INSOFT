import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faCheck } from '@fortawesome/free-solid-svg-icons'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
import { Counter } from '../components/ui/Counter'
import { Doodle, DoodleField } from '../components/ui/Doodles'
import { CURRICULUM_FACTS, splitUnitName, unitIdentity } from '../lib/curriculum'
import { useReveal } from '../hooks/useReveal'
import { cn } from '../lib/utils'

const FACTS = [
  { value: CURRICULUM_FACTS.units, label: 'Unidades' },
  { value: CURRICULUM_FACTS.subtopics, label: 'Subtemas' },
  { value: CURRICULUM_FACTS.questions, label: 'Preguntas' },
  { value: CURRICULUM_FACTS.verified, label: 'Verificado', suffix: '%' },
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
    tint: 'sky',
  },
  {
    title: 'Estudia por unidades',
    body: 'Cada subtema trae su contenido, su tiempo estimado y un repaso al terminar.',
    tint: 'peach',
  },
  {
    title: 'Sigue tu avance',
    body: 'La barra del curso se llena según completas subtemas, dentro y fuera de la lección.',
    tint: 'rose',
  },
]

const TINT_SURFACE = {
  lavender: 'bg-soft-lavender',
  sky: 'bg-soft-sky',
  mint: 'bg-soft-mint',
  butter: 'bg-soft-butter',
  peach: 'bg-soft-peach',
  rose: 'bg-soft-rose',
}
const TINT_INK = {
  lavender: 'text-deep-lavender',
  sky: 'text-deep-sky',
  mint: 'text-deep-mint',
  butter: 'text-deep-butter',
  peach: 'text-deep-peach',
  rose: 'text-deep-rose',
}

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

/**
 * Título de sección con su trazo dibujado debajo. `align` decide de qué lado
 * arranca el trazo, para que acompañe al texto en vez de flotar suelto.
 */
function SectionTitle({ eyebrow, children, underlineClass = 'text-blue-300', align = 'center' }) {
  return (
    <>
      <p className="eyebrow text-blue-800">{eyebrow}</p>
      <h2 className="relative mt-4 inline-block text-[2rem] font-semibold leading-[1.14] tracking-[-0.02em] text-ink-900 lg:text-[2.75rem]">
        {children}
        <Doodle
          name="underline"
          size={132}
          className={cn(
            'absolute -bottom-3 h-4 w-[52%]',
            align === 'center' ? 'left-1/2 -translate-x-1/2' : 'left-0',
            underlineClass,
          )}
        />
      </h2>
    </>
  )
}

export default function LandingPage() {
  return (
    <div className="bg-ink-50">
      {/* ── Portada: el vídeo es el protagonista ─────────────────────── */}
      <section className="relative flex min-h-[44rem] flex-col overflow-hidden lg:min-h-screen">
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
          className="absolute inset-0 bg-gradient-to-b from-ink-950/40 via-ink-950/15 to-ink-950/65"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[radial-gradient(60%_55%_at_50%_52%,rgb(14_14_13_/_0.62)_0%,rgb(14_14_13_/_0.34)_55%,transparent_100%)]"
        />

        <header className="relative z-10 mx-auto flex h-24 w-full max-w-[78rem] items-center justify-between px-6 lg:px-10">
          <Logo light size="lg" />
          <Button as={Link} to="/login" variant="outline" size="sm">
            Acceder
          </Button>
        </header>

        <div className="relative z-10 mx-auto flex w-full max-w-[54rem] flex-1 flex-col items-center justify-center px-6 pb-20 text-center">
          <p className="eyebrow animate-rise-in text-white/80">
            Plataforma de aprendizaje de Oftalmología
          </p>

          <h1
            className="animate-rise-in mt-6 text-[2.75rem] font-semibold leading-[1.06] tracking-[-0.03em] text-white sm:text-[3.5rem] lg:text-[4.25rem]"
            style={{ animationDelay: '80ms' }}
          >
            Aprende <span className="italic text-blue-200">Oftalmología</span> con el contenido
            oficial
          </h1>

          <p
            className="animate-rise-in mt-7 max-w-[52ch] text-[1.0625rem] leading-relaxed text-white/85"
            style={{ animationDelay: '160ms' }}
          >
            Estudia temas verificados, únete a los cursos de tu facultad con un código y sigue tu
            progreso en cada subtema.
          </p>

          <div className="animate-rise-in mt-10" style={{ animationDelay: '240ms' }}>
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

          <dl
            className="animate-rise-in mt-16 grid w-full max-w-2xl grid-cols-2 gap-x-8 gap-y-8 border-t border-white/25 pt-9 sm:grid-cols-4"
            style={{ animationDelay: '320ms' }}
          >
            {FACTS.map((fact) => (
              <div key={fact.label}>
                <dt className="sr-only">{fact.label}</dt>
                <dd>
                  <span className="font-display text-[2.25rem] font-semibold leading-none tracking-[-0.02em] text-white lg:text-[2.75rem]">
                    <Counter to={fact.value} suffix={fact.suffix} />
                  </span>
                  <span className="mt-2.5 block text-[0.8125rem] font-medium text-white/70">
                    {fact.label}
                  </span>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ── El temario ───────────────────────────────────────────────── */}
      <section id="temario" className="relative overflow-hidden py-14 lg:py-20">
        <DoodleField
          items={[
            {
              name: 'eye',
              size: 74,
              rotate: -8,
              className: 'left-[3%] top-[9%] text-deep-lavender/40',
            },
            { name: 'snellen', size: 30, className: 'right-[7%] top-[7%] text-deep-butter/55' },
            {
              name: 'drop',
              size: 30,
              rotate: 12,
              className: 'left-[33%] top-[2%] text-deep-rose/40',
            },
            { name: 'iris', size: 52, className: 'right-[4%] top-[40%] text-deep-sky/35' },
            { name: 'lens', size: 46, className: 'left-[7%] bottom-[2%] text-deep-mint/40' },
            {
              name: 'scalpel',
              size: 40,
              rotate: -10,
              className: 'right-[9%] bottom-[2%] text-deep-peach/45',
            },
          ]}
        />

        <div className="relative mx-auto max-w-[78rem] px-6 lg:px-10">
          <Reveal className="mx-auto max-w-[46ch] text-center">
            <SectionTitle eyebrow="El temario" underlineClass="text-deep-lavender/50">
              Ocho unidades, de la anatomía a la oculoplastia
            </SectionTitle>
            <p className="mt-8 text-[1.0625rem] leading-relaxed text-ink-600">
              El mismo contenido para todos los cursos: una sola fuente académica que tu facultad no
              tiene que mantener por duplicado.
            </p>
          </Reveal>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {UNITS.map(([name, blurb], index) => {
              const { number, title } = splitUnitName(name)
              const identity = unitIdentity(index)
              return (
                <Reveal
                  key={name}
                  delay={index * 60}
                  className={cn(
                    'rounded-3xl p-7 transition-transform duration-300 ease-out hover:-translate-y-1.5',
                    identity.classes.soft,
                    // Alterna la altura para romper la rejilla perfecta.
                    index % 2 === 1 && 'lg:mt-12',
                  )}
                >
                  <span
                    className={cn(
                      'flex h-14 w-14 items-center justify-center rounded-2xl bg-white/70 text-xl',
                      identity.classes.text,
                    )}
                    aria-hidden="true"
                  >
                    <FontAwesomeIcon icon={identity.icon} />
                  </span>

                  <p
                    className={cn(
                      'tabular mt-6 text-xs font-bold uppercase tracking-[0.12em]',
                      identity.classes.text,
                    )}
                  >
                    Unidad {number}
                  </p>
                  <h3 className="mt-2 font-display text-[1.1875rem] font-semibold leading-snug text-ink-900">
                    {title}
                  </h3>
                  <p className="mt-3 text-[0.8125rem] leading-relaxed text-ink-600">{blurb}</p>
                </Reveal>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Sobre la plataforma: collage asimétrico ──────────────────── */}
      <section className="relative overflow-hidden bg-white py-14 lg:py-20">
        <DoodleField
          items={[
            {
              name: 'fundus',
              size: 66,
              rotate: -8,
              className: 'left-[5%] top-[14%] text-deep-mint/32',
            },
            { name: 'drop', size: 30, className: 'right-[8%] top-[12%] text-deep-rose/40' },
            { name: 'snellen', size: 26, className: 'left-[46%] top-[5%] text-deep-butter/45' },
            {
              name: 'forceps',
              size: 44,
              rotate: 14,
              className: 'right-[41%] bottom-[2%] text-deep-sky/38',
            },
            {
              name: 'glasses',
              size: 52,
              rotate: -8,
              className: 'left-[11%] bottom-[3%] text-deep-lavender/40',
            },
          ]}
        />

        <div className="relative mx-auto max-w-[78rem] px-6 lg:px-10">
          <Reveal className="mx-auto max-w-[46ch] text-center">
            <SectionTitle eyebrow="Sobre INSOFT" underlineClass="text-deep-mint/50">
              Estudiar cirugía ocular sin perderse en el camino
            </SectionTitle>
            <p className="mt-8 text-[1.0625rem] leading-relaxed text-ink-600">
              Pensado para instrumentación quirúrgica: el orden del temario, el tiempo que lleva
              cada parte y la comprobación de que de verdad se ha entendido.
            </p>
          </Reveal>

          {/* Collage: alturas y desplazamientos distintos a propósito. */}
          <div className="mt-12 grid grid-cols-2 items-end gap-4 sm:gap-6 lg:grid-cols-4">
            <Reveal className="lg:mb-14">
              <img
                src="/images/slideshow/slide-1.jpg"
                alt="Estudiantes de instrumentación quirúrgica en prácticas"
                loading="lazy"
                className="h-52 w-full rounded-3xl object-cover shadow-e2 sm:h-64"
              />
            </Reveal>
            <Reveal delay={90} className="lg:mt-10">
              <img
                src="/images/slideshow/slide-2.jpg"
                alt="Material e instrumental de quirófano"
                loading="lazy"
                className="h-64 w-full rounded-3xl object-cover shadow-e2 sm:h-80"
              />
            </Reveal>
            <Reveal delay={180} className="lg:mb-20">
              <img
                src="/images/slideshow/slide-3.jpg"
                alt="Microscopio quirúrgico oftalmológico"
                loading="lazy"
                className="h-56 w-full rounded-3xl object-cover shadow-e2 sm:h-72"
              />
            </Reveal>
            <Reveal delay={270} className="relative lg:mt-4">
              <img
                src="/images/slideshow/slide-4.jpg"
                alt="Equipo quirúrgico durante una intervención"
                loading="lazy"
                className="h-52 w-full rounded-3xl object-cover shadow-e2 sm:h-64"
              />
              <span className="absolute -left-5 -top-9 hidden rotate-[-6deg] rounded-full bg-blue-900 px-5 py-3.5 text-center font-display text-[0.9375rem] font-semibold leading-tight text-white shadow-e3 lg:block">
                Del temario
                <br />
                al quirófano
              </span>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── Cómo funciona ────────────────────────────────────────────── */}
      <section className="relative overflow-hidden py-14 lg:py-20">
        <DoodleField
          items={[
            { name: 'chart', size: 42, className: 'right-[6%] top-[16%] text-deep-peach/40' },
            {
              name: 'eye',
              size: 56,
              rotate: 6,
              className: 'left-[3%] bottom-[3%] text-deep-sky/35',
            },
            { name: 'lashes', size: 42, className: 'right-[30%] bottom-[3%] text-deep-rose/38' },
          ]}
        />

        <div className="relative mx-auto max-w-[78rem] px-6 lg:px-10">
          <Reveal>
            <SectionTitle eyebrow="Cómo funciona" underlineClass="text-deep-sky/50" align="left">
              Tres pasos y ya estás estudiando
            </SectionTitle>
          </Reveal>

          <div className="mt-12 grid gap-12 sm:grid-cols-3 lg:gap-16">
            {STEPS.map((step, index) => (
              <Reveal
                key={step.title}
                delay={index * 110}
                className={cn(index === 1 && 'sm:mt-16')}
              >
                <span
                  className={cn(
                    'tabular flex h-16 w-16 items-center justify-center rounded-2xl font-display text-2xl font-semibold',
                    TINT_SURFACE[step.tint],
                    TINT_INK[step.tint],
                  )}
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <h3 className="mt-6 text-xl font-semibold tracking-[-0.01em] text-ink-900">
                  {step.title}
                </h3>
                <p className="mt-3 max-w-[34ch] text-[0.9375rem] leading-relaxed text-ink-600">
                  {step.body}
                </p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Cierre ───────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden py-12 lg:py-16">
        <div className="relative mx-auto max-w-[78rem] px-6 lg:px-10">
          <Reveal className="relative overflow-hidden rounded-[2rem] bg-blue-900 px-8 py-14 lg:px-16 lg:py-20">
            <DoodleField
              items={[
                { name: 'iris', size: 54, className: 'right-[7%] top-[14%] text-white/20' },
                {
                  name: 'eye',
                  size: 60,
                  rotate: -6,
                  className: 'left-[2%] bottom-[3%] text-white/18',
                },
                { name: 'snellen', size: 26, className: 'right-[24%] bottom-[18%] text-white/22' },
              ]}
            />

            <div className="relative flex flex-wrap items-end justify-between gap-x-12 gap-y-10">
              <div>
                <h2 className="max-w-[18ch] text-[2rem] font-semibold leading-[1.14] tracking-[-0.02em] text-white lg:text-[2.75rem]">
                  Empieza por la unidad 1 hoy mismo
                </h2>
                <ul className="mt-9 space-y-3.5">
                  {[
                    'Acceso inmediato al Curso General',
                    'Repasos con explicación en cada pregunta',
                    'Tu progreso guardado subtema a subtema',
                  ].map((line) => (
                    <li
                      key={line}
                      className="flex items-center gap-3 text-[0.9375rem] text-blue-100"
                    >
                      <span
                        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/20 text-[0.5rem] text-white"
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
                className="group/btn"
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
        <p className="mt-3.5 text-xs text-ink-500">
          Sistema web de apoyo al aprendizaje de Oftalmología
        </p>
      </footer>
    </div>
  )
}
