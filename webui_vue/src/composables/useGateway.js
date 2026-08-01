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
export const currentChatId = ref(null)

let socket = null
let chatId = null
let apiToken = null
let wsToken = null
// Per-chat event handlers: Map<string, Set<Function>>
const chatHandlers = new Map()
// Pending newChat Promise
let pendingNewChat = null
// Pending generic requests: Map<request_id, {resolve, reject, timer}>
const pendingRequests = new Map()
// Pending ai_grade_question requests: Map<request_id, {resolve, reject, timer}>
const pendingAiGrade = new Map()
// Pending ai_generate_questions requests: Map<request_id, {resolve, reject, timer}>
const pendingAiGenerate = new Map()
// Pending create_homework requests: Map<request_id, {resolve, reject, timer}>
const pendingCreateHomework = new Map()
// Pending ai_tutor_evaluate requests: Map<request_id, {resolve, reject, timer}>
const pendingAiTutorEvaluate = new Map()
// Pending ai_generate_derivation requests: Map<request_id, {resolve, reject, timer}>
const pendingAiDerivation = new Map()
// Pending ai_tutor_recommend requests: Map<request_id, {resolve, reject, timer}>
const pendingTutorRecommend = new Map()
// Pending ai_polish requests: Map<request_id, {resolve, reject, timer}>
const pendingAiPolish = new Map()
// Pending ai_paper_summary requests: Map<request_id, {resolve, reject, timer}>
const pendingAiPaperSummary = new Map()
// Pending upload_paper requests: Map<request_id, {resolve, reject, timer}>
const pendingUploadPaper = new Map()
const pendingStudentOps = new Map()
let reconnectTimer = null
let reconnectAttempts = 0
let intentionallyClosed = false
let currentUrl = ''
let currentRole = ''
let currentUserId = ''
let tokenRefreshTimer = null
let tokenRefreshPromise = null

function _setStatus(ok) {
  connected.value = ok
}

function _reset() {
  _setStatus(false)
  socket = null
  _setChatId(null)
}

function _chatIdKey() {
  // Scope chatId per user so different accounts don't collide
  if (currentRole && currentUserId) {
    return `${CHAT_ID_KEY}.${currentRole}.${currentUserId}`
  }
  return CHAT_ID_KEY
}

function _loadChatId() {
  try {
    return localStorage.getItem(_chatIdKey()) || null
  } catch { return null }
}

function _saveChatId(id) {
  try {
    if (id) localStorage.setItem(_chatIdKey(), id)
  } catch {}
}

function _setChatId(id) {
  chatId = id || null
  currentChatId.value = chatId
  if (chatId) _saveChatId(chatId)
}

/** Derive WebSocket URL from bootstrap response — same as React webui's deriveWsUrl. */
function deriveWsUrl(wsPath, token) {
  const path = wsPath && wsPath.startsWith('/') ? wsPath : `/${wsPath || ''}`
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
  // Pass token via query parameter for WebSocket (websockets library limitation)
  const query = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${scheme}://${location.host}${path}${query}`
}

function scheduleReconnect() {
  if (intentionallyClosed) return
  const delay = Math.min(500 * 2 ** reconnectAttempts, 15000)
  reconnectAttempts++
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    refreshTokens().then(() => {
      const url = deriveWsUrl(currentWsPath, wsToken)
      _doConnect(url)
    }).catch(() => scheduleReconnect())
  }, delay)
}

let currentWsPath = '/'

function scheduleTokenRefresh(expiresIn) {
  if (tokenRefreshTimer) clearTimeout(tokenRefreshTimer)
  const ttlMs = Math.max(30000, Number(expiresIn || 300) * 1000)
  const refreshIn = Math.max(10000, ttlMs - 30000)
  tokenRefreshTimer = setTimeout(() => {
    tokenRefreshTimer = null
    refreshTokens().catch(() => {})
  }, refreshIn)
}

async function refreshTokens() {
  if (tokenRefreshPromise) return tokenRefreshPromise
  if (!currentRole || !currentUserId) throw new Error('连接失败：缺少用户信息')

  tokenRefreshPromise = (async () => {
    const params = new URLSearchParams({ role: currentRole, user_id: currentUserId })
    const resp = await fetch(`/webui/bootstrap?${params.toString()}`, { credentials: 'same-origin' })
    if (!resp.ok) throw new Error(`Bootstrap failed: HTTP ${resp.status}`)
    const boot = await resp.json()
    if (boot.ws_token && boot.api_token) {
      wsToken = boot.ws_token
      apiToken = boot.api_token
    } else if (boot.token) {
      wsToken = boot.token
      apiToken = boot.token
    } else {
      throw new Error('Bootstrap 缺少 token')
    }
    currentWsPath = boot.ws_path || currentWsPath || '/'
    sessionStorage.setItem('nanobot-webui.ws_token', wsToken)
    sessionStorage.setItem('nanobot-webui.api_token', apiToken)
    scheduleTokenRefresh(boot.expires_in)
    return boot
  })()

  try {
    return await tokenRefreshPromise
  } finally {
    tokenRefreshPromise = null
  }
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
  // Token is passed via query parameter in URL (websockets library limitation)
  const sock = new WebSocket(url)
  socket = sock

  sock.onopen = () => {
    _setStatus(true)
    reconnectAttempts = 0
    connectionError.value = ''

    // Expose global sendEnvelope function for useSessions
    window._wsSendEnvelope = (envelope) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(envelope))
      }
    }
  }

  sock.onmessage = (ev) => {
    let data
    try { data = JSON.parse(ev.data) } catch { return }

    if (data.event === 'ready') {
      const serverChatId = data.chat_id
      const storedChatId = _loadChatId()

      if (storedChatId && storedChatId !== serverChatId) {
        _setChatId(storedChatId)
        sock.send(JSON.stringify({ type: 'attach', chat_id: storedChatId }))
      } else {
        _setChatId(serverChatId)
      }
      return
    }

    if (data.event === 'attached') {
      _setChatId(data.chat_id)
      // Resolve pending newChat Promise
      if (pendingNewChat) {
        clearTimeout(pendingNewChat.timer)
        pendingNewChat.resolve(data.chat_id)
        pendingNewChat = null
      }
      _dispatch(data.chat_id, data)
      return
    }

    // Handle ai_grade_question_result (request/response correlation)
    if (data.event === 'ai_grade_question_result' && data.request_id) {
      const pending = pendingAiGrade.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiGrade.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({ score: data.score, comment: data.comment })
        }
      }
      return
    }

    // Handle ai_grade_submission_result (request/response correlation)
    if (data.event === 'ai_grade_submission_result' && data.request_id) {
      const pending = pendingAiGrade.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiGrade.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            score: data.score,
            feedback: data.feedback,
            rubric: data.rubric,
            strengths: data.strengths,
            improvements: data.improvements,
            questions: data.questions,
          })
        }
      }
      return
    }

    // Handle ai_generate_questions_result (request/response correlation)
    if (data.event === 'ai_generate_questions_result' && data.request_id) {
      const pending = pendingAiGenerate.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiGenerate.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            questions: data.questions,
            totalPoints: data.total_points,
          })
        }
      }
      return
    }

    // Handle create_homework_result (request/response correlation)
    if (data.event === 'create_homework_result' && data.request_id) {
      const pending = pendingCreateHomework.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingCreateHomework.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve(data.homework)
        }
      }
      return
    }

    // Handle ai_tutor_evaluate_result (request/response correlation)
    if (data.event === 'ai_tutor_evaluate_result' && data.request_id) {
      const pending = pendingAiTutorEvaluate.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiTutorEvaluate.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            isCorrect: data.is_correct,
            score: data.score,
            analysis: data.analysis,
            knowledgePoints: data.knowledge_points,
            errorType: data.error_type,
            errorDetail: data.error_detail,
            strategy: data.strategy,
            totalSubmissions: data.total_submissions,
          })
        }
      }
      return
    }

    // Handle ai_generate_derivation_result (request/response correlation)
    if (data.event === 'ai_generate_derivation_result' && data.request_id) {
      const pending = pendingAiDerivation.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiDerivation.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            steps: data.steps,
          })
        }
      }
      return
    }

    // Handle ai_tutor_recommend_result (request/response correlation)
    if (data.event === 'ai_tutor_recommend_result' && data.request_id) {
      const pending = pendingTutorRecommend.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingTutorRecommend.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            questions: data.questions,
            totalPoints: data.total_points,
          })
        }
      }
      return
    }

    // Handle upload_paper_result (request/response correlation)
    if (data.event === 'upload_paper_result' && data.request_id) {
      const pending = pendingUploadPaper.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingUploadPaper.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            paper: data.paper,
            pageCount: data.page_count,
            chunkCount: data.chunk_count,
          })
        }
      }
      return
    }

    // Handle ai_polish_result (request/response correlation)
    if (data.event === 'ai_polish_result' && data.request_id) {
      const pending = pendingAiPolish.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiPolish.delete(data.request_id)
        if (data.error && !data.polished_text) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            polishedText: data.polished_text,
            error: data.error || null,
          })
        }
      }
      return
    }

    // Handle ai_paper_summary_result (request/response correlation)
    if (data.event === 'ai_paper_summary_result' && data.request_id) {
      const pending = pendingAiPaperSummary.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiPaperSummary.delete(data.request_id)
        if (data.error && !data.summary) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            summary: data.summary,
            cached: data.cached || false,
            error: data.error || null,
          })
        }
      }
      return
    }

    // Handle session_deleted event
    if (data.event === 'session_deleted') {
      const handlers = window._wsSessionDeletedHandlers || []
      for (const h of handlers) {
        try { h(data) } catch { /* best-effort */ }
      }
      return
    }

    // Handle research_result_saved (request/response correlation)
    if (data.event === 'research_result_saved' && data.request_id) {
      const pending = pendingRequests.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingRequests.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({ result: data.result })
        }
      }
      return
    }

    // Handle ai_parse_question_item (streaming item)
    if (data.event === 'ai_parse_question_item' && data.request_id) {
      const pending = pendingAiGenerate.get(data.request_id)
      if (pending && pending.onItem) {
        try { pending.onItem(data.question) } catch { /* best-effort */ }
      }
      return
    }

    // Handle ai_parse_questions_result (request/response correlation)
    if (data.event === 'ai_parse_questions_result' && data.request_id) {
      const pending = pendingAiGenerate.get(data.request_id)
      if (pending) {
        clearTimeout(pending.timer)
        pendingAiGenerate.delete(data.request_id)
        if (data.error) {
          pending.reject(new Error(data.error))
        } else {
          pending.resolve({
            questions: data.questions,
            totalPoints: data.total_points,
          })
        }
      }
      return
    }

    // Handle student resource/category results (request/response correlation)
    const _studentResultEvents = [
      'student_resource_list_result',
      'student_resource_create_result',
      'student_resource_delete_result',
      'student_resource_update_result',
      'student_resource_categorize_result',
      'student_categories_list_result',
      'student_category_create_result',
      'student_category_update_result',
      'student_category_delete_result',
    ]
    if (_studentResultEvents.includes(data.event) && data.request_id) {
      const p = pendingStudentOps.get(data.request_id)
      if (p) {
        clearTimeout(p.timer)
        pendingStudentOps.delete(data.request_id)
        if (data.error) {
          p.reject(new Error(data.error))
        } else {
          p.resolve(data)
        }
      }
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

    if (!currentRole || !currentUserId) {
      const msg = '连接失败：缺少用户信息，请重新登录'
      connectionError.value = msg
      throw new Error(msg)
    }

    // 1. Bootstrap
    const params = new URLSearchParams()
    if (opts.role) params.set('role', opts.role)
    if (opts.userId) params.set('user_id', opts.userId)
    const qs = params.toString()

    let boot
    try {
      boot = await refreshTokens()
      if (!boot.ws_path) throw new Error('Bootstrap 缺少 ws_path')
    } catch (err) {
      connectionError.value = `无法连接 Gateway (${err.message})`
      throw err
    }

    // 2. Connect WebSocket (token passed via query parameter)
    currentWsPath = boot.ws_path
    const url = deriveWsUrl(currentWsPath, wsToken)
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
            _setChatId(storedChatId)
            sock.send(JSON.stringify({ type: 'attach', chat_id: storedChatId }))
          } else {
            _setChatId(serverChatId)
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
   *  Pass optional `meta` object to attach metadata (e.g. { _skill: "lesson-plan" }).
   *  Pass optional `targetChatId` to send to a specific chat instead of the current one. */
  function sendMessage(content, meta, targetChatId) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('未连接到 Gateway')
    }
    const envelope = { type: 'message', chat_id: targetChatId || chatId, content }
    if (meta && Object.keys(meta).length) envelope.meta = meta
    socket.send(JSON.stringify(envelope))
  }

  function sendResearcherClarification(question, requestId) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('Not connected to Gateway')
    }
    socket.send(JSON.stringify({
      type: 'researcher_clarify',
      chat_id: chatId,
      request_id: requestId,
      question,
    }))
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
    _setChatId(newChatId)
    socket.send(JSON.stringify({ type: 'attach', chat_id: newChatId }))
  }

  function getChatId() {
    return chatId
  }

  function getToken() {
    return apiToken || sessionStorage.getItem('nanobot-webui.api_token') || sessionStorage.getItem('nanobot-webui.token')
  }

  function disconnect() {
    intentionallyClosed = true
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    if (tokenRefreshTimer) { clearTimeout(tokenRefreshTimer); tokenRefreshTimer = null }
    if (socket) { try { socket.close() } catch {} socket = null }
    _reset()
  }

  function sendSaveSource(path, content) {
    if (!socket || socket.readyState !== WS_OPEN) {
      throw new Error('未连接到 Gateway')
    }
    socket.send(JSON.stringify({ type: 'save_source', path, content }))
  }

  /**
   * Save research result via WebSocket (supports long text).
   * Returns Promise<{result}>.
   */
  function sendSaveResearchResult(contentOrPayload, chatId = '', sessionTitle = '', timeoutMs = 30000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const payload = typeof contentOrPayload === 'object' && contentOrPayload !== null
      ? { ...contentOrPayload }
      : { content: contentOrPayload, chat_id: chatId, session_title: sessionTitle }
    const requestId = 'srr_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingRequests.delete(requestId)
        reject(new Error('保存超时'))
      }, timeoutMs)
      pendingRequests.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        ...payload,
        type: 'save_research_result',
        request_id: requestId,
      }))
    })
  }

  /**
   * Send an AI grading question via WebSocket (avoids HTTP proxy timeout).
   * Returns Promise<{score, comment}>.
   */
  function sendAiGradeQuestion(params, timeoutMs = 60000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'agr_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiGrade.delete(requestId)
        reject(new Error('AI 评分超时'))
      }, timeoutMs)
      pendingAiGrade.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_grade_question',
        request_id: requestId,
        content: params.content,
        max_score: params.maxScore,
        reference_answer: params.referenceAnswer || '',
        student_answer: params.studentAnswer || '',
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * AI-grade an entire submission via WebSocket.
   * Returns Promise<{score, feedback, rubric, strengths, improvements, questions}>.
   */
  function sendAiGradeSubmission(params, timeoutMs = 120000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'ags_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiGrade.delete(requestId)
        reject(new Error('AI 批改超时'))
      }, timeoutMs)
      pendingAiGrade.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_grade_submission',
        request_id: requestId,
        course_id: params.courseId,
        hw_id: params.hwId,
        student_id: params.studentId,
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * Generate questions from knowledge content via WebSocket.
   * Returns Promise<{questions, totalPoints}>.
   */
  function sendAiGenerateQuestions(params, timeoutMs = 120000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'agq_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiGenerate.delete(requestId)
        reject(new Error('AI 生成题目超时'))
      }, timeoutMs)
      pendingAiGenerate.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_generate_questions',
        request_id: requestId,
        content: params.content,
        num_questions: params.numQuestions,
        type_distribution: params.typeDistribution || {},
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  function sendAiParseQuestions(params) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'apq_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      // No timeout - let it run as long as needed
      // Store onItem callback for streaming
      pendingAiGenerate.set(requestId, { resolve, reject, timer: null, onItem: params.onItem })
      socket.send(JSON.stringify({
        type: 'ai_parse_questions',
        request_id: requestId,
        content: params.content,
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * Create homework via WebSocket (avoids HTTP 431 from large URL query params).
   * Returns Promise<homework>.
   */
  function sendCreateHomework(courseId, data, timeoutMs = 30000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'chw_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingCreateHomework.delete(requestId)
        reject(new Error('创建作业超时'))
      }, timeoutMs)
      pendingCreateHomework.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'create_homework',
        request_id: requestId,
        course_id: courseId,
        data: data,
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * AI-evaluate a student's answer in tutor mode.
   * Returns Promise<{isCorrect, score, analysis, knowledgePoints, errorType, errorDetail, strategy, totalSubmissions}>.
   */
  function sendAiTutorEvaluate(params, timeoutMs = 90000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'ate_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiTutorEvaluate.delete(requestId)
        reject(new Error('AI 辅导评估超时'))
      }, timeoutMs)
      pendingAiTutorEvaluate.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_tutor_evaluate',
        request_id: requestId,
        question: params.question,
        student_answer: params.studentAnswer,
        reference_answer: params.referenceAnswer || '',
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * Generate a derivation chain for a topic via AI.
   * Returns Promise<{steps}>.
   */
  function sendAiGenerateDerivation(params, timeoutMs = 120000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'agd_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiDerivation.delete(requestId)
        reject(new Error('AI 生成推导链超时'))
      }, timeoutMs)
      pendingAiDerivation.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_generate_derivation',
        request_id: requestId,
        topic: params.topic,
        mode: params.mode || 'formula',
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * Upload a PDF paper via chunked WebSocket messages (avoids HTTP 431 and large frame issues).
   * Splits base64 data into 512KB chunks and sends start/chunk/end sequence.
   * Returns Promise<{paper, pageCount, chunkCount}>.
   */
  function sendUploadPaper(fileData, fileName, title = '', timeoutMs = 180000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }

    const requestId = 'upl_' + Math.random().toString(36).slice(2, 10)
    const uploadId = 'u_' + Math.random().toString(36).slice(2, 10)
    const CHUNK_SIZE = 512 * 1024 // 512KB per chunk
    const totalChunks = Math.ceil(fileData.length / CHUNK_SIZE)

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingUploadPaper.delete(requestId)
        reject(new Error('上传超时'))
      }, timeoutMs)
      pendingUploadPaper.set(requestId, { resolve, reject, timer })

      // 1. Send start message
      socket.send(JSON.stringify({
        type: 'upload_paper_start',
        upload_id: uploadId,
        file_name: fileName,
        title,
        total_chunks: totalChunks,
        role: currentRole,
        user_id: currentUserId,
      }))

      // 2. Send chunks
      for (let i = 0; i < totalChunks; i++) {
        const chunk = fileData.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE)
        socket.send(JSON.stringify({
          type: 'upload_paper_chunk',
          upload_id: uploadId,
          chunk_index: i,
          chunk_data: chunk,
        }))
      }

      // 3. Send end message
      socket.send(JSON.stringify({
        type: 'upload_paper_end',
        upload_id: uploadId,
        request_id: requestId,
      }))
    })
  }

  /**
   * AI text polishing for writing assistant.
   * Returns Promise<{polishedText, error}>.
   */
  function sendAiPolish(text, mode = 'polish', timeoutMs = 60000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'apl_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiPolish.delete(requestId)
        reject(new Error('AI 润色超时'))
      }, timeoutMs)
      pendingAiPolish.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_polish',
        request_id: requestId,
        text,
        mode,
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * AI paper summarization.
   * Returns Promise<{summary, cached, error}>.
   */
  function sendAiPaperSummary(paperId, timeoutMs = 120000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'asm_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingAiPaperSummary.delete(requestId)
        reject(new Error('AI 摘要生成超时'))
      }, timeoutMs)
      pendingAiPaperSummary.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_paper_summary',
        request_id: requestId,
        paper_id: paperId,
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  /**
   * AI tutor recommend — generate practice questions based on student's tutor profile.
   * Returns Promise<{questions, totalPoints}>.
   */
  function sendAiTutorRecommend(params, timeoutMs = 180000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = 'atr_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingTutorRecommend.delete(requestId)
        reject(new Error('AI 推题超时'))
      }, timeoutMs)
      pendingTutorRecommend.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({
        type: 'ai_tutor_recommend',
        request_id: requestId,
        content: params.content || '',
        num_questions: params.numQuestions || 5,
        type_distribution: params.typeDistribution || {},
        role: currentRole,
        user_id: currentUserId,
      }))
    })
  }

  // -- Student resource/category operations via WebSocket --

  function _wsStudentSend(type, data, timeoutMs = 30000) {
    if (!socket || socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('未连接到 Gateway'))
    }
    const requestId = type + '_' + Math.random().toString(36).slice(2, 10)
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingStudentOps.delete(requestId)
        reject(new Error('操作超时'))
      }, timeoutMs)
      pendingStudentOps.set(requestId, { resolve, reject, timer })
      socket.send(JSON.stringify({ type, request_id: requestId, ...data }))
    })
  }

  function sendStudentResourceList(params = {}) {
    return _wsStudentSend('student_resource_list', {
      resource_type: params.resourceType || null,
      category_id: params.categoryId || null,
    })
  }

  function sendStudentResourceCreate(params) {
    return _wsStudentSend('student_resource_create', {
      resource_type: params.resourceType,
      title: params.title,
      content: params.content || '',
      source_type: params.sourceType || 'manual',
      source_id: params.sourceId || null,
      category_id: params.categoryId || null,
      metadata: params.metadata || {},
    })
  }

  function sendStudentResourceDelete(resourceId) {
    return _wsStudentSend('student_resource_delete', {
      resource_id: resourceId,
    })
  }

  function sendStudentResourceUpdate(resourceId, data) {
    return _wsStudentSend('student_resource_update', {
      resource_id: resourceId,
      data: data,
    })
  }

  function sendStudentResourceCategorize(resourceId, categoryId) {
    return _wsStudentSend('student_resource_categorize', {
      resource_id: resourceId,
      category_id: categoryId,
    })
  }

  function sendStudentCategoriesList() {
    return _wsStudentSend('student_categories_list', {})
  }

  function sendStudentCategoryCreate(params) {
    return _wsStudentSend('student_category_create', {
      name: params.name,
      description: params.description || '',
      color: params.color || null,
    })
  }

  function sendStudentCategoryUpdate(categoryId, params) {
    return _wsStudentSend('student_category_update', {
      category_id: categoryId,
      name: params.name,
      description: params.description,
      color: params.color,
    })
  }

  function sendStudentCategoryDelete(categoryId) {
    return _wsStudentSend('student_category_delete', {
      category_id: categoryId,
    })
  }

  return {
    connected, connectionError, currentChatId, connect, refreshTokens, sendMessage, sendResearcherClarification,
    disconnect, switchSession, getChatId, getToken, onChat, newChat,
    sendSaveSource, sendSaveResearchResult, sendAiGradeQuestion, sendAiGradeSubmission,
    sendAiGenerateQuestions, sendAiParseQuestions, sendCreateHomework, sendAiTutorEvaluate,
    sendAiGenerateDerivation, sendAiTutorRecommend, sendUploadPaper, sendAiPolish, sendAiPaperSummary,
    // Student resource/category operations
    sendStudentResourceList, sendStudentResourceCreate, sendStudentResourceDelete,
    sendStudentResourceUpdate, sendStudentResourceCategorize,
    sendStudentCategoriesList, sendStudentCategoryCreate, sendStudentCategoryUpdate,
    sendStudentCategoryDelete,
  }
}
