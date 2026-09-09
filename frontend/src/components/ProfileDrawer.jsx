import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCakeCandles,
  faChalkboardUser,
  faEnvelope,
  faGlobe,
  faGraduationCap,
  faRightFromBracket,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import { Button } from './ui/Button'
import { useAuth } from '../hooks/useAuth'

function DataRow({ icon, label, value }) {
  if (!value) return null
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <dt className="flex shrink-0 items-center gap-2.5 text-sm text-ink-500">
        <FontAwesomeIcon
          icon={icon}
          className="w-4 text-[0.8rem] text-blue-800"
          aria-hidden="true"
        />
        {label}
      </dt>
      <dd className="break-all text-right text-sm font-medium text-ink-900">{value}</dd>
    </div>
  )
}

export default function ProfileDrawer({ open, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Cerrar con Escape: es un panel modal.
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!user) return null

  const isTeacher = user.role === 'TEACHER'
  const joinedAt = user.created_at
    ? new Date(user.created_at).toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  const handleLogout = () => {
    logout()
    onClose()
    navigate('/')
  }

  return (
    <div className={`fixed inset-0 z-50 ${open ? '' : 'pointer-events-none'}`} aria-hidden={!open}>
      <div
        onClick={onClose}
        className={`absolute inset-0 bg-ink-950/50 backdrop-blur-sm transition-opacity duration-300 ease-out ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
      />

      <aside
        role="dialog"
        aria-label="Mi perfil"
        className={`absolute right-0 top-0 flex h-full w-[22rem] max-w-[92vw] flex-col bg-white shadow-e4 transition-transform duration-300 ease-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="relative bg-gradient-to-br from-soft-lavender to-soft-sky px-7 pb-9 pt-7">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-lg text-ink-500 transition-colors duration-150 hover:bg-white/70 hover:text-ink-900"
            aria-label="Cerrar el panel"
          >
            <FontAwesomeIcon icon={faXmark} />
          </button>

          <div className="flex flex-col items-center text-center">
            {user.profile_image ? (
              <img
                src={user.profile_image}
                alt=""
                className="h-20 w-20 rounded-full ring-4 ring-white/70"
                referrerPolicy="no-referrer"
              />
            ) : (
              <span className="flex h-20 w-20 items-center justify-center rounded-full bg-white font-display text-3xl font-semibold text-deep-lavender ring-4 ring-white/70">
                {user.name?.[0]?.toUpperCase()}
              </span>
            )}
            <h2 className="mt-4 font-display text-xl font-semibold leading-tight text-ink-900">
              {user.name}
            </h2>
            <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1 text-[0.6875rem] font-bold uppercase tracking-[0.08em] text-deep-lavender">
              <FontAwesomeIcon
                icon={isTeacher ? faChalkboardUser : faGraduationCap}
                className="text-[0.65rem]"
                aria-hidden="true"
              />
              {isTeacher ? 'Profesor' : 'Estudiante'}
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-7 py-6">
          <p className="eyebrow text-ink-400">Mi cuenta</p>
          <dl className="mt-2 divide-y divide-ink-200">
            <DataRow icon={faEnvelope} label="Correo" value={user.email} />
            <DataRow icon={faGlobe} label="País" value={user.country} />
            <DataRow
              icon={faCakeCandles}
              label="Edad"
              value={user.age ? `${user.age} años` : null}
            />
          </dl>

          {joinedAt && (
            <p className="mt-5 text-xs leading-relaxed text-ink-400">Miembro desde {joinedAt}</p>
          )}
        </div>

        <div className="border-t border-ink-200 px-7 py-5">
          <Button
            onClick={handleLogout}
            variant="secondary"
            icon={faRightFromBracket}
            className="w-full"
          >
            Cerrar sesión
          </Button>
        </div>
      </aside>
    </div>
  )
}
