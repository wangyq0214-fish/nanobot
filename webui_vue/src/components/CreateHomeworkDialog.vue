<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog-card">
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
        <label class="section-label">题目列表</label>
        <div v-for="(q, qi) in form.questions" :key="qi" class="question-item">
          <div class="q-header">
            <span class="q-num">{{ qi + 1 }}</span>
            <select v-model="q.type" class="q-type" @change="onTypeChange(q)">
              <option value="choice">选择题</option>
              <option value="true_false">判断题</option>
              <option value="fill">填空题</option>
              <option value="short_answer">简答题</option>
              <option value="essay">论述题</option>
            </select>
            <input v-model.number="q.points" type="number" min="1" class="q-points" placeholder="分值" />
            <button class="q-remove" @click="form.questions.splice(qi, 1)" title="删除">✕</button>
          </div>
          <textarea v-model="q.content" rows="2" placeholder="题目内容" class="q-content"></textarea>
          <!-- 选择题选项 -->
          <div v-if="q.type === 'choice'" class="q-options">
            <div v-for="(opt, oi) in q.options" :key="oi" class="option-row">
              <span class="opt-letter">{{ String.fromCharCode(65 + oi) }}.</span>
              <input v-model="q.options[oi]" placeholder="选项内容" class="opt-input" />
              <button class="opt-remove" @click="q.options.splice(oi, 1)">✕</button>
            </div>
            <button class="btn-add-opt" @click="q.options.push('')">+ 添加选项</button>
            <div class="answer-row">
              <label>正确答案:</label>
              <select v-model="q.answer" class="answer-select">
                <option v-for="(opt, oi) in q.options" :key="oi" :value="String.fromCharCode(65 + oi)">{{ String.fromCharCode(65 + oi) }}</option>
              </select>
            </div>
          </div>
          <!-- 判断题答案 -->
          <div v-if="q.type === 'true_false'" class="q-tf-answer">
            <label>正确答案:</label>
            <select v-model="q.answer" class="answer-select">
              <option value="true">正确</option>
              <option value="false">错误</option>
            </select>
          </div>
          <!-- 填空题答案 -->
          <div v-if="q.type === 'fill'" class="q-fill-answer">
            <label>参考答案:</label>
            <input v-model="q.answer" placeholder="正确答案" class="answer-input" />
          </div>
        </div>
        <button class="btn-add-q" @click="addQuestion">+ 添加题目</button>
      </div>

      <div class="total-row">
        <span>总分: {{ totalPoints }} 分</span>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
      <div class="dialog-actions">
        <button class="btn-secondary" @click="$emit('close')">取消</button>
        <button class="btn-primary" @click="handleCreate" :disabled="creating">
          {{ creating ? '发布中...' : '发布作业' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../composables/useCourse.js'
import { useGateway } from '../composables/useGateway.js'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['close', 'created'])
const route = useRoute()
const { createHomework } = useCourse()
const { getToken } = useGateway()

const courseId = route.params.courseId
const creating = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  description: '',
  deadline: '',
  questions: [
    { type: 'short_answer', content: '', points: 10, options: [], answer: '' },
  ],
})

const totalPoints = computed(() => form.questions.reduce((s, q) => s + (q.points || 0), 0))

function addQuestion() {
  form.questions.push({ type: 'short_answer', content: '', points: 10, options: [], answer: '' })
}

function onTypeChange(q) {
  if (q.type === 'choice') {
    q.options = ['', '']
    q.answer = 'A'
  } else if (q.type === 'true_false') {
    q.options = []
    q.answer = 'true'
  } else if (q.type === 'fill') {
    q.options = []
    q.answer = ''
  } else {
    q.options = []
    q.answer = ''
  }
}

async function handleCreate() {
  if (!props.user) { error.value = '未登录'; return }
  if (!form.title.trim()) { error.value = '请输入作业标题'; return }
  if (form.questions.length === 0) { error.value = '请添加至少一道题目'; return }
  const empty = form.questions.find(q => !q.content.trim())
  if (empty) { error.value = '请填写所有题目内容'; return }
  creating.value = true
  error.value = ''
  try {
    const token = getToken()
    console.log('[createHomework] user=', props.user, 'token=', token ? 'yes' : 'no')
    await createHomework(courseId, {
      title: form.title.trim(),
      description: form.description.trim(),
      deadline: form.deadline ? new Date(form.deadline).toISOString() : '',
      questions: form.questions.map((q, i) => {
        const base = {
          id: `q${i + 1}`,
          type: q.type,
          content: q.content.trim(),
          points: q.points || 10,
        }
        // Add options for choice questions
        if (q.type === 'choice' && q.options) {
          base.options = q.options.filter(o => o.trim()).map((o, idx) => ({
            key: String.fromCharCode(65 + idx),
            text: o.trim(),
          }))
          base.answer = q.answer || 'A'
        }
        // Add answer for true/false
        if (q.type === 'true_false') {
          base.answer = q.answer || 'true'
        }
        // Add answer for fill
        if (q.type === 'fill') {
          base.answer = q.answer || ''
        }
        return base
      }),
      totalPoints: totalPoints.value,
    }, props.user.role, props.user.userId, token)
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
.dialog-card h3 { margin: 0 0 20px; font-size: 1.15rem; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: #555; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 8px 12px; border: 1.5px solid #e0dcd5; border-radius: 8px;
  font-size: 0.85rem; outline: none; box-sizing: border-box; font-family: inherit;
}
.form-group input:focus, .form-group textarea:focus { border-color: #5b8def; }
.section-label { display: block; font-size: 0.82rem; font-weight: 600; color: #555; margin-bottom: 10px; }

/* Questions */
.questions-section { margin: 16px 0; }
.question-item { background: #faf8f5; border: 1px solid #e8e4db; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.q-num { font-weight: 700; color: #5b8def; font-size: 0.85rem; min-width: 20px; }
.q-type { width: auto; padding: 4px 8px; font-size: 0.78rem; border-radius: 6px; border: 1px solid #e0dcd5; }
.q-points { width: 60px !important; padding: 4px 8px !important; font-size: 0.78rem; text-align: center; }
.q-remove { background: none; border: none; color: #ccc; cursor: pointer; font-size: 0.9rem; margin-left: auto; }
.q-remove:hover { color: #e74c3c; }
.q-content { width: 100%; padding: 8px; border: 1px solid #e0dcd5; border-radius: 6px; font-size: 0.85rem; resize: vertical; box-sizing: border-box; font-family: inherit; }
.btn-add-q { background: none; border: 1.5px dashed #ccc; border-radius: 8px; padding: 10px; width: 100%; cursor: pointer; font-size: 0.82rem; color: #888; }
.btn-add-q:hover { border-color: #5b8def; color: #5b8def; }

/* Question type specific styles */
.q-options { margin-top: 8px; padding: 8px; background: #fff; border-radius: 6px; border: 1px solid #e8e4db; }
.option-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.opt-letter { font-weight: 600; color: #5b8def; min-width: 20px; }
.opt-input { flex: 1; padding: 6px 8px; border: 1px solid #e0dcd5; border-radius: 4px; font-size: 0.82rem; }
.opt-remove { background: none; border: none; color: #ccc; cursor: pointer; font-size: 0.8rem; }
.opt-remove:hover { color: #e74c3c; }
.btn-add-opt { background: none; border: 1px dashed #ccc; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 0.78rem; color: #888; margin-top: 4px; }
.btn-add-opt:hover { border-color: #5b8def; color: #5b8def; }
.answer-row { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.answer-row label { font-size: 0.82rem; color: #555; }
.answer-select { padding: 4px 8px; border: 1px solid #e0dcd5; border-radius: 4px; font-size: 0.82rem; }
.q-tf-answer, .q-fill-answer { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.q-tf-answer label, .q-fill-answer label { font-size: 0.82rem; color: #555; }
.answer-input { flex: 1; padding: 6px 8px; border: 1px solid #e0dcd5; border-radius: 4px; font-size: 0.82rem; }

.total-row { text-align: right; font-size: 0.85rem; font-weight: 600; color: #555; margin: 8px 0; }
.error-text { color: #e74c3c; font-size: 0.8rem; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 8px 20px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; }
.btn-secondary { padding: 8px 20px; background: #f0ede8; color: #555; border: none; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }

:global(body.dark) .dialog-card { background: #1e1e2e; }
:global(body.dark) .dialog-card h3, :global(body.dark) .section-label { color: #e0e0e0; }
:global(body.dark) .form-group input, :global(body.dark) .form-group textarea,
:global(body.dark) .form-group select, :global(body.dark) .q-content, :global(body.dark) .q-type { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .question-item { background: #252535; border-color: #333; }
:global(body.dark) .total-row { color: #ccc; }
</style>
