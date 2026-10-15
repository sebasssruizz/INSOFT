import { useLayoutEffect, useRef, useSyncExternalStore } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'

import { cn } from '../../lib/utils'

gsap.registerPlugin(ScrollTrigger, SplitText)
// En móvil la barra de direcciones cambia la altura al hacer scroll: sin esto
// cada cambio recalcularía el anclaje y la línea daría saltos.
ScrollTrigger.config({ ignoreMobileResize: true })

const REDUCED_MOTION = '(prefers-reduced-motion: reduce)'

function subscribeReducedMotion(callback) {
  const query = window.matchMedia(REDUCED_MOTION)
  query.addEventListener('change', callback)
  return () => query.removeEventListener('change', callback)
}

function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribeReducedMotion,
    () => window.matchMedia(REDUCED_MOTION).matches,
    () => false,
  )
}

/**
 * Hito del recorrido. Los pares quedan arriba de la línea y los impares abajo;
 * el tallo une el texto con su punto sobre la línea.
 */
function Milestone({ item, index, top }) {
  const text = (
    <div className={cn('pl-5 pr-2', top ? 'pb-5' : 'pt-5')}>
      <p data-label className="eyebrow flex items-center gap-2 text-blue-900">
        <span className="tabular">Unidad {String(index + 1).padStart(2, '0')}</span>
        {item.meta && (
          <span className="font-medium normal-case tracking-normal text-ink-400">
            · {item.meta}
          </span>
        )}
      </p>
      <h3
        data-split
        className="mt-2.5 text-[1.0625rem] font-bold leading-[1.25] tracking-[-0.01em] text-ink-900 sm:text-[1.1875rem] lg:text-[1.3125rem]"
      >
        {item.title}
      </h3>
      <p data-split className="mt-2 text-[0.875rem] leading-relaxed text-ink-600">
        {item.description}
      </p>
    </div>
  )

  const dot = (
    <span
      data-dot
      aria-hidden="true"
      className={cn(
        'relative z-10 block h-3.5 w-3.5 -translate-x-1/2 rounded-full bg-blue-900 ring-4 ring-white',
        top ? 'translate-y-1/2' : '-translate-y-1/2',
      )}
    />
  )

  const stem = (
    <span
      data-stem
      aria-hidden="true"
      className={cn('block w-px flex-1 bg-blue-900/40', top ? 'origin-bottom' : 'origin-top')}
    />
  )

  return (
    <li
      data-milestone
      className={cn('absolute flex h-1/2 flex-col', top ? 'top-0' : 'top-1/2')}
      style={{ left: `calc(var(--step) * ${index})`, width: 'var(--w)' }}
    >
      {top ? (
        <>
          {text}
          {stem}
          {dot}
        </>
      ) : (
        <>
          {dot}
          {stem}
          {text}
        </>
      )}
    </li>
  )
}

/**
 * Recorrido horizontal por hitos. Al llegar a la sección esta se ancla, la
 * pista se desplaza hacia la izquierda con el scroll y cada hito dibuja su
 * tallo y descubre su texto línea a línea al cruzar la pantalla.
 *
 * Con movimiento reducido no se ancla nada: la pista queda como un carrusel
 * que se desplaza con el dedo o la rueda, con todo el contenido visible.
 *
 * items: [{ id, title, description, meta? }]
 */
export default function Timeline({
  items = [],
  eyebrow,
  title,
  intro,
  imageUrl,
  imageAlt = '',
  className,
}) {
  const sectionRef = useRef(null)
  const trackRef = useRef(null)
  const lineRef = useRef(null)
  const barRef = useRef(null)
  const hintRef = useRef(null)
  const reducedMotion = usePrefersReducedMotion()

  useLayoutEffect(() => {
    if (reducedMotion) return undefined
    const section = sectionRef.current
    const track = trackRef.current
    if (!section || !track) return undefined

    const splits = []
    const ctx = gsap.context(() => {
      const distance = () => Math.max(1, track.scrollWidth - document.documentElement.clientWidth)

      // Posición horizontal de cada hito con la pista en reposo. Se mide antes
      // de crear el desplazamiento, que puede mover la pista al instante si la
      // página se abre ya a mitad de la sección.
      const rail = lineRef.current.parentElement
      const restingLeft = new Map(
        gsap.utils
          .toArray('[data-milestone]', section)
          .map((milestone) => [milestone, rail.offsetLeft + milestone.offsetLeft]),
      )

      // La línea se dibuja hasta el 75 % del ancho de la pantalla: su punta
      // acompaña a los hitos que van apareciendo. Se calcula en cada fotograma
      // del desplazamiento en vez de con un ScrollTrigger propio, porque la
      // pista ya es visible en reposo y un disparador que empieza antes del
      // desplazamiento nunca se actualiza con `containerAnimation`.
      const line = lineRef.current
      const drawLine = () => {
        const reach = window.innerWidth * 0.75 - rail.getBoundingClientRect().left
        gsap.set(line, { scaleX: gsap.utils.clamp(0, 1, reach / line.offsetWidth) })
      }

      const scrollTween = gsap.to(track, {
        x: () => -distance(),
        ease: 'none',
        onUpdate: drawLine,
        scrollTrigger: {
          onRefresh: drawLine,
          trigger: section,
          pin: true,
          start: 'top top',
          end: () => `+=${distance()}`,
          scrub: 0.6,
          invalidateOnRefresh: true,
          anticipatePin: 1,
          onUpdate: (self) => {
            if (barRef.current) gsap.set(barRef.current, { scaleX: self.progress })
            if (hintRef.current) {
              gsap.to(hintRef.current, {
                autoAlpha: self.progress > 0.04 ? 0 : 1,
                duration: 0.3,
                overwrite: true,
              })
            }
          },
        },
      })

      drawLine()

      restingLeft.forEach((left, milestone) => {
        // Los hitos que ya se ven antes de que la pista se mueva no pueden
        // esperar al desplazamiento horizontal: con `containerAnimation` no se
        // dispararían hasta empezar a anclar y se verían vacíos al llegar. Esos
        // se revelan cuando la sección entra en pantalla en vertical.
        const visibleAtRest = left < window.innerWidth * 0.82
        const trigger = visibleAtRest
          ? { trigger: section, start: 'top 55%', toggleActions: 'play none none reverse' }
          : {
              trigger: milestone,
              containerAnimation: scrollTween,
              start: 'left 82%',
              toggleActions: 'play none none reverse',
            }

        gsap
          .timeline({ scrollTrigger: trigger })
          .from(milestone.querySelector('[data-dot]'), {
            scale: 0,
            duration: 0.4,
            ease: 'expo.out',
          })
          .from(
            milestone.querySelector('[data-label]'),
            { autoAlpha: 0, x: -8, duration: 0.5, ease: 'power3.out' },
            '<0.05',
          )
          .from(
            milestone.querySelector('[data-stem]'),
            { scaleY: 0, duration: 0.6, ease: 'power3.out' },
            '<0.05',
          )

        // Cada texto se parte en líneas enmascaradas que suben desde abajo.
        // `autoSplit` vuelve a partir si cambia el ancho o cargan las fuentes,
        // y la animación devuelta por `onSplit` se rehace con él.
        milestone.querySelectorAll('[data-split]').forEach((element, order) => {
          splits.push(
            SplitText.create(element, {
              type: 'lines',
              mask: 'lines',
              autoSplit: true,
              onSplit: (self) =>
                gsap.from(self.lines, {
                  yPercent: 110,
                  duration: 0.75,
                  stagger: 0.07,
                  delay: 0.12 + order * 0.08,
                  ease: 'power3.out',
                  scrollTrigger: trigger,
                }),
            }),
          )
        })
      })
    }, section)

    return () => {
      splits.forEach((split) => split.revert())
      ctx.revert()
    }
  }, [reducedMotion, items.length])

  // --w: ancho de un hito. --step: distancia entre hitos consecutivos. Como
  // arriba y abajo se alternan, dos hitos del mismo lado quedan a 2·step y
  // nunca se pisan.
  const railStyle = {
    '--w': 'clamp(15rem, 23vw, 21rem)',
    '--step': 'calc(var(--w) * 0.64)',
    width: `calc(var(--step) * ${Math.max(0, items.length - 1)} + var(--w))`,
  }

  return (
    <section
      ref={sectionRef}
      aria-label={title}
      className={cn('relative overflow-hidden bg-white', className)}
    >
      <div
        className={cn('flex flex-col justify-center pt-16', reducedMotion ? 'py-16' : 'h-[100svh]')}
      >
        <div
          className={cn(
            reducedMotion && 'snap-x snap-mandatory overflow-x-auto overscroll-x-contain pb-6',
          )}
        >
          <div
            ref={trackRef}
            className="flex w-max items-center gap-[clamp(2.5rem,6vw,6rem)] pl-[max(1.25rem,calc((100vw-78rem)/2+2.5rem))] pr-[12vw] will-change-transform"
          >
            {/* Portada del recorrido: imagen, título y una línea de contexto. */}
            <header className="w-[min(80vw,24rem)] shrink-0 snap-start lg:w-[clamp(20rem,28vw,26rem)]">
              {imageUrl && (
                <div className="overflow-hidden rounded-xl">
                  <img
                    src={imageUrl}
                    alt={imageAlt}
                    draggable={false}
                    loading="lazy"
                    className="h-[clamp(9rem,26svh,16rem)] w-full object-cover"
                  />
                </div>
              )}
              {eyebrow && <p className="eyebrow mt-6 text-blue-900">{eyebrow}</p>}
              {title && (
                <h2 className="mt-3 text-[1.75rem] font-bold leading-[1.12] tracking-[-0.02em] text-ink-900 sm:text-[2.125rem] lg:text-[2.5rem]">
                  {title}
                </h2>
              )}
              {intro && (
                <p className="mt-4 max-w-[40ch] text-[0.9375rem] leading-relaxed text-ink-600">
                  {intro}
                </p>
              )}
            </header>

            <ol
              className="relative h-[clamp(24rem,60svh,34rem)] shrink-0 snap-start"
              style={railStyle}
            >
              {/* Pista gris de fondo y, encima, la línea que se dibuja. */}
              {/* La línea termina poco después del último hito, no al final
                  del ancho del texto de este. */}
              <span
                aria-hidden="true"
                className="absolute left-0 top-1/2 h-px bg-ink-200"
                style={{ right: 'calc(var(--w) - 3rem)' }}
              />
              <span
                ref={lineRef}
                aria-hidden="true"
                className="absolute left-0 top-1/2 h-px origin-left bg-blue-900"
                style={{ right: 'calc(var(--w) - 3rem)' }}
              />
              {items.map((item, index) => (
                <Milestone key={item.id} item={item} index={index} top={index % 2 === 0} />
              ))}
            </ol>
          </div>
        </div>

        {/* Pie del tramo anclado: invitación a desplazarse y barra de avance. */}
        {!reducedMotion && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 mx-auto flex max-w-[78rem] items-center gap-4 px-5 pb-6 sm:px-6 lg:px-10">
            <p
              ref={hintRef}
              className="flex shrink-0 items-center gap-2 text-xs font-medium text-ink-500"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-soft-ping rounded-full bg-blue-700" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-900" />
              </span>
              Sigue bajando para recorrer el temario
            </p>
            <span className="h-px flex-1 overflow-hidden bg-ink-200">
              <span
                ref={barRef}
                className="block h-full w-full origin-left scale-x-0 bg-blue-900"
              />
            </span>
          </div>
        )}
      </div>
    </section>
  )
}
