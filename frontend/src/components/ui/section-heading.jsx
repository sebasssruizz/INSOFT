import { motion, useReducedMotion } from 'motion/react'

import { cn } from '../../lib/utils'

const EASE = [0.16, 1, 0.3, 1]

const ACCENT = {
  ins: { light: 'text-ins-600', dark: 'text-ins-400', rule: 'bg-ins-500' },
  oft: { light: 'text-oft-500', dark: 'text-oft-300', rule: 'bg-oft-500' },
}

/**
 * Título de sección con dos rasgos de marca:
 *  - una regla corta de color que se dibuja al entrar en pantalla
 *  - la última letra (más la puntuación final) en color de acento,
 *    alternando INS (verde) / OFT (azul) sección a sección.
 *
 * accent: 'ins' | 'oft'   ·   tone: 'light' | 'dark'
 */
export function SectionHeading({
  children,
  accent = 'ins',
  tone = 'light',
  eyebrow,
  className,
  headingClassName,
}) {
  const reduce = useReducedMotion()
  const text = String(children)

  // Índice de la última letra/dígito: coloreamos desde ahí hasta el final
  // (así "¿Cómo funciona?" colorea "a?").
  const match = text.match(/[\p{L}\p{N}](?=[^\p{L}\p{N}]*$)/u)
  const cut = match ? match.index : Math.max(text.length - 1, 0)
  const head = text.slice(0, cut)
  const tail = text.slice(cut)

  const colors = ACCENT[accent] || ACCENT.ins

  return (
    <div className={className}>
      <motion.span
        aria-hidden="true"
        className={cn('block h-1.5 w-12 rounded-full', colors.rule)}
        style={{ transformOrigin: 'left' }}
        initial={reduce ? false : { scaleX: 0, opacity: 0 }}
        whileInView={{ scaleX: 1, opacity: 1 }}
        viewport={{ once: true, amount: 0.8 }}
        transition={{ duration: 0.5, ease: EASE }}
      />
      {eyebrow && (
        <p
          className={cn(
            'mt-4 text-sm font-semibold',
            tone === 'dark' ? 'text-slate-400' : 'text-slate-500',
          )}
        >
          {eyebrow}
        </p>
      )}
      <h2
        className={cn(
          'mt-3 text-3xl font-extrabold leading-[1.1] tracking-tight md:text-4xl lg:text-[2.6rem]',
          tone === 'dark' ? 'text-white' : 'text-slate-900',
          headingClassName,
        )}
      >
        {head}
        <span className={tone === 'dark' ? colors.dark : colors.light}>{tail}</span>
      </h2>
    </div>
  )
}
