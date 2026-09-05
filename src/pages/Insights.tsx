import React from 'react'
import { Card, Tag } from '../components/ui'
import type { LearningProfile, ActivityRecord } from '../types'

export function Insights({
  profile,
  history
}: {
  profile: LearningProfile,
  history: ActivityRecord[]
}) {
  const completeCount = history.filter(x => x.outcome === 'completed').length
  const total = history.length

  const completionRate = total > 0 ? Math.round((completeCount / total) * 100) : 0
  const recentTopics = Array.from(new Set(history.slice(-5).map(h => h.topic)))

  return (
    <div>
      <header>
        <div>
          <p className="eyebrow">YOUR LEARNING PROGRESS & INSIGHTS</p>
          <h1>Learning Insights</h1>
        </div>
      </header>

      {total === 0 ? (
        <Card className="text-center p-8" style={{ marginTop: '40px' }}>
          <i style={{ fontSize: '48px', display: 'block', marginBottom: '16px' }}>🌱</i>
          <h3>Your journey is just beginning</h3>
          <p>Complete a few learning sessions to start generating insights.</p>
        </Card>
      ) : (
        <div className="dashboard-grid">
          <div>
            <Card className="mb-6">
              <h3 className="mb-4">Activity Overview</h3>
              <div className="flex gap-4 mb-4">
                <div style={{ flex: 1, padding: '16px', background: 'var(--bg-base)', borderRadius: '12px' }}>
                  <p className="eyebrow">Sessions Completed</p>
                  <h2 style={{ fontSize: '32px' }}>{completeCount}</h2>
                </div>
                <div style={{ flex: 1, padding: '16px', background: 'var(--bg-base)', borderRadius: '12px' }}>
                  <p className="eyebrow">Completion Rate</p>
                  <h2 style={{ fontSize: '32px', color: completionRate > 75 ? 'var(--tertiary)' : 'inherit' }}>{completionRate}%</h2>
                </div>
              </div>

              <div className="mt-8">
                <h4 className="mb-4">Recent Topics</h4>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  {recentTopics.map(t => (
                    <Tag key={t}>{t}</Tag>
                  ))}
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="mb-4">Recent History</h3>
              <div style={{ display: 'grid', gap: '12px' }}>
                {history.slice(-5).reverse().map((h, i) => (
                  <div key={i} className="flex justify-between items-center" style={{ padding: '12px', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}>
                    <div>
                      <div style={{ fontWeight: '600' }}>{h.topic}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{new Date(h.timestamp).toLocaleDateString()}</div>
                    </div>
                    <Tag tone={h.outcome === 'completed' ? 'mint' : 'amber'}>{h.outcome}</Tag>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <div>
            <Card className="mb-6 ai-elevated">
              <h3 className="mb-4" style={{ color: 'var(--secondary)' }}>AI Observations</h3>
              <p style={{ fontSize: '14px' }}>Based on your recent activity, the engine has noted:</p>
              
              <ul style={{ fontSize: '14px', paddingLeft: '20px' }}>
                <li>Your preferred format is <b>{profile.preferredFormat}</b></li>
                <li>Your average successful session is around <b>{profile.typicalSuccessfulMinutes} minutes</b></li>
                {profile.repeatedMistakes.length > 0 && (
                  <li>You requested extra help with: {profile.repeatedMistakes.join(', ')}</li>
                )}
                {profile.longActivityAbandoned && (
                  <li>You tend to skip longer sessions, so recommendations are being shortened.</li>
                )}
              </ul>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
