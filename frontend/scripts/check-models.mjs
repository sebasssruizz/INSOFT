// Impide publicar punteros LFS o GLB truncados en lugar de modelos reales.
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

export function checkModels(root) {
  let count = 0
  const errors = []
  function scan(dir) {
    for (const entry of readdirSync(dir)) {
      const path = join(dir, entry)
      if (statSync(path).isDirectory()) scan(path)
      else if (path.endsWith('.glb')) {
        count += 1
        const data = readFileSync(path)
        if (data.subarray(0, 42).toString().startsWith('version https://git-lfs.github.com/spec/v1')) {
          errors.push(`${path}: puntero LFS sin descargar`)
        } else if (data.length < 20 || data.toString('ascii', 0, 4) !== 'glTF' ||
                   data.readUInt32LE(4) !== 2 || data.readUInt32LE(8) !== data.length) {
          errors.push(`${path}: cabecera GLB inválida o archivo truncado`)
        }
      }
    }
  }
  scan(root)
  if (!count) errors.push('No hay modelos GLB en el directorio esperado')
  return { count, errors }
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const { count, errors } = checkModels(process.argv[2] || 'public/models')
  if (errors.length) {
    console.error(errors.join('\n'))
    console.error('Recupera los binarios con Git LFS antes de publicar; no sustituirlos por modelos vacíos.')
    process.exitCode = 1
  } else console.log(`check-models: ${count} modelos con cabecera GLB válida.`)
}
