import React from 'react'
import { Card, Tag } from '../components/ui'
import type { LearningProfile, Recommendation, ActivityRecord } from '../types'

export function StudyPlan({
  profile,
  recommendation,
  onStart
}: {
  profile: LearningProfile,
  recommendation: Recommendation,
  onStart: () => void
}) {
  return (
    <div>
      <header>
        <div>
          <p className="eyebrow">PERSONALIZED STUDY PLAN</p>
          <h1>Your flexible plan</h1>
        </div>
      </header>

      <div className="mb-8" style={{ maxWidth: '800px' }}>
        <p>This plan adapts in real-time based on your progress and available time. Each activity is carefully selected by the adaptive engine to maximize your retention and understanding.</p>
      </div>

      <div style={{ maxWidth: '800px' }}>
        {recommendation ? (
          <div className="flex gap-4" style={{ alignItems: 'stretch' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '40px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                1
              </div>
              <div style={{ width: '2px', flex: 1, background: 'var(--border-subtle)', margin: '8px 0' }}></div>
            </div>
            
            <Card className="flex-1 mb-6 ai-elevated">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="mb-1">{recommendation.activity.topic}: {recommendation.activity.title}</h3>
                  <p className="mb-0 text-sm">{recommendation.activity.subject} · {recommendation.kind}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: '600', fontSize: '18px' }}>{recommendation.duration}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>mins</div>
                </div>
              </div>
              
              <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                <p style={{ fontSize: '14px', marginBottom: 0 }}>
                  <b>AI Insight:</b> {recommendation.bullets?.[0] || 'Recommended to strengthen your foundation.'}
                </p>
              </div>
            </Card>
          </div>
        ) : null}

        {profile.revisionTopics && profile.revisionTopics.length > 0 && (
          <div className="flex gap-4">
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '40px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--bg-card)', border: '2px solid var(--border-subtle)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                2
              </div>
            </div>
            
            <Card className="flex-1 mb-6" style={{ opacity: 0.7 }}>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <Tag tone="amber" className="mb-2">UPCOMING REVISION</Tag>
                  <h3 className="mb-1">{profile.revisionTopics[0]}</h3>
                  <p className="mb-0 text-sm">Scheduled based on spaced repetition</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
