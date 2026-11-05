import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import FeedbackWidget from './FeedbackWidget'

vi.mock('../hooks/useAuth', () => ({ useAuth: () => ({ user: { role: 'STUDENT' } }) }))

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }
})

it('permite elegir la evaluación y continuar directamente a Google Forms', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><FeedbackWidget /></MemoryRouter>)

  await user.click(screen.getByRole('button', { name: 'Comentarios / PQRS' }))
  expect(screen.getByLabelText('Comentario')).toBeVisible()
  await user.click(screen.getByRole('button', { name: /Evaluar página|Califica tu experiencia/ }))

  const start = screen.getByRole('link', { name: 'Comenzar evaluación' })
  expect(start).toHaveAttribute('href', 'https://forms.gle/aadYJxpfVMqrWvsk9')
  expect(start).not.toHaveAttribute('target', '_blank')
  expect(screen.queryByLabelText('Comentario')).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Agregar comentario' }))
  expect(screen.getByLabelText('Comentario')).toBeVisible()
  expect(screen.queryByRole('link', { name: 'Comenzar evaluación' })).not.toBeInTheDocument()
})
