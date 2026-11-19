import { beforeEach, expect, it, vi } from 'vitest'
import { act, render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter } from 'react-router-dom'

import AiChatWidget from './AiChatWidget'
import { askAi, getAiConversation, rateAiAnswer } from '../services/aiService'

vi.mock('../services/aiService', () => ({ askAi: vi.fn(), getAiConversation: vi.fn(), rateAiAnswer: vi.fn() }))
vi.mock('../services/contentService', () => ({
  getCourseTopics: vi.fn().mockResolvedValue([{ id: 2, name: 'UNIDAD 2. Pterigión', subtopics: [{ id: 3, name: 'Instrumentación' }] }]),
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { role: 'STUDENT', name: 'Estudiante' } }),
}))

beforeEach(() => {
  sessionStorage.clear()
  vi.clearAllMocks()
  HTMLElement.prototype.scrollTo = vi.fn()
  vi.stubGlobal('matchMedia', () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
  askAi.mockResolvedValue({ respuesta: 'Respuesta fundamentada', query_id: 10, chunks_usados: 1,
    sources: [{ number: 1, subtopic_id: 3, title: 'Instrumentación', excerpt: 'Material oficial' }] })
  getAiConversation.mockResolvedValue([])
  rateAiAnswer.mockImplementation(async (_id, feedback) => ({ feedback }))
})

it('envía la unidad y mantiene la sesión hasta iniciar otra conversación', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/courses/1/units/2']}><AiChatWidget /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' }))
  const input = screen.getByRole('textbox', { name: 'Tu pregunta para Sofía' })
  await user.type(input, 'Explícame esto')
  await user.click(screen.getByRole('button', { name: 'Enviar pregunta' }))
  expect(await screen.findByText('Respuesta fundamentada')).toBeVisible()
  const firstSession = askAi.mock.calls[0][3].session_id
  expect(askAi).toHaveBeenLastCalledWith('Explícame esto', 1, null, expect.objectContaining({ topic_id: 2, session_id: firstSession }))
  await user.type(input, '¿Y sus cuidados?')
  await user.click(screen.getByRole('button', { name: 'Enviar pregunta' }))
  await waitFor(() => expect(askAi).toHaveBeenCalledTimes(2))
  expect(askAi.mock.calls[1][3].session_id).toBe(firstSession)
  await user.click(screen.getByRole('button', { name: 'Nueva conversación' }))
  expect(screen.queryByText('Respuesta fundamentada')).not.toBeInTheDocument()
  await user.type(input, 'Una nueva duda')
  await user.click(screen.getByRole('button', { name: 'Enviar pregunta' }))
  await waitFor(() => expect(askAi).toHaveBeenCalledTimes(3))
  expect(askAi.mock.calls[2][3].session_id).not.toBe(firstSession)
})

it('restaura historial y valoraciones al recargar', async () => {
  const id = crypto.randomUUID()
  sessionStorage.setItem('sofia:conversation:anonymous:1', id)
  getAiConversation.mockResolvedValue([{ id: 20, question: 'Duda previa', answer: 'Respuesta previa', course_id: 1,
    subtopic_id: 3, sources: [], feedback: { helpful: true } }])
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/courses/1/subtopics/3']}><AiChatWidget /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' }))
  expect(await screen.findByText('Respuesta previa')).toBeVisible()
  expect(screen.getByText('Duda previa')).toBeVisible()
  expect(getAiConversation).toHaveBeenCalledWith(id, 1)
  expect(screen.getByRole('button', { name: '✓ Me sirvió' })).toHaveAttribute('aria-pressed', 'true')
})

it('permite reportar contexto incorrecto y consultar la fuente', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/courses/1/subtopics/3']}><AiChatWidget /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' }))
  await user.type(screen.getByRole('textbox', { name: 'Tu pregunta para Sofía' }), 'Mi duda')
  await user.click(screen.getByRole('button', { name: 'Enviar pregunta' }))
  await user.click(await screen.findByRole('button', { name: 'No me sirvió' }))
  await user.type(screen.getByRole('textbox', { name: 'Comentario de la valoración' }), 'Se refiere a otra cirugía')
  await user.click(screen.getByRole('button', { name: 'Guardar valoración' }))
  expect(await screen.findByText('Valoración guardada. Puedes cambiarla.')).toBeVisible()
  expect(rateAiAnswer).toHaveBeenCalledWith(10, { helpful: false, reason: 'context', comment: 'Se refiere a otra cirugía' })
  await user.click(screen.getByText('Fuentes consultadas'))
  expect(screen.getByRole('link', { name: '[1] Instrumentación' })).toHaveAttribute('href', '/courses/1/subtopics/3')
})

it('muestra fuentes del temario desde el inicio con enlace al curso', async () => {
  askAi.mockResolvedValue({ respuesta: 'Aprenderás los temas del curso.', query_id: 11, chunks_usados: 0,
    sources: [{ number: 1, course_id: 1, subtopic_id: null, title: 'Temario del curso', excerpt: 'Unidades habilitadas' }] })
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/dashboard']}><AiChatWidget /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' }))
  await user.click(screen.getByRole('button', { name: '¿Qué voy a aprender en el curso?' }))
  await user.click(await screen.findByText('Fuentes consultadas'))
  expect(screen.getByRole('link', { name: '[1] Temario del curso' })).toHaveAttribute('href', '/courses/1')
})

it('usa el fragmento seleccionado y descarta respuestas pendientes de otro curso', async () => {
  let finish
  askAi.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve }))
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/courses/1/subtopics/3']}>
    <Link to="/courses/2/subtopics/4">Otro curso</Link><AiChatWidget />
  </MemoryRouter>)
  act(() => window.dispatchEvent(new CustomEvent('sofia:selection', {
    detail: { courseId: 1, subtopicId: 3, text: 'Westcott para disección' },
  })))
  expect(await screen.findByText('Fragmento seleccionado: Westcott para disección')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Enviar pregunta' }))
  expect(askAi.mock.calls[0][3].selected_text).toBe('Westcott para disección')
  await user.click(screen.getByRole('link', { name: 'Otro curso' }))
  await act(async () => finish({ respuesta: 'Respuesta del curso anterior', chunks_usados: 1 }))
  expect(screen.queryByText('Respuesta del curso anterior')).not.toBeInTheDocument()
  expect(screen.queryByText('Fragmento seleccionado: Westcott para disección')).not.toBeInTheDocument()
})

it.each([true, false])('abre y cierra el chat desde Sofía (escritorio: %s)', async (desktop) => {
  vi.stubGlobal('matchMedia', () => ({
    matches: desktop,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }))
  const user = userEvent.setup()
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><AiChatWidget /></MemoryRouter>)

  const launcher = screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' })
  expect(within(launcher).getByText('Hazme una pregunta')).toBeVisible()
  expect(launcher.querySelector('img')).toHaveAttribute('src', '/brand/sofia-asistente.webp')
  await user.click(launcher)

  expect(screen.getByRole('dialog', { name: 'Sofía, asistente de IA' })).toBeVisible()
  expect(screen.getByRole('textbox', { name: 'Tu pregunta para Sofía' })).toBeVisible()
  await user.type(screen.getByRole('textbox', { name: 'Tu pregunta para Sofía' }), 'Mi pregunta')
  await user.click(screen.getByRole('button', { name: 'Cerrar el chat' }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Hablar con Sofía, la asistente de IA' }))
  expect(screen.getByRole('textbox', { name: 'Tu pregunta para Sofía' })).toHaveValue('Mi pregunta')
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})
