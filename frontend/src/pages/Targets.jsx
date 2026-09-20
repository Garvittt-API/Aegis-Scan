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
  X
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const TARGET_TYPE_ICONS = {
  web: Globe,
  source_code: Code,
  repository: FolderGit2,
  local_application: Laptop
}

const ENV_COLORS = {
  local: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  staging: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  production: 'bg-red-500/10 text-red-400 border-red-500/20',
  authorized_remote: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Target Management</h1>
          <p className="text-dark-400 mt-1">Register and manage authorized assessment scopes and applications</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={openAddModal}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-600/20"
          >
            <Plus className="w-5 h-5" />
            Add Target
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-4 bg-dark-900/90 border border-blue-500/20 rounded-xl flex items-start gap-3">
        <Shield className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-dark-300 leading-relaxed">
          <span className="font-semibold text-white">Controlled Assessment Policy:</span> AegisScan evaluates targets within your verified scope. Ensure local/staging boundaries are respected.
        </div>
      </div>

      {/* Filters & Search */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search targets by name, URL, or path..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Types</option>
          <option value="web">Web Application</option>
          <option value="source_code">Source Code</option>
          <option value="repository">Git Repository</option>
          <option value="local_application">Local Application</option>
        </select>
        <select
          value={envFilter}
          onChange={(e) => setEnvFilter(e.target.value)}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Environments</option>
          <option value="local">Local</option>
          <option value="staging">Staging</option>
          <option value="production">Production</option>
          <option value="authorized_remote">Authorized Remote</option>
        </select>
      </div>

      {/* Target Cards / List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      ) : filteredTargets.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredTargets.map((target) => {
            const Icon = TARGET_TYPE_ICONS[target.target_type] || Target
            return (
              <div
                key={target.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-5 hover:border-dark-700 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 bg-dark-800 border border-dark-700 rounded-lg text-blue-400">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{target.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={clsx('px-2 py-0.5 text-xs rounded-full border uppercase font-mono', ENV_COLORS[target.environment])}>
                            {target.environment}
                          </span>
                          <span className="text-xs text-dark-400 capitalize">
                            {target.target_type.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditModal(target)}
                        className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
                        title="Edit Target"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeleteConfirmTarget(target)}
                        className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-800 rounded-lg transition-colors"
                        title="Delete Target"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Target Details */}
                  {target.description && (
                    <p className="text-sm text-dark-300 mt-3 line-clamp-2">{target.description}</p>
                  )}

                  <div className="mt-4 space-y-2 text-xs font-mono">
                    {target.base_url && (
                      <div className="flex items-center gap-2 text-dark-300 bg-dark-800/60 px-3 py-1.5 rounded-lg border border-dark-800 truncate">
                        <span className="text-dark-500 font-sans">URL:</span>
                        <span className="truncate text-blue-400">{target.base_url}</span>
                      </div>
                    )}
                    {target.source_path && (
                      <div className="flex items-center gap-2 text-dark-300 bg-dark-800/60 px-3 py-1.5 rounded-lg border border-dark-800 truncate">
                        <span className="text-dark-500 font-sans">Path:</span>
                        <span className="truncate text-emerald-400">{target.source_path}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer */}
                <div className="mt-5 pt-4 border-t border-dark-800 flex items-center justify-between text-xs text-dark-400">
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{target.assessments_count} assessments</span>
                  </div>
                  <button
                    onClick={() => navigate(`/assessments/new?target_id=${target.id}`)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/20 rounded-lg transition-colors font-sans font-medium text-xs"
                  >
                    <Play className="w-3.5 h-3.5" />
                    New Assessment
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <Target className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">No targets found</h3>
          <p className="text-sm text-dark-400 mt-1 max-w-sm">
            Add a target to configure web endpoints, source repositories, or local applications for security assessments.
          </p>
          <button
            onClick={openAddModal}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Add Your First Target
          </button>
        </div>
      )}

      {/* ADD / EDIT TARGET MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-dark-800">
              <h2 className="text-xl font-bold text-white">
                {editingTarget ? 'Edit Target' : 'Register New Target'}
              </h2>
              <button
                onClick={() => setModalOpen(false)}
                className="text-dark-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleSaveTarget} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1">
                  Target Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. World Monitor Local"
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark-300 mb-1">
                    Target Type
                  </label>
                  <select
                    value={formData.target_type}
                    onChange={(e) => setFormData({ ...formData, target_type: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="web">Web Application</option>
                    <option value="source_code">Source Code</option>
                    <option value="repository">Git Repository</option>
                    <option value="local_application">Local Application</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-300 mb-1">
                    Environment
                  </label>
                  <select
                    value={formData.environment}
                    onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="local">Local</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                    <option value="authorized_remote">Authorized Remote</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1">
                  Base URL (for DAST / Web Scans)
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  placeholder="http://localhost:5173"
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1">
                  Source Code Path (for SAST)
                </label>
                <input
                  type="text"
                  value={formData.source_path}
                  onChange={(e) => setFormData({ ...formData, source_path: e.target.value })}
                  placeholder="./worldmonitor or C:\projects\app"
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Notes on architecture, testing scope, or maintainer..."
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Authorization status note */}
              <div className="p-3 bg-dark-800/80 border border-dark-700 rounded-lg text-xs text-dark-300">
                <div className="flex items-center gap-2 text-green-400 font-medium mb-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Authorization Requirement</span>
                </div>
                By registering this target, you attest that you possess authorized consent to conduct security assessments on it.
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-dark-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-dark-400 hover:text-white text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : editingTarget ? 'Update Target' : 'Register Target'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deleteConfirmTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-red-400 mb-3">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-lg font-bold text-white">Delete Target?</h3>
            </div>
            <p className="text-sm text-dark-300">
              Are you sure you want to delete <span className="font-semibold text-white">{deleteConfirmTarget.name}</span>?
              This will also remove any associated assessment records.
            </p>
            <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-dark-800">
              <button
                onClick={() => setDeleteConfirmTarget(null)}
                className="px-4 py-2 text-dark-400 hover:text-white text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteTarget}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
              >
                Delete Target
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
