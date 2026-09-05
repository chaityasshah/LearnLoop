import React, { useState } from 'react'
import { Card, Button } from '../components/ui'
import type { LearningProfile, Recommendation } from '../types'

export function FocusMode({
  profile,
  recommendation,
  onOpenBuddy,
  onFinish
}: {
  profile: LearningProfile,
  recommendation: Recommendation,
  onOpenBuddy: () => void,
  onFinish: () => void
}) {
  const [step, setStep] = useState(0)
  const act = recommendation.activity
  const simple = profile.simpleLanguage

  const steps = [
    { title: 'Learn', content: simple ? act.explanation.split('.')[0] + '.' : act.explanation },
    { title: 'Example', content: act.example },
    { title: 'Practice', content: act.question }
  ]

  const current = steps[step]

  return (
    <div className="focus-container">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
            {Math.round(((step + 1) / steps.length) * 100)}%
          </div>
          <div>
            <h2 style={{ fontSize: '18px' }}>{act.topic}</h2>
            <p style={{ margin: 0, fontSize: '12px' }}>{act.title}</p>
          </div>
        </div>
        <Button variant="ghost" onClick={onFinish}>Exit Session ✕</Button>
      </div>

      <Card className="ai-elevated p-8 mb-8" style={{ minHeight: '400px' }}>
        <h1 className="mb-6">{current.title}</h1>
        
        <div style={{ fontSize: profile.fontScale === 'Large' ? '20px' : '16px', lineHeight: '1.8' }}>
          {current.content.split('\n').map((para, i) => (
            <p key={i} className="mb-4">{para}</p>
          ))}
        </div>

        {step === 2 && (
          <div className="mt-8 p-6" style={{ background: 'rgba(79, 70, 229, 0.05)', borderRadius: '12px', border: '1px solid rgba(79, 70, 229, 0.1)' }}>
            <h3 className="mb-2" style={{ color: 'var(--primary)' }}>Answer</h3>
            <p style={{ margin: 0 }}>{act.answer}</p>
          </div>
        )}
      </Card>

      <div className="flex justify-between items-center">
        <Button variant="secondary" onClick={onOpenBuddy} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <i>🤖</i> Ask Study Buddy
        </Button>
        
        <div className="flex gap-4">
          {step > 0 && <Button variant="ghost" onClick={() => setStep(s => s - 1)}>← Back</Button>}
          {step < steps.length - 1 ? (
            <Button variant="primary" onClick={() => setStep(s => s + 1)}>Continue →</Button>
          ) : (
            <Button variant="primary" onClick={onFinish}>Complete Session ✓</Button>
          )}
        </div>
      </div>
    </div>
  )
}
