import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendMessage(question, sessionId = null) {
  const { data } = await api.post('/chat', { question, session_id: sessionId })
  return data // { answer, question, session_id }
}

export async function getSession(sessionId) {
  const { data } = await api.get(`/chat/sessions/${sessionId}`)
  return data // { session_id, messages, created_at }
}

export async function listSessions() {
  const { data } = await api.get('/chat/sessions')
  return data // [{ session_id, title, created_at, last_message }]
}

// ── Streaming ─────────────────────────────────────────────────────────────────

export async function sendMessageStream(question, sessionId = null, onChunk, onDone) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000) // 2 min max

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: sessionId }),
      signal: controller.signal,
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const newSessionId = response.headers.get('X-Session-ID')
    const messageId = response.headers.get('X-Message-ID')
    const rawSources = response.headers.get('X-Sources')
    const sources = rawSources ? JSON.parse(rawSources) : []

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onChunk(decoder.decode(value, { stream: true }))
    }

    onDone(newSessionId, sources, messageId)
  } finally {
    clearTimeout(timeout)
  }
}

export async function submitFeedback(messageId, isHelpful, rating = null) {
  await api.post('/feedback', { message_id: messageId, is_helpful: isHelpful, rating })
}

export async function getKpis() {
  const { data } = await api.get('/analytics/kpis')
  return data
}

// ── Documents ─────────────────────────────────────────────────────────────────

export async function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
  return data // { filename, chunks_indexed }
}

export async function listDocuments() {
  const { data } = await api.get('/documents/')
  return data // [{ filename, chunks_indexed }]
}
