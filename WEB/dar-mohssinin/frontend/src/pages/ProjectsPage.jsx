import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Loader2, ArrowRight, Clock, CheckCircle2, BarChart3, X } from 'lucide-react'
import { projectsApi } from '../lib/api'

function fmtReviewTime(ts) {
  if (!ts) return 'recently'
  try {
    return new Date(ts * 1000).toLocaleString()
  } catch {
    return 'recently'
  }
}

function CreateModal({ onClose, onCreated }) {
  const [name,  setName]  = useState('')
  const [desc,  setDesc]  = useState('')
  const [slug,  setSlug]  = useState('')
  const [busy,  setBusy]  = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    if (!name.trim() || !slug.trim()) { setError('Name and preview URL are required'); return }
    setBusy(true); setError('')
    try {
      const r = await projectsApi.create(name.trim(), desc.trim(), slug.trim())
      const d = await r.json()
      if (!r.ok) { setError(d.error || 'Failed to create project'); setBusy(false); return }
      onCreated(d)
    } catch (e) {
      setError('Network error — please try again')
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800">
          <h2 className="font-bold text-slate-100 text-lg">Submit New Deck</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Project Name *</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm placeholder-slate-500 outline-none
                         focus:border-indigo-500 transition-colors"
              placeholder="Series A Round — Q1 2025"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Description</label>
            <textarea
              rows={2}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm placeholder-slate-500 outline-none
                         focus:border-indigo-500 transition-colors resize-none"
              placeholder="Brief overview of your startup and round..."
              value={desc}
              onChange={e => setDesc(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Deck Preview URL *</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5
                         text-slate-100 text-sm font-mono placeholder-slate-500 outline-none
                         focus:border-indigo-500 transition-colors"
              placeholder="https://pitch.com/v/my-deck"
              value={slug}
              onChange={e => setSlug(e.target.value)}
            />
            <p className="text-xs text-slate-600 mt-1.5">
              Our bot will verify the live preview is reachable before scoring.
            </p>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20
                           rounded-xl px-4 py-2.5">{error}</p>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-800 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-50 text-white text-sm font-medium
                       px-5 py-2 rounded-xl transition-colors"
          >
            {busy && <Loader2 className="w-4 h-4 animate-spin" />}
            {busy ? 'Submitting…' : 'Submit for Review'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    setLoading(true)
    projectsApi.list()
      .then(r => r.json())
      .then(d => { setProjects(Array.isArray(d) ? d : []); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Projects</h1>
          <p className="text-slate-500 text-sm mt-0.5">Submit your pitch deck for AI scoring and investor matching</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white
                     text-sm font-medium px-4 py-2 rounded-xl transition-colors"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 text-slate-500 py-12">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading projects...</span>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
          <img
            src="https://c.tenor.com/VfmnI3EcyoMAAAAd/tenor.gif"
            alt="no projects"
            className="w-40 rounded-lg mx-auto mb-4 border border-slate-800"
          />
          <p className="text-slate-500 text-sm">No projects yet. The admin bot is bored.</p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-4 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            Submit your first deck →
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {projects.map(p => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="flex items-center justify-between bg-slate-900/60 border border-slate-800
                         rounded-2xl p-5 hover:border-slate-700 transition-colors group"
            >
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-slate-200 group-hover:text-white transition-colors truncate">
                  {p.name}
                </p>
                {p.description && (
                  <p className="text-slate-500 text-sm mt-0.5 truncate">{p.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  <span className={`text-xs flex items-center gap-1.5 ${
                    p.status === 'reviewed' ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {p.status === 'reviewed'
                      ? <CheckCircle2 className="w-3.5 h-3.5" />
                      : <Clock className="w-3.5 h-3.5" />}
                    {p.status === 'reviewed' ? 'Reviewed' : 'Under Review'}
                  </span>
                  {p.score > 0 && (
                    <span className="text-xs text-indigo-300 flex items-center gap-1">
                      <BarChart3 className="w-3.5 h-3.5" />
                      Score: {p.score}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  {p.status === 'reviewed'
                    ? `Reviewed by Automated Compliance Bot • ${fmtReviewTime(p.reviewed_at)}`
                    : 'Queued for Automated Compliance Bot review'}
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400
                                     transition-colors shrink-0 ml-4" />
            </Link>
          ))}
        </div>
      )}

      {showForm && (
        <CreateModal
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); load() }}
        />
      )}
    </div>
  )
}
