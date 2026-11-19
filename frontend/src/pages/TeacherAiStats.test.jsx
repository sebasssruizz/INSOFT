import { expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import TeacherAiStats from './TeacherAiStats'
import { apiFetch } from '../services/api'

vi.mock('../hooks/useAuth', () => ({ useAuth: () => ({ user: { role: 'TEACHER' } }) }))
vi.mock('../services/api', () => ({ apiFetch: vi.fn(), downloadCsv: vi.fn() }))

it('carga las valoraciones y filtra las respuestas reportadas por contexto', async () => {
  apiFetch.mockImplementation(async (url) => {
    if (url.startsWith('/ai/history/all')) return [{ id: 1, question: '¿Qué estoy viendo?', answer: 'Respuesta',
      subtopic_id: 3, created_at: '2026-11-19T12:00:00Z',
      feedback: { helpful: false, reason: 'context', comment: 'Habló de otra cirugía' } }]
    if (url === '/ai/stats/subtopics') return { subtopics: [{ subtopic_id: 3, nombre: 'Instrumentación', total_preguntas: 1 }] }
    if (url === '/ai/stats/students') return { students: [] }
    return { total_preguntas: 1, preguntas_ultimos_7_dias: 1, tiempo_respuesta_promedio_ms: 100 }
  })
  const user = userEvent.setup()
  render(<MemoryRouter><TeacherAiStats /></MemoryRouter>)
  expect(await screen.findByText('Habló de otra cirugía')).toBeVisible()
  await user.click(screen.getByRole('checkbox', { name: 'Solo respuestas que no sirvieron' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Filtrar motivo de valoración' }), 'context')
  await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(expect.stringMatching(/history\/all\?.*feedback_only=true.*feedback_reason=context/)))
})
