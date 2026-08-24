import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Logo from './Logo'
import ProfileDrawer from './ProfileDrawer'

export default function Layout() {
  const { user } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const isTeacher = user?.role === 'TEACHER'

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-10">
        <div className="h-0.5 flex">
          <div className="w-1/2 bg-ins-500" />
          <div className="w-1/2 bg-oft-500" />
        </div>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="hover:opacity-80 transition-opacity">
            <Logo />
          </Link>

          <div className="flex items-center gap-3">
            <span
              className={`hidden sm:inline-flex items-center text-xs font-semibold rounded-full px-3 py-1 ${
                isTeacher ? 'bg-oft-100 text-oft-700' : 'bg-ins-100 text-ins-700'
              }`}
            >
              {isTeacher ? 'Profesor' : 'Estudiante'}
            </span>

            {/* Avatar: abre el panel lateral de perfil */}
            <button
              onClick={() => setDrawerOpen(true)}
              className="flex items-center gap-2 rounded-full p-0.5 hover:ring-2 hover:ring-oft-300 transition-all"
              aria-label="Abrir mi perfil"
            >
              {user?.profile_image ? (
                <img
                  src={user.profile_image}
                  alt={user.name}
                  className="w-9 h-9 rounded-full shadow"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <span className="w-9 h-9 rounded-full bg-ins-600 text-white flex items-center justify-center text-sm font-bold shadow">
                  {user?.name?.[0]?.toUpperCase()}
                </span>
              )}
              <span className="hidden md:inline text-sm font-medium text-slate-700 pr-1">{user?.name}</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        <span className="font-semibold"><span className="text-ins-600">INS</span><span className="text-oft-600">OFT</span></span>
        {' '}— Sistema web de apoyo al aprendizaje de Oftalmología
      </footer>

      <ProfileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  )
}
