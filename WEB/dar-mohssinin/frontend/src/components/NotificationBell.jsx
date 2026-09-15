import { useEffect, useState, useRef } from 'react'
import { Bell, X, Mail, BarChart3, Info, Shield } from 'lucide-react'
import { notificationsApi } from '../lib/api'

const TYPE_ICON = {
  deck_reviewed:     BarChart3,
  admin_ops:         Shield,
  investor_match:    Mail,
}

function NotifItem({ n, onUseLink }) {
  const Icon = TYPE_ICON[n.type] || Info
  const ago  = formatAgo(n.created_at)
  return (
    <div className="flex items-start gap-3 px-4 py-3 hover:bg-slate-800/60 transition-colors">
      <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-3.5 h-3.5 text-indigo-400" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-slate-200 text-sm font-medium leading-snug">{n.title}</p>
        <p className="text-slate-500 text-xs mt-0.5 leading-relaxed">{n.body}</p>
        {n.type === 'admin_ops' && n.link && (
          <div className="mt-2 rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-2.5">
            <p className="text-[11px] text-indigo-300 mb-2">Admin action required</p>
            <button
              onClick={() => onUseLink(n.link)}
              className="text-[11px] px-2.5 py-1.5 rounded-md border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500"
            >
              Open Compliance Queue
            </button>
            {n.project_name && (
              <p className="text-[11px] text-slate-500 mt-2">
                Project: <span className="text-slate-400">{n.project_name}</span>
              </p>
            )}
          </div>
        )}
        <p className="text-slate-600 text-xs mt-1">{ago}</p>
      </div>
    </div>
  )
}

function formatAgo(ts) {
  if (!ts) return ''
  const diff = Math.floor(Date.now() / 1000) - ts
  if (diff < 60)   return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function NotificationBell() {
  const [open,   setOpen]   = useState(false)
  const [items,  setItems]  = useState([])
  const [addr,   setAddr]   = useState('')
  const [unread, setUnread] = useState(0)
  const ref = useRef(null)

  const poll = () => {
    notificationsApi.feed()
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return
        setItems(d.notifications || [])
        setAddr(d.address || '')
        setUnread((d.notifications || []).filter(n => !n.read).length)
      })
      .catch(() => {})
  }

  const useMagicLink = async (link) => {
    if (!link) return
    try {
      const r = await fetch(link, {
        credentials: 'include',
        headers: { 'X-Requested-With': 'FolioClient/2' },
      })
      if (r.ok) {
        window.location.href = '/dashboard'
      }
    } catch {
      // silent UI fallback
    }
  }

  useEffect(() => {
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => { setOpen(o => !o); setUnread(0) }}
        className="relative w-8 h-8 flex items-center justify-center rounded-lg
                   text-slate-500 hover:text-slate-300 hover:bg-slate-800
                   transition-colors"
        title="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unread > 0 && (
          <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-indigo-500" />
        )}
      </button>

      {open && (
        <div className="absolute left-0 top-10 w-80 bg-slate-900 border border-slate-800
                        rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
            <div>
              <p className="text-slate-200 text-sm font-semibold">Notifications</p>
              {addr && (
                <p className="text-slate-600 text-xs mt-0.5 font-mono truncate max-w-[200px]">
                  → {addr}
                </p>
              )}
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-600 hover:text-slate-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <Bell className="w-6 h-6 text-slate-700 mx-auto mb-2" />
                <p className="text-slate-600 text-xs">
                  {addr && !addr.endsWith('@dar-lmohsinin.ma')
                    ? 'External address — notifications delivered via email.'
                    : 'No notifications yet.'}
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {items.map((n, i) => (
                  <NotifItem
                    key={n.id || i}
                    n={n}
                    onUseLink={useMagicLink}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2.5 border-t border-slate-800 bg-slate-950/40">
            <p className="text-slate-700 text-xs">
              Delivery address set in{' '}
              <a href="/settings" className="text-slate-500 hover:text-slate-400 transition-colors">
                Settings → Notifications
              </a>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
