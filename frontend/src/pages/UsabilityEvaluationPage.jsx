import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { HEURISTICS, RATING_OPTIONS, SURVEY_VERSION, ratingLabel } from '../lib/usabilitySurvey'
import { sendEvaluation } from '../services/feedbackService'

export default function UsabilityEvaluationPage() {
  const location = useLocation()
  const [sourcePage] = useState(() => {
    const path = location.state?.sourcePage
    return typeof path === 'string' && /^\/(?!\/)/.test(path) && !/[?#\\\r\n]/.test(path)
      ? path : '/dashboard'
  })
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [device, setDevice] = useState('No indicado')
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [receipt, setReceipt] = useState(null)
  const [consent, setConsent] = useState(false)
  const [submissionId] = useState(() => crypto.randomUUID())
  const submitting = useRef(false)
  const heading = useRef(null)
  const review = step === 5
  const visible = HEURISTICS.slice(step * 2, step * 2 + 2)
  const completed = Object.keys(answers).length

  useEffect(() => { heading.current?.focus() }, [step, receipt])

  function next(event) {
    event.preventDefault()
    if (visible.some(({ id }) => answers[id] === undefined)) {
      setError('Selecciona una respuesta para cada frase. Puedes marcar «No lo he probado».')
      return
    }
    setError('')
    setStep((value) => value + 1)
  }

  async function submit(event) {
    event.preventDefault()
    if (submitting.current) return
    if (!consent) {
      setError('Confirma que deseas compartir esta evaluación con el equipo de INSOFT.')
      return
    }
    if (!Object.values(answers).some((value) => typeof value === 'number')) {
      setError('Valora al menos una experiencia que hayas probado. Puedes volver a las preguntas o evaluar después de usar la plataforma.')
      return
    }
    submitting.current = true
    setSending(true)
    setError('')
    try {
      const result = await sendEvaluation({
        submission_id: submissionId, version: SURVEY_VERSION, pagina: sourcePage,
        respuestas: Object.fromEntries(HEURISTICS.map(({ id }) => [id, answers[id] === 'na' ? null : answers[id]])),
        dispositivo: device, comentario: comment.trim(),
      })
      setReceipt(result.id)
    } catch (failure) {
      setError(failure.status === 429
        ? 'Has enviado varias evaluaciones. Espera un minuto y vuelve a intentarlo.'
        : 'No se pudo enviar. Tus respuestas siguen aquí; revisa tu conexión y vuelve a intentarlo.')
    } finally {
      submitting.current = false
      setSending(false)
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 pb-28 pt-6 sm:px-8 sm:pt-10">
      <Link to={sourcePage} className="inline-flex min-h-11 items-center text-sm font-medium text-blue-800 underline underline-offset-4">Volver al estudio</Link>
      <h1 ref={heading} tabIndex={-1} className="mt-5 text-2xl font-semibold tracking-tight focus:outline-none sm:text-3xl">
        {receipt ? 'Gracias por ayudarnos a mejorar' : 'Tu experiencia con INSOFT'}
      </h1>
      {receipt ? (
        <div role="status" className="mt-6 space-y-4">
          <p>Tu evaluación quedó guardada con el número {receipt}. El equipo podrá revisarla junto con las demás opiniones.</p>
          <Button as={Link} to={sourcePage}>Volver al estudio</Button>
        </div>
      ) : (
        <>
          <p className="mt-3 max-w-prose leading-relaxed text-ink-600">Piensa en lo que ya usaste: contenido, prácticas, modelos 3D y Sofía. Indica cuánto estás de acuerdo con cada frase. Si no probaste algo, puedes indicarlo.</p>
          <p className="mt-3 text-sm leading-relaxed text-ink-600">Es voluntaria y no afecta tus notas. Se guarda vinculada a tu cuenta para mejorar la plataforma. No incluyas datos de pacientes, contraseñas ni claves.</p>
          <div className="mb-7 mt-7" aria-label="Avance de la evaluación">
            <div className="flex justify-between gap-3 text-sm text-ink-600">
              <span>{review ? 'Revisa y envía' : `Paso ${step + 1} de 5`}</span>
              <span className="tabular">{completed} de 10 respuestas</span>
            </div>
            <progress value={completed} max={10} aria-label="Preguntas respondidas" className="mt-2 h-2 w-full appearance-none overflow-hidden rounded-full bg-ink-200 [&::-webkit-progress-bar]:bg-ink-200 [&::-webkit-progress-value]:bg-blue-900 [&::-moz-progress-bar]:bg-blue-900" />
          </div>
          <form onSubmit={review ? submit : next} noValidate>
            {review ? (
              <>
                <h2 className="text-xl font-semibold">Revisa tus respuestas</h2>
                <dl className="mt-4 divide-y divide-ink-200">
                  {HEURISTICS.map(({ id, title }, index) => (
                    <div key={id} className="flex items-start justify-between gap-4 py-3">
                      <div><dt className="text-sm font-medium">{title}</dt><dd className="mt-1 text-sm text-ink-600">{ratingLabel(answers[id])}</dd></div>
                      <button type="button" onClick={() => { setError(''); setStep(Math.floor(index / 2)) }} className="min-h-11 shrink-0 text-sm font-medium text-blue-800 underline underline-offset-4" aria-label={`Cambiar: ${title}`}>Cambiar</button>
                    </div>
                  ))}
                </dl>
                <label htmlFor="survey-device" className="mt-7 block text-sm font-medium">¿En qué dispositivo usaste principalmente INSOFT? (opcional)</label>
                <select id="survey-device" value={device} onChange={(event) => setDevice(event.target.value)} className="mt-2 min-h-11 w-full rounded-lg border border-ink-300 bg-white p-3 text-base">
                  {['No indicado', 'Teléfono', 'Tableta', 'Computador', 'Otro'].map((value) => <option key={value}>{value}</option>)}
                </select>
                <label htmlFor="survey-comment" className="mt-6 block text-sm font-medium">¿Qué cambiarías o qué te funcionó bien? (opcional)</label>
                <p id="survey-comment-help" className="mt-1 text-sm text-ink-600">Un ejemplo concreto nos ayuda a entender tu experiencia.</p>
                <textarea id="survey-comment" value={comment} onChange={(event) => setComment(event.target.value)} rows={4} maxLength={2000} aria-describedby="survey-comment-help survey-comment-count" className="mt-2 w-full rounded-lg border border-ink-300 bg-white p-3 text-base" />
                <p id="survey-comment-count" className="tabular mt-1 text-right text-xs text-ink-600">{comment.length}/2000</p>
                <label className="mt-6 flex min-h-11 cursor-pointer items-start gap-3 text-sm leading-relaxed">
                  <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 h-5 w-5 shrink-0 accent-blue-900" />
                  Quiero compartir estas respuestas con el equipo de INSOFT para mejorar la plataforma.
                </label>
              </>
            ) : visible.map(({ id, title, statement }, index) => (
              <fieldset key={id} className="mb-8 min-w-0 border-b border-ink-200 pb-8">
                <legend className="max-w-prose text-lg font-semibold">{step * 2 + index + 1}. {title}</legend>
                <p id={`${id}-statement`} className="mb-4 mt-2 leading-relaxed text-ink-700">{statement}</p>
                <div className="grid gap-2 sm:grid-cols-2" role="group" aria-describedby={`${id}-statement`}>
                  {RATING_OPTIONS.map(({ value, label }) => (
                    <label key={value} className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm leading-snug ${answers[id] === value ? 'border-blue-900 bg-soft-sky text-blue-900' : 'border-ink-300 bg-white text-ink-800 hover:bg-ink-100'}`}>
                      <input type="radio" name={id} value={value} checked={answers[id] === value} onChange={() => { setAnswers((previous) => ({ ...previous, [id]: value })); setError('') }} className="h-4 w-4 shrink-0 accent-blue-900" />
                      <span>{typeof value === 'number' ? `${value} · ` : ''}{label}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}
            {error && <p role="alert" className="mt-4 text-sm leading-relaxed text-wrong-700">{error}</p>}
            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
              <Button type="button" variant="secondary" disabled={step === 0 || sending} onClick={() => { setError(''); setStep((value) => value - 1) }}>Anterior</Button>
              <Button type="submit" loading={sending}>{review ? (sending ? 'Enviando…' : 'Enviar evaluación') : step === 4 ? 'Revisar respuestas' : 'Continuar'}</Button>
            </div>
          </form>
          <p className="mt-8 text-xs leading-relaxed text-ink-600">Adaptación propia de INSOFT basada en las <a href="https://www.nngroup.com/articles/ten-usability-heuristics/" target="_blank" rel="noreferrer" className="text-blue-800 underline underline-offset-4">10 heurísticas de Jakob Nielsen</a>. Evalúa tu percepción de uso; no es un cuestionario validado ni una calificación académica.</p>
        </>
      )}
    </main>
  )
}
