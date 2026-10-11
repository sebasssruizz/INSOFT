// Verifica que el build de producción no contenga rastros de desarrollo ni de
// configuración local. Falla (exit 1) si encuentra alguna cadena prohibida.
// Uso: node scripts/check-dist.mjs [carpeta]   (por defecto ./dist)
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'

const FORBIDDEN = [
  'localhost:8000', // backend local por defecto (solo debe existir en desarrollo)
  '/auth/dev', // endpoint de acceso de desarrollo
  'profesor@demo.com', // cuentas de demostración del login de desarrollo
  'estudiante@demo.com',
]

const root = process.argv[2] ?? 'dist'
const SCANNED = new Set(['.js', '.mjs', '.css', '.html', '.json', '.map', '.txt'])

function* files(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) yield* files(path)
    else yield path
  }
}

let scanned = 0
const hits = []
try {
  for (const path of files(root)) {
    if (!SCANNED.has(extname(path))) continue
    scanned += 1
    const text = readFileSync(path, 'utf8')
    for (const needle of FORBIDDEN) {
      if (text.includes(needle)) hits.push(`${path}: contiene "${needle}"`)
    }
  }
} catch (error) {
  console.error(`No se pudo leer ${root}: ${error.message}. ¿Ejecutaste el build?`)
  process.exit(1)
}

if (scanned === 0) {
  console.error(`${root} no contiene archivos que revisar. ¿Ejecutaste el build?`)
  process.exit(1)
}

if (hits.length > 0) {
  console.error('El bundle de producción contiene cadenas prohibidas:')
  for (const hit of hits) console.error(`  - ${hit}`)
  process.exit(1)
}

console.log(`check-dist: ${scanned} archivos revisados, sin cadenas prohibidas.`)
