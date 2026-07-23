import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ChatInput from './ChatInput.jsx'
import { sendMessageStream, getSession } from '../../api/client.js'
import logo from '../../assets/chulogo.png'

export default function ChatWindow({ sessionId, onSessionChange, onMinimize, onNewChat }) {
  const [messages, setMessages]   = useState([])
  const [loading, setLoading]     = useState(false)
  const [pinned, setPinned]       = useState(false)
  const bottomRef                 = useRef(null)
  const skipNextLoad              = useRef(false)
  const winRef                    = useRef(null)

  useEffect(() => {
    import('@tauri-apps/api/webviewWindow')
      .then(({ WebviewWindow }) => { winRef.current = WebviewWindow.getCurrent() })
      .catch(() => {})
  }, [])

  function handleDragStart(e) {
    e.preventDefault()
    winRef.current?.startDragging().catch(() => {})
  }

  async function togglePin() {
    const next = !pinned
    setPinned(next)
    winRef.current?.setAlwaysOnTop(next).catch(() => {})
  }

  useEffect(() => {
    if (!sessionId) return
    if (skipNextLoad.current) { skipNextLoad.current = false; return }
    getSession(sessionId)
      .then(data => setMessages(data.messages.map(m => ({ role: m.role, content: m.content }))))
      .catch(() => {})
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(question) {
    setMessages(prev => [...prev, { role: 'human', content: question }])
    setLoading(true)
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true, searching: true }])

    try {
      await sendMessageStream(
        question, sessionId,
        (chunk) => {
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + chunk, searching: false }
            return updated
          })
        },
        (newSessionId, sources, messageId) => {
          if (newSessionId && !sessionId) {
            skipNextLoad.current = true
            onSessionChange(newSessionId)
          }
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              streaming: false,
              sources: sources || [],
              messageId,
            }
            return updated
          })
        }
      )
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Une erreur est survenue. Veuillez reessayer.',
          streaming: false,
          error: true,
        }
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">

      {/* ── Accent CHU ── */}
      <div className="h-0.5 bg-blue-600 flex-shrink-0 rounded-t-xl" />

      {/* ── Top bar ── */}
      <div
        onMouseDown={handleDragStart}
        className="flex items-center justify-between px-3 pt-2.5 pb-2 select-none cursor-grab active:cursor-grabbing flex-shrink-0"
      >
        {/* Left: system controls */}
        <div className="flex items-center gap-1">
          <button
            onMouseDown={e => e.stopPropagation()}
            onClick={() => onMinimize?.()}
            title="Réduire en avatar"
            className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors text-lg leading-none font-light"
          >
            −
          </button>
          <button
            onMouseDown={e => e.stopPropagation()}
            onClick={togglePin}
            title={pinned ? 'Désépingler' : 'Épingler'}
            className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors ${
              pinned ? 'text-blue-500 bg-blue-50' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill={pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 17v5M5 17h14v-2a2 2 0 00-1.1-1.8l-1.8-.9A2 2 0 0115 10.6V6h1V4H8v2h1v4.6a2 2 0 01-1.1 1.7l-1.8.9A2 2 0 005 15v2z"/>
            </svg>
          </button>
        </div>

        {/* Right: app actions */}
        <div className="flex items-center gap-1">
          <button
            onMouseDown={e => e.stopPropagation()}
            onClick={onNewChat}
            title="Nouvelle conversation"
            className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button
            onMouseDown={e => e.stopPropagation()}
            onClick={() => winRef.current?.toggleMaximize().catch(() => {})}
            title="Agrandir"
            className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1.5"/>
              <rect x="14" y="3" width="7" height="7" rx="1.5"/>
              <rect x="3" y="14" width="7" height="7" rx="1.5"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5"/>
            </svg>
          </button>
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3 pb-8">
            <img src={logo} alt="CHUbot" className="w-16 h-16 object-contain opacity-80" />
            <p className="text-sm text-slate-400">Comment puis-je vous aider ?</p>
            <div className="flex flex-col gap-1.5 w-64 mt-1">
              {[
                'Politique de congés annuels ?',
                'Procédure de demande de formation ?',
                'Comment fonctionne la paie ?',
              ].map(s => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="text-left px-3 py-2 rounded-xl border border-slate-100 text-xs text-slate-500 hover:border-blue-200 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            role={msg.role}
            content={msg.content}
            isStreaming={msg.streaming}
            isSearching={msg.searching}
            sources={msg.sources || []}
            messageId={msg.messageId}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
