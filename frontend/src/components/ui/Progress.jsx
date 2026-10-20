import { useEffect, useRef, useState } from 'react'

import { cn } from '../../lib/utils'

const clamp = (value) => Math.min(100, Math.max(0, Number(value) || 0))

/**
 * Devuelve 0 en el primer fotograma y el valor real en el siguiente, para que
 * la transición CSS llene la barra desde cero al aparecer en vez de saltar
 * directamente a su estado final. Los cambios posteriores se animan igual.
 */
function useFillFromZero(value) {
  const [shown, setShown] = useState(0)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(value))
    return () => cancelAnimationFrame(frame)
  }, [value])
  return shown
}

const EASE_OUT_EXPO = (t) => (t === 1 ? 1 : 1 - 2 ** (-10 * t))

/** La cifra acompaña al relleno: se desliza del valor anterior al nuevo. */
function useTweenedNumber(value, duration = 700) {
  const [shown, setShown] = useState(0)
  const from = useRef(0)

  useEffect(() => {
    const start = from.current
    from.current = value
    if (start === value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setShown(value)
      return undefined
    }
    const begin = performance.now()
    let frame = requestAnimationFrame(function step(now) {
      const t = Math.min(1, (now - begin) / duration)
      setShown(Math.round(start + (value - start) * EASE_OUT_EXPO(t)))
      if (t < 1) frame = requestAnimationFrame(step)
    })
    const safety = setTimeout(() => setShown(value), duration + 300)
    return () => {
      cancelAnimationFrame(frame)
      clearTimeout(safety)
    }
  }, [value, duration])

  return shown
}

const TRACK_HEIGHT = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
}

/**
 * Barra de progreso. Se anima con `scaleX`, no con `width`, para no provocar
 * reflow en cada fotograma mientras el estudiante avanza por el curso.
 *
 * Mientras está a medias lleva un brillo que avanza, la cifra se desliza al
 * cambiar y la pista se engrosa un poco al pasar el cursor.
 */
export function ProgressBar({
  value,
  size = 'md',
  tone = 'blue',
  className,
  label,
  showValue = false,
  ariaLabel,
}) {
  const percentage = clamp(value)
  const fill = useFillFromZero(percentage)
  const shown = useTweenedNumber(Math.round(percentage))
  const inProgress = percentage > 0 && percentage < 100
  const inverse = tone === 'inverse'

  const valueText = (
    <span className={cn('tabular text-xs font-bold', inverse ? 'text-white' : 'text-blue-900')}>
      {shown}%
    </span>
  )

  return (
    <div className={cn('group/bar', className)}>
      {label && (
        <div className="mb-1.5 flex items-baseline justify-between gap-3">
          <span className="text-xs font-medium text-ink-500">{label}</span>
          {valueText}
        </div>
      )}
      <div className="flex items-center gap-3">
        <div
          role="progressbar"
          aria-label={ariaLabel}
          aria-valuenow={Math.round(percentage)}
          aria-valuemin={0}
          aria-valuemax={100}
          className={cn(
            'relative w-full overflow-hidden rounded-full transition-transform duration-200 ease-out group-hover/bar:scale-y-125',
            TRACK_HEIGHT[size],
            inverse ? 'bg-white/20' : 'bg-ink-200',
          )}
        >
          <div
            className="absolute inset-0 origin-left transition-transform duration-700 ease-out"
            style={{ transform: `scaleX(${fill / 100})` }}
          >
            <div
              className={cn(
                'relative h-full w-full overflow-hidden rounded-full',
                inverse ? 'bg-white' : 'bg-gradient-to-r from-blue-800 to-blue-900',
              )}
            >
              {inProgress && (
                <span
                  aria-hidden="true"
                  className={cn(
                    'absolute inset-y-0 left-0 w-1/3 animate-sheen bg-gradient-to-r from-transparent to-transparent',
                    inverse ? 'via-blue-200/60' : 'via-white/45',
                  )}
                />
              )}
            </div>
          </div>
        </div>
        {showValue && !label && valueText}
      </div>
    </div>
  )
}

/**
 * Anillo de progreso para cifras compactas (cabecera de curso, tarjetas).
 */
export function ProgressRing({ value, size = 56, stroke = 5, className, children, tone = 'blue' }) {
  const percentage = clamp(value)
  const fill = useFillFromZero(percentage)
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
          strokeDashoffset={circumference - (fill / 100) * circumference}
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
