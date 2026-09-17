import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowUp,
  faPaperPlane,
  faRobot,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'
import { useMatch } from 'react-router-dom'

import { cn } from '../lib/utils'
import { askAi } from '../services/aiService'

const SUGGESTIONS = [
  '¿Qué es un pterigión?',
  '¿Cuáles son los pasos de la cirugía?',
  '¿Qué complicaciones puede haber?',
]

/** Renderiza negritas **así** como texto en negrita (misma prosa que las lecciones). */
function RichText({ text }) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={i} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  )
}

function Message({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <span
          className="mr-2.5 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-900 text-white"
          aria-hidden="true"
        >
          <FontAwesomeIcon icon={faRobot} className="text-[0.75rem]" />
        </span>
      )}
      <div
        className={cn(
          'max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-[0.8125rem] leading-relaxed',
          isUser
            ? 'rounded-br-md bg-blue-900 text-white'
            : message.error
              ? 'rounded-bl-md border border-wrong-200 bg-wrong-50 text-wrong-700'
              : 'rounded-bl-md border border-ink-200 bg-ink-100 text-ink-800',
        )}
      >
        <RichText text={message.content} />
        {message.chunks > 0 && !message.error && (
          <span className="mt-1.5 block text-[0.6875rem] font-medium text-ink-400">
            {message.scope
              ? 'Según este subtema'
              : message.course
                ? 'Según el contenido del curso'
                : 'Según el contenido general'}
            {' · '}
            {message.chunks} {message.chunks === 1 ? 'fragmento' : 'fragmentos'}
          </span>
        )}
      </div>
    </div>
  )
}

function TypingBubble() {
  return (
    <div className="flex justify-start">
      <span
        className="mr-2.5 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-900 text-white"
        aria-hidden="true"
      >
        <FontAwesomeIcon icon={faRobot} className="text-[0.75rem]" />
      </span>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-ink-200 bg-ink-100 px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}

export default function AiChatWidget() {
  const [open, setOpen] = useState(false)
  // Contiene el curso/carpeta actual (cualquier página dentro de /courses/:courseId/...)
  // y, si es el caso, el subtema concreto para acotar todavía más el RAG.
  const courseMatch = useMatch('/courses/:courseId/*')
  const subtopicMatch = useMatch('/courses/:courseId/subtopics/:subtopicId')
  const courseId = courseMatch ? Number(courseMatch.params.courseId) : null
  const subtopicId = subtopicMatch ? Number(subtopicMatch.params.subtopicId) : null
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hola, soy el asistente del curso. Pregúntame cualquier duda sobre el contenido y te responderé con base en el material oficial.',
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)

  const send = async (question) => {
    const text = (question ?? input).trim()
    if (!text || sending) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setSending(true)

    try {
      const data = await askAi(text, courseId, subtopicId)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.respuesta,
          scope: Boolean(data.subtopic_id),
          course: courseId != null,
          chunks: data.chunks_usados,
        },
      ])
    } catch (err) {
      const hint =
        err.status === 429
          ? '\n\n(Alcanzaste el límite de preguntas por hora; intentá más tarde.)'
          : err.status === 503
            ? '\n\n(El proveedor de IA no responde ahora; intentá de nuevo en unos minutos.)'
            : ''
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: err.message + hint, error: true },
      ])
    } finally {
      setSending(false)
    }
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  return (
    <>
      {/* Botón flotante */}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? 'Cerrar el asistente' : 'Abrir el asistente de IA'}
        className={cn(
          'fixed bottom-5 right-4 z-40 flex items-center justify-center rounded-2xl text-white shadow-e3',
          'transition-[background-color,transform,box-shadow] duration-150 active:translate-y-px sm:right-6',
          open ? 'bg-ink-800 hover:bg-ink-900' : 'bg-blue-900 hover:bg-blue-800 hover:shadow-blue-glow',
        )}
        style={{ height: '3.25rem', width: '3.25rem' }}
      >
        <FontAwesomeIcon
          icon={open ? faXmark : faRobot}
          className={cn('text-lg', !open && 'animate-rise-in')}
          aria-hidden="true"
        />
      </button>

      {/* Panel del chat */}
      {open && (
        <div
          role="dialog"
          aria-label="Asistente de IA"
          className="fixed inset-x-4 bottom-24 z-40 flex h-[min(30rem,calc(100dvh-8rem))] animate-scale-in flex-col overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-e4 sm:left-auto sm:right-6 sm:w-[24rem]"
        >
          <header className="flex items-center gap-3 border-b border-ink-200 bg-soft-sky px-4 py-3.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-900 text-white">
              <FontAwesomeIcon icon={faRobot} aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="font-display text-base font-semibold leading-tight text-ink-900">
                Asistente de IA
              </h2>
              <p className="text-[0.6875rem] text-ink-500">
                {subtopicId
                  ? 'Responde según el subtema actual'
                  : 'Responde según el contenido del curso'}
              </p>
            </div>
          </header>

          <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {messages.map((message, index) => (
              <Message key={index} message={message} />
            ))}
            {sending && <TypingBubble />}
          </div>

          {!sending && messages.filter((m) => m.role === 'user').length === 0 && (
            <div className="border-t border-ink-200 px-4 pb-3 pt-3">
              <p className="eyebrow mb-2 px-1 text-ink-400">Sugerencias</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((text) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => send(text)}
                    className="rounded-full border border-blue-200 bg-soft-sky px-3 py-1.5 text-[0.75rem] font-semibold text-blue-900 transition-colors duration-150 hover:border-blue-400 hover:bg-blue-100"
                  >
                    {text}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form
            className="flex items-end gap-2 border-t border-ink-200 p-3"
            onSubmit={(event) => {
              event.preventDefault()
              send()
            }}
          >
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault()
                  send()
                }
              }}
              rows={1}
              placeholder="Escribí tu pregunta…"
              aria-label="Tu pregunta para el asistente"
              className="max-h-28 min-h-[2.75rem] flex-1 resize-none rounded-xl border border-ink-200 bg-ink-50 px-3.5 py-2 text-[0.8125rem] text-ink-900 placeholder:text-ink-400 transition-[border-color,box-shadow] duration-150 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:ring-offset-0"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              aria-label="Enviar pregunta"
              className="flex h-[2.75rem] w-[2.75rem] shrink-0 items-center justify-center rounded-xl bg-blue-900 text-white transition-colors duration-150 hover:bg-blue-800 disabled:pointer-events-none disabled:opacity-40"
            >
              <FontAwesomeIcon
                icon={sending ? faArrowUp : faPaperPlane}
                className={cn(sending && 'animate-spin')}
                aria-hidden="true"
              />
            </button>
          </form>
        </div>
      )}
    </>
  )
}