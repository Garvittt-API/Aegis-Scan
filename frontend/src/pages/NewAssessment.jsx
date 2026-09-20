import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Shield,
  Check,
  Target,
  Sparkles,
  AlertTriangle,
  Info,
  Server,
  Code,
  Layers,
  Settings2,
  Sliders,
  CheckCircle2,
  ExternalLink
} from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

const STEPS = [
  { id: 1, name: 'Target', description: 'Target selection & authorization' },
  { id: 2, name: 'Scope', description: 'Attack surface components' },
  { id: 3, name: 'Modules', description: 'Scanner engine selection' },
  { id: 4, name: 'Settings', description: 'Safe execution parameters' },
  { id: 5, name: 'Review', description: 'Validation & confirmation' }
]

export default function NewAssessment() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialTargetId = searchParams.get('target_id')

  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [presetNotice, setPresetNotice] = useState('')
  const [availableTargets, setAvailableTargets] = useState([])
  const [targetMode, setTargetMode] = useState(initialTargetId ? 'existing' : 'new') // 'existing' or 'new'
  const [validationResult, setValidationResult] = useState(null)
  const [validating, setValidating] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    target_id: initialTargetId ? parseInt(initialTargetId, 10) : null,
    description: '',
    target_name: '',
    target_type: 'web',
    target_url: '',
    source_path: '',
    environment: 'local',
    authorization_confirmed: false,
    scope: {
      web_application: true,
      apis: true,
      client_side: true,
      source_code: true,
      dependencies: true,
      configuration: true
    },
    modules: {
      dast: true,
      nuclei: true,
      sast: true,
      sca: true,
      custom_checks: true
    },
    scan_settings: {
      rate_limit: 'low',
      crawl_depth: 2,
      timeout: 60,
      follow_redirects: true,
      passive_checks: true,
      active_testing: false
    }
  })

  // Load existing targets
  useEffect(() => {
    fetchTargets()
  }, [])

  // If initial target ID is passed, auto-select it
  useEffect(() => {
    if (initialTargetId && availableTargets.length > 0) {
      const selected = availableTargets.find(t => t.id === parseInt(initialTargetId, 10))
      if (selected) {
        applySelectedTarget(selected)
      }
    }
  }, [initialTargetId, availableTargets])

  const fetchTargets = async () => {
    try {
      const res = await api.get('/targets?limit=100')
      setAvailableTargets(res.data.items || [])
    } catch (err) {
      console.error('Failed to load targets:', err)
    }
  }

  const applySelectedTarget = (target) => {
    setFormData(prev => ({
      ...prev,
      target_id: target.id,
      target_name: target.name,
      target_type: target.target_type,
      target_url: target.base_url || '',
      source_path: target.source_path || '',
      environment: target.environment,
      name: prev.name || `${target.name} Security Assessment`
    }))
  }

  const handleTargetSelectionChange = (e) => {
    const targetId = parseInt(e.target.value, 10)
    if (!targetId) {
      setFormData(prev => ({ ...prev, target_id: null }))
      return
    }
    const selected = availableTargets.find(t => t.id === targetId)
    if (selected) {
      applySelectedTarget(selected)
    }
  }

  const loadWorldMonitorPreset = async () => {
    try {
      setLoading(true)
      const res = await api.get('/assessments/presets/world-monitor')
      const preset = res.data

      setFormData({
        name: preset.name,
        target_id: null,
        description: preset.description,
        target_name: preset.target_name,
        target_type: preset.target_type,
        target_url: preset.target_url,
        source_path: preset.source_path,
        environment: preset.environment,
        authorization_confirmed: true,
        scope: { ...preset.scope },
        modules: { ...preset.modules },
        scan_settings: { ...preset.scan_settings }
      })
      setTargetMode('new')
      setPresetNotice('World Monitor SIH Preset loaded successfully with safe local configuration defaults.')
      setError('')
      setTimeout(() => setPresetNotice(''), 4000)
    } catch (err) {
      console.error('Failed to load preset:', err)
      setError('Could not load preset from backend')
    } finally {
      setLoading(false)
    }
  }

  const validateStep = (step) => {
    setError('')
    if (step === 1) {
      if (!formData.name.trim()) {
        setError('Assessment name is required.')
        return false
      }
      if (!formData.target_url && !formData.source_path) {
        setError('Please provide at least a Target URL or a Source Path.')
        return false
      }
      if (!formData.authorization_confirmed) {
        setError('You must confirm that you have authorization to test this target.')
        return false
      }
    }
    return true
  }

  const handleNext = async () => {
    if (!validateStep(currentStep)) return

    if (currentStep === 4) {
      // Run backend configuration validation before reaching review step
      await runBackendValidation()
    }

    if (currentStep < 5) {
      setCurrentStep(prev => prev + 1)
    }
  }

  const runBackendValidation = async () => {
    setValidating(true)
    try {
      const res = await api.post('/assessments/validate', {
        name: formData.name,
        target_id: formData.target_id,
        description: formData.description,
        target_url: formData.target_url || null,
        source_path: formData.source_path || null,
        environment: formData.environment,
        authorization_confirmed: formData.authorization_confirmed,
        scope: formData.scope,
        modules: formData.modules,
        scan_settings: formData.scan_settings
      })
      setValidationResult(res.data)
    } catch (err) {
      console.error('Validation error:', err)
    } finally {
      setValidating(false)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')

    try {
      // 1. If targetMode is 'new' and target doesn't exist yet, we can register or link it
      let targetId = formData.target_id

      if (targetMode === 'new' && !targetId && formData.target_name) {
        try {
          const targetRes = await api.post('/targets', {
            name: formData.target_name || `${formData.name} Target`,
            target_type: formData.target_type,
            base_url: formData.target_url || null,
            source_path: formData.source_path || null,
            environment: formData.environment,
            authorization_status: 'authorized',
            description: `Auto-registered via assessment: ${formData.name}`
          })
          targetId = targetRes.data.id
        } catch (targetErr) {
          console.warn('Target auto-creation notice:', targetErr)
        }
      }

      // 2. Create the assessment
      const payload = {
        name: formData.name,
        target_id: targetId,
        description: formData.description,
        target_url: formData.target_url || null,
        source_path: formData.source_path || null,
        environment: formData.environment,
        authorization_confirmed: formData.authorization_confirmed,
        scope: formData.scope,
        modules: formData.modules,
        scan_settings: formData.scan_settings
      }

      const res = await api.post('/assessments', payload)
      navigate(`/assessments/${res.data.id}`)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (detail?.errors) {
        setError(detail.errors.join(', '))
      } else if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg || d.message).join(', '))
      } else {
        setError('Failed to create assessment. Please check inputs.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header & Preset Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Assessment Wizard</h1>
          <p className="text-dark-400 mt-1">Configure a multi-engine security assessment with safe boundaries</p>
        </div>
        <button
          onClick={loadWorldMonitorPreset}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-600/20"
        >
          <Sparkles className="w-4 h-4 text-yellow-300" />
          Load World Monitor Preset
        </button>
      </div>

      {presetNotice && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{presetNotice}</span>
        </div>
      )}

      {/* Steps Navigation Bar */}
      <div className="bg-dark-900 border border-dark-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => {
            const isDone = currentStep > step.id
            const isCurrent = currentStep === step.id
            return (
              <div key={step.id} className="flex items-center flex-1 last:flex-none">
                <div className="flex items-center gap-3">
                  <div
                    className={clsx(
                      'w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all',
                      isDone
                        ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                        : isCurrent
                        ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20 ring-2 ring-blue-500/30'
                        : 'bg-dark-800 text-dark-400 border border-dark-700'
                    )}
                  >
                    {isDone ? <Check className="w-4 h-4" /> : step.id}
                  </div>
                  <div className="hidden sm:block">
                    <p className={clsx('text-xs font-semibold', isCurrent ? 'text-white' : 'text-dark-400')}>
                      {step.name}
                    </p>
                    <p className="text-[10px] text-dark-500">{step.description}</p>
                  </div>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={clsx(
                      'flex-1 h-0.5 mx-3 hidden md:block transition-all',
                      isDone ? 'bg-emerald-500' : 'bg-dark-800'
                    )}
                  />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Wizard Step Body */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-6 shadow-xl">
        {error && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ==================================================== */}
        {/* STEP 1: TARGET SELECTION & AUTHORIZATION             */}
        {/* ==================================================== */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                Step 1: Target Definition & Authorization
              </h2>
              <p className="text-dark-400 text-xs mt-1">Select a registered target system or define a target for this assessment session.</p>
            </div>

            {/* Target Selection Switcher */}
            <div className="grid grid-cols-2 gap-3 p-1 bg-dark-800/80 rounded-lg border border-dark-700">
              <button
                type="button"
                onClick={() => setTargetMode('new')}
                className={clsx(
                  'py-2 text-xs font-medium rounded-md transition-colors',
                  targetMode === 'new'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-dark-400 hover:text-white'
                )}
              >
                Define New / Custom Target
              </button>
              <button
                type="button"
                onClick={() => setTargetMode('existing')}
                className={clsx(
                  'py-2 text-xs font-medium rounded-md transition-colors',
                  targetMode === 'existing'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-dark-400 hover:text-white'
                )}
              >
                Select Existing Target ({availableTargets.length})
              </button>
            </div>

            {/* Assessment Name */}
            <div>
              <label className="block text-xs font-medium text-dark-300 mb-1">
                Assessment Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., World Monitor Security Assessment"
                className="w-full px-3 py-2.5 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>

            {targetMode === 'existing' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-dark-300 mb-1">
                    Choose Registered Target *
                  </label>
                  <select
                    value={formData.target_id || ''}
                    onChange={handleTargetSelectionChange}
                    className="w-full px-3 py-2.5 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- Select a target --</option>
                    {availableTargets.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.target_type} - {t.environment})
                      </option>
                    ))}
                  </select>
                </div>

                {formData.target_id && (
                  <div className="p-4 bg-dark-800/60 border border-dark-700 rounded-lg space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Selected Target:</span>
                      <span className="text-white font-medium">{formData.target_name}</span>
                    </div>
                    {formData.target_url && (
                      <div className="flex justify-between">
                        <span className="text-dark-400">Base URL:</span>
                        <span className="text-blue-400 font-mono">{formData.target_url}</span>
                      </div>
                    )}
                    {formData.source_path && (
                      <div className="flex justify-between">
                        <span className="text-dark-400">Source Path:</span>
                        <span className="text-emerald-400 font-mono">{formData.source_path}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-dark-300 mb-1">
                      Target Name / Label
                    </label>
                    <input
                      type="text"
                      value={formData.target_name}
                      onChange={(e) => setFormData({ ...formData, target_name: e.target.value })}
                      placeholder="e.g. World Monitor Local"
                      className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
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
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-dark-300 mb-1">
                      Base URL (for DAST / Web Crawling)
                    </label>
                    <input
                      type="url"
                      value={formData.target_url}
                      onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
                      placeholder="http://localhost:5173"
                      className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 font-mono text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-dark-300 mb-1">
                      Source Path (for SAST / Semgrep)
                    </label>
                    <input
                      type="text"
                      value={formData.source_path}
                      onChange={(e) => setFormData({ ...formData, source_path: e.target.value })}
                      placeholder="./worldmonitor or relative directory"
                      className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 font-mono text-xs"
                    />
                  </div>
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
                    <option value="local">Local Environment (Safe default)</option>
                    <option value="staging">Staging Environment</option>
                    <option value="production">Production Environment</option>
                    <option value="authorized_remote">Authorized Remote</option>
                  </select>
                </div>
              </div>
            )}

            {/* Mandatory Authorization Warning */}
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl space-y-3">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-yellow-300">Authorization Verification</h4>
                  <p className="text-xs text-dark-300 mt-1 leading-relaxed">
                    AegisScan requires explicit confirmation before initiating attack surface analysis.
                    Assessments must only be performed against systems, repositories, and applications that you own or have explicit authorization to assess.
                  </p>
                </div>
              </div>

              <label className="flex items-start gap-3 p-3 bg-dark-900/80 rounded-lg cursor-pointer hover:bg-dark-900 transition-colors border border-dark-700">
                <input
                  type="checkbox"
                  checked={formData.authorization_confirmed}
                  onChange={(e) => setFormData({ ...formData, authorization_confirmed: e.target.checked })}
                  className="mt-0.5 w-4 h-4 rounded border-dark-600 bg-dark-800 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-xs text-white font-medium">
                  I confirm that I am authorized to assess this target and understand AegisScan operates under safe, non-destructive testing controls.
                </span>
              </label>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* STEP 2: ASSESSMENT SCOPE                             */}
        {/* ==================================================== */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-400" />
                Step 2: Assessment Scope
              </h2>
              <p className="text-dark-400 text-xs mt-1">Configure which application layers and components to include in the assessment scope.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                {
                  key: 'web_application',
                  title: 'Web Application',
                  desc: 'HTML views, server-rendered routes, forms, cookies, and HTTP headers.',
                  badge: 'DAST / Discovery'
                },
                {
                  key: 'apis',
                  title: 'REST & GraphQL APIs',
                  desc: 'JSON/XML endpoints, query parameters, authentication headers, and methods.',
                  badge: 'DAST / Nuclei'
                },
                {
                  key: 'client_side',
                  title: 'Client-side Security',
                  desc: 'Bundled JS files, source maps, DOM sinks, and third-party script integrations.',
                  badge: 'Static / Dynamic'
                },
                {
                  key: 'source_code',
                  title: 'Source Code & AST',
                  desc: 'Underlying codebase files, route controllers, and sink/source flow patterns.',
                  badge: 'SAST'
                },
                {
                  key: 'dependencies',
                  title: 'Dependencies & Packages',
                  desc: 'Package manifests (package.json, requirements.txt, go.mod) and known CVEs.',
                  badge: 'SCA'
                },
                {
                  key: 'configuration',
                  title: 'Configuration & Secrets',
                  desc: 'Hardcoded credentials, exposed environment variables, and permissive CORS.',
                  badge: 'Custom / SAST'
                }
              ].map((scopeItem) => (
                <label
                  key={scopeItem.key}
                  className={clsx(
                    'p-4 rounded-xl border cursor-pointer transition-all flex items-start gap-3',
                    formData.scope[scopeItem.key]
                      ? 'bg-blue-600/10 border-blue-500/30'
                      : 'bg-dark-800/50 border-dark-700/50 opacity-60'
                  )}
                >
                  <input
                    type="checkbox"
                    checked={formData.scope[scopeItem.key]}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scope: { ...formData.scope, [scopeItem.key]: e.target.checked }
                      })
                    }
                    className="mt-1 w-4 h-4 rounded border-dark-600 bg-dark-900 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-white">{scopeItem.title}</p>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-800 text-dark-300 border border-dark-700">
                        {scopeItem.badge}
                      </span>
                    </div>
                    <p className="text-xs text-dark-400 mt-1 leading-relaxed">{scopeItem.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* STEP 3: SECURITY MODULES                             */}
        {/* ==================================================== */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-blue-400" />
                Step 3: Security Modules Configuration
              </h2>
              <p className="text-dark-400 text-xs mt-1">
                Configure which scanner engines are registered for this assessment session.
              </p>
            </div>

            <div className="p-3 bg-dark-800/70 border border-blue-500/20 rounded-xl flex items-center gap-3">
              <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <p className="text-xs text-dark-300">
                <span className="font-semibold text-white">Scan Orchestrator Notice:</span> Modules configured here will be invoked by the Scan Orchestrator pipeline during Phase 3.
              </p>
            </div>

            <div className="space-y-3">
              {[
                {
                  key: 'dast',
                  name: 'OWASP ZAP (DAST Engine)',
                  desc: 'Dynamic Application Security Testing for active endpoint spidering and server-side responses.',
                  tag: 'DAST'
                },
                {
                  key: 'nuclei',
                  name: 'Nuclei (Template Engine)',
                  desc: 'Fast YAML template-based vulnerability scanner for security misconfigurations and known CVEs.',
                  tag: 'Vulnerability Engine'
                },
                {
                  key: 'sast',
                  name: 'Semgrep (SAST Engine)',
                  desc: 'Lightweight static analysis over source code ASTs to detect injection flaws, insecure deserialization, and unsafe sinks.',
                  tag: 'SAST'
                },
                {
                  key: 'sca',
                  name: 'Dependency Checker (SCA Engine)',
                  desc: 'Software Composition Analysis auditing direct and transitive package dependencies against vulnerability databases.',
                  tag: 'SCA'
                },
                {
                  key: 'custom_checks',
                  name: 'AegisScan Custom Security Rules',
                  desc: 'Specialized heuristic verification rules tailored for authentication bypasses, IDORs, and misconfigurations.',
                  tag: 'Heuristics'
                }
              ].map((mod) => (
                <label
                  key={mod.key}
                  className={clsx(
                    'flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all',
                    formData.modules[mod.key]
                      ? 'bg-dark-800 border-blue-500/30'
                      : 'bg-dark-850 border-dark-700/50 opacity-50'
                  )}
                >
                  <input
                    type="checkbox"
                    checked={formData.modules[mod.key]}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        modules: { ...formData.modules, [mod.key]: e.target.checked }
                      })
                    }
                    className="mt-1 w-4 h-4 rounded border-dark-600 bg-dark-900 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-white">{mod.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-700 text-blue-400">
                        {mod.tag}
                      </span>
                    </div>
                    <p className="text-xs text-dark-400 mt-1">{mod.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* STEP 4: SCAN SETTINGS & SAFETY                       */}
        {/* ==================================================== */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-blue-400" />
                Step 4: Safe Scan Settings & Guardrails
              </h2>
              <p className="text-dark-400 text-xs mt-1">Configure rate limits, depth boundaries, and safety controls to ensure non-destructive testing.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Rate Limit */}
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <label className="block text-xs font-semibold text-white">
                  Request Rate Limit
                </label>
                <select
                  value={formData.scan_settings.rate_limit}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scan_settings: { ...formData.scan_settings, rate_limit: e.target.value }
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="low">Low (1-5 req/s) — Recommended & Safe</option>
                  <option value="medium">Medium (10-20 req/s) — Moderate Load</option>
                  <option value="high">High (50+ req/s) — Robust Targets Only</option>
                </select>
                <p className="text-[11px] text-dark-400">Controls HTTP concurrency to prevent accidental target degradation.</p>
              </div>

              {/* Max Crawl Depth */}
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <label className="block text-xs font-semibold text-white">
                  Maximum Crawl Depth
                </label>
                <select
                  value={formData.scan_settings.crawl_depth}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scan_settings: { ...formData.scan_settings, crawl_depth: parseInt(e.target.value, 10) }
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value={1}>1 Level (Direct links only)</option>
                  <option value={2}>2 Levels (Standard crawl — Recommended)</option>
                  <option value={3}>3 Levels (Deep discovery)</option>
                  <option value={5}>5 Levels (Extensive traversal)</option>
                </select>
                <p className="text-[11px] text-dark-400">Limits spidering recursion depth across internal paths.</p>
              </div>

              {/* Timeout */}
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <label className="block text-xs font-semibold text-white">
                  Request Timeout (Seconds)
                </label>
                <select
                  value={formData.scan_settings.timeout}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scan_settings: { ...formData.scan_settings, timeout: parseInt(e.target.value, 10) }
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value={30}>30 Seconds</option>
                  <option value={60}>60 Seconds (Standard)</option>
                  <option value={120}>120 Seconds (Slow networks)</option>
                </select>
                <p className="text-[11px] text-dark-400">Maximum threshold to wait for individual HTTP responses.</p>
              </div>

              {/* Follow Redirects */}
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <label className="block text-xs font-semibold text-white">
                  Follow HTTP Redirects
                </label>
                <select
                  value={formData.scan_settings.follow_redirects ? 'yes' : 'no'}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scan_settings: { ...formData.scan_settings, follow_redirects: e.target.value === 'yes' }
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="yes">Yes (Follow 301/302 redirects)</option>
                  <option value="no">No (Strict host origin)</option>
                </select>
                <p className="text-[11px] text-dark-400">Preserves origin boundary security while navigating links.</p>
              </div>
            </div>

            {/* Passive vs Active Testing */}
            <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-white">Passive Inspection vs Active Payloads</h4>
                  <p className="text-[11px] text-dark-400">Passive checks inspect response headers, source maps, and cookies safely.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <label className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg border border-dark-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.scan_settings.passive_checks}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scan_settings: { ...formData.scan_settings, passive_checks: e.target.checked }
                      })
                    }
                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-xs text-white">Enable Passive Checks (Always Safe)</span>
                </label>

                <label className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg border border-dark-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.scan_settings.active_testing}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scan_settings: { ...formData.scan_settings, active_testing: e.target.checked }
                      })
                    }
                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-xs text-white">Enable Active Payloads (Non-Destructive)</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* STEP 5: REVIEW & SAVE                                */}
        {/* ==================================================== */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Step 5: Review & Validate Configuration
              </h2>
              <p className="text-dark-400 text-xs mt-1">Review your assessment parameters and verification status before committing.</p>
            </div>

            {/* Validation Feedback Card */}
            {validating ? (
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500" />
                <span className="text-xs text-dark-300">Validating configuration against backend safety rules...</span>
              </div>
            ) : validationResult ? (
              <div
                className={clsx(
                  'p-4 rounded-xl border space-y-2',
                  validationResult.is_valid
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-red-500/10 border-red-500/30 text-red-300'
                )}
              >
                <div className="flex items-center gap-2 font-semibold text-sm">
                  {validationResult.is_valid ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  )}
                  <span>
                    {validationResult.is_valid
                      ? 'Configuration Validated Successfully'
                      : 'Validation Detected Issues'}
                  </span>
                </div>

                {validationResult.warnings?.length > 0 && (
                  <div className="text-xs text-yellow-400 space-y-1 mt-2">
                    {validationResult.warnings.map((w, i) => (
                      <p key={i}>• Warning: {w}</p>
                    ))}
                  </div>
                )}

                {validationResult.errors?.length > 0 && (
                  <div className="text-xs text-red-400 space-y-1 mt-2">
                    {validationResult.errors.map((err, i) => (
                      <p key={i}>• Error: {err}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : null}

            {/* Summary Review Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <span className="text-dark-400 font-semibold uppercase tracking-wider text-[10px]">Target Details</span>
                <p className="text-white font-medium text-sm">{formData.name}</p>
                {formData.target_url && (
                  <p className="text-blue-400 font-mono">URL: {formData.target_url}</p>
                )}
                {formData.source_path && (
                  <p className="text-emerald-400 font-mono">Path: {formData.source_path}</p>
                )}
                <p className="text-dark-300 capitalize">Environment: {formData.environment}</p>
                <p className="text-emerald-400 flex items-center gap-1.5 mt-2">
                  <Check className="w-3.5 h-3.5" /> Authorization Confirmed
                </p>
              </div>

              <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 space-y-2">
                <span className="text-dark-400 font-semibold uppercase tracking-wider text-[10px]">Active Scanners</span>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {Object.entries(formData.modules)
                    .filter(([_, active]) => active)
                    .map(([key]) => (
                      <span key={key} className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded border border-blue-500/30 uppercase font-mono text-[10px]">
                        {key.replace('_', ' ')}
                      </span>
                    ))}
                </div>
                <div className="pt-2 border-t border-dark-700/60 text-dark-400 space-y-1">
                  <p>Rate Limit: <span className="text-white capitalize">{formData.scan_settings.rate_limit}</span></p>
                  <p>Crawl Depth: <span className="text-white">{formData.scan_settings.crawl_depth}</span> | Timeout: <span className="text-white">{formData.scan_settings.timeout}s</span></p>
                  <p>Active Testing: <span className={formData.scan_settings.active_testing ? 'text-yellow-400' : 'text-emerald-400'}>
                    {formData.scan_settings.active_testing ? 'Enabled' : 'Disabled (Safe)'}
                  </span></p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Footer Navigation */}
        <div className="flex items-center justify-between mt-8 pt-5 border-t border-dark-800">
          <button
            type="button"
            onClick={() => (currentStep > 1 ? setCurrentStep(prev => prev - 1) : navigate('/assessments'))}
            className="flex items-center gap-2 px-4 py-2 text-dark-300 hover:text-white text-xs font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {currentStep === 1 ? 'Cancel' : 'Previous Step'}
          </button>

          {currentStep < 5 ? (
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-md shadow-blue-600/20"
            >
              <span>Next Step</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || (validationResult && !validationResult.is_valid)}
              className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  <span>Creating Assessment...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Create Assessment</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
