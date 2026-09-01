import * as React from 'react'
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react'

import { useMeasure } from '../../hooks/useMeasure'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import { cn } from '../../lib/utils'
import { SectionHeading } from './section-heading'

/*
 * "¿Cómo funciona?" — timeline horizontal ligada al scroll.
 * Adaptado a JSX a partir del bloque original "process-timeline"
 * (sin "use client", sin TypeScript, sin `cva`, sin @uidotdev/usehooks ni alias @/).
 *
 * El título y las tarjetas viven en el MISMO marco fijo (sticky), así que la
 * sección se mantiene compacta: mientras haces scroll dentro de ella, el marco
 * queda pinchado y solo se desplazan las tarjetas en horizontal.
 * En móvil o con `prefers-reduced-motion` cae a una lista vertical.
 */

function PhaseCard({ index, phase, tone = 'dark' }) {
  const accentText = index % 2 === 0 ? 'text-ins-400' : 'text-oft-300'
  return (
    <li
      className={cn(
        'flex w-[78vw] shrink-0 flex-col gap-4 rounded-2xl border p-6 sm:w-[23rem] lg:w-[30rem] lg:p-8',
        tone === 'dark'
          ? 'border-white/10 bg-white/[0.04]'
          : 'border-slate-200 bg-white shadow-sm',
      )}
    >
      <span className={cn('text-4xl font-extrabold tabular-nums', accentText)}>
        {String(index + 1).padStart(2, '0')}
      </span>
      <h3
        className={cn(
          'text-xl font-bold leading-snug lg:text-2xl',
          tone === 'dark' ? 'text-white' : 'text-slate-900',
        )}
      >
        {phase.title}
      </h3>
      <p
        className={cn(
          'text-sm leading-relaxed lg:text-[0.95rem]',
          tone === 'dark' ? 'text-slate-300' : 'text-slate-500',
        )}
      >
        {phase.description}
      </p>
    </li>
  )
}

export function ProcessTimeline({ phases, title, intro, className }) {
  const reduceMotion = useReducedMotion()
  const isDesktop = useMediaQuery('(min-width: 768px)')
  const animate = isDesktop && !reduceMotion

  const sectionRef = React.useRef(null)
  const [frameRef, frame] = useMeasure()
  const [trackRef, track] = useMeasure()

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end end'],
  })

  // La pista mide con border-box (incluye el padding lateral), así el
  // desplazamiento deja la última tarjeta completamente dentro del marco.
  const distance = Math.max(track.width - frame.width + 32, 0)
  const x = useTransform(scrollYProgress, [0.06, 0.92], [0, -distance])

  const header = (
    <SectionHeading accent="oft" tone="dark" className="max-w-2xl">
      {title}
    </SectionHeading>
  )

  if (!animate) {
    return (
      <div className={cn('mx-auto max-w-3xl px-6 py-16 lg:py-20', className)}>
        {header}
        {intro && <p className="mt-4 text-lg text-slate-300">{intro}</p>}
        <ol className="mt-8 grid gap-4">
          {phases.map((phase, index) => (
            <PhaseCard key={phase.id} index={index} phase={phase} tone="dark" />
          ))}
        </ol>
      </div>
    )
  }

  return (
    <div ref={sectionRef} className={cn('relative h-[225vh]', className)}>
      <div
        ref={frameRef}
        className="sticky top-0 flex h-[100dvh] flex-col justify-center gap-7 overflow-hidden py-12"
      >
        <div className="mx-auto w-full max-w-6xl px-6">
          {header}
          {intro && (
            <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-300">{intro}</p>
          )}
        </div>

        <motion.ol
          ref={trackRef}
          style={{ x }}
          className="flex w-max gap-8 px-[max(1.5rem,calc((100vw-72rem)/2))] lg:gap-14"
        >
          {phases.map((phase, index) => (
            <PhaseCard key={phase.id} index={index} phase={phase} tone="dark" />
          ))}
        </motion.ol>

        <div className="mx-auto w-full max-w-6xl px-6">
          <div className="h-1 w-full overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full origin-left rounded-full bg-gradient-to-r from-ins-400 to-oft-400"
              style={{ scaleX: scrollYProgress }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
