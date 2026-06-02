import { useState } from 'react'
import ChatWindow from './chat/ChatWindow.jsx'

export default function FloatingChat({ onMinimize }) {
  const [sessionId, setSessionId] = useState(null)
  const [chatKey, setChatKey] = useState(0)

  function handleNewChat() {
    setSessionId(null)
    setChatKey((k) => k + 1)
  }

  return (
    <div className="floating-chat">
      <ChatWindow
        key={chatKey}
        sessionId={sessionId}
        onSessionChange={setSessionId}
        onMinimize={onMinimize}
      />
      <div className="px-3 py-2 border-t border-slate-200 bg-white rounded-b-xl flex items-center justify-between flex-shrink-0">
        <button
          onClick={handleNewChat}
          className="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          Nouvelle conversation
        </button>
        <span className="text-[10px] text-slate-300 select-none">CHUbot v1.0</span>
      </div>
    </div>
  )
}
