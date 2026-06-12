<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog-card dialog-card-wide">
      <h3>布置作业</h3>
      <div class="form-group">
        <label>作业标题</label>
        <input v-model="form.title" placeholder="如：光合作用与产量形成" />
      </div>
      <div class="form-group">
        <label>作业说明</label>
        <textarea v-model="form.description" rows="2" placeholder="可选"></textarea>
      </div>
      <div class="form-group">
        <label>截止时间</label>
        <input v-model="form.deadline" type="datetime-local" />
      </div>

      <div class="questions-section">
        <div class="section-header">
          <label class="section-label">题目列表</label>
          <span class="question-count">{{ form.questions.length }} 题 · {{ totalPoints }} 分</span>
        </div>

        <!-- Empty state -->
        <div v-if="form.questions.length === 0" class="empty-questions">
          <p>请从题库选择题目</p>
          <button class="btn-from-bank" @click="showQuestionBank = true">📚 从题库选题</button>
        </div>

        <!-- Question list -->
        <div v-else>
          <div v-for="(q, qi) in form.questions" :key="qi" class="question-item">
            <div class="q-header">
              <span class="q-num">{{ qi + 1 }}</span>
              <span class="q-type-badge">{{ getTypeLabel(q.type) }}</span>
              <span class="q-points">{{ q.points }}分</span>
              <button class="q-remove" @click="form.questions.splice(qi, 1)" title="移除">✕</button>
            </div>
            <div class="q-content">{{ q.content }}</div>
            <div v-if="q.answer" class="q-answer">答案：{{ q.answer }}</div>
          </div>
          <button class="btn-add-more" @click="showQuestionBank = true">+ 继续选题</button>
        </div>
      </div>

      <!-- Question Bank Dialog -->
      <QuestionBankDialog v-if="showQuestionBank" :user="user" mode="select" @close="showQuestionBank = false" @select="handleSelectFromBank" />

      <p v-if="error" class="error-text">{{ error }}</p>
      <div class="dialog-actions">
        <button class="btn-secondary" @click="$emit('close')">取消</button>
        <button class="btn-primary" @click="handleCreate" :disabled="creating || form.questions.length === 0">
          {{ creating ? '保存中...' : '保存草稿' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../composables/useCourse.js'
import QuestionBankDialog from './QuestionBankDialog.vue'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['close', 'created'])
const route = useRoute()
const { createHomework } = useCourse()

const courseId = route.params.courseId
const creating = ref(false)
const error = ref('')
const showQuestionBank = ref(false)

const form = reactive({
  title: '',
  description: '',
  deadline: '',
  questions: [],
})

const totalPoints = computed(() => form.questions.reduce((s, q) => s + (q.points || 0), 0))

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

function handleSelectFromBank(selectedQuestions) {
  const TYPE_ORDER = { choice: 0, true_false: 1, fill: 2, short_answer: 3, essay: 4 }
  form.questions.push(...selectedQuestions)
  form.questions.sort((a, b) => (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9))
}

async function handleCreate() {
  if (!props.user) { error.value = '未登录'; return }
  if (!form.title.trim()) { error.value = '请输入作业标题'; return }
  if (form.questions.length === 0) { error.value = '请从题库选择题目'; return }

  creating.value = true
  error.value = ''
  try {
    // Prepare questions data
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
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #fff; border: 1.8px solid var(--accent); border-radius: 16px; padding: 32px; width: 560px; max-height: 85vh; overflow-y: auto; box-shadow: 0 0 24px var(--accent-glow); }
.dialog-card-wide { width: 640px; }
.dialog-card h3 { margin: 0 0 20px; font-size: 1.15rem; color: var(--text-primary); }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 8px 12px; background: #fff; border: 1.5px solid var(--border-medium); border-radius: 8px;
  font-size: 0.85rem; outline: none; box-sizing: border-box; font-family: inherit; color: var(--text-primary);
}
.form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

/* Questions */
.questions-section { margin: 20px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-label { font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); }
.question-count { font-size: 0.82rem; color: var(--text-muted); }

.empty-questions { text-align: center; padding: 40px; background: var(--bg-root); border-radius: 12px; border: 2px dashed var(--border-medium); }
.empty-questions p { color: var(--text-muted); margin-bottom: 16px; }
.btn-from-bank { padding: 10px 24px; background: linear-gradient(135deg,var(--accent),var(--accent-deep)); color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px var(--accent-glow); }
.btn-from-bank:hover { opacity: 0.9; }

.question-item { background: var(--bg-root); border: 1px solid var(--border-light); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.q-num { font-weight: 700; color: var(--accent); font-size: 0.85rem; min-width: 20px; }
.q-type-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: var(--accent-soft); color: var(--accent); }
.q-points { font-size: 0.78rem; color: var(--text-muted); }
.q-remove { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem; margin-left: auto; }
.q-remove:hover { color: var(--danger); }
.q-content { font-size: 0.88rem; line-height: 1.5; color: var(--text-primary); }
.q-answer { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; }

.btn-add-more { width: 100%; padding: 10px; background: none; border: 1.5px dashed var(--success); border-radius: 8px; color: var(--success); font-size: 0.85rem; cursor: pointer; margin-top: 10px; }
.btn-add-more:hover { background: var(--success); color: #fff; }

.error-text { color: var(--danger); font-size: 0.8rem; margin-top: 12px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: linear-gradient(135deg,var(--accent),var(--accent-deep)); color: #fff; border: none; border-radius: 10px; font-size: 0.85rem; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px var(--accent-glow); }
.btn-primary:disabled { opacity: 0.5; }
.btn-secondary { padding: 10px 24px; background: var(--bg-root); color: var(--text-primary); border: 1.5px solid var(--border-medium); border-radius: 10px; font-size: 0.85rem; cursor: pointer; }
.btn-secondary:hover { background: var(--accent-soft); border-color: var(--accent); }

.dark .dialog-card { background: #1e1e2e; }
.dark .form-group input, .dark .form-group textarea, .dark .form-group select { background: #252535; }
.dark .empty-questions { background: #1a1a2e; }
.dark .question-item { background: #1a1a2e; }
</style>
