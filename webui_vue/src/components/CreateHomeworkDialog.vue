<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog-card">
      <!-- 头部 -->
      <div class="dialog-header">
        <div class="dialog-header-left">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
          <h3>布置作业</h3>
        </div>
        <button class="btn-close" @click="$emit('close')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
          </svg>
        </button>
      </div>

      <!-- 内容区：左右双栏 -->
      <div class="dialog-body">
        <!-- 左侧：作业属性配置 -->
        <div class="dialog-left">
          <div class="form-group">
            <label>作业标题</label>
            <input v-model="form.title" placeholder="如：光合作用与产量形成" />
          </div>

          <div class="form-group">
            <label>作业说明</label>
            <textarea v-model="form.description" placeholder="可选，在此输入本次作业的核验要求或实验指标描述..."></textarea>
          </div>

          <div class="form-group">
            <label>截止时间</label>
            <input v-model="form.deadline" type="datetime-local" />
          </div>
        </div>

        <!-- 右侧：题目选择（动态扩展） -->
        <div class="dialog-right">
          <!-- 状态 A：初始就绪状态 -->
          <div v-if="!showBank" class="right-initial">
            <div class="questions-header">
              <span class="questions-title">题目选择</span>
              <span class="questions-count">已选 {{ form.questions.length }} 题 · 共 {{ totalPoints }} 分</span>
            </div>

            <!-- 已选题目列表 -->
            <div v-if="form.questions.length > 0" class="selected-list">
              <div v-for="(q, qi) in form.questions" :key="qi" class="question-item">
                <div class="q-header">
                  <div class="q-header-left">
                    <span class="q-num">{{ qi + 1 }}</span>
                    <span class="q-type-badge">{{ getTypeLabel(q.type) }}</span>
                    <span class="q-points">{{ q.points }}分</span>
                  </div>
                  <button class="q-remove" @click="form.questions.splice(qi, 1)" title="移除">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 6 6 18"/>
                      <path d="m6 6 12 12"/>
                    </svg>
                  </button>
                </div>
                <div class="q-content">{{ q.content }}</div>
              </div>
            </div>

            <!-- 空状态引导 -->
            <div v-else class="empty-questions" @click="showBank = true">
              <div class="empty-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <ellipse cx="12" cy="5" rx="9" ry="3"/>
                  <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
                  <path d="M3 12a9 3 0 0 0 18 0"/>
                </svg>
              </div>
              <p>请从题库选择题目</p>
              <button class="btn-from-bank">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
                <span>从题库选题</span>
              </button>
            </div>

            <!-- 继续选题按钮 -->
            <button v-if="form.questions.length > 0" class="btn-add-more" @click="showBank = true">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="M12 5v14"/>
              </svg>
              <span>继续选题</span>
            </button>
          </div>

          <!-- 状态 B：题库选择面板（原地扩展） -->
          <div v-else class="right-bank">
            <div class="bank-header">
              <div class="bank-header-left">
                <span class="bank-title">课程题库</span>
                <span class="bank-count">{{ questions.length }} 题就绪</span>
              </div>
              <div class="bank-header-right">
                <button class="btn-bank-collapse" @click="showBank = false">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m7 20 5-5 5 5"/>
                    <path d="m7 4 5 5 5-5"/>
                  </svg>
                  <span>收起题库</span>
                </button>
              </div>
            </div>

            <!-- 题库内容：左侧筛选 + 右侧列表 -->
            <div class="bank-body">
              <!-- 左侧题型筛选 -->
              <div class="bank-sidebar">
                <div class="bank-sidebar-item" :class="{ active: !bankFilter }" @click="bankFilter = ''">
                  全部题型 ({{ questions.length }})
                </div>
                <div v-for="type in questionTypes" :key="type.value" class="bank-sidebar-item" :class="{ active: bankFilter === type.value }" @click="bankFilter = type.value">
                  {{ type.label }} ({{ getTypeCount(type.value) }})
                </div>
              </div>

              <!-- 右侧题目列表 -->
              <div class="bank-list">
                <div v-if="bankLoading" class="bank-loading">加载中...</div>
                <div v-else-if="filteredBankQuestions.length === 0" class="bank-empty">暂无题目</div>
                <div v-else class="bank-items">
                  <div v-for="(q, qi) in filteredBankQuestions" :key="q.id" class="bank-item" :class="{ selected: selectedBankIds.has(q.id) }" @click="toggleBankSelect(q)">
                    <div class="bank-item-content">
                      <div class="bank-item-title">{{ qi + 1 }}. {{ q.content }}</div>
                      <div class="bank-item-meta">题型: {{ getTypeLabel(q.questionType) }} | 分值: {{ q.points }}分</div>
                    </div>
                    <input type="checkbox" :checked="selectedBankIds.has(q.id)" @click.stop="toggleBankSelect(q)" />
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部确认 -->
            <div class="bank-footer">
              <button class="btn-confirm-select" @click="confirmBankSelect" :disabled="selectedBankQuestions.length === 0">
                确认选择并同步 ({{ selectedBankQuestions.length }})
              </button>
            </div>
          </div>
        </div>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>

      <!-- 底部操作栏 -->
      <div class="dialog-footer">
        <div class="dialog-actions">
          <button class="btn-secondary" @click="$emit('close')">取消</button>
          <button class="btn-primary" @click="handleCreate" :disabled="creating">
            {{ creating ? '保存中...' : '保存草稿' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../composables/useCourse.js'
import { useGateway } from '../composables/useGateway.js'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['close', 'created'])
const route = useRoute()
const { createHomework, fetchQuestionBank } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

const courseId = route.params.courseId
const creating = ref(false)
const error = ref('')
const showBank = ref(false)
const bankLoading = ref(false)
const questions = ref([])
const bankFilter = ref('')
const selectedBankQuestions = ref([])

const questionTypes = [
  { value: 'choice', label: '选择题' },
  { value: 'true_false', label: '判断题' },
  { value: 'fill', label: '填空题' },
  { value: 'short_answer', label: '简答题' },
  { value: 'essay', label: '论述题' },
]

const form = reactive({
  title: '',
  description: '',
  deadline: '',
  questions: [],
})

const totalPoints = computed(() => form.questions.reduce((s, q) => s + (q.points || 0), 0))

const selectedBankIds = computed(() => new Set(selectedBankQuestions.value.map(q => q.id)))

const filteredBankQuestions = computed(() => {
  let list = questions.value
  if (bankFilter.value) list = list.filter(q => q.questionType === bankFilter.value)
  return list
})

function getTypeLabel(type) {
  const labels = {
    choice: '选择题',
    true_false: '判断题',
    fill: '填空题',
    short_answer: '简答题',
    essay: '论述题',
  }
  return labels[type] || type
}

function getTypeCount(type) {
  return questions.value.filter(q => q.questionType === type).length
}

async function loadBankQuestions() {
  bankLoading.value = true
  try {
    // Ensure gateway is connected
    if (!connected.value && props.user) {
      await connectGateway({ role: props.user.role || 'teacher', userId: props.user.userId })
    }
    questions.value = await fetchQuestionBank(courseId)
    console.log('Loaded questions:', questions.value.length)
  } catch (e) {
    console.error('Failed to load question bank:', e)
  } finally {
    bankLoading.value = false
  }
}

function toggleBankSelect(q) {
  const idx = selectedBankQuestions.value.findIndex(item => item.id === q.id)
  if (idx >= 0) {
    selectedBankQuestions.value.splice(idx, 1)
  } else {
    selectedBankQuestions.value.push(q)
  }
}

function confirmBankSelect() {
  const TYPE_ORDER = { choice: 0, true_false: 1, fill: 2, short_answer: 3, essay: 4 }
  const newQuestions = selectedBankQuestions.value.map(q => ({
    type: q.questionType,
    content: q.content,
    points: q.points,
    answer: q.answer || '',
    options: q.options || [],
    explanation: q.explanation || '',
  }))
  form.questions.push(...newQuestions)
  form.questions.sort((a, b) => (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9))
  selectedBankQuestions.value = []
  showBank.value = false
}

watch(showBank, (val) => {
  if (val && questions.value.length === 0) {
    loadBankQuestions()
  }
})

async function handleCreate() {
  if (!props.user) { error.value = '未登录'; return }
  if (!form.title.trim()) { error.value = '请输入作业标题'; return }

  creating.value = true
  error.value = ''
  try {
    const questionsData = form.questions.map((q, i) => ({
      id: `q${i + 1}`,
      type: q.type,
      content: q.content,
      points: q.points || 10,
      answer: q.answer || '',
      options: q.options || [],
      explanation: q.explanation || '',
    }))

    await createHomework(courseId, {
      title: form.title.trim(),
      description: form.description.trim(),
      deadline: form.deadline ? new Date(form.deadline).toISOString() : '',
      status: 'draft',
      questions: questionsData,
      totalPoints: totalPoints.value,
    })

    emit('created')
  } catch (e) {
    error.value = e.message
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 24px;
}

.dialog-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  width: 100%;
  max-width: 960px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

/* 头部 */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.dialog-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
}

.dialog-header-left h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
}

.btn-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: var(--text-primary);
  background: var(--accent-soft);
}

/* 内容区：左右双栏 */
.dialog-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: var(--accent-soft);
}

/* 左侧：作业属性配置 */
.dialog-left {
  width: 35%;
  padding: 24px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-light);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--accent-soft);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  font-size: 0.8rem;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  color: var(--text-primary);
  transition: all 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--accent);
  background: var(--bg-card);
}

.form-group textarea {
  resize: none;
  min-height: 100px;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--text-muted);
}

/* 右侧：题目选择 */
.dialog-right {
  width: 65%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 右侧初始状态 */
.right-initial {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.questions-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.questions-count {
  font-size: 0.75rem;
  color: var(--text-primary);
  font-family: monospace;
  font-weight: 600;
}

/* 已选题目列表 */
.selected-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
  margin-bottom: 12px;
}

.question-item {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 12px;
  transition: all 0.2s;
}

.question-item:hover {
  border-color: var(--accent);
}

.q-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.q-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.q-num {
  font-weight: 700;
  color: var(--accent);
  font-size: 0.8rem;
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-soft);
  border-radius: 6px;
}

.q-type-badge {
  font-size: 0.6rem;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.q-points {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: monospace;
}

.q-remove {
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.q-remove:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.q-content {
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--text-primary);
}

/* 空状态 */
.empty-questions {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
  background: var(--bg-card);
  border: 2px dashed var(--border-medium);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.empty-questions:hover {
  border-color: var(--accent);
}

.empty-icon {
  width: 48px;
  height: 48px;
  background: var(--accent-soft);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: var(--text-primary);
  transition: all 0.2s;
}

.empty-questions:hover .empty-icon {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

.empty-questions p {
  color: var(--text-muted);
  margin-bottom: 16px;
  font-size: 0.8rem;
}

.btn-from-bank {
  padding: 8px 16px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--accent);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-from-bank:hover {
  background: var(--accent);
  color: #ffffff;
}

.btn-add-more {
  width: 100%;
  padding: 10px;
  background: none;
  border: 1px dashed var(--border-medium);
  border-radius: 10px;
  color: var(--text-muted);
  font-size: 0.75rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-add-more:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}

/* 右侧题库面板 */
.right-bank {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.bank-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.bank-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bank-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.bank-count {
  font-size: 0.65rem;
  padding: 2px 8px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 4px;
  font-family: monospace;
}

.bank-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-bank-collapse {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.7rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-bank-collapse:hover {
  color: var(--text-primary);
  background: var(--accent-soft);
}

/* 题库内容 */
.bank-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧题型筛选 */
.bank-sidebar {
  width: 120px;
  border-right: 1px solid var(--border-light);
  padding: 12px 8px;
  overflow-y: auto;
  flex-shrink: 0;
}

.bank-sidebar-item {
  padding: 6px 10px;
  font-size: 0.7rem;
  color: var(--text-muted);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.bank-sidebar-item:hover {
  background: var(--accent-soft);
  color: var(--text-primary);
}

.bank-sidebar-item.active {
  background: var(--text-primary);
  color: var(--bg-card);
  font-weight: 600;
}

/* 右侧题目列表 */
.bank-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.bank-loading,
.bank-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.bank-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bank-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.bank-item:hover {
  border-color: var(--accent);
}

.bank-item.selected {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.bank-item-content {
  flex: 1;
  min-width: 0;
}

.bank-item-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.bank-item-meta {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: monospace;
}

.bank-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
  flex-shrink: 0;
  margin-top: 2px;
}

/* 题库底部 */
.bank-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.btn-confirm-select {
  padding: 8px 20px;
  background: var(--accent);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-confirm-select:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-confirm-select:not(:disabled):hover {
  background: var(--accent-deep);
}

/* 底部操作栏 */
.dialog-footer {
  padding: 14px 24px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.error-text {
  color: var(--danger);
  font-size: 0.75rem;
  margin-right: auto;
}

.dialog-actions {
  display: flex;
  gap: 8px;
}

.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary:not(:disabled):hover {
  background: var(--accent-deep);
}

.btn-secondary {
  padding: 8px 20px;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--accent-soft);
  color: var(--text-primary);
}

/* 暗色模式 */
body.dark .dialog-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .dialog-header {
  border-color: #2d2d2d;
}

body.dark .dialog-header-left {
  color: #e5e5e5;
}

body.dark .dialog-header-left h3 {
  color: #e5e5e5;
}

body.dark .btn-close {
  color: #666666;
}

body.dark .btn-close:hover {
  color: #e5e5e5;
  background: rgba(255, 255, 255, 0.08);
}

body.dark .dialog-body {
  background: #121212;
}

body.dark .dialog-left {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .form-group label {
  color: #666666;
}

body.dark .form-group input,
body.dark .form-group textarea {
  background: #242424;
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .form-group input:focus,
body.dark .form-group textarea:focus {
  border-color: #ffffff;
  background: #2d2d2d;
}

body.dark .form-group input::placeholder,
body.dark .form-group textarea::placeholder {
  color: #666666;
}

body.dark .questions-title {
  color: #666666;
}

body.dark .questions-count {
  color: #e5e5e5;
}

body.dark .empty-questions {
  background: #242424;
  border-color: #3a3a3a;
}

body.dark .empty-questions:hover {
  border-color: #ffffff;
}

body.dark .empty-icon {
  background: rgba(255, 255, 255, 0.08);
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .empty-questions:hover .empty-icon {
  background: #ffffff;
  color: #121212;
  border-color: #ffffff;
}

body.dark .empty-questions p {
  color: #666666;
}

body.dark .btn-from-bank {
  background: #242424;
  color: #e5e5e5;
  border-color: #ffffff;
}

body.dark .btn-from-bank:hover {
  background: #ffffff;
  color: #121212;
}

body.dark .question-item {
  background: #242424;
  border-color: #3a3a3a;
}

body.dark .question-item:hover {
  border-color: #ffffff;
}

body.dark .q-num {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

body.dark .q-type-badge {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

body.dark .q-remove:hover {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.3);
  color: #f87171;
}

body.dark .btn-add-more {
  border-color: #3a3a3a;
  color: #666666;
}

body.dark .btn-add-more:hover {
  border-color: #ffffff;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

/* 题库面板暗色模式 */
body.dark .right-bank {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .bank-header {
  border-color: #2d2d2d;
}

body.dark .bank-title {
  color: #e5e5e5;
}

body.dark .bank-count {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

body.dark .btn-bank-collapse {
  color: #666666;
}

body.dark .btn-bank-collapse:hover {
  color: #e5e5e5;
  background: rgba(255, 255, 255, 0.08);
}

body.dark .bank-sidebar {
  border-color: #2d2d2d;
}

body.dark .bank-sidebar-item {
  color: #666666;
}

body.dark .bank-sidebar-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e5e5e5;
}

body.dark .bank-sidebar-item.active {
  background: #ffffff;
  color: #121212;
}

body.dark .bank-item {
  background: #242424;
  border-color: #3a3a3a;
}

body.dark .bank-item:hover {
  border-color: #ffffff;
}

body.dark .bank-item.selected {
  border-color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

body.dark .bank-item-title {
  color: #e5e5e5;
}

body.dark .bank-item-meta {
  color: #666666;
}

body.dark .bank-footer {
  border-color: #2d2d2d;
}

body.dark .btn-confirm-select {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-confirm-select:hover {
  background: #e5e5e5;
}

body.dark .dialog-footer {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .btn-primary {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-primary:hover {
  background: #e5e5e5;
}

body.dark .btn-secondary {
  background: #2d2d2d;
  border-color: #3a3a3a;
  color: #999999;
}

body.dark .btn-secondary:hover {
  background: #3a3a3a;
  color: #e5e5e5;
}
</style>
