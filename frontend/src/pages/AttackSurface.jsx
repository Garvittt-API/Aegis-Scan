import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Globe,
  FileCode,
  FileText,
  Image,
  Link2,
  FormInput,
  Settings,
  Code,
  ExternalLink,
  RefreshCw,
  Filter,
  Search,
  AlertTriangle,
  CheckCircle2,
  Play,
  X,
  Plus,
  ArrowLeft,
  Sliders,
  Layers,
  StopCircle,
  Database,
  Cpu,
  Boxes
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const ASSET_ICONS = {
  url: Globe,
  api: Code,
  endpoint: Link2,
  parameter: Settings,
  javascript: FileCode,
  asset: Image,
  service: Cpu,
  technology: Boxes,
  form: FormInput
}

const RISK_COLORS = {
  high: 'bg-red-500/10 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/10 text-blue-400 border-blue-500/30'
}

export default function AttackSurface() {
  const { id } = useParams()
  const [assessments, setAssessments] = useState([])
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(id || '')
  const [assets, setAssets] = useState([])
  const [summary, setSummary] = useState({})
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    type: '',
    method: '',
    source: ''
  })

  // Discovery execution state
  const [discovering, setDiscovering] = useState(false)
  const [activeRun, setActiveRun] = useState(null)
  const [discoveryConfigModal, setDiscoveryConfigModal] = useState(false)
  const [discoveryParams, setDiscoveryParams] = useState({
    crawl_depth: 2,
    max_pages: 50,
    rate_limit: 'low'
  })

  // Add Asset Modal state
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [newAsset, setNewAsset] = useState({
    type: 'endpoint',
    name: '',
    url: '',
    method: 'GET',
    path: '',
    parameter: '',
    risk_relevance: 'medium'
  })

  useEffect(() => {
    fetchAssessments()
  }, [])

  useEffect(() => {
    if (selectedAssessmentId) {
      fetchAttackSurface(selectedAssessmentId)
    } else {
      setAssets([])
      setSummary({})
      setLoading(false)
    }
  }, [selectedAssessmentId, filters])

  const fetchAssessments = async () => {
    try {
      const res = await api.get('/assessments?limit=100')
      const items = res.data.items || []
      setAssessments(items)
      if (!selectedAssessmentId && items.length > 0) {
        setSelectedAssessmentId(items[0].id)
      }
    } catch (err) {
      console.error('Failed to load assessments:', err)
    }
  }

  const fetchAttackSurface = async (assId) => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.type) params.append('type', filters.type)
      if (filters.method) params.append('method', filters.method)
      if (filters.source) params.append('source', filters.source)
      params.append('limit', '500')

      const res = await api.get(`/assessments/${assId}/attack-surface?${params}`)
      setAssets(res.data.items || [])
      setSummary(res.data.summary || {})
    } catch (err) {
      console.error('Failed to fetch attack surface:', err)
    } finally {
      setLoading(false)
    }
  }

  const startDiscovery = async () => {
    if (!selectedAssessmentId) return
    setDiscoveryConfigModal(false)
    setDiscovering(true)

    try {
      const res = await api.post(`/assessments/${selectedAssessmentId}/discovery`, discoveryParams)
      const runId = res.data.id
      setActiveRun(res.data)

      // Poll discovery status
      const interval = setInterval(async () => {
        try {
          const statusRes = await api.get(`/assessments/${selectedAssessmentId}/discovery/${runId}`)
          setActiveRun(statusRes.data)

          if (['completed', 'failed', 'cancelled'].includes(statusRes.data.status)) {
            clearInterval(interval)
            setDiscovering(false)
            fetchAttackSurface(selectedAssessmentId)
          }
        } catch (pollErr) {
          clearInterval(interval)
          setDiscovering(false)
        }
      }, 1500)
    } catch (err) {
      console.error('Failed to launch discovery:', err)
      setDiscovering(false)
    }
  }

  const cancelDiscovery = async () => {
    if (!activeRun || !selectedAssessmentId) return
    try {
      await api.post(`/assessments/${selectedAssessmentId}/discovery/${activeRun.id}/cancel`)
      setDiscovering(false)
      fetchAttackSurface(selectedAssessmentId)
    } catch (err) {
      console.error('Failed to cancel discovery:', err)
    }
  }

  const handleCreateAsset = async (e) => {
    e.preventDefault()
    try {
      await api.post(`/assessments/${selectedAssessmentId}/attack-surface`, newAsset)
      setAddModalOpen(false)
      setNewAsset({
        type: 'endpoint',
        name: '',
        url: '',
        method: 'GET',
        path: '',
        parameter: '',
        risk_relevance: 'medium'
      })
      fetchAttackSurface(selectedAssessmentId)
    } catch (err) {
      console.error('Failed to create asset:', err)
    }
  }

  const filteredAssets = assets.filter(a =>
    a.name?.toLowerCase().includes(search.toLowerCase()) ||
    a.url?.toLowerCase().includes(search.toLowerCase()) ||
    a.path?.toLowerCase().includes(search.toLowerCase()) ||
    a.parameter?.toLowerCase().includes(search.toLowerCase())
  )

  const currentAssessment = assessments.find(a => a.id === parseInt(selectedAssessmentId, 10))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            {id && (
              <Link
                to={`/assessments/${id}`}
                className="p-1.5 bg-dark-900 hover:bg-dark-800 border border-dark-800 rounded-lg text-dark-400 hover:text-white transition-colors mr-1"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
            )}
            <h1 className="text-3xl font-bold text-white tracking-tight">Attack Surface Inventory</h1>
          </div>
          <p className="text-dark-400 mt-1">Discovered endpoints, APIs, forms, parameters, and technologies</p>
        </div>

        {/* Assessment Switcher & Action Controls */}
        <div className="flex items-center gap-3">
          <select
            value={selectedAssessmentId}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
            className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 font-medium"
          >
            <option value="">-- Select Assessment --</option>
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} ({a.environment})
              </option>
            ))}
          </select>

          {selectedAssessmentId && (
            <>
              <button
                onClick={() => setAddModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 bg-dark-800 hover:bg-dark-700 text-white rounded-lg text-xs font-semibold transition-colors border border-dark-700"
              >
                <Plus className="w-4 h-4" />
                Add Asset
              </button>

              <button
                onClick={() => (discovering ? cancelDiscovery() : setDiscoveryConfigModal(true))}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-lg',
                  discovering
                    ? 'bg-red-600 hover:bg-red-700 text-white shadow-red-600/20'
                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20'
                )}
              >
                {discovering ? (
                  <>
                    <StopCircle className="w-4 h-4 animate-pulse" />
                    Cancel Discovery
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Discovery
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Discovery Active Progress Banner */}
      {discovering && activeRun && (
        <div className="p-4 bg-dark-900 border border-cyan-500/30 rounded-xl space-y-3 shadow-xl">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Safe Attack Surface Discovery in Progress ({activeRun.progress}%)</span>
            </div>
            <span className="text-dark-400 font-mono">
              Assets Found: <strong className="text-white">{activeRun.discovered_count}</strong>
            </span>
          </div>
          <div className="w-full bg-dark-800 rounded-full h-2 overflow-hidden border border-dark-700">
            <div
              className="bg-cyan-500 h-2 transition-all duration-300 rounded-full"
              style={{ width: `${Math.max(5, activeRun.progress)}%` }}
            />
          </div>
        </div>
      )}

      {/* Summary Metrics Grid */}
      {summary.total_assets !== undefined && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <SummaryCard label="Total Assets" value={summary.total_assets || 0} icon={Globe} color="text-blue-400" />
          <SummaryCard label="APIs" value={summary.apis_count || 0} icon={Code} color="text-cyan-400" />
          <SummaryCard label="Endpoints" value={summary.endpoints_count || 0} icon={Link2} color="text-emerald-400" />
          <SummaryCard label="Parameters" value={summary.parameters_count || 0} icon={Settings} color="text-purple-400" />
          <SummaryCard label="Forms" value={summary.forms_count || 0} icon={FormInput} color="text-yellow-400" />
          <SummaryCard label="JavaScript" value={summary.javascript_count || 0} icon={FileCode} color="text-indigo-400" />
          <SummaryCard label="Technologies" value={summary.technologies_count || 0} icon={Boxes} color="text-orange-400" />
          <SummaryCard label="High Risk" value={summary.by_risk?.high || 0} icon={AlertTriangle} color="text-red-400" />
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search discovered items by name, path, URL, or parameter..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white text-xs placeholder-dark-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        <select
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
          className="px-3 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
        >
          <option value="">All Types</option>
          <option value="url">URLs</option>
          <option value="api">APIs</option>
          <option value="endpoint">Endpoints</option>
          <option value="parameter">Parameters</option>
          <option value="form">Forms</option>
          <option value="javascript">JavaScript</option>
          <option value="technology">Technologies</option>
        </select>

        <select
          value={filters.method}
          onChange={(e) => setFilters({ ...filters, method: e.target.value })}
          className="px-3 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
        >
          <option value="">All HTTP Methods</option>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="DELETE">DELETE</option>
        </select>
      </div>

      {/* Inventory Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      ) : !selectedAssessmentId ? (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <Globe className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">Select an Assessment</h3>
          <p className="text-sm text-dark-400 mt-1">Choose an assessment to explore its attack surface inventory.</p>
        </div>
      ) : filteredAssets.length > 0 ? (
        <div className="bg-dark-900 rounded-xl border border-dark-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-dark-800/80 border-b border-dark-800 text-[11px] font-semibold text-dark-400 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">Type & Name</th>
                  <th className="px-5 py-3.5">Method</th>
                  <th className="px-5 py-3.5">Path / Parameter</th>
                  <th className="px-5 py-3.5">Discovery Sources</th>
                  <th className="px-5 py-3.5">Risk Level</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800 text-xs font-sans">
                {filteredAssets.map((asset) => {
                  const Icon = ASSET_ICONS[asset.type] || Globe
                  return (
                    <tr key={asset.id} className="hover:bg-dark-800/40 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="p-1.5 bg-dark-800 rounded-md text-blue-400 border border-dark-700">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="text-white font-medium">{asset.name || 'Unnamed Asset'}</div>
                            <span className="text-[10px] font-mono text-dark-400 uppercase">{asset.type}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        {asset.method ? (
                          <span className="px-2 py-0.5 bg-dark-800 text-dark-300 font-mono rounded text-[10px] font-bold border border-dark-700">
                            {asset.method}
                          </span>
                        ) : (
                          <span className="text-dark-500">-</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 max-w-sm">
                        <div className="font-mono text-[11px] text-dark-300 truncate">
                          {asset.path || asset.url || '-'}
                        </div>
                        {asset.parameter && (
                          <div className="text-[10px] text-purple-400 font-mono">
                            Param: {asset.parameter}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-wrap gap-1">
                          {(asset.discovered_by?.length ? asset.discovered_by : [asset.source || 'crawler']).map((src) => (
                            <span
                              key={src}
                              className="px-1.5 py-0.5 bg-dark-800 text-dark-300 border border-dark-700 rounded text-[10px] font-mono"
                            >
                              {src}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={clsx('px-2 py-0.5 text-[10px] font-mono rounded-full border uppercase font-medium', RISK_COLORS[asset.risk_relevance] || 'bg-dark-800 text-dark-300')}>
                          {asset.risk_relevance}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        {asset.url && (
                          <a
                            href={asset.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 text-dark-400 hover:text-white inline-flex"
                            title="Open URL"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <Globe className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">No attack-surface items discovered yet</h3>
          <p className="text-sm text-dark-400 mt-1 max-w-sm">
            Launch safe same-origin spidering to discover endpoints, forms, APIs, and technologies.
          </p>
          <button
            onClick={() => setDiscoveryConfigModal(true)}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Run Discovery Now
          </button>
        </div>
      )}

      {/* DISCOVERY CONFIGURATION MODAL */}
      {discoveryConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-dark-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Play className="w-4 h-4 text-blue-400" />
                Launch Attack Surface Discovery
              </h3>
              <button onClick={() => setDiscoveryConfigModal(false)} className="text-dark-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block font-medium text-dark-300 mb-1">Target Base URL</label>
                <input
                  type="text"
                  disabled
                  value={currentAssessment?.target_url || 'No URL configured'}
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-dark-300 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-dark-300 mb-1">Max Crawl Depth</label>
                  <select
                    value={discoveryParams.crawl_depth}
                    onChange={(e) => setDiscoveryParams({ ...discoveryParams, crawl_depth: parseInt(e.target.value, 10) })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                  >
                    <option value={1}>1 Level</option>
                    <option value={2}>2 Levels (Standard)</option>
                    <option value={3}>3 Levels (Deep)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-dark-300 mb-1">Max Pages Limit</label>
                  <select
                    value={discoveryParams.max_pages}
                    onChange={(e) => setDiscoveryParams({ ...discoveryParams, max_pages: parseInt(e.target.value, 10) })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                  >
                    <option value={20}>20 Pages</option>
                    <option value={50}>50 Pages</option>
                    <option value={100}>100 Pages</option>
                  </select>
                </div>
              </div>

              <div className="p-3 bg-dark-800/60 rounded-lg border border-dark-700 text-dark-400 leading-relaxed">
                Safe Discovery respects the target domain boundaries, extracting links, parameters, and technologies with rate-limiting controls.
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-dark-800">
              <button
                onClick={() => setDiscoveryConfigModal(false)}
                className="px-3 py-1.5 text-dark-400 hover:text-white text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={startDiscovery}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold"
              >
                Start Spidering
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD ASSET MANUAL MODAL */}
      {addModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-dark-800">
              <h3 className="text-lg font-bold text-white">Add Attack Surface Item</h3>
              <button onClick={() => setAddModalOpen(false)} className="text-dark-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateAsset} className="mt-4 space-y-3 text-xs">
              <div>
                <label className="block font-medium text-dark-300 mb-1">Asset Type *</label>
                <select
                  value={newAsset.type}
                  onChange={(e) => setNewAsset({ ...newAsset, type: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                >
                  <option value="endpoint">Endpoint</option>
                  <option value="api">API</option>
                  <option value="url">URL</option>
                  <option value="parameter">Parameter</option>
                  <option value="form">Form</option>
                  <option value="javascript">JavaScript</option>
                  <option value="technology">Technology</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-dark-300 mb-1">Name / Label</label>
                <input
                  type="text"
                  value={newAsset.name}
                  onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })}
                  placeholder="e.g. /api/v1/auth/login"
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-dark-300 mb-1">HTTP Method</label>
                  <select
                    value={newAsset.method}
                    onChange={(e) => setNewAsset({ ...newAsset, method: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                    <option value="PATCH">PATCH</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-dark-300 mb-1">Risk Relevance</label>
                  <select
                    value={newAsset.risk_relevance}
                    onChange={(e) => setNewAsset({ ...newAsset, risk_relevance: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-medium text-dark-300 mb-1">Full URL</label>
                <input
                  type="url"
                  value={newAsset.url}
                  onChange={(e) => setNewAsset({ ...newAsset, url: e.target.value })}
                  placeholder="http://localhost:5173/api/v1/users"
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white font-mono"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-dark-800">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="px-3 py-1.5 text-dark-400 hover:text-white text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold"
                >
                  Add Asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl p-3 flex flex-col justify-between">
      <div className="flex items-center justify-between text-dark-400 mb-1">
        <span className="text-[10px] uppercase font-bold tracking-wider">{label}</span>
        <Icon className={clsx('w-3.5 h-3.5', color)} />
      </div>
      <p className="text-xl font-bold text-white tracking-tight">{value}</p>
    </div>
  )
}
