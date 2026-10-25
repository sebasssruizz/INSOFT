import { cn } from '../lib/utils'

const SIZES = {
  sm: { mark: 26, text: 'text-lg' },
  md: { mark: 32, text: 'text-xl' },
  lg: { mark: 40, text: 'text-2xl' },
  xl: { mark: 52, text: 'text-3xl' },
}

/**
 * Marca INSOFT con el ojo PNG transparente aprobado por el usuario.
 * Las dos mitades del nombre conservan sus tonos de la escala azul.
 */
export default function Logo({ size = 'md', light = false, withText = true, className }) {
  const { mark, text } = SIZES[size] || SIZES.md

  return (
    <span className={cn('inline-flex items-center gap-2.5 select-none', className)}>
      <img
        src="/brand/ojo-insoft-20261024.png"
        width={mark}
        height={mark}
        alt=""
        aria-hidden="true"
        className="shrink-0 object-contain"
        style={{ width: mark, height: mark }}
      />

      {withText && (
        <span className={cn('font-display font-semibold tracking-[-0.015em]', text)}>
          <span className={light ? 'text-white' : 'text-ink-900'}>INS</span>
          <span className={light ? 'text-blue-300' : 'text-blue-700'}>OFT</span>
        </span>
      )}
    </span>
  )
}
