import { useState } from 'react'
import DocumentPanel from '../documents/DocumentPanel.jsx'

export default function Sidebar({ sessionId, onNewChat }) {
  const [tab, setTab] = useState('chat') // 'chat' | 'docs'

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
        <button
          onClick={() => setTab('chat')}
          className={`flex-1 py-3 text-xs font-medium transition-colors ${
            tab === 'chat' ? 'bg-white/10 text-white' : 'text-blue-200 hover:text-white hover:bg-white/5'
          }`}
        >
          Conversation
        </button>
        <button
          onClick={() => setTab('docs')}
          className={`flex-1 py-3 text-xs font-medium transition-colors ${
            tab === 'docs' ? 'bg-white/10 text-white' : 'text-blue-200 hover:text-white hover:bg-white/5'
          }`}
        >
          Documents
        </button>
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
            {sessionId && (
              <div className="mt-4">
                <p className="text-xs text-blue-300 uppercase tracking-wider mb-2 px-1">Session active</p>
                <div className="px-3 py-2 rounded-lg bg-white/10 text-xs text-blue-100 break-all">
                  {sessionId}
                </div>
              </div>
            )}
          </div>
        ) : (
          <DocumentPanel />
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/10">
        <p className="text-xs text-blue-300 text-center">CHU - Service RH &copy; 2026</p>
      </div>
    </aside>
  )
}
