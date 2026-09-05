import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { useLearningController } from './hooks/useLearningController'
import './styles.css'

import { Shell } from './components/layout/Shell'
import { Onboarding } from './pages/Onboarding'
import { Dashboard } from './pages/Dashboard'
import { StudyPlan } from './pages/StudyPlan'
import { FocusMode } from './pages/FocusMode'
import { Completion } from './pages/Completion'
import { StudyBuddy } from './pages/StudyBuddy'
import { Insights } from './pages/Insights'

function App() {
  const [page, setPage] = useState('dashboard')
  const learning = useLearningController() as any

  if (learning.studentId === null && !learning.loading && !learning.error) {
    return <Onboarding login={learning.login} />
  }

  const goSession = () => setPage('session')
  const goDashboard = () => setPage('dashboard')

  return (
    <Shell
      page={page}
      setPage={setPage}
      hideSidebar={page === 'session' || page === 'completion' || page === 'buddy'}
      error={learning.error}
      loading={learning.loading}
      fallbackToLocal={learning.fallbackToLocal}
      fontScale={learning.profile?.fontScale}
      reducedMotion={learning.profile?.reducedMotion}
    >
      {page === 'dashboard' && (
        <Dashboard
          profile={learning.profile}
          recommendation={learning.recommendation}
          history={learning.history}
          onStart={goSession}
          onOpenBuddy={() => {
            learning.recordHelp()
            setPage('buddy')
          }}
        />
      )}
      
      {page === 'plan' && (
        <StudyPlan
          profile={learning.profile}
          recommendation={learning.recommendation}
          onStart={goSession}
        />
      )}
      
      {page === 'session' && (
        <FocusMode
          profile={learning.profile}
          recommendation={learning.recommendation}
          onOpenBuddy={() => {
            learning.recordHelp()
            setPage('buddy')
          }}
          onFinish={() => setPage('completion')}
        />
      )}
      
      {page === 'completion' && (
        <Completion
          onSubmit={(feeling, outcome, duration) => {
            learning.submitOutcome(feeling, outcome, duration)
            setPage('dashboard')
          }}
        />
      )}
      
      {page === 'buddy' && (
        <StudyBuddy
          profile={learning.profile}
          currentActivity={learning.recommendation?.activity}
          onStart={goDashboard}
        />
      )}
      
      {page === 'insights' && (
        <Insights
          profile={learning.profile}
          history={learning.history}
        />
      )}
      
      {page === 'profile' && (
        <div style={{ padding: '40px' }}>
          <h2>Settings</h2>
          <p>Current Profile: {learning.profile?.name}</p>
          <button className="btn-secondary" onClick={() => {
            localStorage.clear()
            window.location.reload()
          }}>
            Log Out / Reset
          </button>
        </div>
      )}
    </Shell>
  )
}

const root = createRoot(document.getElementById('root')!)
root.render(<App />)
