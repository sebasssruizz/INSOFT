import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const MODEL_URL = '/models/Prueba_12.glb'

export default function InteractiveViewPage() {
  const { courseId, subtopicId } = useParams()
  const canvasRef = useRef(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return undefined

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#0a195c')

    const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000)
    camera.position.set(3.8, 2.8, 5.2)

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
    })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.15
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap

    const controls = new OrbitControls(camera, canvas)
    controls.enableDamping = true
    controls.dampingFactor = 0.06
    controls.minDistance = 0.5
    controls.maxDistance = 20
    controls.target.set(0, 0.8, 0)

    scene.add(new THREE.HemisphereLight(0xd5e9ff, 0x0a195c, 2.0))

    const keyLight = new THREE.DirectionalLight(0xffffff, 3.5)
    keyLight.position.set(4, 8, 5)
    keyLight.castShadow = true
    keyLight.shadow.mapSize.set(2048, 2048)
    scene.add(keyLight)

    const fillLight = new THREE.DirectionalLight(0x568eff, 1.6)
    fillLight.position.set(-5, 3, -4)
    scene.add(fillLight)

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(12, 64),
      new THREE.MeshStandardMaterial({
        color: 0x0b1a4d,
        roughness: 0.88,
        metalness: 0.08,
      }),
    )
    floor.rotation.x = -Math.PI / 2
    floor.position.y = -0.02
    floor.receiveShadow = true
    scene.add(floor)

    const grid = new THREE.GridHelper(20, 40, 0x2f65ff, 0x102d9f)
    grid.position.y = -0.01
    grid.material.transparent = true
    grid.material.opacity = 0.38
    scene.add(grid)

    let animationFrame
    let disposed = false

    const resize = () => {
      const { clientWidth, clientHeight } = canvas.parentElement
      camera.aspect = clientWidth / clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(clientWidth, clientHeight, false)
    }

    const loader = new GLTFLoader()
    loader.load(
      MODEL_URL,
      (gltf) => {
        if (disposed) return

        const model = gltf.scene
        model.traverse((object) => {
          if (!object.isMesh) return
          object.castShadow = true
          object.receiveShadow = true
          if (object.material) object.material.needsUpdate = true
        })

        const bounds = new THREE.Box3().setFromObject(model)
        const center = bounds.getCenter(new THREE.Vector3())
        const size = bounds.getSize(new THREE.Vector3())
        const maxDimension = Math.max(size.x, size.y, size.z)
        const scale = maxDimension > 0 ? 3.6 / maxDimension : 1

        model.position.sub(center)
        model.scale.setScalar(scale)
        model.position.y += 0.04
        scene.add(model)

        controls.target.set(0, Math.max(size.y * scale * 0.35, 0.35), 0)
        controls.update()
        setStatus('ready')
      },
      undefined,
      () => {
        if (!disposed) setStatus('error')
      },
    )

    const animate = () => {
      animationFrame = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }

    resize()
    window.addEventListener('resize', resize)
    animate()

    return () => {
      disposed = true
      cancelAnimationFrame(animationFrame)
      window.removeEventListener('resize', resize)
      controls.dispose()
      renderer.dispose()
      scene.traverse((object) => {
        if (!object.isMesh) return
        object.geometry.dispose()
        if (Array.isArray(object.material))
          object.material.forEach((material) => material.dispose())
        else object.material.dispose()
      })
    }
  }, [])

  return (
    <main className="fixed inset-0 overflow-hidden bg-blue-950 text-white">
      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full"
        aria-label="Mesa quirúrgica interactiva en 3D"
      />

      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_35%,transparent_20%,rgba(6,10,32,0.5)_100%)]" />

      <header className="pointer-events-none absolute left-0 right-0 top-0 flex items-start justify-between gap-4 bg-gradient-to-b from-blue-950/95 to-transparent px-5 py-5 sm:px-8 sm:py-7">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-300">
            Vista interactiva
          </p>
          <h1 className="mt-1 font-display text-xl font-semibold text-white sm:text-2xl">
            Armado de la mesa quirúrgica
          </h1>
          <p className="mt-1 text-xs text-blue-200 sm:text-sm">
            Arrastra para rotar · rueda para acercar
          </p>
        </div>
        <Link
          to={`/courses/${courseId}/subtopics/${subtopicId}`}
          className="pointer-events-auto rounded-lg border border-white/20 bg-blue-950/60 px-3 py-2 text-xs font-semibold text-white backdrop-blur transition-colors hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
        >
          Salir de la vista
        </Link>
      </header>

      {status === 'loading' && (
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-lg border border-white/10 bg-blue-950/80 px-4 py-3 text-sm text-blue-100 backdrop-blur">
          Cargando modelo 3D…
        </div>
      )}

      {status === 'error' && (
        <div className="absolute left-1/2 top-1/2 w-[min(90%,28rem)] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-wrong-200/30 bg-blue-950/85 px-5 py-4 text-center text-sm text-wrong-50 backdrop-blur">
          No se pudo cargar la mesa quirúrgica interactiva.
        </div>
      )}

      <div className="pointer-events-none absolute bottom-5 left-5 rounded-lg border border-white/10 bg-blue-950/60 px-3 py-2 text-[11px] text-blue-200 backdrop-blur sm:bottom-7 sm:left-8">
        Modelo: Prueba_12.glb
      </div>
    </main>
  )
}
