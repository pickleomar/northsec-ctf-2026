import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/AuthContext'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import ProfilePage from './pages/ProfilePage'
import SettingsPage from './pages/SettingsPage'

function ProtectedLayout({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-folio-bg flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    )
  }
  if (!user) return <Navigate to="/auth" replace />
  return (
    <div className="min-h-screen bg-folio-bg flex">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}

function AuthGate({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={
            <AuthGate><LoginPage /></AuthGate>
          } />
          <Route path="/dashboard" element={
            <ProtectedLayout><DashboardPage /></ProtectedLayout>
          } />
          <Route path="/projects" element={
            <ProtectedLayout><ProjectsPage /></ProtectedLayout>
          } />
          <Route path="/projects/:id" element={
            <ProtectedLayout><ProjectDetailPage /></ProtectedLayout>
          } />
          <Route path="/profile" element={
            <ProtectedLayout><ProfilePage /></ProtectedLayout>
          } />
          <Route path="/settings" element={
            <ProtectedLayout><SettingsPage /></ProtectedLayout>
          } />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
