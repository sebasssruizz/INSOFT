import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './hooks/useAuth'
import CompleteProfilePage from './pages/CompleteProfilePage'
import DashboardPage from './pages/DashboardPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import TeacherCoursePage from './pages/TeacherCoursePage'
import CourseOverview from './pages/course/CourseOverview'
import CourseShell from './pages/course/CourseShell'
import SubtopicPage from './pages/course/SubtopicPage'
import UnitPage from './pages/course/UnitPage'
import UnitQuizPage from './pages/course/UnitQuizPage'

// Vista 3D a pantalla completa: carga three.js solo cuando se abre.
const InteractiveViewPage = lazy(() => import('./pages/InteractiveViewPage'))

export default function App() {
  const { isAuthenticated, user } = useAuth()

  const homeElement = !isAuthenticated ? (
    <LandingPage />
  ) : user?.profile_completed ? (
    <Navigate to="/dashboard" replace />
  ) : (
    <Navigate to="/complete-profile" replace />
  )

  const loginElement = isAuthenticated ? (
    user?.profile_completed ? (
      <Navigate to="/dashboard" replace />
    ) : (
      <Navigate to="/complete-profile" replace />
    )
  ) : (
    <LoginPage />
  )

  return (
    <Routes>
      <Route path="/" element={homeElement} />
      <Route path="/login" element={loginElement} />

      <Route element={<ProtectedRoute />}>
        <Route path="/complete-profile" element={<CompleteProfilePage />} />
        {/* Vista 3D a pantalla completa: fuera del contenedor de la aplicación. */}
        <Route
          path="/courses/:courseId/subtopics/:subtopicId/interactive"
          element={
            <Suspense fallback={<div className="fixed inset-0 bg-blue-950" />}>
              <InteractiveViewPage />
            </Suspense>
          }
        />

        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* El curso es un contenedor persistente: cabecera con el progreso e
              índice lateral se mantienen mientras se navega por dentro. */}
          <Route path="/courses/:courseId" element={<CourseShell />}>
            <Route index element={<CourseOverview />} />
            <Route path="units/:topicId" element={<UnitPage />} />
            <Route path="units/:topicId/quiz" element={<UnitQuizPage />} />
            <Route path="subtopics/:subtopicId" element={<SubtopicPage />} />
          </Route>

          <Route
            path="/teacher/courses/:courseId"
            element={
              <ProtectedRoute requiredRole="TEACHER">
                <TeacherCoursePage />
              </ProtectedRoute>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
