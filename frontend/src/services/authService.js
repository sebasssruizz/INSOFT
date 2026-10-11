import { apiFetch } from './api'

export function loginWithGoogle(credential) {
  return apiFetch('/auth/google', { method: 'POST', body: { credential } })
}

// Acceso de desarrollo: solo existe en el servidor de desarrollo. Fuera de DEV la
// función no contiene la ruta ni se incluye en el bundle de producción.
export function loginDev(email, name, role) {
  if (!import.meta.env.DEV) {
    return Promise.reject(new Error('El acceso de desarrollo no está disponible.'))
  }
  return apiFetch('/auth/dev', { method: 'POST', body: { email, name, role } })
}

export function fetchMe() {
  return apiFetch('/users/me')
}

export function updateMyProfile(profile) {
  return apiFetch('/users/me/profile', { method: 'PATCH', body: profile })
}
