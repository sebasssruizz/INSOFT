import { describe, it, expect, vi } from 'vitest'
import * as THREE from 'three'
import { disposeModel } from './threeResources'

describe('model resource ownership', () => {
  it('releases shared geometry, materials, textures and bitmap once per owning model', () => {
    const root = new THREE.Group()
    const geometry = new THREE.BoxGeometry()
    const image = { close: vi.fn() }
    const texture = new THREE.Texture(image)
    const material = new THREE.MeshStandardMaterial({ map: texture, normalMap: texture })
    root.add(new THREE.Mesh(geometry, material), new THREE.Mesh(geometry, material))
    const gd = vi.spyOn(geometry, 'dispose')
    const md = vi.spyOn(material, 'dispose')
    const td = vi.spyOn(texture, 'dispose')
    disposeModel(root)
    expect(gd).toHaveBeenCalledTimes(1)
    expect(md).toHaveBeenCalledTimes(1)
    expect(td).toHaveBeenCalledTimes(1)
    expect(image.close).toHaveBeenCalledTimes(1)
  })
})
