<template>
  <div class="tutor-page">
    <!-- 主内容区：左侧学情看板 + 右侧AI导师 -->
    <div class="main-content">
      <!-- 左侧：三段学情诊断看板 -->
      <aside class="diagnosis-panel">
        <!-- 知识点巩固 -->
        <section class="diagnosis-section">
          <div class="section-header">
            <span class="section-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
              </svg>
              知识点巩固
            </span>
            <span class="count-badge">{{ knowledgeItems.length }} 项</span>
          </div>
          <div class="section-body">
            <div v-if="knowledgeItems.length === 0" class="empty-state">
              开始答题后，知识点掌握情况将在这里显示
            </div>
            <div v-for="(item, i) in knowledgeItems" :key="'k'+i" class="knowledge-card">
              <div class="k-icon">📐</div>
              <div class="k-info">
                <div class="k-title">{{ item.title }}</div>
                <div class="k-formula" v-if="item.formula" v-html="renderFormula(item.formula)"></div>
                <div class="k-mastery" :class="masteryClass(item.mastery)">
                  {{ formatMastery(item.mastery) }}
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 错题归因 -->
        <section class="diagnosis-section">
          <div class="section-header">
            <span class="section-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>
              </svg>
              错题归因
            </span>
            <span class="count-badge">{{ errorItems.length }} 项</span>
          </div>
          <div class="section-body">
            <div v-if="errorItems.length === 0" class="empty-state">
              答错题目时，错误分析将在这里显示
            </div>
            <div v-for="(item, i) in errorItems" :key="'e'+i" class="error-card">
              <span class="error-tag">{{ item.type }}</span>
              <div class="error-content">
                <strong>{{ item.title }}</strong>
                <p>{{ item.detail }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 学习策略 -->
        <section class="diagnosis-section">
          <div class="section-header">
            <span class="section-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>
              </svg>
              学习策略
            </span>
            <span class="count-badge">{{ strategyItems.length }} 项</span>
          </div>
          <div class="section-body">
            <div v-if="strategyItems.length === 0" class="empty-state">
              AI 将根据你的答题表现生成个性化学习建议
            </div>
            <div v-for="(item, i) in strategyItems" :key="'s'+i" class="strategy-card">
              <span class="strategy-dot"></span>
              <span>{{ item }}</span>
            </div>
          </div>
        </section>
      </aside>

      <!-- 右侧：AI 导师主区域 -->
      <main class="tutor-main">
        <!-- 头部控制栏 -->
        <header class="tutor-header">
          <div class="header-left">
            <div class="tutor-icon">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
              </svg>
            </div>
            <span class="tutor-label">AI 导师</span>
          </div>
          <div class="header-actions">
            <button
              class="action-btn"
              :class="{ active: currentMode === 'my' }"
              @click="switchMode('my')"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>
              </svg>
              我的题目
            </button>
            <button
              class="action-btn"
              :class="{ active: currentMode === 'ai' }"
              @click="switchMode('ai')"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
              </svg>
              AI 推题
            </button>
            <button
              class="action-btn"
              :class="{ active: currentView === 'chat' }"
              @click="currentView = 'chat'"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
              </svg>
              对话
            </button>
          </div>
        </header>

        <!-- 对话视图 -->
        <div class="chat-container" v-show="currentView === 'chat'">
          <div class="chat-mode-bar">
            <span class="chat-mode-label">对话模式：</span>
            <span class="chat-mode-chip" :class="{ on: chatMode === '' }" @click="chatMode = ''">自由对话</span>
            <span class="chat-mode-chip" :class="{ on: chatMode === 'socratic' }" @click="chatMode = 'socratic'">苏格拉底式引导</span>
            <span class="chat-mode-chip" :class="{ on: chatMode === 'scenario' }" @click="chatMode = 'scenario'">复杂场景练习</span>
          </div>
          <div class="messages-area" ref="tutorMessages">
            <div
              v-for="(msg, i) in chatMessages"
              :key="i"
              class="message-row"
              :class="'msg-' + msg.role"
            >
              <div class="msg-avatar" v-if="msg.role === 'ai'">AI</div>
              <div class="msg-bubble">
                <span v-html="renderMessageContent(msg.content)"></span>
              </div>
            </div>
            <div v-if="isChatLoading" class="message-row msg-ai">
              <div class="msg-avatar">AI</div>
              <div class="msg-bubble typing">正在思考中...</div>
            </div>
          </div>
          <div class="input-bar">
            <div class="input-wrapper">
              <input
                type="text"
                v-model="studentQuestion"
                placeholder="向导师提问，例如：什么是消光系数？"
                @keyup.enter="askQuestion"
              >
              <div class="input-actions">
                <button class="send-btn" @click="askQuestion" :disabled="isChatLoading">
                  发送
                </button>
                <button class="switch-btn" @click="currentView = 'answer'">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  </svg>
                  答题
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 答题视图 -->
        <div class="answer-container" v-show="currentView === 'answer'">
          <div class="answer-scroll">
            <!-- 我的题目模式 -->
            <div v-if="currentMode === 'my'" class="my-question-section">
              <textarea
                v-model="questionInput"
                placeholder="📝 在这里输入或粘贴题目内容..."
                class="question-textarea"
              ></textarea>
              <div class="question-actions">
                <button class="picker-btn" @click="openHomeworkPicker">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
                  </svg>
                  从作业选题
                </button>
                <label class="picker-btn" for="fileInput">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                  </svg>
                  上传题目
                </label>
                <input type="file" id="fileInput" ref="fileInput" style="display:none;" accept=".txt,.doc,.docx,.pdf" multiple @change="handleFileUpload">
              </div>
            </div>

            <!-- AI推题模式 -->
            <div v-else class="ai-recommend-section">
              <!-- 二级 Tab -->
              <div class="sub-tabs">
                <button
                  class="sub-tab"
                  :class="{ active: aiTab === 'generate' }"
                  @click="aiTab = 'generate'"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                  </svg>
                  推题
                </button>
                <button
                  class="sub-tab"
                  :class="{ active: aiTab === 'bank' }"
                  @click="aiTab = 'bank'"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
                  </svg>
                  题库
                  <span v-if="bankTotalCount > 0" class="sub-tab-badge">{{ bankTotalCount }}</span>
                </button>
              </div>

              <!-- 推题 Tab 内容 -->
              <div v-if="aiTab === 'generate'" class="generate-form">
                <!-- 推题模式选择器 -->
                <div class="form-section">
                  <label class="form-label">推题模式</label>
                  <div class="mode-cards">
                    <div
                      class="mode-card"
                      :class="{ active: aiRecommendMode === 'auto' }"
                      @click="aiRecommendMode = 'auto'"
                    >
                      <div class="mode-card-left">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
                        </svg>
                        <span class="mode-card-title">智能推题</span>
                      </div>
                      <svg v-if="aiRecommendMode === 'auto'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>
                      </svg>
                    </div>
                    <div
                      class="mode-card"
                      :class="{ active: aiRecommendMode === 'custom' }"
                      @click="aiRecommendMode = 'custom'"
                    >
                      <div class="mode-card-left">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>
                        </svg>
                        <span class="mode-card-title">指定内容</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 知识点输入区域 -->
                <div class="form-section">
                  <label class="form-label">输入你想练习的知识点或内容</label>
                  <div class="input-box">
                    <input
                      type="text"
                      v-model="aiCustomContent"
                      placeholder="输入知识点、教材内容或你想练习的主题..."
                    >
                  </div>
                </div>

                <!-- 题目数量选择器 -->
                <div class="form-section">
                  <label class="form-label">题目数量</label>
                  <div class="num-selector">
                    <button class="num-btn" @click="aiRecommendNum = Math.max(1, aiRecommendNum - 1)">-</button>
                    <div class="num-display">{{ aiRecommendNum }}</div>
                    <button class="num-btn" @click="aiRecommendNum = Math.min(20, aiRecommendNum + 1)">+</button>
                  </div>
                </div>

                <!-- 开始推题按钮 -->
                <button
                  class="generate-btn"
                  @click="handleAIRecommend"
                  :disabled="aiRecommendLoading || (aiRecommendMode === 'custom' && !aiCustomContent.trim())"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  <span>{{ aiRecommendLoading ? '生成中...' : '开始推题' }}</span>
                </button>

                <div v-if="aiRecommendError" class="error-msg">{{ aiRecommendError }}</div>
              </div>

              <!-- 题库 Tab 内容 -->
              <div v-if="aiTab === 'bank'" class="bank-section">
                <div v-if="aiBatches.length === 0" class="bank-empty">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
                  </svg>
                  <span>题库为空，请先生成题目</span>
                </div>
                <div v-else class="bank-list">
                  <div class="bank-header">
                    <span>{{ aiBatches.length }} 批 · 共 {{ bankTotalCount }} 道题</span>
                    <button class="clear-btn" @click="handleClearBank">清空</button>
                  </div>
                  <div v-for="(batch, bi) in aiBatches" :key="batch.id" class="batch-group">
                    <div class="batch-header" @click="toggleBatch(batch.id)">
                      <span class="batch-arrow" :class="{ expanded: aiExpandedBatches.has(batch.id) }">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="m9 18 6-6-6-6"/>
                        </svg>
                      </span>
                      <span class="batch-label">
                        {{ batch.mode === 'auto' ? '🎯 智能推题' : '📝 ' + (batch.content || '指定内容') }}
                      </span>
                      <span class="batch-meta">{{ (batch.questions || []).length }} 题 · {{ formatBatchTime(batch.createdAt) }}</span>
                      <button class="batch-del" @click.stop="handleDeleteBatch(bi)" title="删除此批">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                        </svg>
                      </button>
                    </div>
                    <div v-if="aiExpandedBatches.has(batch.id)" class="batch-questions">
                      <div
                        v-for="(q, qi) in (batch.questions || [])"
                        :key="qi"
                        class="question-item"
                        @click="startAIQuestion(q, batch.id)"
                      >
                        <span class="q-type">{{ questionTypeLabel(q.type) }}</span>
                        <span class="q-content">{{ q.content }}</span>
                        <span class="q-points">{{ q.points }}分</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 手写解答输入区 -->
            <div class="answer-section">
              <div class="answer-box">
                <textarea
                  class="answer-input"
                  v-model="answerInput"
                  placeholder="在这里写下你的解答..."
                ></textarea>
                <div class="answer-actions">
                  <button
                    class="submit-btn"
                    @click="submitAnswer"
                    :disabled="isEvaluating"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                    </svg>
                    <span>{{ isEvaluating ? 'AI 评估中...' : '提交回答' }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 底部进度条 -->
    <footer class="progress-footer">
      <div class="progress-info">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="m19 9-5 5-4-4-3 3"/>
        </svg>
        <span>辅导进度</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: Math.min(submissionCount * 10, 100) + '%' }"></div>
      </div>
      <span class="progress-count">{{ submissionCount }} 次提交</span>
    </footer>

    <!-- 从作业选题弹窗 -->
    <Teleport to="body">
      <div class="picker-overlay" v-if="showPicker" @click.self="closePicker">
        <div class="picker-dialog">
          <div class="picker-header">
            <span>📚 从作业选题</span>
            <button class="picker-close" @click="closePicker">✕</button>
          </div>
          <div class="picker-body">
            <div class="picker-breadcrumb">
              <span :class="{ active: pickerStep === 'courses' }" @click="pickerStep = 'courses'">课程</span>
              <span v-if="selectedCourse"> / {{ selectedCourse.courseName }}</span>
              <span v-if="selectedHomework"> / {{ selectedHomework.title }}</span>
            </div>
            <div v-if="pickerStep === 'courses'" class="picker-list">
              <div v-if="pickerLoading" class="picker-loading">加载中...</div>
              <div v-else-if="courses.length === 0" class="picker-empty">暂无课程，请先加入课程</div>
              <div v-for="c in courses" :key="c.courseId" class="picker-item" @click="selectCourse(c)">
                <div class="picker-item-title">{{ c.courseName }}</div>
                <div class="picker-item-desc">{{ c.subject }} · {{ c.grade }}</div>
              </div>
            </div>
            <div v-if="pickerStep === 'homework'" class="picker-list">
              <div v-if="pickerLoading" class="picker-loading">加载中...</div>
              <div v-else-if="homeworkList.length === 0" class="picker-empty">该课程暂无作业</div>
              <div v-for="hw in homeworkList" :key="hw.hwId" class="picker-item" @click="selectHomework(hw)">
                <div class="picker-item-title">{{ hw.title }}</div>
                <div class="picker-item-desc">{{ hw.description || '暂无描述' }}</div>
              </div>
            </div>
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import katex from 'katex'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useTutorAssistant } from '../../composables/useTutorAssistant.js'

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
const currentMode = ref('ai')
const currentView = ref('answer')
const chatMode = ref('')  // '' = free chat, 'socratic' = 苏格拉底, 'scenario' = 场景练习
const studentQuestion = ref('')
const questionInput = ref('')
const answerInput = ref('')
const referenceAnswer = ref('')
const isEvaluating = ref(false)
const tutorMessages = ref(null)
const fileInput = ref(null)

// Homework picker state
const showPicker = ref(false)
const pickerStep = ref('courses')
const pickerLoading = ref(false)
const courses = ref([])
const homeworkList = ref([])
const questionList = ref([])
const selectedCourse = ref(null)
const selectedHomework = ref(null)
const submissionAnswers = ref({})

// AI recommend state
const aiRecommendLoading = ref(false)
const aiRecommendError = ref('')
const aiBatches = ref([])
const aiRecommendNum = ref(5)
const aiRecommendMode = ref('auto')
const aiCustomContent = ref('')
const aiCurrentQuestion = ref(null)
const aiCurrentBatchId = ref(null)
const aiTab = ref('generate')
const aiExpandedBatches = ref(new Set())

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
  return content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

function formatMastery(mastery) {
  if (mastery === undefined || mastery === null) return '待评估'
  const pct = Math.round(mastery * 100)
  if (pct >= 80) return `已掌握 (${pct}%)`
  if (pct >= 60) return `待巩固 (${pct}%)`
  return `需加强 (${pct}%)`
}

function masteryClass(mastery) {
  if (mastery === undefined || mastery === null) return 'pending'
  const pct = Math.round(mastery * 100)
  if (pct >= 80) return 'good'
  if (pct >= 60) return 'medium'
  return 'low'
}

function switchMode(mode) {
  currentMode.value = mode
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
    const { authGet } = useAuthFetch()
    const data = await authGet(`/api/courses/${course.courseId}/homework`)
    homeworkList.value = data.homework || data || []
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
    const { authGet } = useAuthFetch()
    const [hwData, subData] = await Promise.all([
      authGet(`/api/courses/${selectedCourse.value.courseId}/homework/${hw.hwId}`),
      authGet(`/api/courses/${selectedCourse.value.courseId}/homework/${hw.hwId}/submissions/${user.value.userId}`),
    ])
    if (hwData) {
      const hwDetail = hwData.homework || hwData
      questionList.value = hwDetail.questions || hwDetail.settings?.questions || []
    }
    if (subData) {
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
  let fullQuestion = content
  const options = q.options || q.choices || []
  if (options.length > 0) {
    const optText = options.map((opt, i) => {
      const label = String.fromCharCode(65 + i)
      const text = typeof opt === 'string' ? opt : (opt.text || opt.content || opt.label || '')
      return `${label}. ${text}`
    }).join('\n')
    fullQuestion = fullQuestion + '\n' + optText
  }
  questionInput.value = fullQuestion
  referenceAnswer.value = q.answer || q.explanation || q.referenceAnswer || ''
  const qid = q.id || q.questionId || ''
  const prevAnswer = submissionAnswers.value[qid] || submissionAnswers.value[`q${questionList.value.indexOf(q) + 1}`] || ''
  if (prevAnswer) {
    answerInput.value = prevAnswer
  }
  closePicker()
  currentMode.value = 'my'
}

async function askQuestion() {
  const q = studentQuestion.value.trim()
  if (!q) return
  studentQuestion.value = ''
  let context = ''
  if (chatMode.value === 'socratic') {
    context = '【苏格拉底引导模式】请用苏格拉底式引导法：不要直接给出答案。先引导学生观察特征 → 提出假设 → 验证假设 → 得出结论。用提问的方式一步步引导。\n学生问题：'
  } else if (chatMode.value === 'scenario') {
    context = '【复杂场景练习模式】请给学生一个综合性的植保案例（如：某地块作物出现异常症状）。让学生主动提问收集信息（土壤、天气、施肥记录等），不直接展示所有信息。当学生给出诊断后，评估其准确性。\n学生需求：'
  }
  await askTutor(context + q)
  nextTick(() => {
    if (tutorMessages.value) tutorMessages.value.scrollTop = tutorMessages.value.scrollHeight
  })
}

async function submitAnswer() {
  const answer = answerInput.value.trim()
  if (!answer) { alert('请输入你的解答'); return }

  const question = questionInput.value.trim() || aiCurrentQuestion.value?.content || ''
  if (!question) { alert('请先输入题目'); return }

  isEvaluating.value = true
  try {
    const result = await evaluateAnswer(question, answer, referenceAnswer.value)

    chatMessages.value.push({
      role: 'ai',
      content: `[答题评估] 题目：${question.slice(0, 60)}...\n你的解答：${answer.slice(0, 60)}...\n\n${result.isCorrect ? '✅ 回答正确' : '❌ 回答有误'}，得分：${result.score}分\n${result.analysis}${result.strategy ? '\n💡 ' + result.strategy : ''}`,
      timestamp: Date.now(),
    })

    answerInput.value = ''
    currentView.value = 'chat'
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
  questionInput.value = q.content
  referenceAnswer.value = q.answer || q.explanation || ''
}

function toggleBatch(batchId) {
  const s = aiExpandedBatches.value
  if (s.has(batchId)) {
    s.delete(batchId)
  } else {
    s.add(batchId)
  }
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

// ---- Init ----
onMounted(async () => {
  const savedTheme = localStorage.getItem('nanobot-theme')
  if (savedTheme && ['white', 'dark', 'green'].includes(savedTheme)) {
    document.body.classList.remove('dark', 'green', 'white')
    if (savedTheme !== 'white') {
      document.body.classList.add(savedTheme)
    }
  }

  if (user.value && !connected.value) {
    try {
      await connect({ role: user.value.role, userId: user.value.userId })
    } catch (e) {
      console.error('[tutor] Gateway connect failed:', e.message)
    }
  }

  subscribeToChat()
  await fetchProfile()

  if (tutorProfile.value?.recommendedQuestions?.length > 0) {
    const raw = tutorProfile.value.recommendedQuestions
    if (raw[0]?.questions) {
      aiBatches.value = raw
    } else {
      aiBatches.value = [{ id: 'b_legacy', mode: 'auto', content: '', createdAt: '', questions: raw }]
    }
    const lastBatch = aiBatches.value[aiBatches.value.length - 1]
    if (lastBatch?.id) aiExpandedBatches.value.add(lastBatch.id)
  }

  if (chatMessages.value.length === 0) {
    chatMessages.value.push({
      role: 'ai',
      content: '👋 欢迎使用 AI 学伴辅导！你可以直接向我提问，也可以切换到"答题"模式输入题目和解答，我会为你进行智能评估。',
      timestamp: Date.now(),
    })
  }
})

function useAuthFetch() {
  const u = user.value
  const params = new URLSearchParams({ role: u.role, user_id: u.userId, token: getToken() || '' })
  return {
    authGet: async (url) => {
      const resp = await fetch(`${url}?${params}`)
      if (resp.ok) return resp.json()
      throw new Error(`HTTP ${resp.status}`)
    }
  }
}
</script>

<style scoped>
/* ===== 页面布局 ===== */
.tutor-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 2fr;
  overflow: hidden;
}

/* ===== 左侧诊断面板 ===== */
.diagnosis-panel {
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.diagnosis-section {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  min-height: 180px;
}

.diagnosis-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #121212;
}

.section-title svg {
  color: #666;
}

.count-badge {
  font-size: 10px;
  background: #f4f4f4;
  padding: 2px 8px;
  border-radius: 4px;
  color: #999;
  font-family: monospace;
}

.section-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #999;
  font-family: 'Noto Serif SC', serif;
}

/* 知识点卡片 */
.knowledge-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9f8;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

.k-icon {
  width: 36px;
  height: 36px;
  background: #f4f4f4;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.k-info {
  flex: 1;
  min-width: 0;
}

.k-title {
  font-weight: 600;
  font-size: 13px;
  color: #121212;
}

.k-formula {
  font-size: 12px;
  margin-top: 4px;
  color: #666;
}

.k-mastery {
  font-size: 11px;
  margin-top: 4px;
  font-weight: 500;
}

.k-mastery.good { color: #16a34a; }
.k-mastery.medium { color: #f59e0b; }
.k-mastery.low { color: #ef4444; }
.k-mastery.pending { color: #999; }

/* 错误卡片 */
.error-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.04);
  border-radius: 10px;
  border-left: 3px solid #ef4444;
}

.error-tag {
  font-size: 10px;
  font-weight: 600;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
  font-size: 12px;
  line-height: 1.5;
}

.error-content strong {
  display: block;
  color: #121212;
  margin-bottom: 4px;
}

.error-content p {
  color: #666;
  margin: 0;
}

/* 策略卡片 */
.strategy-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8f9f8;
  border-radius: 10px;
  font-size: 12px;
  color: #232824;
}

.strategy-dot {
  width: 6px;
  height: 6px;
  background: #121212;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ===== 右侧导师主区域 ===== */
.tutor-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tutor-header {
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tutor-icon {
  width: 28px;
  height: 28px;
  background: #f4f4f4;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #121212;
}

.tutor-label {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
}

.header-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #f0f0f0;
  background: #ffffff;
  color: #666;
  font-size: 11px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #f8f9f8;
  color: #121212;
}

.action-btn.active {
  background: #121212;
  color: #ffffff;
  border-color: #121212;
}

.mode-sep { width:1px; height:20px; background:#f0f0f0; margin:0 4px; }
body.green .chat-mode-bar { border-bottom-color: #dee2de; }
body.green .chat-mode-chip.on { background: rgba(82,110,90,0.08); color: #526e5a; border-color: rgba(82,110,90,0.3); }
body.dark .chat-mode-bar { border-bottom-color: #2d2d2d; }
body.dark .chat-mode-label { color: #777; }
body.dark .chat-mode-chip { color: #777; }
body.dark .chat-mode-chip:hover { color: #fff; }
body.dark .chat-mode-chip.on { background: rgba(255,255,255,0.08); color: #fff; border-color: rgba(255,255,255,0.2); }

/* ===== 对话视图 ===== */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-mode-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.chat-mode-label {
  font-size: 11px;
  color: #999;
  margin-right: 4px;
}

.chat-mode-chip {
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 11px;
  font-weight: 500;
  color: #999;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.chat-mode-chip:hover {
  color: #526e5a;
}

.chat-mode-chip.on {
  background: rgba(82, 110, 90, 0.08);
  color: #526e5a;
  border-color: rgba(82, 110, 90, 0.3);
  font-weight: 600;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 85%;
}

.message-row.msg-student {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  background: #121212;
  color: #ffffff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

.msg-bubble {
  background: #f8f9f8;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.6;
  color: #232824;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.msg-student .msg-bubble {
  background: #121212;
  color: #ffffff;
  border-color: #121212;
}

.msg-bubble.typing {
  color: #999;
  font-style: italic;
}

.input-bar {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: center;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 8px 12px;
  background: #ffffff;
  transition: border-color 0.15s ease;
}

.input-wrapper:focus-within {
  border-color: #121212;
}

.input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 13px;
  color: #121212;
  background: transparent;
  padding: 4px 0;
}

.input-wrapper input::placeholder {
  color: #999;
}

.input-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.send-btn {
  padding: 8px 16px;
  background: #121212;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
}

.send-btn:hover {
  background: #333;
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fbf7ee;
  color: #75684d;
  border: 1px solid #f5ebd3;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.switch-btn:hover {
  background: #f5ebd3;
}

/* ===== 答题视图 ===== */
.answer-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.answer-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 我的题目模式 */
.my-question-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-textarea {
  width: 100%;
  min-height: 120px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #232824;
  resize: none;
  font-family: inherit;
  background: #ffffff;
  transition: border-color 0.15s ease;
}

.question-textarea:focus {
  outline: none;
  border-color: #121212;
}

.question-textarea::placeholder {
  color: #999;
}

.question-actions {
  display: flex;
  gap: 8px;
}

.picker-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid #e0e0e0;
  background: #ffffff;
  color: #666;
  font-size: 12px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.picker-btn:hover {
  background: #f8f9f8;
  border-color: #121212;
  color: #121212;
}

/* AI 推题模式 */
.ai-recommend-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sub-tabs {
  display: flex;
  gap: 16px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.sub-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  border: none;
  background: transparent;
  color: #999;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s ease;
  position: relative;
}

.sub-tab:hover {
  color: #121212;
}

.sub-tab.active {
  color: #121212;
  font-weight: 600;
}

.sub-tab.active svg {
  color: #f59e0b;
}

.sub-tab-badge {
  font-size: 10px;
  background: #121212;
  color: #ffffff;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

/* 推题表单 */
.generate-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 模式卡片 */
.mode-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mode-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #edf0ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  background: #ffffff;
}

.mode-card:hover {
  border-color: #ccc;
}

.mode-card.active {
  border: 2px solid #121212;
  background: #fafbfa;
}

.mode-card-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-card-left svg {
  color: #666;
}

.mode-card.active .mode-card-left svg {
  color: #121212;
}

.mode-card-title {
  font-size: 12px;
  font-weight: 500;
  color: #666;
}

.mode-card.active .mode-card-title {
  font-weight: 600;
  color: #121212;
}

.mode-card > svg {
  color: #121212;
}

/* 输入框 */
.input-box {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 10px 12px;
  background: #ffffff;
  transition: border-color 0.15s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.002);
}

.input-box:focus-within {
  border-color: #121212;
}

.input-box input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 13px;
  color: #121212;
  background: transparent;
}

.input-box input::placeholder {
  color: #ccc;
}

/* 数量选择器 */
.num-selector {
  display: flex;
  align-items: center;
  gap: 6px;
}

.num-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #e0e0e0;
  background: #ffffff;
  color: #666;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.num-btn:hover {
  background: #f9f9f9;
  border-color: #ccc;
}

.num-display {
  width: 40px;
  height: 28px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-size: 12px;
  font-weight: 600;
  color: #121212;
  background: #fafbfa;
}

/* 生成按钮 */
.generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 20px;
  background: #121212;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.generate-btn:hover {
  background: #333;
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  font-size: 12px;
  color: #ef4444;
  text-align: center;
}

/* 题库 */
.bank-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bank-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 16px;
  color: #999;
  font-size: 13px;
}

.bank-empty svg {
  color: #ccc;
}

.bank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bank-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
}

.clear-btn {
  padding: 4px 10px;
  border: 1px solid #e0e0e0;
  background: transparent;
  color: #666;
  font-size: 11px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clear-btn:hover {
  background: #f8f9f8;
  border-color: #ccc;
}

.batch-group {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.batch-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.batch-header:hover {
  background: #f8f9f8;
}

.batch-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  color: #999;
  transition: transform 0.2s ease;
}

.batch-arrow.expanded {
  transform: rotate(90deg);
}

.batch-label {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
  color: #232824;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batch-meta {
  font-size: 11px;
  color: #999;
}

.batch-del {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: #999;
  cursor: pointer;
  transition: all 0.15s ease;
  border-radius: 4px;
}

.batch-del:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

.batch-questions {
  border-top: 1px solid #f0f0f0;
  padding: 8px;
  background: #fafafa;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.question-item:hover {
  background: #f4f4f4;
}

.question-item .q-type {
  font-size: 10px;
  font-weight: 600;
  background: #f4f4f4;
  color: #666;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.question-item .q-content {
  flex: 1;
  font-size: 13px;
  color: #232824;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-item .q-points {
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
}

/* 答题区 */
.answer-section {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.answer-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 12px;
  background: #fdfdfd;
  transition: border-color 0.15s ease;
}

.answer-box:focus-within {
  border-color: #121212;
}

.answer-input {
  width: 100%;
  min-height: 64px;
  border: none;
  outline: none;
  font-size: 13px;
  line-height: 1.6;
  color: #232824;
  resize: none;
  font-family: 'Noto Serif SC', serif;
  background: transparent;
}

.answer-input::placeholder {
  color: #999;
}

.answer-actions {
  display: flex;
  justify-content: flex-end;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #fbf7ee;
  color: #75684d;
  border: 1px solid #f5ebd3;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.submit-btn:hover {
  background: #f5ebd3;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 底部进度条 ===== */
.progress-footer {
  height: 40px;
  background: #f8f9f8;
  border-top: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  flex-shrink: 0;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #121212;
}

.progress-info svg {
  color: #666;
}

.progress-bar {
  flex: 1;
  max-width: 300px;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #121212;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-count {
  font-size: 11px;
  color: #999;
  font-family: monospace;
}

/* ===== 作业选题弹窗 ===== */
.picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 480px;
  max-width: 90vw;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.picker-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 15px;
}

.picker-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  color: #999;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-close:hover {
  background: #f4f4f4;
  color: #121212;
}

.picker-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.picker-breadcrumb {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
}

.picker-breadcrumb span {
  cursor: pointer;
}

.picker-breadcrumb span:hover {
  color: #121212;
}

.picker-breadcrumb span.active {
  color: #121212;
  font-weight: 600;
}

.picker-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-loading {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 13px;
}

.picker-empty {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 13px;
}

.picker-item {
  background: #ffffff;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.picker-item:hover {
  border-color: #121212;
  background: #f8f9f8;
}

.picker-item-title {
  font-weight: 600;
  font-size: 14px;
  color: #232824;
}

.picker-item-desc {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.picker-question {
  display: flex;
  align-items: center;
  gap: 12px;
}

.picker-q-type {
  font-size: 10px;
  font-weight: 600;
  background: #f4f4f4;
  color: #666;
  padding: 3px 10px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.picker-item-content {
  flex: 1;
  min-width: 0;
}

.picker-item-opts {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.picker-item-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.picker-answered {
  font-size: 11px;
  font-weight: 600;
  color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
  padding: 3px 10px;
  border-radius: 4px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .diagnosis-panel {
    display: none;
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .mode-cards {
    grid-template-columns: 1fr;
  }
}

/* ===== 绿色主题 ===== */
body.green .tutor-page { background: #f7f8f7; }
body.green .diagnosis-panel { border-right-color: #dee2de; }
body.green .diagnosis-section { border-bottom-color: #dee2de; }
body.green .section-title { color: #2c332e; }
body.green .section-title svg { color: #526e5a; }
body.green .count-badge { background: #edf0ed; color: #526e5a; }
body.green .empty-state { color: #8fa091; }
body.green .knowledge-card { background: #edf0ed; border-color: #dee2de; }
body.green .k-icon { background: #dbe1db; }
body.green .k-title { color: #2c332e; }
body.green .k-formula { color: #556056; }
body.green .k-mastery.good { color: #526e5a; }
body.green .k-mastery.medium { color: #d97706; }
body.green .k-mastery.low { color: #dc2626; }
body.green .k-mastery.pending { color: #8fa091; }
body.green .error-card { background: rgba(220, 38, 38, 0.04); border-left-color: #dc2626; }
body.green .error-tag { background: rgba(220, 38, 38, 0.1); color: #dc2626; }
body.green .error-content strong { color: #2c332e; }
body.green .error-content p { color: #556056; }
body.green .strategy-card { background: #edf0ed; color: #2c332e; }
body.green .strategy-dot { background: #526e5a; }
body.green .tutor-header { border-bottom-color: #dee2de; background: #f7f8f7; }
body.green .tutor-icon { background: #dbe1db; color: #526e5a; }
body.green .tutor-label { color: #2c332e; }
body.green .action-btn { border-color: #dee2de; background: #f7f8f7; color: #556056; }
body.green .action-btn:hover { background: #edf0ed; color: #2c332e; }
body.green .action-btn.active { background: #526e5a; color: #ffffff; border-color: #526e5a; }
body.green .msg-avatar { background: #526e5a; }
body.green .msg-bubble { background: #edf0ed; border-color: #dee2de; color: #2c332e; }
body.green .msg-student .msg-bubble { background: #526e5a; color: #ffffff; border-color: #526e5a; }
body.green .input-bar { border-top-color: #dee2de; }
body.green .input-wrapper { border-color: #dee2de; background: #f7f8f7; }
body.green .input-wrapper:focus-within { border-color: #526e5a; }
body.green .input-wrapper input { color: #2c332e; }
body.green .input-wrapper input::placeholder { color: #8fa091; }
body.green .send-btn { background: #526e5a; }
body.green .send-btn:hover { background: #3d5243; }
body.green .switch-btn { background: #edf0ed; color: #526e5a; border-color: #dbe1db; }
body.green .switch-btn:hover { background: #dbe1db; }
body.green .answer-scroll { background: #f7f8f7; }
body.green .question-textarea { border-color: #dee2de; color: #2c332e; background: #f7f8f7; }
body.green .question-textarea:focus { border-color: #526e5a; }
body.green .question-textarea::placeholder { color: #8fa091; }
body.green .picker-btn { border-color: #dee2de; background: #f7f8f7; color: #556056; }
body.green .picker-btn:hover { background: #edf0ed; border-color: #526e5a; color: #2c332e; }
body.green .sub-tabs { border-bottom-color: #dee2de; }
body.green .sub-tab { color: #8fa091; }
body.green .sub-tab:hover { color: #2c332e; }
body.green .sub-tab.active { color: #526e5a; }
body.green .sub-tab.active svg { color: #d97706; }
body.green .sub-tab-badge { background: #526e5a; }
body.green .form-label { color: #8fa091; }
body.green .mode-card { border-color: #dee2de; background: #f7f8f7; }
body.green .mode-card:hover { border-color: #aaa; }
body.green .mode-card.active { border-color: #526e5a; background: #edf0ed; }
body.green .mode-card-left svg { color: #556056; }
body.green .mode-card.active .mode-card-left svg { color: #526e5a; }
body.green .mode-card-title { color: #556056; }
body.green .mode-card.active .mode-card-title { color: #2c332e; }
body.green .mode-card > svg { color: #526e5a; }
body.green .input-box { border-color: #dee2de; background: #f7f8f7; }
body.green .input-box:focus-within { border-color: #526e5a; }
body.green .input-box input { color: #2c332e; }
body.green .input-box input::placeholder { color: #8fa091; }
body.green .num-btn { border-color: #dee2de; background: #f7f8f7; color: #556056; }
body.green .num-btn:hover { background: #edf0ed; border-color: #526e5a; }
body.green .num-display { border-color: #dee2de; color: #2c332e; background: #edf0ed; }
body.green .generate-btn { background: #526e5a; }
body.green .generate-btn:hover { background: #3d5243; }
body.green .error-msg { color: #dc2626; }
body.green .bank-empty { color: #8fa091; }
body.green .bank-empty svg { color: #8fa091; }
body.green .bank-header { color: #8fa091; }
body.green .clear-btn { border-color: #dee2de; color: #556056; }
body.green .clear-btn:hover { background: #edf0ed; border-color: #526e5a; }
body.green .batch-group { border-color: #dee2de; }
body.green .batch-header:hover { background: #edf0ed; }
body.green .batch-arrow { color: #8fa091; }
body.green .batch-label { color: #2c332e; }
body.green .batch-meta { color: #8fa091; }
body.green .batch-del { color: #8fa091; }
body.green .batch-del:hover { background: rgba(220, 38, 38, 0.08); color: #dc2626; }
body.green .batch-questions { border-top-color: #dee2de; background: #f3f6f3; }
body.green .question-item:hover { background: #edf0ed; }
body.green .question-item .q-type { background: #edf0ed; color: #526e5a; }
body.green .question-item .q-content { color: #2c332e; }
body.green .question-item .q-points { color: #8fa091; }
body.green .answer-section { border-top-color: #dee2de; }
body.green .answer-box { border-color: #dee2de; background: #f7f8f7; }
body.green .answer-box:focus-within { border-color: #526e5a; }
body.green .answer-input { color: #2c332e; }
body.green .answer-input::placeholder { color: #8fa091; }
body.green .submit-btn { background: #edf0ed; color: #526e5a; border-color: #dbe1db; }
body.green .submit-btn:hover { background: #dbe1db; }
body.green .progress-footer { background: #edf0ed; border-top-color: #dee2de; }
body.green .progress-info { color: #2c332e; }
body.green .progress-info svg { color: #526e5a; }
body.green .progress-bar { background: #dee2de; }
body.green .progress-fill { background: #526e5a; }
body.green .progress-count { color: #8fa091; }
body.green .picker-dialog { background: #f7f8f7; }
body.green .picker-header { border-bottom-color: #dee2de; color: #2c332e; }
body.green .picker-close { color: #8fa091; }
body.green .picker-close:hover { background: #edf0ed; color: #2c332e; }
body.green .picker-breadcrumb { color: #8fa091; }
body.green .picker-breadcrumb span:hover { color: #2c332e; }
body.green .picker-breadcrumb span.active { color: #2c332e; }
body.green .picker-loading { color: #8fa091; }
body.green .picker-empty { color: #8fa091; }
body.green .picker-item { background: #f7f8f7; border-color: #dee2de; }
body.green .picker-item:hover { border-color: #526e5a; background: #edf0ed; }
body.green .picker-item-title { color: #2c332e; }
body.green .picker-item-desc { color: #8fa091; }
body.green .picker-q-type { background: #edf0ed; color: #526e5a; }
body.green .picker-item-opts { color: #556056; }
body.green .picker-answered { color: #16a34a; background: rgba(22, 163, 74, 0.08); }

/* ===== 暗色主题 ===== */
body.dark .tutor-page { background: #121212; }
body.dark .diagnosis-panel { border-right-color: #2d2d2d; }
body.dark .diagnosis-section { border-bottom-color: #2d2d2d; }
body.dark .section-title { color: #e5e5e5; }
body.dark .section-title svg { color: #999; }
body.dark .count-badge { background: #242424; color: #999; }
body.dark .empty-state { color: #777; }
body.dark .knowledge-card { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .k-icon { background: #242424; }
body.dark .k-title { color: #e5e5e5; }
body.dark .k-formula { color: #aaa; }
body.dark .k-mastery.good { color: #4ade80; }
body.dark .k-mastery.medium { color: #fbbf24; }
body.dark .k-mastery.low { color: #f87171; }
body.dark .k-mastery.pending { color: #777; }
body.dark .error-card { background: rgba(248, 113, 113, 0.06); border-left-color: #f87171; }
body.dark .error-tag { background: rgba(248, 113, 113, 0.15); color: #f87171; }
body.dark .error-content strong { color: #e5e5e5; }
body.dark .error-content p { color: #aaa; }
body.dark .strategy-card { background: #1a1a1a; color: #e5e5e5; }
body.dark .strategy-dot { background: #fff; }
body.dark .tutor-header { border-bottom-color: #2d2d2d; background: #121212; }
body.dark .tutor-icon { background: #242424; color: #fff; }
body.dark .tutor-label { color: #e5e5e5; }
body.dark .action-btn { border-color: #2d2d2d; background: #1a1a1a; color: #999; }
body.dark .action-btn:hover { background: #242424; color: #e5e5e5; }
body.dark .action-btn.active { background: #fff; color: #121212; border-color: #fff; }
body.dark .msg-avatar { background: #fff; color: #121212; }
body.dark .msg-bubble { background: #1a1a1a; border-color: #2d2d2d; color: #e5e5e5; }
body.dark .msg-student .msg-bubble { background: #fff; color: #121212; border-color: #fff; }
body.dark .input-bar { border-top-color: #2d2d2d; }
body.dark .input-wrapper { border-color: #333; background: #1a1a1a; }
body.dark .input-wrapper:focus-within { border-color: #fff; }
body.dark .input-wrapper input { color: #e5e5e5; }
body.dark .input-wrapper input::placeholder { color: #777; }
body.dark .send-btn { background: #fff; color: #121212; }
body.dark .send-btn:hover { background: #e5e5e5; }
body.dark .switch-btn { background: #242424; color: #fbbf24; border-color: #333; }
body.dark .switch-btn:hover { background: #333; }
body.dark .answer-scroll { background: #121212; }
body.dark .question-textarea { border-color: #333; color: #e5e5e5; background: #1a1a1a; }
body.dark .question-textarea:focus { border-color: #fff; }
body.dark .question-textarea::placeholder { color: #777; }
body.dark .picker-btn { border-color: #333; background: #1a1a1a; color: #999; }
body.dark .picker-btn:hover { background: #242424; border-color: #fff; color: #e5e5e5; }
body.dark .sub-tabs { border-bottom-color: #2d2d2d; }
body.dark .sub-tab { color: #777; }
body.dark .sub-tab:hover { color: #e5e5e5; }
body.dark .sub-tab.active { color: #fff; }
body.dark .sub-tab.active svg { color: #fbbf24; }
body.dark .sub-tab-badge { background: #fff; color: #121212; }
body.dark .form-label { color: #777; }
body.dark .mode-card { border-color: #2d2d2d; background: #1a1a1a; }
body.dark .mode-card:hover { border-color: #555; }
body.dark .mode-card.active { border-color: #fff; background: #242424; }
body.dark .mode-card-left svg { color: #999; }
body.dark .mode-card.active .mode-card-left svg { color: #fff; }
body.dark .mode-card-title { color: #999; }
body.dark .mode-card.active .mode-card-title { color: #e5e5e5; }
body.dark .mode-card > svg { color: #fff; }
body.dark .input-box { border-color: #333; background: #1a1a1a; }
body.dark .input-box:focus-within { border-color: #fff; }
body.dark .input-box input { color: #e5e5e5; }
body.dark .input-box input::placeholder { color: #777; }
body.dark .num-btn { border-color: #333; background: #1a1a1a; color: #999; }
body.dark .num-btn:hover { background: #242424; border-color: #fff; }
body.dark .num-display { border-color: #333; color: #e5e5e5; background: #242424; }
body.dark .generate-btn { background: #fff; color: #121212; }
body.dark .generate-btn:hover { background: #e5e5e5; }
body.dark .error-msg { color: #f87171; }
body.dark .bank-empty { color: #777; }
body.dark .bank-empty svg { color: #555; }
body.dark .bank-header { color: #777; }
body.dark .clear-btn { border-color: #333; color: #999; }
body.dark .clear-btn:hover { background: #242424; border-color: #fff; }
body.dark .batch-group { border-color: #2d2d2d; }
body.dark .batch-header:hover { background: #1a1a1a; }
body.dark .batch-arrow { color: #777; }
body.dark .batch-label { color: #e5e5e5; }
body.dark .batch-meta { color: #777; }
body.dark .batch-del { color: #777; }
body.dark .batch-del:hover { background: rgba(248, 113, 113, 0.1); color: #f87171; }
body.dark .batch-questions { border-top-color: #2d2d2d; background: #0f0f0f; }
body.dark .question-item:hover { background: #242424; }
body.dark .question-item .q-type { background: #242424; color: #999; }
body.dark .question-item .q-content { color: #e5e5e5; }
body.dark .question-item .q-points { color: #777; }
body.dark .answer-section { border-top-color: #2d2d2d; }
body.dark .answer-box { border-color: #333; background: #1a1a1a; }
body.dark .answer-box:focus-within { border-color: #fff; }
body.dark .answer-input { color: #e5e5e5; }
body.dark .answer-input::placeholder { color: #777; }
body.dark .submit-btn { background: #242424; color: #fbbf24; border-color: #333; }
body.dark .submit-btn:hover { background: #333; }
body.dark .progress-footer { background: #1a1a1a; border-top-color: #2d2d2d; }
body.dark .progress-info { color: #e5e5e5; }
body.dark .progress-info svg { color: #fff; }
body.dark .progress-bar { background: #333; }
body.dark .progress-fill { background: #fff; }
body.dark .progress-count { color: #777; }
body.dark .picker-dialog { background: #1e1e1e; }
body.dark .picker-header { border-bottom-color: #2d2d2d; color: #e5e5e5; }
body.dark .picker-close { color: #777; }
body.dark .picker-close:hover { background: #242424; color: #e5e5e5; }
body.dark .picker-breadcrumb { color: #777; }
body.dark .picker-breadcrumb span:hover { color: #e5e5e5; }
body.dark .picker-breadcrumb span.active { color: #e5e5e5; }
body.dark .picker-loading { color: #777; }
body.dark .picker-empty { color: #777; }
body.dark .picker-item { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .picker-item:hover { border-color: #fff; background: #242424; }
body.dark .picker-item-title { color: #e5e5e5; }
body.dark .picker-item-desc { color: #777; }
body.dark .picker-q-type { background: #242424; color: #999; }
body.dark .picker-item-opts { color: #aaa; }
body.dark .picker-answered { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
</style>
