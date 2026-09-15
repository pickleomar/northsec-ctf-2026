import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { authApi } from '../lib/api'
import { Loader2, Zap } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [mode,     setMode]     = useState('signin')  // 'signin' | 'signup'
  const [username, setUsername] = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [busy,     setBusy]     = useState(false)
  const [error,    setError]    = useState('')
  const [showRecovery, setShowRecovery] = useState(false)
  const [recoveryUser, setRecoveryUser] = useState('')
  const [recoveryToken, setRecoveryToken] = useState('')
  const [recoveryPass, setRecoveryPass] = useState('')
  const [recoveryBusy, setRecoveryBusy] = useState(false)
  const [recoveryMsg, setRecoveryMsg] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      if (mode === 'signup') {
        const r = await authApi.signup(username, email, password)
        const d = await r.json()
        if (!r.ok) { setError(d.error || 'Registration failed'); setBusy(false); return }
      }
      await login(username, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  const requestRecovery = async (e) => {
    e.preventDefault()
    const user = (recoveryUser || username).trim()
    if (!user) {
      setRecoveryMsg({ type: 'error', text: 'Username is required.' })
      return
    }
    setRecoveryBusy(true)
    setRecoveryMsg(null)
    const r = await authApi.requestRecovery(user)
    const d = await r.json()
    setRecoveryBusy(false)
    setRecoveryMsg(r.ok
      ? { type: 'success', text: d.message || 'Recovery requested. Check your primary account email.' }
      : { type: 'error', text: d.error || 'Recovery request failed.' })
  }

  const confirmRecovery = async (e) => {
    e.preventDefault()
    if (!recoveryToken.trim() || recoveryPass.length < 8) {
      setRecoveryMsg({ type: 'error', text: 'Token and password (min 8 chars) are required.' })
      return
    }
    setRecoveryBusy(true)
    setRecoveryMsg(null)
    const r = await authApi.confirmRecovery(recoveryToken.trim(), recoveryPass)
    const d = await r.json()
    setRecoveryBusy(false)
    setRecoveryMsg(r.ok
      ? { type: 'success', text: d.message || 'Password reset successful. You can sign in now.' }
      : { type: 'error', text: d.error || 'Password reset failed.' })
    if (r.ok) {
      setPassword('')
      setRecoveryPass('')
      setRecoveryToken('')
      setShowRecovery(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-100 tracking-tight">Dar Mohssinin</span>
          </div>
          <p className="text-slate-500 text-sm">AI-powered pitch intelligence</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          {/* Tab toggle */}
          <div className="flex bg-slate-800 rounded-xl p-1 mb-6">
            {['signin', 'signup'].map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError('') }}
                className={`flex-1 text-sm font-medium py-1.5 rounded-lg transition-all
                  ${mode === m
                    ? 'bg-slate-700 text-slate-100 shadow-sm'
                    : 'text-slate-500 hover:text-slate-300'}`}
              >
                {m === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 font-medium">Username</label>
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                           text-slate-100 text-sm placeholder-slate-600 outline-none
                           focus:border-indigo-500 transition-colors"
                type="text"
                placeholder="yourhandle"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>

            {mode === 'signup' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1.5 font-medium">Email</label>
                <input
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                             text-slate-100 text-sm placeholder-slate-600 outline-none
                             focus:border-indigo-500 transition-colors"
                  type="email"
                  placeholder="you@startup.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-slate-400 mb-1.5 font-medium">Password</label>
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                           text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              />
            </div>

            {error && (
              <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20
                             rounded-xl px-4 py-2.5">{error}</p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full flex items-center justify-center gap-2
                         bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
                         text-white font-medium text-sm py-2.5 rounded-xl transition-colors mt-2"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'signin' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {mode === 'signin' && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <p className="text-center text-xs text-slate-600">
                Forgot password?{' '}
                <button
                  type="button"
                  className="text-indigo-400 hover:text-indigo-300 transition-colors"
                  onClick={() => {
                    setShowRecovery(v => !v)
                    setRecoveryUser(username)
                    setRecoveryMsg(null)
                  }}
                >
                  Account recovery
                </button>
              </p>
              {showRecovery && (
                <div className="mt-3 space-y-3">
                  <form onSubmit={requestRecovery} className="space-y-2">
                    <input
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                                 text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
                      type="text"
                      placeholder="username"
                      value={recoveryUser}
                      onChange={e => setRecoveryUser(e.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={recoveryBusy}
                      className="w-full text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700
                                 text-slate-200 py-2 rounded-lg transition-colors disabled:opacity-50"
                    >
                      Request Recovery Token
                    </button>
                  </form>

                  <form onSubmit={confirmRecovery} className="space-y-2">
                    <input
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                                 text-slate-100 text-sm font-mono outline-none focus:border-indigo-500 transition-colors"
                      type="text"
                      placeholder="recovery token"
                      value={recoveryToken}
                      onChange={e => setRecoveryToken(e.target.value)}
                    />
                    <input
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                                 text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
                      type="password"
                      placeholder="new password"
                      value={recoveryPass}
                      onChange={e => setRecoveryPass(e.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={recoveryBusy}
                      className="w-full text-xs bg-indigo-600 hover:bg-indigo-500 text-white
                                 py-2 rounded-lg transition-colors disabled:opacity-50"
                    >
                      Reset Password
                    </button>
                  </form>

                  {recoveryMsg && (
                    <p className={`text-xs rounded-lg px-3 py-2 border ${
                      recoveryMsg.type === 'success'
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-red-400 bg-red-500/10 border-red-500/20'
                    }`}>
                      {recoveryMsg.text}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
