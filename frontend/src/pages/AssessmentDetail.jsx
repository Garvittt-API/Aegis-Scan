import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Play,
  RefreshCw,
  Target,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Shield,
  FileText,
  Sliders,
  Layers,
  Sparkles,
  Search,
  Check,
  CircleDot,
  ArrowRight,
  Globe,
  SlidersHorizontal
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const PIPELINE_STAGES = [
  { id: 'target', label: 'Target', status: 'completed', desc: 'Scope defined' },
  { id: 'discovery', label: 'Discovery', status: 'active', desc: 'Same-Origin Spidering' },
  { id: 'attack_surface', label: 'Attack Surface', status: 'active', desc: 'Inventory & Fingerprinting' },
  { id: 'scan_planning', label: 'Scan Planning', status: 'active', desc: 'Job Planner' },
  { id: 'scan_jobs', label: 'Scan Jobs', status: 'queued', desc: 'Queue & Adapters' },
  { id: 'findings', label: 'Findings', status: 'future', desc: 'Multi-Engine Results (Phase 4)' },
  { id: 'normalize', label: 'Normalization', status: 'future', desc: 'Unified Data Model (Phase 5)' },
  { id: 'verify', label: 'Verification', status: 'future', desc: 'Evidence Collection (Phase 6)' },
  { id: 'risk_report', label: 'Risk & Report', status: 'future', desc: 'Context Risk & Reports (Phase 7-9)' }
]

export default function AssessmentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [assessment, setAssessment] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAssessment()
  }, [id])

  const fetchAssessment = async () => {
    try {
      setLoading(true)
      const [assessmentRes, summaryRes] = await Promise.all([
        api.get(`/assessments/${id}`),
        api.get(`/assessments/${id}/summary`)
      ])
      setAssessment(assessmentRes.data)
      setSummary(summaryRes.data)
    } catch (err) {
      setError('Failed to load assessment details')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error || !assessment) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-dark-900 rounded-xl border border-dark-800 p-6">
        <AlertTriangle className="w-12 h-12 text-red-400 mb-3" />
        <p className="text-white font-medium">{error || 'Assessment not found'}</p>
        <button
          onClick={() => navigate('/assessments')}
          className="mt-4 px-4 py-2 bg-dark-800 hover:bg-dark-700 text-white rounded-lg text-xs"
        >
          Back to Assessments
        </button>
      </div>
    )
  }

  const modules = assessment.modules || {
    dast: assessment.enable_zap,
    nuclei: assessment.enable_nuclei,
    sast: assessment.enable_semgrep,
    sca: assessment.enable_dependency_check,
    custom_checks: assessment.enable_custom_checks
  }

  const scanSettings = assessment.scan_settings || {
    rate_limit: 'low',
    crawl_depth: 2,
    timeout: 60,
    follow_redirects: true,
    passive_checks: true,
    active_testing: false
  }

  const scope = assessment.scope || {
    web_application: true,
    apis: true,
    client_side: true,
    source_code: !!assessment.source_path,
    dependencies: true,
    configuration: true
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/assessments"
            className="p-2 bg-dark-900 hover:bg-dark-800 border border-dark-800 rounded-lg text-dark-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">{assessment.name}</h1>
              <span className="px-2.5 py-0.5 text-xs font-mono uppercase rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                {assessment.status}
              </span>
            </div>
            <p className="text-dark-400 text-xs mt-1">
              {assessment.description || 'Configured security assessment session.'}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Link
            to={`/assessments/${id}/attack-surface`}
            className="flex items-center gap-2 px-3.5 py-2 bg-dark-800 hover:bg-dark-700 text-white rounded-lg text-xs font-semibold transition-colors border border-dark-700"
          >
            <Globe className="w-4 h-4 text-cyan-400" />
            Attack Surface
          </Link>
          <Link
            to={`/assessments/${id}/scan-jobs`}
            className="flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-md shadow-blue-600/20"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Scan Jobs
          </Link>
          <button
            onClick={fetchAssessment}
            className="p-2 bg-dark-900 hover:bg-dark-800 border border-dark-800 rounded-lg text-dark-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Target & Assessment Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-4 space-y-1">
          <div className="flex items-center gap-2 text-dark-400 text-xs">
            <Target className="w-4 h-4 text-blue-400" />
            <span>Target System</span>
          </div>
          <p className="text-white font-semibold text-sm truncate">
            {assessment.target_name || 'Direct Configuration'}
          </p>
          <p className="text-[11px] text-dark-400 font-mono truncate">
            {assessment.target_url || assessment.source_path || 'None'}
          </p>
        </div>

        <div className="bg-dark-900 rounded-xl border border-dark-800 p-4 space-y-1">
          <div className="flex items-center gap-2 text-dark-400 text-xs">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>Authorization Status</span>
          </div>
          <p className="text-emerald-400 font-semibold text-sm flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            {assessment.authorization_confirmed ? 'Verified Authorized' : 'Unconfirmed'}
          </p>
          <p className="text-[11px] text-dark-400 capitalize">
            Env: {assessment.environment}
          </p>
        </div>

        <div className="bg-dark-900 rounded-xl border border-dark-800 p-4 space-y-1">
          <div className="flex items-center gap-2 text-dark-400 text-xs">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>Scan Safety Policy</span>
          </div>
          <p className="text-white font-semibold text-sm capitalize">
            Rate: {scanSettings.rate_limit} | Depth: {scanSettings.crawl_depth}
          </p>
          <p className="text-[11px] text-dark-400">
            Active Testing: {scanSettings.active_testing ? 'Enabled' : 'Disabled (Safe)'}
          </p>
        </div>

        <div className="bg-dark-900 rounded-xl border border-dark-800 p-4 space-y-1">
          <div className="flex items-center gap-2 text-dark-400 text-xs">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span>Created Timestamp</span>
          </div>
          <p className="text-white font-semibold text-sm">
            {formatDate(assessment.created_at)}
          </p>
          <p className="text-[11px] text-dark-400">
            Operator: {assessment.created_by || 'analyst'}
          </p>
        </div>
      </div>

      {/* PIPELINE VISUALIZATION */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-400" />
              AegisScan Assessment Pipeline
            </h2>
            <p className="text-dark-400 text-xs mt-0.5">
              Live lifecycle state across discovery, attack surface inventory, scan jobs, and verification
            </p>
          </div>
          <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-lg border border-cyan-500/20">
            Phase 3: Discovery & Orchestrator Active
          </span>
        </div>

        {/* Pipeline Nodes */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-2 pt-2">
          {PIPELINE_STAGES.map((stage, idx) => {
            const isCompleted = stage.status === 'completed'
            const isActive = stage.status === 'active'
            const isQueued = stage.status === 'queued'
            return (
              <div
                key={stage.id}
                className={clsx(
                  'p-3 rounded-xl border flex flex-col justify-between text-xs transition-all relative',
                  isCompleted
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-white'
                    : isActive
                    ? 'bg-cyan-500/10 border-cyan-500/30 text-white'
                    : isQueued
                    ? 'bg-blue-500/10 border-blue-500/30 text-white'
                    : 'bg-dark-800/40 border-dark-700/50 text-dark-400'
                )}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono text-dark-500 font-bold">0{idx + 1}</span>
                    {isCompleted ? (
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    ) : isActive ? (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    ) : isQueued ? (
                      <span className="w-2 h-2 rounded-full bg-blue-400" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-dark-600" />
                    )}
                  </div>
                  <h4 className="font-semibold text-xs text-white">{stage.label}</h4>
                  <p className="text-[10px] text-dark-400 mt-1 leading-snug">{stage.desc}</p>
                </div>

                <div className="mt-3 pt-2 border-t border-dark-700/40 text-[9px] font-mono font-semibold">
                  {isCompleted && <span className="text-emerald-400">CONFIGURED</span>}
                  {isActive && <span className="text-cyan-400">ACTIVE</span>}
                  {isQueued && <span className="text-blue-400">QUEUED</span>}
                  {stage.status === 'future' && <span className="text-dark-500">READY IN PH4+</span>}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Scope and Modules Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scope Breakdown */}
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6 space-y-4">
          <h3 className="text-md font-bold text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-blue-400" />
            Configured Assessment Scope
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(scope).map(([key, enabled]) => (
              <div
                key={key}
                className={clsx(
                  'p-3 rounded-lg border flex items-center justify-between',
                  enabled
                    ? 'bg-dark-800 border-dark-700 text-white'
                    : 'bg-dark-850 border-dark-800 text-dark-500'
                )}
              >
                <span className="capitalize">{key.replace('_', ' ')}</span>
                {enabled ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <span className="text-[10px] font-mono text-dark-500">Excluded</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Selected Scanners */}
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6 space-y-4">
          <h3 className="text-md font-bold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-400" />
            Registered Security Modules
          </h3>
          <div className="space-y-2 text-xs">
            {[
              { key: 'dast', label: 'OWASP ZAP (DAST)', desc: 'Dynamic Application Security Testing' },
              { key: 'nuclei', label: 'Nuclei Scanner', desc: 'Community & Custom vulnerability templates' },
              { key: 'sast', label: 'Semgrep (SAST)', desc: 'Static code analysis for pattern vulnerabilities' },
              { key: 'sca', label: 'Dependency Checker', desc: 'Software Composition Analysis' },
              { key: 'custom_checks', label: 'AegisScan Custom Rules', desc: 'Local security heuristics' }
            ].map((sc) => {
              const active = modules[sc.key]
              return (
                <div
                  key={sc.key}
                  className={clsx(
                    'p-3 rounded-lg border flex items-center justify-between',
                    active
                      ? 'bg-dark-800 border-dark-700 text-white'
                      : 'bg-dark-850 border-dark-800 text-dark-500'
                  )}
                >
                  <div>
                    <span className="font-semibold">{sc.label}</span>
                    <span className="block text-[11px] text-dark-400">{sc.desc}</span>
                  </div>
                  {active ? (
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono">
                      Configured
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono text-dark-500">Disabled</span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
