import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './hooks/useAuth'
import CompleteProfilePage from './pages/CompleteProfilePage'
import CoursePage from './pages/CoursePage'
import DashboardPage from './pages/DashboardPage'
import LandingPage from './pages/LandingPage'
import NotFoundPage from './pages/NotFoundPage'
import SubtopicPage from './pages/SubtopicPage'
import TeacherCoursePage from './pages/TeacherCoursePage'

export default function App() {
  const { isAuthenticated, user } = useAuth()

  const homeElement = !isAuthenticated ? (
    <LandingPage />
  ) : user?.profile_completed ? (
    <Navigate to="/dashboard" replace />
  ) : (
    <Navigate to="/complete-profile" replace />
  )

  return (
    <Routes>
      <Route path="/" element={homeElement} />

      <Route element={<ProtectedRoute />}>
        <Route path="/complete-profile" element={<CompleteProfilePage />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/courses/:courseId" element={<CoursePage />} />
          <Route path="/courses/:courseId/subtopics/:subtopicId" element={<SubtopicPage />} />
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
