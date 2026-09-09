import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'

import { cn } from '../../lib/utils'

/**
 * Genera la textura del iris por código (fibras radiales + collarete), en la
 * escala azul de marca. Evita descargar cualquier imagen.
 */
function createIrisTexture() {
  const size = 512
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  const center = size / 2

  const base = ctx.createRadialGradient(center, center, size * 0.08, center, center, center)
  base.addColorStop(0, '#0a195c')
  base.addColorStop(0.32, '#062acd')
  base.addColorStop(0.62, '#2f65ff')
  base.addColorStop(0.88, '#102d9f')
  base.addColorStop(1, '#0b0f1a')
  ctx.fillStyle = base
  ctx.fillRect(0, 0, size, size)

  // Fibras radiales del estroma.
  ctx.lineCap = 'round'
  for (let i = 0; i < 220; i += 1) {
    const angle = (i / 220) * Math.PI * 2 + Math.random() * 0.02
    const inner = center * (0.24 + Math.random() * 0.08)
    const outer = center * (0.72 + Math.random() * 0.26)
    ctx.beginPath()
    ctx.moveTo(center + Math.cos(angle) * inner, center + Math.sin(angle) * inner)
    ctx.lineTo(center + Math.cos(angle) * outer, center + Math.sin(angle) * outer)
    ctx.strokeStyle = i % 3 === 0 ? 'rgba(133,183,255,0.30)' : 'rgba(10,25,92,0.34)'
    ctx.lineWidth = 0.6 + Math.random() * 1.9
    ctx.stroke()
  }

  // Collarete: el anillo que separa la zona pupilar de la ciliar.
  ctx.beginPath()
  ctx.arc(center, center, center * 0.34, 0, Math.PI * 2)
  ctx.strokeStyle = 'rgba(181,214,255,0.35)'
  ctx.lineWidth = 7
  ctx.stroke()

  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  texture.anisotropy = 4
  return texture
}

/**
 * Ojo anatómico procedural: esclera, iris con fibras, pupila y córnea con
 * transmisión real. Sigue al puntero dentro de un rango contenido y se detiene
 * cuando sale de pantalla, cuando la pestaña se oculta o si el usuario ha
 * pedido reducir el movimiento.
 */
export default function EyeScene({ className, interactive = true }) {
  const containerRef = useRef(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100)
    camera.position.set(0, 0, 6.4)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 0.92
    container.appendChild(renderer.domElement)
    renderer.domElement.style.display = 'block'
    renderer.domElement.style.width = '100%'
    renderer.domElement.style.height = '100%'

    // Entorno procedural: da reflejos creíbles a la córnea sin cargar un HDRI.
    const pmrem = new THREE.PMREMGenerator(renderer)
    const environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
    scene.environment = environment
    scene.environmentIntensity = 0.55

    const eye = new THREE.Group()
    scene.add(eye)

    // Radio angular de la abertura por donde asoma el iris.
    const APERTURE = 0.44
    const EYE_RADIUS = 1.5
    const irisZ = EYE_RADIUS * Math.cos(APERTURE)
    const irisRadius = EYE_RADIUS * Math.sin(APERTURE)

    // Esclera abierta por delante: sin el casquete polar, el iris no queda
    // sepultado dentro de la esfera.
    const sclera = new THREE.Mesh(
      new THREE.SphereGeometry(EYE_RADIUS, 64, 64, 0, Math.PI * 2, APERTURE, Math.PI - APERTURE),
      new THREE.MeshPhysicalMaterial({
        color: 0xeef2fa,
        roughness: 0.38,
        clearcoat: 0.5,
        clearcoatRoughness: 0.3,
        sheen: 0.35,
        sheenColor: new THREE.Color(0xb3d4ff),
        side: THREE.DoubleSide,
      }),
    )
    sclera.rotation.x = Math.PI / 2
    eye.add(sclera)

    const irisTexture = createIrisTexture()
    const iris = new THREE.Mesh(
      new THREE.CircleGeometry(irisRadius * 1.02, 96),
      new THREE.MeshPhysicalMaterial({
        map: irisTexture,
        roughness: 0.4,
        metalness: 0.1,
        clearcoat: 1,
        clearcoatRoughness: 0.06,
      }),
    )
    iris.position.z = irisZ - 0.015
    eye.add(iris)

    const pupil = new THREE.Mesh(
      new THREE.CircleGeometry(irisRadius * 0.31, 64),
      new THREE.MeshBasicMaterial({ color: 0x04060f }),
    )
    pupil.position.z = irisZ
    eye.add(pupil)

    // Casquete corneal: esfera recortada con transmisión sobre el iris.
    const cornea = new THREE.Mesh(
      new THREE.SphereGeometry(1.56, 64, 64, 0, Math.PI * 2, 0, APERTURE * 1.28),
      new THREE.MeshPhysicalMaterial({
        transmission: 1,
        thickness: 0.5,
        ior: 1.376,
        roughness: 0.03,
        clearcoat: 1,
        clearcoatRoughness: 0,
        transparent: true,
        side: THREE.DoubleSide,
      }),
    )
    cornea.rotation.x = Math.PI / 2
    eye.add(cornea)

    scene.add(new THREE.HemisphereLight(0xd5e9ff, 0x0a195c, 0.9))

    const key = new THREE.DirectionalLight(0xffffff, 1.9)
    key.position.set(3.2, 4.2, 5)
    scene.add(key)

    const rim = new THREE.DirectionalLight(0x568eff, 1.4)
    rim.position.set(-4, -1.5, -3)
    scene.add(rim)

    const pointer = new THREE.Vector2(0, 0)
    const target = new THREE.Vector2(0, 0)

    const onPointerMove = (event) => {
      const rect = container.getBoundingClientRect()
      // Normalizado al viewport: el ojo sigue al cursor por toda la página.
      target.x = (event.clientX - (rect.left + rect.width / 2)) / window.innerWidth
      target.y = (event.clientY - (rect.top + rect.height / 2)) / window.innerHeight
    }

    if (interactive && !prefersReduced) {
      window.addEventListener('pointermove', onPointerMove, { passive: true })
    }

    const resize = () => {
      const { clientWidth, clientHeight } = container
      if (!clientWidth || !clientHeight) return
      camera.aspect = clientWidth / clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(clientWidth, clientHeight, false)
    }

    const resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(container)
    resize()

    let frame = null
    let visible = true
    const clock = new THREE.Clock()

    const render = () => {
      const elapsed = clock.getElapsedTime()

      // Amortiguación hacia la mirada objetivo, más una deriva lenta de reposo.
      pointer.x += (target.x - pointer.x) * 0.055
      pointer.y += (target.y - pointer.y) * 0.055

      const idleX = prefersReduced ? 0 : Math.sin(elapsed * 0.42) * 0.06
      const idleY = prefersReduced ? 0 : Math.cos(elapsed * 0.31) * 0.04

      eye.rotation.y = pointer.x * 1.05 + idleX
      eye.rotation.x = pointer.y * 0.75 + idleY

      renderer.render(scene, camera)
    }

    const loop = () => {
      frame = requestAnimationFrame(loop)
      render()
    }

    const start = () => {
      if (frame === null && visible) loop()
    }
    const stop = () => {
      if (frame !== null) {
        cancelAnimationFrame(frame)
        frame = null
      }
    }

    // Solo se anima si está en pantalla y la pestaña está activa.
    const intersectionObserver = new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting
        if (visible) start()
        else stop()
      },
      { threshold: 0.05 },
    )
    intersectionObserver.observe(container)

    const onVisibility = () => {
      if (document.hidden) stop()
      else start()
    }
    document.addEventListener('visibilitychange', onVisibility)

    if (prefersReduced) {
      render()
    } else {
      start()
    }
    setReady(true)

    return () => {
      stop()
      intersectionObserver.disconnect()
      resizeObserver.disconnect()
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('pointermove', onPointerMove)
      irisTexture.dispose()
      environment.dispose()
      pmrem.dispose()
      scene.traverse((object) => {
        if (!object.isMesh) return
        object.geometry.dispose()
        const materials = Array.isArray(object.material) ? object.material : [object.material]
        materials.forEach((material) => material.dispose())
      })
      renderer.dispose()
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [interactive])

  return (
    <div
      ref={containerRef}
      role="img"
      aria-label="Modelo tridimensional de un ojo humano que sigue el movimiento del cursor"
      className={cn(
        'transition-opacity duration-700 ease-out',
        ready ? 'opacity-100' : 'opacity-0',
        className,
      )}
    />
  )
}
