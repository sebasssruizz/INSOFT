import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StudentDashboard from './StudentDashboard'

vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })))

const fixture = vi.hoisted(() => ({ courses: [] }))
vi.mock('../hooks/useAuth', () => ({ useAuth: () => ({ user: { name: 'Prueba', role: 'STUDENT' } }) }))
vi.mock('../hooks/useCourses', () => ({ useCourses: () => ({ courses: fixture.courses, loading: false, error: null, refresh: vi.fn() }) }))
vi.mock('../services/contentService', () => ({ getCourseTopics: vi.fn().mockResolvedValue([
  { id: 1, order: 1, name: 'Unidad 1 · Introducción', subtopics: [
    { id: 7, name: 'Primer subtema', completed: false, question_count: 3 },
  ] },
]) }))

describe('Dashboard después de integración de ramas', () => {
  it('conserva siguiente lectura, preguntas, progreso y navegación del curso', async () => {
    fixture.courses = [{ id: 4, name: 'Curso de prueba', type: 'GENERAL', progress_percentage: 25,
      completed_subtopics: 1, total_subtopics: 4, total_units: 1 }]
    render(<MemoryRouter><StudentDashboard /></MemoryRouter>)
    expect(await screen.findByText('Sigue:')).toBeInTheDocument()
    expect(screen.getByText('3 preguntas de repaso')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Continuar|Empezar/ })).toHaveAttribute('href', '/courses/4/subtopics/7')
    expect(screen.getByRole('progressbar', { name: 'Progreso' })).toHaveAttribute('aria-valuenow', '25')
  })

  it('conserva el indicador de curso completado', async () => {
    fixture.courses = [{ id: 4, name: 'Curso completo', type: 'GENERAL', progress_percentage: 100,
      completed_subtopics: 4, total_subtopics: 4, total_units: 1 }]
    render(<MemoryRouter><StudentDashboard /></MemoryRouter>)
    expect(await screen.findByLabelText('Curso completado')).toBeInTheDocument()
  })
})
