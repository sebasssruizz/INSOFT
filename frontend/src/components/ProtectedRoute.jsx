import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute({ requiredRole, children }) {
  const { isAuthenticated, user } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) return <Navigate to="/" replace />

  // Si el perfil está incompleto, completarlo es obligatorio antes de continuar
  if (user && !user.profile_completed && location.pathname !== '/complete-profile') {
    return <Navigate to="/complete-profile" replace />
  }

  if (requiredRole && user?.role !== requiredRole) return <Navigate to="/dashboard" replace />

  return children ?? <Outlet />
}
