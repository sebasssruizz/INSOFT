import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import UsabilityEvaluationPage from './UsabilityEvaluationPage'
import { sendEvaluation } from '../services/feedbackService'

vi.mock('../services/feedbackService', () => ({ sendEvaluation: vi.fn() }))

const show = () => render(<MemoryRouter initialEntries={[{ pathname: '/feedback/evaluation', state: { sourcePage: '/courses/1/subtopics/2' } }]}><UsabilityEvaluationPage /></MemoryRouter>)

async function fillSurvey(user, onlyNa = false) {
  for (let step = 0; step < 5; step += 1) {
    for (const group of screen.getAllByRole('group').filter((element) => element.tagName === 'FIELDSET')) {
      await user.click(within(group).getByRole('radio', { name: onlyNa ? /No lo he probado/ : /^4 ·/ }))
    }
    await user.click(screen.getByRole('button', { name: step === 4 ? 'Revisar respuestas' : 'Continuar' }))
  }
}

describe('Evaluación de experiencia', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('valida respuestas sin obligar a valorar algo que no se usó y permite corregir', async () => {
    const user = userEvent.setup()
    show()
    await user.click(screen.getByRole('button', { name: 'Continuar' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Selecciona una respuesta')
    const groups = screen.getAllByRole('group').filter((element) => element.tagName === 'FIELDSET')
    await user.click(within(groups[0]).getByRole('radio', { name: /^4 ·/ }))
    await user.click(within(groups[1]).getByRole('radio', { name: /No lo he probado/ }))
    await user.click(screen.getByRole('button', { name: 'Continuar' }))
    expect(screen.getByText('Paso 2 de 5')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Anterior' }))
    expect(screen.getByRole('radio', { name: /^4 ·/, checked: true })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /No lo he probado/, checked: true })).toBeInTheDocument()
    expect(sendEvaluation).not.toHaveBeenCalled()
  })

  it('revisa, conserva datos ante fallo y reintenta con el mismo identificador', async () => {
    const user = userEvent.setup()
    sendEvaluation.mockRejectedValueOnce(new Error('sin conexión')).mockResolvedValueOnce({ id: 17 })
    show()
    await fillSurvey(user)
    await user.selectOptions(screen.getByLabelText(/dispositivo/), 'Teléfono')
    await user.type(screen.getByLabelText(/Qué cambiarías/), 'Me gustaría encontrar ayuda junto al visor.')
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Enviar evaluación' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Tus respuestas siguen aquí')
    await user.click(screen.getByRole('button', { name: 'Enviar evaluación' }))
    expect(await screen.findByRole('status')).toHaveTextContent('número 17')
    const first = sendEvaluation.mock.calls[0][0]
    expect(first).toMatchObject({ version: 'insoft-nielsen-v1', pagina: '/courses/1/subtopics/2', dispositivo: 'Teléfono' })
    expect(Object.keys(first.respuestas)).toHaveLength(10)
    expect(sendEvaluation.mock.calls[1][0]).toEqual(first)
    expect(first).not.toHaveProperty('user_id')
  })

  it('no cuenta una entrega con todas las preguntas sin probar', async () => {
    const user = userEvent.setup()
    show()
    await fillSurvey(user, true)
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Enviar evaluación' }))
    expect(screen.getByRole('alert')).toHaveTextContent('al menos una experiencia')
    expect(sendEvaluation).not.toHaveBeenCalled()
  })
})
