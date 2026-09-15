import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { analyticsApi, projectsApi, flagApi } from '../lib/api'
import { TrendingUp, Folder, Star, ArrowRight, Shield } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuth()
  const [projects, setProjects] = useState([])
  const [flag,     setFlag]     = useState(null)

  useEffect(() => {
    projectsApi.list().then(r => r.json()).then(d => setProjects(Array.isArray(d) ? d : []))
    if (user?.role === 'admin') {
      flagApi.capture().then(r => r.ok ? r.json() : null).then(d => d && setFlag(d.flag))
    }
  }, [user])

  const reviewed = projects.filter(p => p.status === 'reviewed').length
  const avgScore = projects.length
    ? Math.round(projects.reduce((s, p) => s + (p.score || 0), 0) / projects.length)
    : 0

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
          Welcome back, {user?.display_name || user?.username}
        </h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Si Issam created this platform to support startups from Al Mohssinin. If you have a good idea, submit your pitch deck preview so Si Issam can review it.
        </p>
      </div>

      {/* Admin flag banner */}
      {flag && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5 mb-6">
          <div className="flex items-start gap-4 mb-4">
            <Shield className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-300 text-sm mb-1">Admin Access — Flag Captured</p>
              <p className="font-mono text-emerald-200 text-sm">{flag}</p>
            </div>
          </div>
          <img
            src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSsAuoe2w86zSsAn_nO0KRdbm8ue8ZYH831Jg&s"
            alt="admin image"
            className="rounded-lg w-64 mt-2 border border-emerald-700/40"
            referrerPolicy="no-referrer"
          />
          <p className="text-emerald-600 text-xs mt-2 font-mono">
            // Lahydewemha neama lflag olma 
          </p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          { icon: Folder, label: 'Decks Submitted', value: projects.length },
          { icon: Star,   label: 'Reviewed',         value: reviewed },
          { icon: TrendingUp, label: 'Avg Score',    value: avgScore || '—' },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-3">
              <Icon className="w-3.5 h-3.5" /> {label}
            </div>
            <p className="text-3xl font-bold text-slate-100">{value}</p>
          </div>
        ))}
      </div>

      {/* Recent projects */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-200">Recent Projects</h2>
          <Link to="/projects" className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors
                                          flex items-center gap-1">
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        {projects.slice(0, 3).length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 py-10 text-center">
            <img
              src="https://c.tenor.com/VfmnI3EcyoMAAAAd/tenor.gif"
              alt="empty"
              className="w-32 rounded-lg mx-auto mb-4 border border-slate-800"
            />
            <p className="text-slate-500 text-sm">No projects yet. The bot has nothing to fetch.</p>
            <Link to="/projects" className="text-indigo-400 hover:text-indigo-300 text-sm mt-2 inline-block">
              Submit your first deck →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 3).map(p => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                className="flex items-center justify-between bg-slate-900/60 border border-slate-800
                           rounded-xl p-4 hover:border-slate-700 transition-colors group"
              >
                <div>
                  <p className="font-medium text-slate-200 group-hover:text-white transition-colors text-sm">
                    {p.name}
                  </p>
                  <p className="text-slate-500 text-xs mt-0.5">
                    {p.status === 'reviewed' ? `Score: ${p.score}` : 'Under review…'}
                  </p>
                  <p className="text-slate-600 text-[11px] mt-1">
                    {p.status === 'reviewed'
                      ? 'Reviewed by Automated Compliance Bot'
                      : 'Awaiting Automated Compliance Bot fetch'}
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
