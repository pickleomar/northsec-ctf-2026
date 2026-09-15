import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import {
  LayoutDashboard, FolderOpen, User, Settings, LogOut, Zap, Shield
} from 'lucide-react'
import NotificationBell from './NotificationBell'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects',  icon: FolderOpen,      label: 'Projects' },
  { to: '/profile',   icon: User,             label: 'Profile' },
  { to: '/settings',  icon: Settings,         label: 'Settings' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/auth')
  }

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col
                       border-r border-slate-800 bg-slate-950">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-indigo-700 rounded-lg flex items-center justify-center shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-slate-100 tracking-tight">Dar Mohssinin</span>
          {user?.role === 'admin' && (
            <Shield className="w-3 h-3 text-amber-400" />
          )}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] text-slate-500 hidden md:inline">Alerts</span>
            <NotificationBell />
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all
               ${isActive
                 ? 'bg-indigo-600/15 text-indigo-300 font-medium'
                 : 'text-slate-500 hover:text-slate-200 hover:bg-slate-800/60'}`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 py-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-700
                          flex items-center justify-center shrink-0">
            {user?.role === 'admin' ? (
              <img
                src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTkTG8IihgHRFS0Eisal0o6F4BhkKz53jMSbg&s"
                alt="admin avatar"
                className="w-7 h-7 rounded-lg object-cover"
                referrerPolicy="no-referrer"
              />
            ) : (
              <span className="text-xs font-bold text-white">
                {user?.username?.[0]?.toUpperCase()}
              </span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-200 truncate">{user?.username}</p>
            <p className="text-xs text-slate-600 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm
                     text-slate-500 hover:text-slate-200 hover:bg-slate-800/60 transition-all"
        >
          <LogOut className="w-4 h-4 shrink-0" /> Sign Out
        </button>
      </div>
    </aside>
  )
}
