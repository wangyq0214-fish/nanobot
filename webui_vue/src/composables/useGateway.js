import { ref } from 'vue'

/**
 * Gateway WebSocket connection — mirrors the React webui's event-driven pattern.
 *
 * Flow: GET /webui/bootstrap → token + ws_path → WebSocket on same host:port.
 * Vite proxy handles /webui (HTTP) and / (WS upgrade) forwarding to gateway.
 */

const WS_OPEN = 1
const WS_CLOSING = 2
const CHAT_ID_KEY = 'nanobot-webui.chatId'

export const connected = ref(false)
export const connectionError = ref('')

let socket = null
let chatId = null
let apiToken = null
// Per-chat event handlers: Map<string, Set<Function>>
const chatHandlers = new Map()
// Pending newChat Promise
let pendingNewChat = null
let reconnectTimer = null
let reconnectAttempts = 0
let intentionallyClosed = false
let currentUrl = ''
let currentRole = ''
let currentUserId = ''

function _setStatus(ok) {
  connected.value = ok
}

function _reset() {
  _setStatus(false)
  socket = null
}

function _loadChatId() {
  try {
    return localStorage.getItem(CHAT_ID_KEY) || null
  } catch { return null }
}

function _saveChatId(id) {
  try {
    if (id) localStorage.setItem(CHAT_ID_KEY, id)
  } catch {}
}

/** Derive WebSocket URL from bootstrap response — same as React webui's deriveWsUrl. */
function deriveWsUrl(wsPath, token) {
  const path = wsPath && wsPath.startsWith('/') ? wsPath : `/${wsPath || ''}`
  const query = `?token=${encodeURIComponent(token)}`
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${scheme}://${location.host}${path}${query}`
}

function scheduleReconnect() {
  if (intentionallyClosed) return
  const delay = Math.min(500 * 2 ** reconnectAttempts, 15000)
  reconnectAttempts++
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    _doConnect(currentUrl)
  }, delay)
}

/** Dispatch an event to all handlers registered for a chat_id. */
function _dispatch(chatId, ev) {
  const handlers = chatHandlers.get(chatId)
  if (!handlers) return
  for (const h of handlers) {
    try { h(ev) } catch { /* best-effort */ }
  }
}

function _doConnect(url) {
  currentUrl = url
  const sock = new WebSocket(url)
  socket = sock

  sock.onopen = () => {
    _setStatus(true)
    reconnectAttempts = 0
    connectionError.value = ''
  }

  sock.onmessage = (ev) => {
    let data
    try { data = JSON.parse(ev.data) } catch { return }

    if (data.event === 'ready') {
      const serverChatId = data.chat_id
      const storedChatId = _loadChatId()

      if (storedChatId && storedChatId !== serverChatId) {
        chatId = storedChatId
        sock.send(JSON.stringify({ type: 'attach', chat_id: storedChatId }))
      } else {
        chatId = serverChatId
        _saveChatId(serverChatId)
      }
      return
    }

    if (data.event === 'attached') {
      chatId = data.chat_id
      _saveChatId(data.chat_id)
      // Resolve pending newChat Promise
      if (pendingNewChat) {
        clearTimeout(pendingNewChat.timer)
        pendingNewChat.resolve(data.chat_id)
        pendingNewChat = null
      }
      _dispatch(data.chat_id, data)
      return
    }

    // Fan out all other events to per-chat handlers
    if (data.chat_id) {
      _dispatch(data.chat_id, data)
    }
  }

  sock.onerror = () => {
    connectionError.value = 'WebSocket 连接错误'
  }

  sock.onclose = () => {
    socket = null
    _setStatus(false)
    if (!intentionallyClosed) scheduleReconnect()
  }
}

export function useGateway() {

  /**
   * Bootstrap + connect.
   * @param {object} [opts]
   * @param {string} [opts.role]    - 'teacher' | 'student' | 'researcher'
   * @param {string} [opts.userId]
   */
  async function connect(opts = {}) {
    connectionError.value = ''
    intentionallyClosed = false
    currentRole = opts.role || ''
    currentUserId = opts.userId || ''

    // 1. Bootstrap
    const params = new URLSearchParams()
    if (opts.role) params.set('role', opts.role)
    if (opts.userId) params.set('user_id', opts.userId)
    const qs = params.toString()

    let boot
    try {
      const resp = await fetch(`/webui/bootstrap${qs ? '?' + qs : ''}`, { credentials: 'same-origin' })
      if (!resp.ok) throw new Error(`Bootstrap failed: HTTP ${resp.status}`)
      boot = await resp.json()
      if (!boot.token || !boot.ws_path) throw new Error('Bootstrap 缺少 token 或 ws_path')
      apiToken = boot.token
    } catch (err) {
      connectionError.value = `无法连接 Gateway (${err.message})`
      throw err
    }

    // 2. Connect WebSocket
    const url = deriveWsUrl(boot.ws_path, boot.token)
    return new Promise((resolve, reject) => {
      _doConnect(url)
      const sock = socket
      if (!sock) { reject(new Error('WebSocket 创建失败')); return }
      const onReady = (ev) => {
        let data
        try { data = JSON.parse(ev.data) } catch { return }
        if (data.event === 'ready') {
          const serverChatId = data.chat_id
          const storedChatId = _loadChatId()

          if (storedChatId && storedChatId !== serverChatId) {
            chatId = storedChatId
            sock.send(JSON.stringify({ type: 'attach', chat_id: storedChatId }))
          } else {
            chatId = serverChatId
            _saveChatId(serverChatId)
          }
          _setStatus(true)
          resolve()
          sock.removeEventListener('message', onReady)
        }
      }
      sock.addEventListener('message', onReady)
      sock.addEventListener('error', () => reject(new Error('WebSocket 连接失败')), { once: true })
    })
  }

  /**
   * Register an event handler for a specific chat_id.
   * Returns an unsubscribe function.
   *
   * Handler receives InboundEvent objects:
   *   { event: 'delta', chat_id, text, stream_id }
   *   { event: 'stream_end', chat_id, stream_id }
   *   { event: 'message', chat_id, text, kind, media_urls }
   *   { event: 'error', detail }
   */
  function onChat(id, handler) {
    let handlers = chatHandlers.get(id)
    if (!handlers) {
      handlers = new Set()
      chatHandlers.set(id, handlers)
    }
    handlers.add(handler)
    // Auto-attach if connected
    if (socket?.readyState === WS_OPEN) {
      socket.send(JSON.stringify({ type: 'attach', chat_id: id }))
    }
    return () => {
      const current = chatHandlers.get(id)
      if (!current) return
      current.delete(handler)
      if (current.size === 0) chatHandlers.delete(id)
    }
  }

  /** Send a message — fire and forget. Responses arrive via onChat handlers.
   *  Pass optional `meta` object to attach metadata (e.g. { _skill: "lesson-plan" }). */
  function sendMessage(content, meta) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('未连接到 Gateway')
    }
    const envelope = { type: 'message', chat_id: chatId, content }
    if (meta && Object.keys(meta).length) envelope.meta = meta
    socket.send(JSON.stringify(envelope))
  }

  /** Ask the server to create a new chat session. Returns Promise<string> with the new chat_id. */
  function newChat(timeoutMs = 5000) {
    if (pendingNewChat) {
      return Promise.reject(new Error('newChat already in flight'))
    }
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingNewChat = null
        reject(new Error('newChat timed out'))
      }, timeoutMs)
      pendingNewChat = { resolve, reject, timer }
      socket.send(JSON.stringify({ type: 'new_chat' }))
    })
  }

  function switchSession(newChatId) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('未连接到 Gateway')
    }
    chatId = newChatId
    _saveChatId(newChatId)
    socket.send(JSON.stringify({ type: 'attach', chat_id: newChatId }))
  }

  function getChatId() {
    return chatId
  }

  function getToken() {
    return apiToken
  }

  function disconnect() {
    intentionallyClosed = true
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    if (socket) { try { socket.close() } catch {} socket = null }
    _reset()
  }

  function sendSaveSource(path, content) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('未连接到 Gateway')
    }
    socket.send(JSON.stringify({ type: 'save_source', path, content }))
  }

  return { connected, connectionError, connect, sendMessage, disconnect, switchSession, getChatId, getToken, onChat, newChat, sendSaveSource }
}
