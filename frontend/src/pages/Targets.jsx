import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Target,
  Plus,
  Search,
  Globe,
  Code,
  FolderGit2,
  Laptop,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Edit2,
  Trash2,
  Shield,
  Clock,
  Play,
  X,
  Terminal,
  Crosshair
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const TARGET_TYPE_ICONS = {
  web: Globe,
  source_code: Code,
  repository: FolderGit2,
  local_application: Laptop
}

const ENV_BADGES = {
  local: 'bg-cyber-accent/10 text-cyber-accent border-cyber-accent/40 shadow-[0_0_8px_rgba(0,255,136,0.2)]',
  staging: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/40',
  production: 'bg-cyber-destructive/10 text-cyber-destructive border-cyber-destructive/40 shadow-[0_0_8px_rgba(255,51,102,0.2)]',
  authorized_remote: 'bg-cyber-cyan/10 text-cyber-cyan border-cyber-cyan/40 shadow-[0_0_8px_rgba(0,212,255,0.2)]'
}

export default function Targets() {
  const navigate = useNavigate()
  const [targets, setTargets] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [envFilter, setEnvFilter] = useState('')

  // Modal States
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTarget, setEditingTarget] = useState(null)
  const [deleteConfirmTarget, setDeleteConfirmTarget] = useState(null)
  const [modalError, setModalError] = useState('')
  const [saving, setSaving] = useState(false)

  // Target Form Data
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_type: 'web',
    base_url: '',
    source_path: '',
    repository_path: '',
    environment: 'local',
    authorization_status: 'authorized',
    notes: '',
    status: 'active'
  })

  useEffect(() => {
    fetchTargets()
  }, [typeFilter, envFilter])

  const fetchTargets = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (typeFilter) params.append('target_type', typeFilter)
      if (envFilter) params.append('environment', envFilter)
      params.append('limit', '100')

      const res = await api.get(`/targets?${params}`)
      setTargets(res.data.items || [])
    } catch (err) {
      console.error('Failed to load targets:', err)
    } finally {
      setLoading(false)
    }
  }

  const openAddModal = () => {
    setEditingTarget(null)
    setFormData({
      name: '',
      description: '',
      target_type: 'web',
      base_url: '',
      source_path: '',
      repository_path: '',
      environment: 'local',
      authorization_status: 'authorized',
      notes: '',
      status: 'active'
    })
    setModalError('')
    setModalOpen(true)
  }

  const openEditModal = (target) => {
    setEditingTarget(target)
    setFormData({
      name: target.name || '',
      description: target.description || '',
      target_type: target.target_type || 'web',
      base_url: target.base_url || '',
      source_path: target.source_path || '',
      repository_path: target.repository_path || '',
      environment: target.environment || 'local',
      authorization_status: target.authorization_status || 'authorized',
      notes: target.notes || '',
      status: target.status || 'active'
    })
    setModalError('')
    setModalOpen(true)
  }

  const handleSaveTarget = async (e) => {
    e.preventDefault()
    setModalError('')

    if (!formData.name.trim()) {
      setModalError('Target name is required')
      return
    }

    if (!formData.base_url && !formData.source_path && !formData.repository_path) {
      setModalError('Please provide at least one target location (Base URL, Source Path, or Repository Path)')
      return
    }

    setSaving(true)
    try {
      if (editingTarget) {
        await api.put(`/targets/${editingTarget.id}`, formData)
      } else {
        await api.post('/targets', formData)
      }
      setModalOpen(false)
      fetchTargets()
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        setModalError(detail)
      } else if (Array.isArray(detail)) {
        setModalError(detail.map(d => d.msg || d.message).join(', '))
      } else {
        setModalError('Failed to save target. Check inputs.')
      }
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteTarget = async () => {
    if (!deleteConfirmTarget) return
    try {
      await api.delete(`/targets/${deleteConfirmTarget.id}`)
      setDeleteConfirmTarget(null)
      fetchTargets()
    } catch (err) {
      console.error('Failed to delete target:', err)
    }
  }

  const filteredTargets = targets.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.base_url?.toLowerCase().includes(search.toLowerCase()) ||
    t.source_path?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-cyber-border pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-cyber-cyan mb-1">
            <Crosshair className="w-4 h-4 text-cyber-cyan" />
            <span>SCOPE REGISTRY // AUTH_TARGETS.DB</span>
          </div>
          <h1 className="text-3xl font-black uppercase tracking-wider font-orbitron text-white">
            TARGET ASSET MATRIX
          </h1>
          <p className="text-cyber-muted text-xs tracking-wider uppercase mt-1">
            &gt; CONFIGURE AUTHORIZED EVALUATION BOUNDARIES AND CODEBASES
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={openAddModal}
            className="cyber-btn-primary flex items-center gap-2 text-xs py-2.5 px-4 uppercase tracking-widest"
          >
            <Plus className="w-4 h-4" />
            <span>REGISTER TARGET</span>
          </button>
        </div>
      </div>

      {/* Safety Notice HUD */}
      <div className="cyber-card p-4 flex items-start gap-3 bg-cyber-void border-cyber-cyan/30 shadow-[0_0_15px_rgba(0,212,255,0.08)]">
        <Shield className="w-5 h-5 text-cyber-cyan flex-shrink-0 mt-0.5" />
        <div className="text-xs text-cyber-foreground/80 leading-relaxed">
          <span className="font-bold text-cyber-cyan tracking-wider uppercase mr-2">&gt; AUTHORIZATION MANDATE:</span>
          AegisScan operates strictly within authorized test parameters. All targets registered must adhere to legal authorization bounds. Private IP address blocks are governed by deployment configuration.
        </div>
      </div>

      {/* Filters & Search */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative md:col-span-2">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-cyber-accent font-bold text-sm">&gt;</span>
          <input
            type="text"
            placeholder="SEARCH TARGETS (NAME, URL, PATH)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="cyber-input w-full pl-8 pr-4 py-2.5 text-xs text-cyber-accent placeholder:text-cyber-muted uppercase"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="cyber-input px-3 py-2.5 text-xs text-cyber-foreground uppercase bg-cyber-card"
        >
          <option value="">ALL TARGET TYPES</option>
          <option value="web">WEB APPLICATION (DAST)</option>
          <option value="source_code">SOURCE CODE (SAST)</option>
          <option value="repository">GIT REPOSITORY</option>
          <option value="local_application">LOCAL APPLICATION</option>
        </select>
        <select
          value={envFilter}
          onChange={(e) => setEnvFilter(e.target.value)}
          className="cyber-input px-3 py-2.5 text-xs text-cyber-foreground uppercase bg-cyber-card"
        >
          <option value="">ALL ENVIRONMENTS</option>
          <option value="local">LOCAL DEV</option>
          <option value="staging">STAGING ENV</option>
          <option value="production">PRODUCTION</option>
          <option value="authorized_remote">AUTH REMOTE</option>
        </select>
      </div>

      {/* Target Cards / List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-3">
          <div className="w-12 h-12 rounded-full border-2 border-t-cyber-accent border-r-cyber-secondary border-b-transparent border-l-transparent animate-spin" />
          <p className="text-xs text-cyber-muted tracking-widest uppercase">SCANNING TARGET REGISTRY...</p>
        </div>
      ) : filteredTargets.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {filteredTargets.map((target) => {
            const Icon = TARGET_TYPE_ICONS[target.target_type] || Target
            return (
              <div
                key={target.id}
                className="cyber-card p-5 relative flex flex-col justify-between group hover:border-cyber-accent/60 transition-all duration-200"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 bg-cyber-void border border-cyber-accent/40 text-cyber-accent shadow-[0_0_8px_rgba(0,255,136,0.2)]">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white uppercase tracking-wider font-orbitron group-hover:text-cyber-accent transition-colors">
                          {target.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={clsx('px-2 py-0.5 text-[10px] uppercase font-bold tracking-widest border', ENV_BADGES[target.environment] || ENV_BADGES.local)}>
                            {target.environment}
                          </span>
                          <span className="text-[10px] text-cyber-muted uppercase tracking-wider">
                            // {target.target_type.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => openEditModal(target)}
                        className="p-1.5 text-cyber-muted hover:text-cyber-cyan border border-transparent hover:border-cyber-cyan/40 bg-cyber-void transition-colors"
                        title="EDIT TARGET CONFIG"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeleteConfirmTarget(target)}
                        className="p-1.5 text-cyber-muted hover:text-cyber-destructive border border-transparent hover:border-cyber-destructive/40 bg-cyber-void transition-colors"
                        title="DELETE TARGET"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Target Description */}
                  {target.description && (
                    <p className="text-xs text-cyber-foreground/80 mt-3 line-clamp-2 leading-relaxed">
                      {target.description}
                    </p>
                  )}

                  {/* Endpoints & Paths */}
                  <div className="mt-4 space-y-2 text-xs font-mono">
                    {target.base_url && (
                      <div className="flex items-center gap-2 text-cyber-foreground/90 bg-cyber-void px-3 py-1.5 border border-cyber-border truncate">
                        <span className="text-cyber-muted font-bold">URI:</span>
                        <span className="truncate text-cyber-cyan font-bold">{target.base_url}</span>
                      </div>
                    )}
                    {target.source_path && (
                      <div className="flex items-center gap-2 text-cyber-foreground/90 bg-cyber-void px-3 py-1.5 border border-cyber-border truncate">
                        <span className="text-cyber-muted font-bold">PATH:</span>
                        <span className="truncate text-cyber-accent font-bold">{target.source_path}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer */}
                <div className="mt-5 pt-3.5 border-t border-cyber-border/60 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-cyber-muted">
                    <Clock className="w-3.5 h-3.5 text-cyber-secondary" />
                    <span className="tracking-wider uppercase text-[11px]">{target.assessments_count} ENGAGEMENTS</span>
                  </div>
                  <button
                    onClick={() => navigate(`/assessments/new?target_id=${target.id}`)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-cyber-accent/10 hover:bg-cyber-accent text-cyber-accent hover:text-cyber-void border border-cyber-accent font-bold text-[11px] uppercase tracking-widest transition-all duration-150 shadow-[0_0_10px_rgba(0,255,136,0.2)]"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    <span>LAUNCH SCAN</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="cyber-card p-12 flex flex-col items-center justify-center text-center bg-cyber-void border-dashed border-cyber-border">
          <Target className="w-12 h-12 text-cyber-muted mb-3 opacity-40 animate-pulse" />
          <h3 className="text-base font-bold text-white uppercase tracking-wider font-orbitron">
            NO TARGETS CONFIGURED
          </h3>
          <p className="text-xs text-cyber-muted uppercase tracking-widest mt-1 max-w-md">
            REGISTER A WEB APPLICATION ENDPOINT, REPOSITORY, OR LOCAL SOURCE CODEBASE TO COMMENCE SECURITY TELEMETRY.
          </p>
          <button
            onClick={openAddModal}
            className="cyber-btn-primary mt-6 px-5 py-2.5 text-xs uppercase tracking-widest"
          >
            + REGISTER FIRST TARGET
          </button>
        </div>
      )}

      {/* ADD / EDIT TARGET MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-cyber-void/85 backdrop-blur-md">
          <div className="cyber-card max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 border-cyber-accent/60 shadow-[0_0_30px_rgba(0,255,136,0.2)] bg-cyber-card">
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-cyber-accent" />
                <h2 className="text-base font-black text-white uppercase tracking-wider font-orbitron">
                  {editingTarget ? 'MODIFY TARGET SCOPE' : 'REGISTER TARGET SCOPE'}
                </h2>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-cyber-muted hover:text-cyber-accent transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="mt-4 p-3 bg-cyber-destructive/10 border border-cyber-destructive/40 text-cyber-destructive text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleSaveTarget} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                  TARGET IDENTIFIER / NAME *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. WORLD MONITOR LOCALHOST"
                  className="cyber-input w-full px-3 py-2 text-cyber-accent uppercase"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                    TARGET TYPE
                  </label>
                  <select
                    value={formData.target_type}
                    onChange={(e) => setFormData({ ...formData, target_type: e.target.value })}
                    className="cyber-input w-full px-3 py-2 text-white bg-cyber-void uppercase"
                  >
                    <option value="web">WEB APPLICATION</option>
                    <option value="source_code">SOURCE CODE</option>
                    <option value="repository">GIT REPOSITORY</option>
                    <option value="local_application">LOCAL APP</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                    ENVIRONMENT
                  </label>
                  <select
                    value={formData.environment}
                    onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                    className="cyber-input w-full px-3 py-2 text-white bg-cyber-void uppercase"
                  >
                    <option value="local">LOCAL</option>
                    <option value="staging">STAGING</option>
                    <option value="production">PRODUCTION</option>
                    <option value="authorized_remote">AUTH REMOTE</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                  BASE URL (FOR DAST / NETWORK AUDIT)
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  placeholder="http://localhost:5173"
                  className="cyber-input w-full px-3 py-2 text-cyber-cyan"
                />
              </div>

              <div>
                <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                  SOURCE DIRECTORY PATH (FOR SAST / SECRETS)
                </label>
                <input
                  type="text"
                  value={formData.source_path}
                  onChange={(e) => setFormData({ ...formData, source_path: e.target.value })}
                  placeholder="./worldmonitor or C:\projects\app"
                  className="cyber-input w-full px-3 py-2 text-cyber-accent"
                />
              </div>

              <div>
                <label className="block font-bold text-cyber-muted uppercase tracking-wider mb-1">
                  TACTICAL DESCRIPTION &amp; SCOPE NOTES
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Notes on scope, authorization contact, staging ports..."
                  className="cyber-input w-full px-3 py-2 text-white"
                />
              </div>

              <div className="p-3 bg-cyber-void border border-cyber-accent/30 text-[11px] text-cyber-foreground/80">
                <div className="flex items-center gap-2 text-cyber-accent font-bold mb-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span className="uppercase tracking-wider">AUTHORIZATION CONFIRMATION</span>
                </div>
                You verify you hold explicit authorization to conduct vulnerability and exploitation assessments against this target.
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-cyber-border">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-cyber-muted hover:text-white uppercase tracking-wider"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="cyber-btn-primary px-5 py-2 uppercase tracking-widest disabled:opacity-50"
                >
                  {saving ? 'COMMITTING...' : editingTarget ? 'UPDATE TARGET' : 'COMMIT TARGET'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deleteConfirmTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-cyber-void/85 backdrop-blur-md">
          <div className="cyber-card max-w-md w-full p-6 border-cyber-destructive shadow-[0_0_30px_rgba(255,51,102,0.3)] bg-cyber-card">
            <div className="flex items-center gap-3 text-cyber-destructive mb-3">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-base font-bold text-white uppercase tracking-wider font-orbitron">
                TERMINATE TARGET RECORD?
              </h3>
            </div>
            <p className="text-xs text-cyber-foreground/80 leading-relaxed font-mono">
              CONFIRM DELETION OF TARGET: <span className="font-bold text-white uppercase">{deleteConfirmTarget.name}</span>. ALL LINKED AUDIT METRICS AND LOG RECORDS WILL BE PURGED.
            </p>
            <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-cyber-border">
              <button
                onClick={() => setDeleteConfirmTarget(null)}
                className="px-4 py-2 text-cyber-muted hover:text-white text-xs uppercase tracking-wider"
              >
                ABORT
              </button>
              <button
                onClick={handleDeleteTarget}
                className="px-4 py-2 bg-cyber-destructive hover:bg-cyber-destructive/80 text-white font-bold text-xs uppercase tracking-widest shadow-[0_0_12px_rgba(255,51,102,0.4)]"
              >
                CONFIRM PURGE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
