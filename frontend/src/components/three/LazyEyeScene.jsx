import { Suspense, lazy } from 'react'

import { cn } from '../../lib/utils'

// three.js pesa más que todo el resto de la aplicación junta: se carga aparte,
// después de que la página ya sea usable.
const EyeScene = lazy(() => import('./EyeScene'))

/** Hueco del mismo tamaño mientras llega el módulo 3D, sin salto de layout. */
function EyePlaceholder({ className }) {
  return (
    <div className={cn('flex items-center justify-center', className)} aria-hidden="true">
      <span className="h-[62%] w-[62%] animate-pulse rounded-full bg-white/5" />
    </div>
  )
}

export default function LazyEyeScene({ className, ...props }) {
  return (
    <Suspense fallback={<EyePlaceholder className={className} />}>
      <EyeScene className={className} {...props} />
    </Suspense>
  )
}
