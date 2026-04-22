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

// ── Streaming ─────────────────────────────────────────────────────────────────

export async function sendMessageStream(question, sessionId = null, onChunk, onDone) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  })

  const newSessionId = response.headers.get('X-Session-ID')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value, { stream: true }))
  }

  onDone(newSessionId)
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
