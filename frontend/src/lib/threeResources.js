// Models own their GPU resources. Clones used for inspection share those
// resources and must be cleared before their owning model is disposed.
export function disposeModel(root) {
  const geometries = new Set()
  const materials = new Set()
  const textures = new Set()
  const images = new Set()
  root.traverse((object) => {
    if (object.geometry) geometries.add(object.geometry)
    for (const material of [object.material].flat().filter(Boolean)) {
      materials.add(material)
      for (const value of Object.values(material)) {
        if (value?.isTexture) textures.add(value)
      }
    }
    if (object.skeleton?.boneTexture) textures.add(object.skeleton.boneTexture)
  })
  for (const geometry of geometries) geometry.dispose()
  for (const material of materials) material.dispose()
  for (const texture of textures) {
    texture.dispose()
    for (const image of [texture.source?.data].flat().filter(Boolean)) images.add(image)
  }
  for (const image of images) image.close?.()
}
