import { useState } from 'react'
import Sidebar from './components/sidebar/Sidebar.jsx'
import ChatWindow from './components/chat/ChatWindow.jsx'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [chatKey, setChatKey] = useState(0)

  function handleNewChat() {
    setSessionId(null)
    setChatKey((k) => k + 1)
  }

  function handleSelectSession(id) {
    setSessionId(id)
    setChatKey((k) => k + 1)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      <Sidebar sessionId={sessionId} onNewChat={handleNewChat} onSelectSession={handleSelectSession} />
      <main className="flex-1 overflow-hidden">
        <ChatWindow key={chatKey} sessionId={sessionId} onSessionChange={setSessionId} />
      </main>
    </div>
  )
}
