<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog-card dialog-card-wide">
      <div class="dialog-header">
        <h3>📚 课程题库</h3>
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>

      <!-- Add Question Form -->
      <div v-if="showAddForm" class="add-form">
        <h4>添加题目到题库</h4>
        <div class="form-row">
          <select v-model="newQuestion.type" class="q-type-select">
            <option value="choice">选择题</option>
            <option value="true_false">判断题</option>
            <option value="fill">填空题</option>
            <option value="short_answer">简答题</option>
            <option value="essay">论述题</option>
          </select>
          <input v-model.number="newQuestion.points" type="number" min="1" class="points-input" placeholder="分值" />
        </div>
        <textarea v-model="newQuestion.content" rows="3" placeholder="题目内容" class="q-content-input"></textarea>

        <!-- Choice options -->
        <div v-if="newQuestion.type === 'choice'" class="options-section">
          <div v-for="(opt, oi) in newQuestion.options" :key="oi" class="option-row">
            <span>{{ String.fromCharCode(65 + oi) }}.</span>
            <input v-model="newQuestion.options[oi]" placeholder="选项内容" />
            <button @click="newQuestion.options.splice(oi, 1)">✕</button>
          </div>
          <button class="btn-add-opt" @click="newQuestion.options.push('')">+ 添加选项</button>
          <div class="answer-row">
            <label>正确答案：</label>
            <select v-model="newQuestion.answer">
              <option v-for="(opt, oi) in newQuestion.options" :key="oi" :value="String.fromCharCode(65 + oi)">
                {{ String.fromCharCode(65 + oi) }}
              </option>
            </select>
          </div>
        </div>

        <!-- True/False answer -->
        <div v-if="newQuestion.type === 'true_false'" class="answer-row">
          <label>正确答案：</label>
          <select v-model="newQuestion.answer">
            <option value="true">正确</option>
            <option value="false">错误</option>
          </select>
        </div>

        <!-- Fill/Short answer -->
        <div v-if="['fill', 'short_answer', 'essay'].includes(newQuestion.type)" class="answer-row">
          <label>参考答案：</label>
          <textarea v-model="newQuestion.answer" rows="2" placeholder="参考答案"></textarea>
        </div>

        <textarea v-model="newQuestion.explanation" rows="2" placeholder="解析（可选）" class="explanation-input"></textarea>

        <div class="form-actions">
          <button class="btn-secondary" @click="showAddForm = false">取消</button>
          <button class="btn-primary" @click="handleAddQuestion" :disabled="!newQuestion.content.trim()">
            添加到题库
          </button>
        </div>
      </div>

      <!-- Filter -->
      <div class="filter-row">
        <select v-model="filterType" class="filter-select">
          <option value="">全部题型</option>
          <option value="choice">选择题</option>
          <option value="true_false">判断题</option>
          <option value="fill">填空题</option>
          <option value="short_answer">简答题</option>
          <option value="essay">论述题</option>
        </select>
        <span class="question-count">{{ filteredQuestions.length }} 道题</span>
        <div class="filter-actions">
          <button class="btn-add" @click="showAddForm = true">+ 手动添加</button>
          <button class="btn-ai" @click="showAIForm = true">🤖 AI 生成</button>
        </div>
      </div>

      <!-- AI Generate Form -->
      <div v-if="showAIForm" class="ai-form">
        <h4>🤖 AI 智能出题</h4>
        <div class="form-group">
          <label>知识内容</label>
          <textarea v-model="aiForm.content" rows="4" placeholder="粘贴教材、笔记或知识点..."></textarea>
        </div>
        <div class="ai-config-row">
          <div class="form-group compact">
            <label>题目数量</label>
            <input v-model.number="aiForm.numQuestions" type="number" min="1" max="50" />
          </div>
          <div class="form-group compact">
            <label>选择题</label>
            <input v-model.number="aiForm.typeDistribution.choice" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group compact">
            <label>判断题</label>
            <input v-model.number="aiForm.typeDistribution.true_false" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group compact">
            <label>填空题</label>
            <input v-model.number="aiForm.typeDistribution.fill" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group compact">
            <label>简答题</label>
            <input v-model.number="aiForm.typeDistribution.short_answer" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group compact">
            <label>论述题</label>
            <input v-model.number="aiForm.typeDistribution.essay" type="number" min="0" placeholder="0" />
          </div>
        </div>
        <p class="ai-hint">题型分布可选，不填则由 AI 自动分配</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showAIForm = false">取消</button>
          <button class="btn-primary" @click="handleAIGenerate" :disabled="aiGenerating || !aiForm.content.trim()">
            {{ aiGenerating ? '🔄 生成中...' : '✨ 生成题目' }}
          </button>
        </div>
        <p v-if="aiError" class="error-text">{{ aiError }}</p>
      </div>

      <!-- AI Preview -->
      <div v-if="previewQuestions.length > 0" class="preview-section">
        <div class="preview-header">
          <h4>✨ AI 生成预览（{{ previewQuestions.length }} 道题）</h4>
          <div class="preview-actions">
            <button class="btn-secondary" @click="previewQuestions = []">✕ 丢弃</button>
            <button class="btn-primary" @click="handleSavePreview" :disabled="previewSaving">
              {{ previewSaving ? '保存中...' : '💾 保存到题库' }}
            </button>
          </div>
        </div>
        <div class="question-list preview-list">
          <div v-for="(q, qi) in previewQuestions" :key="qi" class="question-item preview-item">
            <div class="q-header">
              <span class="q-num">{{ qi + 1 }}</span>
              <span class="q-type-badge">{{ getTypeLabel(q.type) }}</span>
              <span class="q-points">{{ q.points }}分</span>
              <button class="btn-delete-q" @click="previewQuestions.splice(qi, 1)" title="移除">🗑</button>
            </div>
            <div class="q-content">{{ q.content }}</div>
            <div v-if="q.type === 'choice' && q.options" class="q-options">
              <div v-for="opt in q.options" :key="opt.key" class="q-option">
                <span class="opt-key" :class="{ correct: opt.key === q.answer }">{{ opt.key }}.</span>
                <span class="opt-text">{{ opt.text }}</span>
              </div>
            </div>
            <div v-if="q.answer" class="q-answer">
              <span class="label">答案：</span>{{ q.answer }}
            </div>
            <div v-if="q.explanation" class="q-explanation">
              <span class="label">解析：</span>{{ q.explanation }}
            </div>
          </div>
        </div>
      </div>

      <!-- Question List -->
      <div class="question-list" v-show="previewQuestions.length === 0">
        <div v-if="loading" class="loading-hint">加载中...</div>
        <div v-else-if="filteredQuestions.length === 0" class="empty-hint">题库为空</div>
        <div v-for="(q, qi) in filteredQuestions" :key="q.id" class="question-item"
             :class="{ selected: selectedIds.has(q.id), editing: editingQuestion && editingQuestion.id === q.id }"
             @click="mode === 'select' ? toggleSelect(q) : null">

          <!-- View Mode -->
          <template v-if="!(editingQuestion && editingQuestion.id === q.id)">
            <div class="q-header">
              <span v-if="mode === 'select'" class="q-checkbox">
                <input type="checkbox" :checked="selectedIds.has(q.id)" @click.stop="toggleSelect(q)" />
              </span>
              <span class="q-num">{{ qi + 1 }}</span>
              <span class="q-type-badge">{{ getTypeLabel(q.questionType) }}</span>
              <span class="q-points">{{ q.points }}分</span>
              <span class="q-source">{{ q.source === 'ai' ? '🤖 AI' : '✏️ 手动' }}</span>
              <button class="btn-edit-q" @click.stop="handleEdit(q)" title="编辑">✏️</button>
              <button class="btn-delete-q" @click.stop="handleDelete(q)" title="删除">🗑</button>
            </div>
            <div class="q-content">{{ q.content }}</div>
            <div v-if="q.answer" class="q-answer">
              <span class="label">答案：</span>{{ q.answer }}
            </div>
            <div v-if="q.explanation" class="q-explanation">
              <span class="label">解析：</span>{{ q.explanation }}
            </div>
          </template>

          <!-- Inline Edit Mode -->
          <template v-else>
            <div class="inline-edit-form">
              <div class="form-row">
                <select v-model="editingQuestion.questionType" class="q-type-select">
                  <option value="choice">选择题</option>
                  <option value="true_false">判断题</option>
                  <option value="fill">填空题</option>
                  <option value="short_answer">简答题</option>
                  <option value="essay">论述题</option>
                </select>
                <input v-model.number="editingQuestion.points" type="number" min="1" class="points-input" placeholder="分值" />
              </div>
              <textarea v-model="editingQuestion.content" rows="3" placeholder="题目内容" class="q-content-input"></textarea>

              <!-- Choice options -->
              <div v-if="editingQuestion.questionType === 'choice'" class="options-section">
                <div v-for="(opt, oi) in editingQuestion.options" :key="oi" class="option-row">
                  <span>{{ String.fromCharCode(65 + oi) }}.</span>
                  <input v-model="editingQuestion.options[oi].text" placeholder="选项内容" />
                  <button @click="editingQuestion.options.splice(oi, 1)">✕</button>
                </div>
                <button class="btn-add-opt" @click="editingQuestion.options.push({key: String.fromCharCode(65 + editingQuestion.options.length), text: ''})">+ 添加选项</button>
                <div class="answer-row">
                  <label>正确答案：</label>
                  <select v-model="editingQuestion.answer">
                    <option v-for="(opt, oi) in editingQuestion.options" :key="oi" :value="opt.key">
                      {{ opt.key }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- True/False answer -->
              <div v-if="editingQuestion.questionType === 'true_false'" class="answer-row">
                <label>正确答案：</label>
                <select v-model="editingQuestion.answer">
                  <option value="true">正确</option>
                  <option value="false">错误</option>
                </select>
              </div>

              <!-- Fill/Short answer -->
              <div v-if="['fill', 'short_answer', 'essay'].includes(editingQuestion.questionType)" class="answer-row">
                <label>参考答案：</label>
                <textarea v-model="editingQuestion.answer" rows="2" placeholder="参考答案"></textarea>
              </div>

              <textarea v-model="editingQuestion.explanation" rows="2" placeholder="解析（可选）" class="explanation-input"></textarea>

              <div class="form-actions">
                <button class="btn-secondary" @click="editingQuestion = null">取消</button>
                <button class="btn-primary" @click="handleSaveEdit" :disabled="!editingQuestion.content.trim()">
                  保存修改
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Actions -->
      <div class="dialog-actions">
        <button class="btn-secondary" @click="$emit('close')">关闭</button>
        <button v-if="mode === 'select'" class="btn-primary" @click="handleSelect" :disabled="selectedQuestions.length === 0">
          选择题目 ({{ selectedQuestions.length }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../composables/useCourse.js'
import { useGateway } from '../composables/useGateway.js'

const props = defineProps({
  user: { type: Object, default: null },
  mode: { type: String, default: 'view' },  // 'view' or 'select'
})
const emit = defineEmits(['close', 'select', 'updated'])
const route = useRoute()
const { fetchQuestionBank, deleteFromQuestionBank, addToQuestionBank, batchAddToQuestionBank, updateQuestionBank } = useCourse()
const { getToken, sendAiGenerateQuestions } = useGateway()

const courseId = route.params.courseId
const loading = ref(true)
const questions = ref([])
const filterType = ref('')
const selectedQuestions = ref([])
const showAddForm = ref(false)
const showAIForm = ref(false)
const aiGenerating = ref(false)
const aiError = ref('')
const editingQuestion = ref(null)
const previewQuestions = ref([])
const previewSaving = ref(false)

const aiForm = reactive({
  content: '',
  numQuestions: 10,
  typeDistribution: {
    choice: 0,
    true_false: 0,
    fill: 0,
    short_answer: 0,
    essay: 0,
  },
})

const newQuestion = reactive({
  type: 'short_answer',
  content: '',
  points: 10,
  answer: '',
  options: ['', '', '', ''],
  explanation: '',
})

const selectedIds = computed(() => new Set(selectedQuestions.value.map(q => q.id)))

const TYPE_ORDER = { choice: 0, true_false: 1, fill: 2, short_answer: 3, essay: 4 }

const filteredQuestions = computed(() => {
  let list = questions.value
  if (filterType.value) list = list.filter(q => q.questionType === filterType.value)
  return [...list].sort((a, b) => (TYPE_ORDER[a.questionType] ?? 9) - (TYPE_ORDER[b.questionType] ?? 9))
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

function toggleSelect(q) {
  const idx = selectedQuestions.value.findIndex(item => item.id === q.id)
  if (idx >= 0) {
    selectedQuestions.value.splice(idx, 1)
  } else {
    selectedQuestions.value.push(q)
  }
}

async function loadQuestions() {
  loading.value = true
  try {
    const token = getToken()
    questions.value = await fetchQuestionBank(courseId, token)
  } catch (e) {
    console.error('Failed to load question bank:', e)
  } finally {
    loading.value = false
  }
}

async function handleAddQuestion() {
  if (!newQuestion.content.trim()) return
  try {
    const token = getToken()
    const questionData = {
      type: newQuestion.type,
      content: newQuestion.content.trim(),
      points: newQuestion.points,
      answer: newQuestion.answer,
      explanation: newQuestion.explanation,
    }
    if (newQuestion.type === 'choice') {
      questionData.options = newQuestion.options.filter(o => o.trim()).map((o, idx) => ({
        key: String.fromCharCode(65 + idx),
        text: o.trim(),
      }))
    }

    const result = await addToQuestionBank(courseId, questionData, props.user?.role, props.user?.userId, token)
    questions.value.unshift(result.question)
    emit('updated')

    // Reset form
    newQuestion.content = ''
    newQuestion.answer = ''
    newQuestion.explanation = ''
    newQuestion.options = ['', '', '', '']
    showAddForm.value = false
  } catch (e) {
    alert('添加失败: ' + (e.message || '未知错误'))
  }
}

async function handleDelete(q) {
  if (!confirm('确定要从题库中删除这道题吗？')) return
  try {
    const token = getToken()
    await deleteFromQuestionBank(courseId, q.id, props.user?.role, props.user?.userId, token)
    questions.value = questions.value.filter(item => item.id !== q.id)
    selectedQuestions.value = selectedQuestions.value.filter(item => item.id !== q.id)
    emit('updated')
  } catch (e) {
    alert('删除失败: ' + (e.message || '未知错误'))
  }
}

function handleEdit(q) {
  // Deep clone the question for editing
  editingQuestion.value = {
    id: q.id,
    questionType: q.questionType || 'short_answer',
    content: q.content || '',
    points: q.points || 10,
    answer: q.answer || '',
    options: q.options ? q.options.map(opt => ({ ...opt })) : [],
    explanation: q.explanation || '',
  }
}

async function handleSaveEdit() {
  if (!editingQuestion.value || !editingQuestion.value.content.trim()) return
  try {
    const token = getToken()
    const updateData = {
      type: editingQuestion.value.questionType,
      content: editingQuestion.value.content.trim(),
      points: editingQuestion.value.points,
      answer: editingQuestion.value.answer,
      explanation: editingQuestion.value.explanation,
    }
    if (editingQuestion.value.questionType === 'choice') {
      updateData.options = editingQuestion.value.options.filter(o => o.text?.trim())
    }

    const result = await updateQuestionBank(courseId, editingQuestion.value.id, updateData, props.user?.role, props.user?.userId, token)
    if (result.question) {
      // Update the question in the list
      const idx = questions.value.findIndex(item => item.id === editingQuestion.value.id)
      if (idx >= 0) {
        questions.value[idx] = result.question
      }
    }
    editingQuestion.value = null
    emit('updated')
  } catch (e) {
    alert('保存失败: ' + (e.message || '未知错误'))
  }
}

async function handleAIGenerate() {
  if (!aiForm.content.trim()) {
    aiError.value = '请输入知识内容'
    return
  }

  // Build type distribution (only include non-zero values)
  const typeDistribution = {}
  for (const [key, val] of Object.entries(aiForm.typeDistribution)) {
    if (val > 0) {
      typeDistribution[key] = val
    }
  }

  aiGenerating.value = true
  aiError.value = ''

  try {
    const result = await sendAiGenerateQuestions({
      content: aiForm.content.trim(),
      numQuestions: aiForm.numQuestions,
      typeDistribution,
    }, 120000)

    if (result.questions && result.questions.length > 0) {
      // Show preview instead of auto-saving
      previewQuestions.value = result.questions
      showAIForm.value = false
    } else {
      aiError.value = 'AI 未能生成题目，请重试'
    }
  } catch (e) {
    aiError.value = e.message || 'AI 生成失败，请重试'
  } finally {
    aiGenerating.value = false
  }
}

async function handleSavePreview() {
  if (previewQuestions.value.length === 0) return
  previewSaving.value = true
  const total = previewQuestions.value.length
  try {
    const token = getToken()
    const saved = []
    // Save one by one to avoid URL length limit (HTTP 431)
    for (const q of previewQuestions.value) {
      try {
        const result = await addToQuestionBank(courseId, q, props.user?.role, props.user?.userId, token)
        if (result.question) saved.push(result.question)
      } catch (e) {
        console.error('Failed to save question:', q.content, e)
      }
    }
    if (saved.length > 0) {
      questions.value.unshift(...saved)
    }
    previewQuestions.value = []
    aiForm.content = ''
    emit('updated')
    if (saved.length < total) {
      alert(`已保存 ${saved.length} 道题，${total - saved.length} 道保存失败`)
    }
  } catch (e) {
    alert('保存失败: ' + (e.message || '未知错误'))
  } finally {
    previewSaving.value = false
  }
}

function handleSelect() {
  // Convert to homework question format
  const formatted = selectedQuestions.value.map((q, i) => ({
    type: q.questionType,
    content: q.content,
    points: q.points,
    answer: q.answer,
    options: q.options || [],
    explanation: q.explanation || '',
  }))
  emit('select', formatted)
  emit('close')
}

onMounted(loadQuestions)
</script>

<style scoped>
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #fff; border: 1.8px solid var(--accent); border-radius: 16px; padding: 24px; width: 560px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 0 24px var(--accent-glow); }
.dialog-card-wide { width: 720px; }
.dialog-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.dialog-header h3 { margin: 0; font-size: 1.15rem; color: var(--text-primary); }
.btn-close { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: var(--text-muted); padding: 4px; }
.btn-close:hover { color: var(--text-primary); }

/* Add Form */
.add-form { background: var(--bg-root); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.add-form h4 { margin: 0 0 12px; font-size: 0.95rem; color: var(--text-primary); }
.form-row { display: flex; gap: 10px; margin-bottom: 10px; }
.q-type-select { flex: 1; padding: 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; color: var(--text-primary); outline: none; }
.q-type-select:focus { border-color: var(--accent); }
.points-input { width: 80px; padding: 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; color: var(--text-primary); outline: none; box-sizing: border-box; }
.points-input:focus { border-color: var(--accent); }
.q-content-input { width: 100%; padding: 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; resize: vertical; box-sizing: border-box; color: var(--text-primary); outline: none; }
.q-content-input:focus { border-color: var(--accent); }
.options-section { margin: 10px 0; padding: 10px; background: #fff; border-radius: 8px; border: 1px solid var(--border-light); }
.option-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.option-row span { min-width: 20px; font-weight: 600; color: var(--accent); }
.option-row input { flex: 1; padding: 6px 8px; border: 1px solid var(--border-medium); border-radius: 4px; font-size: 0.82rem; color: var(--text-primary); outline: none; }
.option-row input:focus { border-color: var(--accent); }
.option-row button { background: none; border: none; color: var(--text-muted); cursor: pointer; }
.option-row button:hover { color: var(--danger); }
.btn-add-opt { background: none; border: 1px dashed var(--border-medium); border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }
.btn-add-opt:hover { border-color: var(--accent); color: var(--accent); }
.answer-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.answer-row label { font-size: 0.82rem; color: var(--text-secondary); min-width: 70px; }
.answer-row select, .answer-row textarea { flex: 1; padding: 6px 8px; border: 1px solid var(--border-medium); border-radius: 4px; font-size: 0.82rem; color: var(--text-primary); outline: none; }
.answer-row select:focus, .answer-row textarea:focus { border-color: var(--accent); }
.explanation-input { width: 100%; padding: 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; margin-top: 10px; resize: vertical; box-sizing: border-box; color: var(--text-primary); outline: none; }
.explanation-input:focus { border-color: var(--accent); }

.filter-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.filter-select { padding: 6px 12px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; outline: none; color: var(--text-primary); }
.filter-select:focus { border-color: var(--accent); }
.question-count { font-size: 0.82rem; color: var(--text-muted); }
.filter-actions { margin-left: auto; display: flex; gap: 8px; }
.btn-add { padding: 6px 12px; background: linear-gradient(135deg,var(--accent),var(--accent-deep)); color: #fff; border: none; border-radius: 8px; font-size: 0.82rem; cursor: pointer; box-shadow: 0 2px 8px var(--accent-glow); }
.btn-add:hover { opacity: 0.9; }
.btn-ai { padding: 6px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; border-radius: 8px; font-size: 0.82rem; cursor: pointer; }
.btn-ai:hover { opacity: 0.9; }

/* AI Form */
.ai-form { background: var(--bg-root); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.ai-form h4 { margin: 0 0 12px; font-size: 0.95rem; color: var(--text-primary); }
.ai-form .form-group { margin-bottom: 10px; }
.ai-form .form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; }
.ai-form textarea { width: 100%; padding: 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.85rem; resize: vertical; box-sizing: border-box; color: var(--text-primary); outline: none; }
.ai-form textarea:focus { border-color: var(--accent); }
.ai-config-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 8px; }
.form-group.compact { margin-bottom: 0; }
.form-group.compact label { font-size: 0.75rem; text-align: center; }
.form-group.compact input { width: 100%; padding: 6px 8px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 6px; font-size: 0.82rem; box-sizing: border-box; color: var(--text-primary); outline: none; }
.form-group.compact input:focus { border-color: var(--accent); }
.ai-hint { font-size: 0.75rem; color: var(--text-muted); margin: 8px 0; }
.error-text { color: var(--danger); font-size: 0.8rem; margin-top: 8px; }

/* Inline Edit Form */
.inline-edit-form { padding: 4px 0; }
.inline-edit-form .form-row { display: flex; gap: 10px; margin-bottom: 10px; }

.question-list { flex: 1; overflow-y: auto; min-height: 200px; max-height: 50vh; }
.question-item { background: var(--bg-root); border: 1px solid var(--border-light); border-radius: 10px; padding: 12px; margin-bottom: 10px; cursor: default; transition: all 0.2s; }
.question-item.selected { border-color: var(--accent); background: var(--accent-soft); }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.q-checkbox input { width: 16px; height: 16px; cursor: pointer; accent-color: var(--accent); }
.q-num { font-weight: 700; color: var(--accent); font-size: 0.85rem; min-width: 20px; }
.q-type-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: var(--accent-soft); color: var(--accent); }
.q-points { font-size: 0.78rem; color: var(--text-muted); }
.q-source { font-size: 0.72rem; color: var(--text-muted); margin-left: auto; }
.btn-delete-q { background: none; border: none; cursor: pointer; font-size: 0.85rem; color: var(--text-muted); transition: color 0.2s; }
.btn-delete-q:hover { color: var(--danger); }
.btn-edit-q { background: none; border: none; cursor: pointer; font-size: 0.85rem; color: var(--text-muted); transition: color 0.2s; }
.btn-edit-q:hover { color: var(--accent); }
.q-content { font-size: 0.88rem; line-height: 1.5; color: var(--text-primary); margin-bottom: 4px; }
.q-answer, .q-explanation { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; }
.q-answer .label, .q-explanation .label { font-weight: 600; color: var(--text-primary); }
.q-options { margin: 6px 0; padding: 6px 0; }
.q-option { display: flex; align-items: baseline; gap: 6px; font-size: 0.82rem; line-height: 1.6; }
.opt-key { font-weight: 600; color: var(--text-secondary); min-width: 18px; }
.opt-key.correct { color: var(--success); }
.opt-text { color: var(--text-secondary); }

.loading-hint, .empty-hint { text-align: center; padding: 40px; color: var(--text-muted); }

/* Preview Section */
.preview-section { margin-bottom: 16px; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.preview-header h4 { margin: 0; font-size: 0.95rem; color: var(--accent); }
.preview-actions { display: flex; gap: 8px; }
.preview-list { max-height: 45vh; }
.preview-item { border-left: 3px solid var(--accent); }

.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 12px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: linear-gradient(135deg,var(--accent),var(--accent-deep)); color: #fff; border: none; border-radius: 10px; font-size: 0.85rem; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px var(--accent-glow); }
.btn-primary:disabled { opacity: 0.5; }
.btn-secondary { padding: 10px 24px; background: var(--bg-root); color: var(--text-primary); border: 1.5px solid var(--border-medium); border-radius: 10px; font-size: 0.85rem; cursor: pointer; }
.btn-secondary:hover { background: var(--accent-soft); border-color: var(--accent); }

.dark .dialog-card { background: #1e1e2e; }
.dark .add-form, .dark .ai-form { background: #1a1a2e; }
.dark .filter-select,
.dark .q-type-select,
.dark .points-input,
.dark .q-content-input,
.dark .explanation-input,
.dark .option-row input,
.dark .answer-row select,
.dark .answer-row textarea,
.dark .ai-form textarea,
.dark .form-group.compact input { background: #252535; border-color: #444; color: #e0e0e0; }
.dark .options-section { background: #2a2a3a; border-color: #444; }
.dark .question-item { background: #1a1a2e; border-color: #333; }
.dark .question-item.selected { background: #1e1e3e; border-color: var(--accent); }
</style>
