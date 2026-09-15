import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]     = useState(null)
  const [csrf, setCsrf]     = useState('')
  const [loading, setLoad]  = useState(true)

  useEffect(() => {
    authApi.whoami()
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d && !d.error) { setUser(d); setCsrf(d.csrf_token || '') } })
      .finally(() => setLoad(false))
  }, [])

  const login = async (username, password) => {
    const r = await authApi.signin(username, password)
    const d = await r.json()
    if (!r.ok) throw new Error(d.error || 'Sign in failed')
    setUser(d)
    setCsrf(d.csrf_token || '')
    return d
  }

  const logout = async () => {
    await authApi.signout()
    setUser(null)
    setCsrf('')
  }

  return (
    <AuthContext.Provider value={{ user, csrf, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
