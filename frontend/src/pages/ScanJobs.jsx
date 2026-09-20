import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  Sliders,
  Play,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  FolderSearch,
  Layers,
  ArrowLeft,
  Shield,
  Info,
  ChevronRight,
  Terminal,
  Zap,
  Code,
  FileCode,
  Box,
  Check,
  X,
  FileText,
  Copy,
  ExternalLink
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const SCANNER_ICONS = {
  zap: Zap,
  nuclei: Shield,
  semgrep: Code,
  sca: Box,
  custom: Terminal
}

const SCANNER_LABELS = {
  zap: 'OWASP ZAP (DAST)',
  nuclei: 'Nuclei (Templates)',
  semgrep: 'Semgrep (SAST)',
  sca: 'Dependency Check (SCA)',
  custom: 'AegisScan Custom Rules'
}

const JOB_STATUS_COLORS = {
  pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  queued: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  running: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 animate-pulse',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  unavailable: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  timeout: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  cancelled: 'bg-dark-700 text-dark-400 border-dark-600',
  not_implemented: 'bg-purple-500/10 text-purple-400 border-purple-500/30'
}

export default function ScanJobs() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [assessments, setAssessments] = useState([])
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(id || '')
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [planning, setPlanning] = useState(false)
  const [executingAll, setExecutingAll] = useState(false)
  const [executingJobId, setExecutingJobId] = useState(null)
  const [toolsStatus, setToolsStatus] = useState([])
  const [planMessage, setPlanMessage] = useState('')
  const [logModalJob, setLogModalJob] = useState(null)
  const [rawOutputData, setRawOutputData] = useState(null)
  const [loadingRawLogs, setLoadingRawLogs] = useState(false)
  const [activeLogTab, setActiveLogTab] = useState('raw')

  useEffect(() => {
    fetchAssessments()
    fetchToolsStatus()
  }, [])

  useEffect(() => {
    if (selectedAssessmentId) {
      fetchScanJobs(selectedAssessmentId)
    } else {
      setJobs([])
      setLoading(false)
    }
  }, [selectedAssessmentId])

  const fetchToolsStatus = async () => {
    try {
      const res = await api.get('/scanners/status')
      setToolsStatus(res.data || [])
    } catch (err) {
      console.error('Failed to query scanner tools availability:', err)
    }
  }

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

  const fetchScanJobs = async (assId) => {
    try {
      setLoading(true)
      const res = await api.get(`/assessments/${assId}/scan-jobs`)
      setJobs(res.data.items || [])
    } catch (err) {
      console.error('Failed to load scan jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePlan = async () => {
    if (!selectedAssessmentId) return
    try {
      setPlanning(true)
      setPlanMessage('')
      const res = await api.post(`/assessments/${selectedAssessmentId}/scan-jobs/plan`, {
        override_existing: true,
        priority: 'normal'
      })
      setPlanMessage(res.data.message || `Created ${res.data.planned_jobs_count} scan jobs.`)
      await fetchScanJobs(selectedAssessmentId)
      setTimeout(() => setPlanMessage(''), 6000)
    } catch (err) {
      console.error('Failed to generate scan plan:', err)
    } finally {
      setPlanning(false)
    }
  }

  const handleExecuteSingleJob = async (jobId) => {
    try {
      setExecutingJobId(jobId)
      await api.post(`/assessments/${selectedAssessmentId}/scan-jobs/${jobId}/execute`)
      await fetchScanJobs(selectedAssessmentId)
    } catch (err) {
      console.error('Failed to execute job:', err)
    } finally {
      setExecutingJobId(null)
    }
  }

  const handleExecuteAllJobs = async () => {
    if (!selectedAssessmentId) return
    try {
      setExecutingAll(true)
      await api.post(`/assessments/${selectedAssessmentId}/scan-jobs/execute-all`)
      await fetchScanJobs(selectedAssessmentId)
    } catch (err) {
      console.error('Failed to execute all scan jobs:', err)
    } finally {
      setExecutingAll(false)
    }
  }

  const handleCancelJob = async (jobId) => {
    try {
      await api.post(`/assessments/${selectedAssessmentId}/scan-jobs/${jobId}/cancel`)
      fetchScanJobs(selectedAssessmentId)
    } catch (err) {
      console.error('Failed to cancel job:', err)
    }
  }

  const openLogModal = async (job) => {
    setLogModalJob(job)
    setRawOutputData(null)
    setLoadingRawLogs(true)
    setActiveLogTab('raw')
    try {
      const res = await api.get(`/assessments/${selectedAssessmentId}/scan-jobs/${job.id}/raw`)
      setRawOutputData(res.data)
    } catch (err) {
      console.error('Failed to load raw scan artifacts:', err)
      setRawOutputData({ error: 'Could not load raw scan logs or artifacts from disk.' })
    } finally {
      setLoadingRawLogs(false)
    }
  }

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
            <h1 className="text-3xl font-bold text-white tracking-tight">Security Scanners & Execution</h1>
          </div>
          <p className="text-dark-400 mt-1">
            Real multi-engine execution (OWASP ZAP, Nuclei, Semgrep, Dependency-Check, Custom Rules)
          </p>
        </div>

        {/* Assessment Selector & Actions */}
        <div className="flex flex-wrap items-center gap-3">
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
                onClick={handleGeneratePlan}
                disabled={planning || executingAll}
                className="flex items-center gap-2 px-3.5 py-2 bg-dark-800 hover:bg-dark-700 text-white rounded-lg text-xs font-semibold transition-colors border border-dark-700 disabled:opacity-50"
              >
                <Sliders className="w-4 h-4 text-cyan-400" />
                {planning ? 'Planning...' : 'Generate Plan'}
              </button>

              <button
                onClick={handleExecuteAllJobs}
                disabled={executingAll || jobs.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-lg shadow-blue-600/20 disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-current" />
                {executingAll ? 'Executing Scanners...' : 'Run Assessment Scans'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tool Installation & Availability Row */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-400" />
            Scanner Engine Availability on Host
          </h3>
          <button
            onClick={fetchToolsStatus}
            className="text-xs text-dark-400 hover:text-white flex items-center gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Tools
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {toolsStatus.map((tool) => {
            const Icon = SCANNER_ICONS[tool.scanner] || Shield
            return (
              <div
                key={tool.scanner}
                className={clsx(
                  'p-3.5 rounded-xl border flex flex-col justify-between text-xs transition-all',
                  tool.available
                    ? 'bg-dark-850 border-emerald-500/30'
                    : 'bg-dark-850/60 border-dark-800'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-dark-300" />
                    <span className="font-semibold text-white text-xs">{tool.name.split(' ')[0]}</span>
                  </div>
                  {tool.available ? (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      <Check className="w-3 h-3" /> Installed
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      <X className="w-3 h-3" /> Unavailable
                    </span>
                  )}
                </div>

                <div className="mt-2 text-[10px] text-dark-400 font-mono truncate">
                  {tool.available ? (
                    <span className="text-dark-300 truncate" title={tool.resolved_path}>
                      {tool.resolved_path === 'built-in' ? 'Built-in Native' : 'PATH Resolved'}
                    </span>
                  ) : (
                    <span className="text-dark-500">Not in PATH</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {planMessage && (
        <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center gap-2 shadow-lg">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{planMessage}</span>
        </div>
      )}

      {/* Scan Jobs List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      ) : !selectedAssessmentId ? (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <Sliders className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">Select an Assessment</h3>
          <p className="text-sm text-dark-400 mt-1">Choose an assessment to view or execute scanner jobs.</p>
        </div>
      ) : jobs.length > 0 ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {jobs.map((job) => {
              const Icon = SCANNER_ICONS[job.scanner] || Shield
              const isExecutingThis = executingJobId === job.id || (executingAll && job.status === 'running')
              return (
                <div
                  key={job.id}
                  className="bg-dark-900 rounded-xl border border-dark-800 p-5 hover:border-dark-700 transition-all flex flex-col justify-between shadow-lg"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-dark-800 border border-dark-700 rounded-lg text-blue-400">
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-white">
                            {SCANNER_LABELS[job.scanner] || job.scanner.toUpperCase()}
                          </h3>
                          <span className="text-[10px] font-mono text-dark-400 uppercase">
                            Priority: {job.priority}
                          </span>
                        </div>
                      </div>
                      <span
                        className={clsx(
                          'px-2.5 py-0.5 text-[10px] font-mono rounded-full border uppercase font-bold',
                          JOB_STATUS_COLORS[job.status] || 'bg-dark-700 text-dark-300'
                        )}
                      >
                        {job.status.replace('_', ' ')}
                      </span>
                    </div>

                    {/* Target & Timing */}
                    <div className="mt-4 space-y-1 text-xs">
                      <div className="text-dark-400 text-[11px] truncate">
                        Target: <span className="font-mono text-dark-200">{job.target}</span>
                      </div>
                      {job.completed_at && (
                        <div className="text-dark-400 text-[11px]">
                          Finished: <span className="text-dark-300 font-mono">{new Date(job.completed_at).toLocaleTimeString()}</span>
                        </div>
                      )}
                    </div>

                    {/* Error / Status Message */}
                    {job.error && (
                      <div className="mt-3 p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-[11px] leading-relaxed">
                        {job.error}
                      </div>
                    )}

                    {/* Result Location */}
                    {job.result_location && (
                      <div className="mt-3 p-2 bg-dark-850 rounded border border-dark-800 text-[10px] font-mono text-dark-400 truncate">
                        Artifacts: <span className="text-dark-300">{job.result_location.split('assessments')[1] || job.result_location}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-5 pt-3 border-t border-dark-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      {(job.status === 'pending' || job.status === 'queued') && (
                        <button
                          onClick={() => handleExecuteSingleJob(job.id)}
                          disabled={isExecutingThis || executingAll}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded text-xs font-semibold transition-colors disabled:opacity-50"
                        >
                          <Play className="w-3 h-3" />
                          {isExecutingThis ? 'Running...' : 'Run Scan'}
                        </button>
                      )}

                      {job.status === 'queued' && (
                        <button
                          onClick={() => handleCancelJob(job.id)}
                          className="text-red-400 hover:text-red-300 text-xs font-medium"
                        >
                          Cancel
                        </button>
                      )}
                    </div>

                    {(job.status === 'completed' || job.status === 'failed' || job.status === 'unavailable') && (
                      <button
                        onClick={() => openLogModal(job)}
                        className="flex items-center gap-1 text-dark-300 hover:text-white text-xs font-medium"
                      >
                        <FileText className="w-3.5 h-3.5 text-cyan-400" />
                        View Raw Logs
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 text-center p-6">
          <Sliders className="w-12 h-12 text-dark-500 mb-3" />
          <h3 className="text-lg font-medium text-white">No scan jobs planned yet</h3>
          <p className="text-sm text-dark-400 mt-1 max-w-sm">
            Generate a scan plan to queue jobs based on the assessment's selected modules and attack surface.
          </p>
          <button
            onClick={handleGeneratePlan}
            disabled={planning}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
          >
            {planning ? 'Generating Plan...' : 'Generate Scan Plan'}
          </button>
        </div>
      )}

      {/* RAW LOGS & ARTIFACTS MODAL */}
      {logModalJob && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 bg-dark-850 border-b border-dark-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Raw Scan Artifacts: {SCANNER_LABELS[logModalJob.scanner] || logModalJob.scanner}
                  </h3>
                  <p className="text-[11px] font-mono text-dark-400">
                    Job ID: #{logModalJob.id} | Status: {logModalJob.status.toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setLogModalJob(null)}
                className="p-1.5 hover:bg-dark-700 rounded-lg text-dark-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Navigation Tabs */}
            <div className="flex border-b border-dark-800 bg-dark-900 px-4 text-xs">
              {[
                { id: 'raw', label: 'Raw Output / JSON' },
                { id: 'stdout', label: 'Standard Output (stdout)' },
                { id: 'stderr', label: 'Standard Error (stderr)' },
                { id: 'metadata', label: 'Execution Metadata' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveLogTab(tab.id)}
                  className={clsx(
                    'py-3 px-4 font-semibold border-b-2 transition-colors',
                    activeLogTab === tab.id
                      ? 'border-blue-500 text-blue-400 bg-dark-850/50'
                      : 'border-transparent text-dark-400 hover:text-white'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Modal Content */}
            <div className="p-5 flex-1 overflow-y-auto bg-dark-950 font-mono text-xs text-dark-200">
              {loadingRawLogs ? (
                <div className="flex items-center justify-center h-48">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
                </div>
              ) : !rawOutputData ? (
                <p className="text-dark-400">No log data found.</p>
              ) : activeLogTab === 'raw' ? (
                <pre className="whitespace-pre-wrap leading-relaxed text-dark-200 bg-dark-900 p-4 rounded-xl border border-dark-800 overflow-x-auto">
                  {rawOutputData.result_data ? JSON.stringify(rawOutputData.result_data, null, 2) : 'No raw JSON report generated.'}
                </pre>
              ) : activeLogTab === 'stdout' ? (
                <pre className="whitespace-pre-wrap leading-relaxed text-emerald-400 bg-dark-900 p-4 rounded-xl border border-dark-800 overflow-x-auto">
                  {rawOutputData.stdout || '(Stdout is empty)'}
                </pre>
              ) : activeLogTab === 'stderr' ? (
                <pre className="whitespace-pre-wrap leading-relaxed text-red-400 bg-dark-900 p-4 rounded-xl border border-dark-800 overflow-x-auto">
                  {rawOutputData.stderr || '(Stderr is empty)'}
                </pre>
              ) : (
                <pre className="whitespace-pre-wrap leading-relaxed text-cyan-400 bg-dark-900 p-4 rounded-xl border border-dark-800 overflow-x-auto">
                  {JSON.stringify(rawOutputData.metadata, null, 2)}
                </pre>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 bg-dark-850 border-t border-dark-800 flex items-center justify-between text-xs text-dark-400">
              <span className="font-mono text-[11px] truncate">
                Disk Location: {rawOutputData?.result_location || 'Local Storage'}
              </span>
              <button
                onClick={() => setLogModalJob(null)}
                className="px-4 py-1.5 bg-dark-700 hover:bg-dark-600 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

