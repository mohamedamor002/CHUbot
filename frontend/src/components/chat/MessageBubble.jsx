import ReactMarkdown from 'react-markdown'

export default function MessageBubble({ role, content, isStreaming = false }) {
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
        {isUser ? (
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
      </div>
    </div>
  )
}
