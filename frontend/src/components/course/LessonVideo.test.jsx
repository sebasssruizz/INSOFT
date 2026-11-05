import { expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import LessonVideo from './LessonVideo'

it('ofrece el video de chalazión con controles y sin reproducir automáticamente', () => {
  render(<LessonVideo subtopicName="Drenaje de chalazión" />)
  const video = screen.getByLabelText('Video educativo: drenaje de chalazión')
  expect(video).toHaveAttribute('controls')
  expect(video).toHaveAttribute('playsinline')
  expect(video).not.toHaveAttribute('autoplay')
  expect(video.querySelector('source')).toHaveAttribute('src', '/videos/drenaje-chalazion.mp4')
})

it('no muestra el video en otros procedimientos ni mientras carga el subtema', () => {
  const { container, rerender } = render(<LessonVideo subtopicName="Resección de pterigión" />)
  expect(container.querySelector('video')).toBeNull()
  rerender(<LessonVideo />)
  expect(container.querySelector('video')).toBeNull()
})
