import { useState } from 'react'
import ChatWindow from './chat/ChatWindow.jsx'

export default function FloatingChat({ onMinimize }) {
  const [sessionId, setSessionId] = useState(null)
  const [chatKey, setChatKey]     = useState(0)

  function handleNewChat() {
    setSessionId(null)
    setChatKey(k => k + 1)
  }

  return (
    <div className="floating-chat">
      <ChatWindow
        key={chatKey}
        sessionId={sessionId}
        onSessionChange={setSessionId}
        onMinimize={onMinimize}
        onNewChat={handleNewChat}
      />
    </div>
  )
}
