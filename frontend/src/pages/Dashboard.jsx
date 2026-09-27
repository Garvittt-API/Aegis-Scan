import { useEffect, useState } from 'react'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Target,
  TrendingUp,
  Clock,
  History,
  Terminal,
  Activity,
  Cpu,
  Radio,
  Zap
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import api from '../services/api'
import clsx from 'clsx'

const COLORS = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#eab308',
  low: '#00d4ff',
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
    name: name[0].toUpperCase() + name.slice(1),
    value,
    color: COLORS[name] || '#6b7280'
  })).filter(d => d.value > 0) : []

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 font-mono">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-2 border-cyber-accent/20 animate-ping" />
          <div className="w-16 h-16 rounded-full border-2 border-t-cyber-accent border-r-cyber-secondary border-b-cyber-cyan border-l-transparent animate-spin" />
        </div>
        <p className="text-cyber-accent text-sm tracking-[0.25em] animate-pulse uppercase">
          [ INITIALIZING HUD TELEMETRY... ]
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8 font-mono">
      {/* Header HUD Banner */}
      <div className="relative border-b border-cyber-border pb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="inline-block w-2.5 h-2.5 bg-cyber-accent rounded-full animate-ping" />
              <span className="text-xs uppercase tracking-[0.3em] text-cyber-accent">SYSTEM OPERATIONAL // LIVE FEED</span>
            </div>
            <h1 className="text-3xl lg:text-4xl font-black uppercase tracking-wider font-orbitron text-white mt-1 cyber-glitch" data-text="TACTICAL OVERVIEW">
              TACTICAL OVERVIEW
            </h1>
            <p className="text-cyber-muted text-xs tracking-widest uppercase mt-1">
              &gt; REAL-TIME SECURITY THREAT MATRIX &amp; VULNERABILITY TELEMETRY
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="cyber-card px-4 py-2 text-xs flex items-center gap-2 border-cyber-accent/40 bg-cyber-card/80">
              <Radio className="w-4 h-4 text-cyber-accent animate-pulse" />
              <span className="text-cyber-muted uppercase tracking-wider">THREAT LEVEL:</span>
              <span className="font-bold text-cyber-accent tracking-widest">
                {analytics?.severity?.critical > 0 ? 'CRITICAL' : analytics?.severity?.high > 0 ? 'ELEVATED' : 'NOMINAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="TOTAL FINDINGS"
          value={analyticsError ? 'ERR' : analytics?.total_findings ?? 0}
          icon={AlertTriangle}
          accentColor="border-cyber-secondary text-cyber-secondary"
          glowColor="rgba(255, 0, 255, 0.15)"
          code="VULN_COUNT"
        />
        <StatCard
          title="VERIFIED TRUE POSITIVES"
          value={analyticsError ? 'ERR' : analytics?.verified_findings ?? 0}
          icon={CheckCircle}
          accentColor="border-cyber-accent text-cyber-accent"
          glowColor="rgba(0, 255, 136, 0.15)"
          code="CONFIRMED_EXPLOITS"
        />
        <StatCard
          title="CRITICAL THREATS"
          value={analyticsError ? 'ERR' : analytics?.severity?.critical ?? 0}
          icon={Shield}
          accentColor="border-cyber-destructive text-cyber-destructive"
          glowColor="rgba(255, 51, 102, 0.15)"
          code="SEV_0_THREATS"
        />
        <StatCard
          title="TARGET ASSESSMENTS"
          value={analyticsError ? 'ERR' : analytics?.assessments ?? 0}
          icon={Target}
          accentColor="border-cyber-cyan text-cyber-cyan"
          glowColor="rgba(0, 212, 255, 0.15)"
          code="OP_ENGAGEMENTS"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="cyber-card p-6 relative">
          <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyber-accent" />
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">
                SEVERITY SPECTRUM
              </h2>
            </div>
            <span className="text-[10px] text-cyber-muted tracking-[0.2em] uppercase">DIST_PIE.EXE</span>
          </div>

          {severityData.length > 0 ? (
            <div>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="#0a0a0f"
                    strokeWidth={2}
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#12121a',
                      border: '1px solid #00ff88',
                      boxShadow: '0 0 10px rgba(0,255,136,0.3)',
                      color: '#ffffff',
                      fontFamily: 'monospace',
                      fontSize: '12px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-4 pt-4 border-t border-cyber-border/40">
                {severityData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2 text-xs">
                    <span
                      className="w-2.5 h-2.5 inline-block"
                      style={{ backgroundColor: item.color, boxShadow: `0 0 6px ${item.color}` }}
                    />
                    <span className="text-cyber-muted uppercase">{item.name}:</span>
                    <span className="font-bold text-white ml-auto">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[240px] text-cyber-muted text-xs text-center p-4">
              <Shield className="w-10 h-10 mb-2 opacity-30 text-cyber-accent" />
              <p className="uppercase tracking-widest">
                {analyticsError ? 'TELEMETRY UNAVAILABLE' : 'NO FINDINGS LOGGED ACROSS TARGETS'}
              </p>
            </div>
          )}
        </div>

        {/* Recent Operations */}
        <div className="cyber-card p-6 relative">
          <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-5">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyber-cyan" />
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">
                RECENT ENGAGEMENTS
              </h2>
            </div>
            <span className="text-[10px] text-cyber-muted tracking-[0.2em] uppercase">OPS_LOG.SYS</span>
          </div>

          {recentAssessments.length > 0 ? (
            <div className="space-y-3">
              {recentAssessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="flex items-center justify-between p-3.5 bg-cyber-void border border-cyber-border hover:border-cyber-accent/60 transition-all duration-150 group"
                >
                  <div className="min-w-0 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-cyber-accent text-xs font-bold">&gt;</span>
                      <p className="text-white font-semibold text-sm truncate uppercase tracking-wide group-hover:text-cyber-accent transition-colors">
                        {assessment.name}
                      </p>
                    </div>
                    <p className="text-xs text-cyber-muted truncate mt-0.5 font-mono">
                      {assessment.target_url || 'N/A'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={clsx(
                        'px-2.5 py-0.5 text-[11px] font-bold tracking-wider uppercase border',
                        assessment.status === 'completed' && 'bg-cyber-accent/10 border-cyber-accent text-cyber-accent shadow-[0_0_8px_rgba(0,255,136,0.3)]',
                        assessment.status === 'running' && 'bg-cyber-cyan/10 border-cyber-cyan text-cyber-cyan shadow-[0_0_8px_rgba(0,212,255,0.3)] animate-pulse',
                        assessment.status === 'pending' && 'bg-yellow-500/10 border-yellow-400 text-yellow-400'
                      )}
                    >
                      {assessment.status}
                    </span>
                    <span className="text-xs text-cyber-muted font-bold w-10 text-right">{assessment.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[240px] text-cyber-muted text-xs text-center p-4">
              <Target className="w-10 h-10 mb-2 opacity-30 text-cyber-cyan" />
              <p className="uppercase tracking-widest">NO ENGAGEMENTS RECORDED</p>
              <p className="text-[11px] text-cyber-muted/80 mt-1">&gt; INITIALIZE A NEW ASSESSMENT TARGET</p>
            </div>
          )}
        </div>
      </div>

      {/* History & Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="cyber-card p-6">
          <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-cyber-secondary" />
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">
                ENGAGEMENT ARCHIVES
              </h2>
            </div>
            <span className="text-[10px] text-cyber-muted uppercase tracking-[0.2em]">INDEX_HISTORY</span>
          </div>

          {recentAssessments.length > 0 ? (
            <div className="divide-y divide-cyber-border/40">
              {recentAssessments.map(item => (
                <div key={item.id} className="flex items-center justify-between py-3 text-xs">
                  <div>
                    <p className="text-white font-medium uppercase tracking-wide">
                      <span className="text-cyber-secondary font-bold mr-1.5">[{item.id}]</span>
                      {item.name}
                    </p>
                    <p className="text-[11px] text-cyber-muted mt-0.5">
                      {item.findings} FINDINGS // {item.verified} VERIFIED EXPLOITS
                    </p>
                  </div>
                  <span className="text-[11px] text-cyber-accent font-bold uppercase tracking-widest">
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-cyber-muted uppercase tracking-widest py-6 text-center">NO ARCHIVES RECORDED</p>
          )}
        </div>

        <div className="cyber-card p-6">
          <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyber-accent" />
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">
                SECURITY INTELLIGENCE
              </h2>
            </div>
            <span className="text-[10px] text-cyber-muted uppercase tracking-[0.2em]">LIVE_TELEMETRY</span>
          </div>

          <ul className="space-y-3.5 text-xs text-cyber-foreground/90">
            <li className="flex items-start gap-2.5 p-2.5 bg-cyber-void border border-cyber-border/60">
              <span className="text-cyber-secondary font-bold">&gt;&gt;</span>
              <div>
                <span className="font-bold text-white mr-1.5">OPEN VULNERABILITY BACKLOG:</span>
                <span className="text-cyber-secondary font-bold">{analytics?.open_findings ?? 0}</span> active findings awaiting mitigation.
              </div>
            </li>
            <li className="flex items-start gap-2.5 p-2.5 bg-cyber-void border border-cyber-border/60">
              <span className="text-cyber-accent font-bold">&gt;&gt;</span>
              <div>
                <span className="font-bold text-white mr-1.5">VALIDATED REMEDIATIONS:</span>
                <span className="text-cyber-accent font-bold">{analytics?.validated_remediations ?? 0}</span> patches verified clear.
              </div>
            </li>
            <li className="flex items-start gap-2.5 p-2.5 bg-cyber-void border border-cyber-border/60">
              <span className="text-cyber-cyan font-bold">&gt;&gt;</span>
              <div>
                <span className="font-bold text-white mr-1.5">SCANNER ENGINES ACTIVE:</span>
                <span className="text-cyber-cyan font-bold">{analytics?.scanner_checks_executed ?? 0}</span> diagnostic plugins registered.
              </div>
            </li>
          </ul>
        </div>
      </div>

      {/* Metric Categorization */}
      {!analyticsError && analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricList title="VERIFICATION MATRIX" values={analytics.verification} empty="No verification records." />
          <MetricList title="VULNERABILITY CLASSES" values={analytics.categories} empty="No categories logged." />
          <div className="cyber-card p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
                <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">REMEDIATION SCORE</h2>
                <span className="text-[10px] text-cyber-accent uppercase">AUDITED</span>
              </div>
              <p className="text-4xl font-black text-cyber-accent font-orbitron drop-shadow-[0_0_12px_rgba(0,255,136,0.4)]">
                {analytics.validated_remediations}
              </p>
              <p className="text-xs text-cyber-muted uppercase tracking-wider mt-1">VERIFIED REMEDIATED FINDINGS</p>
            </div>
            <div className="mt-4 pt-3 border-t border-cyber-border/40 text-[11px] text-cyber-muted">
              STATUS: AUDIT-COMPLIANT
            </div>
          </div>
        </div>
      )}

      {/* Trend & Scanner Coverage */}
      {!analyticsError && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="cyber-card p-6">
            <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">ENGAGEMENT TRENDS</h2>
              <span className="text-[10px] text-cyber-muted uppercase">HISTORICAL</span>
            </div>
            {trends?.available ? trends.items.map(item => (
              <div key={item.assessment_id} className="flex justify-between py-2 border-b border-cyber-border/40 last:border-0 text-xs">
                <span className="text-cyber-foreground uppercase">ASSESSMENT #{item.assessment_id}</span>
                <span className="text-cyber-secondary font-bold font-mono">{item.findings} FINDINGS</span>
              </div>
            )) : <p className="text-xs text-cyber-muted uppercase tracking-widest">{trends?.message || 'HISTORICAL TRENDS REQUIRE MULTIPLE ASSESSMENTS.'}</p>}
          </div>

          <div className="cyber-card p-6">
            <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
              <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">SCANNER COVERAGE</h2>
              <span className="text-[10px] text-cyber-cyan uppercase">DIAGNOSTICS</span>
            </div>
            {scannerCoverage?.available ? scannerCoverage.items.map(item => (
              <div key={item.scanner} className="flex justify-between py-2 border-b border-cyber-border/40 last:border-0 text-xs">
                <span className="text-cyber-foreground uppercase font-semibold">{item.scanner}</span>
                <span className="text-cyber-cyan font-mono font-bold">
                  {item.completed ? 'COMPLETED' : item.unavailable ? 'UNAVAILABLE' : item.failed ? 'FAILED' : 'STANDBY'} | {item.findings} FINDINGS
                </span>
              </div>
            )) : <p className="text-xs text-cyber-muted uppercase tracking-widest">{scannerCoverage?.message || 'SCANNER COVERAGE TELEMETRY UNAVAILABLE.'}</p>}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon: Icon, accentColor, glowColor, code }) {
  return (
    <div
      className={clsx(
        'cyber-card p-5 relative group transition-all duration-200 hover:-translate-y-0.5',
        accentColor.split(' ')[0]
      )}
      style={{ boxShadow: `0 0 15px ${glowColor}` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <span className="text-[10px] text-cyber-muted tracking-[0.2em] uppercase font-mono block">
            {code}
          </span>
          <p className="text-3xl font-black font-orbitron text-white mt-1.5 tracking-tight">
            {value}
          </p>
          <p className="text-xs text-cyber-muted uppercase tracking-wider mt-1 font-mono">
            {title}
          </p>
        </div>
        <div className={clsx('p-2.5 border bg-cyber-void/80', accentColor)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}

function MetricList({ title, values, empty }) {
  const entries = Object.entries(values || {})
  return (
    <div className="cyber-card p-6">
      <div className="flex items-center justify-between border-b border-cyber-border/60 pb-3 mb-4">
        <h2 className="text-sm font-bold uppercase tracking-widest font-orbitron text-white">{title}</h2>
        <span className="text-[10px] text-cyber-muted uppercase">BREAKDOWN</span>
      </div>
      {entries.length ? (
        <div className="space-y-2">
          {entries.map(([name, value]) => (
            <div key={name} className="flex justify-between items-center py-1.5 border-b border-cyber-border/30 last:border-0 text-xs">
              <span className="text-cyber-muted uppercase tracking-wider">{name.replaceAll('_', ' ')}</span>
              <span className="text-cyber-accent font-bold font-mono">{value}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-cyber-muted uppercase tracking-widest">{empty}</p>
      )}
    </div>
  )
}
