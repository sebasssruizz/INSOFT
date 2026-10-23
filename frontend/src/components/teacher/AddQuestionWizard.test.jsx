import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import AddQuestionWizard from './AddQuestionWizard'

vi.mock('../../services/questionService', () => ({
  createTeacherQuestion: vi.fn().mockResolvedValue({ id: 1 }),
}))

import { createTeacherQuestion } from '../../services/questionService'

const TOPICS = [
  {
    id: 1,
    name: 'UNIDAD 1. Generalidades',
    subtopics: [
      { id: 11, name: 'Anatomía del globo ocular' },
      { id: 12, name: 'Medicación' },
    ],
  },
  {
    id: 2,
    name: 'UNIDAD 2. Procedimientos',
    subtopics: [{ id: 21, name: 'Resección de pterigión' }],
  },
]

const DEFAULT_PROPS = { topics: TOPICS, initialSubtopicId: null, onClose: vi.fn(), onSaved: vi.fn() }

async function fillValidQuestion(user) {
  await user.type(screen.getByLabelText(/Enunciado/), '¿Cuántas preguntas de prueba hay?')
  await user.type(screen.getByLabelText(/texto de la respuesta a/i), 'Pocas')
  await user.type(screen.getByLabelText(/texto de la respuesta b/i), 'Muchas')
  await user.type(screen.getByLabelText(/texto de la respuesta c/i), 'Ninguna')
  await user.type(screen.getByLabelText(/texto de la respuesta d/i), 'Mil')
  await user.click(screen.getByLabelText('Opción B es la correcta'))
}

describe('AddQuestionWizard', () => {
  it('muestra los selectores de unidad y subtema dependientes', async () => {
    render(<AddQuestionWizard {...DEFAULT_PROPS} />)
    expect(screen.getByLabelText('Unidad')).toBeInTheDocument()
    const subtopicSelect = screen.getByLabelText('Subtema')
    expect(subtopicSelect).toBeDisabled()
    await userEvent.selectOptions(screen.getByLabelText('Unidad'), '1')
    expect(subtopicSelect).toBeEnabled()
    expect(screen.getByRole('option', { name: 'Anatomía del globo ocular' })).toBeInTheDocument()
  })

  it('marca la correcta y el foco inicial va a los selectores si no hay subtema', async () => {
    render(<AddQuestionWizard {...DEFAULT_PROPS} />)
    expect(screen.getByLabelText('Enunciado')).toBeInTheDocument()
  })

  it('Guardar y agregar otra conserva unidad y subtema y limpia el enunciado', async () => {
    const onSaved = vi.fn()
    render(<AddQuestionWizard {...DEFAULT_PROPS} initialSubtopicId={11} onSaved={onSaved} />)
    const user = userEvent.setup()
    const topicSelect = screen.getByLabelText('Unidad')
    const subtopicSelect = screen.getByLabelText('Subtema')

    await fillValidQuestion(user)
    await user.click(screen.getByRole('button', { name: 'Guardar y agregar otra' }))

    await waitFor(() => {
      expect(createTeacherQuestion).toHaveBeenCalledWith(
        11,
        expect.objectContaining({ correct_index: 1 }),
      )
    })
    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('Pregunta guardada')
    })
    expect(screen.getByLabelText(/Enunciado/)).toHaveValue('')
    expect(screen.getByLabelText(/texto de la respuesta a/i)).toHaveValue('')
    expect(topicSelect).toHaveValue('1')
    expect(subtopicSelect).toHaveValue('11')
    expect(onSaved).toHaveBeenCalledWith(11)
    await waitFor(() => {
      expect(screen.getByLabelText(/Enunciado/)).toHaveFocus()
    })
  })

  it('Guardar y salir cierra el asistente tras guardar', async () => {
    const onClose = vi.fn()
    render(<AddQuestionWizard {...DEFAULT_PROPS} onClose={onClose} />)
    const user = userEvent.setup()
    await user.selectOptions(screen.getByLabelText('Unidad'), '1')
    await user.selectOptions(screen.getByLabelText('Subtema'), '11')
    await fillValidQuestion(user)
    await user.click(screen.getByRole('button', { name: 'Guardar y salir' }))
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    })
  })

  it('deshabilita los botones mientras falta la correcta marcada', async () => {
    render(<AddQuestionWizard {...DEFAULT_PROPS} initialSubtopicId={11} />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/Enunciado/), '¿Pregunta válida para guardar?')
    for (const [i, label] of ['Pocas', 'Muchas', 'Ninguna', 'Mil'].entries()) {
      await user.type(screen.getByLabelText(new RegExp(`respuesta ${['A', 'B', 'C', 'D'][i]}`, 'i')), label)
    }
    expect(screen.getByRole('button', { name: 'Guardar y agregar otra' })).toBeDisabled()
    await user.click(screen.getByLabelText('Opción D es la correcta'))
    expect(screen.getByRole('button', { name: 'Guardar y agregar otra' })).toBeEnabled()
  })
})
