import React, { useState } from 'react'
import { Card, Button, Tag, ProgressBar } from '../components/ui'
import type { LearningProfile, Recommendation, ActivityRecord } from '../types'

function toneForFlags(flags: string[]) {
  if (flags.some((f) => f.includes('↓') || f.includes('REDUCED') || f.includes('REVISION'))) return 'coral'
  if (flags.some((f) => f.includes('↑') || f.includes('STRETCH') || f.includes('DEEP'))) return 'amber'
  return 'mint'
}

export function Dashboard({
  profile,
  recommendation,
  onStart,
  history,
  onOpenBuddy
}: {
  profile: LearningProfile,
  recommendation: Recommendation,
  onStart: () => void,
  history: ActivityRecord[],
  onOpenBuddy: () => void
}) {
  const [showWhy, setShowWhy] = useState(true)
  const complete = history.filter((x) => x.outcome === 'completed').length
  const struggles = history.filter((x) => x.outcome !== 'completed' || x.feeling === 'difficult').length
  
  const r = recommendation
  const flags = (r?.flags as string[]) || []
  const bullets = (r?.bullets as string[]) || []
  const isAdapted = flags.some((f) => f.includes('↓') || f.includes('REDUCED'))

  return (
    <div>
      <header>
        <div>
          <p className="eyebrow">{new Date().toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase()} · A LEARNING DAY FOR YOU</p>
          <h1>Hello, {profile.name} 👋</h1>
        </div>
        <Button variant="secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <i>⚙️</i> {profile.preferredFormat} learning
        </Button>
      </header>

      <div className="stats-grid">
        <Card>
          <div className="flex justify-between items-center mb-2">
            <span className="eyebrow" style={{ margin: 0 }}>Available Time</span>
            <i style={{ color: 'var(--text-tertiary)' }}>⏱️</i>
          </div>
          <h2 style={{ fontSize: '28px' }}>{profile.availableMinutes} min</h2>
          <p style={{ fontSize: '12px', marginTop: '4px', marginBottom: 0 }}>Based on your schedule</p>
        </Card>
        
        <Card>
          <div className="flex justify-between items-center mb-2">
            <span className="eyebrow" style={{ margin: 0 }}>Today's Goal</span>
            <i style={{ color: 'var(--tertiary)' }}>🎯</i>
          </div>
          <h2 style={{ fontSize: '28px' }}>{profile.completedToday} / {profile.goalToday || 3}</h2>
          <ProgressBar percent={((profile.completedToday) / (profile.goalToday || 3)) * 100} tone="tertiary" />
        </Card>
        
        <Card className="ai-elevated" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', background: 'rgba(139, 92, 246, 0.05)', borderColor: 'rgba(139, 92, 246, 0.2)' }}>
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 style={{ fontSize: '16px', color: 'var(--secondary)' }}>Study Buddy</h3>
              <p style={{ fontSize: '12px', margin: 0 }}>Your AI learning companion</p>
            </div>
            <i style={{ fontSize: '24px' }}>🤖</i>
          </div>
          <Button variant="primary" style={{ width: '100%', background: 'var(--secondary)' }} onClick={onOpenBuddy}>
            Ask a question
          </Button>
        </Card>
      </div>

      <h3 className="mb-4">Up Next for You</h3>
      
      {r ? (
        <Card className="rec-card">
          <div className="rec-content">
            <div className="flex items-center gap-2 mb-2">
              <Tag tone="lilac">AI RECOMMENDED</Tag>
              {flags.map((f) => (
                <Tag key={f} tone={toneForFlags([f])}>{f}</Tag>
              ))}
            </div>
            
            <h2 className="mb-2">{r.activity.topic}: {r.activity.title}</h2>
            <p>{r.activity.subject} · {r.kind}</p>
            
            <div className="rec-meta">
              <Tag>⏱️ {r.duration} min</Tag>
              <Tag>📚 {r.format}</Tag>
              <Tag tone={r.difficulty === 'Easy' ? 'mint' : r.difficulty === 'Challenging' ? 'coral' : 'blue'}>
                {r.difficulty}
              </Tag>
              {r.breakMinutes > 0 && <Tag tone="amber">{r.breakMinutes} min break after</Tag>}
              {r.supportNeeded && <Tag tone="lilac">Study Buddy ready</Tag>}
            </div>

            {showWhy && bullets.length > 0 && (
              <div className="rec-why">
                <b>Why this was recommended</b>
                <ul>
                  {bullets.slice(0, 5).map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <div className="flex" style={{ flexDirection: 'column', gap: '12px', minWidth: '160px', justifyContent: 'center' }}>
            <Button variant="primary" onClick={onStart}>
              Start learning →
            </Button>
            <Button variant="ghost" onClick={() => setShowWhy(!showWhy)}>
              {showWhy ? 'Hide reasoning ⌃' : 'Why? ⌄'}
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <p className="text-center" style={{ margin: '32px 0' }}>No recommendations right now.</p>
        </Card>
      )}
    </div>
  )
}
