import { useState, useRef } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText]   = useState('')
  const textareaRef       = useRef(null)

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleInput(e) {
    setText(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const canSend = !!text.trim() && !disabled

  return (
    <div className="px-3 pb-3 pt-1 flex-shrink-0">
      <div className={`flex items-end rounded-2xl border bg-white transition-all duration-150 ${
        canSend ? 'border-blue-300 shadow-md shadow-blue-50' : 'border-slate-200 shadow-sm shadow-slate-50'
      }`}>

        {/* ── Text area ── */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message..."
          className="flex-1 min-w-0 bg-transparent resize-none outline-none text-sm text-slate-800 placeholder-slate-400 pl-4 pr-2 py-2.5 max-h-28 disabled:opacity-50 leading-relaxed"
        />

        {/* ── Send button ── */}
        <div className="pr-2 pb-2 pt-2 shrink-0">
          <button
            onClick={submit}
            disabled={!canSend}
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-150 ${
              canSend
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:scale-95'
                : 'bg-slate-100 text-slate-300 cursor-not-allowed'
            }`}
          >
            {disabled ? (
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 19V5M5 12l7-7 7 7"/>
              </svg>
            )}
          </button>
        </div>

      </div>
    </div>
  )
}
