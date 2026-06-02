import { useState, useEffect } from 'react'

async function getWindow() {
  const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
  return WebviewWindow.getCurrent()
}

export default function WindowControls({ onMinimize }) {
  const [isMaximized, setIsMaximized] = useState(false)

  useEffect(() => {
    getWindow().then(async (win) => {
      setIsMaximized(await win.isMaximized())
      win.onResized(() => win.isMaximized().then(setIsMaximized))
    }).catch(() => {})
  }, [])

  async function handleMinimizeTaskbar(e) {
    e.stopPropagation()
    const win = await getWindow()
    await win.minimize()
  }

  async function handleMaximize(e) {
    e.stopPropagation()
    const win = await getWindow()
    await win.toggleMaximize()
  }

  async function handleClose(e) {
    e.stopPropagation()
    const win = await getWindow()
    await win.close()
  }

  const btnBase = "w-8 h-7 flex items-center justify-center transition-colors"

  return (
    <div style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>

      {/* Retour avatar */}
      {onMinimize && (
        <button
          onClick={(e) => { e.stopPropagation(); onMinimize() }}
          className={`${btnBase} text-white/70 hover:text-white hover:bg-white/20 rounded`}
          title="Réduire en avatar"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="10" y="3" width="4" height="18" rx="1"/>
            <rect x="3" y="10" width="18" height="4" rx="1"/>
          </svg>
        </button>
      )}

      <div style={{ width: '8px' }} />

      {/* Minimiser barre des tâches */}
      <button
        onClick={handleMinimizeTaskbar}
        className={`${btnBase} text-slate-600 hover:bg-slate-300/60`}
        title="Réduire"
      >
        <svg width="11" height="11" viewBox="0 0 11 2" fill="currentColor">
          <rect width="11" height="2" rx="1"/>
        </svg>
      </button>

      {/* Maximiser / Restaurer */}
      <button
        onClick={handleMaximize}
        className={`${btnBase} text-slate-600 hover:bg-slate-300/60`}
        title={isMaximized ? 'Restaurer' : 'Agrandir'}
      >
        {isMaximized ? (
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="2.5" y="0.5" width="8" height="8" rx="0.5"/>
            <path d="M0.5 2.5v8h8"/>
          </svg>
        ) : (
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="0.5" y="0.5" width="10" height="10" rx="0.5"/>
          </svg>
        )}
      </button>

      {/* Fermer */}
      <button
        onClick={handleClose}
        className={`${btnBase} text-slate-600 hover:bg-red-500 hover:text-white`}
        title="Fermer"
      >
        <svg width="11" height="11" viewBox="0 0 11 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          <line x1="1" y1="1" x2="10" y2="10"/>
          <line x1="10" y1="1" x2="1" y2="10"/>
        </svg>
      </button>

    </div>
  )
}
