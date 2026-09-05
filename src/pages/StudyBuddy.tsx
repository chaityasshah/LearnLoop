import React, { useState, useEffect, useRef } from 'react'
import { Card, Button } from '../components/ui'
import type { LearningProfile, LearningActivity } from '../types'

interface Message {
  role: 'student' | 'bot'
  text: string
}

export function StudyBuddy({
  profile,
  currentActivity,
  onStart
}: {
  profile: LearningProfile,
  currentActivity?: LearningActivity,
  onStart: () => void
}) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: `Hi ${profile.name}! I'm your Study Buddy. How can I help you with ${currentActivity?.topic || 'your studies'} today?` }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  async function send() {
    if (!input.trim()) return
    const userMsg = input
    setMessages(prev => [...prev, { role: 'student', text: userMsg }])
    setInput('')
    setLoading(true)

    try {
      const endpoint = window.location.hostname === 'localhost' ? 'http://localhost:8000' : ''
      const res = await fetch(`${endpoint}/api/study-buddy/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          studentId: 'pilot-student-123',
          question: userMsg,
          contextActivityId: currentActivity?.id
        })
      })

      if (!res.ok) throw new Error('API failed')
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'bot', text: data.answer || "I'm sorry, I couldn't process that right now." }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', text: "I'm having trouble connecting right now. Please try again later." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="focus-container">
      <header>
        <div>
          <p className="eyebrow">AI LEARNING COMPANION</p>
          <h1>Study Buddy</h1>
        </div>
      </header>

      <Card className="flex flex-col mb-4" style={{ height: '600px' }}>
        {currentActivity && (
          <div className="mb-4 pb-4" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <p className="eyebrow">CURRENT CONTEXT</p>
            <h3 style={{ fontSize: '16px' }}>{currentActivity.topic}</h3>
          </div>
        )}

        <div className="buddy-chat flex-1" style={{ overflowY: 'auto', paddingRight: '10px' }} ref={chatRef}>
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              {m.text}
            </div>
          ))}
          {loading && (
            <div className="bubble bot" style={{ opacity: 0.7 }}>
              Thinking...
            </div>
          )}
        </div>

        <div className="flex gap-2" style={{ marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <input 
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Type your question..."
            style={{ flex: 1 }}
          />
          <Button variant="primary" onClick={send} disabled={loading || !input.trim()}>
            Send ↗
          </Button>
        </div>
      </Card>
      
      <div className="text-center">
        <Button variant="ghost" onClick={onStart}>Back to Dashboard</Button>
      </div>
    </div>
  )
}
