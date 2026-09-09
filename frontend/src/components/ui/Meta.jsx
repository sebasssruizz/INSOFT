import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

import { cn } from '../../lib/utils'

/** Dato breve con icono: "8 subtemas", "1 h 12 min", "21 preguntas". */
export function Meta({ icon, children, className }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-xs text-ink-500', className)}>
      {icon && (
        <FontAwesomeIcon icon={icon} className="text-[0.7rem] text-ink-400" aria-hidden="true" />
      )}
      <span className="tabular">{children}</span>
    </span>
  )
}

const BADGE_TONES = {
  official: 'bg-blue-100 text-blue-900 ring-1 ring-inset ring-blue-200',
  done: 'bg-correct-50 text-correct-700 ring-1 ring-inset ring-correct-200',
  progress: 'bg-blue-700 text-white',
  quiet: 'bg-ink-100 text-ink-600 ring-1 ring-inset ring-ink-200',
  inverse: 'bg-white/15 text-white ring-1 ring-inset ring-white/25',
}

export function Badge({ tone = 'quiet', icon, children, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-sans text-[0.6875rem] font-bold uppercase tracking-[0.08em]',
        BADGE_TONES[tone],
        className,
      )}
    >
      {icon && <FontAwesomeIcon icon={icon} className="text-[0.7rem]" aria-hidden="true" />}
      {children}
    </span>
  )
}
