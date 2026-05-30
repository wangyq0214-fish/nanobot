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
            <select v-model="q.type" class="q-type">
              <option value="short_answer">简答题</option>
              <option value="essay">论述题</option>
              <option value="fill">填空题</option>
            </select>
            <input v-model.number="q.points" type="number" min="1" class="q-points" placeholder="分值" />
            <button class="q-remove" @click="form.questions.splice(qi, 1)" title="删除">✕</button>
          </div>
          <textarea v-model="q.content" rows="2" placeholder="题目内容" class="q-content"></textarea>
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
    { type: 'short_answer', content: '', points: 10 },
  ],
})

const totalPoints = computed(() => form.questions.reduce((s, q) => s + (q.points || 0), 0))

function addQuestion() {
  form.questions.push({ type: 'short_answer', content: '', points: 10 })
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
      questions: form.questions.map((q, i) => ({
        id: `q${i + 1}`,
        type: q.type,
        content: q.content.trim(),
        points: q.points || 10,
      })),
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
