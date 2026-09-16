import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faComputerMouse,
  faGamepad,
  faHandPointer,
  faKeyboard,
  faPause,
  faPersonRunning,
  faPersonWalking,
} from '@fortawesome/free-solid-svg-icons'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const MODEL_URL = '/models/Prueba_12.glb'
const INITIAL_CAMERA = { x: -0.5, y: 5.18, z: -2.63 }
const TOOL_INFO = {
  blepharostat: {
    title: 'Blefaróstato Colibrí',
    eyebrow: 'Instrumental palpebral',
    description:
      'Separador autoestático utilizado para mantener los párpados abiertos y despejar el campo quirúrgico durante procedimientos oftalmológicos.',
    details: ['Facilita la exposición del globo ocular', 'Debe colocarse sin ejercer presión excesiva', 'Se revisa su limpieza y articulación antes del montaje'],
    modelUrl: encodeURI('/models/blefaróstato__B0001.glb'),
  },
  conjunctiveForceps: {
    title: 'Pinza conjuntiva',
    eyebrow: 'Instrumental de disección',
    description:
      'Pinza delicada para sujetar y manipular la conjuntiva y tejidos superficiales con precisión durante la cirugía oftalmológica.',
    details: ['Permite una sujeción atraumática', 'Sus puntas deben estar alineadas', 'Se utiliza con movimientos firmes y controlados'],
    modelUrl: encodeURI('/models/Pinza conjuntiva__B0002.glb'),
  },
}

function KeyCap({ children, className = '' }) {
  return (
    <span
      className={`inline-flex h-8 min-w-8 items-center justify-center rounded-md border border-white/20 bg-white/10 px-2 font-mono text-xs font-bold text-white shadow-[0_3px_0_rgba(0,0,0,0.28)] ${className}`}
    >
      {children}
    </span>
  )
}

export default function InteractiveViewPage() {
  const { courseId, subtopicId } = useParams()
  const canvasRef = useRef(null)
  const cameraReadoutRef = useRef(null)
  const startGameRef = useRef(() => {})
  const closeInspectionRef = useRef(() => {})
  const pauseGameRef = useRef(() => {})
  const joystickBaseRef = useRef(null)
  const joystickKnobRef = useRef(null)
  const runRef = useRef(false)
  const [status, setStatus] = useState('loading')
  const [paused, setPaused] = useState(true)
  const [hasStarted, setHasStarted] = useState(false)
  const [inspectedId, setInspectedId] = useState(null)
  const [running, setRunning] = useState(false)
  // Detección de pantalla táctil (móvil/tablet) para habilitar los controles
  // en pantalla en lugar de teclado y mouse.
  const [isTouchDevice] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches,
  )

  const toggleRun = () => {
    runRef.current = !runRef.current
    setRunning(runRef.current)
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return undefined

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#b8c5ca')

    const camera = new THREE.PerspectiveCamera(48, 1, 0.01, 1000)
    camera.position.set(INITIAL_CAMERA.x, INITIAL_CAMERA.y, INITIAL_CAMERA.z)
    camera.rotation.order = 'YXZ'
    camera.lookAt(0, 1, 0)

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isTouchDevice ? 1.75 : 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.05
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap

    const keys = new Set()
    // Entrada del joystick táctil: x = desplazamiento lateral, y = avance.
    const moveInput = { x: 0, y: 0 }
    const yaw = { value: camera.rotation.y }
    const pitch = { value: camera.rotation.x }
    const pausedRef = { value: true }
    const clock = new THREE.Clock()
    let animationFrame
    let disposed = false
    const roomGroup = new THREE.Group()
    const inspectionGroup = new THREE.Group()
    const inspection = { id: null, savedPosition: null, savedQuaternion: null }
    const interactiveMeshes = []
    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    const cameraTransition = { active: false }
    const mainModelRef = { current: null }
    const modelLoader = new GLTFLoader()
    const inspectionRef = { current: inspection }
    scene.add(roomGroup, inspectionGroup)
    inspectionGroup.visible = false

    const updateCameraRotation = () => {
      camera.rotation.set(pitch.value, yaw.value, 0)
    }

    const pauseGame = () => {
      pausedRef.value = true
      keys.clear()
      if (document.pointerLockElement === canvas) document.exitPointerLock()
      setPaused(true)
    }

    const startGame = () => {
      if (inspectionRef.current.id) return
      pausedRef.value = false
      setHasStarted(true)
      setPaused(false)
      if (!isTouchDevice) canvas.requestPointerLock?.()
    }
    startGameRef.current = startGame
    pauseGameRef.current = pauseGame

    const onKeyDown = (event) => {
      if (event.code === 'Escape') {
        pauseGame()
        return
      }

      // Durante la inspección de un objeto la cámara queda fija mirándolo.
      if (!pausedRef.value && !inspectionRef.current.id && ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight', 'ShiftLeft', 'ShiftRight'].includes(event.code)) {
        event.preventDefault()
        keys.add(event.code)
      }
    }

    const onKeyUp = (event) => keys.delete(event.code)

    const onMouseMove = (event) => {
      // Durante la inspección no se permite girar la vista: la cámara se
      // mantiene fija y es el objeto el que rota.
      if (pausedRef.value || inspectionRef.current.id || document.pointerLockElement !== canvas) return
      const sensitivity = 0.0022
      yaw.value -= event.movementX * sensitivity
      pitch.value -= event.movementY * sensitivity
      pitch.value = THREE.MathUtils.clamp(pitch.value, -Math.PI / 2.15, Math.PI / 2.15)
      updateCameraRotation()
    }

    const onPointerLockChange = () => {
      if (document.pointerLockElement !== canvas && !pausedRef.value && !inspectionRef.current.id) pauseGame()
    }

    const getInspectionQuaternion = (position, target) => {
      const lookCamera = new THREE.PerspectiveCamera()
      lookCamera.position.copy(position)
      lookCamera.lookAt(target)
      return lookCamera.quaternion.clone()
    }

    const transitionCamera = (position, quaternion) => {
      cameraTransition.active = true
      cameraTransition.elapsed = 0
      cameraTransition.duration = 720
      cameraTransition.fromPosition = camera.position.clone()
      cameraTransition.fromQuaternion = camera.quaternion.clone()
      cameraTransition.toPosition = position.clone()
      cameraTransition.toQuaternion = quaternion.clone()
    }

    const normalizeInspectionObject = (object) => {
      object.updateMatrixWorld(true)
      const wrapper = new THREE.Group()
      wrapper.add(object)
      wrapper.updateMatrixWorld(true)
      const bounds = new THREE.Box3().setFromObject(wrapper)
      const center = bounds.getCenter(new THREE.Vector3())
      const size = bounds.getSize(new THREE.Vector3())
      const maxDimension = Math.max(size.x, size.y, size.z)
      const scale = maxDimension > 0 ? 2.4 / maxDimension : 1
      wrapper.scale.setScalar(scale)
      wrapper.position.set(-center.x * scale, 0.95 - center.y * scale, -center.z * scale)
      return wrapper
    }

    const mountInspectionObject = (object) => {
      inspectionGroup.clear()
      object.updateMatrixWorld(true)
      const isolated = object.clone(true)
      isolated.applyMatrix4(object.matrixWorld)
      isolated.traverse((child) => {
        if (!child.isMesh) return
        child.castShadow = true
        child.receiveShadow = true
      })
      inspectionGroup.add(normalizeInspectionObject(isolated))
      inspectionGroup.visible = true
    }

    const resetTouchInput = () => {
      moveInput.x = 0
      moveInput.y = 0
      if (joystickKnobRef.current) joystickKnobRef.current.style.transform = 'translate(0px, 0px)'
    }

    const closeInspection = () => {
      if (!inspectionRef.current.id) return
      inspectionGroup.clear()
      inspectionGroup.visible = false
      if (mainModelRef.current) mainModelRef.current.visible = true
      roomGroup.visible = true
      const savedPosition = inspectionRef.current.savedPosition
      const savedQuaternion = inspectionRef.current.savedQuaternion
      inspectionRef.current.id = null
      setInspectedId(null)
      transitionCamera(savedPosition, savedQuaternion)
      pausedRef.value = false
      setPaused(false)
      resetTouchInput()
      if (!isTouchDevice) canvas.requestPointerLock?.()
    }
    closeInspectionRef.current = closeInspection

    const openInspection = (id, sourceObject) => {
      if (!TOOL_INFO[id]) return
      inspectionRef.current.id = id
      inspectionRef.current.savedPosition = camera.position.clone()
      inspectionRef.current.savedQuaternion = camera.quaternion.clone()
      setInspectedId(id)
      pauseGame()
      pausedRef.value = false
      setHasStarted(true)
      setPaused(false)
      resetTouchInput()
      // No se bloquea el puntero durante la inspección: la cámara queda fija y
      // el cursor debe poder llegar al botón "Volver a la sala".
      if (mainModelRef.current) mainModelRef.current.visible = false
      roomGroup.visible = false
      mountInspectionObject(sourceObject)

      // En móvil el panel de información ocupa la parte inferior, así que la
      // cámara se aleja y enfoca más abajo para que el objeto quede en la zona
      // superior visible mientras gira.
      const inspectionPosition = new THREE.Vector3(0, 1.55, isTouchDevice ? 7.2 : 6.2)
      const inspectionTarget = new THREE.Vector3(0, isTouchDevice ? -0.3 : 0.95, 0)
      transitionCamera(inspectionPosition, getInspectionQuaternion(inspectionPosition, inspectionTarget))

      // If the individual GLB is added later, use it automatically; otherwise keep the embedded mesh.
      modelLoader.load(TOOL_INFO[id].modelUrl, (gltf) => {
        if (!disposed && inspectionRef.current.id === id) mountInspectionObject(gltf.scene)
      }, undefined, () => {})
    }

    const inspectAt = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect()
      pointer.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1)
      raycaster.setFromCamera(pointer, camera)
      const hit = raycaster.intersectObjects(interactiveMeshes, true).find((item) => item.object.userData.inspectId)
      if (!hit) return false
      openInspection(hit.object.userData.inspectId, hit.object)
      return true
    }

    const onCanvasClick = (event) => {
      if (suppressClick || pausedRef.value || inspectionRef.current.id) return
      if (document.pointerLockElement === canvas) {
        pointer.set(0, 0)
        raycaster.setFromCamera(pointer, camera)
        const hit = raycaster.intersectObjects(interactiveMeshes, true).find((item) => item.object.userData.inspectId)
        if (hit) {
          openInspection(hit.object.userData.inspectId, hit.object)
          return
        }
      } else if (inspectAt(event.clientX, event.clientY)) {
        return
      }
      canvas.requestPointerLock?.()
    }

    // ── Controles táctiles (móvil) ─────────────────────────────────────────
    const joystickBase = joystickBaseRef.current
    const joystickKnob = joystickKnobRef.current
    let joystickPointerId = null
    let lookPointerId = null
    let lookStartX = 0
    let lookStartY = 0
    let lookLastX = 0
    let lookLastY = 0
    // Un toque solo cuenta como tap si el dedo no se desplaza más de esto;
    // así se distingue con claridad entre inspeccionar y arrastrar para mirar.
    let lookDragging = false
    let suppressClick = false
    const TAP_THRESHOLD = 12

    const setKnob = (dx, dy) => {
      if (joystickKnob) joystickKnob.style.transform = `translate(${dx}px, ${dy}px)`
    }

    const updateJoystick = (clientX, clientY) => {
      if (!joystickBase) return
      const rect = joystickBase.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2
      const max = rect.width / 2 - 16
      let dx = clientX - centerX
      let dy = clientY - centerY
      const length = Math.hypot(dx, dy)
      if (length > max) {
        dx = (dx / length) * max
        dy = (dy / length) * max
      }
      setKnob(dx, dy)
      moveInput.x = dx / max
      moveInput.y = -dy / max
    }

    const onJoystickDown = (event) => {
      if (event.pointerType !== 'touch' || pausedRef.value) return
      joystickPointerId = event.pointerId
      joystickBase.setPointerCapture?.(event.pointerId)
      updateJoystick(event.clientX, event.clientY)
      event.preventDefault()
    }

    const onJoystickMove = (event) => {
      if (event.pointerId !== joystickPointerId) return
      updateJoystick(event.clientX, event.clientY)
      event.preventDefault()
    }

    const onJoystickUp = (event) => {
      if (event.pointerId !== joystickPointerId) return
      joystickPointerId = null
      resetTouchInput()
    }

    const onCanvasPointerDown = (event) => {
      if (event.pointerType !== 'touch' || pausedRef.value || inspectionRef.current.id) return
      lookPointerId = event.pointerId
      lookStartX = event.clientX
      lookStartY = event.clientY
      lookLastX = event.clientX
      lookLastY = event.clientY
      lookDragging = false
      canvas.setPointerCapture?.(event.pointerId)
    }

    const onCanvasPointerMove = (event) => {
      if (event.pointerId !== lookPointerId) return
      // Mientras el dedo no supere el umbral, se considera un tap: no se gira.
      if (!lookDragging) {
        const travelled = Math.hypot(event.clientX - lookStartX, event.clientY - lookStartY)
        if (travelled <= TAP_THRESHOLD) return
        lookDragging = true
      }
      const dx = event.clientX - lookLastX
      const dy = event.clientY - lookLastY
      lookLastX = event.clientX
      lookLastY = event.clientY
      const sensitivity = 0.005
      yaw.value -= dx * sensitivity
      pitch.value -= dy * sensitivity
      pitch.value = THREE.MathUtils.clamp(pitch.value, -Math.PI / 2.15, Math.PI / 2.15)
      updateCameraRotation()
      event.preventDefault()
    }

    const onCanvasPointerUp = (event) => {
      if (event.pointerId !== lookPointerId) return
      lookPointerId = null
      // Siempre se ignora el click sintético posterior: si fue un toque se
      // inspecciona aquí y si fue un arrastre no debe abrir nada.
      suppressClick = true
      if (!lookDragging) inspectAt(event.clientX, event.clientY)
      lookDragging = false
      window.setTimeout(() => {
        suppressClick = false
      }, 350)
    }

    const resize = () => {
      const { clientWidth, clientHeight } = canvas.parentElement
      camera.aspect = clientWidth / clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(clientWidth, clientHeight, false)
    }

    const hemiLight = new THREE.HemisphereLight(0xf0f6ff, 0x22303b, 1.15)
    scene.add(hemiLight)

    const surgicalLight = new THREE.SpotLight(0xffffff, 90, 24, Math.PI / 5, 0.5, 1.2)
    surgicalLight.position.set(0, 9, 1)
    surgicalLight.castShadow = true
    const shadowMapSize = isTouchDevice ? 1024 : 2048
    surgicalLight.shadow.mapSize.set(shadowMapSize, shadowMapSize)
    const surgicalTarget = new THREE.Object3D()
    surgicalTarget.position.set(0, 0, 0)
    scene.add(surgicalLight, surgicalTarget)
    surgicalLight.target = surgicalTarget

    const fillLight = new THREE.DirectionalLight(0xc4dcff, 1.3)
    fillLight.position.set(-5, 5, -4)
    scene.add(fillLight)

    const floorTextureCanvas = document.createElement('canvas')
    floorTextureCanvas.width = 1024
    floorTextureCanvas.height = 1024
    const floorContext = floorTextureCanvas.getContext('2d')
    floorContext.fillStyle = '#aeb8bd'
    floorContext.fillRect(0, 0, 1024, 1024)
    const tileSize = 128
    for (let row = 0; row < 8; row += 1) {
      for (let column = 0; column < 8; column += 1) {
        floorContext.fillStyle = (row + column) % 2 === 0 ? '#b8c1c5' : '#a7b1b6'
        floorContext.fillRect(column * tileSize + 3, row * tileSize + 3, tileSize - 6, tileSize - 6)
      }
    }
    const floorTexture = new THREE.CanvasTexture(floorTextureCanvas)
    floorTexture.colorSpace = THREE.SRGBColorSpace
    floorTexture.wrapS = THREE.RepeatWrapping
    floorTexture.wrapT = THREE.RepeatWrapping
    floorTexture.repeat.set(18, 18)

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(70, 70),
      new THREE.MeshStandardMaterial({
        map: floorTexture,
        color: 0xd1d8da,
        roughness: 0.62,
        metalness: 0.02,
      }),
    )
    floor.rotation.x = -Math.PI / 2
    floor.position.y = -0.02
    floor.receiveShadow = true
    roomGroup.add(floor)

    const addRoomBox = (geometry, material, position, options = {}) => {
      const mesh = new THREE.Mesh(geometry, material)
      mesh.position.set(...position)
      mesh.castShadow = options.castShadow ?? false
      mesh.receiveShadow = options.receiveShadow ?? true
      roomGroup.add(mesh)
      return mesh
    }

    const wallMaterial = new THREE.MeshStandardMaterial({ color: 0xd5dfe1, roughness: 0.9 })
    const ceilingMaterial = new THREE.MeshStandardMaterial({ color: 0xe8eef0, roughness: 0.84 })
    const trimMaterial = new THREE.MeshStandardMaterial({ color: 0x7b9da9, roughness: 0.72, metalness: 0.08 })
    const cabinetMaterial = new THREE.MeshStandardMaterial({ color: 0x607b86, roughness: 0.45, metalness: 0.28 })
    const darkMetalMaterial = new THREE.MeshStandardMaterial({ color: 0x263940, roughness: 0.35, metalness: 0.65 })
    const lightPanelMaterial = new THREE.MeshStandardMaterial({
      color: 0xf8fcff,
      emissive: 0xd8efff,
      emissiveIntensity: 2.2,
      roughness: 0.28,
    })

    // Room shell: the physical walls keep the lower half of the surgical room readable.
    addRoomBox(new THREE.BoxGeometry(70, 0.25, 70), ceilingMaterial, [0, 12, 8])
    addRoomBox(new THREE.BoxGeometry(70, 20, 0.25), wallMaterial, [0, 6, 18])
    addRoomBox(new THREE.BoxGeometry(0.25, 20, 70), wallMaterial, [-18, 6, 0])
    addRoomBox(new THREE.BoxGeometry(0.25, 20, 70), wallMaterial, [18, 6, 0])

    // Blue-gray wall trim and a recessed door make the space read as a clinical room.
    addRoomBox(new THREE.BoxGeometry(70, 0.16, 0.12), trimMaterial, [0, 4.1, 17.8])
    addRoomBox(new THREE.BoxGeometry(0.12, 0.16, 36), trimMaterial, [-17.8, 4.1, 0])
    addRoomBox(new THREE.BoxGeometry(5.2, 8.5, 0.12), darkMetalMaterial, [10.5, 4.25, 17.78])
    addRoomBox(new THREE.BoxGeometry(4.5, 7.8, 0.1), new THREE.MeshStandardMaterial({ color: 0x9db2bb, roughness: 0.3, metalness: 0.15 }), [10.5, 4.25, 17.68])

    // Wall cabinets and a compact equipment column suggest the operating-room setup.
    addRoomBox(new THREE.BoxGeometry(5.4, 5.5, 0.7), cabinetMaterial, [-10.5, 5.4, 17.35], { castShadow: true })
    for (let shelf = 0; shelf < 3; shelf += 1) {
      addRoomBox(new THREE.BoxGeometry(4.8, 0.08, 0.9), darkMetalMaterial, [-10.5, 3.8 + shelf * 1.5, 16.92])
    }
    addRoomBox(new THREE.BoxGeometry(1.1, 5.8, 1.1), darkMetalMaterial, [6.2, 3.2, 16.9], { castShadow: true })
    addRoomBox(new THREE.BoxGeometry(1.5, 0.8, 0.14), lightPanelMaterial, [6.2, 4.4, 16.3])

    // Recessed ceiling panels and a brighter surgical lamp above the working area.
    for (const z of [2, 8, 14]) {
      addRoomBox(new THREE.BoxGeometry(4.2, 0.08, 2.2), lightPanelMaterial, [-5, 11.82, z])
      addRoomBox(new THREE.BoxGeometry(4.2, 0.08, 2.2), lightPanelMaterial, [5, 11.82, z])
    }
    addRoomBox(new THREE.BoxGeometry(3.8, 0.16, 3.2), lightPanelMaterial, [0, 9.25, 0], { castShadow: true })
    addRoomBox(new THREE.BoxGeometry(0.18, 2, 0.18), darkMetalMaterial, [0, 10.55, 0], { castShadow: true })

    modelLoader.load(
      MODEL_URL,
      (gltf) => {
        if (disposed) return

        const model = gltf.scene
        mainModelRef.current = model
        let meshIndex = 0
        model.traverse((object) => {
          if (!object.isMesh) return
          object.castShadow = true
          object.receiveShadow = true
          if (object.material) object.material.needsUpdate = true
          if (meshIndex === 1) {
            object.userData.inspectId = 'blepharostat'
            interactiveMeshes.push(object)
          } else if (meshIndex === 2) {
            object.userData.inspectId = 'conjunctiveForceps'
            interactiveMeshes.push(object)
          }
          meshIndex += 1
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
        setStatus('ready')
      },
      undefined,
      () => {
        if (!disposed) setStatus('error')
      },
    )

    const animate = () => {
      animationFrame = requestAnimationFrame(animate)
      const delta = Math.min(clock.getDelta(), 0.05)

      if (cameraTransition.active) {
        cameraTransition.elapsed += delta * 1000
        const progress = THREE.MathUtils.clamp(cameraTransition.elapsed / cameraTransition.duration, 0, 1)
        const eased = progress * progress * (3 - 2 * progress)
        camera.position.lerpVectors(cameraTransition.fromPosition, cameraTransition.toPosition, eased)
        camera.quaternion.slerpQuaternions(cameraTransition.fromQuaternion, cameraTransition.toQuaternion, eased)
        if (progress === 1) {
          cameraTransition.active = false
          const euler = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ')
          yaw.value = euler.y
          pitch.value = euler.x
        }
      }

      // El objeto inspeccionado gira siempre; la cámara permanece fija.
      if (inspectionRef.current.id) {
        inspectionGroup.rotation.y += delta * 0.7
        inspectionGroup.position.y = Math.sin(clock.elapsedTime * 1.4) * 0.035
      }

      if (!pausedRef.value && !inspectionRef.current.id && !cameraTransition.active) {
        const forward = new THREE.Vector3(-Math.sin(yaw.value), 0, -Math.cos(yaw.value))
        const right = new THREE.Vector3(Math.cos(yaw.value), 0, -Math.sin(yaw.value))
        const direction = new THREE.Vector3()

        if (keys.has('KeyW') || keys.has('ArrowUp')) direction.add(forward)
        if (keys.has('KeyS') || keys.has('ArrowDown')) direction.sub(forward)
        if (keys.has('KeyD') || keys.has('ArrowRight')) direction.add(right)
        if (keys.has('KeyA') || keys.has('ArrowLeft')) direction.sub(right)

        // Entrada del joystick táctil (avance y desplazamiento lateral).
        direction.addScaledVector(forward, moveInput.y)
        direction.addScaledVector(right, moveInput.x)

        if (direction.lengthSq() > 0) {
          direction.normalize()
          const isRunning = keys.has('ShiftLeft') || keys.has('ShiftRight') || runRef.current
          const speed = isRunning ? 4.8 : 2.4
          camera.position.addScaledVector(direction, speed * delta)
        }
      }

      if (cameraReadoutRef.current) {
        const { x, y, z } = camera.position
        cameraReadoutRef.current.textContent = `Cámara · X ${x.toFixed(2)} · Y ${y.toFixed(2)} · Z ${z.toFixed(2)}`
      }

      renderer.render(scene, camera)
    }

    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('keyup', onKeyUp)
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('pointerlockchange', onPointerLockChange)
    canvas.addEventListener('click', onCanvasClick)
    canvas.addEventListener('pointerdown', onCanvasPointerDown)
    canvas.addEventListener('pointermove', onCanvasPointerMove)
    canvas.addEventListener('pointerup', onCanvasPointerUp)
    canvas.addEventListener('pointercancel', onCanvasPointerUp)
    if (joystickBase) {
      joystickBase.addEventListener('pointerdown', onJoystickDown)
      joystickBase.addEventListener('pointermove', onJoystickMove)
      joystickBase.addEventListener('pointerup', onJoystickUp)
      joystickBase.addEventListener('pointercancel', onJoystickUp)
    }
    resize()
    window.addEventListener('resize', resize)
    animate()

    return () => {
      disposed = true
      cancelAnimationFrame(animationFrame)
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('keyup', onKeyUp)
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('pointerlockchange', onPointerLockChange)
      canvas.removeEventListener('click', onCanvasClick)
      canvas.removeEventListener('pointerdown', onCanvasPointerDown)
      canvas.removeEventListener('pointermove', onCanvasPointerMove)
      canvas.removeEventListener('pointerup', onCanvasPointerUp)
      canvas.removeEventListener('pointercancel', onCanvasPointerUp)
      if (joystickBase) {
        joystickBase.removeEventListener('pointerdown', onJoystickDown)
        joystickBase.removeEventListener('pointermove', onJoystickMove)
        joystickBase.removeEventListener('pointerup', onJoystickUp)
        joystickBase.removeEventListener('pointercancel', onJoystickUp)
      }
      window.removeEventListener('resize', resize)
      if (document.pointerLockElement === canvas) document.exitPointerLock()
      startGameRef.current = () => {}
      pauseGameRef.current = () => {}
      renderer.dispose()
      floorTexture.dispose()
      scene.traverse((object) => {
        if (!object.isMesh) return
        object.geometry.dispose()
        if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose())
        else object.material.dispose()
      })
    }
  }, [])

  return (
    <main className="fixed inset-0 overflow-hidden bg-blue-950 text-white">
      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full touch-none select-none cursor-crosshair"
        aria-label="Mesa quirúrgica interactiva en 3D"
      />

      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_35%,transparent_20%,rgba(6,10,32,0.35)_100%)]" />

      <header className="pointer-events-none absolute left-0 right-0 top-0 flex items-start justify-between gap-3 bg-gradient-to-b from-blue-950/90 to-transparent px-4 pb-6 pt-[calc(0.9rem+env(safe-area-inset-top))] sm:gap-4 sm:px-8 sm:py-7 sm:pt-7">
        <div className="min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-300">Vista interactiva</p>
          <h1 className="mt-1 font-display text-base font-semibold leading-tight text-white sm:text-2xl">Armado de la mesa quirúrgica</h1>
          <p className="mt-1 hidden text-xs text-blue-200 sm:block sm:text-sm">WASD o flechas para moverte · mouse para mirar</p>
          <p className="mt-1 text-[11px] text-blue-200 sm:hidden">Joystick para moverte · arrastra para mirar</p>
        </div>
        <div className="pointer-events-auto flex shrink-0 items-center gap-1.5 sm:gap-2">
          {isTouchDevice && !paused && !inspectedId && (
            <>
              <button
                type="button"
                onClick={toggleRun}
                aria-pressed={running}
                aria-label="Correr"
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-2 text-xs font-semibold backdrop-blur transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 ${
                  running
                    ? 'border-blue-300/60 bg-blue-500 text-white'
                    : 'border-white/20 bg-blue-950/60 text-white hover:bg-white/15'
                }`}
              >
                <FontAwesomeIcon icon={faPersonRunning} aria-hidden="true" />
                <span className="hidden sm:inline">Correr</span>
              </button>
              <button
                type="button"
                onClick={() => pauseGameRef.current()}
                aria-label="Pausar"
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/20 bg-blue-950/60 px-2.5 py-2 text-xs font-semibold text-white backdrop-blur transition-colors hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
              >
                <FontAwesomeIcon icon={faPause} aria-hidden="true" />
                <span className="hidden sm:inline">Pausa</span>
              </button>
            </>
          )}
          <Link
            to={`/courses/${courseId}/subtopics/${subtopicId}`}
            className="rounded-lg border border-white/20 bg-blue-950/60 px-3 py-2 text-xs font-semibold text-white backdrop-blur transition-colors hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
          >
            <span className="sm:hidden">Salir</span>
            <span className="hidden sm:inline">Salir de la vista</span>
          </Link>
        </div>
      </header>

      {!paused && !inspectedId && (
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 text-xl font-light text-white/80 drop-shadow">
          +
        </div>
      )}

      {/* Joystick táctil: siempre montado en móvil para que el visor 3D pueda
          enganchar sus eventos; se oculta durante la pausa y la inspección. */}
      {isTouchDevice && (
        <div
          ref={joystickBaseRef}
          aria-hidden="true"
          style={{ bottom: 'calc(1.5rem + env(safe-area-inset-bottom))' }}
          className={`absolute left-5 z-30 flex h-28 w-28 touch-none select-none items-center justify-center rounded-full border border-white/25 bg-blue-950/45 backdrop-blur transition-opacity duration-200 ${
            !paused && !inspectedId ? 'opacity-100' : 'pointer-events-none opacity-0'
          }`}
        >
          <span className="pointer-events-none absolute inset-0 rounded-full border border-white/10" />
          <span className="pointer-events-none absolute inset-x-0 top-1.5 text-center text-[9px] font-bold uppercase tracking-widest text-blue-200/60">
            Mover
          </span>
          <div
            ref={joystickKnobRef}
            className="pointer-events-none h-12 w-12 rounded-full border border-white/40 bg-white/25 shadow-lg shadow-black/40"
          />
        </div>
      )}

      {inspectedId && (
        <div className="pointer-events-none absolute inset-0 z-20">
          <section className="pointer-events-auto absolute inset-x-0 bottom-0 max-h-[48vh] overflow-y-auto rounded-t-3xl border border-blue-300/25 bg-[#102a3b] p-5 pb-[calc(1.25rem+env(safe-area-inset-bottom))] shadow-2xl shadow-black/50 sm:inset-x-auto sm:bottom-8 sm:left-8 sm:max-h-none sm:w-[min(90%,24rem)] sm:rounded-2xl sm:p-7">
            <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-white/20 sm:hidden" />
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-300">
              {TOOL_INFO[inspectedId].eyebrow}
            </p>
            <h2 className="mt-2 font-display text-2xl font-semibold text-white sm:text-3xl">
              {TOOL_INFO[inspectedId].title}
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-blue-100 sm:mt-4">
              {TOOL_INFO[inspectedId].description}
            </p>
            <div className="mt-4 rounded-lg border border-blue-200/15 bg-blue-950/60 px-3 py-2 text-[11px] leading-relaxed text-blue-200">
              {isTouchDevice ? (
                <>
                  El modelo gira automáticamente. Toca <strong className="text-white">Volver a la sala</strong> para seguir explorando.
                </>
              ) : (
                <>
                  Ajusta la vista con <strong className="text-white">WASD/flechas</strong>, mira con el <strong className="text-white">mouse</strong> y usa <strong className="text-white">Shift</strong> para acercarte más rápido. Las coordenadas aparecen abajo a la derecha.
                </>
              )}
            </div>
            <ul className="mt-5 space-y-2 text-xs text-blue-200">
              {TOOL_INFO[inspectedId].details.map((detail) => (
                <li key={detail} className="flex gap-2">
                  <span className="text-blue-300">•</span>
                  {detail}
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => closeInspectionRef.current()}
              className="mt-6 w-full rounded-lg bg-blue-500 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 focus-visible:ring-offset-2 focus-visible:ring-offset-[#102a3b] sm:mt-7 sm:w-auto"
            >
              Volver a la sala
            </button>
          </section>
        </div>
      )}

      {paused && !inspectedId && (
        <div className="absolute inset-0 z-20 flex items-center justify-center overflow-y-auto bg-[#07131f] px-4 py-6 pt-[calc(1rem+env(safe-area-inset-top))] pb-[calc(1rem+env(safe-area-inset-bottom))] sm:px-5">
          <section className="my-auto w-full max-w-lg rounded-2xl border border-blue-300/25 bg-[#102a3b] p-5 shadow-2xl shadow-black/40 sm:p-7">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/20 text-blue-300">
                <FontAwesomeIcon icon={hasStarted ? faPause : isTouchDevice ? faGamepad : faKeyboard} />
              </span>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-300">{hasStarted ? 'Pausa' : 'Cómo explorar'}</p>
                <h2 className="mt-1 font-display text-xl font-semibold text-white sm:text-2xl">
                  {hasStarted ? 'La vista está en pausa' : 'Recorre la sala quirúrgica'}
                </h2>
              </div>
            </div>

            {isTouchDevice ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-200">
                    <FontAwesomeIcon icon={faGamepad} /> Movimiento
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-blue-100">
                    Usa el <strong className="text-white">joystick</strong> de la esquina inferior izquierda para desplazarte por la sala.
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                    <FontAwesomeIcon icon={faHandPointer} className="w-5 shrink-0 text-blue-300" />
                    <div>
                      <p className="text-xs font-bold uppercase tracking-wider text-blue-200">Mirada</p>
                      <p className="mt-1 text-xs text-blue-100">Arrastra el dedo sobre la escena para mirar</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                    <FontAwesomeIcon icon={faPersonRunning} className="w-5 shrink-0 text-blue-300" />
                    <p className="text-xs text-blue-100">Activa <strong className="text-white">Correr</strong> para moverte más rápido.</p>
                  </div>
                  <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                    <FontAwesomeIcon icon={faHandPointer} className="w-5 shrink-0 text-blue-300" />
                    <p className="text-xs text-blue-100">Toca un instrumento para ver su información.</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-200">
                    <FontAwesomeIcon icon={faPersonWalking} /> Movimiento
                  </div>
                  <div className="mt-3 flex items-center justify-center gap-4">
                    <div className="grid w-fit grid-cols-3 gap-1">
                      <span />
                      <KeyCap>W</KeyCap>
                      <span />
                      <KeyCap>A</KeyCap>
                      <KeyCap>S</KeyCap>
                      <KeyCap>D</KeyCap>
                    </div>
                    <div className="grid w-fit grid-cols-3 gap-1">
                      <span />
                      <KeyCap>↑</KeyCap>
                      <span />
                      <KeyCap>←</KeyCap>
                      <KeyCap>↓</KeyCap>
                      <KeyCap>→</KeyCap>
                    </div>
                  </div>
                  <p className="mt-3 text-center text-[11px] text-blue-200">WASD o flechas</p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                    <FontAwesomeIcon icon={faComputerMouse} className="w-5 text-blue-300" />
                    <div>
                      <p className="text-xs font-bold uppercase tracking-wider text-blue-200">Mirada</p>
                      <p className="mt-1 text-xs text-blue-100">Mueve el mouse para mirar</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4">
                    <span className="flex items-center gap-2 text-xs text-blue-100"><KeyCap className="h-7 min-w-12">Shift</KeyCap> Correr</span>
                    <span className="flex items-center gap-2 text-xs text-blue-100"><KeyCap className="h-7 min-w-12">Esc</KeyCap> Pausa</span>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => startGameRef.current()}
                className="w-full rounded-lg bg-blue-500 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 focus-visible:ring-offset-2 focus-visible:ring-offset-blue-950 sm:flex-1"
              >
                {hasStarted ? 'Continuar' : 'Iniciar experiencia'}
              </button>
              <Link
                to={`/courses/${courseId}/subtopics/${subtopicId}`}
                className="w-full rounded-lg border border-white/20 bg-white/5 px-4 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 sm:w-auto"
              >
                Salir de la vista
              </Link>
            </div>
          </section>
        </div>
      )}

      {status === 'loading' && (
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-lg border border-white/10 bg-blue-950/80 px-4 py-3 text-sm text-blue-100 backdrop-blur">
          Cargando modelo 3D…
        </div>
      )}

      {status === 'error' && (
        <div className="absolute left-1/2 top-1/2 z-10 w-[min(90%,28rem)] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-red-200/30 bg-blue-950/85 px-5 py-4 text-center text-sm text-red-50 backdrop-blur">
          No se pudo cargar la mesa quirúrgica interactiva.
        </div>
      )}

      <div className="pointer-events-none absolute bottom-5 left-5 hidden rounded-lg border border-white/10 bg-blue-950/60 px-3 py-2 text-[11px] text-blue-200 backdrop-blur sm:bottom-7 sm:left-8 sm:block">
        Modelo: Prueba_12.glb · Sala quirúrgica 3D
      </div>

      <div
        ref={cameraReadoutRef}
        className="pointer-events-none absolute bottom-5 right-5 hidden rounded-lg border border-blue-300/30 bg-blue-950/70 px-3 py-2 font-mono text-[11px] text-blue-100 backdrop-blur sm:bottom-7 sm:right-8 sm:block"
      >
        Cámara · X -0.50 · Y 5.18 · Z -2.63
      </div>
    </main>
  )
}
