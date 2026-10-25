import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import QuestionCard from './QuestionCard'

const question = {
  id: 12,
  prompt: 'Pregunta oficial de prueba',
  options: ['Primera', 'Segunda', 'Tercera', 'Cuarta'],
  correct_index: 1,
  explanation: 'Explicación de prueba',
  source: 'official',
  status: 'approved',
  is_owner: false,
}

describe('Retirar preguntas del curso', () => {
  it('permite cancelar y solo retira al confirmar dentro de la tarjeta', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    render(<QuestionCard question={question} onDelete={onDelete} />)
    const trash = screen.getByRole('button', { name: `Retirar del curso: ${question.prompt}` })
    await user.click(trash)
    expect(onDelete).not.toHaveBeenCalled()
    expect(screen.getByText(/Se conservarán las respuestas anteriores/)).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Cancelar', exact: true }))
    expect(onDelete).not.toHaveBeenCalled()
    await user.click(trash)
    await user.click(screen.getByRole('button', { name: 'Retirar del curso', exact: true }))
    expect(onDelete).toHaveBeenCalledTimes(1)
    expect(onDelete).toHaveBeenCalledWith(question)
  })

  it('no ofrece retirada en vistas que no proporcionan esa acción', () => {
    render(<QuestionCard question={question} />)
    expect(screen.queryByRole('button', { name: /Retirar del curso/ })).not.toBeInTheDocument()
    expect(screen.getByText('Respuesta correcta')).toBeVisible()
  })
})
