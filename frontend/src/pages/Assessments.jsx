import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, FolderSearch, Eye, Trash2, Shield, Play, AlertTriangle } from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const STATUS_COLORS = {
  draft: 'bg-dark-700 text-dark-300 border-dark-600',
  configured: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  discovering: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  scanning: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  running: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  verifying: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  cancelled: 'bg-dark-700 text-dark-400 border-dark-600'
}

export default function Assessments() {
  const navigate = useNavigate()
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    fetchAssessments()
  }, [statusFilter])

  const fetchAssessments = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter) params.append('status', statusFilter)
      params.append('limit', '50')

      const response = await api.get(`/assessments?${params}`)
      setAssessments(response.data.items || [])
    } catch (error) {
      console.error('Failed to fetch assessments:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAssessment = async () => {
    if (!deleteConfirm) return
    try {
      await api.delete(`/assessments/${deleteConfirm.id}`)
      setDeleteConfirm(null)
      fetchAssessments()
    } catch (err) {
      console.error('Failed to delete assessment:', err)
    }
  }

  const filteredAssessments = assessments.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.target_url?.toLowerCase().includes(search.toLowerCase()) ||
    a.target_name?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Assessments</h1>
          <p className="text-dark-400 mt-1">Configured security assessment projects and verification sessions</p>
        </div>
        <Link
          to="/assessments/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-600/20 text-sm"
        >
          <Plus className="w-5 h-5" />
          New Assessment
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search assessments by name or target..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:border-blue-500 text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="configured">Configured</option>
          <option value="pending">Pending</option>
          <option value="discovering">Discovering</option>
          <option value="scanning">Scanning</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Assessments Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      ) : filteredAssessments.length > 0 ? (
        <div className="bg-dark-900 rounded-xl border border-dark-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-dark-800/80 border-b border-dark-800 text-[11px] font-semibold text-dark-400 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Assessment Name</th>
                  <th className="px-6 py-3.5">Target</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Selected Modules</th>
                  <th className="px-6 py-3.5">Created</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800 text-xs">
                {filteredAssessments.map((assessment) => (
                  <tr
                    key={assessment.id}
                    onClick={() => navigate(`/assessments/${assessment.id}`)}
                    className="hover:bg-dark-800/50 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4">
                      <div className="text-white font-medium text-sm">{assessment.name}</div>
                      <div className="text-[11px] text-dark-400 capitalize mt-0.5">
                        Env: <span className="text-dark-300 font-mono">{assessment.environment}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-dark-300">
                      {assessment.target_name && (
                        <div className="font-semibold text-white">{assessment.target_name}</div>
                      )}
                      <div className="font-mono text-[11px] text-dark-400 truncate max-w-xs">
                        {assessment.target_url || assessment.source_path || 'No target path'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2.5 py-1 text-[11px] font-mono rounded-full border capitalize font-medium',
                          STATUS_COLORS[assessment.status] || 'bg-dark-700 text-dark-300'
                        )}
                      >
                        {assessment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {assessment.modules ? (
                          Object.entries(assessment.modules)
                            .filter(([_, active]) => active)
                            .map(([mod]) => (
                              <span
                                key={mod}
                                className="px-1.5 py-0.5 bg-dark-800 text-dark-300 border border-dark-700 rounded text-[10px] uppercase font-mono"
                              >
                                {mod.replace('_', ' ')}
                              </span>
                            ))
                        ) : (
                          <span className="text-dark-500 font-mono text-[11px]">Legacy flags</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-dark-400 font-mono text-[11px]">
                      {new Date(assessment.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/assessments/${assessment.id}`}
                          className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => setDeleteConfirm(assessment)}
                          className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-800 rounded-lg transition-colors"
                          title="Delete Assessment"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <FolderSearch className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">No assessments found</h3>
          <p className="text-sm text-dark-400 mt-1 max-w-sm">
            Launch your first multi-engine security assessment session using the wizard.
          </p>
          <Link
            to="/assessments/new"
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Create Assessment
          </Link>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-red-400 mb-3">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-lg font-bold text-white">Delete Assessment?</h3>
            </div>
            <p className="text-sm text-dark-300">
              Are you sure you want to delete <span className="font-semibold text-white">{deleteConfirm.name}</span>?
              All associated findings and configuration records will be permanently removed.
            </p>
            <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-dark-800">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-dark-400 hover:text-white text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAssessment}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
              >
                Delete Assessment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
