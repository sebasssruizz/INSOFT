import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import FeedbackReviewPage from './FeedbackReviewPage'
import { getFeedbackAccess, getFeedbackReviews } from '../services/feedbackService'
import { downloadCsv } from '../services/api'
vi.mock('../services/feedbackService', () => ({ getFeedbackAccess: vi.fn(), getFeedbackReviews: vi.fn() }))
vi.mock('../services/api', () => ({ downloadCsv: vi.fn() }))
beforeEach(() => vi.clearAllMocks())
const show = () => render(<MemoryRouter><FeedbackReviewPage /></MemoryRouter>)
it('sin autorización no pide los datos ni ofrece descargar', async () => {
  getFeedbackAccess.mockResolvedValue({ can_review: false })
  show()
  expect(await screen.findByText(/Tu cuenta no tiene acceso/)).toBeInTheDocument()
  expect(getFeedbackReviews).not.toHaveBeenCalled()
  expect(screen.queryByRole('button', { name: 'Descargar todo (CSV)' })).not.toBeInTheDocument()
})
it('lee comentarios seguros, cambia a evaluaciones y descarga todo', async () => {
  getFeedbackAccess.mockResolvedValue({ can_review: true })
  getFeedbackReviews.mockResolvedValue({ total: 1, items: [{ id: 8, participante: 'P1', creado_en: '2026-10-24T12:00:00Z', pagina: '/dashboard', comentario: '<script>comentario</script>', tipo: 'Sugerencia', categoria: 'Otro', respuestas: { h10: null }, version: 'insoft-nielsen-v1' }] })
  downloadCsv.mockResolvedValue()
  const user = userEvent.setup()
  show()
  expect(await screen.findByText('<script>comentario</script>')).toBeInTheDocument()
  expect(document.querySelector('script')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Evaluaciones de uso' }))
  expect(await screen.findByText('Evaluación de uso #8')).toBeInTheDocument()
  await user.click(screen.getByText('Ver las 10 respuestas'))
  expect(screen.getAllByText('No probado / No aplica')).toHaveLength(10)
  await user.click(screen.getByRole('button', { name: 'Descargar todo (CSV)' }))
  expect(downloadCsv).toHaveBeenCalledWith('/feedback/export.csv', 'insoft-opiniones.csv')
})
