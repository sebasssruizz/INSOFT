import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { sendFeedback } from '../services/feedbackService'
import { Button } from './ui/Button'

const TYPES = ['Petición', 'Queja', 'Reclamo', 'Sugerencia', 'Felicitación']
const CATEGORIES = [
  'Diseño y apariencia', 'Error o bug', 'Contenido educativo', 'Asistente de IA',
  'Rendimiento y velocidad', 'Cuenta e inicio de sesión', 'Otro',
]
const FIELD = 'mt-1 w-full rounded-lg border border-ink-300 bg-white p-2.5 text-base'

export default function FeedbackWidget() {
  const { user } = useAuth()
  const { pathname } = useLocation()
  const dialog = useRef(null)
  const trigger = useRef(null)
  const firstOption = useRef(null)
  const submitting = useRef(false)
  const [open, setOpen] = useState(false)
  const [option, setOption] = useState('comment')
  const [tipo, setTipo] = useState('')
  const [categoria, setCategoria] = useState('')
  const [comentario, setComentario] = useState('')
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [confirmation, setConfirmation] = useState('')

  useEffect(() => {
    if (!open) return
    const modal = dialog.current
    modal.showModal()
    firstOption.current.focus()
    return () => {
      modal.close()
      trigger.current?.focus()
    }
  }, [open])

  async function submit(event) {
    event.preventDefault()
    if (submitting.current) return
    const validation = {}
    if (!TYPES.includes(tipo)) validation.tipo = 'Selecciona un tipo.'
    if (!CATEGORIES.includes(categoria)) validation.categoria = 'Selecciona una categoría.'
    const text = comentario.trim()
    if (text.length < 10 || text.length > 1000) {
      validation.comentario = 'Escribe entre 10 y 1000 caracteres.'
    }
    setErrors(validation)
    setError('')
    if (Object.keys(validation).length) return
    submitting.current = true
    setSending(true)
    try {
      await sendFeedback({ tipo, categoria, comentario: text, pagina: pathname })
      setTipo('')
      setCategoria('')
      setComentario('')
      setConfirmation('Comentario enviado. Gracias por compartir tu opinión.')
      setOpen(false)
    } catch (failure) {
      setError(failure.status === 429
        ? 'Has enviado varios comentarios. Inténtalo en un minuto.'
        : 'No se pudo enviar el comentario. Inténtalo de nuevo.')
    } finally {
      submitting.current = false
      setSending(false)
    }
  }

  if (!user) return null

  return (
    <>
      {confirmation && (
        <div role="status" className="fixed bottom-20 left-4 z-40 flex max-w-[calc(100vw-2rem)] items-center gap-2 rounded-xl border border-ink-200 bg-white p-3 text-sm text-ink-800 shadow-e3 sm:max-w-sm">
          <p>{confirmation}</p>
          <button type="button" onClick={() => setConfirmation('')} aria-label="Cerrar confirmación" className="min-h-11 min-w-11">×</button>
        </div>
      )}
      <div className="fixed bottom-[max(1.25rem,env(safe-area-inset-bottom))] left-4 z-40 sm:left-6 lg:left-[18rem]">
      <Button
        ref={trigger}
        className="shadow-e3"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => {
          setConfirmation('')
          setOption('comment')
          setOpen(true)
        }}
      >
        Comentarios / PQRS
      </Button>
      </div>
      <dialog
        ref={dialog}
        aria-labelledby="feedback-title"
        onCancel={(event) => {
          event.preventDefault()
          setOpen(false)
        }}
        onClose={() => setOpen(false)}
        className="m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-lg overflow-y-auto rounded-xl border border-ink-200 bg-white p-5 text-ink-900 shadow-e4 backdrop:bg-ink-950/40"
      >
        <div className="flex items-center justify-between gap-3">
          <h2 id="feedback-title" className="text-xl font-semibold">Comentarios (PQRS)</h2>
          <Button type="button" variant="ghost" size="icon" className="min-h-11 min-w-11" onClick={() => setOpen(false)} aria-label="Cerrar comentarios">×</Button>
        </div>
        <div className="my-5 flex flex-wrap gap-2" role="group" aria-label="Opciones de comentarios">
          <Button ref={firstOption} type="button" variant={option === 'comment' ? 'primary' : 'secondary'} aria-pressed={option === 'comment'} onClick={() => setOption('comment')}>Agregar comentario</Button>
          <Button type="button" variant={option === 'rating' ? 'primary' : 'secondary'} aria-pressed={option === 'rating'} onClick={() => setOption('rating')}>Evaluar página</Button>
        </div>
        {option === 'rating' ? (
          <div className="space-y-4 pb-2">
            <h3 className="text-lg font-semibold">Cuéntanos cómo fue usar INSOFT</h3>
            <p className="text-sm leading-relaxed text-ink-600">Diez preguntas sobre navegación, claridad y ayuda. Puedes marcar lo que todavía no has probado y revisar todo antes de enviarlo.</p>
            <Button as={Link} to="/feedback/evaluation" state={{ sourcePage: pathname === '/feedback/evaluation' ? '/dashboard' : pathname }} onClick={() => setOpen(false)} className="w-full">Comenzar evaluación</Button>
          </div>
        ) : (
          <form onSubmit={submit} noValidate className="space-y-4">
            <div>
              <label htmlFor="feedback-type" className="text-sm font-medium">Tipo</label>
              <select id="feedback-type" required value={tipo} onChange={(event) => setTipo(event.target.value)} aria-invalid={!!errors.tipo} aria-describedby={errors.tipo ? 'feedback-type-error' : undefined} className={FIELD}>
                <option value="">Selecciona un tipo</option>
                {TYPES.map((value) => <option key={value}>{value}</option>)}
              </select>
              {errors.tipo && <p id="feedback-type-error" className="mt-1 text-sm text-wrong-700">{errors.tipo}</p>}
            </div>
            <div>
              <label htmlFor="feedback-category" className="text-sm font-medium">Categoría</label>
              <select id="feedback-category" required value={categoria} onChange={(event) => setCategoria(event.target.value)} aria-invalid={!!errors.categoria} aria-describedby={errors.categoria ? 'feedback-category-error' : undefined} className={FIELD}>
                <option value="">Selecciona una categoría</option>
                {CATEGORIES.map((value) => <option key={value}>{value}</option>)}
              </select>
              {errors.categoria && <p id="feedback-category-error" className="mt-1 text-sm text-wrong-700">{errors.categoria}</p>}
            </div>
            <div>
              <label htmlFor="feedback-comment" className="text-sm font-medium">Comentario</label>
              <textarea id="feedback-comment" required minLength={10} maxLength={1000} rows={5} value={comentario} onChange={(event) => setComentario(event.target.value)} aria-invalid={!!errors.comentario} aria-describedby={`feedback-count${errors.comentario ? ' feedback-comment-error' : ''}`} className={FIELD} />
              <p id="feedback-count" className="tabular text-right text-xs text-ink-500">{comentario.length}/1000</p>
              {errors.comentario && <p id="feedback-comment-error" className="mt-1 text-sm text-wrong-700">{errors.comentario}</p>}
            </div>
            <p className="text-xs leading-relaxed text-ink-600">Se guarda con tu cuenta para que el equipo revise tu opinión. No incluyas datos de pacientes, contraseñas ni claves.</p>
            <p className="break-all text-xs text-ink-600">Página actual: {pathname}</p>
            {error && <p role="alert" className="text-sm text-wrong-700">{error}</p>}
            <Button type="submit" disabled={sending} aria-busy={sending} className="w-full">{sending ? 'Enviando…' : 'Enviar comentario'}</Button>
          </form>
        )}
      </dialog>
    </>
  )
}
