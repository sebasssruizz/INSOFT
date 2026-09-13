import { cn } from '../lib/utils'

const SIZES = {
  sm: { mark: 26, text: 'text-lg' },
  md: { mark: 32, text: 'text-xl' },
  lg: { mark: 40, text: 'text-2xl' },
  xl: { mark: 52, text: 'text-3xl' },
}

/**
 * Marca INSOFT. El ojo está dibujado a medida (almendra + iris + reflejo) en
 * lugar de un icono genérico, y las dos mitades del nombre se distinguen por
 * profundidad de tono dentro de la misma escala azul.
 */
export default function Logo({ size = 'md', light = false, withText = true, className }) {
  const { mark, text } = SIZES[size] || SIZES.md

  return (
    <span className={cn('inline-flex items-center gap-2.5 select-none', className)}>
      <svg
        width={mark}
        height={mark}
        viewBox="0 0 40 40"
        fill="none"
        aria-hidden="true"
        className="shrink-0"
      >
        <rect width="40" height="40" rx="11" className={light ? 'fill-white' : 'fill-blue-700'} />
        <path
          d="M8 20c3.4-5.4 7.4-8.1 12-8.1S28.6 14.6 32 20c-3.4 5.4-7.4 8.1-12 8.1S11.4 25.4 8 20Z"
          className={light ? 'fill-blue-700' : 'fill-white'}
          fillOpacity={light ? 0.16 : 0.22}
        />
        <path
          d="M8 20c3.4-5.4 7.4-8.1 12-8.1S28.6 14.6 32 20c-3.4 5.4-7.4 8.1-12 8.1S11.4 25.4 8 20Z"
          className={light ? 'stroke-blue-700' : 'stroke-white'}
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <circle cx="20" cy="20" r="4.4" className={light ? 'fill-blue-700' : 'fill-white'} />
        <circle cx="21.7" cy="18.3" r="1.35" className={light ? 'fill-white' : 'fill-blue-700'} />
      </svg>

      {withText && (
        <span className={cn('font-display font-semibold tracking-[-0.015em]', text)}>
          <span className={light ? 'text-white' : 'text-ink-900'}>INS</span>
          <span className={light ? 'text-blue-300' : 'text-blue-700'}>OFT</span>
        </span>
      )}
    </span>
  )
}
