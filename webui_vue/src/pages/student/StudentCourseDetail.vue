<template>
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
        <span class="tab-item" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">学习章节</span>
        <span class="tab-item" :class="{ active: activeTab === 'homework' }" @click="activeTab = 'homework'">作业</span>
        <span class="tab-item" :class="{ active: activeTab === 'exams' }" @click="activeTab = 'exams'">考试</span>
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
          <div class="hw-header" @click="handleHomeworkClick(hw)">
            <div class="hw-title-row">
              <span class="hw-title">{{ hw.title }}</span>
              <span class="hw-status" :class="getHwStatus(hw.hwId)">
                {{ getHwStatusLabel(hw.hwId) }}
              </span>
            </div>
            <div class="hw-meta">
              <span v-if="hw.deadline">截止时间: {{ formatDate(hw.deadline) }}</span>
              <span v-if="hw.deadline">•</span>
              <span>{{ hw.questions?.length || 0 }} 题</span>
              <span>•</span>
              <span>{{ hw.totalPoints }} 分</span>
            </div>
          </div>

          <!-- Expanded: questions + submit (only for graded) -->
          <div v-if="getHwStatus(hw.hwId) === 'graded' && expandedHw === hw.hwId" class="hw-body">
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

            <div v-if="getHwStatus(hw.hwId) === 'pending'" class="hw-actions">
              <button class="btn-primary" @click="handleSubmit(hw)" :disabled="submitting === hw.hwId">
                {{ submitting === hw.hwId ? '提交中...' : '提交作业' }}
              </button>
              <p v-if="submitError[hw.hwId]" class="error-text">{{ submitError[hw.hwId] }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: 考试 -->
      <div v-if="activeTab === 'exams'" class="tab-content">
        <div v-if="examList.length === 0" class="empty-hint">暂无考试</div>
        <div v-for="e in examList" :key="e.id" class="exam-card">
          <div class="exam-info">
            <div class="exam-title-row">
              <span class="exam-title">{{ e.title }}</span>
              <span class="exam-status" :class="e.status">
                {{ e.status === 'ongoing' ? '进行中' : e.status === 'submitted' ? '已交卷' : e.status === 'ended' ? '已结束' : '未开始' }}
              </span>
            </div>
            <div class="exam-meta">
              <span>时长: {{ e.duration }}分钟</span>
              <span>·</span>
              <span>开始: {{ e.startTime }}</span>
              <span>·</span>
              <span>总分: {{ e.totalPoints }}分</span>
            </div>
          </div>
          <div class="exam-actions">
            <button v-if="e.status === 'ongoing'" class="btn-primary btn-sm">进入考试</button>
            <span v-else-if="e.status === 'submitted'" class="exam-score">{{ e.score }}分</span>
            <span v-else-if="e.status === 'upcoming'" class="exam-countdown">待开始</span>
            <span v-else class="exam-ended-text">已结束</span>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup>
// 完全保持原样，无需修改
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'

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
const submissions = ref({})
const submitting = ref(null)
const submitError = reactive({})

const examList = ref([
  { id: 1, title: '植物病理学期中考试', duration: 60, startTime: '7月30日 14:00', totalPoints: 100, status: 'upcoming', score: null },
  { id: 2, title: '植保基础单元测验', duration: 30, startTime: '7月25日 10:00', totalPoints: 50, status: 'ended', score: 42 },
])

function toggleTheme() { isDark.value = !isDark.value; document.body.classList.toggle('dark', isDark.value) }
function handleLogout() { authLogout(); router.push('/login') }

function renderMd(text) { return marked.parse(text || '') }
function formatDate(d) { if (!d) return '-'; return new Date(d).toLocaleDateString('zh-CN') }

async function loadAll() {
  await Promise.all([
    fetchCourseDetail(courseId),
    fetchLessons(courseId),
    fetchHomeworkList(courseId),
  ])
  for (const hw of homeworkList.value) {
    if (!answers[hw.hwId]) {
      answers[hw.hwId] = {}
      for (const q of hw.questions || []) {
        answers[hw.hwId][q.id] = ''
      }
    }
    try {
      const subs = await fetchSubmissions(courseId, hw.hwId, t)
      const mySub = subs.find(s => s.studentId === user.value?.userId)
      if (mySub) {
        submissions.value[hw.hwId] = mySub
      }
    } catch {}
  }
}

async function toggleLesson(lessonId) {
  if (expandedLesson.value === lessonId) { expandedLesson.value = null; return }
  expandedLesson.value = lessonId
  if (!lessonPlans[lessonId]) {
    try {
      const detail = await fetchLessonDetail(courseId, lessonId)
      lessonPlans[lessonId] = detail?.planContent || ''
    } catch { lessonPlans[lessonId] = '(加载失败)' }
  }
}

function toggleHomework(hwId) {
  expandedHw.value = expandedHw.value === hwId ? null : hwId
}

function handleHomeworkClick(hw) {
  const status = getHwStatus(hw.hwId)
  if (status === 'graded') {
    // 已批改：展开显示结果
    toggleHomework(hw.hwId)
  } else {
    // 未提交或已提交未批改：跳转到答题页面
    router.push(`/student/courses/${courseId}/homework/${hw.hwId}`)
  }
}

function getHwStatus(hwId) {
  const sub = submissions.value[hwId]
  if (!sub) return 'pending'
  return sub.status
}

function getHwStatusLabel(hwId) {
  const status = getHwStatus(hwId)
  if (status === 'graded') return `已批改 (${submissions.value[hwId].score ?? 0}分)`
  if (status === 'submitted') return '已提交'
  return '未提交'
}

function getSubmission(hwId) { return submissions.value[hwId] }

async function handleSubmit(hw) {
  const hwAnswers = answers[hw.hwId] || {}
  const hasAnswer = Object.values(hwAnswers).some(v => v.trim())
  if (!hasAnswer) { submitError[hw.hwId] = '请至少回答一道题'; return }
  submitting.value = hw.hwId
  submitError[hw.hwId] = ''
  try {
    await submitHomework(courseId, hw.hwId, hwAnswers)
    const subs = await fetchSubmissions(courseId, hw.hwId)
    const mySub = subs.find(s => s.studentId === user.value?.userId)
    if (mySub) submissions.value[hw.hwId] = mySub
  } catch (e) {
    submitError[hw.hwId] = e.message
  } finally {
    submitting.value = null
  }
}

onMounted(async () => {
  if (!user.value) { router.push('/login'); return }
  await loadAll()
})
</script>

<style>
:root {
  --bg-root: #ffffff;
  --bg-card: #ffffff;
  --bg-subtle: #f8f9f8;
  --accent: #121212;
  --accent-deep: #121212;
  --accent-soft: rgba(18,18,18,0.04);
  --border-light: #f0f0f0;
  --border-medium: #eaeaea;
  --border-hover: #121212;
  --text-primary: #121212;
  --text-secondary: #4a534c;
  --text-muted: #9ca3af;
  --divider: #f0f0f0;
  --danger: #ef4444;
  --success: #0d9488;
  --warning: #cda052;
  --tag-warn-bg: #fbf7ee;
  --tag-warn-text: #cda052;
  --tag-warn-border: #f5ebd3;
  --serif: 'Noto Serif SC', 'PingFang SC', serif;
}
body.dark {
  --bg-root: #0a0a0a;
  --bg-card: #141414;
  --bg-subtle: #1a1a1a;
  --accent: #e0e0e0;
  --accent-deep: #ffffff;
  --accent-soft: rgba(255,255,255,0.05);
  --border-light: #222;
  --border-medium: #2a2a2a;
  --border-hover: #e0e0e0;
  --text-primary: #e5e5e5;
  --text-secondary: #a0a0a0;
  --text-muted: #666;
  --divider: #222;
  --danger: #f87171;
  --success: #34d399;
  --warning: #d4a853;
  --tag-warn-bg: rgba(205,160,82,0.1);
  --tag-warn-text: #d4a853;
  --tag-warn-border: rgba(205,160,82,0.2);
}
</style>

<style scoped>
/* ========== 布局 ========== */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 36px;
  background: var(--bg-card);
  border-radius: 20px;
  margin: 6px 10px;
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: var(--border-light) transparent;
}
.main-content::-webkit-scrollbar { width: 4px; }
.main-content::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 2px; }

/* ========== 返回按钮 ========== */
.back-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.78rem;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 4px 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}
.back-btn:hover { color: var(--text-primary); }

/* ========== 课程头部 ========== */
.course-header {
  margin-bottom: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.002);
}
.course-header h2 {
  margin: 0 0 10px;
  font-family: var(--serif);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.03em;
}
.course-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag {
  background: var(--bg-subtle);
  color: var(--text-primary);
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}
.teacher-tag {
  background: var(--tag-warn-bg);
  color: var(--tag-warn-text);
  border: 1px solid var(--tag-warn-border);
}

/* ========== 标签栏 ========== */
.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--divider);
  margin-bottom: 20px;
}
.tab-item {
  padding: 8px 18px;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
}
.tab-item:hover { color: var(--text-primary); }
.tab-item.active {
  color: var(--text-primary);
  font-weight: 600;
  border-bottom-color: var(--text-primary);
}

/* ========== 课时卡片 ========== */
.lesson-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color 0.3s;
}
.lesson-card:hover {
  border-color: var(--border-hover);
}
.lesson-header {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  cursor: pointer;
  gap: 10px;
}
.lesson-header:hover { background: var(--accent-soft); }
.lesson-order {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
  min-width: 30px;
}
.lesson-title {
  flex: 1;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--text-primary);
}
.lesson-toggle {
  font-size: 0.65rem;
  color: var(--text-muted);
}
.lesson-body {
  padding: 0 18px 16px;
  border-top: 1px solid var(--divider);
}
.lesson-desc {
  color: var(--text-secondary);
  font-size: 0.78rem;
  margin: 10px 0;
}
.plan-content {
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--text-primary);
}

/* ========== 作业卡片 ========== */
.hw-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color 0.3s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.002);
}
.hw-card:hover {
  border-color: var(--border-hover);
}
.hw-header {
  padding: 14px 18px;
  cursor: pointer;
}
.hw-header:hover { background: var(--accent-soft); }
.hw-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.hw-title {
  font-weight: 700;
  font-size: 0.82rem;
  color: var(--text-primary);
}
.hw-status {
  font-size: 0.65rem;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
}
.hw-status.pending {
  background: var(--tag-warn-bg);
  color: var(--tag-warn-text);
  border: 1px solid var(--tag-warn-border);
}
.hw-status.submitted {
  background: var(--tag-warn-bg);
  color: var(--tag-warn-text);
  border: 1px solid var(--tag-warn-border);
}
.hw-status.graded {
  background: rgba(13, 148, 136, 0.08);
  color: var(--success);
}
.hw-meta {
  display: flex;
  gap: 12px;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: monospace;
}
.hw-body {
  padding: 0 18px 16px;
  border-top: 1px solid var(--divider);
}

/* 已批改结果 */
.graded-result {
  text-align: center;
  padding: 16px 0;
}
.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}
.score-num {
  font-family: var(--serif);
  font-size: 2.2rem;
  font-weight: 600;
  color: var(--text-primary);
}
.score-total {
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* 题目 */
.hw-question {
  margin: 12px 0;
}
.q-label {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.q-points {
  font-size: 0.7rem;
  color: var(--text-muted);
}
.q-type-badge {
  display: inline-block;
  font-size: 0.65rem;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--bg-subtle);
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-weight: 600;
}
.answer-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-size: 0.82rem;
  outline: none;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
  color: var(--text-primary);
  transition: border 0.2s;
}
.answer-input:focus {
  border-color: var(--border-hover);
}

/* 选择题 */
.choice-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.choice-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
}
.choice-option:hover {
  border-color: var(--border-hover);
  background: var(--accent-soft);
}
.choice-option.selected {
  border-color: var(--border-hover);
  background: var(--accent-soft);
  color: var(--text-primary);
}
.choice-option input[type="radio"] { display: none; }
.opt-key {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 20px;
}
.opt-text { font-size: 0.82rem; }

/* 判断题 */
.tf-options {
  display: flex;
  gap: 10px;
}
.tf-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
}
.tf-option:hover {
  border-color: var(--border-hover);
  background: var(--accent-soft);
}
.tf-option.selected {
  border-color: var(--border-hover);
  background: var(--accent-soft);
  color: var(--text-primary);
}
.tf-option input[type="radio"] { display: none; }

/* 已批改答案 */
.graded-answer {
  background: var(--bg-subtle);
  padding: 12px;
  border-radius: 8px;
  margin-top: 6px;
  border: 1px solid var(--border-light);
}
.answer-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 0 0 4px;
}
.answer-text {
  font-size: 0.82rem;
  margin: 0 0 6px;
  color: var(--text-primary);
}
.feedback-text {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin: 0;
  font-style: italic;
  font-weight: 500;
}

/* 操作区 */
.hw-actions {
  margin-top: 16px;
  text-align: right;
}
.error-text {
  color: var(--danger);
  font-size: 0.78rem;
  margin-top: 8px;
}

/* 按钮 */
.btn-primary {
  padding: 10px 24px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-primary:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.btn-primary:not(:disabled):hover {
  background: var(--accent-deep);
}

/* ========== 考试卡片 ========== */
.exam-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 10px;
  transition: border-color 0.3s;
}
.exam-card:hover { border-color: var(--border-hover); }
.exam-info { flex: 1; min-width: 0; }
.exam-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.exam-title { font-weight: 700; font-size: 0.82rem; color: var(--text-primary); }
.exam-status { font-size: 0.65rem; padding: 2px 8px; border-radius: 8px; font-weight: 600; }
.exam-status.upcoming { background: var(--bg-subtle); color: var(--text-muted); }
.exam-status.ongoing { background: rgba(13,148,136,0.08); color: var(--success); }
.exam-status.submitted { background: rgba(13,148,136,0.08); color: var(--success); }
.exam-status.ended { background: var(--bg-subtle); color: var(--text-muted); }
.exam-meta { display: flex; gap: 10px; font-size: 0.7rem; color: var(--text-muted); }
.exam-actions { flex-shrink: 0; margin-left: 16px; }
.exam-score { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.exam-countdown { font-size: 0.74rem; color: var(--text-muted); }
.exam-ended-text { font-size: 0.74rem; color: var(--text-muted); }
.btn-sm { padding: 6px 16px; font-size: 0.72rem; border-radius: 8px; }

/* 空状态 */
.empty-hint, .loading-hint {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 0.8rem;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px dashed var(--border-light);
}
</style>