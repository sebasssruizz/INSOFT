import { useId } from 'react'

import { cn } from '../../lib/utils'

// En SVG, `transform-origin` se mide contra el lienzo entero salvo que se pida
// la caja del propio elemento: sin esto el ojo parpadearía desde una esquina.
const OWN_BOX = { transformBox: 'fill-box', transformOrigin: 'center' }

const ALMOND = 'M4 24C10.8 13.4 18.6 8 28 8s17.2 5.4 24 16c-6.8 10.6-14.6 16-24 16S10.8 34.6 4 24Z'

/**
 * Cargador de la plataforma: un ojo que parpadea mientras el iris recorre el
 * campo visual. Habla del tema de la página, no de "cargando" en abstracto.
 * Con movimiento reducido queda quieto y abierto, y el texto sigue diciendo
 * qué está pasando.
 */
export function EyeLoader({ size = 56, label = 'Cargando', tone = 'blue', className }) {
  const stroke = tone === 'inverse' ? 'stroke-white' : 'stroke-blue-900'
  const iris = tone === 'inverse' ? 'fill-blue-300' : 'fill-blue-700'
  const pupil = tone === 'inverse' ? 'fill-blue-950' : 'fill-ink-950'
  // useId devuelve ":r1:"; los dos puntos rompen la referencia url(#…).
  const clipId = `eye-loader-${useId().replace(/:/g, '')}`

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('inline-flex flex-col items-center gap-3', className)}
    >
      <svg
        width={size}
        height={(size * 48) / 56}
        viewBox="0 0 56 48"
        fill="none"
        aria-hidden="true"
        className="overflow-visible"
      >
        <defs>
          <clipPath id={clipId}>
            <path d={ALMOND} />
          </clipPath>
        </defs>

        <g className="animate-blink" style={OWN_BOX}>
          <g clipPath={`url(#${clipId})`}>
            <g className="animate-iris-scan" style={OWN_BOX}>
              <circle cx="28" cy="24" r="9.5" className={iris} />
              <circle
                cx="28"
                cy="24"
                r="4.2"
                className={cn('animate-pupil', pupil)}
                style={OWN_BOX}
              />
              <circle cx="31" cy="20.6" r="1.7" className="fill-white" />
            </g>
          </g>
          <path d={ALMOND} className={stroke} strokeWidth="2.6" strokeLinejoin="round" />
        </g>
      </svg>

      {label && (
        <span
          className={cn(
            'text-[0.8125rem] font-medium',
            tone === 'inverse' ? 'text-blue-100' : 'text-ink-500',
          )}
        >
          {label}
          <span className="inline-block w-4 text-left" aria-hidden="true">
            …
          </span>
        </span>
      )}
    </div>
  )
}

/** Cargador centrado en su contenedor, para pantallas y secciones enteras. */
export function PageLoader({ label = 'Preparando tu espacio de estudio', className }) {
  return (
    <div
      className={cn(
        'flex min-h-[50vh] w-full animate-fade-in items-center justify-center px-6',
        className,
      )}
    >
      <EyeLoader label={label} />
    </div>
  )
}

/**
 * Versión mínima para dentro de los botones: un iris abierto que gira con la
 * pupila fija en el centro. Hereda el color del texto del botón.
 */
export function IrisSpinner({ className }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
      className={cn('h-[1.05em] w-[1.05em] shrink-0', className)}
    >
      <circle
        cx="10"
        cy="10"
        r="7.5"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="2.2"
      />
      <path
        d="M10 2.5a7.5 7.5 0 0 1 7.5 7.5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        className="animate-spin-iris"
        style={{ transformBox: 'view-box', transformOrigin: '10px 10px' }}
      />
      <circle cx="10" cy="10" r="2.4" fill="currentColor" />
    </svg>
  )
}
