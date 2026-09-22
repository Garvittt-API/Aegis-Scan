import { useEffect, useState } from 'react'
import { Search, AlertTriangle, ExternalLink, X } from 'lucide-react'
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
  const [selectedFinding, setSelectedFinding] = useState(null)
  const [remediation, setRemediation] = useState(null)
  const [remediationLoading, setRemediationLoading] = useState(false)

  const sourceLabels = (finding) => {
    try {
      return JSON.parse(finding.source_scanners || '[]').join(', ') || finding.scanner
    } catch {
      return finding.source_scanners || finding.scanner
    }
  }

  const verifySelected = async () => {
    if (!selectedFinding) return
    try {
      const response = await api.post(`/findings/${selectedFinding.id}/reverify`)
      setSelectedFinding(response.data)
      setFindings(current => current.map(item => item.id === response.data.id ? response.data : item))
    } catch (error) {
      console.error('Verification failed:', error)
    }
  }

  const openFinding = async (finding) => {
    setSelectedFinding(finding)
    setRemediation(null)
    setRemediationLoading(true)
    try {
      const response = await api.get(`/findings/${finding.id}/remediation`)
      setRemediation(response.data)
    } catch (error) {
      console.error('Failed to load remediation:', error)
    } finally {
      setRemediationLoading(false)
    }
  }

  const updateRemediation = async (status) => {
    if (!selectedFinding) return
    try {
      const response = await api.patch(`/findings/${selectedFinding.id}/remediation`, { status })
      setRemediation(response.data)
    } catch (error) {
      console.error('Failed to update remediation:', error)
    }
  }

  const validateRemediation = async () => {
    if (!selectedFinding) return
    try {
      const response = await api.post(`/findings/${selectedFinding.id}/remediation/validate`)
      setRemediation(response.data)
    } catch (error) {
      console.error('Failed to validate remediation:', error)
    }
  }

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

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {['critical', 'high', 'medium', 'low', 'informational'].map((severity) => (
          <div key={severity} className="bg-dark-900 border border-dark-800 rounded-lg p-3">
            <p className="text-xs uppercase text-dark-400">{severity}</p>
            <p className="text-2xl font-semibold text-white">{findings.filter(f => f.severity === severity).length}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {['verified', 'likely', 'unverified', 'false_positive'].map((status) => (
          <div key={status} className="bg-dark-900 border border-dark-800 rounded-lg p-3">
            <p className="text-xs uppercase text-dark-400">{status.replace('_', ' ')}</p>
            <p className="text-2xl font-semibold text-white">{findings.filter(f => f.verification_status === status).length}</p>
          </div>
        ))}
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
              onClick={() => openFinding(finding)}
              role="button"
              tabIndex={0}
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
                      {sourceLabels(finding)}
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
          <p className="text-dark-400">No findings generated for this assessment.</p>
        </div>
      )}

      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={() => setSelectedFinding(null)}>
          <div className="bg-dark-900 border border-dark-700 rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">{selectedFinding.title}</h2>
                <p className="text-dark-400 mt-1">{selectedFinding.description || 'No description provided.'}</p>
              </div>
              <button className="p-2 text-dark-400 hover:text-white" onClick={() => setSelectedFinding(null)} aria-label="Close finding detail"><X /></button>
            </div>
            <dl className="grid grid-cols-2 gap-4 mt-6 text-sm">
              <div><dt className="text-dark-400">Severity</dt><dd className="text-white">{selectedFinding.severity}</dd></div>
              <div><dt className="text-dark-400">Risk / Priority</dt><dd className="text-white">{selectedFinding.risk_score ?? 'Not calculated'} / {selectedFinding.priority || 'Not calculated'}</dd></div>
              <div><dt className="text-dark-400">Confidence</dt><dd className="text-white">{Math.round((selectedFinding.confidence || 0) * 100)}%</dd></div>
              <div><dt className="text-dark-400">Exposure</dt><dd className="text-white">{selectedFinding.exposure || 'unknown'}</dd></div>
              <div><dt className="text-dark-400">Scanner(s)</dt><dd className="text-white">{sourceLabels(selectedFinding)}</dd></div>
              <div><dt className="text-dark-400">Verification</dt><dd className="text-white">{selectedFinding.verification_status}</dd></div>
              <div className="col-span-2"><dt className="text-dark-400">Location</dt><dd className="text-white font-mono">{selectedFinding.endpoint || selectedFinding.source_file || 'Not provided'}</dd></div>
              <div className="col-span-2"><dt className="text-dark-400">Evidence</dt><dd className="text-white whitespace-pre-wrap">{selectedFinding.evidence || 'No evidence provided.'}</dd></div>
              <div className="col-span-2"><dt className="text-dark-400">Raw evidence</dt><dd className="text-white break-all">{selectedFinding.raw_output || 'Unavailable'}</dd></div>
              <div className="col-span-2"><dt className="text-dark-400">Risk explanation</dt><dd className="text-white">{selectedFinding.risk_explanation || 'Risk has not been calculated.'}</dd></div>
            </dl>
            <div className="flex gap-3 mt-6">
              <button className="px-3 py-2 bg-blue-600 text-white rounded-lg" onClick={verifySelected}>Verify safely</button>
              <span className="text-sm text-dark-400 self-center">Verification never performs destructive actions.</span>
            </div>
            <section className="mt-8 border-t border-dark-800 pt-6">
              <h3 className="text-lg font-semibold text-white">Remediation</h3>
              {remediationLoading ? (
                <p className="text-dark-400 mt-3">Loading remediation guidance...</p>
              ) : remediation ? (
                <div className="space-y-4 mt-4 text-sm">
                  <div><p className="text-dark-400">What is wrong</p><p className="text-white">{remediation.summary}</p></div>
                  <div><p className="text-dark-400">Why it matters</p><p className="text-white">{remediation.explanation || 'No additional explanation available.'}</p></div>
                  <div><p className="text-dark-400">Recommended fix</p><p className="text-white whitespace-pre-wrap">{remediation.recommended_action}</p></div>
                  <div><p className="text-dark-400">Technical steps</p><p className="text-white whitespace-pre-wrap">{remediation.technical_steps || 'No technical steps available.'}</p></div>
                  {remediation.configuration_guidance && <div><p className="text-dark-400">Configuration guidance</p><p className="text-white">{remediation.configuration_guidance}</p></div>}
                  {remediation.dependency_guidance && <div><p className="text-dark-400">Dependency guidance</p><p className="text-white">{remediation.dependency_guidance}</p></div>}
                  <div><p className="text-dark-400">Validation steps</p><p className="text-white">{remediation.verification_steps}</p></div>
                  <div className="grid grid-cols-3 gap-3"><div><p className="text-dark-400">Priority</p><p className="text-white">{remediation.priority || 'Unknown'}</p></div><div><p className="text-dark-400">Effort</p><p className="text-white">{remediation.estimated_effort}</p></div><div><p className="text-dark-400">Status</p><p className="text-white">{remediation.status}</p></div></div>
                  {remediation.validation_evidence && <div><p className="text-dark-400">Validation evidence</p><p className="text-white whitespace-pre-wrap">{remediation.validation_evidence}</p></div>}
                  <div className="flex flex-wrap gap-2">
                    <button className="px-3 py-2 bg-dark-800 text-white rounded-lg" onClick={() => updateRemediation('in_progress')}>Mark in progress</button>
                    <button className="px-3 py-2 bg-dark-800 text-white rounded-lg" onClick={() => updateRemediation('ready_for_validation')}>Ready for validation</button>
                    <button className="px-3 py-2 bg-blue-600 text-white rounded-lg" onClick={validateRemediation}>Validate with new evidence</button>
                  </div>
                </div>
              ) : <p className="text-dark-400 mt-3">No remediation guidance is available.</p>}
            </section>
          </div>
        </div>
      )}
    </div>
  )
}
