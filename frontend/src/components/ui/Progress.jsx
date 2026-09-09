import { cn } from '../../lib/utils'

const clamp = (value) => Math.min(100, Math.max(0, Number(value) || 0))

const TRACK_HEIGHT = {
  sm: 'h-1',
  md: 'h-1.5',
  lg: 'h-2.5',
}

/**
 * Barra de progreso. Se anima con `scaleX`, no con `width`, para no provocar
 * reflow en cada fotograma mientras el estudiante avanza por el curso.
 */
export function ProgressBar({ value, size = 'md', tone = 'blue', className, label }) {
  const percentage = clamp(value)

  return (
    <div className={className}>
      {label && (
        <div className="mb-1.5 flex items-baseline justify-between gap-3">
          <span className="text-xs font-medium text-ink-500">{label}</span>
          <span className="tabular text-xs font-bold text-blue-900">{Math.round(percentage)}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={Math.round(percentage)}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn(
          'w-full overflow-hidden rounded-full',
          TRACK_HEIGHT[size],
          tone === 'inverse' ? 'bg-white/20' : 'bg-ink-200',
        )}
      >
        <div
          className={cn(
            'h-full w-full origin-left rounded-full transition-transform duration-700 ease-out',
            tone === 'inverse' ? 'bg-white' : 'bg-blue-900',
          )}
          style={{ transform: `scaleX(${percentage / 100})` }}
        />
      </div>
    </div>
  )
}

/**
 * Anillo de progreso para cifras compactas (cabecera de curso, tarjetas).
 */
export function ProgressRing({ value, size = 56, stroke = 5, className, children, tone = 'blue' }) {
  const percentage = clamp(value)
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          className={tone === 'inverse' ? 'stroke-white/20' : 'stroke-ink-200'}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - (percentage / 100) * circumference}
          className={cn(
            'transition-[stroke-dashoffset] duration-700 ease-out',
            tone === 'inverse' ? 'stroke-white' : 'stroke-blue-900',
          )}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center">
        {children ?? (
          <span
            className={cn(
              'tabular text-xs font-bold',
              tone === 'inverse' ? 'text-white' : 'text-blue-900',
            )}
          >
            {Math.round(percentage)}%
          </span>
        )}
      </span>
    </div>
  )
}
