import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useMatch } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowUp,
  faChevronDown,
  faListCheck,
  faPaperPlane,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import { suggestionsFor } from '../lib/chatSuggestions'
import { splitUnitName } from '../lib/curriculum'
import { cn } from '../lib/utils'
import { useAuth } from '../hooks/useAuth'
import { useMediaQuery } from '../hooks/useMediaQuery'
import { askAi, getAiConversation } from '../services/aiService'
import AiAnswerFeedback from './AiAnswerFeedback'
import { getCourseTopics } from '../services/contentService'

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

function SofiaAvatar({ size = 'sm' }) {
  return (
    <img
      src="/brand/sofia-asistente.webp"
      alt=""
      aria-hidden="true"
      className={cn(
        'shrink-0 object-contain',
        size === 'sm' ? 'h-9 w-9' : 'h-12 w-12',
      )}
    />
  )
}

function Message({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex animate-rise-in gap-2.5', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && <SofiaAvatar />}
      <div
        className={cn(
          'max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-[0.9375rem] leading-relaxed sm:text-[0.8125rem]',
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
        {message.degraded && <p className="mt-2 text-xs font-semibold">Modo respaldo: fragmentos del material académico.</p>}
        {message.sources?.length > 0 && (
          <details className="mt-2 whitespace-normal text-xs">
            <summary className="cursor-pointer font-semibold">Fuentes consultadas</summary>
            {message.sources.map((source) => {
              const sourceCourse = source.course_id ?? message.courseId
              const href = sourceCourse ? `/courses/${sourceCourse}${source.subtopic_id ? `/subtopics/${source.subtopic_id}` : source.topic_id ? `/units/${source.topic_id}` : ''}` : null
              return <div key={source.number} className="mt-2">
                {href ? <Link className="text-blue-900 underline" to={href}>
                  [{source.number}] {source.title}
                </Link> : <span>[{source.number}] {source.title}</span>}
                <p className="mt-1 text-ink-500">{source.excerpt}</p>
              </div>
            })}
          </details>
        )}
        {!isUser && message.queryId && !message.error && (
          <AiAnswerFeedback queryId={message.queryId} initialFeedback={message.feedback} />
        )}
      </div>
    </div>
  )
}

function TypingBubble() {
  return (
    <div className="flex justify-start gap-2.5">
      <SofiaAvatar />
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

/**
 * Unidad y subtema en los que está el estudiante, deducidos de la URL y del
 * temario del curso. Sirven para elegir las preguntas sugeridas.
 */
function useStudyContext(courseId, topicId, subtopicId, enabled) {
  const [topics, setTopics] = useState([])

  const loadedFor = useRef(null)

  // Solo se pide el temario al abrir el chat, y una vez por curso: así el
  // asistente no añade una petición en cada cambio de página.
  useEffect(() => {
    if (!courseId) {
      loadedFor.current = null
      setTopics([])
      return undefined
    }
    if (loadedFor.current !== courseId && loadedFor.current !== null) setTopics([])
    if (!enabled || loadedFor.current === courseId) return undefined
    loadedFor.current = courseId
    // Cerrar el chat a mitad de la petición no la descarta; solo se ignora
    // si mientras tanto el estudiante cambió de curso.
    getCourseTopics(courseId)
      .then((data) => loadedFor.current === courseId && setTopics(data))
      .catch(() => {
        if (loadedFor.current === courseId) loadedFor.current = null
      })
    return undefined
  }, [courseId, enabled])

  return useMemo(() => {
    let topic = null
    let subtopic = null
    if (subtopicId) {
      for (const candidate of topics) {
        const found = candidate.subtopics.find((sub) => sub.id === subtopicId)
        if (found) {
          topic = candidate
          subtopic = found
          break
        }
      }
    } else if (topicId) {
      topic = topics.find((candidate) => candidate.id === topicId) || null
    }
    const unit = topic ? splitUnitName(topic.name) : null
    return { unit, subtopic }
  }, [topics, topicId, subtopicId])
}

/**
 * Altura visible real en móvil. Con el teclado abierto `100dvh` no se encoge
 * en iOS, así que el panel se ajusta a `visualViewport` para que el campo de
 * texto quede siempre a la vista, justo encima del teclado.
 */
function useVisualViewport(active) {
  const [box, setBox] = useState(null)

  useEffect(() => {
    const viewport = window.visualViewport
    if (!active || !viewport) {
      setBox(null)
      return undefined
    }
    const update = () => setBox({ height: viewport.height, top: viewport.offsetTop })
    update()
    viewport.addEventListener('resize', update)
    viewport.addEventListener('scroll', update)
    return () => {
      viewport.removeEventListener('resize', update)
      viewport.removeEventListener('scroll', update)
    }
  }, [active])

  return box
}

export default function AiChatWidget() {
  const { user } = useAuth()
  const firstName = user?.name?.split(' ')[0] || ''
  // Pantalla completa en celular, también en horizontal (poca altura): ahí
  // una ventana flotante dejaría dos líneas de conversación a la vista.
  const isMobile = !useMediaQuery('(min-width: 640px) and (min-height: 560px)')
  // Sin cursor fino el campo usa 16px: por debajo iOS hace zoom al enfocarlo.
  const touch = !useMediaQuery('(hover: hover) and (pointer: fine)')

  const [open, setOpen] = useState(false)

  // Curso, unidad y subtema actuales (cualquier página dentro de /courses/:courseId/...).
  const courseMatch = useMatch('/courses/:courseId/*')
  const unitMatch = useMatch('/courses/:courseId/units/:topicId/*')
  const subtopicMatch = useMatch('/courses/:courseId/subtopics/:subtopicId')
  const courseId = courseMatch ? Number(courseMatch.params.courseId) : null
  const topicId = unitMatch ? Number(unitMatch.params.topicId) : null
  const subtopicId = subtopicMatch ? Number(subtopicMatch.params.subtopicId) : null
  const { unit, subtopic } = useStudyContext(courseId, topicId, subtopicId, open)
  const suggestions = suggestionsFor(unit?.number, subtopic?.name)

  const greeting = `Hola${firstName ? `, ${firstName}` : ''}. Soy Sofía y estoy para ayudarte.`
  const [messages, setMessages] = useState([])
  const storageKey = `sofia:conversation:${user?.id ?? user?.email ?? 'anonymous'}:${courseId ?? 'general'}`
  const [sessionId, setSessionId] = useState(null)
  const [restoring, setRestoring] = useState(true)
  const [historyError, setHistoryError] = useState('')
  const [selectedText, setSelectedText] = useState('')
  const activeConversation = useRef(null)
  const conversationEpoch = useRef(0)
  const activeScope = useRef(storageKey)
  activeScope.current = storageKey
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)
  const viewport = useVisualViewport(open && isMobile)

  useEffect(() => {
    let cancelled = false
    let stored
    try { stored = sessionStorage.getItem(storageKey) } catch { /* memoria de esta página */ }
    const id = stored || crypto.randomUUID()
    try { sessionStorage.setItem(storageKey, id) } catch { /* memoria de esta página */ }
    activeConversation.current = id
    conversationEpoch.current += 1
    setSessionId(id)
    setMessages([])
    setInput('')
    setSending(false)
    setHistoryError('')
    setRestoring(Boolean(stored))
    if (stored) {
      getAiConversation(id, courseId).then((rows) => {
        if (cancelled) return
        setMessages([...rows].reverse().flatMap((row) => [
          { role: 'user', content: row.question },
          { role: 'assistant', content: row.answer || '', queryId: row.id, feedback: row.feedback,
            sources: row.sources, courseId: row.course_id, course: row.course_id != null,
            scope: Boolean(row.subtopic_id), chunks: row.sources?.length || 0, degraded: row.degraded },
        ]))
      }).catch((err) => {
        if (!cancelled) setHistoryError(`No se pudo recuperar la conversación: ${err.message}`)
      }).finally(() => { if (!cancelled) setRestoring(false) })
    }
    return () => { cancelled = true }
  }, [storageKey, courseId])

  useEffect(() => { setSelectedText('') }, [courseId, subtopicId])

  useEffect(() => {
    const selectFragment = (event) => {
      if (Number(event.detail.courseId) !== courseId || Number(event.detail.subtopicId) !== subtopicId) return
      setSelectedText(event.detail.text.slice(0, 2000))
      setInput('Explícame este fragmento')
      setOpen(true)
    }
    window.addEventListener('sofia:selection', selectFragment)
    return () => window.removeEventListener('sofia:selection', selectFragment)
  }, [courseId, subtopicId])

  const newConversation = () => {
    const id = crypto.randomUUID()
    activeConversation.current = id
    conversationEpoch.current += 1
    setSessionId(id)
    try { sessionStorage.setItem(storageKey, id) } catch { /* memoria de esta página */ }
    setMessages([])
    setInput('')
    setHistoryError('')
    setSelectedText('')
  }

  // En móvil el chat ocupa la pantalla: se bloquea el scroll del fondo para
  // que el gesto no arrastre la página por debajo.
  useEffect(() => {
    if (!open || !isMobile) return undefined
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [open, isMobile])

  useEffect(() => {
    if (!open) return undefined
    const onKey = (event) => event.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open, viewport?.height])

  const openChat = () => {
    setOpen(true)
  }

  const send = async (question) => {
    const text = (question ?? input).trim()
    if (!text || sending || restoring || !sessionId) return
    const requestSession = sessionId
    const requestScope = storageKey
    const requestEpoch = conversationEpoch.current
    const stillActive = () => activeConversation.current === requestSession && activeScope.current === requestScope && conversationEpoch.current === requestEpoch

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setSending(true)

    try {
      const data = await askAi(text, courseId, subtopicId, {
        session_id: requestSession, topic_id: topicId, selected_text: selectedText || null,
      })
      if (!stillActive()) return
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.respuesta,
          scope: Boolean(data.subtopic_id),
          course: courseId != null,
          chunks: data.chunks_usados,
          degraded: Boolean(data.degraded),
          queryId: data.query_id,
          sources: data.sources,
          courseId,
        },
      ])
    } catch (err) {
      if (!stillActive()) return
      const hint =
        err.status === 429
          ? '\n\n(Alcanzaste el límite de consultas; reintenta en el tiempo indicado.)'
          : err.status === 503
            ? '\n\n(El asistente no está disponible en este momento; en un minuto reintentamos.)'
            : ''
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: err.message + hint, error: true },
      ])
    } finally {
      if (stillActive()) setSending(false)
    }
  }

  const hasAsked = messages.some((m) => m.role === 'user')
  const contextLabel = subtopic
    ? subtopic.name
    : unit
      ? `Unidad ${unit.number ?? ''} · ${unit.title}`
      : 'Contenido del curso'

  // En móvil el panel ocupa toda la pantalla visible (encima del teclado si
  // está abierto). En escritorio es una ventana flotante sobre el botón.
  const mobileStyle =
    isMobile && viewport ? { top: viewport.top, height: viewport.height } : undefined

  return (
    <>
      {/* Botón flotante. En móvil se oculta con el chat abierto: el panel
          tiene su propio botón de cerrar y no debe quedar nada encima. */}
      <button
        type="button"
        onClick={() => (open ? setOpen(false) : openChat())}
        aria-label={open ? 'Cerrar a Sofía' : 'Hablar con Sofía, la asistente de IA'}
        aria-expanded={open}
        className={cn(
          'group/sofia fixed right-4 z-40 rounded-xl transition-transform duration-150 active:scale-[0.97] sm:right-6',
          open
            ? 'bottom-[max(1.25rem,env(safe-area-inset-bottom))] flex h-[3.25rem] w-[3.25rem] items-center justify-center rounded-full bg-ink-800 text-white shadow-e3 hover:bg-ink-900'
            : 'bottom-[max(4.75rem,calc(env(safe-area-inset-bottom)+4rem))] h-28 w-56 text-left sm:bottom-[max(1.25rem,env(safe-area-inset-bottom))] sm:w-60',
          open && isMobile && 'hidden',
        )}
      >
        {open ? (
          <FontAwesomeIcon icon={faChevronDown} className="text-lg" aria-hidden="true" />
        ) : (
          <>
            <span className="absolute -top-1.5 left-0 z-10 w-40 rounded-xl border border-black bg-white px-3 py-2 text-blue-900 shadow-e3 transition-colors duration-150 group-hover/sofia:bg-soft-sky sm:top-0">
              <span className="block text-xs leading-4">Sofía · Asistente IA</span>
              <span className="mt-0.5 block text-sm font-semibold leading-[1.125rem]">Hazme una pregunta</span>
            </span>
            <img
              src="/brand/sofia-asistente.webp"
              alt=""
              aria-hidden="true"
              width="384"
              height="448"
              draggable="false"
              className="pointer-events-none absolute bottom-0 right-0 h-28 w-24 object-contain"
            />
          </>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-modal={isMobile || undefined}
          aria-label="Sofía, asistente de IA"
          style={mobileStyle}
          className={cn(
            'fixed z-50 flex flex-col overflow-hidden bg-white',
            isMobile
              ? // Celular: pantalla completa, sube desde abajo.
                'inset-x-0 top-0 h-[100dvh] animate-slide-in-up'
              : // Escritorio y tableta: ventana flotante sobre el botón.
                'bottom-24 right-6 h-[min(34rem,calc(100dvh-8rem))] w-[24rem] animate-scale-in rounded-2xl border border-ink-200 shadow-e4',
          )}
        >
          <header
            className={cn(
              'flex items-center gap-3 border-b border-ink-200 bg-soft-sky px-4 py-3',
              isMobile && 'pt-[max(0.75rem,env(safe-area-inset-top))]',
            )}
          >
            <SofiaAvatar size="md" />
            <div className="min-w-0 flex-1">
              <h2 className="flex items-center gap-2 text-base font-semibold leading-tight text-ink-900">
                Sofía
                <span className="h-1.5 w-1.5 rounded-full bg-correct-500" aria-hidden="true" />
              </h2>
              <p className="truncate text-[0.75rem] text-ink-500" title={contextLabel}>Contexto actual: {contextLabel}</p>
            </div>
            <button type="button" disabled={sending || restoring} onClick={newConversation}
              className="text-xs font-semibold text-blue-900 disabled:opacity-50">Nueva conversación</button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Cerrar el chat"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-ink-500 transition-colors duration-150 hover:bg-white hover:text-ink-900"
            >
              <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
            </button>
          </header>

          {/* En un subtema: acceso directo al modo práctica de ese subtema. */}
          {subtopicId && courseId && (
            <div className="border-b border-ink-200 px-4 py-2.5">
              <Link
                to={`/courses/${courseId}/subtopics/${subtopicId}?practice=1`}
                onClick={() => isMobile && setOpen(false)}
                className="flex items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white px-3 py-2 text-[0.8125rem] font-semibold text-blue-900 transition-colors duration-150 hover:border-blue-400 hover:bg-soft-sky"
              >
                <FontAwesomeIcon icon={faListCheck} className="text-[0.7rem]" aria-hidden="true" />
                Ponme a prueba
              </Link>
            </div>
          )}

          <div
            ref={scrollRef}
            className="min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain px-4 py-4"
          >
            <Message message={{ role: 'assistant', content: greeting }} />
            {restoring && <p role="status" className="text-xs text-ink-500">Recuperando conversación…</p>}
            {historyError && <p role="alert" className="text-xs text-wrong-700">{historyError} Puedes iniciar una nueva conversación.</p>}

            {!hasAsked && !sending && !restoring && (
              <div className="animate-fade-in pl-[2.375rem]" style={{ animationDelay: '150ms' }}>
                <p className="eyebrow mb-2 text-ink-400">Puedes preguntarme</p>
                <div className="flex flex-col items-start gap-2">
                  {suggestions.map((text) => (
                    <button
                      key={text}
                      type="button"
                      onClick={() => send(text)}
                      className="rounded-2xl border border-blue-200 bg-white px-3.5 py-2 text-left text-[0.875rem] font-medium leading-snug text-blue-900 transition-[border-color,background-color,transform] duration-150 hover:border-blue-400 hover:bg-soft-sky active:scale-[0.98] sm:text-[0.8125rem]"
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <Message key={`${sessionId}-${index}`} message={message} />
            ))}
            {sending && <TypingBubble />}
          </div>

          {selectedText && <div className="border-t border-ink-200 px-4 py-2 text-xs">
            <p className="line-clamp-2">Fragmento seleccionado: {selectedText}</p>
            <button type="button" className="mt-1 text-blue-900 underline" onClick={() => setSelectedText('')}>Quitar fragmento</button>
          </div>}
          <form
            className={cn(
              'flex items-end gap-2 border-t border-ink-200 bg-white p-3',
              isMobile && 'pb-[max(0.75rem,env(safe-area-inset-bottom))]',
            )}
            onSubmit={(event) => {
              event.preventDefault()
              send()
              inputRef.current?.focus()
            }}
          >
            {/* text-base en móvil: por debajo de 16px iOS hace zoom al enfocar
                el campo y la página entera se descuadra. */}
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (
                  !touch &&
                  event.key === 'Enter' &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault()
                  send()
                }
              }}
              rows={1}
              maxLength={500}
              enterKeyHint="send"
              placeholder="Escribe tu pregunta…"
              aria-label="Tu pregunta para Sofía"
              className={cn(
                'max-h-28 min-h-[2.75rem] flex-1 resize-none rounded-xl border border-ink-200 bg-ink-50 px-3.5 text-ink-900 placeholder:text-ink-400 transition-[border-color,box-shadow] duration-150 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:ring-offset-0',
                touch ? 'py-2.5 text-base' : 'py-2 text-[0.8125rem]',
              )}
            />
            <button
              type="submit"
              disabled={sending || restoring || !sessionId || !input.trim()}
              aria-label="Enviar pregunta"
              className="flex h-[2.75rem] w-[2.75rem] shrink-0 items-center justify-center rounded-xl bg-blue-900 text-white transition-[background-color,transform] duration-150 hover:bg-blue-800 active:scale-95 disabled:pointer-events-none disabled:opacity-40"
            >
              <FontAwesomeIcon
                icon={sending ? faArrowUp : faPaperPlane}
                className={cn(sending && 'animate-pulse')}
                aria-hidden="true"
              />
            </button>
          </form>
        </div>
      )}
    </>
  )
}
