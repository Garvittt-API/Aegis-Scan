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
  X
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
    <div className="min-h-screen bg-dark-950">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-dark-900 border-r border-dark-800 transform transition-transform duration-200 ease-in-out lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-dark-800">
          <Link to="/" className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-500" />
            <div className="flex flex-col">
              <span className="text-xl font-semibold text-white tracking-tight">AegisScan</span>
              <span className="text-[10px] uppercase font-mono tracking-wider text-blue-400">Security Platform</span>
            </div>
          </Link>
          <button
            className="lg:hidden text-dark-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href))
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20'
                    : 'text-dark-400 hover:text-white hover:bg-dark-800'
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Safety Badge in Sidebar */}
        <div className="absolute bottom-4 left-4 right-4 p-3 bg-dark-800/60 border border-dark-700/50 rounded-xl text-xs text-dark-400">
          <div className="flex items-center gap-2 font-medium text-dark-300 mb-1">
            <Shield className="w-4 h-4 text-green-400" />
            <span>Authorized Scope Only</span>
          </div>
          <p className="text-[11px] leading-relaxed text-dark-400">
            Local-first verification mode enabled. Non-destructive scanning.
          </p>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-dark-900/80 backdrop-blur-sm border-b border-dark-800">
          <div className="flex items-center justify-between h-full px-6">
            <button
              className="lg:hidden text-dark-400 hover:text-white"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Phase 3: Discovery & Orchestrator
              </span>
              <span className="text-sm text-dark-400 font-mono">
                v1.2.0
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6 max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
