import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, Globe, Loader2, AlertCircle, CheckCircle2,
  Clock, Star, BarChart3, ExternalLink
} from 'lucide-react'
import { projectsApi } from '../lib/api'

const STATUS_CONFIG = {
  pending:  { color: 'text-amber-400 bg-amber-400/10 border-amber-400/20', label: 'Under Review' },
  reviewed: { color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20', label: 'Reviewed' },
}

function fmtReviewTime(ts) {
  if (!ts) return 'recently'
  try {
    return new Date(ts * 1000).toLocaleString()
  } catch {
    return 'recently'
  }
}

export default function ProjectDetailPage() {
  const { id }                     = useParams()
  const [project, setProject]      = useState(null)
  const [preview,  setPreview]     = useState(null)
  const [error,    setError]       = useState('')
  const [loading,  setLoading]     = useState(true)
  const [previewLoading, setPvLoad] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)

    projectsApi.getById(id)
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        if (data.error) { setError(data.error); setLoading(false); return }
        setProject(data)
        setLoading(false)

        // Attempt to load live preview metadata for the submitted deck URL.
        // buildPreviewEndpoint() (see api.js) resolves the slug relative to
        // the preview catalog root before fetching — normalizes ../ segments.
        if (data.preview_slug) {
          setPvLoad(true)
          projectsApi.fetchPreview(data.preview_slug)
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d && !d.error) setPreview(d) })
            .catch(() => {})
            .finally(() => setPvLoad(false))
        }
      })
      .catch(() => { setError('Failed to load project'); setLoading(false) })
  }, [id])

  const cfg = STATUS_CONFIG[project?.status] || STATUS_CONFIG.pending

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <Link
        to="/projects"
        className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300
                   text-sm mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Projects
      </Link>

      <h1 className="text-2xl font-bold text-slate-100 mb-6 tracking-tight">Project Details</h1>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-12">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading project...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5
                        flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-400">Error</p>
            <p className="text-slate-400 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {project && (
        <div className="space-y-5">
          {/* Main card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-start justify-between gap-4 mb-5">
              <div>
                <h2 className="text-xl font-bold text-slate-100">{project.name}</h2>
                {project.description && (
                  <p className="text-slate-400 text-sm mt-1">{project.description}</p>
                )}
              </div>
              <span className={`shrink-0 text-xs font-medium px-3 py-1 rounded-full border ${cfg.color}`}>
                {cfg.label}
              </span>
            </div>
            <p className="text-xs text-slate-600 mb-4">
              {project.status === 'reviewed'
                ? `Reviewed by Automated Compliance Bot • ${fmtReviewTime(project.reviewed_at)}`
                : 'Queued for Automated Compliance Bot review'}
            </p>

            {/* Preview slug */}
            <div className="flex items-center gap-2 bg-slate-800/60 rounded-lg px-3 py-2 mb-5">
              <Globe className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span className="text-slate-400 text-xs font-mono truncate">{project.preview_slug}</span>
              <a
                href={`https://${project.preview_slug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto text-slate-600 hover:text-slate-400 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            {/* Score */}
            {project.score > 0 && (
              <div className="flex items-center gap-3 mb-5">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <span className="text-sm text-slate-300">
                  Dar Mohssinin Score: <span className="font-bold text-indigo-300">{project.score}</span>
                  <span className="text-slate-500">/100</span>
                </span>
              </div>
            )}

            {/* Feedback */}
            {project.feedback ? (
              <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3">
                <p className="text-xs font-mono text-indigo-300 mb-1.5 flex items-center gap-1.5">
                  <Star className="w-3 h-3" /> Investor Feedback
                </p>
                <p className="text-slate-300 text-sm leading-relaxed">{project.feedback}</p>
                <img
                  src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSeLqGrkGAJ_il6NUL-uHZRGxcNFiOQO_dknQ&s"
                  alt="reviewed project"
                  className="rounded-lg w-52 mt-3 border border-indigo-700/40"
                  referrerPolicy="no-referrer"
                />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <Clock className="w-4 h-4" />
                  Awaiting review — our team will analyse your deck shortly.
                </div>
                <img
                  src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ-uAKQjNGt01709KTDNWVm7YOjSmjheplLCA&s"
                  alt="waiting for admin bot"
                  className="rounded-lg w-48 border border-slate-700/60"
                />
              </div>
            )}
          </div>

          {/* Preview metadata */}
          {previewLoading && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4
                            flex items-center gap-3 text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              Fetching live preview metadata...
            </div>
          )}

          {preview && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-2">
                Preview Confirmed
              </p>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <p className="text-slate-300 text-sm">
                  Live preview reachable at <span className="font-mono text-xs">{preview.preview_slug}</span>
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
