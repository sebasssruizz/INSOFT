import { useState } from 'react'
import { Link } from 'react-router-dom'
import { faArrowLeft, faLayerGroup } from '@fortawesome/free-solid-svg-icons'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'
import { useAuth } from '../hooks/useAuth'
import { cn } from '../lib/utils'

/**
 * Carta de Snellen. La primera línea es el error; las siguientes esconden un
 * mensaje que solo se lee al "acomodar la vista": las dos últimas filas están
 * desenfocadas hasta que se pasa el cursor (o se enfoca) sobre la carta.
 */
const CHART = [
  { text: '404', acuity: '20/200', size: 'text-[4.5rem] sm:text-[6rem]', blur: false },
  { text: 'NO', acuity: '20/100', size: 'text-[2.25rem] sm:text-[2.75rem]', blur: false },
  { text: 'ESTÁ', acuity: '20/70', size: 'text-[1.625rem] sm:text-[2rem]', blur: false },
  { text: 'AQUÍ', acuity: '20/50', size: 'text-[1.25rem] sm:text-[1.5rem]', blur: true },
  { text: 'VUELVE', acuity: '20/40', size: 'text-[0.9375rem] sm:text-[1.0625rem]', blur: true },
]

export default function NotFoundPage() {
  const { isAuthenticated } = useAuth()
  // En pantallas táctiles no hay cursor: un toque enfoca la carta.
  const [focused, setFocused] = useState(false)

  return (
    <main className="flex min-h-screen flex-col bg-ink-50">
      <header className="mx-auto flex h-20 w-full max-w-[78rem] items-center px-5 sm:px-6 lg:px-10">
        <Link to="/" aria-label="Ir al inicio de INSOFT">
          <Logo size="md" />
        </Link>
      </header>

      <div className="mx-auto grid w-full max-w-[64rem] flex-1 items-center gap-12 px-5 pb-16 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-16 lg:px-10">
        {/* La carta es decorativa: el mensaje real está en el texto de al lado. */}
        <div
          aria-hidden="true"
          onClick={() => setFocused((value) => !value)}
          className="group mx-auto w-full max-w-[22rem] cursor-default select-none rounded-xl border border-ink-200 bg-white px-6 py-8 shadow-e2 transition-shadow duration-300 hover:shadow-e3 sm:px-8"
        >
          <ol className="space-y-4">
            {CHART.map((row, index) => (
              <li
                key={row.text}
                className="grid grid-cols-[3.25rem_1fr] items-center gap-3 animate-focus-in"
                style={{ animationDelay: `${index * 140}ms` }}
              >
                <span className="tabular text-[0.625rem] font-semibold text-ink-400">
                  {row.acuity}
                </span>
                <span
                  className={cn(
                    'text-center font-bold leading-none text-ink-900 transition-[filter,opacity] duration-500 ease-out',
                    row.size,
                    index === 0 ? 'tracking-[0.12em]' : 'tracking-[0.32em]',
                    row.blur &&
                      (focused
                        ? 'opacity-100 blur-0'
                        : 'opacity-70 blur-[2.5px] group-hover:opacity-100 group-hover:blur-0'),
                  )}
                >
                  {row.text}
                </span>
              </li>
            ))}
          </ol>

          {/* Prueba duocromática: la franja roja y verde del final de la carta. */}
          <div className="mt-8 grid grid-cols-2 overflow-hidden rounded-md">
            <span className="h-2 bg-wrong-500/80" />
            <span className="h-2 bg-correct-500/80" />
          </div>
          <p className="mt-3 text-center text-[0.6875rem] text-ink-400 transition-colors duration-300 group-hover:text-ink-500">
            Pasa el cursor o toca la carta para enfocar
          </p>
        </div>

        <div className="text-center lg:text-left">
          <p className="eyebrow text-blue-900">Error 404</p>
          <h1 className="mt-3 text-[1.75rem] font-bold leading-[1.15] tracking-[-0.02em] text-ink-900 sm:text-[2.25rem]">
            Esta página está fuera de foco
          </h1>
          <p className="mx-auto mt-4 max-w-[44ch] text-[0.9375rem] leading-relaxed text-ink-600 lg:mx-0">
            La dirección que abriste no corresponde a ninguna sección de INSOFT. Puede que el enlace
            haya cambiado o que falte una letra. Vuelve a un lugar conocido y sigue donde ibas.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center lg:justify-start">
            <Button as={Link} to="/" icon={faArrowLeft} className="w-full sm:w-auto">
              Volver al inicio
            </Button>
            {isAuthenticated && (
              <Button
                as={Link}
                to="/dashboard"
                variant="secondary"
                icon={faLayerGroup}
                className="w-full sm:w-auto"
              >
                Ir a mis cursos
              </Button>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
