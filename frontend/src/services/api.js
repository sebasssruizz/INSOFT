const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getApiUrl() {
  // Si VITE_API_URL está configurado, usarlo
  if (DEFAULT_API_URL && DEFAULT_API_URL !== 'http://localhost:8000') {
    return DEFAULT_API_URL
  }
  // Si estamos en producción (distinto host), inferir el backend desde el mismo host
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return DEFAULT_API_URL
}

const API_URL = getApiUrl()

const TOKEN_KEY = 'insoft_token'
const USER_KEY = 'insoft_user'

export const session = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getUser: () => {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  },
  save: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail)
    this.status = status
  }
}

/** Descarga un CSV del backend con el token de sesión. */
export async function downloadCsv(path, filename) {
  const headers = {}
  const token = session.getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API_URL}/api${path}`, { headers })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new ApiError(response.status, data.detail || 'No se pudo descargar el CSV')
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

// Servidores gratuitos (Render free) se quedan dormidos: la primera petición
// puede superar los 5 s. Al excederse se avisa a la UI con eventos
// 'insoft:api-slow' / 'insoft:api-slow-end' (componente SlowServerBanner).
const SLOW_THRESHOLD_MS = 5000
let slowRequestCount = 0

const notifySlowCount = () =>
  window.dispatchEvent(
    new CustomEvent(slowRequestCount > 0 ? 'insoft:api-slow' : 'insoft:api-slow-end'),
  )

export async function apiFetch(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = session.getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await new Promise((resolve, reject) => {
    let wentSlow = false
    const timer = setTimeout(() => {
      if (!wentSlow) {
        wentSlow = true
        slowRequestCount += 1
        notifySlowCount()
      }
    }, SLOW_THRESHOLD_MS)
    fetch(`${API_URL}/api${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
      .then(resolve, reject)
      .finally(() => {
        clearTimeout(timer)
        if (wentSlow) {
          wentSlow = false
          slowRequestCount -= 1
          notifySlowCount()
        }
      })
  })

  if (response.status === 401) {
    session.clear()
    window.location.href = '/'
    throw new ApiError(401, 'Sesión expirada')
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(response.status, data.detail || 'Error inesperado')
  }
  return data
}
