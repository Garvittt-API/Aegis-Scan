import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import Targets from './pages/Targets'
import Assessments from './pages/Assessments'
import NewAssessment from './pages/NewAssessment'
import AssessmentDetail from './pages/AssessmentDetail'
import ScanJobs from './pages/ScanJobs'
import Findings from './pages/Findings'
import AttackSurface from './pages/AttackSurface'
import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/assessments" element={<Assessments />} />
          <Route path="/assessments/new" element={<NewAssessment />} />
          <Route path="/assessments/:id" element={<AssessmentDetail />} />
          <Route path="/assessments/:id/attack-surface" element={<AttackSurface />} />
          <Route path="/assessments/:id/scan-jobs" element={<ScanJobs />} />
          <Route path="/scan-jobs" element={<ScanJobs />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/attack-surface" element={<AttackSurface />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
