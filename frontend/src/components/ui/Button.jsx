import { forwardRef } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'

import { cn } from '../../lib/utils'

const BASE =
  'relative inline-flex select-none items-center justify-center gap-2 rounded-xl font-sans font-semibold ' +
  'transition-[background-color,color,box-shadow,transform,border-color] duration-150 ease-out ' +
  'active:translate-y-px disabled:pointer-events-none disabled:opacity-45'

const VARIANTS = {
  // Acción principal de la pantalla. Solo una por vista.
  primary:
    'bg-blue-900 text-white shadow-e2 hover:bg-blue-800 hover:shadow-blue-glow active:bg-blue-950',
  // Acción secundaria sobre superficie clara.
  secondary:
    'border border-ink-200 bg-white text-ink-800 shadow-e1 hover:border-blue-300 hover:bg-soft-sky hover:text-blue-900 active:bg-blue-100',
  // Acción sobre fondos profundos (portada, cabeceras oscuras).
  inverse: 'bg-white text-blue-950 shadow-e2 hover:bg-soft-sky active:bg-blue-100',
  outline:
    'border border-white/30 bg-white/5 text-white backdrop-blur-sm hover:border-white/60 hover:bg-white/15',
  // Sin peso visual: navegación, cancelar, acciones terciarias.
  ghost: 'text-ink-600 hover:bg-ink-100 hover:text-ink-900 active:bg-ink-200',
  danger: 'bg-wrong-500 text-white shadow-e2 hover:bg-wrong-700 active:bg-wrong-700',
}

const SIZES = {
  sm: 'h-9 px-3.5 text-[0.8125rem]',
  md: 'h-11 px-5 text-sm',
  lg: 'h-[3.25rem] px-7 text-[0.9375rem]',
  icon: 'h-10 w-10',
}

/**
 * Botón único de toda la aplicación. Cubre los siete estados: reposo, hover,
 * foco, activo, deshabilitado, cargando y con icono.
 *
 * `as` permite renderizar un Link de react-router conservando la apariencia.
 */
export const Button = forwardRef(function Button(
  {
    as: Component = 'button',
    variant = 'primary',
    size = 'md',
    icon,
    iconRight,
    loading = false,
    disabled,
    className,
    children,
    ...props
  },
  ref,
) {
  const isDisabled = disabled || loading

  return (
    <Component
      ref={ref}
      className={cn(BASE, VARIANTS[variant], SIZES[size], className)}
      disabled={Component === 'button' ? isDisabled : undefined}
      aria-disabled={Component === 'button' ? undefined : isDisabled || undefined}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? (
        <FontAwesomeIcon icon={faSpinner} className="animate-spin" aria-hidden="true" />
      ) : (
        icon && <FontAwesomeIcon icon={icon} aria-hidden="true" />
      )}
      {children}
      {iconRight && !loading && (
        <FontAwesomeIcon
          icon={iconRight}
          aria-hidden="true"
          className="transition-transform duration-200 ease-out group-hover/btn:translate-x-0.5"
        />
      )}
    </Component>
  )
})
