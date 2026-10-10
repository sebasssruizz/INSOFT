import { cn } from '../../lib/utils'

/**
 * Iris en línea fina para el fondo de superficies de color: anillos, pupila y
 * estrías. Siempre decorativo y muy tenue; toma el color del texto, así que se
 * controla con `text-white/[0.07]` o similar.
 */
export function IrisMark({ className }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 200 200"
      fill="none"
      stroke="currentColor"
      className={cn('pointer-events-none absolute', className)}
    >
      <circle cx="100" cy="100" r="96" strokeWidth="2" />
      <circle cx="100" cy="100" r="68" strokeWidth="2" />
      <circle cx="100" cy="100" r="30" fill="currentColor" stroke="none" />
      <path
        d="M100 4v36M100 160v36M4 100h36M160 100h36M32 32l25 25M143 143l25 25M168 32l-25 25M57 143l-25 25"
        strokeWidth="2"
      />
    </svg>
  )
}
