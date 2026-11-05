import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import AiChatWidget from './AiChatWidget'

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { role: 'STUDENT', name: 'Estudiante' } }),
}))

beforeEach(() => {
  HTMLElement.prototype.scrollTo = vi.fn()
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
