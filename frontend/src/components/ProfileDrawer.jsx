import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCakeCandles,
  faChalkboardUser,
  faGlobe,
  faGraduationCap,
  faRightFromBracket,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'
import { useAuth } from '../hooks/useAuth'

function RoleBadge({ role }) {
  const isTeacher = role === 'TEACHER'
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-3 py-1 ${
        isTeacher ? 'bg-oft-100 text-oft-700' : 'bg-ins-100 text-ins-700'
      }`}
    >
      <FontAwesomeIcon icon={isTeacher ? faChalkboardUser : faGraduationCap} />
      {isTeacher ? 'Profesor' : 'Estudiante'}
    </span>
  )
}

function DataRow({ icon, label, value }) {
  if (!value) return null
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <dt className="text-slate-500 flex items-center gap-2">
        <FontAwesomeIcon icon={icon} className="text-ins-500 w-4" />
        {label}
      </dt>
      <dd className="font-medium text-slate-800 text-right break-all">{value}</dd>
    </div>
  )
}

export default function ProfileDrawer({ open, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const isTeacher = user.role === 'TEACHER'
  const joinedAt = user.created_at
    ? new Date(user.created_at).toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' })
    : null

  const handleLogout = () => {
    logout()
    onClose()
    navigate('/')
  }

  return (
    <div className={`fixed inset-0 z-50 ${open ? '' : 'pointer-events-none'}`} aria-hidden={!open}>
      {/* Overlay */}
      <div
        onClick={onClose}
        className={`absolute inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity duration-300 ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* Panel lateral */}
      <aside
        className={`absolute right-0 top-0 h-full w-80 max-w-[90vw] bg-white shadow-2xl flex flex-col transform transition-transform duration-300 ease-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Cabecera con degradado INS → OFT */}
        <div className="bg-ins-700 px-6 pt-6 pb-8 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white/70 hover:text-white text-lg leading-none"
            aria-label="Cerrar panel"
          >
            <FontAwesomeIcon icon={faXmark} />
          </button>
          <div className="flex flex-col items-center text-center mt-2">
            {user.profile_image ? (
              <img
                src={user.profile_image}
                alt={user.name}
                className="w-20 h-20 rounded-full ring-4 ring-white/30 shadow-lg"
                referrerPolicy="no-referrer"
              />
            ) : (
              <span className="w-20 h-20 rounded-full bg-white/20 ring-4 ring-white/30 flex items-center justify-center text-3xl font-bold">
                {user.name?.[0]?.toUpperCase()}
              </span>
            )}
            <h2 className="mt-3 text-lg font-bold leading-tight">{user.name}</h2>
            <p className="text-sm text-white/80 break-all">{user.email}</p>
            <div className="mt-3">
              <RoleBadge role={user.role} />
            </div>
          </div>
        </div>

        {/* Datos del perfil */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">Mi cuenta</h3>
            <dl className="space-y-2.5">
              <DataRow icon={faGlobe} label="País" value={user.country} />
              <DataRow icon={faCakeCandles} label="Edad" value={user.age ? `${user.age} años` : null} />
            </dl>
            <p className="mt-3 text-xs text-slate-400">
              Rol asignado por {user.profile_image ? 'Google' : 'INSOFT'}
              {joinedAt && ` · Miembro desde ${joinedAt}`}
            </p>
          </section>
        </div>

        {/* Pie */}
        <div className="border-t border-slate-100 px-6 py-4">
          <button
            onClick={handleLogout}
            className="w-full inline-flex items-center justify-center gap-2 text-sm font-medium text-red-600 hover:text-white hover:bg-red-500 border border-red-200 rounded-lg px-4 py-2.5 transition-colors"
          >
            <FontAwesomeIcon icon={faRightFromBracket} />
            Cerrar sesión
          </button>
        </div>
      </aside>
    </div>
  )
}
