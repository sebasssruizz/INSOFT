import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBars,
  faGraduationCap,
  faHouse,
  faRightFromBracket,
  faUsers,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

import { cn } from '../lib/utils'
import { useAuth } from '../hooks/useAuth'
import { CoursesProvider, useCourses } from '../hooks/useCourses'
import Logo from './Logo'
import ProfileDrawer from './ProfileDrawer'

function CourseLink({ course, isTeacher }) {
  const to = isTeacher ? `/teacher/courses/${course.id}` : `/courses/${course.id}`
  const percentage = Math.round(course.progress_percentage || 0)

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'group block rounded-xl px-3 py-2.5 transition-colors duration-150',
          isActive ? 'bg-soft-sky' : 'hover:bg-ink-100',
        )
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={cn(
              'line-clamp-2 text-[0.8125rem] font-medium leading-snug',
              isActive ? 'text-deep-sky' : 'text-ink-700',
            )}
          >
            {course.name}
          </span>
          {isTeacher ? (
            <span className="tabular mt-1.5 block text-[0.6875rem] text-ink-500">
              {course.student_count} {course.student_count === 1 ? 'estudiante' : 'estudiantes'}
            </span>
          ) : (
            <span className="mt-2 flex items-center gap-2">
              <span className="h-1 flex-1 overflow-hidden rounded-full bg-ink-200">
                <span
                  className="block h-full w-full origin-left rounded-full bg-blue-800 transition-transform duration-700 ease-out"
                  style={{ transform: `scaleX(${percentage / 100})` }}
                />
              </span>
              <span className="tabular text-[0.6875rem] font-bold text-blue-800">
                {percentage}%
              </span>
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

function SidebarContent({ onNavigate, onOpenProfile }) {
  const { user, logout } = useAuth()
  const { courses, loading } = useCourses()
  const isTeacher = user?.role === 'TEACHER'

  return (
    <div className="flex h-full flex-col">
      <div className="px-5 pb-2 pt-7">
        <Link to="/dashboard" onClick={onNavigate} className="inline-block">
          <Logo size="md" />
        </Link>
      </div>

      <nav className="px-3 pt-6">
        <NavLink
          to="/dashboard"
          end
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors duration-150',
              isActive
                ? 'bg-blue-900 text-white'
                : 'text-ink-700 hover:bg-ink-100 hover:text-ink-900',
            )
          }
        >
          <FontAwesomeIcon icon={faHouse} className="w-4" aria-hidden="true" />
          Inicio
        </NavLink>
      </nav>

      <div className="mt-8 min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        <p className="eyebrow px-3 pb-2.5 text-ink-400">
          {isTeacher ? 'Cursos que imparto' : 'Mis cursos'}
        </p>

        {loading && (
          <div className="space-y-2 px-3">
            {[0, 1].map((i) => (
              <div key={i} className="skeleton h-9 rounded-lg" />
            ))}
          </div>
        )}

        {!loading && courses.length === 0 && (
          <p className="px-3 text-[0.8125rem] leading-relaxed text-ink-500">
            {isTeacher
              ? 'Crea tu primer curso desde Inicio.'
              : 'Únete a un curso con el código de tu facultad.'}
          </p>
        )}

        <div className="space-y-1" onClick={onNavigate}>
          {courses.map((course) => (
            <CourseLink key={course.id} course={course} isTeacher={isTeacher} />
          ))}
        </div>
      </div>

      <div className="border-t border-ink-200 p-3">
        <button
          onClick={onOpenProfile}
          className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left transition-colors duration-150 hover:bg-ink-100"
        >
          {user?.profile_image ? (
            <img
              src={user.profile_image}
              alt=""
              className="h-9 w-9 rounded-full ring-2 ring-ink-200"
              referrerPolicy="no-referrer"
            />
          ) : (
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-soft-lavender font-sans text-sm font-bold text-deep-lavender">
              {user?.name?.[0]?.toUpperCase()}
            </span>
          )}
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[0.8125rem] font-semibold text-ink-900">
              {user?.name}
            </span>
            <span className="flex items-center gap-1.5 text-[0.6875rem] text-ink-500">
              <FontAwesomeIcon
                icon={isTeacher ? faUsers : faGraduationCap}
                className="text-[0.625rem]"
                aria-hidden="true"
              />
              {isTeacher ? 'Profesor' : 'Estudiante'}
            </span>
          </span>
        </button>

        <button
          onClick={logout}
          className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2 text-[0.8125rem] font-medium text-ink-500 transition-colors duration-150 hover:bg-ink-100 hover:text-ink-900"
        >
          <FontAwesomeIcon icon={faRightFromBracket} className="w-4" aria-hidden="true" />
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}

function Shell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen bg-ink-50 lg:flex">
      {/* Barra lateral fija en escritorio */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[16.5rem] flex-col border-r border-ink-200 bg-white lg:flex">
        <SidebarContent onOpenProfile={() => setProfileOpen(true)} />
      </aside>

      {/* Cabecera compacta en móvil */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-ink-200 bg-ink-50/90 px-4 backdrop-blur lg:hidden">
        <Link to="/dashboard">
          <Logo size="sm" />
        </Link>
        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Abrir el menú de navegación"
          className="flex h-10 w-10 items-center justify-center rounded-lg text-ink-700 transition-colors hover:bg-ink-100"
        >
          <FontAwesomeIcon icon={faBars} />
        </button>
      </header>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            aria-label="Cerrar el menú"
            onClick={() => setMobileOpen(false)}
            className="absolute inset-0 animate-fade-in bg-ink-950/40 backdrop-blur-sm"
          />
          <div className="absolute inset-y-0 left-0 w-[17rem] animate-rise-in bg-white shadow-e4">
            <button
              onClick={() => setMobileOpen(false)}
              aria-label="Cerrar el menú"
              className="absolute right-3 top-6 flex h-9 w-9 items-center justify-center rounded-lg text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-900"
            >
              <FontAwesomeIcon icon={faXmark} />
            </button>
            <SidebarContent
              onNavigate={() => setMobileOpen(false)}
              onOpenProfile={() => {
                setMobileOpen(false)
                setProfileOpen(true)
              }}
            />
          </div>
        </div>
      )}

      <div className="min-w-0 flex-1 lg:pl-[16.5rem]">
        <Outlet />
      </div>

      {/* Fuera de la barra lateral: dentro, el `transform` del cajón móvil
          crearía un bloque contenedor y atraparía este panel `fixed`. */}
      <ProfileDrawer open={profileOpen} onClose={() => setProfileOpen(false)} />
    </div>
  )
}

export default function Layout() {
  return (
    <CoursesProvider>
      <Shell />
    </CoursesProvider>
  )
}
