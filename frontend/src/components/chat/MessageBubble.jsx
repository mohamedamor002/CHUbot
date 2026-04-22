import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { submitFeedback } from '../../api/client.js'

const IconPdf = () => (
  <svg className="w-3.5 h-3.5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
  </svg>
)

const IconWeb = () => (
  <svg className="w-3.5 h-3.5 shrink-0 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
  </svg>
)

function SourceLink({ source }) {
  const isWeb = source.type === 'web'
  const href = isWeb
    ? source.url
    : `/api/v1/documents/file/${encodeURIComponent(source.name)}`

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="flex items-center gap-1.5 text-xs hover:underline truncate"
      style={{ color: isWeb ? '#2563eb' : '#dc2626' }}
      title={source.name}
    >
      {isWeb ? <IconWeb /> : <IconPdf />}
      <span className="truncate">{source.name}</span>
    </a>
  )
}

function FeedbackButtons({ messageId }) {
  const [vote, setVote] = useState(null) // 'up' | 'down' | null

  async function handleVote(isHelpful) {
    if (!messageId || vote) return
    setVote(isHelpful ? 'up' : 'down')
    try { await submitFeedback(messageId, isHelpful) } catch (_) {}
  }

  if (vote) return (
    <p className="text-xs text-slate-400 mt-2">
      {vote === 'up' ? 'Merci pour votre retour ✓' : 'Retour enregistré ✓'}
    </p>
  )

  return (
    <div className="flex gap-2 mt-2">
      <button onClick={() => handleVote(true)}
        className="text-slate-400 hover:text-green-500 transition-colors" title="Réponse utile">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017a2 2 0 01-1.789-1.106L7 13H4a2 2 0 01-2-2V8a2 2 0 012-2h2.5" />
        </svg>
      </button>
      <button onClick={() => handleVote(false)}
        className="text-slate-400 hover:text-red-500 transition-colors" title="Réponse non utile">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 011.789 1.106L17 11h3a2 2 0 012 2v2a2 2 0 01-2 2h-2.5" />
        </svg>
      </button>
    </div>
  )
}

export default function MessageBubble({ role, content, isStreaming = false, isSearching = false, sources = [], messageId }) {
  const isUser = role === 'human' || role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
        isUser ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'
      }`}>
        {isUser ? 'V' : 'C'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
        isUser
          ? 'bg-blue-600 text-white rounded-tr-sm'
          : 'bg-white text-slate-800 border border-slate-100 shadow-sm rounded-tl-sm'
      }`}>
        {isSearching ? (
          <span className="flex items-center gap-2 text-slate-400 text-xs">
            <svg className="w-3.5 h-3.5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Recherche dans les documents...
          </span>
        ) : isUser ? (
          <span className="whitespace-pre-wrap">{content}</span>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noreferrer" className="underline">{children}</a>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        )}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-slate-400 ml-1 animate-pulse rounded-sm" />
        )}
        {!isStreaming && !isUser && messageId && (
          <FeedbackButtons messageId={messageId} />
        )}
        {!isStreaming && !isUser && sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100">
            <p className="text-xs text-slate-400 mb-1.5">Sources :</p>
            <div className="flex flex-col gap-1.5">
              {sources.map((source, i) => (
                <SourceLink key={i} source={source} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
