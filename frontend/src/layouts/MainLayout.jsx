import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Shield,
  LayoutDashboard,
  Target,
  FolderSearch,
  AlertTriangle,
  Globe,
  SlidersHorizontal,
  Settings,
  Menu,
  X,
  ExternalLink
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Targets', href: '/targets', icon: Target },
  { name: 'Assessments', href: '/assessments', icon: FolderSearch },
  { name: 'Attack Surface', href: '/attack-surface', icon: Globe },
  { name: 'Scan Jobs', href: '/scan-jobs', icon: SlidersHorizontal },
  { name: 'Findings', href: '/findings', icon: AlertTriangle },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function MainLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen bg-[#050811] text-slate-100 flex flex-col">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-[#090d16] border-r border-[#1a2333] transform transition-transform duration-200 ease-in-out lg:translate-x-0 flex flex-col justify-between',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div>
          {/* Brand Header */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-[#1a2333]">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                <Shield className="w-5 h-5 text-[#00ff66]" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-wider text-white font-mono uppercase">
                  Aegis<span className="text-[#00ff66]">Scan</span>
                </span>
                <span className="text-[9px] uppercase font-mono tracking-widest text-[#00f0ff]">
                  AppSec Platform
                </span>
              </div>
            </Link>
            <button
              className="lg:hidden text-slate-400 hover:text-white p-2 min-h-[44px] min-w-[44px] flex items-center justify-center"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Nav items */}
          <nav className="p-4 space-y-1.5" aria-label="Main Navigation">
            {navigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== '/' && location.pathname.startsWith(item.href))
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all min-h-[44px]',
                    isActive
                      ? 'bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 font-semibold shadow-[0_0_12px_rgba(0,255,102,0.15)]'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-[#121927]'
                  )}
                >
                  <item.icon className={clsx('w-5 h-5', isActive ? 'text-[#00ff66]' : 'text-slate-400')} />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Safety & Environment Badge */}
        <div className="p-4 border-t border-[#1a2333] bg-[#070b13]">
          <div className="p-3 bg-[#0d1422] border border-[#1e2a3e] rounded-xl text-xs">
            <div className="flex items-center gap-2 font-medium text-emerald-400 mb-1">
              <Shield className="w-3.5 h-3.5 text-[#00ff66]" />
              <span className="font-mono text-[11px] tracking-wide">AUTHORIZED SCOPE</span>
            </div>
            <p className="text-[10px] leading-relaxed text-slate-400 font-mono">
              Evidence-based verification. Non-destructive automated checks.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="lg:pl-64 flex-1 flex flex-col">
        {/* Header bar */}
        <header className="sticky top-0 z-30 h-16 bg-[#090d16]/90 backdrop-blur-md border-b border-[#1a2333]">
          <div className="flex items-center justify-between h-full px-6">
            <button
              className="lg:hidden text-slate-400 hover:text-white p-2 min-h-[44px] min-w-[44px] flex items-center justify-center"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/30">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-pulse" />
                SIH26163 Security Engine
              </span>
              <span className="text-xs text-slate-400 font-mono bg-[#121927] px-2.5 py-1 rounded border border-[#1a2333]">
                v1.0.0
              </span>
            </div>
          </div>
        </header>

        {/* Page Container */}
        <main className="p-4 sm:p-6 max-w-7xl mx-auto w-full flex-1">
          {children}
        </main>
      </div>
    </div>
  )
}
