import { useAuth } from '../hooks/useAuth'
import StudentDashboard from './StudentDashboard'
import TeacherDashboard from './TeacherDashboard'

export default function DashboardPage() {
  const { user } = useAuth()
  return user?.role === 'TEACHER' ? <TeacherDashboard /> : <StudentDashboard />
}
