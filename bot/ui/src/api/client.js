import axios from 'axios'

export const BACKEND = 'http://127.0.0.1:8765'

const api = axios.create({
  baseURL: `${BACKEND}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

export async function sendMessage(question, sessionId = null) {
  const { data } = await api.post('/chat', { question, session_id: sessionId })
  return data
}

export async function getSession(sessionId) {
  const { data } = await api.get(`/chat/sessions/${sessionId}`)
  return data
}

export async function listSessions() {
  const { data } = await api.get('/chat/sessions')
  return data
}

export async function sendMessageStream(question, sessionId = null, onChunk, onDone) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000)

  try {
    const response = await fetch(`${BACKEND}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: sessionId }),
      signal: controller.signal,
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const newSessionId = response.headers.get('X-Session-ID')
    const messageId   = response.headers.get('X-Message-ID')
    const rawSources  = response.headers.get('X-Sources')
    const sources     = rawSources ? JSON.parse(rawSources) : []

    const reader  = response.body.getReader()
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

export async function checkHealth() {
  const res = await fetch(`${BACKEND}/health`, { signal: AbortSignal.timeout(3000) })
  if (!res.ok) throw new Error('backend not ready')
  return res.json()
}
