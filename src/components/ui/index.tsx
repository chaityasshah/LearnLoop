import React from 'react'

export function Card({ children, className = '', ...props }: any) {
  return (
    <div className={`card ${className}`} {...props}>
      {children}
    </div>
  )
}

export function Button({ children, variant = 'primary', className = '', ...props }: any) {
  return (
    <button className={`btn-${variant} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Tag({ children, tone = 'default', className = '' }: any) {
  const toneClass = tone !== 'default' ? tone : ''
  return (
    <span className={`tag ${toneClass} ${className}`}>
      {children}
    </span>
  )
}

export function ProgressBar({ percent, tone = 'primary' }: { percent: number, tone?: string }) {
  return (
    <div className="progress-track">
      <div 
        className="progress-fill" 
        style={{ width: `${Math.min(100, Math.max(0, percent))}%`, background: tone === 'tertiary' ? 'var(--tertiary)' : 'var(--primary)' }}
      />
    </div>
  )
}
