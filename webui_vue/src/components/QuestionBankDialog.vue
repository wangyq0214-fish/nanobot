<template>
  <div class="qb-overlay" @click.self="$emit('close')">
    <div class="qb-modal">
      <!-- Header -->
      <div class="qb-header">
        <div class="qb-header-left">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            <path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
          </svg>
          <h3>课程题库中心</h3>
        </div>
        <button class="qb-close" @click="$emit('close')">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
          </svg>
        </button>
      </div>

      <!-- ===== Empty State: 3 Entry Cards ===== -->
      <div v-if="!showAddForm && !showAIForm && questions.length === 0 && !loading" class="qb-empty">
        <div class="qb-empty-text">
          <h4>暂无自定义题库数据</h4>
          <p>通过以下三种方式快捷构建结构化试题资产矩阵，支持自动解析与智能推荐。</p>
        </div>
        <div class="qb-entry-grid">
          <!-- Card 1: Import Text -->
          <div class="qb-entry-card" @click="showAddForm = true">
            <div class="qb-entry-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
                <path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>
              </svg>
            </div>
            <div class="qb-entry-body">
              <h5>导入文本自动转换</h5>
              <p>粘贴大段文献资料或题目文本，快速解析为标准题目结构并录入题库。</p>
            </div>
            <span class="qb-entry-action">启动解析流 →</span>
          </div>

          <!-- Card 2: Manual Add -->
          <div class="qb-entry-card" @click="showAddForm = true">
            <div class="qb-entry-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>
              </svg>
            </div>
            <div class="qb-entry-body">
              <h5>手动结构化添加</h5>
              <p>标准可视化表单录入，支持对单选、多选、判断及论述大题的分值与解析做精确配置。</p>
            </div>
            <span class="qb-entry-action">空白表单 →</span>
          </div>

          <!-- Card 3: AI Generate -->
          <div class="qb-entry-card ai" @click="showAIForm = true">
            <div class="qb-entry-icon ai-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
              </svg>
            </div>
            <div class="qb-entry-body">
              <h5>AI 智能矩阵生成</h5>
              <p>联动当前章节的 AI 教案，召唤专家级 Agent 智能分析薄弱学情，一键定向演化多模态试题。</p>
            </div>
            <span class="qb-entry-action ai-action">大模型协同 →</span>
          </div>
        </div>
      </div>

      <!-- ===== Non-empty: Filter Bar + Add Buttons ===== -->
      <div v-if="!showAddForm && !showAIForm && questions.length > 0" class="qb-toolbar">
        <div class="qb-toolbar-left">
          <select v-model="filterType" class="qb-filter-select">
            <option value="">全部题型</option>
            <option value="choice">选择题</option>
            <option value="true_false">判断题</option>
            <option value="fill">填空题</option>
            <option value="short_answer">简答题</option>
            <option value="essay">论述题</option>
          </select>
          <span class="qb-count">{{ filteredQuestions.length }} 道题</span>
        </div>
        <div class="qb-toolbar-right">
          <button class="qb-btn-outline" @click="showAddForm = true">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>
            </svg>
            <span>手动添加</span>
          </button>
          <button class="qb-btn-ai" @click="showAIForm = true">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
            <span>AI 生成</span>
          </button>
        </div>
      </div>

      <!-- ===== Add Question Form ===== -->
      <div v-if="showAddForm" class="qb-form-area">
        <div class="qb-form-header">
          <h4>添加题目到题库</h4>
          <button class="qb-close-sm" @click="showAddForm = false">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <div class="qb-form-body">
          <div class="qb-form-row">
            <select v-model="newQuestion.type" class="qb-input">
              <option value="choice">选择题</option>
              <option value="true_false">判断题</option>
              <option value="fill">填空题</option>
              <option value="short_answer">简答题</option>
              <option value="essay">论述题</option>
            </select>
            <input v-model.number="newQuestion.points" type="number" min="1" class="qb-input qb-input-sm" placeholder="分值" />
          </div>
          <textarea v-model="newQuestion.content" rows="3" placeholder="题目内容" class="qb-input qb-textarea"></textarea>

          <!-- Choice options -->
          <div v-if="newQuestion.type === 'choice'" class="qb-options">
            <div v-for="(opt, oi) in newQuestion.options" :key="oi" class="qb-opt-row">
              <span class="qb-opt-key">{{ String.fromCharCode(65 + oi) }}.</span>
              <input v-model="newQuestion.options[oi]" placeholder="选项内容" class="qb-input" />
              <button class="qb-opt-del" @click="newQuestion.options.splice(oi, 1)">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>
            <button class="qb-add-opt" @click="newQuestion.options.push('')">+ 添加选项</button>
            <div class="qb-answer-row">
              <label>正确答案：</label>
              <select v-model="newQuestion.answer" class="qb-input">
                <option v-for="(opt, oi) in newQuestion.options" :key="oi" :value="String.fromCharCode(65 + oi)">
                  {{ String.fromCharCode(65 + oi) }}
                </option>
              </select>
            </div>
          </div>

          <!-- True/False -->
          <div v-if="newQuestion.type === 'true_false'" class="qb-answer-row">
            <label>正确答案：</label>
            <select v-model="newQuestion.answer" class="qb-input">
              <option value="true">正确</option>
              <option value="false">错误</option>
            </select>
          </div>

          <!-- Other types -->
          <div v-if="['fill', 'short_answer', 'essay'].includes(newQuestion.type)" class="qb-answer-row">
            <label>参考答案：</label>
            <textarea v-model="newQuestion.answer" rows="2" placeholder="参考答案" class="qb-input qb-textarea"></textarea>
          </div>

          <textarea v-model="newQuestion.explanation" rows="2" placeholder="解析（可选）" class="qb-input qb-textarea"></textarea>
        </div>

        <div class="qb-form-actions">
          <button class="qb-btn-cancel" @click="showAddForm = false">取消</button>
          <button class="qb-btn-primary" @click="handleAddQuestion" :disabled="!newQuestion.content.trim()">添加到题库</button>
        </div>
      </div>

      <!-- ===== AI Generate Form ===== -->
      <div v-if="showAIForm" class="qb-form-area">
        <div class="qb-form-header">
          <h4>AI 智能出题</h4>
          <button class="qb-close-sm" @click="showAIForm = false">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <div class="qb-form-body">
          <div class="qb-field">
            <label>知识内容</label>
            <textarea v-model="aiForm.content" rows="4" placeholder="粘贴教材、笔记或知识点..." class="qb-input qb-textarea"></textarea>
          </div>
          <div class="qb-ai-grid">
            <div class="qb-field qb-field-sm">
              <label>题目数量</label>
              <input v-model.number="aiForm.numQuestions" type="number" min="1" max="50" class="qb-input" />
            </div>
            <div class="qb-field qb-field-sm">
              <label>选择题</label>
              <input v-model.number="aiForm.typeDistribution.choice" type="number" min="0" placeholder="0" class="qb-input" />
            </div>
            <div class="qb-field qb-field-sm">
              <label>判断题</label>
              <input v-model.number="aiForm.typeDistribution.true_false" type="number" min="0" placeholder="0" class="qb-input" />
            </div>
            <div class="qb-field qb-field-sm">
              <label>填空题</label>
              <input v-model.number="aiForm.typeDistribution.fill" type="number" min="0" placeholder="0" class="qb-input" />
            </div>
            <div class="qb-field qb-field-sm">
              <label>简答题</label>
              <input v-model.number="aiForm.typeDistribution.short_answer" type="number" min="0" placeholder="0" class="qb-input" />
            </div>
            <div class="qb-field qb-field-sm">
              <label>论述题</label>
              <input v-model.number="aiForm.typeDistribution.essay" type="number" min="0" placeholder="0" class="qb-input" />
            </div>
          </div>
          <p class="qb-hint">题型分布可选，不填则由 AI 自动分配</p>
          <p v-if="aiError" class="qb-error">{{ aiError }}</p>
        </div>

        <div class="qb-form-actions">
          <button class="qb-btn-cancel" @click="showAIForm = false">取消</button>
          <button class="qb-btn-primary" @click="handleAIGenerate" :disabled="aiGenerating || !aiForm.content.trim()">
            {{ aiGenerating ? '生成中...' : '生成题目' }}
          </button>
        </div>
      </div>

      <!-- ===== AI Preview ===== -->
      <div v-if="previewQuestions.length > 0" class="qb-preview">
        <div class="qb-preview-header">
          <h4>AI 生成预览（{{ previewQuestions.length }} 道题）</h4>
          <div class="qb-preview-actions">
            <button class="qb-btn-cancel" @click="previewQuestions = []">丢弃</button>
            <button class="qb-btn-primary" @click="handleSavePreview" :disabled="previewSaving">
              {{ previewSaving ? '保存中...' : '保存到题库' }}
            </button>
          </div>
        </div>
        <div class="qb-preview-list">
          <div v-for="(q, qi) in previewQuestions" :key="qi" class="qb-q-card preview">
            <div class="qb-q-top">
              <span class="qb-q-num">{{ qi + 1 }}</span>
              <span class="qb-q-type">{{ getTypeLabel(q.type) }}</span>
              <span class="qb-q-pts">{{ q.points }}分</span>
              <button class="qb-q-del" @click="previewQuestions.splice(qi, 1)" title="移除">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </button>
            </div>
            <div class="qb-q-content">{{ q.content }}</div>
            <div v-if="q.type === 'choice' && q.options" class="qb-q-options">
              <div v-for="opt in q.options" :key="opt.key" class="qb-q-opt">
                <span class="qb-opt-key" :class="{ correct: opt.key === q.answer }">{{ opt.key }}.</span>
                <span>{{ opt.text }}</span>
              </div>
            </div>
            <div v-if="q.answer" class="qb-q-answer">
              <span class="qb-label">答案：</span>{{ q.answer }}
            </div>
            <div v-if="q.explanation" class="qb-q-explain">
              <span class="qb-label">解析：</span>{{ q.explanation }}
            </div>
          </div>
        </div>
      </div>

      <!-- ===== Question List ===== -->
      <div v-if="previewQuestions.length === 0 && !showAddForm && !showAIForm" class="qb-list">
        <div v-if="loading" class="qb-status">加载中...</div>
        <div v-else-if="questions.length === 0" class="qb-status"></div>
        <div v-else-if="filteredQuestions.length === 0" class="qb-status">没有该题型的题目</div>
        <div v-for="(q, qi) in filteredQuestions" :key="q.id" class="qb-q-card"
             :class="{ selected: mode === 'select' && selectedIds.has(q.id), editing: editingQuestion && editingQuestion.id === q.id }"
             @click="mode === 'select' ? toggleSelect(q) : null">

          <!-- View Mode -->
          <template v-if="!(editingQuestion && editingQuestion.id === q.id)">
            <div class="qb-q-top">
              <span v-if="mode === 'select'" class="qb-q-check">
                <input type="checkbox" :checked="selectedIds.has(q.id)" @click.stop="toggleSelect(q)" />
              </span>
              <span class="qb-q-num">{{ qi + 1 }}</span>
              <span class="qb-q-type">{{ getTypeLabel(q.questionType) }}</span>
              <span class="qb-q-pts">{{ q.points }}分</span>
              <span v-if="q.source === 'ai'" class="qb-q-ai">AI</span>
              <div class="qb-q-actions">
                <button class="qb-q-fav" @click.stop="handleFavorite(q)" title="收藏到我的题库">
                  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                  </svg>
                </button>
                <button class="qb-q-edit" @click.stop="handleEdit(q)" title="编辑">
                  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button class="qb-q-del" @click.stop="handleDelete(q)" title="删除">
                  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="qb-q-content">{{ q.content }}</div>
            <div v-if="q.type === 'choice' && q.options" class="qb-q-options">
              <div v-for="opt in q.options" :key="opt.key" class="qb-q-opt">
                <span class="qb-opt-key" :class="{ correct: opt.key === q.answer }">{{ opt.key }}.</span>
                <span>{{ opt.text }}</span>
              </div>
            </div>
            <div v-if="q.answer" class="qb-q-answer">
              <span class="qb-label">答案：</span>{{ q.answer }}
            </div>
            <div v-if="q.explanation" class="qb-q-explain">
              <span class="qb-label">解析：</span>{{ q.explanation }}
            </div>
          </template>

          <!-- Inline Edit Mode -->
          <template v-else>
            <div class="qb-edit-form">
              <div class="qb-form-row">
                <select v-model="editingQuestion.questionType" class="qb-input">
                  <option value="choice">选择题</option>
                  <option value="true_false">判断题</option>
                  <option value="fill">填空题</option>
                  <option value="short_answer">简答题</option>
                  <option value="essay">论述题</option>
                </select>
                <input v-model.number="editingQuestion.points" type="number" min="1" class="qb-input qb-input-sm" placeholder="分值" />
              </div>
              <textarea v-model="editingQuestion.content" rows="3" placeholder="题目内容" class="qb-input qb-textarea"></textarea>

              <!-- Choice options -->
              <div v-if="editingQuestion.questionType === 'choice'" class="qb-options">
                <div v-for="(opt, oi) in editingQuestion.options" :key="oi" class="qb-opt-row">
                  <span class="qb-opt-key">{{ String.fromCharCode(65 + oi) }}.</span>
                  <input v-model="editingQuestion.options[oi].text" placeholder="选项内容" class="qb-input" />
                  <button class="qb-opt-del" @click="editingQuestion.options.splice(oi, 1)">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  </button>
                </div>
                <button class="qb-add-opt" @click="editingQuestion.options.push({key: String.fromCharCode(65 + editingQuestion.options.length), text: ''})">+ 添加选项</button>
                <div class="qb-answer-row">
                  <label>正确答案：</label>
                  <select v-model="editingQuestion.answer" class="qb-input">
                    <option v-for="(opt, oi) in editingQuestion.options" :key="oi" :value="opt.key">{{ opt.key }}</option>
                  </select>
                </div>
              </div>

              <!-- True/False -->
              <div v-if="editingQuestion.questionType === 'true_false'" class="qb-answer-row">
                <label>正确答案：</label>
                <select v-model="editingQuestion.answer" class="qb-input">
                  <option value="true">正确</option>
                  <option value="false">错误</option>
                </select>
              </div>

              <!-- Other types -->
              <div v-if="['fill', 'short_answer', 'essay'].includes(editingQuestion.questionType)" class="qb-answer-row">
                <label>参考答案：</label>
                <textarea v-model="editingQuestion.answer" rows="2" placeholder="参考答案" class="qb-input qb-textarea"></textarea>
              </div>

              <textarea v-model="editingQuestion.explanation" rows="2" placeholder="解析（可选）" class="qb-input qb-textarea"></textarea>

              <div class="qb-form-actions">
                <button class="qb-btn-cancel" @click="editingQuestion = null">取消</button>
                <button class="qb-btn-primary" @click="handleSaveEdit" :disabled="!editingQuestion.content.trim()">保存修改</button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Footer -->
      <div class="qb-footer">
        <button class="qb-btn-cancel" @click="$emit('close')">关闭</button>
        <button v-if="mode === 'select'" class="qb-btn-primary" @click="handleSelect" :disabled="selectedQuestions.length === 0">
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
import { useMyResources } from '../composables/useMyResources.js'

const props = defineProps({
  user: { type: Object, default: null },
  mode: { type: String, default: 'view' },
})
const emit = defineEmits(['close', 'select', 'updated'])
const route = useRoute()
const { fetchQuestionBank, deleteFromQuestionBank, addToQuestionBank, updateQuestionBank } = useCourse()
const { getToken, sendAiGenerateQuestions } = useGateway()
const { favoriteQuestion } = useMyResources()

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
  const labels = { choice: '选择题', true_false: '判断题', fill: '填空题', short_answer: '简答题', essay: '论述题' }
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
    newQuestion.content = ''
    newQuestion.answer = ''
    newQuestion.explanation = ''
    newQuestion.options = ['', '', '', '']
    showAddForm.value = false
  } catch (e) {
    alert('添加失败: ' + (e.message || '未知错误'))
  }
}

async function handleFavorite(q) {
  try {
    await favoriteQuestion(courseId, q.id)
    alert('已收藏到我的题库')
  } catch (e) {
    alert('收藏失败: ' + (e.message || '未知错误'))
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
      const idx = questions.value.findIndex(item => item.id === editingQuestion.value.id)
      if (idx >= 0) questions.value[idx] = result.question
    }
    editingQuestion.value = null
    emit('updated')
  } catch (e) {
    alert('保存失败: ' + (e.message || '未知错误'))
  }
}

async function handleAIGenerate() {
  if (!aiForm.content.trim()) { aiError.value = '请输入知识内容'; return }
  const typeDistribution = {}
  for (const [key, val] of Object.entries(aiForm.typeDistribution)) {
    if (val > 0) typeDistribution[key] = val
  }
  aiGenerating.value = true
  aiError.value = ''
  try {
    const result = await sendAiGenerateQuestions({ content: aiForm.content.trim(), numQuestions: aiForm.numQuestions, typeDistribution }, 120000)
    if (result.questions && result.questions.length > 0) {
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
    for (const q of previewQuestions.value) {
      try {
        const result = await addToQuestionBank(courseId, q, props.user?.role, props.user?.userId, token)
        if (result.question) saved.push(result.question)
      } catch (e) {
        console.error('Failed to save question:', q.content, e)
      }
    }
    if (saved.length > 0) questions.value.unshift(...saved)
    previewQuestions.value = []
    aiForm.content = ''
    emit('updated')
    if (saved.length < total) alert(`已保存 ${saved.length} 道题，${total - saved.length} 道保存失败`)
  } catch (e) {
    alert('保存失败: ' + (e.message || '未知错误'))
  } finally {
    previewSaving.value = false
  }
}

function handleSelect() {
  const formatted = selectedQuestions.value.map((q) => ({
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
/* ========== Overlay & Modal ========== */
.qb-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 24px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.qb-modal {
  background: var(--bg-card, #ffffff);
  border-radius: 20px;
  width: 100%;
  max-width: 800px;
  height: 72vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border-light, #f0f0f0);
  overflow: hidden;
  animation: scaleUp 0.25s ease;
}

@keyframes scaleUp {
  from { transform: scale(0.96); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* ========== Header ========== */
.qb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  flex-shrink: 0;
}

.qb-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary, #121212);
}

.qb-header-left h3 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
  font-family: 'Noto Serif SC', serif;
}

.qb-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted, #9ca3af);
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qb-close:hover {
  color: var(--text-primary, #121212);
  background: var(--accent-soft, #f5f5f5);
}

/* ========== Empty State ========== */
.qb-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 32px;
  background: var(--bg-card-alt, #fafbfa);
  overflow-y: auto;
}

.qb-empty-text {
  text-align: center;
  margin-bottom: 32px;
  max-width: 400px;
}

.qb-empty-text h4 {
  margin: 0 0 6px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
  font-family: 'Noto Serif SC', serif;
}

.qb-empty-text p {
  margin: 0;
  font-size: 0.72rem;
  color: var(--text-muted, #9ca3af);
  line-height: 1.6;
}

.qb-entry-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 680px;
}

.qb-entry-card {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-light, #eef0ee);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 192px;
  cursor: pointer;
  transition: all 0.25s;
}

.qb-entry-card:hover {
  border-color: var(--accent, #121212);
  box-shadow: 0 4px 20px var(--accent-glow, rgba(0, 0, 0, 0.06));
}

.qb-entry-card.ai:hover {
  border-color: var(--warning, #92400e);
}

.qb-entry-icon {
  width: 36px;
  height: 36px;
  background: var(--bg-card-alt, #f9fafb);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary, #121212);
  margin-bottom: 14px;
  transition: all 0.25s;
}

.qb-entry-card:hover .qb-entry-icon {
  background: var(--accent, #121212);
  color: var(--bg-card, #ffffff);
}

.qb-entry-icon.ai-icon {
  background: var(--status-bg, #fffbeb);
  color: var(--status-text, #92400e);
  border: 1px solid var(--status-border, #fef3c7);
}

.qb-entry-card.ai:hover .qb-entry-icon.ai-icon {
  background: var(--accent, #121212);
  color: var(--bg-card, #ffffff);
  border-color: transparent;
}

.qb-entry-body h5 {
  margin: 0 0 6px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
  font-family: 'Noto Serif SC', serif;
}

.qb-entry-body p {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-muted, #9ca3af);
  line-height: 1.6;
}

.qb-entry-action {
  font-size: 0.62rem;
  font-family: monospace;
  color: var(--text-muted, #9ca3af);
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid var(--divider, #f9fafb);
  transition: color 0.2s;
}

.qb-entry-card:hover .qb-entry-action {
  color: var(--text-primary, #121212);
}

.qb-entry-action.ai-action {
  color: var(--status-text, #92400e);
}

.qb-entry-card.ai:hover .qb-entry-action.ai-action {
  color: var(--text-primary, #121212);
}

/* ========== Toolbar (non-empty) ========== */
.qb-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.qb-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qb-toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qb-filter-select {
  padding: 6px 12px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-medium, #e0e0e0);
  border-radius: 8px;
  font-size: 0.78rem;
  color: var(--text-primary, #121212);
  outline: none;
  transition: border 0.2s;
}

.qb-filter-select:focus {
  border-color: var(--accent, #121212);
}

.qb-count {
  font-size: 0.72rem;
  color: var(--text-muted, #9ca3af);
  background: var(--accent-soft, rgba(18, 18, 18, 0.04));
  padding: 3px 10px;
  border-radius: 6px;
  font-family: monospace;
}

/* ========== Buttons ========== */
.qb-btn-outline {
  padding: 6px 14px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--accent, #121212);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent, #121212);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.qb-btn-outline:hover {
  background: var(--accent, #121212);
  color: var(--bg-card, #ffffff);
}

.qb-btn-ai {
  padding: 6px 14px;
  background: var(--accent, #121212);
  border: 1px solid var(--accent, #121212);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--bg-card, #ffffff);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.qb-btn-ai:hover {
  background: var(--accent-deep, #333333);
}

.qb-btn-primary {
  padding: 8px 20px;
  background: var(--accent, #121212);
  color: var(--bg-card, #ffffff);
  border: none;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.qb-btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.qb-btn-primary:not(:disabled):hover {
  background: var(--accent-deep, #333333);
}

.qb-btn-cancel {
  padding: 8px 20px;
  background: var(--bg-card, #ffffff);
  color: var(--text-primary, #121212);
  border: 1px solid var(--border-medium, #e0e0e0);
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.qb-btn-cancel:hover {
  background: var(--accent-soft, #f9fafb);
  border-color: var(--accent, #121212);
}

/* ========== Form Area ========== */
.qb-form-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.qb-form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  flex-shrink: 0;
}

.qb-form-header h4 {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.qb-close-sm {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted, #9ca3af);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
}

.qb-close-sm:hover {
  color: var(--text-primary, #121212);
}

.qb-form-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
  background: var(--bg-card-alt, #fafbfa);
}

.qb-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--border-light, #f0f0f0);
  background: var(--bg-card, #fdfdfd);
  flex-shrink: 0;
}

/* ========== Form Elements ========== */
.qb-form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.qb-input {
  padding: 8px 12px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-medium, #e0e0e0);
  border-radius: 8px;
  font-size: 0.82rem;
  color: var(--text-primary, #121212);
  outline: none;
  transition: border 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.qb-input:focus {
  border-color: var(--accent, #121212);
}

.qb-input-sm {
  width: 80px;
  flex-shrink: 0;
  text-align: center;
}

.qb-textarea {
  resize: vertical;
  min-height: 72px;
  margin-bottom: 12px;
  font-family: inherit;
}

.qb-options {
  margin: 12px 0;
  padding: 14px;
  background: var(--bg-card, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--border-light, #f0f0f0);
}

.qb-opt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.qb-opt-row:last-child {
  margin-bottom: 0;
}

.qb-opt-key {
  min-width: 22px;
  font-weight: 700;
  font-size: 0.82rem;
  color: var(--text-primary, #121212);
}

.qb-opt-key.correct {
  color: var(--success, #059669);
}

.qb-opt-del {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted, #9ca3af);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
}

.qb-opt-del:hover {
  color: var(--danger, #ef4444);
  background: rgba(239, 68, 68, 0.08);
}

.qb-add-opt {
  background: none;
  border: 1px dashed var(--border-medium, #e0e0e0);
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-muted, #9ca3af);
  margin-top: 8px;
  transition: all 0.2s;
}

.qb-add-opt:hover {
  border-color: var(--accent, #121212);
  color: var(--accent, #121212);
  background: var(--accent-soft, rgba(18, 18, 18, 0.03));
}

.qb-answer-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 12px;
}

.qb-answer-row label {
  font-size: 0.78rem;
  color: var(--text-secondary, #4a534c);
  min-width: 70px;
  padding-top: 8px;
  font-weight: 500;
}

.qb-field {
  margin-bottom: 14px;
}

.qb-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary, #4a534c);
  margin-bottom: 6px;
}

.qb-ai-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-bottom: 8px;
}

.qb-field-sm {
  margin-bottom: 0;
}

.qb-field-sm label {
  text-align: center;
  font-size: 0.7rem;
}

.qb-hint {
  font-size: 0.7rem;
  color: var(--text-muted, #9ca3af);
  margin: 8px 0 0;
}

.qb-error {
  color: var(--danger, #ef4444);
  font-size: 0.75rem;
  margin: 8px 0 0;
}

/* ========== Preview ========== */
.qb-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.qb-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  flex-shrink: 0;
}

.qb-preview-header h4 {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.qb-preview-actions {
  display: flex;
  gap: 8px;
}

.qb-preview-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

/* ========== Question Cards ========== */
.qb-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.qb-status {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted, #9ca3af);
  font-size: 0.82rem;
}

.qb-q-card {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-light, #f0f0f0);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 10px;
  transition: all 0.2s;
}

.qb-q-card:hover {
  border-color: var(--accent, #121212);
}

.qb-q-card.preview {
  border-left: 3px solid var(--accent, #121212);
}

.qb-q-card.selected {
  border-color: var(--accent, #121212);
  background: var(--accent-soft, rgba(18, 18, 18, 0.03));
}

.qb-q-card.editing {
  border-color: var(--accent, #121212);
  box-shadow: 0 0 0 3px var(--accent-glow, rgba(18, 18, 18, 0.06));
}

.qb-q-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.qb-q-check input {
  width: 15px;
  height: 15px;
  cursor: pointer;
  accent-color: var(--accent, #121212);
}

.qb-q-num {
  font-weight: 700;
  color: var(--bg-card, #ffffff);
  background: var(--accent, #121212);
  font-family: monospace;
  font-size: 0.72rem;
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.qb-q-type {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.qb-q-pts {
  font-size: 0.68rem;
  color: var(--text-muted, #9ca3af);
}

.qb-q-ai {
  font-size: 0.58rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--accent-soft, rgba(139, 112, 255, 0.1));
  color: var(--accent, #8b70ff);
}

.qb-q-actions {
  margin-left: auto;
  display: flex;
  gap: 2px;
}

.qb-q-edit,
.qb-q-del {
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  padding: 5px;
  border-radius: 6px;
  color: var(--text-muted, #9ca3af);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qb-q-edit:hover {
  background: var(--accent-soft, rgba(18, 18, 18, 0.05));
  border-color: var(--border-light, #f0f0f0);
  color: var(--text-primary, #121212);
}

.qb-q-del:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: var(--danger, #ef4444);
}

.qb-q-content {
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--text-primary, #121212);
  margin-bottom: 6px;
}

.qb-q-options {
  margin: 6px 0;
}

.qb-q-opt {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 0.78rem;
  line-height: 1.6;
  color: var(--text-secondary, #4a534c);
}

.qb-q-answer,
.qb-q-explain {
  font-size: 0.72rem;
  color: var(--text-secondary, #4a534c);
  margin-top: 8px;
  padding: 8px 10px;
  background: var(--accent-soft, #f9fafb);
  border-radius: 8px;
}

.qb-label {
  font-weight: 600;
  color: var(--text-primary, #121212);
}

/* ========== Edit Form ========== */
.qb-edit-form {
  padding: 4px 0;
}

/* ========== Footer ========== */
.qb-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--border-light, #f0f0f0);
  background: var(--bg-card, #fdfdfd);
  flex-shrink: 0;
}

/* ========== Responsive ========== */
@media (max-width: 640px) {
  .qb-entry-grid {
    grid-template-columns: 1fr;
  }

  .qb-ai-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .qb-modal {
    height: 90vh;
    border-radius: 16px;
  }
}
</style>
