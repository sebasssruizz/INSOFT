import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { getFeedbackAccess, getFeedbackReviews } from '../services/feedbackService'
import { downloadCsv } from '../services/api'
import { HEURISTICS } from '../lib/usabilitySurvey'

export default function FeedbackReviewPage() {
  const [allowed, setAllowed] = useState(null)
  const [kind, setKind] = useState('pqrs')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [message, setMessage] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setError('')
    getFeedbackAccess().then((result) => { if (active) setAllowed(result.can_review) })
      .catch(() => { if (active) setError('No se pudo verificar el acceso. Pulsa Actualizar para intentarlo de nuevo.') })
    return () => { active = false }
  }, [attempt])

  useEffect(() => {
    if (!allowed) return
    let active = true
    setLoading(true)
    setData(null)
    setError('')
    getFeedbackReviews(kind, offset).then((result) => { if (active) setData(result) })
      .catch(() => { if (active) setError('No se pudieron cargar las opiniones. Pulsa Actualizar para intentarlo de nuevo.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [allowed, kind, offset, attempt])

  async function download() {
    if (downloading) return
    setDownloading(true)
    setError('')
    setMessage('')
    try {
      await downloadCsv('/feedback/export.csv', 'insoft-opiniones.csv')
      setMessage('La descarga está lista. Revisa las descargas de tu navegador.')
    } catch {
      setError('No se pudo descargar el archivo. Verifica tu acceso y vuelve a intentarlo.')
    } finally { setDownloading(false) }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 pb-28 pt-8 sm:px-8">
      <Link to="/dashboard" className="inline-flex min-h-11 items-center text-sm text-blue-800 underline underline-offset-4">Volver al panel</Link>
      <h1 className="mt-4 text-2xl font-semibold">Opiniones y PQRS</h1>
      <p className="mt-3 max-w-prose leading-relaxed text-ink-600">Espacio privado del equipo investigador. Consulta los comentarios y descarga las respuestas para analizarlas.</p>
      <div className="my-6 flex flex-col gap-3 sm:flex-row">
        {allowed && <Button onClick={download} loading={downloading}>{downloading ? 'Preparando archivo…' : 'Descargar todo (CSV)'}</Button>}
        <Button variant="secondary" onClick={() => setAttempt((value) => value + 1)} disabled={loading}>Actualizar</Button>
      </div>
      {allowed === null && !error && <p role="status">Verificando acceso…</p>}
      {allowed === false && <p className="mt-4 leading-relaxed">Tu cuenta no tiene acceso al panel de opiniones. Solo pueden entrar las cuentas autorizadas por el equipo.</p>}
      {allowed && <>
        <div role="group" aria-label="Tipo de opinión" className="flex flex-wrap gap-2 border-b border-ink-200 pb-5">
          {[['pqrs', 'Comentarios / PQRS'], ['evaluacion', 'Evaluaciones de uso']].map(([value, label]) => (
            <Button key={value} variant={kind === value ? 'primary' : 'secondary'} aria-pressed={kind === value} onClick={() => { setKind(value); setOffset(0) }}>{label}</Button>
          ))}
        </div>
        {loading && <p role="status" className="py-8">Cargando opiniones…</p>}
        {data && <>
          <p className="tabular py-5 text-sm text-ink-600">{data.total === 0 ? 'Todavía no hay envíos en esta sección.' : `${offset + 1}–${offset + data.items.length} de ${data.total} envíos`}</p>
          <ol className="divide-y divide-ink-200">
            {data.items.map((item) => <li key={item.id} className="min-w-0 py-6 first:pt-0">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-lg font-semibold">{kind === 'pqrs' ? `${item.tipo} · ${item.categoria}` : `Evaluación de uso #${item.id}`}</h2>
                <time className="text-sm text-ink-600" dateTime={item.creado_en}>{new Date(item.creado_en).toLocaleString('es-CO')}</time>
              </div>
              <p className="mt-2 text-xs text-ink-600">Participante {item.participante} · Registro #{item.id}{item.dispositivo ? ` · ${item.dispositivo}` : ''}</p>
              <p className="mt-3 whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{item.comentario || 'Sin comentario adicional.'}</p>
              <p className="mt-3 text-xs text-ink-600 [overflow-wrap:anywhere]">Página: {item.pagina}</p>
              {kind === 'evaluacion' && <details className="mt-4">
                <summary className="flex min-h-11 cursor-pointer items-center text-sm font-medium text-blue-800 underline underline-offset-4">Ver las 10 respuestas</summary>
                <p className="mb-3 text-xs text-ink-600">Versión: {item.version}. Escala de acuerdo: 1 (mínimo) a 5 (máximo).</p>
                <dl className="space-y-3">{HEURISTICS.map(({ id, title }) => <div key={id} className="flex justify-between gap-4 text-sm"><dt>{title}</dt><dd className="shrink-0 font-medium">{item.respuestas[id] ?? 'No probado / No aplica'}</dd></div>)}</dl>
              </details>}
            </li>)}
          </ol>
          {data.total > 20 && <nav aria-label="Páginas de opiniones" className="mt-6 flex justify-between gap-3">
            <Button variant="secondary" disabled={offset === 0 || loading} onClick={() => setOffset((value) => Math.max(0, value - 20))}>Anterior</Button>
            <Button variant="secondary" disabled={offset + 20 >= data.total || loading} onClick={() => setOffset((value) => value + 20)}>Siguiente</Button>
          </nav>}
        </>}
        <p className="mt-8 border-t border-ink-200 pt-5 text-xs leading-relaxed text-ink-600">El CSV incluye PQRS y evaluaciones completas. h01 a h10 siguen el orden de las heurísticas: 1 significa totalmente en desacuerdo y 5 totalmente de acuerdo; las celdas vacías no deben contarse como cero. El código de participante permite distinguir personas de entregas repetidas. No se exportan nombres ni correos de las cuentas; el texto libre puede contener información personal. Conserva el archivo dentro del equipo autorizado.</p>
      </>}
      {error && <p role="alert" className="mt-4 text-sm text-wrong-700">{error}</p>}
      {message && <p role="status" className="mt-4 text-sm">{message}</p>}
    </main>
  )
}
