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
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
        isUser
          ? 'bg-blue-600 text-white rounded-tr-sm'
          : 'bg-white text-slate-800 border border-slate-100 shadow-sm rounded-tl-sm'
      }`}>
        {content}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-slate-400 ml-1 animate-pulse rounded-sm" />
        )}
      </div>
    </div>
  )
}
