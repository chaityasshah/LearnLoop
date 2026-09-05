import React from 'react'

export function Sidebar({ page, setPage }: { page: string, setPage: (p: string) => void }) {
  return (
    <aside>
      <div className="logo">
        <span className="icon">◈</span> <span>LearnLoop</span>
      </div>
      <nav>
        <button className={page === 'dashboard' ? 'active' : ''} onClick={() => setPage('dashboard')}>
          <i>⌂</i> <span>Dashboard</span>
        </button>
        <button className={page === 'plan' ? 'active' : ''} onClick={() => setPage('plan')}>
          <i>📅</i> <span>Study Plan</span>
        </button>
        <button className={page === 'insights' ? 'active' : ''} onClick={() => setPage('insights')}>
          <i>📈</i> <span>Progress & Insights</span>
        </button>
        <button className={page === 'buddy' ? 'active' : ''} onClick={() => setPage('buddy')}>
          <i>🤖</i> <span>Study Buddy</span>
        </button>
      </nav>
      
      <div style={{ marginTop: 'auto' }}>
        <button className="btn-ghost" style={{ width: '100%', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '12px' }} onClick={() => setPage('profile')}>
          <i>⚙️</i> <span>Settings</span>
        </button>
      </div>
    </aside>
  )
}
