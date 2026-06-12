<template>
<div class="app">
<StudentNav active-tab="tutoring-assistant" />

  <div class="main-wrapper" ref="mainWrapper">
    <div class="left-area" ref="leftArea">
      <!-- 知识点巩固 -->
      <div class="panel" ref="knowledgePanel" :style="{ height: panelHeights.knowledge + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>📐 知识点巩固</div>
          <span class="size-badge">{{ knowledgeItems.length }} 项</span>
        </div>
        <div class="panel-body">
          <div v-if="knowledgeItems.length === 0" class="empty-hint">
            开始答题后，知识点掌握情况将在这里显示
          </div>
          <div v-for="(item, i) in knowledgeItems" :key="'k'+i" class="knowledge-mini">
            <div class="k-icon">📐</div>
            <div class="k-info">
              <div class="k-title">{{ item.title }}</div>
              <div class="k-formula" v-if="item.formula" v-html="renderFormula(item.formula)"></div>
              <div class="k-mastery">掌握度：{{ formatMastery(item.mastery) }}</div>
            </div>
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'knowledge')"></div>
      </div>
      <!-- 错题归因 -->
      <div class="panel" ref="errorPanel" :style="{ height: panelHeights.error + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>🔬 错题归因</div>
          <span class="size-badge">{{ errorItems.length }} 项</span>
        </div>
        <div class="panel-body">
          <div v-if="errorItems.length === 0" class="empty-hint">
            答错题目时，错误分析将在这里显示
          </div>
          <div v-for="(item, i) in errorItems" :key="'e'+i" class="error-entry">
            <span class="e-tag">{{ item.type }}</span>
            <div><strong>{{ item.title }}</strong><br>{{ item.detail }}</div>
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'error')"></div>
      </div>
      <!-- 学习策略 -->
      <div class="panel" ref="strategyPanel" :style="{ height: panelHeights.strategy + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>💡 学习策略</div>
          <span class="size-badge">{{ strategyItems.length }} 项</span>
        </div>
        <div class="panel-body">
          <div v-if="strategyItems.length === 0" class="empty-hint">
            AI 将根据你的答题表现生成个性化学习建议
          </div>
          <div v-for="(item, i) in strategyItems" :key="'s'+i" class="strategy-entry">
            <span class="s-dot"></span>{{ item }}
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'strategy')"></div>
      </div>
    </div>
    <div
      class="resize-handle-h"
      :class="{ locked: isLockedH, unlocked: !isLockedH }"
      @dblclick="isLockedH = !isLockedH"
      @mousedown="startHorizontalResize"
      ref="resizeHandleH"
      title="双击解锁拖拽左右宽度"
    ></div>
    <div class="right-area" ref="rightArea">
      <div class="tutor-panel">
        <div class="tutor-header">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="tutor-avatar">🧑‍🏫</div>
            <span>AI 导师</span>
          </div>
          <div class="header-right">
            <div class="mode-switch">
              <button class="mode-btn" :class="{ active: currentMode === 'my' }" @click="switchMode('my')">📝 我的题目</button>
              <button class="mode-btn" :class="{ active: currentMode === 'ai' }" @click="switchMode('ai')">🤖 AI推题</button>
            </div>
            <button class="view-toggle-btn" :class="{ answering: currentView === 'answer' }" @click="toggleView">
              {{ currentView === 'chat' ? '✏️ 答题' : '💬 对话' }}
            </button>
          </div>
        </div>
        <!-- 对话视图 -->
        <div class="chat-view" :class="{ hidden: currentView !== 'chat' }">
          <div class="tutor-messages" ref="tutorMessages">
            <div v-for="(msg, i) in chatMessages" :key="i" class="tutor-msg" :class="'msg-' + msg.role">
              <strong v-if="msg.role === 'student'">👤 学生：</strong>
              <strong v-else-if="msg.role === 'ai'">🤖 导师：</strong>
              <strong v-else>ℹ️ 系统：</strong>
              <span v-html="renderMessageContent(msg.content)"></span>
            </div>
            <div v-if="isChatLoading" class="tutor-msg msg-ai">
              <strong>🤖 导师：</strong>
              <span class="typing-indicator">正在思考中...</span>
            </div>
          </div>
          <div class="chat-bottom-bar">
            <input type="text" class="student-input" v-model="studentQuestion" placeholder="向导师提问，例如：什么是消光系数？" @keyup.enter="askQuestion">
            <button class="send-btn" @click="askQuestion" :disabled="isChatLoading">发送</button>
            <button class="start-answer-btn" @click="switchToAnswer">✏️ 答题</button>
          </div>
        </div>
        <!-- 答题视图 -->
        <div class="answer-view" :class="{ hidden: currentView !== 'answer' }">
          <div class="qa-top">
            <div class="question-box" v-if="currentMode === 'my'">
              <textarea v-model="questionInput" placeholder="📝 在这里输入或粘贴题目内容..." class="question-textarea"></textarea>
            </div>
            <div class="question-box" v-else>
              <!-- AI: answering a specific question -->
              <div v-if="aiCurrentQuestion" class="ai-question-detail">
                <button class="ai-back-btn" @click="backToAIView">← 返回</button>
                <div class="ai-q-full">
                  <span class="ai-q-type">{{ questionTypeLabel(aiCurrentQuestion.type) }}</span>
                  <span class="ai-q-points">{{ aiCurrentQuestion.points }}分</span>
                </div>
                <div class="ai-q-stem">{{ aiCurrentQuestion.content }}</div>
                <div v-if="aiCurrentQuestion.options && aiCurrentQuestion.options.length > 0" class="ai-q-options">
                  <div v-for="(opt, oi) in aiCurrentQuestion.options" :key="oi" class="ai-q-opt">
                    <strong>{{ opt.key }}.</strong> {{ opt.text }}
                  </div>
                </div>
              </div>
              <!-- AI: main view with tabs -->
              <div v-else class="ai-main-view">
                <!-- Tab bar -->
                <div class="ai-tabs">
                  <button class="ai-tab" :class="{ active: aiTab === 'generate' }" @click="aiTab = 'generate'">✨ 推题</button>
                  <button class="ai-tab" :class="{ active: aiTab === 'bank' }" @click="aiTab = 'bank'">
                    📚 题库
                    <span v-if="bankTotalCount > 0" class="ai-tab-badge">{{ bankTotalCount }}</span>
                  </button>
                </div>
                <!-- Tab: generate -->
                <div v-if="aiTab === 'generate'" class="ai-tab-body">
                  <div class="ai-form-section">
                    <label class="ai-form-label">推题模式</label>
                    <div class="ai-mode-switch">
                      <button class="ai-mode-btn" :class="{ active: aiRecommendMode === 'auto' }" @click="aiRecommendMode = 'auto'">🎯 智能推题</button>
                      <button class="ai-mode-btn" :class="{ active: aiRecommendMode === 'custom' }" @click="aiRecommendMode = 'custom'">📝 指定内容</button>
                    </div>
                    <p class="ai-form-hint" v-if="aiRecommendMode === 'auto'">基于你的学习画像，针对薄弱知识点自动推荐练习题</p>
                    <p class="ai-form-hint" v-else>输入你想练习的知识点或内容</p>
                  </div>
                  <div v-if="aiRecommendMode === 'custom'" class="ai-form-section">
                    <textarea v-model="aiCustomContent" class="ai-custom-input" placeholder="输入知识点、教材内容或你想练习的主题..." rows="3"></textarea>
                  </div>
                  <div class="ai-form-section">
                    <label class="ai-form-label">题目数量</label>
                    <div class="ai-num-control">
                      <button class="ai-num-btn" @click="aiRecommendNum = Math.max(1, aiRecommendNum - 1)">−</button>
                      <span class="ai-num-value">{{ aiRecommendNum }}</span>
                      <button class="ai-num-btn" @click="aiRecommendNum = Math.min(20, aiRecommendNum + 1)">+</button>
                    </div>
                  </div>
                  <button class="ai-generate-btn" @click="handleAIRecommend" :disabled="aiRecommendLoading || (aiRecommendMode === 'custom' && !aiCustomContent.trim())">
                    {{ aiRecommendLoading ? '🔄 生成中...' : '✨ 开始推题' }}
                  </button>
                  <div v-if="aiRecommendError" class="ai-error">{{ aiRecommendError }}</div>
                </div>
                <!-- Tab: bank -->
                <div v-if="aiTab === 'bank'" class="ai-tab-body ai-bank-body">
                  <div v-if="aiBatches.length === 0" class="ai-bank-empty">
                    📭 题库为空，请先生成题目
                  </div>
                  <div v-else class="ai-bank-list">
                    <div class="ai-bank-header">
                      <span>{{ aiBatches.length }} 批 · 共 {{ bankTotalCount }} 道题</span>
                      <button class="ai-bank-clear" @click="handleClearBank">🗑️ 清空</button>
                    </div>
                    <div v-for="(batch, bi) in aiBatches" :key="batch.id" class="ai-batch-group">
                      <div class="ai-batch-header" @click="toggleBatch(batch.id)">
                        <span class="ai-batch-arrow" :class="{ expanded: aiExpandedBatches.has(batch.id) }">▶</span>
                        <span class="ai-batch-label">
                          {{ batch.mode === 'auto' ? '🎯 智能推题' : '📝 ' + (batch.content || '指定内容') }}
                        </span>
                        <span class="ai-batch-meta">{{ (batch.questions || []).length }} 题 · {{ formatBatchTime(batch.createdAt) }}</span>
                        <button class="ai-batch-del" @click.stop="handleDeleteBatch(bi)" title="删除此批">✕</button>
                      </div>
                      <div v-if="aiExpandedBatches.has(batch.id)" class="ai-batch-questions">
                        <div v-for="(q, qi) in (batch.questions || [])" :key="qi" class="ai-bank-item">
                          <div class="ai-bank-item-main" @click="startAIQuestion(q, batch.id)">
                            <span class="ai-q-type">{{ questionTypeLabel(q.type) }}</span>
                            <span class="ai-bank-item-content">{{ q.content }}</span>
                            <span class="ai-q-points">{{ q.points }}分</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="upload-row" v-show="currentMode === 'my'">
              <button class="file-label" @click="openHomeworkPicker">📚 从作业选题</button>
              <input type="file" id="fileInput" ref="fileInput" style="display:none;" accept=".txt,.doc,.docx,.pdf" multiple @change="handleFileUpload">
              <label for="fileInput" class="file-label">📎 上传题目</label>
            </div>
          </div>
          <div class="qa-bottom">
            <textarea class="answer-input" v-model="answerInput" placeholder="✏️ 在这里写下你的解答..."></textarea>
            <div class="submit-row">
              <button class="submit-btn" @click="submitAnswer" :disabled="isEvaluating">
                {{ isEvaluating ? '⏳ AI 评估中...' : '✅ 提交回答' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="progress-bar">
    <span>📊 辅导进度</span>
    <div style="flex:1;background:var(--border);height:6px;border-radius:3px;"><div class="progress-fill" :style="{ width: Math.min(submissionCount * 10, 100) + '%' }"></div></div>
    <span>{{ submissionCount }} 次提交</span>
  </div>

  <!-- 从作业选题弹窗 -->
  <div class="picker-overlay" v-if="showPicker" @click.self="closePicker">
    <div class="picker-dialog">
      <div class="picker-header">
        <span>📚 从作业选题</span>
        <button class="picker-close" @click="closePicker">✕</button>
      </div>
      <div class="picker-body">
        <!-- 面包屑 -->
        <div class="picker-breadcrumb">
          <span :class="{ active: pickerStep === 'courses' }" @click="pickerStep = 'courses'">课程</span>
          <span v-if="selectedCourse"> / {{ selectedCourse.courseName }}</span>
          <span v-if="selectedHomework"> / {{ selectedHomework.title }}</span>
        </div>
        <!-- 课程列表 -->
        <div v-if="pickerStep === 'courses'" class="picker-list">
          <div v-if="pickerLoading" class="picker-loading">加载中...</div>
          <div v-else-if="courses.length === 0" class="picker-empty">暂无课程，请先加入课程</div>
          <div v-for="c in courses" :key="c.courseId" class="picker-item" @click="selectCourse(c)">
            <div class="picker-item-title">{{ c.courseName }}</div>
            <div class="picker-item-desc">{{ c.subject }} · {{ c.grade }}</div>
          </div>
        </div>
        <!-- 作业列表 -->
        <div v-if="pickerStep === 'homework'" class="picker-list">
          <div v-if="pickerLoading" class="picker-loading">加载中...</div>
          <div v-else-if="homeworkList.length === 0" class="picker-empty">该课程暂无作业</div>
          <div v-for="hw in homeworkList" :key="hw.hwId" class="picker-item" @click="selectHomework(hw)">
            <div class="picker-item-title">{{ hw.title }}</div>
            <div class="picker-item-desc">{{ hw.description || '暂无描述' }}</div>
          </div>
        </div>
        <!-- 题目列表 -->
        <div v-if="pickerStep === 'questions'" class="picker-list">
          <div v-if="pickerLoading" class="picker-loading">加载中...</div>
          <div v-else-if="questionList.length === 0" class="picker-empty">该作业暂无题目</div>
          <div v-for="(q, i) in questionList" :key="i" class="picker-item picker-question" @click="selectQuestion(q)">
            <div class="picker-q-type">{{ questionTypeLabel(q.type || q.objType) }}</div>
            <div class="picker-item-content">
              <div class="picker-item-title">{{ q.content || q.stem || '题目 ' + (i + 1) }}</div>
              <div class="picker-item-opts" v-if="(q.options || q.choices || []).length > 0">
                {{ (q.options || q.choices || []).length }} 个选项
              </div>
            </div>
            <div class="picker-item-right">
              <span v-if="hasPreviousAnswer(q, i)" class="picker-answered">✅ 已作答</span>
              <span class="picker-item-desc">{{ q.points || q.maxScore || 0 }} 分</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import katex from 'katex'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useTutorAssistant } from '../../composables/useTutorAssistant.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const { user, logout: authLogout } = useAuth()
const { connect, connected, getToken } = useGateway()
const {
  tutorProfile,
  chatMessages,
  isLoading,
  fetchProfile,
  askTutor,
  subscribeToChat,
  evaluateAnswer,
  recommendQuestions,
  clearChat,
} = useTutorAssistant()

// UI state
const isLockedH = ref(true)
const currentMode = ref('my')
const currentView = ref('chat')
const studentQuestion = ref('')
const questionInput = ref('')
const answerInput = ref('')
const referenceAnswer = ref('') // 参考答案/解析
const isEvaluating = ref(false)
const panelHeights = ref({ knowledge: 378, error: 277, strategy: 200 })
const mainWrapper = ref(null)
const leftArea = ref(null)
const rightArea = ref(null)
const resizeHandleH = ref(null)
const tutorMessages = ref(null)
const fileInput = ref(null)

// Homework picker state
const showPicker = ref(false)
const pickerStep = ref('courses') // courses | homework | questions
const pickerLoading = ref(false)
const courses = ref([])
const homeworkList = ref([])
const questionList = ref([])
const selectedCourse = ref(null)
const selectedHomework = ref(null)
const submissionAnswers = ref({}) // { questionId: answerText }

// AI recommend state
const aiRecommendLoading = ref(false)
const aiRecommendError = ref('')
const aiBatches = ref([]) // [{id, mode, content, createdAt, questions:[]}]
const aiRecommendNum = ref(5)
const aiRecommendMode = ref('auto') // auto | custom
const aiCustomContent = ref('') // custom knowledge content for recommend
const aiCurrentQuestion = ref(null) // currently selected question for answering
const aiCurrentBatchId = ref(null) // batch id of current question
const aiAnswerInput = ref('') // student's answer for AI question
const aiAnswerResult = ref(null) // evaluation result for current AI question
const aiTab = ref('generate') // generate | bank
const aiExpandedBatches = ref(new Set()) // expanded batch ids

// Computed
const isChatLoading = computed(() => isLoading.value)

const bankTotalCount = computed(() => {
  return aiBatches.value.reduce((sum, b) => sum + (b.questions?.length || 0), 0)
})

const knowledgeItems = computed(() => {
  return tutorProfile.value?.knowledgePoints || []
})

const errorItems = computed(() => {
  return tutorProfile.value?.errorRecords || []
})

const strategyItems = computed(() => {
  return (tutorProfile.value?.strategies || []).map(s => s.content || s)
})

const submissionCount = computed(() => {
  return tutorProfile.value?.totalSubmissions || 0
})

function renderFormula(value) {
  if (!value) return ''
  try {
    return value.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex) => {
      return katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })
    }).replace(/\$([^$]+)\$/g, (_, latex) => {
      return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false })
    })
  } catch { return value }
}

function renderMessageContent(content) {
  if (!content) return ''
  // Escape HTML, then render newlines
  return content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

function formatMastery(mastery) {
  if (mastery === undefined || mastery === null) return '待评估'
  const pct = Math.round(mastery * 100)
  if (pct >= 80) return `🟢 已掌握 (${pct}%)`
  if (pct >= 60) return `🟡 待巩固 (${pct}%)`
  return `🔴 需加强 (${pct}%)`
}

function switchMode(mode) {
  currentMode.value = mode
}

function toggleView() {
  if (currentView.value === 'chat') switchToAnswer()
  else switchToChat()
}

function switchToAnswer() {
  currentView.value = 'answer'
}

function switchToChat() {
  currentView.value = 'chat'
}

function handleFileUpload(event) {
  const files = event.target.files
  if (!files.length) return
  const firstFile = files[0]
  const reader = new FileReader()
  reader.onload = function(e) {
    let content = e.target.result
    if (content.length > 500) content = content.substring(0, 500) + '…'
    questionInput.value = content
  }
  reader.readAsText(firstFile, 'UTF-8')
}

// ---- Homework picker ----
function questionTypeLabel(type) {
  const map = { choice: '选择题', true_false: '判断题', fill: '填空题', blank: '填空题', essay: '主观题', short_answer: '简答题' }
  return map[type] || '题目'
}

async function openHomeworkPicker() {
  showPicker.value = true
  pickerStep.value = 'courses'
  selectedCourse.value = null
  selectedHomework.value = null
  await fetchCoursesForPicker()
}

function closePicker() {
  showPicker.value = false
}

async function fetchCoursesForPicker() {
  const u = user.value
  if (!u?.userId) return
  pickerLoading.value = true
  try {
    const params = new URLSearchParams({ role: u.role, user_id: u.userId, token: getToken() || '' })
    const resp = await fetch(`/api/courses?${params}`)
    if (resp.ok) {
      const data = await resp.json()
      courses.value = data.courses || data || []
    }
  } catch (e) {
    console.error('[picker] fetch courses failed:', e)
  } finally {
    pickerLoading.value = false
  }
}

async function selectCourse(course) {
  selectedCourse.value = course
  pickerStep.value = 'homework'
  pickerLoading.value = true
  try {
    const params = new URLSearchParams({ role: user.value.role, user_id: user.value.userId, token: getToken() || '' })
    const resp = await fetch(`/api/courses/${course.courseId}/homework?${params}`)
    if (resp.ok) {
      const data = await resp.json()
      homeworkList.value = data.homework || data || []
    }
  } catch (e) {
    console.error('[picker] fetch homework failed:', e)
  } finally {
    pickerLoading.value = false
  }
}

async function selectHomework(hw) {
  selectedHomework.value = hw
  pickerStep.value = 'questions'
  pickerLoading.value = true
  submissionAnswers.value = {}
  try {
    const params = new URLSearchParams({ role: user.value.role, user_id: user.value.userId, token: getToken() || '' })
    // Fetch homework detail and submission in parallel
    const [hwResp, subResp] = await Promise.all([
      fetch(`/api/courses/${selectedCourse.value.courseId}/homework/${hw.hwId}?${params}`),
      fetch(`/api/courses/${selectedCourse.value.courseId}/homework/${hw.hwId}/submissions/${user.value.userId}?${params}`),
    ])
    if (hwResp.ok) {
      const data = await hwResp.json()
      const hwDetail = data.homework || data
      questionList.value = hwDetail.questions || hwDetail.settings?.questions || []
    }
    if (subResp.ok) {
      const subData = await subResp.json()
      const answers = subData.answers || subData.submission?.answers || {}
      submissionAnswers.value = answers
    }
  } catch (e) {
    console.error('[picker] fetch questions/submission failed:', e)
  } finally {
    pickerLoading.value = false
  }
}

function hasPreviousAnswer(q, index) {
  const qid = q.id || q.questionId || ''
  return !!(submissionAnswers.value[qid] || submissionAnswers.value[`q${index + 1}`])
}

function selectQuestion(q) {
  const content = q.content || q.stem || ''
  // Build full question text with options
  let fullQuestion = content
  const options = q.options || q.choices || []
  if (options.length > 0) {
    const optText = options.map((opt, i) => {
      const label = String.fromCharCode(65 + i) // A, B, C, D
      const text = typeof opt === 'string' ? opt : (opt.text || opt.content || opt.label || '')
      return `${label}. ${text}`
    }).join('\n')
    fullQuestion = fullQuestion + '\n' + optText
  }
  questionInput.value = fullQuestion
  // Save reference answer/explanation for AI evaluation
  referenceAnswer.value = q.answer || q.explanation || q.referenceAnswer || ''
  // Auto-fill previous answer if available
  const qid = q.id || q.questionId || ''
  const prevAnswer = submissionAnswers.value[qid] || submissionAnswers.value[`q${questionList.value.indexOf(q) + 1}`] || ''
  if (prevAnswer) {
    answerInput.value = prevAnswer
  }
  closePicker()
  switchToAnswer()
}

async function askQuestion() {
  const q = studentQuestion.value.trim()
  if (!q) return
  studentQuestion.value = ''
  await askTutor(q)
  // Auto-scroll
  nextTick(() => {
    if (tutorMessages.value) tutorMessages.value.scrollTop = tutorMessages.value.scrollHeight
  })
}

async function submitAnswer() {
  const answer = answerInput.value.trim()
  if (!answer) { alert('请输入你的解答'); return }

  const question = questionInput.value.trim()
  if (!question) { alert('请先输入题目'); return }

  isEvaluating.value = true
  try {
    const result = await evaluateAnswer(question, answer, referenceAnswer.value)

    // Add evaluation result to chat
    const resultHtml = result.isCorrect
      ? `✅ <strong>回答正确！</strong>得分：${result.score}分<br>${result.analysis}`
      : `❌ <strong>回答有误</strong>，得分：${result.score}分<br>${result.analysis}<br>🔍 错误类型：${result.errorType}<br>📝 ${result.errorDetail}`

    chatMessages.value.push({
      role: 'ai',
      content: `[答题评估] 题目：${question.slice(0, 60)}...\n你的解答：${answer.slice(0, 60)}...\n\n${result.isCorrect ? '✅ 回答正确' : '❌ 回答有误'}，得分：${result.score}分\n${result.analysis}${result.strategy ? '\n💡 ' + result.strategy : ''}`,
      timestamp: Date.now(),
    })

    // Clear answer input
    answerInput.value = ''
    // Switch to chat to see the result
    switchToChat()
    nextTick(() => {
      if (tutorMessages.value) tutorMessages.value.scrollTop = tutorMessages.value.scrollHeight
    })
  } catch (err) {
    alert('评估失败: ' + err.message)
  } finally {
    isEvaluating.value = false
  }
}

// ---- AI Recommend ----
async function handleAIRecommend() {
  aiRecommendError.value = ''
  aiRecommendLoading.value = true
  try {
    const params = {
      numQuestions: aiRecommendNum.value,
    }
    if (aiRecommendMode.value === 'custom' && aiCustomContent.value.trim()) {
      params.content = aiCustomContent.value.trim()
    }
    const result = await recommendQuestions(params)
    if (result.questions && result.questions.length > 0) {
      // Build a new batch and append
      const newBatch = {
        id: 'b_' + Date.now() + '_' + aiBatches.value.length,
        mode: aiRecommendMode.value,
        content: aiRecommendMode.value === 'custom' ? aiCustomContent.value.trim().slice(0, 100) : '',
        createdAt: new Date().toISOString(),
        questions: result.questions,
      }
      aiBatches.value.push(newBatch)
      aiExpandedBatches.value.add(newBatch.id)
      aiTab.value = 'bank'
    } else {
      aiRecommendError.value = 'AI 未能生成题目，请重试'
    }
  } catch (e) {
    aiRecommendError.value = e.message || 'AI 推题失败，请重试'
  } finally {
    aiRecommendLoading.value = false
  }
}

function startAIQuestion(q, batchId) {
  aiCurrentQuestion.value = q
  aiCurrentBatchId.value = batchId || null
  aiAnswerInput.value = ''
  aiAnswerResult.value = null
  questionInput.value = q.content
  referenceAnswer.value = q.answer || q.explanation || ''
  switchToAnswer()
}

function backToAIView() {
  aiCurrentQuestion.value = null
  aiCurrentBatchId.value = null
  aiAnswerResult.value = null
  aiAnswerInput.value = ''
  aiTab.value = 'bank'
}

function toggleBatch(batchId) {
  const s = aiExpandedBatches.value
  if (s.has(batchId)) {
    s.delete(batchId)
  } else {
    s.add(batchId)
  }
  // Force reactivity
  aiExpandedBatches.value = new Set(s)
}

function handleDeleteBatch(index) {
  aiBatches.value.splice(index, 1)
}

function handleClearBank() {
  if (confirm('确定清空所有题目？')) {
    aiBatches.value = []
  }
}

function formatBatchTime(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return '' }
}

// ---- Horizontal resize ----
let isResizingH = false, startX, startLeftW, startRightW

function startHorizontalResize(e) {
  if (isLockedH.value) return
  isResizingH = true
  startX = e.clientX
  startLeftW = leftArea.value.getBoundingClientRect().width
  startRightW = rightArea.value.getBoundingClientRect().width
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMove(e) {
  if (!isResizingH) return
  const dx = e.clientX - startX
  const ww = mainWrapper.value.getBoundingClientRect().width
  let nl = startLeftW + dx, nr = startRightW - dx
  if (nl < 280) nl = 280
  if (nr < 420) nr = 420
  leftArea.value.style.width = (nl / ww * 100) + '%'
  rightArea.value.style.width = (nr / ww * 100) + '%'
}

function onMouseUp() {
  if (isResizingH) { isResizingH = false; document.body.style.cursor = ''; document.body.style.userSelect = '' }
}

// ---- Vertical resize ----
let isResizingV = false, resizingPanelKey = '', startY, startHeight

function startVerticalResize(e, panelKey) {
  isResizingV = true
  resizingPanelKey = panelKey
  startY = e.clientY
  startHeight = panelHeights.value[panelKey]
  document.body.style.cursor = 'row-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMoveV(e) {
  if (!isResizingV) return
  const dy = e.clientY - startY
  let newH = startHeight + dy
  if (newH < 120) newH = 120
  if (newH > 500) newH = 500
  panelHeights.value[resizingPanelKey] = Math.round(newH)
}

function onMouseUpV() {
  if (isResizingV) { isResizingV = false; resizingPanelKey = ''; document.body.style.cursor = ''; document.body.style.userSelect = '' }
}

// ---- Init ----
onMounted(async () => {
  // Ensure gateway connection
  if (user.value && !connected.value) {
    try {
      await connect({ role: user.value.role, userId: user.value.userId })
    } catch (e) {
      console.error('[tutor] Gateway connect failed:', e.message)
    }
  }

  // Subscribe to chat responses
  subscribeToChat()

  // Fetch tutor profile
  await fetchProfile()

  // Load saved question batches from profile
  if (tutorProfile.value?.recommendedQuestions?.length > 0) {
    const raw = tutorProfile.value.recommendedQuestions
    // Compat: old format is flat question array, new format is batch array
    if (raw[0]?.questions) {
      aiBatches.value = raw
    } else {
      aiBatches.value = [{ id: 'b_legacy', mode: 'auto', content: '', createdAt: '', questions: raw }]
    }
    const lastBatch = aiBatches.value[aiBatches.value.length - 1]
    if (lastBatch?.id) aiExpandedBatches.value.add(lastBatch.id)
  }

  // Welcome message
  if (chatMessages.value.length === 0) {
    chatMessages.value.push({
      role: 'ai',
      content: '👋 欢迎使用 AI 学伴辅导！你可以直接向我提问，也可以切换到"答题"模式输入题目和解答，我会为你进行智能评估。',
      timestamp: Date.now(),
    })
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('mousemove', onMouseMoveV)
  window.addEventListener('mouseup', onMouseUpV)
})
</script>

<style>
:root {
  --bg: #f8f6f1;
  --card: #ffffff;
  --nav-bg: #ffffff;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.2);
  --accent-glow: rgba(91,141,239,0.15);
  --border: #e8e4db;
  --text: #2c2c2c;
  --text2: #666666;
  --text3: #999999;
  --divider: #e8e4db;
  --tutor-msg-bg: #eef4ff;
  --green: #16a34a;
  --red: #e74c3c;
  --radius: 12px;
  --panel-radius: 14px;
  --card-radius: 10px;
  --quiz-border: #5b8def;
  --quiz-bg: #f0f4ff;
  --resize-handle-color: rgba(91,141,239,0.3);
}
body.dark {
  --bg: #12121a;
  --card: #1e1e2e;
  --nav-bg: #1e1e2e;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.2);
  --accent-glow: rgba(91,141,239,0.2);
  --border: #333333;
  --text: #e0e0e0;
  --text2: #aaaaaa;
  --text3: #777777;
  --divider: #333333;
  --tutor-msg-bg: #1a1a2a;
  --quiz-border: #5b8def;
  --quiz-bg: #1a1830;
  --resize-handle-color: rgba(91,141,239,0.35);
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',sans-serif;
  background:var(--bg); color:var(--text); height:100vh; overflow:hidden;
  transition:0.3s; letter-spacing:0.01em;
}
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:8px; }
</style>
<style scoped>
.app { display:flex; flex-direction:column; height:100vh; max-width:1800px; margin:0 auto; padding:10px 14px; gap:10px; }

.main-wrapper { flex:1; min-height:0; display:flex; gap:0; position:relative; }
.left-area {
  width:25%; min-width:280px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;
  padding-right:1px;
}
.right-area {
  width:75%; min-width:420px; display:flex; flex-direction:column; gap:0;
  padding-left:1px;
}
.resize-handle-h {
  width:4px; cursor:default; background:transparent; position:relative; z-index:10;
  flex-shrink:0; display:flex; align-items:center; justify-content:center; transition:background 0.2s;
  margin:0; border-radius:var(--card-radius);
}
.resize-handle-h.locked::after { content:'🔒'; font-size:0.7rem; opacity:0.6; }
.resize-handle-h.unlocked::after { content:'🔓'; font-size:0.7rem; opacity:0.6; }
.resize-handle-h.unlocked:hover { background:var(--accent-light); cursor:col-resize; }

.panel {
  background:var(--card);
  border:1px solid var(--border); border-radius:var(--panel-radius);
  overflow:hidden;
  display:flex; flex-direction:column; flex-shrink:0; position:relative;
}
.panel-hd {
  display:flex; align-items:center; gap:8px; padding:10px 14px;
  border-bottom:1px solid var(--divider); font-weight:700; font-size:0.7rem;
  text-transform:uppercase; letter-spacing:0.04em; background:var(--card);
  flex-shrink:0; border-radius:var(--panel-radius) var(--panel-radius) 0 0;
  justify-content:space-between;
}
.panel-hd i { width:3px; height:16px; background:var(--accent); border-radius:2px; box-shadow:0 0 6px var(--accent-glow); }
.panel-title-group { display:flex; align-items:center; gap:8px; }
.size-badge {
  font-size:0.55rem; font-weight:500; background:var(--accent-light);
  padding:2px 8px; border-radius:6px; color:var(--accent); white-space:nowrap;
}
.panel-body {
  padding:12px 14px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;
  flex:1; min-height:0;
}
.empty-hint {
  font-size:0.6rem; color:var(--text3); text-align:center; padding:20px 10px;
  line-height:1.6;
}
.resize-handle-v {
  height:6px; background:transparent; cursor:row-resize; flex-shrink:0;
  transition:background 0.2s; border-radius:0 0 var(--panel-radius) var(--panel-radius);
  display:flex; align-items:center; justify-content:center;
}
.resize-handle-v::after {
  content:''; width:30px; height:2px; background:var(--resize-handle-color);
  border-radius:1px; transition:0.2s;
}
.resize-handle-v:hover { background:var(--accent-light); }
.resize-handle-v:hover::after { background:var(--accent); }

.knowledge-mini {
  background:var(--card); border:1.5px solid var(--accent); border-radius:var(--card-radius);
  padding:12px 14px; display:flex; align-items:center; gap:12px;
  animation:slideIn 0.4s; flex-shrink:0;
}
@keyframes slideIn { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
.k-icon { width:36px; height:36px; background:var(--accent-light); border-radius:var(--card-radius); display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }
.k-info { flex:1; min-width:0; }
.k-title { font-weight:700; font-size:0.68rem; color:var(--accent); }
.k-formula { font-size:0.7rem; margin-top:2px; }
.k-mastery { font-size:0.55rem; color:var(--text3); margin-top:2px; }
.error-entry {
  background:rgba(239,68,68,0.06); border-left:3px solid var(--red); border-radius:var(--card-radius);
  padding:10px 12px; font-size:0.62rem; display:flex; align-items:flex-start; gap:8px;
  animation:slideIn 0.4s; flex-shrink:0;
}
.e-tag { background:rgba(239,68,68,0.12); color:var(--red); font-weight:700; font-size:0.55rem; padding:3px 8px; border-radius:6px; white-space:nowrap; flex-shrink:0; }
.strategy-entry {
  background:var(--accent-light); border-radius:var(--card-radius); padding:10px 12px;
  font-size:0.62rem; display:flex; align-items:center; gap:8px;
  animation:slideIn 0.4s; flex-shrink:0;
}
.s-dot { width:8px; height:8px; background:var(--accent); border-radius:2px; flex-shrink:0; }

.tutor-panel {
  background:var(--card);
  border:1px solid var(--border); border-radius:var(--panel-radius);
  overflow:hidden;
  display:flex; flex-direction:column; flex:1; min-height:0;
}
.tutor-header {
  padding:8px 16px; border-bottom:1px solid var(--divider);
  display:flex; align-items:center; gap:10px; font-weight:700; font-size:0.7rem;
  background:var(--card); justify-content:space-between; flex-shrink:0;
  border-radius:var(--panel-radius) var(--panel-radius) 0 0;
}
.tutor-avatar { width:34px; height:34px; background:var(--accent); border-radius:var(--card-radius); display:flex; align-items:center; justify-content:center; font-size:1.2rem; color:#fff; box-shadow:0 0 10px var(--accent-glow); }
.header-right { display:flex; gap:6px; align-items:center; }
.mode-switch { display:flex; gap:4px; }
.mode-btn {
  padding:5px 12px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-weight:700; font-size:0.62rem; cursor:pointer;
  transition:0.2s; border-radius:var(--card-radius);
}
.mode-btn.active { background:var(--accent); color:#fff; }
.view-toggle-btn {
  padding:5px 14px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-weight:700; font-size:0.62rem; cursor:pointer;
  transition:0.2s; border-radius:var(--card-radius);
}
.view-toggle-btn:hover { background:var(--accent-light); }
.view-toggle-btn.answering { background:var(--accent); color:#fff; }
.chat-view { flex:1; display:flex; flex-direction:column; min-height:0; }
.chat-view.hidden { display:none; }
.tutor-messages { flex:1; overflow-y:auto; padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
.tutor-msg {
  background:var(--tutor-msg-bg); border-left:3px solid var(--accent);
  padding:10px 12px; font-size:0.63rem; line-height:1.6;
  animation:slideIn 0.35s; border-radius:0 var(--card-radius) var(--card-radius) 0;
}
.tutor-msg.msg-student { border-left-color: var(--green); background: rgba(13,148,136,0.06); }
.tutor-msg.msg-system { border-left-color: var(--text3); background: rgba(0,0,0,0.03); }
.typing-indicator { animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.5} }
.chat-bottom-bar {
  padding:8px 14px; border-top:1px solid var(--divider);
  display:flex; gap:8px; align-items:center; flex-shrink:0;
}
.student-input {
  flex:1; padding:8px 12px; border:2px solid var(--accent); border-radius:var(--card-radius);
  background:var(--card); color:var(--text); font-size:0.65rem; font-family:inherit;
}
.student-input:focus { outline:none; border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-light); }
.send-btn {
  padding:8px 14px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.65rem; border:none; cursor:pointer; border-radius:var(--card-radius);
  white-space:nowrap;
}
.send-btn:disabled { opacity:0.6; cursor:not-allowed; }
.start-answer-btn {
  padding:10px 22px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.7rem; border:none; cursor:pointer; box-shadow:0 0 10px var(--accent-glow);
  border-radius:var(--card-radius); white-space:nowrap;
}
.answer-view { flex:1; display:flex; flex-direction:column; min-height:0; }
.answer-view.hidden { display:none; }
.qa-top { flex:1; display:flex; flex-direction:column; padding:14px 16px; gap:6px; border-bottom:1px solid var(--divider); min-height:0; }
.qa-bottom { flex:1; padding:14px 16px; display:flex; flex-direction:column; gap:8px; min-height:0; }
.question-box {
  flex:1; border:2px solid var(--quiz-border); padding:16px 18px; font-size:0.7rem;
  font-weight:500; display:flex; align-items:flex-start; overflow-y:auto;
  background:var(--quiz-bg); color:var(--text); border-radius:var(--card-radius);
  line-height:1.6; min-height:0;
}
.question-textarea {
  width:100%; height:100%; border:none; background:transparent; resize:none;
  font-size:0.7rem; font-family:inherit; line-height:1.6; color:var(--text);
}
.question-textarea:focus { outline:none; }
.ai-notice {
  width:100%; text-align:center; color:var(--text3); font-size:0.7rem;
  display:flex; align-items:center; justify-content:center; height:100%;
}
/* AI Recommend Form */
.ai-recommend-form {
  width:100%; display:flex; flex-direction:column; gap:14px; padding:4px 0;
}
.ai-form-section { display:flex; flex-direction:column; gap:6px; }
.ai-form-label { font-weight:700; font-size:0.65rem; color:var(--accent); }
.ai-form-hint { font-size:0.55rem; color:var(--text3); margin:0; }
.ai-mode-switch { display:flex; gap:6px; }
.ai-mode-btn {
  flex:1; padding:8px 12px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-weight:700; font-size:0.62rem; cursor:pointer;
  transition:0.2s; border-radius:var(--card-radius); text-align:center;
}
.ai-mode-btn.active { background:var(--accent); color:#fff; }
.ai-custom-input {
  width:100%; padding:10px 12px; border:2px solid var(--accent); border-radius:var(--card-radius);
  background:var(--card); color:var(--text); font-size:0.65rem; font-family:inherit;
  resize:none; line-height:1.5;
}
.ai-custom-input:focus { outline:none; box-shadow:0 0 0 3px var(--accent-light); }
.ai-num-control { display:flex; align-items:center; gap:10px; }
.ai-num-btn {
  width:32px; height:32px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-size:1rem; font-weight:700; cursor:pointer;
  border-radius:var(--card-radius); display:flex; align-items:center; justify-content:center;
  transition:0.2s;
}
.ai-num-btn:hover { background:var(--accent-light); }
.ai-num-value { font-size:1rem; font-weight:700; color:var(--text); min-width:24px; text-align:center; }
.ai-generate-btn {
  padding:12px 24px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.7rem; border:none; cursor:pointer; border-radius:var(--card-radius);
  box-shadow:0 0 10px var(--accent-glow); transition:0.2s; align-self:stretch;
}
.ai-generate-btn:disabled { opacity:0.6; cursor:not-allowed; }
.ai-error { font-size:0.6rem; color:var(--red); text-align:center; }
/* AI Preview List */
.ai-preview {
  width:100%; display:flex; flex-direction:column; gap:8px; overflow-y:auto;
}
.ai-preview-header {
  display:flex; align-items:center; justify-content:space-between;
  font-weight:700; font-size:0.65rem; color:var(--accent); padding-bottom:4px;
  border-bottom:1px solid var(--divider); flex-shrink:0;
}
.ai-preview-clear {
  padding:4px 10px; border:1.5px solid var(--red); background:transparent;
  color:var(--red); font-size:0.55rem; font-weight:600; cursor:pointer;
  border-radius:var(--card-radius); transition:0.2s;
}
.ai-preview-clear:hover { background:rgba(239,68,68,0.08); }
.ai-preview-item {
  display:flex; align-items:center; gap:8px; padding:10px 12px;
  border:1.5px solid var(--border); border-radius:var(--card-radius);
  cursor:pointer; transition:all 0.2s; font-size:0.63rem;
}
.ai-preview-item:hover { border-color:var(--accent); background:var(--accent-light); }
.ai-q-type {
  font-size:0.5rem; font-weight:700; background:var(--accent-light);
  color:var(--accent); padding:2px 8px; border-radius:6px; white-space:nowrap; flex-shrink:0;
}
.ai-q-content { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ai-q-points { font-size:0.5rem; color:var(--text3); flex-shrink:0; }
/* AI Question Detail */
.ai-question-detail { width:100%; display:flex; flex-direction:column; gap:10px; }
.ai-back-btn {
  align-self:flex-start; padding:4px 10px; border:1.5px solid var(--accent);
  background:transparent; color:var(--accent); font-size:0.58rem; font-weight:600;
  cursor:pointer; border-radius:var(--card-radius); transition:0.2s;
}
.ai-back-btn:hover { background:var(--accent-light); }
.ai-q-full { display:flex; align-items:center; gap:8px; }
.ai-q-stem { font-size:0.68rem; line-height:1.6; color:var(--text); }
.ai-q-options { display:flex; flex-direction:column; gap:4px; padding-left:8px; }
.ai-q-opt { font-size:0.63rem; color:var(--text2); line-height:1.5; }
/* AI Main View + Tabs */
.ai-main-view { width:100%; display:flex; flex-direction:column; min-height:0; flex:1; }
.ai-tabs {
  display:flex; gap:0; border-bottom:2px solid var(--divider); flex-shrink:0;
  margin:-4px -4px 0 -4px; padding:0 4px;
}
.ai-tab {
  padding:8px 16px; border:none; background:transparent; color:var(--text3);
  font-weight:700; font-size:0.62rem; cursor:pointer; transition:0.2s;
  border-bottom:2px solid transparent; margin-bottom:-2px; display:flex;
  align-items:center; gap:4px;
}
.ai-tab:hover { color:var(--accent); }
.ai-tab.active { color:var(--accent); border-bottom-color:var(--accent); }
.ai-tab-badge {
  font-size:0.5rem; background:var(--accent); color:#fff; padding:1px 6px;
  border-radius:8px; min-width:16px; text-align:center;
}
.ai-tab-body {
  flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px;
  padding:10px 2px 4px;
}
/* AI Bank */
.ai-bank-body { gap:8px; }
.ai-bank-empty {
  text-align:center; color:var(--text3); font-size:0.65rem;
  padding:40px 10px; line-height:1.8;
}
.ai-bank-list { display:flex; flex-direction:column; gap:6px; }
.ai-bank-header {
  display:flex; align-items:center; justify-content:space-between;
  font-size:0.58rem; color:var(--text3); padding-bottom:4px; flex-shrink:0;
}
.ai-bank-clear {
  padding:3px 10px; border:1.5px solid var(--red); background:transparent;
  color:var(--red); font-size:0.52rem; font-weight:600; cursor:pointer;
  border-radius:var(--card-radius); transition:0.2s;
}
.ai-bank-clear:hover { background:rgba(239,68,68,0.08); }
.ai-bank-item {
  display:flex; align-items:center; gap:4px;
  border:1.5px solid var(--border); border-radius:var(--card-radius);
  transition:all 0.2s; overflow:hidden;
}
.ai-bank-item:hover { border-color:var(--accent); }
.ai-bank-item-main {
  flex:1; display:flex; align-items:center; gap:8px; padding:10px 12px;
  cursor:pointer; min-width:0;
}
.ai-bank-item-main:hover { background:var(--accent-light); }
.ai-bank-item-content {
  flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font-size:0.63rem;
}
.ai-bank-item-del {
  padding:0 10px; height:100%; border:none; background:transparent;
  color:var(--text3); font-size:0.7rem; cursor:pointer; transition:0.2s;
  align-self:stretch; display:flex; align-items:center;
}
.ai-bank-item-del:hover { background:rgba(239,68,68,0.08); color:var(--red); }
/* AI Batch Group */
.ai-batch-group {
  border:1.5px solid var(--border); border-radius:var(--card-radius); overflow:hidden;
}
.ai-batch-header {
  display:flex; align-items:center; gap:8px; padding:10px 12px;
  cursor:pointer; transition:background 0.2s; background:var(--card);
}
.ai-batch-header:hover { background:var(--accent-light); }
.ai-batch-arrow {
  font-size:0.5rem; color:var(--text3); transition:transform 0.2s; flex-shrink:0;
  width:12px; text-align:center;
}
.ai-batch-arrow.expanded { transform:rotate(90deg); }
.ai-batch-label {
  flex:1; font-weight:600; font-size:0.63rem; color:var(--text);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.ai-batch-meta { font-size:0.5rem; color:var(--text3); flex-shrink:0; }
.ai-batch-del {
  padding:2px 6px; border:none; background:transparent; color:var(--text3);
  font-size:0.65rem; cursor:pointer; transition:0.2s; border-radius:4px;
}
.ai-batch-del:hover { background:rgba(239,68,68,0.08); color:var(--red); }
.ai-batch-questions {
  border-top:1px solid var(--divider); padding:6px; display:flex; flex-direction:column; gap:4px;
  background:var(--quiz-bg);
}
.ai-batch-questions .ai-bank-item { border-color:transparent; }
.ai-batch-questions .ai-bank-item:hover { border-color:var(--accent); }
.answer-input {
  flex:1; border:2px solid var(--quiz-border); padding:16px 18px;
  font-size:0.68rem; font-family:inherit; resize:none; border-radius:var(--card-radius);
  line-height:1.6; background:var(--card); color:var(--text); min-height:0;
}
.upload-row { display:flex; gap:6px; align-items:center; margin-top:4px; flex-shrink:0; }
.file-label {
  padding:5px 12px; border:2px solid var(--accent); background:transparent;
  cursor:pointer; font-size:0.6rem; font-weight:600; color:var(--accent);
  border-radius:var(--card-radius); transition:0.2s;
}
.file-label:hover { background:var(--accent-light); }
.submit-row { display:flex; gap:8px; justify-content:flex-end; flex-shrink:0; }
.submit-btn {
  padding:10px 26px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.68rem; border:none; cursor:pointer; box-shadow:0 0 8px var(--accent-glow);
  border-radius:var(--card-radius);
}
.submit-btn:disabled { opacity:0.6; cursor:not-allowed; }
.progress-bar {
  flex-shrink:0; height:32px; background:var(--card); border:2px solid var(--accent);
  border-radius:var(--panel-radius); display:flex; align-items:center; padding:0 14px;
  gap:8px; font-size:0.58rem;
}
.progress-fill { height:6px; background:var(--accent); border-radius:3px; transition:width 0.5s; }
@media (max-width:768px) {
  .main-wrapper { flex-direction:column; }
  .resize-handle-h { display:none; }
  .left-area, .right-area { width:100%!important; min-width:0; }
  .left-area { max-height:40%; }
  .right-area { flex:1; }
}

/* Homework picker dialog */
.picker-overlay {
  position:fixed; top:0; left:0; right:0; bottom:0;
  background:rgba(0,0,0,0.5); z-index:1000;
  display:flex; align-items:center; justify-content:center;
}
.picker-dialog {
  background:var(--card); border:2px solid var(--accent); border-radius:var(--panel-radius);
  width:480px; max-width:90vw; max-height:70vh; display:flex; flex-direction:column;
  box-shadow:0 8px 32px rgba(0,0,0,0.2);
}
.picker-header {
  padding:12px 16px; border-bottom:1px solid var(--divider);
  display:flex; align-items:center; justify-content:space-between;
  font-weight:700; font-size:0.75rem; flex-shrink:0;
}
.picker-close {
  width:28px; height:28px; border:none; background:transparent;
  cursor:pointer; font-size:0.8rem; color:var(--text3); border-radius:50%;
  display:flex; align-items:center; justify-content:center;
}
.picker-close:hover { background:var(--accent-light); color:var(--accent); }
.picker-body { flex:1; overflow-y:auto; padding:12px 16px; }
.picker-breadcrumb {
  font-size:0.6rem; color:var(--text3); margin-bottom:12px;
}
.picker-breadcrumb span { cursor:pointer; }
.picker-breadcrumb span:hover { color:var(--accent); }
.picker-breadcrumb span.active { color:var(--accent); font-weight:600; }
.picker-list { display:flex; flex-direction:column; gap:8px; }
.picker-loading { text-align:center; padding:24px; color:var(--text3); font-size:0.65rem; }
.picker-empty { text-align:center; padding:24px; color:var(--text3); font-size:0.65rem; }
.picker-item {
  background:var(--card); border:1.5px solid var(--border); border-radius:var(--card-radius);
  padding:12px 14px; cursor:pointer; transition:all 0.2s;
}
.picker-item:hover { border-color:var(--accent); background:var(--accent-light); }
.picker-item-content { flex:1; min-width:0; }
.picker-item-title { font-weight:600; font-size:0.68rem; color:var(--text); }
.picker-item-opts { font-size:0.5rem; color:var(--accent); margin-top:2px; }
.picker-item-desc { font-size:0.55rem; color:var(--text3); margin-top:2px; }
.picker-question { display:flex; align-items:center; gap:10px; }
.picker-q-type {
  font-size:0.5rem; font-weight:700; background:var(--accent-light);
  color:var(--accent); padding:2px 8px; border-radius:6px; white-space:nowrap; flex-shrink:0;
}
.picker-item-right { display:flex; align-items:center; gap:8px; margin-left:auto; flex-shrink:0; }
.picker-answered {
  font-size:0.5rem; font-weight:600; color:var(--green);
  background:rgba(13,148,136,0.1); padding:2px 8px; border-radius:6px;
}
</style>
