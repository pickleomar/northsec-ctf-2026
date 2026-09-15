import { useEffect, useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import { accountApi } from '../lib/api'
import { User, FileText, CheckCircle2, AlertCircle, Loader2, Save } from 'lucide-react'

function Toast({ msg }) {
  if (!msg) return null
  const ok = msg.type === 'success'
  return (
    <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm
      ${ok ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
           : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" />
          : <AlertCircle className="w-4 h-4 shrink-0" />}
      {msg.text}
    </div>
  )
}

export default function ProfilePage() {
  const { user, csrf } = useAuth()
  const [displayName, setDisplayName] = useState('')
  const [bio,         setBio]         = useState('')
  const [saving,      setSaving]      = useState(false)
  const [msg,         setMsg]         = useState(null)

  useEffect(() => {
    accountApi.profile()
      .then(r => r.json())
      .then(d => {
        setDisplayName(d.display_name || '')
        setBio(d.bio || '')
      })
  }, [])

  const save = async (e) => {
    e.preventDefault()
    setSaving(true); setMsg(null)
    const r = await accountApi.updateProfile(displayName, bio, csrf)
    const d = await r.json()
    setSaving(false)
    setMsg(r.ok ? { type: 'success', text: 'Profile updated.' }
                : { type: 'error',   text: d.error })
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Profile</h1>
        <p className="text-slate-500 text-sm mt-0.5">Manage your public founder profile</p>
      </div>

      {/* Identity card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 mb-6 flex items-center gap-4">
        <div className="w-14 h-14 rounded-xl bg-indigo-700
                        flex items-center justify-center shadow-sm shrink-0">
          <span className="text-2xl font-bold text-white">
            {user?.username?.[0]?.toUpperCase()}
          </span>
        </div>
        <div>
          <p className="font-bold text-slate-100">{user?.username}</p>
          <p className="text-slate-500 text-sm">{user?.email}</p>
        </div>
      </div>

      {/* Edit form */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2 mb-5">
          <User className="w-4 h-4 text-indigo-400" /> Founder Bio
        </h2>
        <form onSubmit={save} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Display Name</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              placeholder="Jane Smith"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Bio</label>
            <textarea
              rows={4}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm outline-none focus:border-indigo-500 transition-colors resize-none"
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder="Second-time founder. Previously built..."
            />
          </div>
          <Toast msg={msg} />
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-50 text-white text-sm font-medium
                       px-4 py-2 rounded-xl transition-colors"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
