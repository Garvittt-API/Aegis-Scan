import { useEffect, useState } from 'react'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Target,
  TrendingUp,
  Clock
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
  const [stats, setStats] = useState({
    totalAssessments: 0,
    totalFindings: 0,
    verifiedFindings: 0,
    criticalFindings: 0,
    highFindings: 0,
    mediumFindings: 0,
    lowFindings: 0
  })
  const [recentAssessments, setRecentAssessments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [assessmentsRes, findingsRes] = await Promise.all([
        api.get('/assessments?limit=5'),
        api.get('/findings?limit=100')
      ])

      const assessments = assessmentsRes.data.items || []
      const findings = findingsRes.data.items || []

      setRecentAssessments(assessments)
      setStats({
        totalAssessments: assessmentsRes.data.total || 0,
        totalFindings: findingsRes.data.total || 0,
        verifiedFindings: findings.filter(f => f.verification_status === 'verified').length,
        criticalFindings: findings.filter(f => f.severity === 'critical').length,
        highFindings: findings.filter(f => f.severity === 'high').length,
        mediumFindings: findings.filter(f => f.severity === 'medium').length,
        lowFindings: findings.filter(f => f.severity === 'low').length
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const severityData = [
    { name: 'Critical', value: stats.criticalFindings, color: COLORS.critical },
    { name: 'High', value: stats.highFindings, color: COLORS.high },
    { name: 'Medium', value: stats.mediumFindings, color: COLORS.medium },
    { name: 'Low', value: stats.lowFindings, color: COLORS.low }
  ].filter(d => d.value > 0)

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
          value={stats.totalFindings}
          icon={AlertTriangle}
          color="text-orange-400"
          bgColor="bg-orange-500/10"
        />
        <StatCard
          title="Verified"
          value={stats.verifiedFindings}
          icon={CheckCircle}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        <StatCard
          title="Critical"
          value={stats.criticalFindings}
          icon={Shield}
          color="text-red-400"
          bgColor="bg-red-500/10"
        />
        <StatCard
          title="Assessments"
          value={stats.totalAssessments}
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
              No findings yet
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
