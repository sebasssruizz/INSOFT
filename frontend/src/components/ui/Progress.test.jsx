import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ProgressRing } from './Progress'

describe('ProgressRing', () => {
  it('se anuncia como barra de progreso con nombre y valor', () => {
    render(<ProgressRing value={42} label="Progreso del curso" />)

    const bar = screen.getByRole('progressbar', { name: 'Progreso del curso' })
    expect(bar).toHaveAttribute('aria-valuenow', '42')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
  })

  it('usa "Progreso" como nombre por defecto', () => {
    render(<ProgressRing value={10} />)
    expect(screen.getByRole('progressbar', { name: 'Progreso' })).toBeInTheDocument()
  })

  it('limita el valor entre 0 y 100', () => {
    const { rerender } = render(<ProgressRing value={150} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')

    rerender(<ProgressRing value={-5} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
  })

  it('muestra el contenido visible (cifra) dentro del anillo', () => {
    render(
      <ProgressRing value={50} label="Avance">
        <span>50%</span>
      </ProgressRing>,
    )
    expect(screen.getByText('50%')).toBeInTheDocument()
  })
})
