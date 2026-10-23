import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Cada prueba carga api.js de nuevo para fijar VITE_API_URL en ese momento.
async function loadApi(apiUrl) {
  vi.resetModules()
  vi.stubEnv('VITE_API_URL', apiUrl ?? '')
  return import('./api')
}

function jsonResponse(status, body) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('api.js', () => {
  let originalLocation

  beforeEach(() => {
    localStorage.clear()
    originalLocation = window.location
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    Object.defineProperty(window, 'location', { value: originalLocation, configurable: true })
  })

  it('usa VITE_API_URL como base y quita las barras finales', async () => {
    const { apiFetch } = await loadApi('https://api.ejemplo.test//')
    fetch.mockResolvedValue(jsonResponse(200, []))

    await apiFetch('/courses')

    expect(fetch).toHaveBeenCalledWith(
      'https://api.ejemplo.test/api/courses',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('sin VITE_API_URL en desarrollo usa el backend local', async () => {
    const { apiFetch } = await loadApi(undefined)
    fetch.mockResolvedValue(jsonResponse(200, {}))

    await apiFetch('/users/me')

    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/users/me', expect.anything())
  })

  it('envía el token de sesión como Bearer', async () => {
    const { apiFetch, session } = await loadApi('https://api.ejemplo.test')
    session.save('tok-de-prueba', { id: 1 })
    fetch.mockResolvedValue(jsonResponse(200, {}))

    await apiFetch('/courses')

    const [, init] = fetch.mock.calls[0]
    expect(init.headers.Authorization).toBe('Bearer tok-de-prueba')
  })

  it('401: borra la sesión y manda a la pantalla de entrada', async () => {
    const { apiFetch, session, ApiError } = await loadApi('https://api.ejemplo.test')
    session.save('caducado', { id: 1 })
    Object.defineProperty(window, 'location', {
      value: { href: 'https://app.ejemplo.test/dashboard' },
      configurable: true,
    })
    fetch.mockResolvedValue(jsonResponse(401, { detail: 'Token inválido' }))

    const error = await apiFetch('/courses').catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(401)
    expect(session.getToken()).toBeNull()
    expect(session.getUser()).toBeNull()
    expect(window.location.href).toBe('/')
  })

  it('403: lanza ApiError con el detalle del servidor y conserva la sesión', async () => {
    const { apiFetch, session, ApiError } = await loadApi('https://api.ejemplo.test')
    session.save('vigente', { id: 2 })
    fetch.mockResolvedValue(jsonResponse(403, { detail: 'No tienes acceso a este curso.' }))

    const error = await apiFetch('/courses/9').catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(403)
    expect(error.message).toBe('No tienes acceso a este curso.')
    expect(session.getToken()).toBe('vigente')
  })

  it('error sin cuerpo JSON usa un mensaje genérico', async () => {
    const { apiFetch } = await loadApi('https://api.ejemplo.test')
    fetch.mockResolvedValue(new Response('<html>502</html>', { status: 502 }))

    const error = await apiFetch('/courses').catch((e) => e)

    expect(error.status).toBe(502)
    expect(error.message).toBe('Error inesperado')
  })

  it('respuesta correcta devuelve el JSON', async () => {
    const { apiFetch } = await loadApi('https://api.ejemplo.test')
    fetch.mockResolvedValue(jsonResponse(200, { ok: true }))

    await expect(apiFetch('/health')).resolves.toEqual({ ok: true })
  })
})
