import { useEffect, useState } from 'react'
import { Search, Filter, AlertTriangle, ExternalLink } from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const SEVERITY_COLORS = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  informational: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

const VERIFICATION_COLORS = {
  verified: 'bg-green-500/20 text-green-400',
  likely: 'bg-blue-500/20 text-blue-400',
  unverified: 'bg-yellow-500/20 text-yellow-400',
  false_positive: 'bg-gray-500/20 text-gray-400'
}

export default function Findings() {
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    severity: '',
    verification_status: '',
    scanner: ''
  })

  useEffect(() => {
    fetchFindings()
  }, [filters])

  const fetchFindings = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.severity) params.append('severity', filters.severity)
      if (filters.verification_status) params.append('verification_status', filters.verification_status)
      if (filters.scanner) params.append('scanner', filters.scanner)
      params.append('limit', '100')

      const response = await api.get(`/findings?${params}`)
      setFindings(response.data.items || [])
    } catch (error) {
      console.error('Failed to fetch findings:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredFindings = findings.filter(f =>
    f.title.toLowerCase().includes(search.toLowerCase()) ||
    f.endpoint?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Findings</h1>
        <p className="text-dark-400 mt-1">Security findings from all assessments</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={filters.severity}
          onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={filters.verification_status}
          onChange={(e) => setFilters(prev => ({ ...prev, verification_status: e.target.value }))}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Status</option>
          <option value="verified">Verified</option>
          <option value="unverified">Unverified</option>
          <option value="false_positive">False Positive</option>
        </select>
      </div>

      {/* Findings List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      ) : filteredFindings.length > 0 ? (
        <div className="space-y-3">
          {filteredFindings.map((finding) => (
            <div
              key={finding.id}
              className="bg-dark-900 rounded-xl border border-dark-800 p-4 hover:border-dark-700 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={clsx(
                        'px-2 py-1 text-xs rounded-full border',
                        SEVERITY_COLORS[finding.severity]
                      )}
                    >
                      {finding.severity}
                    </span>
                    <span
                      className={clsx(
                        'px-2 py-1 text-xs rounded-full',
                        VERIFICATION_COLORS[finding.verification_status]
                      )}
                    >
                      {finding.verification_status}
                    </span>
                    <span className="px-2 py-1 text-xs bg-dark-800 text-dark-300 rounded-full">
                      {finding.scanner}
                    </span>
                  </div>
                  <h3 className="text-white font-medium">{finding.title}</h3>
                  {finding.endpoint && (
                    <p className="text-sm text-dark-400 mt-1 font-mono">{finding.endpoint}</p>
                  )}
                  {finding.description && (
                    <p className="text-sm text-dark-300 mt-2">{finding.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors">
                    <ExternalLink className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800">
          <AlertTriangle className="w-12 h-12 text-dark-400 mb-2" />
          <p className="text-dark-400">No findings found</p>
          <p className="text-sm text-dark-500">Run an assessment to discover security findings</p>
        </div>
      )}
    </div>
  )
}
