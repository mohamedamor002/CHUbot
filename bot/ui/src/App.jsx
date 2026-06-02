import { useState } from 'react'
import Avatar from './components/Avatar.jsx'
import FloatingChat from './components/FloatingChat.jsx'

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

  async function handleOpen() {
    await resizeWindow(CHAT_SIZE.w, CHAT_SIZE.h) // redimensionne AVANT d'afficher
    setIsOpen(true)
  }

  async function handleMinimize() {
    setIsOpen(false)                               // cache le chat AVANT de réduire
    await resizeWindow(AVATAR_SIZE.w, AVATAR_SIZE.h)
  }

  return (
    <div className="app-root">
      {isOpen
        ? <FloatingChat onMinimize={handleMinimize} />
        : <Avatar onClick={handleOpen} />
      }
    </div>
  )
}
