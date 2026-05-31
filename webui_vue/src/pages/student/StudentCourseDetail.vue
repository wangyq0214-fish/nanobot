<template>
  <div class="app">
    <StudentNav active-tab="courses" />

    <div class="main-content">
      <!-- Back + Header -->
      <button class="back-btn" @click="router.push('/student/courses')">← 返回课程列表</button>
      <div v-if="course" class="course-header">
        <h2>{{ course.courseName }}</h2>
        <div class="course-tags">
          <span class="tag">{{ course.subject }}</span>
          <span class="tag">{{ course.grade }}</span>
          <span class="tag teacher-tag">{{ course.teacherName }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tab-bar">
        <span class="tab-item" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">课时</span>
        <span class="tab-item" :class="{ active: activeTab === 'homework' }" @click="activeTab = 'homework'">作业</span>
      </div>

      <!-- Tab: Lessons -->
      <div v-if="activeTab === 'lessons'" class="tab-content">
        <div v-if="lessons.length === 0" class="empty-hint">暂无课时</div>
        <div v-for="l in lessons" :key="l.lessonId" class="lesson-card">
          <div class="lesson-header" @click="toggleLesson(l.lessonId)">
            <span class="lesson-order">#{{ l.order || '?' }}</span>
            <span class="lesson-title">{{ l.title }}</span>
            <span class="lesson-toggle">{{ expandedLesson === l.lessonId ? '▲' : '▼' }}</span>
          </div>
          <div v-if="expandedLesson === l.lessonId" class="lesson-body">
            <p v-if="l.description" class="lesson-desc">{{ l.description }}</p>
            <div v-if="lessonPlans[l.lessonId]" class="plan-content" v-html="renderMd(lessonPlans[l.lessonId])"></div>
            <div v-else class="loading-hint">加载中...</div>
          </div>
        </div>
      </div>

      <!-- Tab: Homework -->
      <div v-if="activeTab === 'homework'" class="tab-content">
        <div v-if="homeworkList.length === 0" class="empty-hint">暂无作业</div>
        <div v-for="hw in homeworkList" :key="hw.hwId" class="hw-card">
          <div class="hw-header" @click="toggleHomework(hw.hwId)">
            <div class="hw-title-row">
              <span class="hw-title">{{ hw.title }}</span>
              <span class="hw-status" :class="getHwStatus(hw.hwId)">
                {{ getHwStatusLabel(hw.hwId) }}
              </span>
            </div>
            <div class="hw-meta">
              <span v-if="hw.deadline">截止: {{ formatDate(hw.deadline) }}</span>
              <span>{{ hw.questions?.length || 0 }} 题 · {{ hw.totalPoints }} 分</span>
            </div>
          </div>

          <!-- Expanded: questions + submit -->
          <div v-if="expandedHw === hw.hwId" class="hw-body">
            <div v-if="getHwStatus(hw.hwId) === 'graded'" class="graded-result">
              <div class="score-display">
                <span class="score-num">{{ getSubmission(hw.hwId)?.score || 0 }}</span>
                <span class="score-total">/ {{ hw.totalPoints }}</span>
              </div>
            </div>

            <div v-for="(q, qi) in hw.questions" :key="q.id" class="hw-question">
              <p class="q-label">{{ qi + 1 }}. {{ q.content }} <span class="q-points">({{ q.points }}分)</span></p>
              <span v-if="q.type === 'choice'" class="q-type-badge">选择题</span>
              <span v-else-if="q.type === 'true_false'" class="q-type-badge">判断题</span>
              <span v-else-if="q.type === 'fill'" class="q-type-badge">填空题</span>
              <span v-else-if="q.type === 'short_answer'" class="q-type-badge">简答题</span>
              <span v-else-if="q.type === 'essay'" class="q-type-badge">论述题</span>

              <div v-if="getHwStatus(hw.hwId) === 'graded'" class="graded-answer">
                <p class="answer-label">我的答案:</p>
                <p class="answer-text">{{ getSubmission(hw.hwId)?.answers?.[q.id] || '未作答' }}</p>
                <p v-if="getSubmission(hw.hwId)?.feedback?.[q.id]" class="feedback-text">
                  评语: {{ getSubmission(hw.hwId).feedback[q.id] }}
                </p>
              </div>

              <!-- 选择题 -->
              <div v-else-if="q.type === 'choice'" class="choice-options">
                <label v-for="opt in q.options" :key="opt.key" class="choice-option" :class="{ selected: answers[hw.hwId][q.id] === opt.key }">
                  <input type="radio" :name="`${hw.hwId}-${q.id}`" :value="opt.key" v-model="answers[hw.hwId][q.id]" />
                  <span class="opt-key">{{ opt.key }}.</span>
                  <span class="opt-text">{{ opt.text }}</span>
                </label>
              </div>

              <!-- 判断题 -->
              <div v-else-if="q.type === 'true_false'" class="tf-options">
                <label class="tf-option" :class="{ selected: answers[hw.hwId][q.id] === 'true' }">
                  <input type="radio" :name="`${hw.hwId}-${q.id}`" value="true" v-model="answers[hw.hwId][q.id]" />
                  <span>✓ 正确</span>
                </label>
                <label class="tf-option" :class="{ selected: answers[hw.hwId][q.id] === 'false' }">
                  <input type="radio" :name="`${hw.hwId}-${q.id}`" value="false" v-model="answers[hw.hwId][q.id]" />
                  <span>✕ 错误</span>
                </label>
              </div>

              <!-- 填空题/简答题/论述题 -->
              <textarea v-else v-model="answers[hw.hwId][q.id]" :rows="q.type === 'essay' ? 5 : 3" :placeholder="q.type === 'fill' ? '填写答案...' : '输入你的答案...'" class="answer-input"></textarea>
            </div>

            <div v-if="getHwStatus(hw.hwId) !== 'graded'" class="hw-actions">
              <button class="btn-primary" @click="handleSubmit(hw)" :disabled="submitting === hw.hwId">
                {{ submitting === hw.hwId ? '提交中...' : '提交作业' }}
              </button>
              <p v-if="submitError[hw.hwId]" class="error-text">{{ submitError[hw.hwId] }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const route = useRoute()
const { user, logout: authLogout } = useAuth()
const {
  currentCourse: course, lessons, homeworkList,
  fetchCourseDetail, fetchLessons, fetchHomeworkList,
  fetchLessonDetail, submitHomework, fetchSubmissions,
} = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

const courseId = route.params.courseId
const activeTab = ref('lessons')
const isDark = ref(false)
const expandedLesson = ref(null)
const expandedHw = ref(null)
const lessonPlans = reactive({})
const answers = reactive({})
const submissions = reactive({}) // hwId -> submission
const submitting = ref(null)
const submitError = reactive({})

function toggleTheme() { isDark.value = !isDark.value; document.body.classList.toggle('dark', isDark.value) }
function handleLogout() { authLogout(); router.push('/login') }

function renderMd(text) { return marked.parse(text || '') }
function formatDate(d) { if (!d) return '-'; return new Date(d).toLocaleDateString('zh-CN') }

async function loadAll() {
  const t = getToken()
  await Promise.all([
    fetchCourseDetail(courseId, t),
    fetchLessons(courseId, t),
    fetchHomeworkList(courseId, t),
  ])
  // Init answer slots
  for (const hw of homeworkList.value) {
    if (!answers[hw.hwId]) {
      answers[hw.hwId] = {}
      for (const q of hw.questions || []) {
        answers[hw.hwId][q.id] = ''
      }
    }
    // Load submission status
    try {
      const subs = await fetchSubmissions(courseId, hw.hwId, t)
      const mySub = subs.find(s => s.studentId === user.value?.userId)
      if (mySub) submissions[hw.hwId] = mySub
    } catch { /* no submissions */ }
  }
}

async function toggleLesson(lessonId) {
  if (expandedLesson.value === lessonId) { expandedLesson.value = null; return }
  expandedLesson.value = lessonId
  if (!lessonPlans[lessonId]) {
    try {
      const detail = await fetchLessonDetail(courseId, lessonId, getToken())
      lessonPlans[lessonId] = detail?.planContent || ''
    } catch { lessonPlans[lessonId] = '(加载失败)' }
  }
}

function toggleHomework(hwId) {
  expandedHw.value = expandedHw.value === hwId ? null : hwId
}

function getHwStatus(hwId) {
  const sub = submissions[hwId]
  if (!sub) return 'pending'
  return sub.status
}

function getHwStatusLabel(hwId) {
  const status = getHwStatus(hwId)
  if (status === 'graded') return `已批改 (${submissions[hwId].score}分)`
  if (status === 'submitted') return '已提交'
  return '未提交'
}

function getSubmission(hwId) { return submissions[hwId] }

async function handleSubmit(hw) {
  const hwAnswers = answers[hw.hwId] || {}
  // Check at least one answer
  const hasAnswer = Object.values(hwAnswers).some(v => v.trim())
  if (!hasAnswer) { submitError[hw.hwId] = '请至少回答一道题'; return }
  submitting.value = hw.hwId
  submitError[hw.hwId] = ''
  try {
    await submitHomework(courseId, hw.hwId, hwAnswers, user.value.role, user.value.userId, getToken())
    // Reload submission
    const subs = await fetchSubmissions(courseId, hw.hwId, getToken())
    const mySub = subs.find(s => s.studentId === user.value?.userId)
    if (mySub) submissions[hw.hwId] = mySub
  } catch (e) {
    submitError[hw.hwId] = e.message
  } finally {
    submitting.value = null
  }
}

onMounted(async () => {
  if (!user.value) { router.push('/login'); return }
  if (!connected.value) {
    try { await connectGateway({ role: user.value.role, userId: user.value.userId }) } catch {}
  }
  await loadAll()
})
</script>

<style scoped>
.app { display: flex; flex-direction: column; height: 100vh; background: var(--bg, #f8f6f1); }

/* Nav (same as StudentCourses) */
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 52px; background: #fff; border-bottom: 1px solid #e8e4db; flex-shrink: 0; }
.nav-left { display: flex; align-items: center; }
.nav-logo { font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; background: #5b8def; border-radius: 50%; display: inline-block; }
.nav-center { display: flex; gap: 4px; }
.nav-tab { padding: 6px 16px; font-size: 0.82rem; font-weight: 600; color: #888; cursor: pointer; border-radius: 6px; transition: all 0.2s; }
.nav-tab:hover { background: #f0ede8; }
.nav-tab.active { color: #5b8def; background: #eef4ff; }
.nav-right { display: flex; align-items: center; gap: 8px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; color: #666; display: flex; align-items: center; }
.icon-btn:hover { background: #f0ede8; }
.icon-btn svg { width: 18px; height: 18px; }
.nav-avatar { width: 30px; height: 30px; border-radius: 50%; background: #5b8def; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; }

/* Main */
.main-content { flex: 1; overflow-y: auto; padding: 24px 32px; width: 100%; box-sizing: border-box; }

/* Header */
.back-btn { background: none; border: none; color: #5b8def; font-size: 0.85rem; cursor: pointer; margin-bottom: 16px; padding: 0; }
.course-header { margin-bottom: 20px; }
.course-header h2 { margin: 0 0 8px; font-size: 1.3rem; }
.course-tags { display: flex; gap: 8px; }
.tag { background: #eef4ff; color: #5b8def; font-size: 0.72rem; font-weight: 600; padding: 2px 10px; border-radius: 4px; }
.teacher-tag { background: #f0f8e8; color: #4caf50; }

/* Tabs */
.tab-bar { display: flex; gap: 0; border-bottom: 2px solid #e8e4db; margin-bottom: 20px; }
.tab-item { padding: 10px 20px; font-size: 0.88rem; font-weight: 600; color: #888; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
.tab-item.active { color: #5b8def; border-bottom-color: #5b8def; }

/* Lessons (same as teacher CourseDetail) */
.lesson-card { background: #fff; border: 1px solid #e8e4db; border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
.lesson-header { display: flex; align-items: center; padding: 14px 18px; cursor: pointer; gap: 10px; }
.lesson-header:hover { background: #faf8f5; }
.lesson-order { font-size: 0.8rem; color: #5b8def; font-weight: 700; min-width: 30px; }
.lesson-title { flex: 1; font-weight: 600; font-size: 0.92rem; }
.lesson-toggle { font-size: 0.7rem; color: #999; }
.lesson-body { padding: 0 18px 16px; border-top: 1px solid #f0ede8; }
.lesson-desc { color: #666; font-size: 0.82rem; margin: 10px 0; }
.plan-content { font-size: 0.85rem; line-height: 1.7; }
.plan-content :deep(table) { border-collapse: collapse; margin: 8px 0; }
.plan-content :deep(th), .plan-content :deep(td) { border: 1px solid #e0dcd5; padding: 6px 10px; font-size: 0.82rem; }

/* Homework */
.hw-card { background: #fff; border: 1px solid #e8e4db; border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
.hw-header { padding: 14px 18px; cursor: pointer; }
.hw-header:hover { background: #faf8f5; }
.hw-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.hw-title { font-weight: 600; font-size: 0.92rem; }
.hw-status { font-size: 0.75rem; padding: 2px 10px; border-radius: 4px; }
.hw-status.pending { background: #f5f5f5; color: #999; }
.hw-status.submitted { background: #fff3e0; color: #e67e22; }
.hw-status.graded { background: #e8f5e9; color: #2e7d32; }
.hw-meta { display: flex; gap: 16px; font-size: 0.78rem; color: #888; }
.hw-body { padding: 0 18px 16px; border-top: 1px solid #f0ede8; }

/* Graded result */
.graded-result { text-align: center; padding: 16px 0; }
.score-display { display: flex; align-items: baseline; justify-content: center; gap: 4px; }
.score-num { font-size: 2.2rem; font-weight: 700; color: #2e7d32; }
.score-total { font-size: 1rem; color: #888; }

/* Questions */
.hw-question { margin: 12px 0; }
.q-label { font-size: 0.88rem; font-weight: 500; margin: 0 0 8px; }
.q-points { font-size: 0.75rem; color: #999; }
.q-type-badge { display: inline-block; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; background: #e8f4fd; color: #5b8def; margin-bottom: 8px; }
.answer-input { width: 100%; padding: 10px; border: 1.5px solid #e0dcd5; border-radius: 8px; font-size: 0.85rem; outline: none; resize: vertical; box-sizing: border-box; font-family: inherit; }
.answer-input:focus { border-color: #5b8def; }

/* Choice options */
.choice-options { display: flex; flex-direction: column; gap: 8px; }
.choice-option { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1.5px solid #e0dcd5; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.choice-option:hover { border-color: #5b8def; background: #f8f9ff; }
.choice-option.selected { border-color: #5b8def; background: #e8f4fd; }
.choice-option input[type="radio"] { display: none; }
.opt-key { font-weight: 600; color: #5b8def; min-width: 20px; }
.opt-text { font-size: 0.88rem; }

/* True/False options */
.tf-options { display: flex; gap: 12px; }
.tf-option { display: flex; align-items: center; gap: 8px; padding: 10px 20px; border: 1.5px solid #e0dcd5; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.tf-option:hover { border-color: #5b8def; background: #f8f9ff; }
.tf-option.selected { border-color: #5b8def; background: #e8f4fd; }
.tf-option input[type="radio"] { display: none; }

.graded-answer { background: #faf8f5; padding: 10px; border-radius: 8px; margin-top: 6px; }
.answer-label { font-size: 0.78rem; color: #888; margin: 0 0 4px; }
.answer-text { font-size: 0.85rem; margin: 0 0 6px; color: #333; }
.feedback-text { font-size: 0.82rem; color: #5b8def; margin: 0; font-style: italic; }

.hw-actions { margin-top: 16px; text-align: right; }
.error-text { color: #e74c3c; font-size: 0.8rem; margin-top: 8px; }
.btn-primary { padding: 10px 24px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; }
.empty-hint { text-align: center; padding: 30px; color: #999; font-size: 0.85rem; }

/* Dark */
:global(body.dark) .app { background: #12121a; }
:global(body.dark) .top-nav { background: #1e1e2e; border-color: #333; }
:global(body.dark) .lesson-card, :global(body.dark) .hw-card { background: #1e1e2e; border-color: #333; }
:global(body.dark) .lesson-header:hover, :global(body.dark) .hw-header:hover { background: #252535; }
:global(body.dark) .course-header h2, :global(body.dark) .hw-title { color: #e0e0e0; }
:global(body.dark) .answer-input { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .graded-answer { background: #252535; }
:global(body.dark) .answer-text { color: #ccc; }
:global(body.dark) .nav-tab.active { background: #252535; }
</style>
