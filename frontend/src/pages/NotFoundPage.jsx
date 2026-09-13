import { Link } from 'react-router-dom'

import Logo from '../components/Logo'
import { Button } from '../components/ui/Button'

export default function NotFoundPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-soft-sky via-ink-50 to-soft-peach px-6 text-center">
      <div className="relative">
        <Logo size="lg" className="justify-center" />

        <p className="tabular mt-14 font-display text-[7rem] font-semibold leading-none text-blue-900">
          404
        </p>
        <h1 className="mt-4 text-[1.75rem] font-semibold tracking-[-0.02em] text-ink-900">
          Esta página no existe
        </h1>
        <p className="mx-auto mt-3 max-w-[42ch] text-[0.9375rem] leading-relaxed text-ink-600">
          La dirección que has abierto no corresponde a ninguna sección de INSOFT.
        </p>

        <Button as={Link} to="/" className="mt-9">
          Volver al inicio
        </Button>
      </div>
    </main>
  )
}
