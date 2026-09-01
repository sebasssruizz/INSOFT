import { useEffect, useRef, useState } from 'react'

/**
 * Mide el tamaño de un elemento y se actualiza cuando cambia (ResizeObserver).
 * Devuelve [ref, { width, height }]. Sustituye a `useMeasure` de
 * @uidotdev/usehooks para no añadir esa dependencia.
 */
export function useMeasure() {
  const ref = useRef(null)
  const [rect, setRect] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const el = ref.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(([entry]) => {
      // border-box: incluye padding (necesario para medir pistas con padding lateral)
      let width
      let height
      if (entry.borderBoxSize && entry.borderBoxSize.length) {
        width = entry.borderBoxSize[0].inlineSize
        height = entry.borderBoxSize[0].blockSize
      } else {
        const r = entry.target.getBoundingClientRect()
        width = r.width
        height = r.height
      }
      setRect((prev) => (prev.width === width && prev.height === height ? prev : { width, height }))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return [ref, rect]
}
