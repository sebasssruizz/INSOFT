import { useMemo, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowRight,
  faCheck,
  faLightbulb,
  faRotateRight,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

function OptionRow({ label, text, state, onSelect, disabled }) {
  const isChosenRight = state === 'chosen-right'
  const isChosenWrong = state === 'chosen-wrong'
  const isRevealed = state === 'revealed'

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={cn(
        'flex w-full items-start gap-3.5 rounded-xl border px-4 py-3.5 text-left',
        'transition-[background-color,border-color,box-shadow,transform] duration-150 ease-out',
        state === 'idle' &&
          'border-ink-200 bg-white hover:-translate-y-px hover:border-blue-400 hover:bg-blue-50 hover:shadow-e2',
        isChosenRight && 'border-correct-500 bg-correct-50',
        isChosenWrong && 'border-wrong-500 bg-wrong-50',
        isRevealed && 'border-correct-200 bg-correct-50/60',
        state === 'muted' && 'border-ink-200 bg-white opacity-55',
        disabled && 'cursor-default',
      )}
    >
      <span
        className={cn(
          'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg font-sans text-xs font-bold transition-colors duration-150',
          state === 'idle' && 'bg-ink-100 text-ink-600',
          isChosenRight && 'bg-correct-500 text-white',
          isChosenWrong && 'bg-wrong-500 text-white',
          isRevealed && 'bg-correct-500 text-white',
          state === 'muted' && 'bg-ink-100 text-ink-400',
        )}
        aria-hidden="true"
      >
        {isChosenRight || isRevealed ? (
          <FontAwesomeIcon icon={faCheck} />
        ) : isChosenWrong ? (
          <FontAwesomeIcon icon={faXmark} />
        ) : (
          label
        )}
      </span>
      <span
        className={cn(
          'pt-0.5 text-[0.9375rem] leading-relaxed',
          isChosenRight || isRevealed
            ? 'font-medium text-correct-700'
            : isChosenWrong
              ? 'font-medium text-wrong-700'
              : 'text-ink-700',
        )}
      >
        {text}
      </span>
    </button>
  )
}

function Results({ answers, questions, onRestart, footer, exit }) {
  const right = answers.filter((answer) => answer.correct).length
  const score = Math.round((right / questions.length) * 100)
  const passed = score >= 70

  return (
    <div className="animate-scale-in">
      <div
        className={cn(
          'rounded-2xl border px-6 py-8 text-center',
          passed ? 'border-correct-200 bg-correct-50' : 'border-ink-200 bg-white',
        )}
      >
        <p className="eyebrow text-ink-500">Resultado del repaso</p>
        <p
          className={cn(
            'tabular mt-3 font-display text-6xl font-semibold leading-none',
            passed ? 'text-correct-700' : 'text-blue-800',
          )}
        >
          {score}%
        </p>
        <p className="tabular mt-3 text-sm text-ink-600">
          {right} de {questions.length} respuestas correctas
        </p>
        <p className="mx-auto mt-4 max-w-[46ch] text-sm leading-relaxed text-ink-600">
          {passed
            ? 'Dominas los conceptos de esta parte del temario. Puedes seguir avanzando.'
            : 'Merece la pena releer el contenido antes de continuar. Revisa abajo lo que falló.'}
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button onClick={onRestart} variant="secondary" icon={faRotateRight}>
            Repetir el repaso
          </Button>
          {footer}
          {exit}
        </div>
      </div>

      {answers.some((answer) => !answer.correct) && (
        <div className="mt-8">
          <h3 className="text-base font-semibold text-ink-900">Preguntas que fallaste</h3>
          <div className="mt-4 space-y-4">
            {answers
              .map((answer, index) => ({
                ...answer,
                question: questions[index],
              }))
              .filter((answer) => !answer.correct)
              .map((answer) => (
                <div
                  key={answer.question.id}
                  className="rounded-xl border border-ink-200 bg-white p-5"
                >
                  <p className="text-[0.9375rem] font-medium leading-relaxed text-ink-900">
                    {answer.question.prompt}
                  </p>
                  <p className="mt-3 flex items-start gap-2 text-sm text-correct-700">
                    <FontAwesomeIcon icon={faCheck} className="mt-1 shrink-0" aria-hidden="true" />
                    {answer.question.options[answer.question.correct_index]}
                  </p>
                  <p className="mt-2.5 text-sm leading-relaxed text-ink-600">
                    {answer.question.explanation}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Repaso de opción múltiple con retroalimentación inmediata.
 *
 * El valor formativo está en la explicación que aparece tras responder, no en
 * la nota: por eso se muestra siempre, se acierte o no, y no se puede cambiar
 * la respuesta una vez enviada.
 */
export default function Quiz({ questions, onFinish, footer, exit }) {
  const [index, setIndex] = useState(0)
  const [chosen, setChosen] = useState(null)
  const [answers, setAnswers] = useState([])
  const [finished, setFinished] = useState(false)

  const question = questions[index]
  const isLast = index === questions.length - 1
  const progress = useMemo(
    () => ((index + (chosen !== null ? 1 : 0)) / questions.length) * 100,
    [index, chosen, questions.length],
  )

  const restart = () => {
    setIndex(0)
    setChosen(null)
    setAnswers([])
    setFinished(false)
  }

  const choose = (optionIndex) => {
    if (chosen !== null) return
    setChosen(optionIndex)
    setAnswers((previous) => [
      ...previous,
      { chosen: optionIndex, correct: optionIndex === question.correct_index },
    ])
  }

  const advance = () => {
    if (isLast) {
      setFinished(true)
      const right = answers.filter((answer) => answer.correct).length
      onFinish?.({
        right,
        total: questions.length,
        score: Math.round((right / questions.length) * 100),
      })
      return
    }
    setIndex((current) => current + 1)
    setChosen(null)
  }

  if (!questions.length) {
    return (
      <p className="rounded-xl border border-dashed border-ink-300 bg-white px-5 py-8 text-center text-sm text-ink-500">
        Esta parte del temario todavía no tiene preguntas de repaso.
      </p>
    )
  }

  if (finished) {
    return (
      <Results
        answers={answers}
        questions={questions}
        onRestart={restart}
        footer={footer}
        exit={exit}
      />
    )
  }

  const answered = chosen !== null
  const wasRight = answered && chosen === question.correct_index

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
        <span className="h-1 min-w-[8rem] flex-1 overflow-hidden rounded-full bg-ink-200">
          <span
            className="block h-full w-full origin-left rounded-full bg-blue-800 transition-transform duration-500 ease-out"
            style={{ transform: `scaleX(${progress / 100})` }}
          />
        </span>
        <span className="tabular shrink-0 text-xs font-semibold text-ink-500">
          {index + 1} / {questions.length}
        </span>
        {/* Salir a mitad del repaso sin perder de vista el resto del temario. */}
        {exit}
      </div>

      <div key={question.id} className="animate-rise-in mt-7">
        <h3 className="font-display text-[1.375rem] font-semibold leading-snug tracking-[-0.01em] text-ink-900">
          {question.prompt}
        </h3>

        <div className="mt-5 space-y-2.5">
          {question.options.map((option, optionIndex) => {
            let state = 'idle'
            if (answered) {
              if (optionIndex === chosen) state = wasRight ? 'chosen-right' : 'chosen-wrong'
              else if (optionIndex === question.correct_index) state = 'revealed'
              else state = 'muted'
            }
            return (
              <OptionRow
                key={optionIndex}
                label={LETTERS[optionIndex]}
                text={option}
                state={state}
                disabled={answered}
                onSelect={() => choose(optionIndex)}
              />
            )
          })}
        </div>

        {answered && (
          <div className="animate-rise-in mt-5 rounded-xl border border-blue-200 bg-blue-50 p-5">
            <p className="flex items-center gap-2 font-sans text-xs font-bold uppercase tracking-[0.1em] text-blue-800">
              <FontAwesomeIcon icon={faLightbulb} aria-hidden="true" />
              {wasRight ? 'Correcto' : 'Por qué la respuesta es otra'}
            </p>
            <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-700">
              {question.explanation}
            </p>
            <Button onClick={advance} className="group/btn mt-5" iconRight={faArrowRight}>
              {isLast ? 'Ver resultado' : 'Siguiente pregunta'}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
