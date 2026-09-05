import React, { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

export function Shell({
  page,
  setPage,
  children,
  hideSidebar = false,
  error,
  loading,
  fallbackToLocal,
  fontScale,
  reducedMotion
}: {
  page: string,
  setPage: (p: string) => void,
  children: ReactNode,
  hideSidebar?: boolean,
  error?: boolean,
  loading?: boolean,
  fallbackToLocal?: () => void,
  fontScale?: 'Standard' | 'Large',
  reducedMotion?: boolean
}) {
  return (
    <div className={`app ${reducedMotion ? 'no-motion' : ''}`} style={{ fontSize: fontScale === 'Large' ? '17px' : '16px' }}>
      {error && (
        <div style={{ background: '#f8d7da', color: '#721c24', padding: '10px', textAlign: 'center', position: 'fixed', top: 0, width: '100%', zIndex: 50 }}>
          Backend unavailable. 
          <button onClick={fallbackToLocal} style={{ marginLeft: '10px', textDecoration: 'underline' }}>Fallback to Local Mode</button>
        </div>
      )}
      {loading && (
        <div style={{ background: '#e2e3e5', color: '#383d41', padding: '10px', textAlign: 'center', position: 'fixed', top: error ? '40px' : 0, width: '100%', zIndex: 50 }}>
          Loading learning state from backend...
        </div>
      )}

      {!hideSidebar && <Sidebar page={page} setPage={setPage} />}
      
      <main style={{ marginLeft: hideSidebar ? 0 : '260px', width: hideSidebar ? '100%' : 'calc(100% - 260px)' }}>
        {children}
      </main>
    </div>
  )
}
