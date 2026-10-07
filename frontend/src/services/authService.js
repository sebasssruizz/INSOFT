import { apiFetch } from './api'

export function loginWithGoogle(credential) {
  return apiFetch('/auth/google', { method: 'POST', body: { credential } })
}

export function loginDev(email, name, role) {
  return apiFetch('/auth/dev', { method: 'POST', body: { email, name, role } })
}

export function fetchMe() {
  return apiFetch('/users/me')
}

export function updateMyProfile(profile) {
  return apiFetch('/users/me/profile', { method: 'PATCH', body: profile })
}
