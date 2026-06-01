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
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #fff; border-radius: 16px; padding: 32px; width: 560px; max-height: 85vh; overflow-y: auto; }
.dialog-card-wide { width: 640px; }
.dialog-card h3 { margin: 0 0 20px; font-size: 1.15rem; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: #555; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 8px 12px; border: 1.5px solid #e0dcd5; border-radius: 8px;
  font-size: 0.85rem; outline: none; box-sizing: border-box; font-family: inherit;
}
.form-group input:focus, .form-group textarea:focus { border-color: #5b8def; }

/* Questions */
.questions-section { margin: 20px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-label { font-size: 0.82rem; font-weight: 600; color: #555; }
.question-count { font-size: 0.82rem; color: #888; }

.empty-questions { text-align: center; padding: 40px; background: #f8f6f1; border-radius: 12px; border: 2px dashed #e0dcd5; }
.empty-questions p { color: #888; margin-bottom: 16px; }
.btn-from-bank { padding: 10px 24px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
.btn-from-bank:hover { background: #4a7de0; }

.question-item { background: #faf8f5; border: 1px solid #e8e4db; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.q-num { font-weight: 700; color: #5b8def; font-size: 0.85rem; min-width: 20px; }
.q-type-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: #eef4ff; color: #5b8def; }
.q-points { font-size: 0.78rem; color: #888; }
.q-remove { background: none; border: none; color: #ccc; cursor: pointer; font-size: 0.9rem; margin-left: auto; }
.q-remove:hover { color: #e74c3c; }
.q-content { font-size: 0.88rem; line-height: 1.5; }
.q-answer { font-size: 0.78rem; color: #666; margin-top: 4px; }

.btn-add-more { width: 100%; padding: 10px; background: none; border: 1.5px dashed #27ae60; border-radius: 8px; color: #27ae60; font-size: 0.85rem; cursor: pointer; margin-top: 10px; }
.btn-add-more:hover { background: #27ae60; color: #fff; }

.error-text { color: #e74c3c; font-size: 0.8rem; margin-top: 12px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 8px 20px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; }
.btn-secondary { padding: 8px 20px; background: #f0ede8; color: #555; border: none; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }

:global(body.dark) .dialog-card { background: #1e1e2e; }
:global(body.dark) .dialog-card h3, :global(body.dark) .section-label { color: #e0e0e0; }
:global(body.dark) .form-group input, :global(body.dark) .form-group textarea { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .empty-questions { background: #252535; border-color: #444; }
:global(body.dark) .question-item { background: #252535; border-color: #333; }
:global(body.dark) .q-content { color: #e0e0e0; }
:global(body.dark) .q-answer { color: #aaa; }
</style>
