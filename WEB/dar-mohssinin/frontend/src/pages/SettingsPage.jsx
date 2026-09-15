import { useEffect, useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import { accountApi } from '../lib/api'
import { Bell, Lock, CheckCircle2, AlertCircle, Loader2, Save, Shield } from 'lucide-react'

function Toast({ msg }) {
  if (!msg) return null
  const ok = msg.type === 'success'
  return (
    <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm
      ${ok ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
           : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
      {msg.text}
    </div>
  )
}

export default function SettingsPage() {
  const { user, csrf } = useAuth()

  // Notification settings
  const [notifyEmail, setNotifyEmail] = useState('')
  const [savingNotify, setSavingNotify] = useState(false)
  const [notifyMsg,    setNotifyMsg]    = useState(null)

  // Security
  const [currentPass, setCurrentPass] = useState('')
  const [newPass,     setNewPass]      = useState('')
  const [savingPass,  setSavingPass]   = useState(false)
  const [passMsg,     setPassMsg]      = useState(null)

  useEffect(() => {
    accountApi.notifications()
      .then(r => r.json())
      .then(d => { if (d.notify_email) setNotifyEmail(d.notify_email) })
  }, [])

  const saveNotifications = async (e) => {
    e.preventDefault()
    setSavingNotify(true); setNotifyMsg(null)
    const r = await accountApi.updateNotifications(notifyEmail, csrf)
    const d = await r.json()
    setSavingNotify(false)
    setNotifyMsg(r.ok ? { type: 'success', text: 'Notification address updated.' }
                      : { type: 'error',   text: d.error })
  }

  const saveSecurity = async (e) => {
    e.preventDefault()
    setSavingPass(true); setPassMsg(null)
    const r = await accountApi.updateSecurity(currentPass, newPass, csrf)
    const d = await r.json()
    setSavingPass(false)
    setPassMsg(r.ok ? { type: 'success', text: 'Password changed.' }
                    : { type: 'error',   text: d.error })
    if (r.ok) { setCurrentPass(''); setNewPass('') }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Settings</h1>
        <p className="text-slate-500 text-sm mt-0.5">Manage your account preferences</p>
      </div>

      {/* Notifications */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 mb-6">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2 mb-2">
          <Bell className="w-4 h-4 text-indigo-400" /> Notification Address
        </h2>
        <p className="text-slate-500 text-sm mb-1">
          All system alerts, deck review results, and internal workflow emails go here.
          Can differ from your login email — useful for team inboxes or Slack integrations.
        </p>
        <p className="text-slate-600 text-xs mb-1">
          Security-sensitive recovery flows are sent to your primary account email, not this operational mailbox.
        </p>
        <p className="text-slate-600 text-xs mb-2">
          Legacy one-click notification links in older emails still use direct GET callbacks.
          If opened while authenticated, they update your notification routing instantly.
        </p>
        <form onSubmit={saveNotifications} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Notification email</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
              type="text"
              value={notifyEmail}
              onChange={e => setNotifyEmail(e.target.value)}
              placeholder="alerts@yourstartup.com"
            />
            <p className="text-slate-600 text-xs mt-1.5">
              Use a <span className="font-mono">@dar-lmohsinin.ma</span> address to receive
              notifications in the in-app bell instead.
            </p>
          </div>
          <Toast msg={notifyMsg} />
          <button
            type="submit"
            disabled={savingNotify}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-50 text-white text-sm font-medium
                       px-4 py-2 rounded-xl transition-colors"
          >
            {savingNotify
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Save className="w-4 h-4" />}
            {savingNotify ? 'Saving…' : 'Save'}
          </button>
        </form>
      </div>

      {/* Security */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2 mb-5">
          <Shield className="w-4 h-4 text-indigo-400" /> Security
        </h2>
        <form onSubmit={saveSecurity} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Current password</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
              type="password"
              value={currentPass}
              onChange={e => setCurrentPass(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">New password</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
              type="password"
              value={newPass}
              onChange={e => setNewPass(e.target.value)}
            />
          </div>
          <Toast msg={passMsg} />
          <button
            type="submit"
            disabled={savingPass}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-50 text-white text-sm font-medium
                       px-4 py-2 rounded-xl transition-colors"
          >
            {savingPass
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Lock className="w-4 h-4" />}
            {savingPass ? 'Saving…' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
