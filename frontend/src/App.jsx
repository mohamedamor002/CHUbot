import { useState } from 'react'
import Sidebar from './components/sidebar/Sidebar.jsx'
import ChatWindow from './components/chat/ChatWindow.jsx'

export default function App() {
  const [sessionId, setSessionId] = useState(null)

  function handleNewChat() {
    setSessionId(null)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      <Sidebar sessionId={sessionId} onNewChat={handleNewChat} />
      <main className="flex-1 overflow-hidden">
        <ChatWindow sessionId={sessionId} onSessionChange={setSessionId} />
      </main>
    </div>
  )
}
