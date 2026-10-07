import { useEffect, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faHourglassHalf } from '@fortawesome/free-solid-svg-icons'

/**
 * Aviso amable cuando la API tarda más de 5 s (el plan gratis de Render
 * duerme el servidor y hay que esperar a que despierte). Escucha los
 * eventos 'insoft:api-slow' / 'insoft:api-slow-end' que emite api.js.
 */
export default function SlowServerBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const on = () => setVisible(true)
    const off = () => setVisible(false)
    window.addEventListener('insoft:api-slow', on)
    window.addEventListener('insoft:api-slow-end', off)
    return () => {
      window.removeEventListener('insoft:api-slow', on)
      window.removeEventListener('insoft:api-slow-end', off)
    }
  }, [])

  if (!visible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-4 left-1/2 z-[60] flex -translate-x-1/2 items-center gap-2.5 rounded-2xl border border-ink-200 bg-white px-4 py-2.5 text-sm font-medium text-ink-700 shadow-e3"
    >
      <FontAwesomeIcon icon={faHourglassHalf} spin className="text-blue-800" aria-hidden="true" />
      El servidor se está despertando, un momento…
    </div>
  )
}
