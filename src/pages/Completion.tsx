import React, { useState } from 'react'
import { Card, Button } from '../components/ui'
import type { Feeling, Outcome } from '../types'

export function Completion({
  onSubmit
}: {
  onSubmit: (f: Feeling, o: Outcome, m: number) => void
}) {
  const [feeling, setFeeling] = useState<Feeling | null>(null)
  const [outcome, setOutcome] = useState<Outcome | null>(null)
  const [mins, setMins] = useState('10')

  return (
    <div className="flex items-center justify-center" style={{ minHeight: '80vh' }}>
      <Card className="ai-elevated p-8 text-center" style={{ maxWidth: '600px', width: '100%' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎉</div>
        <h2 className="mb-2">Session Complete</h2>
        <p className="mb-8">Great job focusing! Let the engine know how that went so it can adapt your next session.</p>

        <div className="mb-6 text-left">
          <label className="eyebrow" style={{ display: 'block', marginBottom: '12px' }}>How did it feel?</label>
          <div className="flex gap-4">
            {(['easy', 'manageable', 'difficult'] as Feeling[]).map(f => (
              <Button 
                key={f}
                variant={feeling === f ? 'primary' : 'secondary'}
                onClick={() => setFeeling(f)}
                className="flex-1"
                style={{ textTransform: 'capitalize' }}
              >
                {f}
              </Button>
            ))}
          </div>
        </div>

        <div className="mb-6 text-left">
          <label className="eyebrow" style={{ display: 'block', marginBottom: '12px' }}>How much did you complete?</label>
          <div className="flex gap-4">
            {(['skipped', 'partial', 'completed'] as Outcome[]).map(o => (
              <Button 
                key={o}
                variant={outcome === o ? 'primary' : 'secondary'}
                onClick={() => setOutcome(o)}
                className="flex-1"
                style={{ textTransform: 'capitalize' }}
              >
                {o}
              </Button>
            ))}
          </div>
        </div>

        <div className="mb-8 text-left">
          <label className="eyebrow" style={{ display: 'block', marginBottom: '12px' }}>Actual time spent (minutes)</label>
          <input 
            type="number" 
            value={mins} 
            onChange={e => setMins(e.target.value)}
            style={{ width: '100px', padding: '10px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}
          />
        </div>

        <Button 
          variant="primary" 
          onClick={() => { if(feeling && outcome) onSubmit(feeling, outcome, parseInt(mins) || 10) }}
          disabled={!feeling || !outcome}
          className="w-full"
          style={{ width: '100%' }}
        >
          Update My Plan →
        </Button>
      </Card>
    </div>
  )
}
