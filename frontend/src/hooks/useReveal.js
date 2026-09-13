import { useEffect, useRef, useState } from 'react'

/**
 * Revela un elemento cuando entra en pantalla.
 *
 * Arranca en visible si el navegador no soporta IntersectionObserver: el
 * contenido nunca debe quedar oculto porque falle la animación.
 */
export function useReveal({ amount = 0.35 } = {}) {
  const ref = useRef(null)
  const [revealed, setRevealed] = useState(() => typeof IntersectionObserver === 'undefined')

  useEffect(() => {
    const element = ref.current
    if (!element || revealed) return undefined

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setRevealed(true)
          observer.disconnect()
        }
      },
      { threshold: amount },
    )
    observer.observe(element)
    return () => observer.disconnect()
  }, [amount, revealed])

  return [ref, revealed]
}
