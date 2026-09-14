import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowLeft,
  faCheck,
  faFileArrowUp,
  faLayerGroup,
  faWandMagicSparkles,
} from '@fortawesome/free-solid-svg-icons'

import { Button } from '../components/ui/Button'
import { importCourseContent } from '../services/courseService'
import { DEMO_DOCUMENT } from '../lib/demoContent'

const SAMPLE = `# UNIDAD 9. Cirugía de Pterigión paso a paso
Breve descripción de la unidad.

## Resección de pterigión
Contenido libre con párrafos, **negritas** y listas.

### Preguntas
1. **¿Pregunta de repaso?**
   - [ ] Opción incorrecta
   - [x] Opción correcta
   Explicación de la respuesta.`

export default function TeacherImportPage() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const fileRef = useRef(null)

  const loadFile = (file) => {
    if (!file) return
    setError(null)
    setResult(null)
    const reader = new FileReader()
    reader.onload = (event) => setText(String(event.target.result || ''))
    reader.onerror = () => setError('No se pudo leer el archivo.')
    reader.readAsText(file)
  }

  const loadExample = () => {
    setError(null)
    setResult(null)
    setText(DEMO_DOCUMENT)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const summary = await importCourseContent(text)
      setResult(summary)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-[72rem] px-6 py-10 lg:px-10">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:text-blue-800"
      >
        <FontAwesomeIcon icon={faArrowLeft} className="text-[0.7rem]" aria-hidden="true" />
        Panel del profesor
      </Link>

      <header className="mt-4">
        <p className="eyebrow text-blue-800">Panel del profesor</p>
        <h1 className="mt-2 text-[2rem] font-semibold leading-tight tracking-[-0.02em] text-ink-900">
          Importar contenido
        </h1>
        <p className="mt-2.5 max-w-[62ch] text-[0.9375rem] leading-relaxed text-ink-500">
          Subí un documento Markdown con unidades, subtemas y preguntas de repaso. Se agrega al
          contenido oficial (visible en todos los cursos) y se indexa automáticamente para el
          asistente de IA. Nunca borra contenido existente.
        </p>
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_26rem]">
        {/* Formulario */}
        <form onSubmit={handleSubmit} className="rounded-2xl border border-ink-200 bg-white p-6 shadow-e1 lg:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <span
              className="flex h-11 w-11 items-center justify-center rounded-2xl bg-soft-lavender text-deep-lavender"
              aria-hidden="true"
            >
              <FontAwesomeIcon icon={faFileArrowUp} />
            </span>
            <div>
              <h2 className="text-lg font-semibold tracking-[-0.01em] text-ink-900">
                Documento (.md o .txt)
              </h2>
              <p className="text-sm text-ink-500">Arrastrá un archivo o escribilo a mano.</p>
            </div>
          </div>

          <input
            ref={fileRef}
            type="file"
            accept=".md,.txt,text/markdown,text/plain"
            onChange={(event) => loadFile(event.target.files?.[0])}
            className="mt-5 block w-full cursor-pointer text-sm text-ink-500 file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-soft-sky file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-800 hover:file:bg-blue-100"
          />

          <textarea
            value={text}
            onChange={(event) => {
              setText(event.target.value)
              setResult(null)
            }}
            placeholder={`# UNIDAD 9. Nombre de la unidad\nBreve descripción...\n\n## Subtema\nContenido del subtema...\n\n### Preguntas\n1. **¿Pregunta?**\n   - [ ] Opción\n   - [x] Correcta\n   Explicación.`}
            rows={18}
            spellCheck={false}
            aria-label="Documento Markdown a importar"
            className="mt-4 w-full resize-y rounded-xl border border-ink-300 bg-ink-50 px-4 py-3 font-mono text-[0.8125rem] leading-relaxed text-ink-900 placeholder:text-ink-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-700"
          />

          {error && (
            <div className="mt-4 rounded-xl border border-wrong-200 bg-wrong-50 px-4 py-3 text-sm text-wrong-700">
              {error}
            </div>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button
              type="submit"
              loading={loading}
              icon={faWandMagicSparkles}
              disabled={text.trim().length < 20}
            >
              {loading ? 'Importando e indexando…' : 'Importar e indexar'}
            </Button>
            <Button type="button" variant="secondary" size="sm" onClick={loadExample}>
              Cargar ejemplo
            </Button>
            {text.trim().length > 0 && text.trim().length < 20 && (
              <span className="text-xs text-ink-400">Mínimo 20 caracteres.</span>
            )}
          </div>
        </form>

        {/* Ayuda + resultado */}
        <aside className="space-y-6 lg:sticky lg:top-8 lg:self-start">
          <div className="rounded-2xl border border-ink-200 bg-white p-6 shadow-e1">
            <p className="eyebrow text-ink-400">Formato</p>
            <pre className="mt-3 overflow-x-auto rounded-xl bg-ink-950 p-4 font-mono text-[0.6875rem] leading-relaxed text-blue-100">
              {SAMPLE}
            </pre>
            <ul className="mt-4 space-y-1.5 text-[0.8125rem] leading-relaxed text-ink-600">
              <li>
                <span className="font-semibold text-ink-900">#</span> crea una unidad,{' '}
                <span className="font-semibold text-ink-900">##</span> un subtema.
              </li>
              <li>
                La correcta se marca con <span className="font-semibold text-ink-900">[x]</span>.
                La explicación va después de las opciones.
              </li>
              <li>
                Al importar, el subtema se indexa en el{' '}
                <span className="font-semibold text-ink-900">RAG</span> para la IA.
              </li>
            </ul>
          </div>

          {result && (
            <div className="animate-rise-in rounded-2xl border border-correct-200 bg-correct-50 p-6">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-correct-500 text-white">
                  <FontAwesomeIcon icon={faCheck} />
                </span>
                <div>
                  <h3 className="text-base font-semibold text-ink-900">Importado correctamente</h3>
                  <p className="text-sm text-correct-700">
                    {result.subtemas_creados + result.subtemas_actualizados} subtemas ·{' '}
                    {result.chunks_indexados} fragmentos indexados para la IA
                  </p>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-white/70 p-3">
                  <p className="tabular font-display text-2xl font-semibold text-blue-900">
                    {result.unidades}
                  </p>
                  <p className="eyebrow mt-1 text-ink-500">
                    {result.unidades === 1 ? 'Unidad' : 'Unidades'} (creadas:{' '}
                    {result.unidades_creadas})
                  </p>
                </div>
                <div className="rounded-xl bg-white/70 p-3">
                  <p className="tabular font-display text-2xl font-semibold text-deep-lavender">
                    {result.preguntas_creadas + result.preguntas_actualizadas}
                  </p>
                  <p className="eyebrow mt-1 text-ink-500">Preguntas</p>
                </div>
              </div>

              {result.subtemas.length > 0 && (
                <div className="mt-4">
                  <p className="eyebrow mb-2 text-ink-500">Subtemas</p>
                  <ul className="space-y-1">
                    {result.subtemas.map((name) => (
                      <li key={name} className="text-sm text-ink-700">
                        {name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <Link
                to="/dashboard"
                className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-correct-700 hover:text-correct-700"
              >
                <FontAwesomeIcon icon={faLayerGroup} className="text-[0.7rem]" aria-hidden="true" />
                Ver en el panel / Cursos
              </Link>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}