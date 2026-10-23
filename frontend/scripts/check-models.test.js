import { afterEach, describe, expect, it } from 'vitest'
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { checkModels } from './check-models.mjs'

let dir
function fixture(data) {
  dir = mkdtempSync(join(tmpdir(), 'insoft-model-test-'))
  writeFileSync(join(dir, 'model.glb'), data)
  return checkModels(dir)
}
afterEach(() => { if (dir) rmSync(dir, { recursive: true }); dir = undefined })

describe('protección de assets del despliegue', () => {
  it('rechaza un puntero LFS sin descargar', () => {
    expect(fixture('version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 20\n').errors[0]).toContain('puntero LFS')
  })
  it('acepta una cabecera GLB coherente', () => {
    const glb = Buffer.alloc(24)
    glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(24, 8)
    expect(fixture(glb).errors).toEqual([])
  })
  it('rechaza un GLB cuya longitud no corresponde al archivo', () => {
    const glb = Buffer.alloc(24)
    glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(200, 8)
    expect(fixture(glb).errors[0]).toContain('truncado')
  })
})
