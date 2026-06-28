<template>
<div class="paper-workspace">
  <!-- Left sidebar: paper info + AI summary -->
  <aside class="sidebar">
    <div class="sidebar-content">
      <button class="btn-back" @click="router.push('/researcher/paper-library')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>
        </svg>
        <span>返回文献列表</span>
      </button>

      <div v-if="loading" class="sidebar-loading">加载中...</div>

      <template v-if="paper">
        <div class="paper-info">
          <h2 class="paper-title">{{ paper.title }}</h2>
          <p class="paper-authors" v-if="paper.authors">{{ paper.authors }}</p>
          <div class="paper-meta">
            <span v-if="paper.pageCount" class="meta-tag">{{ paper.pageCount }} 页</span>
            <span v-if="paper.year" class="meta-tag">{{ paper.year }}</span>
            <span v-if="paper.source" class="meta-source">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
              {{ paper.source }}
            </span>
          </div>
        </div>

        <div class="divider"></div>

        <div class="ai-section">
          <div class="ai-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
            <span>AI 核心摘要</span>
          </div>

          <button v-if="!summary && !summaryLoading" class="btn-generate" @click="generateSummary">
            生成 AI 摘要
          </button>

          <div v-if="summaryLoading" class="ai-loading">
            <div class="spinner"></div>
            <span>AI 正在分析...</span>
          </div>

          <template v-if="summary">
            <div class="summary-block">
              <h3 class="summary-heading">■ 核心研究概述</h3>
              <p class="summary-text">{{ extractOverview(summary) }}</p>
            </div>
            <div class="summary-block">
              <h3 class="summary-heading">■ 论证方法论</h3>
              <p class="summary-text">{{ extractMethodology(summary) }}</p>
            </div>
          </template>

          <div v-if="summaryError" class="ai-error">{{ summaryError }}</div>
        </div>

        <div class="divider"></div>

        <div class="info-section">
          <h3 class="info-heading">📊 论文信息</h3>
          <div class="info-grid">
            <div class="info-item" v-if="paper.doi">
              <span class="info-label">DOI</span>
              <span class="info-value">{{ paper.doi }}</span>
            </div>
            <div class="info-item" v-if="paper.venue">
              <span class="info-label">期刊</span>
              <span class="info-value">{{ paper.venue }}</span>
            </div>
            <div class="info-item" v-if="paper.citationCount">
              <span class="info-label">引用</span>
              <span class="info-value">{{ paper.citationCount }}</span>
            </div>
          </div>
        </div>

        <template v-if="annotations.length">
          <div class="divider"></div>
          <div class="info-section">
            <h3 class="info-heading">📝 我的标注</h3>
            <div class="annotations-list">
              <div v-for="(ann, i) in annotations" :key="i" class="annotation-item">
                <div class="ann-header">
                  <span class="ann-type">🖍 标记</span>
                  <span class="ann-page">P.{{ ann.page }}</span>
                  <button class="ann-delete" @click="deleteAnnotation(i)" title="删除">×</button>
                </div>
                <p class="ann-text">{{ ann.text }}</p>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>
  </aside>

  <!-- Main: PDF viewer -->
  <main class="main-panel">
    <div v-if="loading" class="main-loading">
      <div class="spinner large"></div>
      <div>加载论文内容...</div>
    </div>

    <div v-if="paper" class="pdf-content">
      <!-- Toolbar -->
      <div class="pdf-toolbar">
        <div class="toolbar-group">
          <button class="toolbar-btn" @click="pdfPage = Math.max(1, pdfPage - 1)" :disabled="pdfPage <= 1">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <span class="page-info">{{ pdfPage }} / {{ pdfTotal }} 页</span>
          <button class="toolbar-btn" @click="pdfPage = Math.min(pdfTotal, pdfPage + 1)" :disabled="pdfPage >= pdfTotal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>

        <div class="toolbar-divider"></div>

        <div class="toolbar-group">
          <button class="toolbar-btn" @click="pdfWidth = Math.max(400, pdfWidth - 100)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
          </button>
          <span class="zoom-label">{{ Math.round(pdfWidth / 9) }}%</span>
          <button class="toolbar-btn" @click="pdfWidth = Math.min(1400, pdfWidth + 100)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          </button>
        </div>

        <div class="toolbar-divider"></div>

        <button class="toolbar-btn-text" @click="fitWidth">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="m21 3-7 7"/><path d="m3 21 7-7"/></svg>
          <span>高度适应</span>
        </button>

        <div class="toolbar-spacer"></div>

        <!-- AI Chat Toggle -->
        <button class="toolbar-btn-text" :class="{ active: showChat }" @click="showChat = !showChat">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
          </svg>
          <span>Copilot</span>
        </button>
      </div>

      <!-- PDF Viewer -->
      <div class="pdf-viewer" ref="pdfViewerRef" @mouseup="onTextSelect">
        <div class="pdf-page-wrapper">
          <VuePdfEmbed
            :key="`pdf-${pdfPage}-${showChat}`"
            :source="pdfUrl"
            :page="pdfPage"
            :width="pdfWidth"
            textLayer
            @loaded="onPdfLoaded"
            @password-requested="onPdfPassword"
          />
        </div>

        <!-- Selection Toolbar -->
        <Teleport to="body">
          <div
            v-if="selectionToolbar.show"
            class="selection-toolbar"
            :style="{ left: selectionToolbar.x + 'px', top: selectionToolbar.y + 'px' }"
            @mousedown.prevent
          >
            <button class="st-btn" @click="doHighlight" title="标记高亮">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 11-6 6v3h9l3-3"/><path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/></svg>
              <span>标记</span>
            </button>
            <div class="st-divider"></div>
            <button class="st-btn" @click="doExplain" title="AI 解释">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 5 8 12 8 12s8-7 8-12a8 8 0 0 0-8-8z"/><path d="M12 13V9"/><circle cx="12" cy="16" r=".5" fill="currentColor"/></svg>
              <span>AI 解释</span>
            </button>
            <button class="st-btn" @click="doTranslate" title="翻译">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>
              <span>翻译</span>
            </button>
          </div>
        </Teleport>
      </div>
    </div>
  </main>

  <!-- Right: AI Chat Panel -->
  <aside v-if="showChat" class="chat-panel">
    <div class="chat-header">
      <div class="chat-title">
        <div class="chat-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
          </svg>
        </div>
        <span>学术研讨 Copilot</span>
      </div>
      <div class="chat-status">
        <span class="status-dot"></span>
        <span>论证引擎在线</span>
      </div>
    </div>

    <div class="chat-messages" ref="chatMessagesRef">
      <div v-for="(msg, i) in chatMessages" :key="i" class="message" :class="msg.role">
        <div class="message-avatar" :class="msg.role">
          {{ msg.role === 'ai' ? 'AI' : '您' }}
        </div>
        <div class="message-content" v-html="msg.content"></div>
      </div>
    </div>

    <div class="chat-actions">
      <button class="action-btn" @click="sendQuickAction('拆解消融指标')">📊 拆解消融指标</button>
      <button class="action-btn" @click="sendQuickAction('溯源引证漏洞')">🔍 溯源引证漏洞</button>
    </div>

    <div class="chat-input-area">
      <div class="chat-input-wrapper">
        <textarea
          v-model="chatInput"
          class="chat-input"
          placeholder="向 Copilot 提问..."
          @keydown.enter.exact.prevent="sendMessage"
          rows="2"
        ></textarea>
        <div class="chat-input-actions">
          <button class="send-btn" @click="sendMessage" :disabled="!chatInput.trim()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </aside>
</div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import VuePdfEmbed from 'vue-pdf-embed'
import 'vue-pdf-embed/dist/styles/textLayer.css'
import { useGateway } from '../../composables/useGateway.js'

const router = useRouter()
const route = useRoute()
const { getToken } = useGateway()

const paper = ref(null)
const loading = ref(true)

// Auth helpers
function _authParams() {
  const raw = localStorage.getItem('nanobot-webui.user')
  const user = raw ? JSON.parse(raw) : {}
  const params = new URLSearchParams()
  if (user.role) params.set('role', user.role)
  if (user.userId) params.set('user_id', user.userId)
  const token = getToken()
  if (token) params.set('token', token)
  return params
}

function _authHeaders() {
  const token = getToken()
  const h = { 'X-Requested-With': 'XMLHttpRequest' }
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

// PDF viewer state
const pdfPage = ref(1)
const pdfTotal = ref(1)
const pdfWidth = ref(900)
const pdfViewerRef = ref(null)
let resizeObserver = null

const pdfUrl = ref(null)

async function loadPdfBlob() {
  if (!paper.value) return
  const params = _authParams()
  try {
    const res = await fetch(`/api/researcher/papers/${paper.value.id}/pdf?${params.toString()}`, {
      credentials: 'omit',
      headers: _authHeaders(),
    })
    if (!res.ok) { console.warn('PDF fetch failed:', res.status); return }
    const blob = await res.blob()
    pdfUrl.value = URL.createObjectURL(blob)
  } catch (e) { console.warn('PDF load error:', e) }
}

function onPdfLoaded(pdf) {
  pdfTotal.value = pdf.numPages || 1
}

function onPdfPassword() {
  console.warn('PDF requires password')
}

function fitWidth() {
  if (!pdfViewerRef.value) return
  const containerW = pdfViewerRef.value.clientWidth - 48
  pdfWidth.value = Math.min(1200, Math.max(400, containerW))
}

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    if (pdfViewerRef.value) {
      const containerW = pdfViewerRef.value.clientWidth - 48
      pdfWidth.value = Math.min(1200, Math.max(400, containerW))
    }
  })
  if (pdfViewerRef.value) {
    resizeObserver.observe(pdfViewerRef.value)
  }
  fetchPaper()
})

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
})

// AI summary state
const summary = ref('')
const summaryLoading = ref(false)
const summaryError = ref('')

async function fetchPaper() {
  const paperId = route.params.id
  if (!paperId) return

  loading.value = true
  try {
    const params = _authParams()
    const res = await fetch(`/api/researcher/papers/${paperId}?${params.toString()}`, {
      credentials: 'omit',
      headers: _authHeaders(),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    paper.value = data.paper
    loadPdfBlob()

    if (paper.value?.aiSummary) {
      summary.value = paper.value.aiSummary
    }
    if (paper.value?.annotations) {
      annotations.value = paper.value.annotations
    }
  } catch (e) {
    console.error('[PaperWorkspace] fetch error:', e)
  } finally {
    loading.value = false
  }
}

async function generateSummary() {
  if (!paper.value) return
  summaryLoading.value = true
  summaryError.value = ''

  try {
    const { sendAiPaperSummary } = useGateway()
    const result = await sendAiPaperSummary(paper.value.id)
    summary.value = result.summary || ''
    if (result.error) summaryError.value = result.error
    if (result.summary) paper.value.aiSummary = result.summary
  } catch (err) {
    summaryError.value = err.message || 'AI 摘要生成失败'
  } finally {
    summaryLoading.value = false
  }
}

function extractOverview(text) {
  if (!text) return '暂无概述'
  // Try to extract first paragraph or section
  const lines = text.split('\n').filter(l => l.trim())
  return lines.slice(0, 3).join(' ').substring(0, 300) + (text.length > 300 ? '...' : '')
}

function extractMethodology(text) {
  if (!text) return '暂无方法论'
  // Try to find methodology section
  const methodMatch = text.match(/(?:方法|methodology|approach|framework)[:\s]*([\s\S]*?)(?=\n\n|\n#|$)/i)
  if (methodMatch) return methodMatch[1].substring(0, 300)
  // Fallback to middle section
  const lines = text.split('\n').filter(l => l.trim())
  return lines.slice(3, 6).join(' ').substring(0, 300) + '...'
}

// Chat state
const showChat = ref(false)
const chatInput = ref('')
const chatMessagesRef = ref(null)
const chatMessages = ref([
  {
    role: 'ai',
    content: '您好，首席研究员。我已完成对本篇论文的多维图谱重构，请问需要针对哪个核心算式、控制变量或消融缺陷进行深度探讨？'
  }
])

// Selection toolbar state
const selectionToolbar = ref({ show: false, x: 0, y: 0, text: '' })
const annotations = ref([])

function onTextSelect() {
  const sel = window.getSelection()
  const text = sel?.toString().trim()
  if (!text || text.length < 2) {
    return
  }
  const range = sel.getRangeAt(0)
  const rect = range.getBoundingClientRect()
  selectionToolbar.value = {
    show: true,
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
    text,
  }
}

function hideToolbar() {
  selectionToolbar.value.show = false
}

function doHighlight() {
  const text = selectionToolbar.value.text.slice(0, 200)
  annotations.value.push({ page: pdfPage.value, type: 'highlight', text })
  saveAnnotations()
  hideToolbar()
}

function doExplain() {
  const text = selectionToolbar.value.text
  showChat.value = true
  chatInput.value = `请解释以下学术文本：\n\n"${text}"`
  hideToolbar()
  nextTick(() => sendMessage())
}

function doTranslate() {
  const text = selectionToolbar.value.text
  showChat.value = true
  chatInput.value = `请翻译以下学术文本为中文：\n\n"${text}"`
  hideToolbar()
  nextTick(() => sendMessage())
}

async function saveAnnotations() {
  if (!paper.value) return
  try {
    const params = _authParams()
    params.set('data', JSON.stringify({ annotations: annotations.value }))
    await fetch(`/api/researcher/papers/${paper.value.id}/annotations?${params.toString()}`, {
      headers: _authHeaders(),
    })
  } catch (e) { console.warn('Save annotations failed:', e) }
}

function deleteAnnotation(index) {
  annotations.value.splice(index, 1)
  saveAnnotations()
}

// Hide toolbar on click outside
onMounted(() => {
  document.addEventListener('mousedown', onDocMouseDown)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocMouseDown)
})
function onDocMouseDown(e) {
  if (!selectionToolbar.value.show) return
  if (e.target.closest('.selection-toolbar')) return
  hideToolbar()
}

async function sendMessage() {
  if (!chatInput.value.trim()) return

  const userMsg = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', content: userMsg })
  chatInput.value = ''

  // Scroll to bottom
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })

  // Simulate AI response (replace with actual API call)
  chatMessages.value.push({ role: 'ai', content: '正在分析您的问题...' })

  // TODO: Integrate with actual AI chat API
  setTimeout(() => {
    chatMessages.value[chatMessages.value.length - 1].content =
      `关于"${userMsg}"，这是一个很好的问题。基于论文内容，我建议从以下几个角度进行分析...`
  }, 1000)
}

function sendQuickAction(action) {
  chatInput.value = action
  sendMessage()
}
</script>

<style scoped>
.paper-workspace {
  display: flex;
  height: 100%;
  background: #f8f8f8;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #edf0ed;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  font-size: 12px;
  color: #666666;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.btn-back:hover {
  color: #121212;
}

.sidebar-loading {
  text-align: center;
  color: #999999;
  padding: 40px 0;
  font-size: 12px;
}

.paper-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.paper-title {
  font-size: 14px;
  font-weight: 600;
  color: #121212;
  line-height: 1.5;
}

.paper-authors {
  font-size: 11px;
  color: #9ca3af;
}

.paper-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 10px;
  padding: 2px 8px;
  background: #f4f4f4;
  border: 1px solid #e2e7e2;
  border-radius: 4px;
  color: #999999;
}

.meta-source {
  font-size: 10px;
  padding: 2px 8px;
  background: #f4f4f4;
  border: 1px solid #e2e7e2;
  border-radius: 4px;
  color: #999999;
  display: flex;
  align-items: center;
  gap: 4px;
}

.divider {
  border-top: 1px solid #f5f7f5;
}

/* AI Section */
.ai-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f0f0f0;
  border: 1px solid #e2eae2;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #121212;
  width: fit-content;
}

.btn-generate {
  width: 100%;
  padding: 10px;
  background: #121212;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-generate:hover {
  background: #333333;
}

.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  color: #121212;
  font-size: 12px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #dee3de;
  border-top-color: #121212;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner.large {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.ai-error {
  padding: 8px;
  color: #ef4444;
  font-size: 12px;
}

.summary-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-heading {
  font-size: 12px;
  font-weight: 600;
  color: #121212;
}

.summary-text {
  font-size: 11px;
  color: #333333;
  line-height: 1.6;
  font-family: 'Noto Serif SC', 'SimSun', serif;
  text-align: justify;
}

/* Info Section */
.info-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-heading {
  font-size: 12px;
  font-weight: 600;
  color: #121212;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.info-label {
  color: #999999;
  min-width: 40px;
}

.info-value {
  color: #666666;
  word-break: break-all;
}

/* Annotations list */
.annotations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.annotation-item {
  background: #f8faf8;
  border-radius: 6px;
  padding: 8px 10px;
  border-left: 3px solid #526e5a;
}

.ann-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.ann-type {
  font-size: 10px;
  font-weight: 600;
  color: #121212;
}

.ann-page {
  font-size: 10px;
  color: #999999;
  margin-left: auto;
}

.ann-delete {
  background: none;
  border: none;
  color: #b0b8b1;
  font-size: 14px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
}

.ann-delete:hover {
  color: #d44;
}

.ann-text {
  font-size: 11px;
  color: #3a4a3a;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Main Panel */
.main-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #eaecea;
}

.main-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #666666;
  font-size: 12px;
}

/* PDF Content */
.pdf-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* Toolbar */
.pdf-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #dee3de;
  flex-shrink: 0;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: 1px solid #dee3de;
  border-radius: 6px;
  cursor: pointer;
  color: #666666;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background: #f8f8f8;
  border-color: #121212;
  color: #121212;
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.toolbar-btn-text {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f2f6f3;
  border: 1px solid #c8decb;
  border-radius: 6px;
  cursor: pointer;
  color: #121212;
  font-size: 11px;
  font-weight: 500;
  transition: all 0.2s;
}

.toolbar-btn-text:hover {
  background: #e2eae2;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #f0f0f0;
}

.page-info {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  background: #f4f4f4;
  padding: 2px 8px;
  border: 1px solid #e2e7e2;
  border-radius: 4px;
  color: #666666;
}

.zoom-label {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  min-width: 36px;
  text-align: center;
  color: #666666;
}

/* PDF Viewer */
.pdf-viewer {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.pdf-page-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px;
  min-height: 100%;
}

.pdf-page-wrapper :deep(.vue-pdf-embed) {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.pdf-page-wrapper :deep(canvas) {
  display: block;
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  border: 1px solid #dee3de;
}

/* Text layer: only show highlight overlay, no text */
.pdf-page-wrapper :deep(.textLayer) span {
  color: transparent !important;
}
.pdf-page-wrapper :deep(.textLayer) ::selection {
  background: rgba(0, 0, 0, 0.3);
  color: transparent !important;
  text-shadow: none;
}

.toolbar-spacer {
  flex: 1;
}

.toolbar-btn-text.active {
  background: #121212;
  color: white;
  border-color: #121212;
}

/* Chat Panel */
.chat-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #edf0ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid #edf0ed;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #121212;
}

.chat-icon {
  width: 24px;
  height: 24px;
  background: #f0f0f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #121212;
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #059669;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid #d1fae5;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: linear-gradient(to bottom, #fbfdfb, white);
}

.message {
  display: flex;
  gap: 10px;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

.message-avatar.ai {
  background: #121212;
  color: white;
}

.message-avatar.user {
  background: #e8e8e8;
  color: #121212;
}

.message-content {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 12px;
  line-height: 1.6;
}

.message.ai .message-content {
  background: #f8f8f8;
  border: 1px solid #edf1ed;
  color: #121212;
  font-family: 'Noto Serif SC', 'SimSun', serif;
}

.message.user .message-content {
  background: #121212;
  color: white;
}

.chat-actions {
  padding: 8px 16px;
  border-top: 1px solid #f5f7f5;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.action-btn {
  font-size: 10px;
  padding: 4px 10px;
  background: #f8f8f8;
  border: 1px solid #dee3de;
  border-radius: 6px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f2f6f3;
  color: #121212;
  border-color: #121212;
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #edf0ed;
  background: white;
}

.chat-input-wrapper {
  background: #f8f8f8;
  border: 1px solid #dee3de;
  border-radius: 12px;
  padding: 10px;
  transition: all 0.2s;
}

.chat-input-wrapper:focus-within {
  border-color: #121212;
  background: white;
}

.chat-input {
  width: 100%;
  background: none;
  border: none;
  outline: none;
  font-size: 12px;
  color: #121212;
  resize: none;
  line-height: 1.5;
}

.chat-input::placeholder {
  color: #999999;
}

.chat-input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.send-btn {
  width: 28px;
  height: 28px;
  background: #121212;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.send-btn:hover {
  background: #333333;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Dark Theme ===== */
body.dark .sidebar {
  background: #1a1a1a;
  border-right-color: #2d2d2d;
}

body.dark .btn-back {
  color: #999999;
}

body.dark .btn-back:hover {
  color: #ffffff;
}

body.dark .sidebar-loading {
  color: #666666;
}

body.dark .paper-title {
  color: #ffffff;
}

body.dark .paper-authors {
  color: #999999;
}

body.dark .meta-tag,
body.dark .meta-source {
  background: #242424;
  border-color: #2d2d2d;
  color: #999999;
}

body.dark .divider {
  border-top-color: #2d2d2d;
}

body.dark .ai-badge {
  background: #1a2420;
  border-color: #2d3d30;
  color: #b3b3b3;
}

body.dark .btn-generate {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-generate:hover {
  background: #e5e5e5;
}

body.dark .ai-loading {
  color: #b3b3b3;
}

body.dark .spinner {
  border-color: #333333;
  border-top-color: #ffffff;
}

body.dark .ai-error {
  color: #ef4444;
}

body.dark .summary-heading {
  color: #ffffff;
}

body.dark .summary-text {
  color: #b3b3b3;
}

body.dark .info-heading {
  color: #ffffff;
}

body.dark .info-label {
  color: #666666;
}

body.dark .info-value {
  color: #b3b3b3;
}

body.dark .annotation-item {
  background: #242424;
  border-left-color: #ffffff;
}

body.dark .ann-type {
  color: #ffffff;
}

body.dark .ann-page {
  color: #666666;
}

body.dark .ann-delete {
  color: #666666;
}

body.dark .ann-delete:hover {
  color: #ef4444;
}

body.dark .ann-text {
  color: #b3b3b3;
}

body.dark .main-panel {
  background: #141414;
}

body.dark .main-loading {
  color: #b3b3b3;
}

body.dark .pdf-toolbar {
  background: #1a1a1a;
  border-bottom-color: #2d2d2d;
}

body.dark .toolbar-btn {
  border-color: #333333;
  color: #b3b3b3;
}

body.dark .toolbar-btn:hover:not(:disabled) {
  background: #242424;
  border-color: #ffffff;
  color: #ffffff;
}

body.dark .toolbar-btn-text {
  background: #1a2420;
  border-color: #2d3d30;
  color: #b3b3b3;
}

body.dark .toolbar-btn-text:hover {
  background: #2d3d30;
}

body.dark .toolbar-btn-text.active {
  background: #ffffff;
  color: #121212;
  border-color: #ffffff;
}

body.dark .toolbar-divider {
  background: #333333;
}

body.dark .page-info {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .zoom-label {
  color: #b3b3b3;
}

body.dark .pdf-page-wrapper :deep(canvas) {
  border-color: #2d2d2d;
}

body.dark .chat-panel {
  background: #1a1a1a;
  border-left-color: #2d2d2d;
}

body.dark .chat-header {
  background: #141414;
  border-bottom-color: #2d2d2d;
}

body.dark .chat-title {
  color: #ffffff;
}

body.dark .chat-icon {
  background: #2d2d2d;
  color: #ffffff;
}

body.dark .chat-status {
  color: #10b981;
  background: #0a2520;
  border-color: #0d3b2e;
}

body.dark .chat-messages {
  background: linear-gradient(to bottom, #141414, #1a1a1a);
}

body.dark .message-avatar.ai {
  background: #ffffff;
  color: #121212;
}

body.dark .message-avatar.user {
  background: #333333;
  color: #e5e5e5;
}

body.dark .message.ai .message-content {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .message.user .message-content {
  background: #333333;
  color: #ffffff;
}

body.dark .chat-actions {
  border-top-color: #2d2d2d;
}

body.dark .action-btn {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .action-btn:hover {
  background: #2d2d2d;
  color: #ffffff;
  border-color: #ffffff;
}

body.dark .chat-input-area {
  background: #1a1a1a;
  border-top-color: #2d2d2d;
}

body.dark .chat-input-wrapper {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .chat-input-wrapper:focus-within {
  background: #1a1a1a;
  border-color: #444444;
}

body.dark .chat-input {
  color: #e5e5e5;
}

body.dark .chat-input::placeholder {
  color: #666666;
}

body.dark .send-btn {
  background: #ffffff;
  color: #121212;
}

body.dark .send-btn:hover {
  background: #e5e5e5;
}
</style>

<style>
/* Selection toolbar (teleported to body, not scoped) */
.selection-toolbar {
  position: fixed;
  z-index: 10000;
  transform: translateX(-50%) translateY(-100%);
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.14), 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  animation: st-fade-in 0.12s ease-out;
  border: 1px solid #e8ece8;
}

@keyframes st-fade-in {
  from { opacity: 0; transform: translateX(-50%) translateY(-100%) scale(0.95); }
  to { opacity: 1; transform: translateX(-50%) translateY(-100%) scale(1); }
}

.st-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 12px;
  color: #3a4a3a;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.st-btn:hover {
  background: #f0f0f0;
}

.st-btn:active {
  background: #dfe6df;
}

.st-divider {
  width: 1px;
  height: 20px;
  background: #e0e4e0;
  margin: 0 2px;
}

/* Dark theme for selection toolbar */
body.dark .selection-toolbar {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4), 0 1px 4px rgba(0,0,0,0.3);
}

body.dark .st-btn {
  color: #e5e5e5;
}

body.dark .st-btn:hover {
  background: #2d2d2d;
}

body.dark .st-btn:active {
  background: #333333;
}

body.dark .st-divider {
  background: #333333;
}
</style>
