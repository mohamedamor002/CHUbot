import { useState, useEffect } from 'react'
import Avatar from './components/Avatar.jsx'
import FloatingChat from './components/FloatingChat.jsx'
import { checkHealth } from './api/client.js'

const AVATAR_SIZE = { w: 80,  h: 80  }
const CHAT_SIZE   = { w: 380, h: 620 }

async function resizeWindow(w, h) {
  try {
    const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
    const win = WebviewWindow.getCurrent()
    const { LogicalSize } = await import('@tauri-apps/api/dpi')
    await win.setSize(new LogicalSize(w, h))
  } catch (err) {
    console.error('[resizeWindow] erreur:', err)
  }
}

export default function App() {
  const [isOpen, setIsOpen] = useState(false)
  const [backendReady, setBackendReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function poll() {
      while (!cancelled) {
        try {
          await checkHealth()
          if (!cancelled) setBackendReady(true)
          return
        } catch {}
        await new Promise(r => setTimeout(r, 2000))
      }
    }
    poll()
    return () => { cancelled = true }
  }, [])

  async function handleOpen() {
    if (!backendReady) return
    await resizeWindow(CHAT_SIZE.w, CHAT_SIZE.h)
    setIsOpen(true)
  }

  async function handleMinimize() {
    setIsOpen(false)
    await resizeWindow(AVATAR_SIZE.w, AVATAR_SIZE.h)
  }

  return (
    <div className="app-root">
      {isOpen
        ? <FloatingChat onMinimize={handleMinimize} />
        : <Avatar onClick={handleOpen} connecting={!backendReady} />
      }
    </div>
  )
}
