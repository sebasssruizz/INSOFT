/** Ojo animado en CSS puro para la página principal. */
export default function AnimatedEye() {
  return (
    <div className="animate-float-soft">
      <div className="animated-eye" role="img" aria-label="Ojo animado de INSOFT">
        <div className="animated-eye-iris">
          <div className="animated-eye-pupil" />
          <div className="animated-eye-shine" />
        </div>
      </div>
    </div>
  )
}
