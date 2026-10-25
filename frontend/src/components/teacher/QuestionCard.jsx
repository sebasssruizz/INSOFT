import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faCircleXmark, faPen, faRobot, faTrash } from '@fortawesome/free-solid-svg-icons'

import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

const LETTERS = ['A', 'B', 'C', 'D']

const SOURCE_LABELS = {
  official: 'Oficial',
  teacher: 'Docente',
  ai: 'IA',
}

function Badge({ tone, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.6875rem] font-bold uppercase tracking-[0.06em]',
        tone === 'official' && 'bg-ink-100 text-ink-600',
        tone === 'teacher' && 'bg-soft-sky text-blue-900',
        tone === 'ai-pending' && 'bg-soft-butter text-deep-butter',
        tone === 'ai-approved' && 'bg-correct-50 text-correct-700',
        tone === 'ai-practice' && 'bg-soft-lavender text-deep-lavender',
        tone === 'rejected' && 'bg-wrong-50 text-wrong-700',
      )}
    >
      {tone === 'ai-pending' || tone === 'ai-approved' || tone === 'ai-practice' ? (
        <FontAwesomeIcon icon={faRobot} className="text-[0.625rem]" aria-hidden="true" />
      ) : null}
      {children}
    </span>
  )
}

function badgeFor(question) {
  if (question.status === 'rejected') return { tone: 'rejected', label: 'Rechazada' }
  if (question.source === 'ai') {
    if (question.status === 'approved') return { tone: 'ai-approved', label: 'IA · aprobada' }
    if (question.status === 'practice') return { tone: 'ai-practice', label: 'IA · práctica' }
    return { tone: 'ai-pending', label: 'IA · pendiente' }
  }
  if (question.source === 'teacher') return { tone: 'teacher', label: 'Docente' }
  return { tone: 'official', label: 'Oficial' }
}

/**
 * Tarjeta de una pregunta del banco del profesor: enunciado, opciones A-D con
 * la correcta marcada, explicación y acciones según permisos (is_owner).
 */
export default function QuestionCard({ question, onEdit, onDelete, onReview, busy }) {
  const [confirmRemove, setConfirmRemove] = useState(false)
  const badge = badgeFor(question)
  const canManage = question.is_owner && question.source !== 'official'
  const canReview =
    question.is_owner && question.source === 'ai' && question.status === 'pending'
  // Práctica (created_by NULL): cualquier profesor con acceso al subtema puede
  // promoverla al banco o descartarla (excepción a la regla "solo el autor").
  const canReviewPractice = question.source === 'ai' && question.status === 'practice'

  return (
    <article
      className={cn(
        'rounded-2xl border bg-white p-5',
        question.status === 'pending' && 'border-deep-butter/40',
        question.status === 'rejected' && 'border-wrong-200 opacity-75',
        question.status === 'approved' && 'border-ink-200',
      )}
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Badge tone={badge.tone}>{badge.label}</Badge>
        {(canManage || onDelete) && (
          <div className="flex items-center gap-2">
            {canManage && onEdit && (
              <Button variant="ghost" size="sm" icon={faPen} onClick={() => onEdit(question)} disabled={busy}>
                Editar
              </Button>
            )}
            {onDelete && (
              <Button type="button" variant="ghost" size="icon" icon={faTrash}
                className="h-11 w-11 text-wrong-700"
                aria-label={`Retirar del curso: ${question.prompt}`}
                title="Retirar de este curso"
                aria-expanded={confirmRemove}
                onClick={() => setConfirmRemove((current) => !current)} disabled={busy} />
            )}
          </div>
        )}
      </header>

      {confirmRemove && (
        <div role="alert" className="mt-3 rounded-xl border border-wrong-200 bg-wrong-50 p-3.5">
          <p className="text-sm font-medium text-ink-900">¿Retirar esta pregunta de este curso?</p>
          <p className="mt-1 text-sm text-ink-600">Se conservarán las respuestas anteriores y seguirá disponible en otros cursos.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button type="button" variant="secondary" size="sm" disabled={busy} onClick={() => setConfirmRemove(false)}>Cancelar</Button>
            <Button type="button" variant="danger" size="sm" disabled={busy} onClick={() => { setConfirmRemove(false); onDelete(question) }}>Retirar del curso</Button>
          </div>
        </div>
      )}

      <p className="mt-3 text-[0.9375rem] font-medium leading-relaxed text-ink-900">
        {question.prompt}
      </p>

      <ul className="mt-3 space-y-2">
        {question.options.map((option, index) => {
          const isCorrect = index === question.correct_index
          return (
            <li
              key={index}
              className={cn(
                'flex items-start gap-3 rounded-xl border px-3.5 py-2.5 text-sm',
                isCorrect ? 'border-correct-300 bg-correct-50' : 'border-ink-200 bg-white',
              )}
            >
              <span
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[0.6875rem] font-bold',
                  isCorrect ? 'bg-correct-500 text-white' : 'bg-ink-100 text-ink-600',
                )}
                aria-hidden="true"
              >
                {LETTERS[index]}
              </span>
              <span className={cn('pt-0.5', isCorrect ? 'font-medium text-correct-700' : 'text-ink-700')}>
                {option}
                {isCorrect && <span className="mt-1 block text-xs font-semibold">Respuesta correcta</span>}
              </span>
            </li>
          )
        })}
      </ul>

      {question.explanation && (
        <p className="mt-3 rounded-xl bg-ink-50 px-3.5 py-2.5 text-[0.8125rem] leading-relaxed text-ink-600">
          <span className="font-semibold text-ink-700">Explicación: </span>
          {question.explanation}
        </p>
      )}

      {canReview && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-ink-100 pt-4">
          <p className="mr-auto text-[0.8125rem] text-ink-500">
            Revisa la propuesta antes de mostrarla a tus estudiantes.
          </p>
          <Button
            variant="primary"
            size="sm"
            icon={faCircleCheck}
            onClick={() => onReview(question, 'approve')}
            disabled={busy}
          >
            Aprobar
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={faCircleXmark}
            onClick={() => onReview(question, 'reject')}
            disabled={busy}
          >
            Rechazar
          </Button>
        </div>
      )}

      {canReviewPractice && onReview && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-ink-100 pt-4">
          <p className="mr-auto text-[0.8125rem] text-ink-500">
            La usó el modo práctica. ¿La promueves al banco o la descartas?
          </p>
          <Button
            variant="primary"
            size="sm"
            icon={faCircleCheck}
            onClick={() => onReview(question, 'approve')}
            disabled={busy}
          >
            Aprobar para el banco
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={faCircleXmark}
            onClick={() => onReview(question, 'reject')}
            disabled={busy}
          >
            Descartar
          </Button>
        </div>
      )}
    </article>
  )
}
