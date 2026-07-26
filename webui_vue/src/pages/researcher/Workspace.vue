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
        v-for="(msg, idx) in visibleMessages"
        :key="idx"
        class="chat-msg"
        :class="msg.role"
      >
        <template v-if="msg.role === 'aux_group'">
          <div class="msg-avatar tool">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0"/>
              <path d="M3 12h4"/>
              <path d="M12 3v4"/>
              <circle cx="12" cy="12" r="1"/>
            </svg>
          </div>
          <div class="msg-body">
            <div class="aux-timeline-container">
              <div class="aux-timeline-line"></div>
              <div
                v-for="item in msg.items"
                :key="item.id || `${item.role}_${item.name || 'reasoning'}_${item.content?.length || 0}`"
                class="aux-timeline-node"
              >
                <div class="aux-node-dot" :class="item.role === 'tool' ? 'dot-tool' : 'dot-reasoning'">
                  <svg v-if="item.role === 'tool'" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                  </svg>
                  <svg v-else width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
                    <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
                    <path d="M12 5v14"/>
                  </svg>
                </div>
                <div class="aux-node-body">
                  <div class="aux-node-head">
                    <div class="aux-node-info">
                      <span class="aux-node-label font-mono">{{ item.role === 'tool' ? (item.name || 'tool') : 'reasoning' }}</span>
                      <span class="aux-node-preview">{{ getAuxPreview(item) }}</span>
                    </div>
                    <button
                      class="aux-expand-btn"
                      @click="item.collapsed = !item.collapsed"
                    >
                      <span>{{ item.collapsed ? '展开' : '收起' }}</span>
                      <svg :class="{ rotated: !item.collapsed }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m6 9 6 6 6-6"/>
                      </svg>
                    </button>
                  </div>
                  <div v-if="!item.collapsed" class="aux-node-detail">
                    <div class="aux-detail-header">
                      <span>🎯 Target Payload</span>
                      <span class="aux-detail-badge">{{ item.role === 'tool' ? (item.name || 'tool') : 'reasoning' }}</span>
                    </div>
                    <div class="aux-detail-content" v-html="renderMarkdown(item.content)"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
        <div class="msg-avatar" :class="msg.role">
          {{ msg.role === 'ai' ? 'AI' : '您' }}
        </div>
        <div class="msg-body">
          <div class="msg-mode-tag" v-if="msg.role === 'user' && msg.mode">
            {{ msg.mode === 'deep' ? '深度推理' : '快速响应' }}
          </div>
          <div class="msg-mode-tag tool-tag" v-if="msg.role === 'tool'">
            {{ msg.name || 'tool' }}
          </div>
          <div class="msg-mode-tag reasoning-tag" v-if="msg.reasoning">
            reasoning
          </div>
          <button
            v-if="isAuxiliaryMessage(msg)"
            class="collapse-toggle"
            @click="msg.collapsed = !msg.collapsed"
          >
            {{ msg.collapsed ? '展开' : '收起' }}
          </button>
          <div
            v-if="!msg.collapsed"
            class="msg-content"
            :class="{ auxiliary: isAuxiliaryMessage(msg) }"
            v-html="renderMarkdown(msg.content)"
          ></div>
          <div class="msg-loading" v-if="msg.loading">
            <span class="dot-pulse"></span>
          </div>
          <!-- Save to research results button -->
          <button
            v-if="msg.role === 'ai' && !msg.loading && !msg.reasoning && msg.content && !isAuxiliaryMessage(msg)"
            class="save-result-btn"
            :class="{ saved: msg.saved }"
            @click="saveToResults(msg)"
            :title="msg.saved ? '已保存到研究成果' : '保存到研究成果'"
          >
            <svg v-if="!msg.saved" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            <span>{{ msg.saved ? '已保存' : '保存' }}</span>
          </button>
        </div>
        </template>
      </div>
    </div>

    <div v-if="clarificationPending && !clarificationReady" class="clarification-loading">
      <span class="dot-pulse"></span>
      <span>正在分析问题维度并生成澄清问卷...</span>
    </div>

    <div v-if="showClarificationForm" class="clarification-panel">
      <div class="clarification-head">
        <div class="clarification-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
          </svg>
        </div>
        <div>
          <h2>开始前，请确认几个关键点</h2>
          <p>模型已完成初步维度判断，请用选择与填空补充研究边界。</p>
        </div>
      </div>

      <div class="clarification-block">
        <label>你的需求</label>
        <div class="original-question">{{ originalDeepQuestion }}</div>
      </div>

      <div class="clarification-block">
        <label>模型维度判断</label>
        <div class="model-analysis" v-html="renderMarkdown(clarificationQuestion)"></div>
      </div>

      <div
        v-for="question in clarificationSchema.questions"
        :key="question.id"
        class="clarification-block"
      >
        <label>{{ question.label }}</label>
        <p v-if="question.help" class="field-help">{{ question.help }}</p>

        <div v-if="question.type === 'single'" class="option-row">
          <button
            v-for="option in question.options"
            :key="option.value"
            class="choice-chip"
            :class="{ selected: clarificationAnswers[question.id] === option.value }"
            @click="clarificationAnswers[question.id] = option.value"
          >
            {{ option.label }}
          </button>
        </div>

        <div v-else-if="question.type === 'multi'" class="option-row">
          <button
            v-for="option in question.options"
            :key="option.value"
            class="choice-chip"
            :class="{ selected: isDynamicOptionSelected(question.id, option.value) }"
            @click="toggleDynamicOption(question.id, option.value)"
          >
            {{ option.label }}
          </button>
        </div>

        <div v-else-if="question.type === 'textarea'">
          <textarea
            v-model="clarificationAnswers[question.id]"
            rows="3"
            :placeholder="question.placeholder || '请补充说明'"
          ></textarea>
        </div>

        <div v-else class="inline-input">
          <input
            v-model="clarificationAnswers[question.id]"
            type="text"
            :placeholder="question.placeholder || '请填写'"
          />
        </div>
      </div>

      <div class="clarification-actions">
        <button class="secondary-action" @click="submitClarificationForm(true)" :disabled="sending">按模型判断继续</button>
        <button class="primary-action" @click="submitClarificationForm(false)" :disabled="sending">
          <span v-if="!sending">开启分布式深度研究</span>
          <span v-else class="btn-spinner dark"></span>
        </button>
      </div>
    </div>

    <!-- 搜索与对话容器 -->
    <div v-if="!showClarificationForm" class="search-container" :class="{ focused: isFocused }">
      <textarea
        v-model="query"
        class="search-textarea"
        :placeholder="messages.length > 0 ? '继续提问...' : '输入您正在跟进的课题方向，或者上传文献进行深度交叉论证... 例如：探究存算一体架构（PIM）在端侧大模型部署中的能效比与潜在技术瓶颈。'"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keydown.enter.exact.prevent="handleSubmit"
      ></textarea>

      <div v-if="workspaceAttachments.length" class="attachment-strip">
        <div
          v-for="attachment in workspaceAttachments"
          :key="attachment.id"
          class="attachment-chip"
          :class="attachment.parseStatus"
        >
          <span class="attachment-name">{{ attachment.fileName }}</span>
          <span class="attachment-status">{{ attachment.parseStatus === 'ready' ? '已入库' : attachment.parseStatus }}</span>
          <button @click="removeAttachment(attachment.id)" title="移除本轮上下文">×</button>
        </div>
      </div>

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
          <input
            ref="fileInputRef"
            type="file"
            class="hidden-file-input"
            accept=".pdf,.txt,.md,.csv,.xlsx,.xls,.docx"
            @change="handleFileSelected"
          />
          <button class="upload-btn" title="上传外部数据集 / PDF 文献" @click="triggerAttachmentUpload" :disabled="uploadingAttachment">
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

  <Teleport to="body">
    <div v-if="saveDialogOpen" class="save-dialog-overlay" @click.self="closeSaveDialog">
      <div class="save-dialog-card">
        <div class="save-dialog-header">
          <h3>???????</h3>
          <button @click="closeSaveDialog">?</button>
        </div>
        <div class="save-dialog-body">
          <label>??</label>
          <input v-model="saveForm.title" type="text" />
          <label>????</label>
          <input v-model="saveForm.projectName" type="text" placeholder="????????????" />
          <label>??</label>
          <input v-model="saveForm.tagsText" type="text" placeholder="??????? PIM, ??, ??" />
          <label>????</label>
          <div class="save-attachment-list" v-if="workspaceAttachments.length">
            <span v-for="item in workspaceAttachments" :key="item.id">{{ item.fileName }}</span>
          </div>
          <p v-else class="save-muted">??????????</p>
        </div>
        <div class="save-dialog-footer">
          <button class="secondary-action" @click="closeSaveDialog">??</button>
          <button class="primary-action" @click="confirmSaveResult" :disabled="savingResult">{{ savingResult ? '???...' : '??' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useSessions } from '../../composables/useSessions.js'
import { useResearchResults } from '../../composables/useResearchResults.js'
import { useResearchWorkspace } from '../../composables/useResearchWorkspace.js'

marked.setOptions({ breaks: true, gfm: true })
marked.use(markedKatex({
  throwOnError: false,
  output: 'html',
  nonStandard: true,
}))

const router = useRouter()
const { user } = useAuth()
const { sendMessage, sendResearcherClarification, onChat, getChatId, getToken, currentChatId } = useGateway()
const { fetchSessionMessages } = useSessions()
const { saveResult } = useResearchResults()
const { projects, attachments, uploadingAttachment, fetchProjects, fetchAttachments, uploadAttachment } = useResearchWorkspace()

const query = ref('')
const isFocused = ref(false)
const chatMode = ref('quick')
const sending = ref(false)
const messages = ref([])
const chatAreaRef = ref(null)
const fileInputRef = ref(null)
const workspaceAttachments = ref([])
const saveDialogOpen = ref(false)
const savingResult = ref(false)
const saveTargetMessage = ref(null)
const saveForm = ref({ title: '', projectName: '', tagsText: '' })
const clarificationPending = ref(false)
const originalDeepQuestion = ref('')
const clarificationQuestion = ref('')
const clarificationReady = ref(false)
const clarificationSchema = ref(createFallbackClarificationSchema())
const clarificationAnswers = ref({})
let unsubChat = null
let subscribedChatId = null
let activeStreamId = null
let activeAiMessageId = null
let historyLoadSeq = 0
let clarificationStreamText = ''
let restoringClarification = false
let activeClarificationRequestId = null
let clarificationTimeoutTimer = null

const userName = computed(() => user.value?.userId || '研究员')
const showClarificationForm = computed(() => clarificationPending.value && clarificationReady.value)
const visibleMessages = computed(() => {
  const grouped = []
  let activeGroup = null

  messages.value.forEach((message, index) => {
    if (isAuxiliaryMessage(message)) {
      if (!activeGroup) {
        activeGroup = {
          role: 'aux_group',
          items: [],
        }
        grouped.push(activeGroup)
      }
      activeGroup.items.push(message)
      return
    }

    activeGroup = null
    grouped.push(message)
  })

  return grouped
})

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

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function saveToResults(msg) {
  if (msg.saved) return
  saveTargetMessage.value = msg
  saveForm.value = {
    title: extractResultTitle(msg.content),
    projectName: '',
    tagsText: '',
  }
  saveDialogOpen.value = true
}

function closeSaveDialog() {
  saveDialogOpen.value = false
  saveTargetMessage.value = null
}

async function confirmSaveResult() {
  const msg = saveTargetMessage.value
  if (!msg || savingResult.value) return
  savingResult.value = true
  try {
    const payload = {
      title: saveForm.value.title || extractResultTitle(msg.content),
      content: msg.content,
      chat_id: currentChatId.value || getChatId(),
      session_title: originalDeepQuestion.value || '',
      sourceMessageId: msg.id || '',
      projectName: saveForm.value.projectName.trim(),
      tags: parseTags(saveForm.value.tagsText),
      sections: extractStructuredSections(msg.content),
      attachments: workspaceAttachments.value.map(item => ({
        id: item.id,
        fileName: item.fileName,
        fileType: item.fileType,
        summary: item.summary,
      })),
      citations: buildAttachmentCitations(),
      metadata: { savedFrom: 'researcher_workspace' },
    }
    const result = await saveResult(payload)
    if (result) {
      msg.saved = true
      closeSaveDialog()
    }
  } finally {
    savingResult.value = false
  }
}

function parseTags(text) {
  return String(text || '').split(/[,?]/).map(t => t.trim()).filter(Boolean)
}

function extractResultTitle(content) {
  const firstHeading = String(content || '').split('\n').find(line => line.trim().replace(/^#+\s*/, '').length > 4)
  return (firstHeading || '???????').replace(/^#+\s*/, '').replace(/[\*`]/g, '').slice(0, 80)
}

function extractStructuredSections(content) {
  const lines = String(content || '').split('\n')
  const sections = []
  let current = { key: 'summary', title: '??', content: '' }
  for (const line of lines) {
    const match = line.match(/^#{1,3}\s+(.+)$/)
    if (match) {
      if (current.content.trim()) sections.push({ ...current, content: current.content.trim(), sortOrder: sections.length })
      const title = match[1].trim()
      current = { key: title.toLowerCase().replace(/\s+/g, '_'), title, content: '' }
    } else {
      current.content += line + '\n'
    }
  }
  if (current.content.trim()) sections.push({ ...current, content: current.content.trim(), sortOrder: sections.length })
  return sections
}

function buildAttachmentCitations() {
  return workspaceAttachments.value.map(item => ({
    attachmentId: item.id,
    sourceName: item.fileName,
    evidenceText: item.summary || '',
  }))
}

function triggerAttachmentUpload() {
  fileInputRef.value?.click()
}

async function handleFileSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  const attachment = await uploadAttachment(file, {
    chatId: currentChatId.value || getChatId(),
  })
  if (attachment) {
    workspaceAttachments.value.unshift(attachment)
  }
}

function removeAttachment(id) {
  workspaceAttachments.value = workspaceAttachments.value.filter(item => item.id !== id)
}

function buildWorkspaceContextMeta() {
  return {
    attachments: workspaceAttachments.value.map(item => ({
      id: item.id,
      fileName: item.fileName,
      fileType: item.fileType,
      summary: item.summary,
      parseStatus: item.parseStatus,
    })),
    output_template: chatMode.value === 'deep' ? 'research_deep_v1' : undefined,
  }
}

function applyClarificationFallback(reason = '??????????????????') {
  if (!clarificationPending.value || clarificationReady.value) return
  clarificationQuestion.value = reason
  clarificationSchema.value = createFallbackClarificationSchema()
  clarificationAnswers.value = createAnswersFromSchema(clarificationSchema.value)
  clarificationReady.value = true
  sending.value = false
  activeClarificationRequestId = null
  saveClarificationDraft()
}

function startClarificationTimeout() {
  if (clarificationTimeoutTimer) clearTimeout(clarificationTimeoutTimer)
  clarificationTimeoutTimer = setTimeout(() => {
    applyClarificationFallback('?????? 30 ???????????????')
  }, 30000)
}

function clearClarificationTimeout() {
  if (clarificationTimeoutTimer) {
    clearTimeout(clarificationTimeoutTimer)
    clarificationTimeoutTimer = null
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

function getClarificationStorageKey(chatId = currentChatId.value || getChatId()) {
  return chatId ? `researcher:clarification:${chatId}` : null
}

function saveClarificationDraft() {
  if (restoringClarification) return
  const key = getClarificationStorageKey()
  if (!key || !clarificationPending.value) return
  try {
    localStorage.setItem(key, JSON.stringify({
      originalDeepQuestion: originalDeepQuestion.value,
      clarificationQuestion: clarificationQuestion.value,
      clarificationReady: clarificationReady.value,
      clarificationSchema: clarificationSchema.value,
      clarificationAnswers: clarificationAnswers.value,
    }))
  } catch (err) {
    console.warn('Failed to save clarification draft:', err)
  }
}

function clearClarificationDraft(chatId = currentChatId.value || getChatId()) {
  const key = getClarificationStorageKey(chatId)
  if (!key) return
  try {
    localStorage.removeItem(key)
  } catch (err) {
    console.warn('Failed to clear clarification draft:', err)
  }
}

function restoreClarificationDraft(chatId = currentChatId.value || getChatId()) {
  const key = getClarificationStorageKey(chatId)
  if (!key) return false
  let draft = null
  try {
    draft = JSON.parse(localStorage.getItem(key) || 'null')
  } catch {
    clearClarificationDraft(chatId)
    return false
  }
  if (!draft?.originalDeepQuestion || !draft?.clarificationReady || !draft?.clarificationSchema?.questions?.length) {
    return false
  }

  restoringClarification = true
  clarificationPending.value = true
  originalDeepQuestion.value = draft.originalDeepQuestion
  clarificationQuestion.value = draft.clarificationQuestion || draft.clarificationSchema.analysis || ''
  clarificationReady.value = true
  clarificationSchema.value = normalizeClarificationSchema(draft.clarificationSchema)
  clarificationAnswers.value = draft.clarificationAnswers || createAnswersFromSchema(clarificationSchema.value)
  clarificationStreamText = ''
  if (!messages.value.some(m => m.role === 'user' && m.content === originalDeepQuestion.value)) {
    messages.value.push({ role: 'user', content: originalDeepQuestion.value, mode: 'deep' })
  }
  restoringClarification = false
  return true
}

function createFallbackClarificationSchema() {
  return {
    analysis: '模型未返回可解析的澄清表单，已切换到通用澄清表单。',
    questions: [
      {
        id: 'accuracy',
        type: 'single',
        label: '模型对研究对象和领域的判断是否准确？',
        options: [
          { label: '准确，继续', value: '准确，继续' },
          { label: '大致准确，下方补充', value: '大致准确，下方补充' },
          { label: '不准确，我来修正', value: '不准确，我来修正' },
        ],
        defaultValue: '准确，继续',
      },
      {
        id: 'focus',
        type: 'multi',
        label: '本次研究最看重哪些维度？',
        options: [
          { label: '技术路线', value: '技术路线' },
          { label: '功能对比', value: '功能对比' },
          { label: '文献脉络', value: '文献脉络' },
          { label: '实验设计', value: '实验设计' },
        ],
        defaultValue: ['技术路线', '文献脉络'],
      },
      {
        id: 'targets',
        type: 'text',
        label: '需要重点比较或纳入的对象',
        placeholder: '论文、方法、工具、数据集、竞品等',
        defaultValue: '',
      },
      {
        id: 'scope',
        type: 'textarea',
        label: '范围约束与补充说明',
        placeholder: '时间范围、应用场景、评价指标、排除项等',
        defaultValue: '',
      },
    ],
  }
}

function buildClarificationRequest(question) {
  return [
    '你正在处理研究者深度模式请求。当前阶段不是回答问题，而是根据用户原始问题进行意图识别和问题澄清。',
    '',
    `用户原始问题：${question}`,
    '',
    '请先分析这个问题可能涉及的关键维度，再生成一个用于前端渲染的动态澄清表单。',
    '',
    '严格只输出一个 JSON 对象，不要使用 Markdown，不要加解释文字。',
    'JSON 结构如下：',
    '{',
    '  "analysis": "用中文概括你识别到的研究对象、领域/方向、潜在比较对象、关键维度、产出类型和不确定点。不要直接回答原问题。",',
    '  "questions": [',
    '    {',
    '      "id": "short_snake_case_id",',
    '      "type": "single | multi | text | textarea",',
    '      "label": "面向用户的澄清问题",',
    '      "help": "可选，解释为什么需要这个信息",',
    '      "placeholder": "可选，text/textarea 的占位提示",',
    '      "options": [{"label": "选项文本", "value": "选项值"}],',
    '      "defaultValue": "默认值；multi 类型使用字符串数组"',
    '    }',
    '  ]',
    '}',
    '',
    '问题生成要求：',
    '1. questions 必须包含 4-7 个问题。',
    '2. 至少包含 1 个 single、1 个 multi、1 个 text 或 textarea。',
    '3. 所有选项都必须根据用户原始问题动态生成，不要使用通用固定选项。',
    '4. 问题需要覆盖：研究对象/领域确认、范围边界、重点维度、比较对象或资料约束、期望产出。',
    '5. 如果原问题涉及具体工具、论文、模型、方法或数据集，选项中要体现这些实体及合理候选项。'
  ].join('\n')
}

function extractJsonObject(text) {
  if (!text) return null
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  const raw = fenced ? fenced[1] : text
  const start = raw.indexOf('{')
  const end = raw.lastIndexOf('}')
  if (start < 0 || end <= start) return null
  try {
    return JSON.parse(raw.slice(start, end + 1))
  } catch {
    return null
  }
}

function normalizeOption(option, index) {
  if (typeof option === 'string') {
    return { label: option, value: option }
  }
  const label = String(option?.label || option?.value || `选项 ${index + 1}`)
  return { label, value: String(option?.value || label) }
}

function normalizeQuestion(question, index) {
  const allowedTypes = new Set(['single', 'multi', 'text', 'textarea'])
  const type = allowedTypes.has(question?.type) ? question.type : 'text'
  const id = String(question?.id || `question_${index + 1}`).replace(/[^\w-]/g, '_')
  const normalized = {
    id,
    type,
    label: String(question?.label || `澄清问题 ${index + 1}`),
    help: question?.help ? String(question.help) : '',
    placeholder: question?.placeholder ? String(question.placeholder) : '',
    options: Array.isArray(question?.options) ? question.options.map(normalizeOption) : [],
    defaultValue: question?.defaultValue,
  }
  if ((type === 'single' || type === 'multi') && normalized.options.length === 0) {
    normalized.type = 'text'
  }
  return normalized
}

function normalizeClarificationSchema(schema) {
  const fallback = createFallbackClarificationSchema()
  if (!schema || !Array.isArray(schema.questions)) return fallback
  const questions = schema.questions.slice(0, 7).map(normalizeQuestion)
  if (!questions.length) return fallback
  return {
    analysis: String(schema.analysis || fallback.analysis),
    questions,
  }
}

function createAnswersFromSchema(schema) {
  const answers = {}
  for (const question of schema.questions) {
    if (question.type === 'multi') {
      answers[question.id] = Array.isArray(question.defaultValue)
        ? [...question.defaultValue]
        : []
    } else if (question.type === 'single') {
      answers[question.id] = question.defaultValue || question.options[0]?.value || ''
    } else {
      answers[question.id] = question.defaultValue || ''
    }
  }
  return answers
}

function applyClarificationResponse(text) {
  const schema = normalizeClarificationSchema(extractJsonObject(text))
  applyClarificationSchema(schema)
}

function applyClarificationSchema(schema) {
  schema = normalizeClarificationSchema(schema)
  clarificationSchema.value = schema
  clarificationAnswers.value = createAnswersFromSchema(schema)
  clarificationQuestion.value = schema.analysis
  clarificationReady.value = true
  saveClarificationDraft()
}

function captureClarificationQuestion() {
  const lastAi = [...messages.value].reverse().find(m => m.role === 'ai' && !m.loading && m.content)
  clarificationQuestion.value = lastAi?.content || ''
}

function resetClarificationState({ clearDraft = false } = {}) {
  clearClarificationTimeout()
  if (clearDraft) clearClarificationDraft()
  clarificationPending.value = false
  originalDeepQuestion.value = ''
  clarificationQuestion.value = ''
  clarificationReady.value = false
  clarificationSchema.value = createFallbackClarificationSchema()
  clarificationAnswers.value = {}
  clarificationStreamText = ''
}

function isDynamicOptionSelected(questionId, value) {
  const answer = clarificationAnswers.value[questionId]
  return Array.isArray(answer) && answer.includes(value)
}

function toggleDynamicOption(questionId, value) {
  if (!Array.isArray(clarificationAnswers.value[questionId])) {
    clarificationAnswers.value[questionId] = []
  }
  const answer = clarificationAnswers.value[questionId]
  const idx = answer.indexOf(value)
  if (idx >= 0) {
    answer.splice(idx, 1)
  } else {
    answer.push(value)
  }
  saveClarificationDraft()
}

function buildFormClarificationText(useModelJudgment = false) {
  if (useModelJudgment) return '按你的判断继续'

  const lines = []
  for (const question of clarificationSchema.value.questions) {
    const answer = clarificationAnswers.value[question.id]
    const answerText = Array.isArray(answer)
      ? (answer.length ? answer.join('、') : '未选择')
      : (String(answer || '').trim() || '未填写')
    lines.push(`${question.label}：${answerText}`)
  }
  return lines.join('\n')
}

function submitClarificationForm(useModelJudgment = false) {
  if (!clarificationPending.value || sending.value) return
  const text = buildFormClarificationText(useModelJudgment)
  query.value = text
  handleSubmit()
}

function buildLegacyClarifiedQuestion(originalQuestion, clarification) {
  const normalizedClarification = clarification.trim()
  if (!normalizedClarification || /^(不补充|无需补充|没有|无|按现有信息继续)$/i.test(normalizedClarification)) {
    return [
      '深度模式研究请求',
      '',
      `原始问题：${originalQuestion}`,
      '',
      '用户未补充额外澄清信息。请先基于现有问题明确合理假设，再进行深度推理、交叉验证和结构化回答。'
    ].join('\n')
  }

  return [
    '深度模式研究请求',
    '',
    `原始问题：${originalQuestion}`,
    '',
    `用户澄清：${normalizedClarification}`,
    '',
    '请综合原始问题与澄清信息，先界定研究范围和假设，再进行深度推理、交叉验证和结构化回答。'
  ].join('\n')
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
      messages.value.push({ id: activeAiMessageId, streamId, role: 'ai', content: '', loading: true, hidden: clarificationPending.value })
    }
  }

  let msg = messages.value.find(m => m.id === activeAiMessageId)
  if (!msg) {
    msg = { id: activeAiMessageId, streamId, role: 'ai', content: '', loading: true, hidden: clarificationPending.value }
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
    if (ev.event === 'researcher_clarification') {
      if (ev.request_id && activeClarificationRequestId && ev.request_id !== activeClarificationRequestId) return
      clearClarificationTimeout()
      applyClarificationSchema({
        analysis: ev.analysis,
        questions: ev.questions,
      })
      sending.value = false
      activeClarificationRequestId = null
      scrollToBottom()
    } else if (ev.event === 'delta') {
      if (clarificationPending.value && !clarificationReady.value) {
        clarificationStreamText += ev.text || ''
        return
      }
      const msg = upsertStreamingAiMessage(ev)
      msg.content += ev.text || ''
      msg.loading = true
      scrollToBottom()
    } else if (ev.event === 'stream_end') {
      if (clarificationPending.value && !clarificationReady.value) {
        clearClarificationTimeout()
        applyClarificationResponse(clarificationStreamText)
        sending.value = false
        activeStreamId = null
        activeAiMessageId = null
        scrollToBottom()
        return
      }
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
      if (ev.kind === 'trace') {
        appendRealtimeTrace(ev)
        scrollToBottom()
        return
      }
      if (clarificationPending.value && !clarificationReady.value) {
        clearClarificationTimeout()
        applyClarificationResponse(text)
        sending.value = false
        activeStreamId = null
        activeAiMessageId = null
        scrollToBottom()
        return
      }
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

  const isClarificationReply = clarificationPending.value
  const mode = isClarificationReply ? 'deep' : chatMode.value

  // In deep mode the first prompt is collected before the formal chat turn.
  // Keep the visible/persisted user message anchored to that original prompt.
  const visibleUserText = isClarificationReply
    ? (originalDeepQuestion.value || text)
    : text
  const userMsg = { role: 'user', content: visibleUserText, mode }
  if (isClarificationReply) {
    const hasOriginalUserMessage = messages.value.some(message =>
      message.role === 'user' && message.content === visibleUserText
    )
    if (!hasOriginalUserMessage) {
      messages.value.push(userMsg)
    }
  } else {
    messages.value.push(userMsg)
  }
  query.value = ''
  scrollToBottom()

    if (mode === 'deep' && !isClarificationReply) {
      clarificationPending.value = true
      originalDeepQuestion.value = text
      clarificationQuestion.value = ''
      clarificationReady.value = false
      clarificationSchema.value = createFallbackClarificationSchema()
      clarificationAnswers.value = {}
      clarificationStreamText = ''
      activeClarificationRequestId = `clarify_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      saveClarificationDraft()
    }

  sending.value = true

  // Add AI placeholder, except for hidden clarification-schema generation.
  if (!(mode === 'deep' && !isClarificationReply)) {
    messages.value.push({ role: 'ai', content: '', loading: true })
    scrollToBottom()
  }

  // Ensure we're listening for responses
  ensureChatListener()

  try {
    // Send message with mode in meta (not displayed in chat)
    if (isClarificationReply && !clarificationQuestion.value) {
      captureClarificationQuestion()
    }
    if (mode === 'deep' && !isClarificationReply) {
      startClarificationTimeout()
      sendResearcherClarification(text, activeClarificationRequestId)
      return
    }

    const outgoingText = text
    const outgoingMeta = isClarificationReply
      ? {
          mode: 'deep',
          phase: 'clarified',
          original_question: originalDeepQuestion.value,
          display_content: originalDeepQuestion.value,
          clarification_answers: text,
          model_clarification: clarificationQuestion.value,
          clarification_schema: clarificationSchema.value,
          ...buildWorkspaceContextMeta(),
        }
      : mode === 'deep'
        ? { mode: 'deep', phase: 'clarifying', original_question: text, ...buildWorkspaceContextMeta() }
        : { mode, ...buildWorkspaceContextMeta() }

    if (isClarificationReply) {
      resetClarificationState({ clearDraft: true })
    }

    sendMessage(outgoingText, outgoingMeta)
  } catch (err) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'ai') {
      last.content = '⚠️ 发送失败：' + (err.message || '未连接到 Gateway')
      last.loading = false
    } else if (mode === 'deep' && !isClarificationReply) {
      messages.value.push({ role: 'ai', content: '澄清问卷生成失败：' + (err.message || '未连接到 Gateway'), loading: false })
      resetClarificationState()
    }
    sending.value = false
    if (isClarificationReply) {
      clarificationPending.value = true
    }
  }
}

function stringifySessionContent(value) {
  if (typeof value === 'string') return value
  if (value == null) return ''
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function truncateMessageText(text, maxLength = 800) {
  const normalized = String(text || '').trim()
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, maxLength)}...`
}

function formatToolCalls(toolCalls) {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) return 'Tool calls'
  const lines = ['Tool calls:']
  toolCalls.forEach((call, index) => {
    const fn = call?.function || {}
    const name = fn.name || call?.name || 'tool'
    const args = fn.arguments || call?.arguments || ''
    lines.push(`${index + 1}. ${name}`)
    if (args) lines.push(typeof args === 'string' ? args : stringifySessionContent(args))
  })
  return lines.join('\n')
}

function normalizeAuxiliaryMessage(message) {
  if (!message) return null
  if (message.role === 'tool') {
    return {
      role: 'tool',
      name: message.name || 'tool',
      content: stringifySessionContent(message.content),
      collapsed: message.collapsed ?? false,
      loading: false,
    }
  }
  if (message.reasoning) {
    return {
      role: 'ai',
      content: stringifySessionContent(message.content),
      reasoning: true,
      collapsed: message.collapsed ?? false,
      loading: false,
      mode: message.mode || null,
    }
  }
  return message
}

function isAuxiliaryMessage(msg) {
  return msg?.role === 'tool' || !!msg?.reasoning
}

function getAuxPreview(item) {
  const text = String(item?.content || '').replace(/\n/g, ' ').trim()
  if (!text) return ''
  return text.length > 60 ? text.slice(0, 60) + '...' : text
}

function mapSessionMessage(m) {
  if (m.role === 'user') {
    return [{
      role: 'user',
      content: stringifySessionContent(m.metadata?.display_content || m.content),
      loading: false,
      mode: m.metadata?.mode || null,
    }]
  }

  if (m.role === 'assistant') {
    const content = stringifySessionContent(m.content).trim()
    const reasoning = stringifySessionContent(m.reasoning_content).trim()
    if (!content && !reasoning && !m.tool_calls?.length) return null
    const mapped = []
    if (reasoning) {
      mapped.push(normalizeAuxiliaryMessage({
        role: 'ai',
        content: reasoning,
        reasoning: true,
        collapsed: false,
        loading: false,
        mode: m.metadata?.mode || null,
      }))
    }
    if (!content && m.tool_calls?.length) {
      mapped.push(normalizeAuxiliaryMessage({
        role: 'ai',
        content: formatToolCalls(m.tool_calls),
        reasoning: true,
        collapsed: false,
        loading: false,
        mode: m.metadata?.mode || null,
      }))
    } else if (content || !reasoning) {
      mapped.push({
        role: 'ai',
        content,
        reasoning: false,
        collapsed: false,
        loading: false,
        mode: m.metadata?.mode || null,
      })
    }
    return mapped
  }

  if (m.role === 'tool') {
    return [normalizeAuxiliaryMessage({
      role: 'tool',
      name: m.name || 'tool',
      content: truncateMessageText(stringifySessionContent(m.content), 600),
      collapsed: false,
      loading: false,
    })]
  }

  return null
}

function promoteFallbackAnswers(mappedMessages) {
  let segmentStart = 0

  const promoteInSegment = (start, end) => {
    let hasAnswer = false
    let lastReasoning = null
    for (let i = start; i < end; i++) {
      const message = mappedMessages[i]
      if (!message) continue
      if (message.role === 'ai' && !message.reasoning) {
        hasAnswer = true
      } else if (message.role === 'ai' && message.reasoning) {
        lastReasoning = message
      }
    }
    if (!hasAnswer && lastReasoning) {
      lastReasoning.reasoning = false
      lastReasoning.collapsed = false
    }
  }

  for (let i = 0; i < mappedMessages.length; i++) {
    if (mappedMessages[i]?.role === 'user') {
      promoteInSegment(segmentStart, i)
      segmentStart = i + 1
    }
  }
  promoteInSegment(segmentStart, mappedMessages.length)
  return mappedMessages
}

function appendRealtimeTrace(ev) {
  const text = ev.text || ev.content || ''
  if (!text) return
  if (ev.role === 'tool') {
    messages.value.push(normalizeAuxiliaryMessage({
      role: 'tool',
      name: ev.name || 'tool',
      content: text,
      collapsed: false,
      loading: false,
    }))
    return
  }
  if (ev.reasoning) {
    const last = messages.value[messages.value.length - 1]
    if (last?.role === 'ai' && last.reasoning) {
      if (text === last.content || last.content.endsWith(text)) return
      if (text.startsWith(last.content)) {
        last.content = text
      } else {
        last.content += text
      }
      last.collapsed = false
      return
    }
  }
  messages.value.push(normalizeAuxiliaryMessage({
    role: 'ai',
    content: text,
    reasoning: !!ev.reasoning,
    collapsed: false,
    loading: false,
  }))
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
        .filter(m => m.role === 'user' || m.role === 'assistant' || m.role === 'tool')
        .filter(m => m.metadata?.phase !== 'clarifying')
        .flatMap(m => mapSessionMessage(m) || [])
        .filter(Boolean)
      history = promoteFallbackAnswers(history)
    }
  } catch (err) {
    // Silently ignore — fresh session
  }
  if (seq !== historyLoadSeq || chatId !== (currentChatId.value || getChatId())) return
  messages.value = history
  resetClarificationState()
  restoreClarificationDraft(chatId)
  scrollToBottom()
  // Always register chat listener for live messages
  ensureChatListener(chatId)
}

onMounted(async () => {
  fetchProjects().catch(() => {})
  const chatId = currentChatId.value || getChatId()
  if (chatId) {
    await loadHistory(chatId)
    fetchAttachments(chatId).then(items => { workspaceAttachments.value = items || [] }).catch(() => {})
  }
})

watch(currentChatId, async (chatId, oldChatId) => {
  if (!chatId || chatId === oldChatId) return
  stopChatListener()
  sending.value = false
  resetClarificationState()
  await loadHistory(chatId)
  fetchAttachments(chatId).then(items => { workspaceAttachments.value = items || [] }).catch(() => {})
}, { immediate: false })

watch(clarificationAnswers, () => {
  if (clarificationPending.value && clarificationReady.value) {
    saveClarificationDraft()
  }
}, { deep: true })

onBeforeUnmount(() => {
  clearClarificationTimeout()
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

.msg-avatar.tool {
  background: #121212;
  color: #fff;
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

.tool-tag {
  color: #121212;
  background: #f4f4f4;
  border-color: #eaeaea;
}

.reasoning-tag {
  color: #7a5b00;
  background: #fff7df;
  border-color: #f3df9f;
}

.collapse-toggle {
  border: none;
  background: transparent;
  color: #777777;
  font-size: 11px;
  line-height: 1;
  padding: 0;
  margin: 0 0 6px 8px;
  cursor: pointer;
  font-family: inherit;
}

.collapse-toggle:hover {
  color: #121212;
}

.msg-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.msg-content.auxiliary {
  font-size: 12px;
  line-height: 1.6;
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

.chat-msg.tool .msg-content {
  background: #f8f8f8;
  border: 1px solid #eaeaea;
  color: #121212;
  border-top-left-radius: 4px;
  font-size: 12px;
}

/* Save to research results button */
.save-result-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px 10px;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  background: white;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.save-result-btn:hover {
  border-color: #121212;
  color: #121212;
  background: #f8f8f8;
}

.save-result-btn.saved {
  border-color: #526e5a;
  color: #526e5a;
  background: #f0f7f1;
  cursor: default;
}

.save-result-btn.saved:hover {
  background: #f0f7f1;
}

.chat-msg.aux_group .msg-body {
  max-width: 85%;
}

/* Timeline container */
.aux-timeline-container {
  position: relative;
  background: #fafbfa;
  border: 1px solid #edf0ed;
  border-radius: 16px;
  border-top-left-radius: 4px;
  padding: 16px 16px 16px 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.001);
}

.aux-timeline-line {
  position: absolute;
  left: 30px;
  top: 24px;
  bottom: 24px;
  width: 1px;
  background: #d4d4d4;
}

/* Timeline node */
.aux-timeline-node {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 6px 0;
}

.aux-timeline-node + .aux-timeline-node {
  margin-top: 4px;
}

/* Node dot */
.aux-node-dot {
  position: relative;
  z-index: 1;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.aux-node-dot.dot-tool {
  background: #fff;
  border: 1.5px solid #121212;
  color: #121212;
}

.aux-node-dot.dot-reasoning {
  background: #fff;
  border: 1.5px solid #121212;
  color: #121212;
}

/* Node body */
.aux-node-body {
  flex: 1;
  min-width: 0;
}

.aux-node-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.aux-node-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.aux-node-label {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  white-space: nowrap;
  font-family: 'Courier New', monospace;
}

.aux-node-preview {
  font-size: 11px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.aux-expand-btn {
  border: none;
  background: transparent;
  color: #999;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0;
  white-space: nowrap;
  font-family: inherit;
  transition: color 0.2s;
}

.aux-expand-btn:hover {
  color: #121212;
}

.aux-expand-btn svg {
  transition: transform 0.2s ease;
}

.aux-expand-btn svg.rotated {
  transform: rotate(180deg);
}

/* Expanded detail panel */
.aux-node-detail {
  margin-top: 8px;
  background: #fff;
  border: 1px solid #edf0ed;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.002);
}

.aux-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 10px;
  color: #999;
  border-bottom: 1px solid #f5f5f5;
  font-family: 'Courier New', monospace;
}

.aux-detail-badge {
  font-size: 9px;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 4px;
  color: #666;
}

.aux-detail-content {
  padding: 12px;
  font-size: 12px;
  line-height: 1.7;
  color: #333;
  max-height: 300px;
  overflow-y: auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.msg-content :deep(p),
.aux-detail-content :deep(p) {
  margin: 0 0 10px;
}

.msg-content :deep(p:last-child),
.aux-detail-content :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-content :deep(h1),
.msg-content :deep(h2),
.msg-content :deep(h3),
.msg-content :deep(h4),
.aux-detail-content :deep(h1),
.aux-detail-content :deep(h2),
.aux-detail-content :deep(h3),
.aux-detail-content :deep(h4) {
  margin: 16px 0 8px;
  font-weight: 600;
  line-height: 1.4;
}

.msg-content :deep(h1),
.aux-detail-content :deep(h1) { font-size: 1.3em; }
.msg-content :deep(h2),
.aux-detail-content :deep(h2) { font-size: 1.15em; }
.msg-content :deep(h3),
.aux-detail-content :deep(h3) { font-size: 1.05em; }

.msg-content :deep(ul),
.msg-content :deep(ol),
.aux-detail-content :deep(ul),
.aux-detail-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.msg-content :deep(li),
.aux-detail-content :deep(li) {
  margin: 4px 0;
}

.msg-content :deep(code),
.aux-detail-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Courier New', monospace;
}

.msg-content :deep(pre),
.aux-detail-content :deep(pre) {
  background: #1a1a1a;
  color: #e5e5e5;
  border-radius: 10px;
  padding: 14px 16px;
  margin: 10px 0;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
}

.msg-content :deep(pre code),
.aux-detail-content :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
  color: inherit;
  font-size: inherit;
}

.msg-content :deep(blockquote),
.aux-detail-content :deep(blockquote) {
  border-left: 3px solid #d4d4d4;
  margin: 10px 0;
  padding: 4px 12px;
  color: #666;
}

.msg-content :deep(table),
.aux-detail-content :deep(table) {
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 13px;
  width: 100%;
}

.msg-content :deep(th),
.msg-content :deep(td),
.aux-detail-content :deep(th),
.aux-detail-content :deep(td) {
  border: 1px solid #eaeaea;
  padding: 6px 10px;
  text-align: left;
}

.msg-content :deep(th),
.aux-detail-content :deep(th) {
  background: #f4f4f4;
  font-weight: 600;
}

.msg-content :deep(hr),
.aux-detail-content :deep(hr) {
  border: none;
  border-top: 1px solid #eaeaea;
  margin: 14px 0;
}

.msg-content :deep(a),
.aux-detail-content :deep(a) {
  color: #121212;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.msg-content :deep(strong),
.aux-detail-content :deep(strong) {
  font-weight: 600;
}

.msg-content :deep(em),
.aux-detail-content :deep(em) {
  font-style: italic;
}

.msg-content :deep(.katex-display),
.aux-detail-content :deep(.katex-display) {
  margin: 12px 0;
  overflow-x: auto;
}

.msg-content :deep(.katex),
.aux-detail-content :deep(.katex) {
  font-size: 1.05em;
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

.clarification-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 18px;
}

.clarification-loading {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  padding: 16px 18px;
  margin-bottom: 18px;
  color: #666666;
  font-size: 13px;
}

.clarification-head,
.clarification-block {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  padding: 18px;
}

.clarification-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.clarification-icon {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: #f7f7f7;
  border: 1px solid #eeeeee;
  color: #121212;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.clarification-head h2 {
  margin: 0 0 4px;
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 15px;
  font-weight: 600;
  color: #121212;
}

.clarification-head p,
.clarification-block label {
  margin: 0;
  font-size: 11px;
  color: #999999;
}

.clarification-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.clarification-block label {
  font-weight: 700;
  letter-spacing: 0.8px;
}

.original-question,
.model-analysis {
  background: #fdfdfd;
  border: 1px solid #f1f1f1;
  border-radius: 12px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.7;
  color: #121212;
}

.model-analysis {
  max-height: 220px;
  overflow-y: auto;
}

.option-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.choice-chip {
  border: 1px solid #e4e4e4;
  background: #fff;
  color: #606060;
  border-radius: 12px;
  padding: 7px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.choice-chip:hover {
  border-color: #999999;
}

.choice-chip.selected {
  border: 2px solid #121212;
  background: #fafafa;
  color: #121212;
  font-weight: 700;
  padding: 6px 11px;
}

.inline-input {
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 0 12px;
  background: #fdfdfd;
}

.inline-input:focus-within,
.clarification-block textarea:focus {
  border-color: #121212;
}

.inline-input input,
.clarification-block textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: #121212;
  font-size: 13px;
  font-family: inherit;
}

.inline-input input {
  height: 42px;
}

.clarification-block textarea {
  resize: vertical;
  min-height: 76px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 10px 12px;
  line-height: 1.6;
}

.clarification-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.clarification-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 2px;
}

.primary-action,
.secondary-action {
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}

.primary-action {
  background: #121212;
  color: #fff;
}

.secondary-action {
  background: #fff;
  color: #555555;
  border: 1px solid #e4e4e4;
}

.primary-action:disabled,
.secondary-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner.dark {
  border-color: rgba(18, 18, 18, 0.2);
  border-top-color: #121212;
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

body.green .msg-avatar.tool {
  background: #526e5a;
  color: #fff;
}

body.green .msg-mode-tag {
  color: #526e5a;
  background: #edf2ee;
  border-color: #d4e0d6;
}

body.green .tool-tag {
  color: #3b473d;
  background: #edf2ee;
  border-color: #d4e0d6;
}

body.green .chat-msg.tool .msg-content {
  background: #f4f6f4;
  border-color: #edf1ed;
  color: #2c332e;
}

body.green .chat-msg.ai .msg-content {
  background: #f4f6f4;
  border-color: #edf1ed;
  color: #2c332e;
}

body.green .aux-timeline-container {
  background: #f6f8f6;
  border-color: #dce4dc;
}

body.green .aux-timeline-line {
  background: #b8c8b8;
}

body.green .aux-node-dot {
  border-color: #526e5a;
  color: #526e5a;
}

body.green .aux-node-label {
  color: #2c3a2e;
}

body.green .aux-node-detail {
  border-color: #dce4dc;
}

body.green .aux-detail-header {
  border-bottom-color: #edf1ed;
}

body.green .aux-detail-badge {
  background: #edf2ee;
  color: #526e5a;
}

body.green .aux-detail-content {
  color: #2c3a2e;
}

body.green .chat-msg.user .msg-content {
  background: #526e5a;
  color: #fff;
}

body.green .msg-content :deep(code),
body.green .aux-detail-content :deep(code) {
  background: rgba(82, 110, 90, 0.1);
}

body.green .msg-content :deep(pre),
body.green .aux-detail-content :deep(pre) {
  background: #2c3a2e;
  color: #e5e5e5;
}

body.green .msg-content :deep(blockquote),
body.green .aux-detail-content :deep(blockquote) {
  border-left-color: #b8c8b8;
  color: #556056;
}

body.green .msg-content :deep(th),
body.green .aux-detail-content :deep(th) {
  background: #edf2ee;
}

body.green .msg-content :deep(th),
body.green .msg-content :deep(td),
body.green .aux-detail-content :deep(th),
body.green .aux-detail-content :deep(td) {
  border-color: #d4e0d6;
}

body.green .msg-content :deep(hr),
body.green .aux-detail-content :deep(hr) {
  border-top-color: #d4e0d6;
}

body.green .msg-content :deep(a),
body.green .aux-detail-content :deep(a) {
  color: #526e5a;
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

body.dark .msg-avatar.tool {
  background: #ffffff;
  color: #121212;
}

body.dark .msg-mode-tag {
  color: #b3b3b3;
  background: #2d2d2d;
  border-color: #333333;
}

body.dark .tool-tag {
  color: #b3b3b3;
  background: #2d2d2d;
  border-color: #333333;
}

body.dark .chat-msg.tool .msg-content {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .chat-msg.ai .msg-content {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .aux-timeline-container {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .aux-timeline-line {
  background: #444;
}

body.dark .aux-node-dot {
  border-color: #e5e5e5;
  color: #e5e5e5;
  background: #242424;
}

body.dark .aux-node-label {
  color: #e5e5e5;
}

body.dark .aux-node-preview {
  color: #888;
}

body.dark .aux-expand-btn {
  color: #888;
}

body.dark .aux-expand-btn:hover {
  color: #e5e5e5;
}

body.dark .aux-node-detail {
  background: #242424;
  border-color: #333;
}

body.dark .aux-detail-header {
  border-bottom-color: #333;
  color: #888;
}

body.dark .aux-detail-badge {
  background: #333;
  color: #b3b3b3;
}

body.dark .aux-detail-content {
  color: #e5e5e5;
}

body.dark .chat-msg.user .msg-content {
  background: #333333;
  color: #ffffff;
}

body.dark .msg-content :deep(code),
body.dark .aux-detail-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

body.dark .msg-content :deep(pre),
body.dark .aux-detail-content :deep(pre) {
  background: #111;
  color: #e5e5e5;
}

body.dark .msg-content :deep(blockquote),
body.dark .aux-detail-content :deep(blockquote) {
  border-left-color: #444;
  color: #999;
}

body.dark .msg-content :deep(th),
body.dark .aux-detail-content :deep(th) {
  background: #2d2d2d;
}

body.dark .msg-content :deep(th),
body.dark .msg-content :deep(td),
body.dark .aux-detail-content :deep(th),
body.dark .aux-detail-content :deep(td) {
  border-color: #333;
}

body.dark .msg-content :deep(hr),
body.dark .aux-detail-content :deep(hr) {
  border-top-color: #333;
}

body.dark .msg-content :deep(a),
body.dark .aux-detail-content :deep(a) {
  color: #e5e5e5;
}

body.dark .msg-content :deep(.katex),
body.dark .aux-detail-content :deep(.katex) {
  color: #e5e5e5;
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

  .clarification-grid {
    grid-template-columns: 1fr;
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

  .clarification-actions {
    flex-direction: column;
  }

  .primary-action,
  .secondary-action {
    width: 100%;
  }
}

.hidden-file-input { display: none; }

.attachment-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 18px 12px;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f4f4f4;
  border: 1px solid #e5e5e5;
  font-size: 12px;
  color: #333;
}
.attachment-chip.ready { border-color: #c8d8cc; background: #eef5f0; }
.attachment-chip.failed { border-color: #f3caca; background: #fff1f1; }
.attachment-name { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attachment-status { color: #526e5a; font-weight: 600; }
.attachment-chip button { border: none; background: transparent; cursor: pointer; color: #777; font-size: 14px; }

.save-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0, 0, 0, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
}
.save-dialog-card {
  width: min(520px, calc(100vw - 32px));
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 18px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}
.save-dialog-header, .save-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}
.save-dialog-footer { border-top: 1px solid #eee; border-bottom: none; justify-content: flex-end; gap: 10px; }
.save-dialog-header h3 { margin: 0; font-size: 16px; }
.save-dialog-header button { border: none; background: transparent; font-size: 22px; cursor: pointer; color: #777; }
.save-dialog-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 8px; }
.save-dialog-body label { font-size: 12px; font-weight: 700; color: #555; margin-top: 8px; }
.save-dialog-body input { height: 38px; border: 1px solid #ddd; border-radius: 10px; padding: 0 12px; font: inherit; }
.save-attachment-list { display: flex; flex-wrap: wrap; gap: 6px; }
.save-attachment-list span { font-size: 12px; padding: 5px 8px; background: #f4f4f4; border-radius: 999px; }
.save-muted { margin: 0; font-size: 12px; color: #888; }
body.dark .attachment-chip { background: #2d2d2d; border-color: #444; color: #ddd; }
body.dark .save-dialog-card { background: #242424; border-color: #333; color: #e5e5e5; }
body.dark .save-dialog-header, body.dark .save-dialog-footer { border-color: #333; }
body.dark .save-dialog-body input { background: #1a1a1a; border-color: #444; color: #e5e5e5; }
body.dark .save-attachment-list span { background: #333; }

</style>
