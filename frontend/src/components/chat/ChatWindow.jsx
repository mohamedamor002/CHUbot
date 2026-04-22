import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ChatInput from './ChatInput.jsx'
import { sendMessageStream } from '../../api/client.js'

export default function ChatWindow({ sessionId, onSessionChange }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(question) {
    setMessages((prev) => [...prev, { role: 'human', content: question }])
    setLoading(true)

    // Add empty assistant message for streaming
    setMessages((prev) => [...prev, { role: 'assistant', content: '', streaming: true }])

    try {
      await sendMessageStream(
        question,
        sessionId,
        (chunk) => {
          setMessages((prev) => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
            return updated
          })
        },
        (newSessionId) => {
          if (newSessionId && !sessionId) {
            onSessionChange(newSessionId)
          }
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false }
            return updated
          })
        }
      )
    } catch (err) {
      setMessages((prev) => {
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
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white">
        <h1 className="text-base font-semibold text-slate-800">Assistant RH - CHUbot</h1>
        <p className="text-xs text-slate-500">Posez vos questions sur les politiques et procedures RH</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 bg-slate-50">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-16">
            <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-slate-700">Comment puis-je vous aider ?</p>
              <p className="text-sm text-slate_500 mt-1 text-slate-500">
                Posez une question sur les conges, la paie, le reglement interieur...
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2 w-full max-w-md">
              {[
                "Quelle est la politique de conges ?",
                "Comment fonctionne la paie ?",
                "Quelles sont les heures de travail ?",
                "Procedure de demande de formation ?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSend(suggestion)}
                  className="text-left px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs text-slate-600 hover:border-blue-300 hover:text-blue-600 transition-colors"
                >
                  {suggestion}
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
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
