import { cn } from '../../lib/utils'

/**
 * Trazos decorativos dibujados a mano que se reparten por el fondo de la
 * portada. Todos salen del mundo oftalmológico —ojos, iris, fondo de ojo,
 * óptica, optotipos, instrumental—: el adorno habla del tema de la página, no
 * de decoración genérica. Son puramente ornamentales: van siempre con
 * `aria-hidden` y `pointer-events-none`, nunca transportan información.
 */
const SHAPES = {
  // Ojo almendrado con iris y pupila.
  eye: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 15c6-8.4 12.6-12.6 20-12.6S36 6.6 42 15c-6 8.4-12.6 12.6-20 12.6S8 23.4 2 15Z" />
      <circle cx="22" cy="15" r="6.6" />
      <circle cx="22" cy="15" r="2.2" fill="currentColor" stroke="none" />
    </g>
  ),
  // Iris con sus estrías radiales.
  iris: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round">
      <circle cx="18" cy="18" r="15" />
      <circle cx="18" cy="18" r="5.4" />
      <path d="M18 3v5.2M18 27.8V33M3 18h5.2M27.8 18H33M7.4 7.4l3.7 3.7M24.9 24.9l3.7 3.7M28.6 7.4l-3.7 3.7M11.1 24.9l-3.7 3.7" />
    </g>
  ),
  // Fondo de ojo: papila y vasos saliendo hacia la periferia.
  fundus: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round">
      <circle cx="18" cy="18" r="15" />
      <circle cx="18" cy="18" r="4" />
      <path d="M21.6 15.4c3.6-2.8 7.4-3.8 11.4-3M21.6 20.6c3.6 2.8 7.4 3.8 11.4 3M14.4 14.6c-3.6-2-6.4-4.8-8.4-8.2M14.4 21.4c-3.6 2-6.4 4.8-8.4 8.2" />
    </g>
  ),
  // Ojo cerrado con pestañas.
  lashes: (
    <g fill="none" strokeWidth="2.4" strokeLinecap="round">
      <path d="M2 7c6 7.2 12 10.8 18 10.8S32 14.2 38 7" />
      <path d="M8.4 15.6 6 20.4M15.4 18.2 14.4 23.4M24.6 18.2l1 5.2M31.6 15.6 34 20.4" />
    </g>
  ),
  // Gafas: dos aros, puente y patillas.
  glasses: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="8" />
      <circle cx="36" cy="12" r="8" />
      <path d="M20.2 10.6c2.4-1.6 5.2-1.6 7.6 0" />
      <path d="M4.6 7.4 2 2.6M43.4 7.4 46 2.6" />
    </g>
  ),
  // Optotipo de Snellen: la E que rota.
  snellen: (
    <g fill="none" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 3v28" />
      <path d="M6 3h19M6 17h14M6 31h19" />
    </g>
  ),
  // Cartel de agudeza visual, con las líneas cada vez más pequeñas.
  chart: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="24" height="30" rx="3.5" />
      <path d="M9.5 10.5h11M11 17h8M12.5 23h5M14 28.5h2" />
    </g>
  ),
  // Gota de colirio.
  drop: (
    <path
      d="M12 2.5c6 8 9 12.6 9 17a9 9 0 0 1-18 0c0-4.4 3-9 9-17Z"
      fill="none"
      strokeWidth="2.4"
      strokeLinejoin="round"
    />
  ),
  // Lente biconvexa: los rayos entran paralelos y convergen en el foco.
  lens: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 3c6 4.6 6 19.4 0 24-6-4.6-6-19.4 0-24Z" />
      <path d="M2 7h9.4M2 15h11M2 23h9.4" />
      <path d="m19.6 9 11.4 5.6M19.6 21 31 15.4" />
    </g>
  ),
  // Bisturí de hoja fina.
  scalpel: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.6 16.4C18 10.8 23 6.6 29.6 4.6 28 11.4 24.6 16.6 19.6 20.4l-5-4Z" />
      <path d="M13.4 17.6 3 28" />
    </g>
  ),
  // Pinzas de microcirugía, con las puntas juntas.
  forceps: (
    <g fill="none" strokeWidth="2.2" strokeLinecap="round">
      <path d="M8 3c-1.6 10-1.4 20 3.9 28M16 3c1.6 10 1.4 20-3.9 28" />
      <path d="M8.4 5h7.2" />
    </g>
  ),
  // Subrayado a mano, para acompañar titulares.
  underline: <path d="M2 12c22-9 62-13 106-7" fill="none" strokeWidth="3" strokeLinecap="round" />,
}

const VIEWBOX = {
  eye: '0 0 44 30',
  iris: '0 0 36 36',
  fundus: '0 0 36 36',
  lashes: '0 0 40 26',
  glasses: '0 0 48 22',
  snellen: '0 0 30 34',
  chart: '0 0 30 36',
  drop: '0 0 24 32',
  lens: '0 0 34 30',
  scalpel: '0 0 34 32',
  forceps: '0 0 24 34',
  underline: '0 0 110 16',
}

export function Doodle({ name, className, size = 36, rotate = 0 }) {
  const shape = SHAPES[name]
  if (!shape) return null

  return (
    <svg
      viewBox={VIEWBOX[name]}
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      aria-hidden="true"
      className={cn('pointer-events-none select-none', className)}
      style={rotate ? { transform: `rotate(${rotate}deg)` } : undefined}
    >
      {shape}
    </svg>
  )
}

/**
 * Reparte trazos por el fondo de una sección. Las posiciones se pasan a mano
 * y a propósito: la asimetría es la gracia, una rejilla regular la destruiría.
 *
 * Solo se usa en la portada: dentro de la aplicación las pantallas van limpias.
 * Y solo a partir de `lg`: por debajo no queda margen libre donde ponerlos sin
 * cruzarse con el contenido, así que desaparecen en vez de estorbar.
 *
 * items: [{ name, className, size, rotate }]
 */
export function DoodleField({ items = [], className }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'pointer-events-none absolute inset-0 hidden overflow-hidden lg:block',
        className,
      )}
    >
      {items.map((item, index) => (
        <Doodle
          key={`${item.name}-${index}`}
          name={item.name}
          size={item.size}
          rotate={item.rotate}
          className={cn('absolute', item.className)}
        />
      ))}
    </div>
  )
}
