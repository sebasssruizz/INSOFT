export default function LessonVideo({ subtopicName }) {
  const name = subtopicName?.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  if (name !== 'drenaje de chalazion') return null

  return (
    <figure className="mt-6">
      <video
        controls
        playsInline
        preload="metadata"
        poster="/videos/drenaje-chalazion-poster.jpg"
        aria-label="Video educativo: drenaje de chalazión"
        className="aspect-video w-full rounded-xl bg-ink-950 object-contain"
      >
        <source src="/videos/drenaje-chalazion.mp4" type="video/mp4" />
        Tu navegador no puede reproducir este video.{' '}
        <a href="/videos/drenaje-chalazion.mp4">Abrir el video de chalazión</a>.
      </video>
      <figcaption className="mt-2 text-sm leading-relaxed text-ink-600">
        Visualización educativa generada con IA. Complementa la lectura del procedimiento.
      </figcaption>
    </figure>
  )
}
