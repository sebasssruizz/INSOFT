import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { session } from '../services/api'
import { loginDev, loginWithGoogle, updateMyProfile, updateMyRole } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => session.getUser())
  const [token, setToken] = useState(() => session.getToken())

  const handleAuthResponse = useCallback((data) => {
    session.save(data.access_token, data.user)
    setToken(data.access_token)
    setUser(data.user)
  }, [])

  const loginGoogle = useCallback(
    async (credential) => {
      const data = await loginWithGoogle(credential)
      handleAuthResponse(data)
      return data.user
    },
    [handleAuthResponse],
  )

  const loginDevelopment = useCallback(
    async (email, name, role) => {
      const data = await loginDev(email, name, role)
      handleAuthResponse(data)
      return data.user
    },
    [handleAuthResponse],
  )

  const changeRole = useCallback(
    async (role) => {
      const updated = await updateMyRole(role)
      if (token) session.save(token, updated)
      setUser(updated)
      return updated
    },
    [token],
  )

  const completeProfile = useCallback(
    async (profile) => {
      const updated = await updateMyProfile(profile)
      if (token) session.save(token, updated)
      setUser(updated)
      return updated
    },
    [token],
  )

  const logout = useCallback(() => {
    session.clear()
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      loginGoogle,
      loginDevelopment,
      changeRole,
      completeProfile,
      logout,
    }),
    [user, token, loginGoogle, loginDevelopment, changeRole, completeProfile, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
