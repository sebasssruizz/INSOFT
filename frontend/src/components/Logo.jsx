import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faEye } from '@fortawesome/free-solid-svg-icons'

/**
 * Logo de INSOFT con diferenciador de color:
 *  INS (Instrumentación Quirúrgica) en verde · OFT (Oftalmología) en rojo
 */
export default function Logo({ size = 'text-xl', withIcon = true, light = false }) {
  const iconSize =
    size === 'text-4xl' ? 'w-12 h-12 text-xl' : size === 'text-2xl' ? 'w-10 h-10 text-base' : 'w-8 h-8 text-sm'
  return (
    <span className="inline-flex items-center gap-2 select-none">
      {withIcon && (
        <span
          className={`${iconSize} rounded-xl bg-ins-600 text-white flex items-center justify-center shadow-md ${
            light ? 'shadow-black/30' : 'shadow-oft-200'
          }`}
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={faEye} />
        </span>
      )}
      <span className={`font-extrabold tracking-tight ${size}`}>
        <span className={light ? 'text-ins-300' : 'text-ins-600'}>INS</span>
        <span className={light ? 'text-oft-300' : 'text-oft-600'}>OFT</span>
      </span>
    </span>
  )
}
