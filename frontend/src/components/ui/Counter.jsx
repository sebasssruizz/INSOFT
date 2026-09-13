import { useEffect, useRef, useState } from 'react'

const EASE_OUT_EXPO = (t) => (t === 1 ? 1 : 1 - 2 ** (-10 * t))

/**
 * Cifra que cuenta hasta su valor al entrar en pantalla.
 *
 * Si la pestaña está en segundo plano el navegador congela
 * `requestAnimationFrame`: un temporizador de seguridad fija entonces el valor
 * final, de modo que la cifra jamás se queda clavada en cero.
 */
export function Counter({ to = 0, duration = 1500, suffix = '', className }) {
  const ref = useRef(null)
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const element = ref.current
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (reduce || typeof IntersectionObserver === 'undefined') {
      setDisplay(to)
      return undefined
    }

    let frame = null
    let safety = null

    const run = () => {
      const start = performance.now()
      const step = (now) => {
        const progress = Math.min(1, (now - start) / duration)
        setDisplay(Math.round(EASE_OUT_EXPO(progress) * to))
        if (progress < 1) frame = requestAnimationFrame(step)
      }
      frame = requestAnimationFrame(step)
      safety = setTimeout(() => setDisplay(to), duration + 400)
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return
        observer.disconnect()
        run()
      },
      { threshold: 0.4 },
    )

    if (element) observer.observe(element)

    return () => {
      observer.disconnect()
      if (frame) cancelAnimationFrame(frame)
      if (safety) clearTimeout(safety)
    }
  }, [to, duration])

  return (
    <span ref={ref} className={className}>
      <span className="tabular">{display}</span>
      {suffix}
    </span>
  )
}
