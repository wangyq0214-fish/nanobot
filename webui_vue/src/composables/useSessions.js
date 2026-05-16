import { ref } from 'vue'

/**
 * Session management — fetch, select, delete sessions from the gateway API.
 */

const sessions = ref([])
const loading = ref(false)
const error = ref(null)
const activeKey = ref(null)

export function useSessions() {

  async function fetchSessions(role, userId, token) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (role) params.set('role', role)
      if (userId) params.set('user_id', userId)
      const qs = params.toString()
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch(`/api/sessions${qs ? '?' + qs : ''}`, {
        credentials: 'same-origin',
        headers,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      sessions.value = (body.sessions || []).map(s => ({
        key: s.key,
        chatId: extractChatId(s.key),
        createdAt: s.created_at,
        updatedAt: s.updated_at,
        preview: s.preview || '',
      }))
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchSessionMessages(key, role, userId, token) {
    const params = new URLSearchParams()
    if (role) params.set('role', role)
    if (userId) params.set('user_id', userId)
    const qs = params.toString()
    const url = `/api/sessions/${encodeURIComponent(key)}/messages${qs ? '?' + qs : ''}`
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(url, { credentials: 'same-origin', headers })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }

  async function deleteSession(key, role, userId, token) {
    const params = new URLSearchParams()
    if (role) params.set('role', role)
    if (userId) params.set('user_id', userId)
    const qs = params.toString()
    const url = `/api/sessions/${encodeURIComponent(key)}/delete${qs ? '?' + qs : ''}`
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(url, { credentials: 'same-origin', headers })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const body = await res.json()
    if (body.deleted) {
      sessions.value = sessions.value.filter(s => s.key !== key)
      if (activeKey.value === key) activeKey.value = null
    }
    return body.deleted
  }

  function setActive(key) {
    activeKey.value = key
  }

  return {
    sessions,
    loading,
    error,
    activeKey,
    fetchSessions,
    fetchSessionMessages,
    deleteSession,
    setActive,
  }
}

/** Extract the chat_id portion from a session key like "websocket:uuid" or "role:user:websocket:uuid" */
function extractChatId(key) {
  const idx = key.indexOf('websocket:')
  if (idx === -1) return key
  return key.slice(idx + 'websocket:'.length)
}
