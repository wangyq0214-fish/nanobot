<template>
<div class="workspace-page">
  <!-- 顶部动态提示 -->
  <div class="top-hint">
    <div class="hint-badge">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
        <path d="M3 3v5h5"/>
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
        <path d="M16 16h5v5"/>
      </svg>
      <span>内核升级：强化交叉学科论证推理引擎</span>
    </div>
  </div>

  <!-- 中心核心区域 -->
  <div class="center-area" :class="{ 'has-chat': messages.length > 0 }">
    <!-- 欢迎语 -->
    <div class="welcome-section" v-show="messages.length === 0">
      <h1 class="welcome-title">工作台已就绪，{{ userName }}</h1>
      <p class="welcome-subtitle">
        <span>分布式学术智能体 —— </span>
        <span class="highlight">多智能体交叉验证，无坚实数据不作推论</span>
      </p>
    </div>

    <!-- 对话消息区域 -->
    <div class="chat-area" v-show="messages.length > 0" ref="chatAreaRef">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="msg-avatar" :class="msg.role">
          {{ msg.role === 'ai' ? 'AI' : '您' }}
        </div>
        <div class="msg-body">
          <div class="msg-mode-tag" v-if="msg.role === 'user' && msg.mode">
            {{ msg.mode === 'deep' ? '深度推理' : '快速响应' }}
          </div>
          <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
          <div class="msg-loading" v-if="msg.loading">
            <span class="dot-pulse"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索与对话容器 -->
    <div class="search-container" :class="{ focused: isFocused }">
      <textarea
        v-model="query"
        class="search-textarea"
        :placeholder="messages.length > 0 ? '继续提问...' : '输入您正在跟进的课题方向，或者上传文献进行深度交叉论证... 例如：探究存算一体架构（PIM）在端侧大模型部署中的能效比与潜在技术瓶颈。'"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keydown.enter.exact.prevent="handleSubmit"
      ></textarea>

      <div class="search-footer">
        <div class="mode-toggle">
          <button
            class="mode-btn"
            :class="{ active: chatMode === 'quick' }"
            @click="chatMode = 'quick'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            快速
          </button>
          <button
            class="mode-btn"
            :class="{ active: chatMode === 'deep' }"
            @click="chatMode = 'deep'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
            </svg>
            深度
          </button>
        </div>
        <span class="mode-desc">{{ chatMode === 'quick' ? '快速响应，适合简要问答与文献检索' : '深度推理，交叉验证多源论据并生成结构化报告' }}</span>

        <div class="search-actions">
          <button class="model-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
            </svg>
            <span>学术大模型内核</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </button>
          <button class="upload-btn" title="上传外部数据集 / PDF 文献">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          <button class="submit-btn" @click="handleSubmit" :disabled="sending">
            <svg v-if="!sending" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
            <span v-else class="btn-spinner"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- 场景引导卡片 -->
    <div class="scenarios-section" v-show="messages.length === 0">
      <div class="scenarios-label">快速启动科研工作流</div>

      <div class="scenarios-grid">
        <div
          v-for="scenario in scenarios"
          :key="scenario.path"
          class="scenario-card"
          @click="router.push(scenario.path)"
        >
          <div class="scenario-icon">
            <span v-html="scenario.icon"></span>
          </div>
          <h3 class="scenario-title">{{ scenario.title }}</h3>
          <p class="scenario-desc">{{ scenario.desc }}</p>
        </div>
      </div>
    </div>
  </div>

</div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useSessions } from '../../composables/useSessions.js'

const router = useRouter()
const { user } = useAuth()
const { sendMessage, onChat, getChatId, getToken, currentChatId } = useGateway()
const { fetchSessionMessages } = useSessions()

const query = ref('')
const isFocused = ref(false)
const chatMode = ref('quick')
const sending = ref(false)
const messages = ref([])
const chatAreaRef = ref(null)
let unsubChat = null
let subscribedChatId = null
let activeStreamId = null
let activeAiMessageId = null
let historyLoadSeq = 0

const userName = computed(() => user.value?.userId || '研究员')

const scenarios = [
  {
    path: '/researcher/paper-search',
    title: '演进脉络梳理',
    desc: '追踪并提炼某一细分技术路线近三年的主流演变与学术争鸣路线图',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v12"/><path d="M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M15 6a9 9 0 0 0-9 9"/><path d="M18 15v6"/><path d="M21 18h-6"/><path d="M15 18a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>'
  },
  {
    path: '/researcher/paper-library',
    title: '文献对照分析',
    desc: '上传多篇竞争性顶会论文，对其核心方法论、数据集表现进行多维比对',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M12 3v18"/><path d="M3 12h18"/></svg>'
  },
  {
    path: '/researcher/toolbench',
    title: 'AI 工具台中心',
    desc: '数据图谱分析、文献 OCR 解析、Python 沙箱终端等多模态学术工具矩阵',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'
  },
  {
    path: '/researcher/writing-assistant',
    title: '开题与评议准备',
    desc: '依据最新同行评审规范，全面评估论文初稿或开题报告的论证严密性',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/></svg>'
  }
]

// Simple markdown renderer
function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

function stopChatListener() {
  if (unsubChat) {
    unsubChat()
    unsubChat = null
  }
  subscribedChatId = null
  activeStreamId = null
  activeAiMessageId = null
}

function upsertStreamingAiMessage(ev) {
  const streamId = ev.stream_id || '__default_stream__'
  if (activeStreamId !== streamId || !activeAiMessageId) {
    activeStreamId = streamId
    activeAiMessageId = `ai_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'ai' && last.loading && !last.content) {
      last.id = activeAiMessageId
      last.streamId = streamId
    } else {
      messages.value.push({ id: activeAiMessageId, streamId, role: 'ai', content: '', loading: true })
    }
  }

  let msg = messages.value.find(m => m.id === activeAiMessageId)
  if (!msg) {
    msg = { id: activeAiMessageId, streamId, role: 'ai', content: '', loading: true }
    messages.value.push(msg)
  }
  return msg
}

function ensureChatListener(chatId = getChatId()) {
  if (!chatId) return
  if (subscribedChatId === chatId && unsubChat) return

  stopChatListener()
  subscribedChatId = chatId

  unsubChat = onChat(chatId, (ev) => {
    if (ev.chat_id && ev.chat_id !== subscribedChatId) return
    console.log('Chat event:', ev.event, 'Messages count:', messages.value.length)
    if (ev.event === 'delta') {
      const msg = upsertStreamingAiMessage(ev)
      msg.content += ev.text || ''
      msg.loading = true
      scrollToBottom()
    } else if (ev.event === 'stream_end') {
      const target = activeAiMessageId
        ? messages.value.find(m => m.id === activeAiMessageId)
        : messages.value[messages.value.length - 1]
      if (target && target.role === 'ai') {
        target.loading = false
        sending.value = false
        activeStreamId = null
        activeAiMessageId = null
        scrollToBottom()
      }
    } else if (ev.event === 'message') {
      // Non-streaming complete message
      const text = ev.text || ev.content || ''
      if (!text) return
      const target = activeAiMessageId
        ? messages.value.find(m => m.id === activeAiMessageId)
        : messages.value[messages.value.length - 1]
      if (target && target.role === 'ai' && target.loading) {
        target.content = text
        target.loading = false
      } else {
        messages.value.push({ role: 'ai', content: text, loading: false })
      }
      sending.value = false
      activeStreamId = null
      activeAiMessageId = null
      scrollToBottom()
    } else if (ev.event === 'error') {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai' && last.loading) {
        last.content = '⚠️ 请求出错：' + (ev.detail || ev.text || '未知错误')
        last.loading = false
        sending.value = false
        scrollToBottom()
      }
    }
  })
}

async function handleSubmit() {
  const text = query.value.trim()
  if (!text || sending.value) return

  // Add user message (only show user's actual text, not mode prefix)
  const userMsg = { role: 'user', content: text, mode: chatMode.value }
  console.log('Adding user message:', userMsg)
  messages.value.push(userMsg)
  query.value = ''
  sending.value = true
  scrollToBottom()

  // Add AI placeholder
  messages.value.push({ role: 'ai', content: '', loading: true })
  scrollToBottom()

  // Ensure we're listening for responses
  ensureChatListener()

  try {
    // Send message with mode in meta (not displayed in chat)
    sendMessage(text, { mode: chatMode.value })
  } catch (err) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'ai') {
      last.content = '⚠️ 发送失败：' + (err.message || '未连接到 Gateway')
      last.loading = false
    }
    sending.value = false
  }
}

// Load session history on mount
async function loadHistory(chatId = currentChatId.value || getChatId()) {
  if (!chatId) return
  // Session key format: websocket:{uuid} — must match backend convention
  const sessionKey = `websocket:${chatId}`
  const seq = ++historyLoadSeq
  let history = []
  try {
    const data = await fetchSessionMessages(sessionKey, 'researcher', user.value?.userId, getToken())
    if (data?.messages?.length) {
      history = data.messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({
          role: m.role === 'assistant' ? 'ai' : 'user',
          content: m.content || '',
          loading: false,
          mode: m.metadata?.mode || null,
        }))
    }
  } catch (err) {
    // Silently ignore — fresh session
  }
  if (seq !== historyLoadSeq || chatId !== (currentChatId.value || getChatId())) return
  messages.value = history
  scrollToBottom()
  // Always register chat listener for live messages
  ensureChatListener(chatId)
}

onMounted(() => {
  if (currentChatId.value || getChatId()) loadHistory()
})

watch(currentChatId, async (chatId, oldChatId) => {
  if (!chatId || chatId === oldChatId) return
  stopChatListener()
  sending.value = false
  await loadHistory(chatId)
}, { immediate: false })

onBeforeUnmount(() => {
  stopChatListener()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap');

.workspace-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 32px 24px;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
}

/* 顶部提示 */
.top-hint {
  margin-bottom: 48px;
  width: 100%;
  display: flex;
  justify-content: flex-start;
}

.hint-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 50px;
  padding: 8px 16px;
  font-size: 12px;
  color: #666666;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
}

.hint-badge:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.hint-badge svg {
  color: #121212;
  animation: spin-slow 3s linear infinite;
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 中心区域 */
.center-area {
  max-width: 800px;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-top: -40px;
}

.center-area.has-chat {
  justify-content: flex-start;
  padding-bottom: 24px;
}

/* 欢迎语 */
.welcome-section {
  text-align: center;
  margin-bottom: 32px;
}

.welcome-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 36px;
  font-weight: 400;
  color: #121212;
  margin: 0 0 12px;
  letter-spacing: 1px;
}

.welcome-subtitle {
  font-size: 14px;
  color: #666666;
  letter-spacing: 0.5px;
  margin: 0;
}

.highlight {
  font-weight: 500;
  color: #333333;
}

/* ===== Chat Area ===== */
.chat-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin-bottom: 16px;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.chat-msg {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.msg-avatar.ai {
  background: #121212;
  color: #fff;
}

.msg-avatar.user {
  background: #f0f0f0;
  color: #121212;
}

.msg-body {
  max-width: 85%;
  min-width: 0;
}

.msg-mode-tag {
  font-size: 10px;
  color: #121212;
  background: #f4f4f4;
  border: 1px solid #eaeaea;
  border-radius: 6px;
  padding: 2px 8px;
  display: inline-block;
  margin-bottom: 4px;
}

.msg-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.chat-msg.ai .msg-content {
  background: #f8f8f8;
  border: 1px solid #eaeaea;
  color: #121212;
  border-top-left-radius: 4px;
}

.chat-msg.user .msg-content {
  background: #121212;
  color: #fff;
  border-top-right-radius: 4px;
}

.msg-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Courier New', monospace;
}

.msg-content :deep(strong) {
  font-weight: 600;
}

.msg-loading {
  padding: 8px 16px;
}

.dot-pulse {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #121212;
  animation: dot-bounce 1.4s infinite ease-in-out both;
  position: relative;
}

.dot-pulse::before,
.dot-pulse::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #121212;
  animation: dot-bounce 1.4s infinite ease-in-out both;
}

.dot-pulse::before {
  left: -10px;
  animation-delay: -0.32s;
}

.dot-pulse::after {
  left: 10px;
  animation-delay: -0.16s;
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 搜索容器 */
.search-container {
  background: white;
  border-radius: 24px;
  border: 1px solid #eaeaea;
  padding: 20px;
  margin-bottom: 48px;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.search-container.focused {
  border-color: #121212;
  box-shadow: 0 16px 45px rgba(0, 0, 0, 0.05);
}

.center-area.has-chat .search-container {
  margin-top: auto;
  margin-bottom: 0;
}

.search-textarea {
  width: 100%;
  height: 112px;
  resize: none;
  background: transparent;
  border: none;
  font-size: 14px;
  color: #121212;
  line-height: 1.6;
  padding: 8px;
  outline: none;
  font-family: inherit;
  letter-spacing: 0.5px;
}

.center-area.has-chat .search-textarea {
  height: 60px;
}

.search-textarea::placeholder {
  color: #999999;
}

.search-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  margin-top: 8px;
  border-top: 1px solid #f0f0f0;
}

/* Mode toggle */
.mode-toggle {
  display: flex;
  align-items: center;
  gap: 2px;
  background: #f4f4f4;
  border-radius: 10px;
  padding: 3px;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  color: #666666;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  white-space: nowrap;
}

.mode-btn:hover {
  color: #121212;
  background: rgba(0, 0, 0, 0.04);
}

.mode-btn.active {
  color: #fff;
  background: #121212;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.mode-btn.active svg {
  stroke: #fff;
}

.mode-desc {
  font-size: 11px;
  color: #999999;
  margin-left: 8px;
}

.search-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f4f4f4;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.model-btn:hover {
  background: #e8e8e8;
}

.upload-btn {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #666666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.upload-btn:hover {
  background: #f4f4f4;
}

.submit-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #121212;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
}

.submit-btn:hover {
  background: #333333;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 场景引导 */
.scenarios-section {
  width: 100%;
}

.scenarios-label {
  text-align: center;
  font-size: 12px;
  color: #999999;
  letter-spacing: 2px;
  font-weight: 500;
  text-transform: uppercase;
  margin-bottom: 20px;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.scenario-card {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 20px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01);
}

.scenario-card:hover {
  border-color: #121212;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.scenario-icon {
  width: 40px;
  height: 40px;
  background: #f4f4f4;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  color: #121212;
  transition: background 0.2s ease;
}

.scenario-card:hover .scenario-icon {
  background: #e8e8e8;
}

.scenario-title {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
  margin: 0 0 8px;
  letter-spacing: 0.5px;
}

.scenario-desc {
  font-size: 11px;
  color: #999;
  line-height: 1.5;
  margin: 0;
  letter-spacing: 0.5px;
}

/* ===== Green Theme ===== */
body.green .hint-badge {
  background: white;
  border-color: #e2e6e2;
  color: #445c4b;
}

body.green .hint-badge svg {
  color: #526e5a;
}

body.green .welcome-title {
  color: #1e2720;
}

body.green .welcome-subtitle {
  color: #6b756c;
}

body.green .highlight {
  color: #3b473d;
}

body.green .msg-avatar.ai {
  background: #526e5a;
  color: #fff;
}

body.green .msg-avatar.user {
  background: #dbe1db;
  color: #1e2720;
}

body.green .msg-mode-tag {
  color: #526e5a;
  background: #edf2ee;
  border-color: #d4e0d6;
}

body.green .chat-msg.ai .msg-content {
  background: #f4f6f4;
  border-color: #edf1ed;
  color: #2c332e;
}

body.green .chat-msg.user .msg-content {
  background: #526e5a;
  color: #fff;
}

body.green .msg-content :deep(code) {
  background: rgba(82, 110, 90, 0.1);
}

body.green .dot-pulse,
body.green .dot-pulse::before,
body.green .dot-pulse::after {
  background: #526e5a;
}

body.green .search-container {
  border-color: #dee3de;
}

body.green .search-container.focused {
  border-color: #bad2be;
  box-shadow: 0 16px 45px rgba(30, 39, 32, 0.05);
}

body.green .search-textarea {
  color: #1e2720;
}

body.green .search-textarea::placeholder {
  color: #9da79e;
}

body.green .search-footer {
  border-top-color: #f0f3f0;
}

body.green .mode-toggle {
  background: #f0f2f0;
}

body.green .mode-btn {
  color: #717c72;
}

body.green .mode-btn:hover {
  color: #3b473d;
  background: rgba(82, 110, 90, 0.06);
}

body.green .mode-btn.active {
  background: #526e5a;
  box-shadow: 0 2px 6px rgba(82, 110, 90, 0.25);
}

body.green .mode-desc {
  color: #9da79e;
}

body.green .model-btn {
  background: #f0f2f0;
  color: #4a554b;
}

body.green .model-btn:hover {
  background: #e4e7e4;
}

body.green .upload-btn {
  color: #6b756c;
}

body.green .upload-btn:hover {
  background: #f0f2f0;
}

body.green .submit-btn {
  background: #526e5a;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.2);
}

body.green .submit-btn:hover {
  background: #415848;
  box-shadow: 0 6px 16px rgba(82, 110, 90, 0.3);
}

body.green .scenarios-label {
  color: #9da79e;
}

body.green .scenario-card {
  border-color: #e8ebe8;
}

body.green .scenario-card:hover {
  border-color: #bad2be;
  box-shadow: 0 8px 22px rgba(82, 110, 90, 0.07);
}

body.green .scenario-icon {
  background: #f2f4f2;
  color: #526e5a;
}

body.green .scenario-card:hover .scenario-icon {
  background: #ebf0eb;
}

body.green .scenario-title {
  color: #1e2720;
}

/* ===== Dark Theme ===== */
body.dark .hint-badge {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .hint-badge svg {
  color: #ffffff;
}

body.dark .welcome-title {
  color: #e5e5e5;
}

body.dark .welcome-subtitle {
  color: #999999;
}

body.dark .highlight {
  color: #b3b3b3;
}

body.dark .msg-avatar.ai {
  background: #ffffff;
  color: #121212;
}

body.dark .msg-avatar.user {
  background: #333333;
  color: #e5e5e5;
}

body.dark .msg-mode-tag {
  color: #b3b3b3;
  background: #2d2d2d;
  border-color: #333333;
}

body.dark .chat-msg.ai .msg-content {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .chat-msg.user .msg-content {
  background: #333333;
  color: #ffffff;
}

body.dark .msg-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

body.dark .dot-pulse,
body.dark .dot-pulse::before,
body.dark .dot-pulse::after {
  background: #ffffff;
}

body.dark .search-container {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2);
}

body.dark .search-container.focused {
  border-color: #444444;
  box-shadow: 0 16px 45px rgba(0, 0, 0, 0.3);
}

body.dark .search-textarea {
  color: #e5e5e5;
}

body.dark .search-textarea::placeholder {
  color: #666666;
}

body.dark .search-footer {
  border-top-color: #2d2d2d;
}

body.dark .mode-toggle {
  background: #1a1a1a;
}

body.dark .mode-btn {
  color: #999999;
}

body.dark .mode-btn:hover {
  color: #e5e5e5;
  background: rgba(255, 255, 255, 0.06);
}

body.dark .mode-btn.active {
  color: #121212;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

body.dark .mode-btn.active svg {
  stroke: #121212;
}

body.dark .mode-desc {
  color: #666666;
}

body.dark .model-btn {
  background: #1a1a1a;
  color: #999999;
}

body.dark .model-btn:hover {
  background: #2d2d2d;
}

body.dark .upload-btn {
  color: #999999;
}

body.dark .upload-btn:hover {
  background: #2d2d2d;
}

body.dark .submit-btn {
  background: #ffffff;
  color: #121212;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

body.dark .submit-btn:hover {
  background: #e5e5e5;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

body.dark .scenarios-label {
  color: #666666;
}

body.dark .scenario-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

body.dark .scenario-card:hover {
  border-color: #444444;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.2);
}

body.dark .scenario-icon {
  background: #1a1a1a;
  color: #ffffff;
}

body.dark .scenario-card:hover .scenario-icon {
  background: #2d2d2d;
}

body.dark .scenario-title {
  color: #e5e5e5;
}

body.dark .scenario-desc {
  color: #999999;
}

/* 响应式 */
@media (max-width: 900px) {
  .scenarios-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .welcome-title {
    font-size: 28px;
  }
}

@media (max-width: 600px) {
  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .search-footer {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
