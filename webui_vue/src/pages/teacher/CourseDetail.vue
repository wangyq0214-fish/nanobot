<template>
  <div class="app-shell">
    <TeacherNav active-tab="courses" @logout="onLogout" />

    <div class="main-area">
      <div class="detail-page">
        <!-- Back + Header -->
        <button class="back-btn" @click="$router.push('/teacher/courses')">← 返回课程列表</button>
        <div v-if="course" class="course-header">
          <div class="course-info">
            <h2>{{ course.courseName }}</h2>
            <div class="course-tags">
              <span class="tag">{{ course.subject }}</span>
              <span class="tag">{{ course.grade }}</span>
              <span class="tag code-tag">课程码: {{ course.joinCode }}</span>
            </div>
            <p v-if="course.description" class="course-desc">{{ course.description }}</p>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tab-bar">
          <span class="tab-item" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">课时</span>
          <span class="tab-item" :class="{ active: activeTab === 'homework' }" @click="activeTab = 'homework'">作业</span>
          <span class="tab-item" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">学生 ({{ members.length }})</span>
        </div>

        <!-- Tab: Lessons -->
        <div v-if="activeTab === 'lessons'" class="tab-content">
          <div v-if="lessons.length === 0" class="empty-hint">暂无课时，通过教案页面生成教案后可关联到课程</div>
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
          <div class="tab-header">
            <button class="btn-primary" @click="showCreateHw = true">+ 布置作业</button>
          </div>
          <div v-if="homeworkList.length === 0" class="empty-hint">暂无作业</div>
          <div v-for="hw in homeworkList" :key="hw.hwId" class="hw-card">
            <div class="hw-header" @click="toggleHomework(hw.hwId)">
              <div class="hw-title-row">
                <span class="hw-title">{{ hw.title }}</span>
                <span class="hw-deadline" v-if="hw.deadline">截止: {{ formatDate(hw.deadline) }}</span>
              </div>
              <span class="hw-questions">{{ hw.questions?.length || 0 }} 题 · {{ hw.totalPoints }} 分</span>
            </div>
            <div v-if="expandedHw === hw.hwId" class="hw-body">
              <div v-for="(q, qi) in hw.questions" :key="q.id" class="hw-question">
                <span class="q-label">{{ qi + 1 }}.</span>
                <span class="q-content">{{ q.content }}</span>
                <span class="q-points">{{ q.points }}分</span>
              </div>
              <div class="hw-actions">
                <button class="btn-secondary" @click="viewSubmissions(hw.hwId)">查看提交 ({{ submissionCounts[hw.hwId] || 0 }})</button>
              </div>
              <!-- Submissions list -->
              <div v-if="viewingSubmissions === hw.hwId" class="submissions-panel">
                <h4>提交列表</h4>
                <div v-if="currentSubmissions.length === 0" class="empty-hint">暂无提交</div>
                <div v-for="sub in currentSubmissions" :key="sub.studentId" class="sub-row">
                  <span class="sub-student">{{ sub.studentId }}</span>
                  <span class="sub-status" :class="sub.status">{{ sub.status === 'graded' ? `${sub.score}分` : '待批改' }}</span>
                  <button v-if="sub.status !== 'graded'" class="btn-small" @click="openGrade(hw, sub)">批改</button>
                  <button v-else class="btn-small secondary" @click="openGrade(hw, sub)">查看</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Students -->
        <div v-if="activeTab === 'students'" class="tab-content">
          <div v-if="members.length === 0" class="empty-hint">暂无学生加入，分享课程码 <strong>{{ course?.joinCode }}</strong> 给学生</div>
          <table v-else class="students-table">
            <thead><tr><th>学生</th><th>加入时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="m in members" :key="m.userId">
                <td>{{ m.displayName || m.userId }}</td>
                <td>{{ formatDate(m.joinedAt) }}</td>
                <td><button class="btn-small" @click="viewAnalytics(m.userId)">查看学情</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- CREATE HOMEWORK DIALOG -->
    <CreateHomeworkDialog v-if="showCreateHw && user" :user="user" @close="showCreateHw = false" @created="onHomeworkCreated" />

    <!-- GRADE DIALOG -->
    <div v-if="gradingSub" class="dialog-overlay" @click.self="gradingSub = null">
      <div class="dialog-card">
        <h3>批改: {{ gradingSub.studentId }}</h3>
        <div v-for="(q, qi) in gradingHw.questions" :key="q.id" class="grade-question">
          <p class="grade-q-label">{{ qi + 1 }}. {{ q.content }} ({{ q.points }}分)</p>
          <p class="grade-answer">学生答案: {{ gradingSub.answers?.[q.id] || '未作答' }}</p>
          <div class="grade-input-row">
            <input v-model="gradeScores[q.id]" type="number" :max="q.points" min="0" placeholder="得分" />
            <input v-model="gradeFeedbacks[q.id]" placeholder="评语（可选）" />
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="gradingSub = null">取消</button>
          <button class="btn-primary" @click="submitGrade">确认批改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import TeacherNav from '../../components/TeacherNav.vue'
import CreateHomeworkDialog from '../../components/CreateHomeworkDialog.vue'

const router = useRouter()
const route = useRoute()
const { user, logout: authLogout } = useAuth()
const { connect: connectGateway, connected, getToken } = useGateway()
const {
  currentCourse: course, members, lessons, homeworkList,
  fetchCourseDetail, fetchMembers, fetchLessons, fetchHomeworkList,
  fetchLessonDetail, fetchSubmissions, gradeSubmission,
} = useCourse()

const courseId = route.params.courseId
const activeTab = ref('lessons')
const expandedLesson = ref(null)
const expandedHw = ref(null)
const lessonPlans = reactive({})
const showCreateHw = ref(false)

function onLogout() { authLogout(); router.push('/login') }

async function loadAll() {
  const t = getToken()
  await Promise.all([
    fetchCourseDetail(courseId, t),
    fetchMembers(courseId, t),
    fetchLessons(courseId, t),
    fetchHomeworkList(courseId, t),
  ])
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
  viewingSubmissions.value = null
}

function renderMd(text) { return marked.parse(text || '') }
function formatDate(d) { if (!d) return '-'; return new Date(d).toLocaleDateString('zh-CN') }

// Submissions
const viewingSubmissions = ref(null)
const currentSubmissions = ref([])
const submissionCounts = reactive({})

async function viewSubmissions(hwId) {
  if (viewingSubmissions.value === hwId) { viewingSubmissions.value = null; return }
  viewingSubmissions.value = hwId
  try {
    const subs = await fetchSubmissions(courseId, hwId, getToken())
    currentSubmissions.value = subs
    submissionCounts[hwId] = subs.length
  } catch { currentSubmissions.value = [] }
}

// Grading
const gradingHw = ref(null)
const gradingSub = ref(null)
const gradeScores = reactive({})
const gradeFeedbacks = reactive({})

function openGrade(hw, sub) {
  gradingHw.value = hw
  gradingSub.value = sub
  for (const q of hw.questions) {
    gradeScores[q.id] = sub.score && sub.status === 'graded' ? Math.round(sub.score / hw.questions.length) : ''
    gradeFeedbacks[q.id] = sub.feedback?.[q.id] || ''
  }
}

async function submitGrade() {
  const hw = gradingHw.value
  const sub = gradingSub.value
  const feedback = {}
  let totalScore = 0
  for (const q of hw.questions) {
    const s = parseInt(gradeScores[q.id]) || 0
    feedback[q.id] = gradeFeedbacks[q.id] || ''
    totalScore += s
  }
  try {
    await gradeSubmission(courseId, hw.hwId, sub.studentId, totalScore, feedback, user.value.role, user.value.userId, getToken())
    gradingSub.value = null
    await viewSubmissions(hw.hwId)
  } catch (e) { alert('批改失败: ' + e.message) }
}

function viewAnalytics(studentId) {
  router.push(`/teacher/courses/${courseId}/analytics/${studentId}`)
}

function onHomeworkCreated() {
  showCreateHw.value = false
  fetchHomeworkList(courseId, getToken())
}

onMounted(async () => {
  if (!user.value) return
  if (!connected.value) {
    try { await connectGateway({ role: user.value.role, userId: user.value.userId }) } catch {}
  }
  loadAll()
})
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; background: var(--bg, #f8f6f1); }
.main-area { flex: 1; overflow-y: auto; padding: 24px 32px; }
.detail-page { width: 100%; }

/* Login (reuse) */
.login-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; }
.login-card { background: #fff; border-radius: 16px; padding: 40px; width: 360px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.login-header { text-align: center; margin-bottom: 24px; }
.login-logo { font-size: 1.5rem; font-weight: 700; }
.login-logo .dot { display: inline-block; width: 8px; height: 8px; background: #5b8def; border-radius: 50%; margin-right: 6px; }
.login-subtitle { color: #888; font-size: 0.85rem; margin-top: 4px; }
.login-input { width: 100%; padding: 10px 14px; border: 1.5px solid #e0dcd5; border-radius: 8px; font-size: 0.9rem; outline: none; box-sizing: border-box; }
.login-error { color: #e74c3c; font-size: 0.8rem; margin-top: 8px; }
.login-submit { width: 100%; padding: 10px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-top: 12px; }
.login-submit:disabled { opacity: 0.5; }

/* Header */
.back-btn { background: none; border: none; color: #5b8def; font-size: 0.85rem; cursor: pointer; margin-bottom: 16px; padding: 0; }
.course-header { margin-bottom: 24px; }
.course-header h2 { margin: 0 0 8px; font-size: 1.4rem; }
.course-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.tag { background: #eef4ff; color: #5b8def; font-size: 0.72rem; font-weight: 600; padding: 2px 10px; border-radius: 4px; }
.code-tag { background: #fff3e0; color: #e67e22; font-family: monospace; }
.course-desc { color: #666; font-size: 0.85rem; margin-top: 8px; }

/* Tabs */
.tab-bar { display: flex; gap: 0; border-bottom: 2px solid #e8e4db; margin-bottom: 20px; }
.tab-item { padding: 10px 20px; font-size: 0.88rem; font-weight: 600; color: #888; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
.tab-item.active { color: #5b8def; border-bottom-color: #5b8def; }
.tab-header { display: flex; justify-content: flex-end; margin-bottom: 16px; }

/* Lessons */
.lesson-card { background: #fff; border: 1px solid #e8e4db; border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
.lesson-header { display: flex; align-items: center; padding: 14px 18px; cursor: pointer; gap: 10px; }
.lesson-header:hover { background: #faf8f5; }
.lesson-order { font-size: 0.8rem; color: #5b8def; font-weight: 700; min-width: 30px; }
.lesson-title { flex: 1; font-weight: 600; font-size: 0.92rem; }
.lesson-toggle { font-size: 0.7rem; color: #999; }
.lesson-body { padding: 0 18px 16px; border-top: 1px solid #f0ede8; }
.lesson-desc { color: #666; font-size: 0.82rem; margin: 10px 0; }
.plan-content { font-size: 0.85rem; line-height: 1.7; }
.plan-content :deep(h1), .plan-content :deep(h2), .plan-content :deep(h3) { margin: 12px 0 6px; }
.plan-content :deep(table) { border-collapse: collapse; margin: 8px 0; }
.plan-content :deep(th), .plan-content :deep(td) { border: 1px solid #e0dcd5; padding: 6px 10px; font-size: 0.82rem; }

/* Homework */
.hw-card { background: #fff; border: 1px solid #e8e4db; border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
.hw-header { padding: 14px 18px; cursor: pointer; }
.hw-header:hover { background: #faf8f5; }
.hw-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.hw-title { font-weight: 600; font-size: 0.92rem; }
.hw-deadline { font-size: 0.75rem; color: #e67e22; }
.hw-questions { font-size: 0.78rem; color: #888; }
.hw-body { padding: 0 18px 16px; border-top: 1px solid #f0ede8; }
.hw-question { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px dashed #f0ede8; align-items: flex-start; }
.hw-question:last-child { border-bottom: none; }
.q-label { font-weight: 700; color: #5b8def; min-width: 24px; }
.q-content { flex: 1; font-size: 0.85rem; }
.q-points { font-size: 0.75rem; color: #999; }
.hw-actions { margin-top: 12px; }

/* Submissions */
.submissions-panel { margin-top: 16px; padding: 16px; background: #faf8f5; border-radius: 8px; }
.submissions-panel h4 { margin: 0 0 12px; font-size: 0.9rem; }
.sub-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0ede8; }
.sub-row:last-child { border-bottom: none; }
.sub-student { font-weight: 600; font-size: 0.85rem; flex: 1; }
.sub-status { font-size: 0.78rem; padding: 2px 8px; border-radius: 4px; }
.sub-status.submitted { background: #fff3e0; color: #e67e22; }
.sub-status.graded { background: #e8f5e9; color: #2e7d32; }

/* Students table */
.students-table { width: 100%; border-collapse: collapse; }
.students-table th, .students-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #e8e4db; font-size: 0.85rem; }
.students-table th { font-weight: 600; color: #555; background: #faf8f5; }

/* Grade dialog */
.grade-question { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f0ede8; }
.grade-q-label { font-weight: 600; font-size: 0.85rem; margin: 0 0 4px; }
.grade-answer { font-size: 0.82rem; color: #555; margin: 0 0 8px; background: #f8f6f1; padding: 8px; border-radius: 6px; }
.grade-input-row { display: flex; gap: 8px; }
.grade-input-row input { flex: 1; padding: 6px 10px; border: 1.5px solid #e0dcd5; border-radius: 6px; font-size: 0.82rem; outline: none; }
.grade-input-row input:first-child { max-width: 80px; }

/* Dialog (shared) */
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #fff; border-radius: 16px; padding: 32px; width: 520px; max-height: 85vh; overflow-y: auto; }
.dialog-card h3 { margin: 0 0 20px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

/* Buttons */
.btn-primary { padding: 8px 20px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #4a7de0; }
.btn-secondary { padding: 8px 20px; background: #f0ede8; color: #555; border: none; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-small { padding: 4px 12px; background: #5b8def; color: #fff; border: none; border-radius: 6px; font-size: 0.75rem; cursor: pointer; }
.btn-small.secondary { background: #f0ede8; color: #555; }

.empty-hint { text-align: center; padding: 40px; color: #999; }

/* Dark */
:global(body.dark) .app-shell { background: #12121a; }
:global(body.dark) .login-card, :global(body.dark) .dialog-card, :global(body.dark) .lesson-card, :global(body.dark) .hw-card { background: #1e1e2e; border-color: #333; }
:global(body.dark) .course-header h2, :global(body.dark) .dialog-card h3 { color: #e0e0e0; }
:global(body.dark) .lesson-header:hover, :global(body.dark) .hw-header:hover { background: #252535; }
:global(body.dark) .login-input, :global(body.dark) .grade-input-row input { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .students-table th { background: #252535; color: #ccc; }
:global(body.dark) .submissions-panel { background: #252535; }
:global(body.dark) .grade-answer { background: #252535; color: #ccc; }
</style>
