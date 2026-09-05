import React, { useState } from 'react'
import { Card, Button } from '../components/ui'

export function Onboarding({ login }: { login: (name: string, email: string) => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  
  return (
    <div className="flex items-center justify-center" style={{ minHeight: '100vh', padding: '24px' }}>
      <div className="onboarding-wrap">
        <div className="logo text-center mb-8" style={{ justifyContent: 'center' }}>
          <span className="icon">◈</span> <span>LearnLoop</span>
        </div>
        <Card className="ai-elevated p-8">
          <h2 className="text-center mb-2">Welcome to LearnLoop</h2>
          <p className="text-center mb-8" style={{ fontSize: '14px' }}>Please enter your details to get started on your adaptive learning journey.</p>
          
          <div className="mb-4">
            <label className="eyebrow" style={{ display: 'block', color: 'var(--text-secondary)' }}>Full Name</label>
            <input 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              placeholder="e.g. Aarav Sharma" 
            />
          </div>
          
          <div className="mb-8">
            <label className="eyebrow" style={{ display: 'block', color: 'var(--text-secondary)' }}>Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              placeholder="aarav@example.com" 
            />
          </div>
          
          <Button 
            className="w-full" 
            style={{ width: '100%', padding: '14px' }} 
            onClick={() => { if(name && email) login(name, email) }} 
            disabled={!name || !email}
          >
            Start Learning
          </Button>
        </Card>
      </div>
    </div>
  )
}
