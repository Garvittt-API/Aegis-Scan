import { useEffect, useState } from 'react'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Target,
  TrendingUp,
  Clock,
  History
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import api from '../services/api'
import clsx from 'clsx'

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  informational: '#6b7280'
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null)
  const [recentAssessments, setRecentAssessments] = useState([])
  const [trends, setTrends] = useState(null)
  const [scannerCoverage, setScannerCoverage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyticsError, setAnalyticsError] = useState(false)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [overviewRes, assessmentsRes, trendsRes, scannersRes] = await Promise.all([
        api.get('/analytics/overview'),
        api.get('/analytics/assessments'),
        api.get('/analytics/trends'),
        api.get('/analytics/scanners')
      ])
      setAnalytics(overviewRes.data)
      setRecentAssessments((assessmentsRes.data.items || []).slice(-5).reverse())
      setTrends(trendsRes.data)
      setScannerCoverage(scannersRes.data)
    } catch (error) {
      setAnalyticsError(true)
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const severityData = analytics ? Object.entries(analytics.severity || {}).map(([name, value]) => ({
    name: name[0].toUpperCase() + name.slice(1), value, color: COLORS[name]
  })).filter(d => d.value > 0) : []

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-dark-400 mt-1">Security assessment overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Findings"
          value={analyticsError ? 'Unavailable' : analytics?.total_findings ?? 0}
          icon={AlertTriangle}
          color="text-orange-400"
          bgColor="bg-orange-500/10"
        />
        <StatCard
          title="Verified"
          value={analyticsError ? 'Unavailable' : analytics?.verified_findings ?? 0}
          icon={CheckCircle}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        <StatCard
          title="Critical"
          value={analyticsError ? 'Unavailable' : analytics?.severity?.critical ?? 0}
          icon={Shield}
          color="text-red-400"
          bgColor="bg-red-500/10"
        />
        <StatCard
          title="Assessments"
          value={analyticsError ? 'Unavailable' : analytics?.assessments ?? 0}
          icon={Target}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Severity Distribution</h2>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px] text-dark-400">
              {analyticsError ? 'Analytics unavailable' : analytics?.total_findings === 0 ? 'No findings were produced by the executed assessments.' : 'Analytics unavailable'}
            </div>
          )}
          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {severityData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-dark-300">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Findings by Category */}
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Assessments</h2>
          {recentAssessments.length > 0 ? (
            <div className="space-y-3">
              {recentAssessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="flex items-center justify-between p-3 bg-dark-800 rounded-lg"
                >
                  <div>
                    <p className="text-white font-medium">{assessment.name}</p>
                    <p className="text-sm text-dark-400">{assessment.target_url || 'No target'}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={clsx(
                        'px-2 py-1 text-xs rounded-full',
                        assessment.status === 'completed' && 'bg-green-500/20 text-green-400',
                        assessment.status === 'running' && 'bg-blue-500/20 text-blue-400',
                        assessment.status === 'pending' && 'bg-yellow-500/20 text-yellow-400'
                      )}
                    >
                      {assessment.status}
                    </span>
                    <span className="text-sm text-dark-400">{assessment.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[250px] text-dark-400">
              <Target className="w-12 h-12 mb-2 opacity-50" />
              <p>No assessments yet</p>
              <p className="text-sm">Create your first assessment to get started</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><History className="w-5 h-5 text-cyan-400" />Assessment History</h2>
          {recentAssessments.length > 0 ? recentAssessments.map(item => (
            <div key={item.id} className="flex items-center justify-between border-b border-dark-800 py-3 last:border-0">
              <div><p className="text-white">#{item.id} {item.name}</p><p className="text-xs text-dark-400">{item.findings} findings | {item.verified} verified</p></div>
              <span className="text-xs text-dark-400">{item.status}</span>
            </div>
          )) : <p className="text-dark-400">No assessments available.</p>}
        </div>
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Security Intelligence</h2>
          <ul className="space-y-3 text-sm text-dark-300">
            <li>{analytics?.open_findings ?? 0} findings are currently open.</li>
            <li>{analytics?.validated_remediations ?? 0} remediations are validated.</li>
            <li>{analytics?.scanner_checks_executed ?? 0} scanner/check types have execution records.</li>
          </ul>
        </div>
      </div>

      {!analyticsError && analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricList title="Verification" values={analytics.verification} empty="No findings were produced." />
          <MetricList title="Categories" values={analytics.categories} empty="No categories recorded." />
          <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Remediation</h2>
            <p className="text-2xl font-semibold text-white">{analytics.validated_remediations}</p>
            <p className="text-sm text-dark-400 mt-1">validated remediations</p>
          </div>
        </div>
      )}

      {!analyticsError && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Assessment Trend</h2>
            {trends?.available ? trends.items.map(item => (
              <div key={item.assessment_id} className="flex justify-between py-2 border-b border-dark-800 last:border-0 text-sm"><span className="text-dark-300">Assessment #{item.assessment_id}</span><span className="text-white">{item.findings} findings</span></div>
            )) : <p className="text-dark-400">{trends?.message || 'Historical trends require multiple assessments.'}</p>}
          </div>
          <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Scanner Coverage</h2>
            {scannerCoverage?.available ? scannerCoverage.items.map(item => (
              <div key={item.scanner} className="flex justify-between py-2 border-b border-dark-800 last:border-0 text-sm"><span className="text-dark-300">{item.scanner}</span><span className="text-white">{item.completed ? 'Completed' : item.unavailable ? 'Unavailable' : item.failed ? 'Failed' : 'Not run'} | {item.findings} findings</span></div>
            )) : <p className="text-dark-400">{scannerCoverage?.message || 'Scanner coverage data unavailable.'}</p>}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color, bgColor }) {
  return (
    <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-dark-400 text-sm">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={clsx('p-3 rounded-lg', bgColor)}>
          <Icon className={clsx('w-6 h-6', color)} />
        </div>
      </div>
    </div>
  )
}

function MetricList({ title, values, empty }) {
  const entries = Object.entries(values || {})
  return (
    <div className="bg-dark-900 rounded-xl border border-dark-800 p-6">
      <h2 className="text-lg font-semibold text-white mb-4">{title}</h2>
      {entries.length ? entries.map(([name, value]) => (
        <div key={name} className="flex justify-between py-2 border-b border-dark-800 last:border-0 text-sm">
          <span className="text-dark-300 capitalize">{name.replaceAll('_', ' ')}</span>
          <span className="text-white font-medium">{value}</span>
        </div>
      )) : <p className="text-dark-400">{empty}</p>}
    </div>
  )
}
