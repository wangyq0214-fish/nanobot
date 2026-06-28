import { ref } from 'vue'
import { useAuthFetch } from './useAuthFetch.js'

/**
 * Session management — fetch, select, delete sessions from the gateway API.
 */

const CHAT_ID_KEY = 'nanobot-webui.chat_id'

const sessions = ref([])
const loading = ref(false)
const error = ref(null)
const activeKey = ref(null)

export function useSessions() {
  const { authGet, authDelete } = useAuthFetch()

  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      const body = await authGet('/api/sessions')
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

  async function fetchSessionMessages(key) {
    return authGet(`/api/sessions/${encodeURIComponent(key)}/messages`)
  }

  async function deleteSession(key) {
    // Try WebSocket first via global sendWs function
    if (window._wsSendEnvelope) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket delete timeout'))
        }, 5000)

        // Register temporary event handler for session_deleted
        const onDeleted = (data) => {
          if (data.key === key) {
            clearTimeout(timeout)
            // Remove handler
            const idx = (window._wsSessionDeletedHandlers || []).indexOf(onDeleted)
            if (idx >= 0) window._wsSessionDeletedHandlers.splice(idx, 1)
            if (data.deleted) {
              sessions.value = sessions.value.filter(s => s.key !== key)
              if (activeKey.value === key) activeKey.value = null
              // Clear stored chatId if deleting current session
              const storedChatId = localStorage.getItem(CHAT_ID_KEY)
              const deletedChatId = extractChatId(key)
              if (storedChatId === deletedChatId) {
                localStorage.removeItem(CHAT_ID_KEY)
              }
            }
            resolve(data.deleted)
          }
        }

        // Register handler
        if (!window._wsSessionDeletedHandlers) window._wsSessionDeletedHandlers = []
        window._wsSessionDeletedHandlers.push(onDeleted)

        // Send delete request via WebSocket envelope
        window._wsSendEnvelope({ type: 'delete_session', key })
      })
    }

    // Fallback to HTTP
    const body = await authDelete(`/api/sessions/${encodeURIComponent(key)}/delete`)
    if (body.deleted) {
      sessions.value = sessions.value.filter(s => s.key !== key)
      if (activeKey.value === key) activeKey.value = null
      // Clear stored chatId if deleting current session
      const storedChatId = localStorage.getItem(CHAT_ID_KEY)
      const deletedChatId = extractChatId(key)
      if (storedChatId === deletedChatId) {
        localStorage.removeItem(CHAT_ID_KEY)
      }
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
