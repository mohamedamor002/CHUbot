import { useState, useRef } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

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
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleInput(e) {
    setText(e.target.value)
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3">
      <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-2 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Posez votre question RH..."
          className="flex-1 bg-transparent resize-none outline-none text-sm text-slate-800 placeholder-slate-400 py-1 max-h-36 disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="w-8 h-8 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white disabled:text-slate-400 flex items-center justify-center transition-colors shrink-0 mb-0.5"
        >
          {disabled ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-center text-xs text-slate-400 mt-2">
        Entree pour envoyer &middot; Shift+Entree pour une nouvelle ligne
      </p>
    </div>
  )
}
