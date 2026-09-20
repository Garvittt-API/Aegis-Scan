import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import api from '../services/api'
import clsx from 'clsx'

export default function Settings() {
  const [health, setHealth] = useState(null)
  const [scanners, setScanners] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkHealth()
    checkScanners()
  }, [])

  const checkHealth = async () => {
    try {
      const response = await api.get('/health/ready')
      setHealth(response.data)
    } catch (error) {
      setHealth({ status: 'error', database: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const checkScanners = async () => {
    try {
      const response = await api.get('/scanners/status')
      setScanners(response.data || [])
    } catch (error) {
      setScanners([])
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-dark-400 mt-1">System status and configuration</p>
      </div>

      {/* System Status */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">System Status</h2>
          <button
            onClick={() => { checkHealth(); checkScanners() }}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-dark-800 hover:bg-dark-700 text-dark-300 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        ) : (
          <div className="space-y-3">
            <StatusItem
              name="API Server"
              status={health?.status === 'ready' ? 'healthy' : 'error'}
            />
            <StatusItem
              name="Database"
              status={health?.database === 'ready' ? 'healthy' : 'error'}
            />
          </div>
        )}
      </div>

      {/* Scanner Status */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Scanner Availability</h2>
        <div className="space-y-3">
          {scanners.map((scanner) => (
            <ScannerStatus key={scanner.scanner} name={scanner.name} available={scanner.available} />
          ))}
        </div>
        <p className="text-sm text-dark-400 mt-4">
          Availability is detected from the local host. Unavailable optional scanners do not stop the assessment.
        </p>
      </div>

      {/* About */}
      <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">About AegisScan</h2>
        <div className="space-y-2 text-dark-300">
          <p><span className="text-dark-400">Version:</span> 1.0.0</p>
          <p><span className="text-dark-400">Built for:</span> Smart India Hackathon 2026</p>
          <p><span className="text-dark-400">Problem Statement:</span> SIH26163 - Security Assessment</p>
        </div>
        <div className="mt-4 p-4 bg-dark-800 rounded-lg">
          <p className="text-dark-300 text-sm">
            AegisScan is a multi-engine security assessment platform that combines DAST, SAST,
            dependency analysis, attack-surface discovery and custom security checks into one
            evidence-driven workflow.
          </p>
        </div>
      </div>
    </div>
  )
}

function StatusItem({ name, status }) {
  const isHealthy = status === 'healthy'
  return (
    <div className="flex items-center justify-between p-3 bg-dark-800 rounded-lg">
      <span className="text-dark-200">{name}</span>
      <div className="flex items-center gap-2">
        {isHealthy ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
        <span className={clsx('text-sm', isHealthy ? 'text-green-400' : 'text-red-400')}>
          {status}
        </span>
      </div>
    </div>
  )
}

function ScannerStatus({ name, available }) {
  return (
    <div className="flex items-center justify-between p-3 bg-dark-800 rounded-lg">
      <span className="text-dark-200">{name}</span>
      <div className="flex items-center gap-2">
        {available ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-dark-400" />
        )}
        <span className={clsx('text-sm', available ? 'text-green-400' : 'text-dark-400')}>
          {available ? 'Available' : 'Not Configured'}
        </span>
      </div>
    </div>
  )
}
