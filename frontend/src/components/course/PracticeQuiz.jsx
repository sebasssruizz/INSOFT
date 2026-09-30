import { useCallback, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRotateRight, faSpinner, faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons'

import Quiz from './Quiz'
import { Button } from '../ui/Button'
import { ApiError } from '../../services/api'
import { submitQuizAnswer } from '../../services/quizService'
import { startPracticeSession } from '../../services/practiceService'
import { cn } from '../../lib/utils'

/**
 * Modo práctica: pide una sesión al servidor (banco + IA reutilizable) y
 * reutiliza el quiz con el attempt_id del servidor. Errores: 404 amable,
 * 429 (más tarde), red (reintentar).
 */
export default function PracticeQuiz({ subtopicId = null, topicId = null, count, exit }) {
  const [session, setSession] = useState(null)
  const [preparing, setPreparing] = useState(false)
  const [error, setError] = useState(null)
  const [round, setRound] = useState(0)

  const start = useCallback(async () => {
    setPreparing(true)
    setError(null)
    setSession(null)
    try {
      const data = await startPracticeSession({ subtopicId, topicId, count })
      setSession(data)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) setError(err.message)
        else if (err.status === 429) setError('Has alcanzado el límite de prácticas por hora. Intenta más tarde.')
        else if (err.status === 403) setError('No tienes acceso a la práctica de este tema.')
        else setError(err.message)
      } else {
        setError('No se pudo preparar tu práctica. Revisa tu conexión.')
      }
    } finally {
      setPreparing(false)
    }
  }, [subtopicId, topicId, count])

  const answerQuestion = useCallback(
    (questionId, selectedIndex) =>
      submitQuizAnswer({
        questionId,
        selectedIndex,
        attemptId: session.attempt_id,
      }),
    [session],
  )

  if (preparing) {
    return (
      <div className="animate-fade-in flex flex-col items-center justify-center gap-3 px-5 py-12 text-center">
        <FontAwesomeIcon icon={faSpinner} spin className="text-xl text-blue-800" aria-hidden="true" />
        <p className="text-sm text-ink-600">Preparando tu práctica…</p>
        <p className="max-w-[46ch] text-[0.75rem] text-ink-400">
          Puede tardar unos segundos si la IA está generando preguntas nuevas.
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 px-5 py-12 text-center">
        <p className="max-w-[46ch] text-sm text-wrong-700">{error}</p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button onClick={start} variant="secondary" icon={faRotateRight}>
            Reintentar
          </Button>
          {exit}
        </div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 px-5 py-10 text-center">
        <p className="max-w-[46ch] text-sm leading-relaxed text-ink-500">
          Un set corto con preguntas del banco y, si hace falta, generadas por IA
          enfocadas en lo que más se consulta.
        </p>
        <Button onClick={start} variant="primary">
          Empezar la práctica
        </Button>
        {exit}
      </div>
    )
  }

  return (
    <div>
      {session.composition.ai > 0 && !session.ai_available && (
        <p className="mb-4 rounded-xl border border-soft-butter bg-soft-butter/50 px-3.5 py-2.5 text-[0.75rem] text-deep-butter">
          La IA no está disponible ahora: practicás solo con preguntas del banco.
        </p>
      )}
      <Quiz
        key={`${session.attempt_id}-${round}`}
        questions={session.questions}
        onAnswer={answerQuestion}
        badgeFor={(question) =>
          question.is_ai_generated ? (
            <p className="mt-2 flex items-center gap-1.5 text-[0.6875rem] font-semibold uppercase tracking-[0.08em] text-ink-400">
              <FontAwesomeIcon icon={faWandMagicSparkles} aria-hidden="true" />
              Generada por IA · no revisada
            </p>
          ) : null
        }
        onRestartAttempt={() => setRound((value) => value + 1)}
        exit={exit}
      />
      <div className="mt-6 text-center">
        <Button
          variant="secondary"
          icon={faRotateRight}
          onClick={() => {
            setSession(null)
            start()
          }}
        >
          Practicar de nuevo
        </Button>
      </div>
    </div>
  )
}
