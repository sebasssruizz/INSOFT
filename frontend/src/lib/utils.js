/**
 * cn: une clases condicionales ignorando valores falsy.
 * Versión mínima sin dependencias (clsx/tailwind-merge) porque el proyecto
 * no usa la estructura shadcn. Si en el futuro se adopta shadcn/ui, sustituir
 * por `clsx` + `twMerge`.
 */
export function cn(...inputs) {
  return inputs.flat(Infinity).filter(Boolean).join(' ')
}
