import { useEffect, useState } from 'react'
import DocumentPanel from '../documents/DocumentPanel.jsx'
import AnalyticsPanel from '../analytics/AnalyticsPanel.jsx'
import { listSessions } from '../../api/client.js'

export default function Sidebar({ sessionId, onNewChat, onSelectSession }) {
  const [tab, setTab] = useState('chat')
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {})
  }, [sessionId]) // recharger à chaque changement de session

  return (
    <aside className="w-72 bg-brand-900 text-white flex flex-col h-full shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">
            C
          </div>
          <div>
            <p className="font-semibold text-sm leading-tight">CHUbot</p>
            <p className="text-xs text-blue-200">Assistant RH</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/10">
        {['chat', 'docs', 'stats'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-3 text-xs font-medium transition-colors ${
              tab === t ? 'bg-white/10 text-white' : 'text-blue-200 hover:text-white hover:bg-white/5'
            }`}
          >
            {t === 'chat' ? 'Chat' : t === 'docs' ? 'Docs' : 'Stats'}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {tab === 'chat' ? (
          <div className="space-y-2">
            <button
              onClick={onNewChat}
              className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors text-sm font-medium"
            >
              <span className="text-lg leading-none">+</span>
              Nouvelle conversation
            </button>

            {sessions.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-blue-300 uppercase tracking-wider mb-2 px-1">
                  Récentes
                </p>
                <div className="space-y-1">
                  {sessions.map((s) => (
                    <button
                      key={s.session_id}
                      onClick={() => onSelectSession(s.session_id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors truncate ${
                        s.session_id === sessionId
                          ? 'bg-white/20 text-white'
                          : 'text-blue-100 hover:bg-white/10 hover:text-white'
                      }`}
                      title={s.title}
                    >
                      {s.title || 'Conversation'}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : tab === 'docs' ? (
          <DocumentPanel />
        ) : (
          <AnalyticsPanel />
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/10">
        <p className="text-xs text-blue-300 text-center">CHU - Service RH &copy; 2026</p>
      </div>
    </aside>
  )
}
