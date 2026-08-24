import { useEffect, useState } from 'react'

/**
 * Carrusel de imágenes con transición de fundido suave.
 * Las fotos cambian poco a poco (cada `interval` ms) con un crossfade de 1s.
 */
export default function ImageCarousel({ images, interval = 6000, className = '', showCaptions = true }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (images.length < 2) return undefined
    const id = setInterval(() => setIndex((i) => (i + 1) % images.length), interval)
    return () => clearInterval(id)
  }, [images.length, interval])

  if (!images.length) return null

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {images.map((img, i) => (
        <img
          key={img.src}
          src={img.src}
          alt={img.alt}
          loading={i === 0 ? 'eager' : 'lazy'}
          className={`absolute inset-0 w-full h-full object-cover object-center transition-opacity duration-1000 ease-in-out ${
            i === index ? 'opacity-100' : 'opacity-0'
          }`}
        />
      ))}

      {/* Pie de foto */}
      {showCaptions && (
        <div className="absolute bottom-0 left-0 right-0 sm:right-auto sm:max-w-md bg-slate-900/60 backdrop-blur-sm px-4 py-2.5 sm:rounded-tr-xl">
          <p className="text-white text-sm font-medium truncate">{images[index].caption}</p>
        </div>
      )}

      {/* Indicadores */}
      <div className="absolute bottom-4 right-4 flex gap-1.5">
        {images.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            aria-label={`Ir a la imagen ${i + 1}`}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i === index ? 'w-5 bg-white' : 'w-1.5 bg-white/50 hover:bg-white/80'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
