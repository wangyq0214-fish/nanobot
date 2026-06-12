<template>
  <div class="app-shell">
    <TeacherNav active-tab="courses" @logout="onLogout" />

    <!-- 主内容框：紫色描边 + 扫描线 + 横向铺满 -->
    <div class="main-area panel">
      <!-- 四边扫描线装饰 -->
      <div class="panel-strip top"></div>
      <div class="panel-strip right"></div>
      <div class="panel-strip bottom"></div>
      <div class="panel-strip left"></div>

      <div class="detail-page">
        <!-- 返回按钮 -->
        <button class="back-btn" @click="$router.push('/teacher/courses')">← 返回课程列表</button>

        <!-- 课程头部 -->
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

        <!-- 标签栏 -->
        <div class="tab-bar">
          <span class="tab-item" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">课时</span>
          <span class="tab-item" :class="{ active: activeTab === 'homework' }" @click="activeTab = 'homework'">作业</span>
          <span class="tab-item" :class="{ active: activeTab === 'questionBank' }" @click="activeTab = 'questionBank'">题库</span>
          <span class="tab-item" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">学生 ({{ members.length }})</span>
        </div>

        <!-- ===== 课时 ===== -->
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

        <!-- ===== 作业 ===== -->
        <div v-if="activeTab === 'homework'" class="tab-content">
          <div class="tab-header">
            <button class="btn-primary" @click="showCreateHw = true">+ 布置作业</button>
          </div>
          <div v-if="homeworkList.length === 0" class="empty-hint">暂无作业</div>
          <div v-for="hw in homeworkList" :key="hw.hwId" class="hw-card" :class="{ 'hw-draft': hw.status === 'draft' }">
            <div class="hw-header" @click="toggleHomework(hw.hwId)">
              <div class="hw-title-row">
                <span class="hw-title">{{ hw.title }}</span>
                <span v-if="hw.status === 'draft'" class="hw-status-badge draft">草稿</span>
                <span v-else class="hw-status-badge published">已发布</span>
                <span class="hw-deadline" v-if="hw.deadline">截止: {{ formatDate(hw.deadline) }}</span>
              </div>
              <div class="hw-meta-row">
                <span class="hw-questions">{{ hw.questions?.length || 0 }} 题 · {{ hw.totalPoints }} 分</span>
                <div class="hw-actions-row">
                  <button v-if="hw.status === 'draft'" class="btn-publish-hw" @click.stop="handlePublishHomework(hw)" title="发布作业">📤 发布</button>
                  <button class="btn-delete-hw" @click.stop="handleDeleteHomework(hw)" title="删除作业">🗑 删除</button>
                </div>
              </div>
            </div>
            <div v-if="expandedHw === hw.hwId" class="hw-body">
              <div v-for="(q, qi) in hw.questions" :key="q.id" class="hw-question">
                <span class="q-label">{{ qi + 1 }}.</span>
                <span class="q-content">{{ q.content }}</span>
                <span class="q-points">{{ q.points }}分</span>
              </div>
              <div class="hw-actions">
                <button v-if="hw.status === 'published'" class="btn-secondary" @click="viewSubmissions(hw.hwId)">查看提交 ({{ submissionCounts[hw.hwId] || 0 }})</button>
                <span v-else class="hint-text">发布后学生才能提交</span>
              </div>
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

        <!-- ===== 题库 ===== -->
        <div v-if="activeTab === 'questionBank'" class="tab-content">
          <div class="tab-header qb-header">
            <div class="qb-filter-row">
              <select v-model="qbFilterType" class="qb-filter-select">
                <option value="">全部题型</option>
                <option value="choice">选择题</option>
                <option value="true_false">判断题</option>
                <option value="fill">填空题</option>
                <option value="short_answer">简答题</option>
                <option value="essay">论述题</option>
              </select>
              <span class="question-count">共 {{ filteredQuestionBank.length }} 道题</span>
            </div>
            <button class="btn-primary" @click="showQuestionBank = true">管理题库</button>
          </div>
          <div v-if="questionBank.length === 0" class="empty-hint">题库为空，布置作业时可保存题目到题库</div>
          <div v-else-if="filteredQuestionBank.length === 0" class="empty-hint">没有该题型的题目</div>
          <div v-for="(q, qi) in filteredQuestionBank" :key="q.id" class="qb-question-card"
               :class="{ 'qb-editing': editingQuestion && editingQuestion.id === q.id }">

            <!-- 查看模式 -->
            <template v-if="!(editingQuestion && editingQuestion.id === q.id)">
              <div class="q-header">
                <span class="q-num">{{ qi + 1 }}</span>
                <span class="q-type-badge">{{ getTypeLabel(q.questionType) }}</span>
                <span class="q-points">{{ q.points }}分</span>
                <span class="q-source">{{ q.source === 'ai' ? '🤖' : '✏️' }}</span>
                <div class="q-actions">
                  <button class="btn-edit-q" @click.stop="handleEditQ(q)" title="编辑">✏️</button>
                  <button class="btn-delete-q" @click.stop="handleDeleteQ(q)" title="删除">🗑</button>
                </div>
              </div>
              <div class="q-content">{{ q.content }}</div>
              <div v-if="q.answer" class="q-answer">答案：{{ q.answer }}</div>
              <div v-if="q.explanation" class="q-explanation">解析：{{ q.explanation }}</div>
            </template>

            <!-- 编辑模式 -->
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
                      <option v-for="(opt, oi) in editingQuestion.options" :key="oi" :value="opt.key">{{ opt.key }}</option>
                    </select>
                  </div>
                </div>

                <div v-if="editingQuestion.questionType === 'true_false'" class="answer-row">
                  <label>正确答案：</label>
                  <select v-model="editingQuestion.answer">
                    <option value="true">正确</option>
                    <option value="false">错误</option>
                  </select>
                </div>

                <div v-if="['fill', 'short_answer', 'essay'].includes(editingQuestion.questionType)" class="answer-row">
                  <label>参考答案：</label>
                  <textarea v-model="editingQuestion.answer" rows="2" placeholder="参考答案"></textarea>
                </div>

                <textarea v-model="editingQuestion.explanation" rows="2" placeholder="解析（可选）" class="explanation-input"></textarea>

                <div class="form-actions">
                  <button class="btn-secondary" @click="handleCancelEditQ">取消</button>
                  <button class="btn-primary" @click="handleSaveEditQ" :disabled="!editingQuestion.content.trim()">保存修改</button>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- ===== 学生 ===== -->
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

    <!-- 对话框组件 -->
    <CreateHomeworkDialog v-if="showCreateHw" :user="user" @close="showCreateHw = false" @created="onHomeworkCreated" />
    <QuestionBankDialog v-if="showQuestionBank" :user="user" @close="onQuestionBankClose" @updated="onQuestionBankUpdated" />

    <!-- 批改对话框 -->
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import TeacherNav from '../../components/TeacherNav.vue'
import CreateHomeworkDialog from '../../components/CreateHomeworkDialog.vue'
import QuestionBankDialog from '../../components/QuestionBankDialog.vue'

const router = useRouter()
const route = useRoute()
const { user, logout: authLogout } = useAuth()
const { connect: connectGateway, connected, getToken } = useGateway()
const {
  currentCourse: course, members, lessons, homeworkList,
  fetchCourseDetail, fetchMembers, fetchLessons, fetchHomeworkList,
  fetchLessonDetail, fetchSubmissions, gradeSubmission, deleteHomework, publishHomework,
  fetchQuestionBank, deleteFromQuestionBank, updateQuestionBank,
} = useCourse()

const courseId = route.params.courseId
const activeTab = ref('lessons')
const expandedLesson = ref(null)
const expandedHw = ref(null)
const lessonPlans = reactive({})
const showCreateHw = ref(false)
const showQuestionBank = ref(false)
const questionBank = ref([])
const editingQuestion = ref(null)
const qbFilterType = ref('')

const filteredQuestionBank = computed(() => {
  if (!qbFilterType.value) return questionBank.value
  return questionBank.value.filter(q => q.questionType === qbFilterType.value)
})

function onLogout() { authLogout(); router.push('/login') }

async function loadAll() {
  const t = getToken()
  await Promise.all([
    fetchCourseDetail(courseId, t),
    fetchMembers(courseId, t),
    fetchLessons(courseId, t),
    fetchHomeworkList(courseId, t),
  ])
  try {
    questionBank.value = await fetchQuestionBank(courseId, t)
  } catch {}
  for (const hw of homeworkList.value) {
    try {
      const subs = await fetchSubmissions(courseId, hw.hwId, t)
      submissionCounts[hw.hwId] = subs.length
    } catch {}
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

async function handleDeleteHomework(hw) {
  if (!confirm(`确定要删除作业"${hw.title}"吗？此操作不可恢复。`)) return
  try {
    const t = getToken()
    if (!user.value) return
    await deleteHomework(courseId, hw.hwId, user.value.role, user.value.userId, t)
    await fetchHomeworkList(courseId, t)
    alert('作业已删除')
  } catch (e) { alert('删除失败: ' + (e.message || '未知错误')) }
}

async function handlePublishHomework(hw) {
  if (!confirm(`确定要发布作业"${hw.title}"吗？发布后学生可以看到并提交。`)) return
  try {
    const t = getToken()
    if (!user.value) return
    await publishHomework(courseId, hw.hwId, user.value.role, user.value.userId, t)
    await fetchHomeworkList(courseId, t)
    alert('作业已发布')
  } catch (e) { alert('发布失败: ' + (e.message || '未知错误')) }
}

async function onQuestionBankClose() {
  showQuestionBank.value = false
  try { questionBank.value = await fetchQuestionBank(courseId, getToken()) } catch {}
}
async function onQuestionBankUpdated() {
  try { questionBank.value = await fetchQuestionBank(courseId, getToken()) } catch {}
}

function handleEditQ(q) {
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
function handleCancelEditQ() { editingQuestion.value = null }

async function handleSaveEditQ() {
  if (!editingQuestion.value || !editingQuestion.value.content.trim()) return
  try {
    const t = getToken()
    if (!user.value) return
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
    const result = await updateQuestionBank(courseId, editingQuestion.value.id, updateData, user.value.role, user.value.userId, t)
    if (result.question) {
      const idx = questionBank.value.findIndex(item => item.id === editingQuestion.value.id)
      if (idx >= 0) questionBank.value[idx] = result.question
    }
    editingQuestion.value = null
  } catch (e) { alert('保存失败: ' + (e.message || '未知错误')) }
}

async function handleDeleteQ(q) {
  if (!confirm('确定要从题库中删除这道题吗？')) return
  try {
    const t = getToken()
    if (!user.value) return
    await deleteFromQuestionBank(courseId, q.id, user.value.role, user.value.userId, t)
    questionBank.value = questionBank.value.filter(item => item.id !== q.id)
  } catch (e) { alert('删除失败: ' + (e.message || '未知错误')) }
}

function toggleHomework(hwId) {
  expandedHw.value = expandedHw.value === hwId ? null : hwId
  viewingSubmissions.value = null
}

function renderMd(text) { return marked.parse(text || '') }
function formatDate(d) { if (!d) return '-'; return new Date(d).toLocaleDateString('zh-CN') }

function getTypeLabel(type) {
  const labels = { choice: '选择题', true_false: '判断题', fill: '填空题', short_answer: '简答题', essay: '论述题' }
  return labels[type] || type
}

const viewingSubmissions = ref(null)
const currentSubmissions = ref([])
const submissionCounts = reactive({})

async function viewSubmissions(hwId) {
  if (viewingSubmissions.value === hwId) { viewingSubmissions.value = null; return }
  viewingSubmissions.value = hwId
  try {
    const subs = await fetchSubmissions(courseId, hwId, getToken())
    currentSubmissions.value = subs || []
    submissionCounts[hwId] = subs.length
  } catch { currentSubmissions.value = [] }
}

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
  loadAll()
})
</script>

<style>
/* ========== 全局主题变量 ========== */
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255, 255, 255, 0.55);
  --accent: #6b5df0;
  --accent-deep: #5a4ad0;
  --accent-soft: rgba(107, 93, 240, 0.09);
  --accent-glow: rgba(107, 93, 240, 0.22);
  --border-light: rgba(0, 0, 0, 0.08);
  --border-medium: rgba(0, 0, 0, 0.14);
  --border-active: #6b5df0;
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0, 0, 0, 0.06);
  --danger: #ef4444;
  --success: #0d9488;
  --warning: #f39c12;
}

body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18, 19, 34, 0.50);
  --accent: #8b70ff;
  --accent-deep: #6b50e0;
  --accent-soft: rgba(139, 112, 255, 0.12);
  --accent-glow: rgba(139, 112, 255, 0.30);
  --border-light: rgba(255, 255, 255, 0.08);
  --border-medium: rgba(255, 255, 255, 0.16);
  --border-active: #8b70ff;
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255, 255, 255, 0.07);
}
</style>

<style scoped>
/* ========== 布局 ========== */
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 6px 10px;
  gap: 8px;
  background: var(--bg-root);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  transition: background 0.4s, color 0.4s;
  overflow: hidden;
}

.main-area {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: 24px 36px;
  background: var(--bg-card);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1.8px solid var(--border-active);
  border-radius: 20px;
  box-shadow: 0 0 20px var(--accent-glow), 0 0 44px var(--accent-soft);
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: var(--border-light) transparent;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.main-area:hover {
  border-color: var(--accent);
  box-shadow: 0 0 28px var(--accent-glow), 0 0 56px var(--accent-soft);
}

.main-area::-webkit-scrollbar { width: 4px; }
.main-area::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 2px; }

.detail-page { width: 100%; }

/* ========== 扫描线动画（参考批改页面panel-strip） ========== */
.panel-strip { position: absolute; pointer-events: none; z-index: 1; }
.panel-strip.top, .panel-strip.bottom { left: -100%; width: 100%; height: 1.5px; background: linear-gradient(90deg, transparent, #C4B0FF, #7B5CFF, #C4B0FF, transparent); box-shadow: 0 0 7px #C4B0FF; }
.panel-strip.right, .panel-strip.left { top: -100%; width: 1.5px; height: 100%; background: linear-gradient(180deg, transparent, #C4B0FF, #A78BFA, #C4B0FF, transparent); box-shadow: 0 0 7px #C4B0FF; }
.panel-strip.top    { top: 0;    animation: scanH 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); }
.panel-strip.right  { right: 0;  animation: scanV 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay: 0.8s; }
.panel-strip.bottom { bottom: 0; animation: scanHRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay: 1.6s; }
.panel-strip.left   { left: 0;   animation: scanVRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay: 2.4s; }

@keyframes scanH    { 0%{left:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:100%;opacity:0} }
@keyframes scanHRev { 0%{left:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:-100%;opacity:0} }
@keyframes scanV    { 0%{top:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:100%;opacity:0} }
@keyframes scanVRev { 0%{top:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:-100%;opacity:0} }

/* ========== 返回按钮 ========== */
.back-btn {
  background: none; border: none; color: var(--accent); font-size: 0.85rem;
  cursor: pointer; margin-bottom: 16px; padding: 4px 0;
  display: inline-flex; align-items: center; gap: 4px; transition: color 0.2s;
}
.back-btn:hover { color: var(--accent-deep); }

/* ========== 课程头 ========== */
.course-header {
  margin-bottom: 24px;
  background: var(--bg-card); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1.8px solid var(--accent); border-radius: 14px; padding: 20px;
  box-shadow: 0 0 16px var(--accent-soft);
}
.course-header h2 { margin: 0 0 10px; font-size: 1.4rem; color: var(--text-primary); }
.course-tags { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.tag { background: rgba(107,93,240,0.1); color: var(--accent); font-size: 0.72rem; font-weight: 600; padding: 3px 10px; border-radius: 20px; border: 1px solid var(--accent); white-space: nowrap; }
.code-tag { background: rgba(245,158,12,0.1); color: var(--warning); border-color: var(--warning); font-family: monospace; font-size: 0.7rem; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 3px 10px; }
.course-desc { color: var(--text-secondary); font-size: 0.85rem; margin-top: 8px; }

/* ========== 标签栏 ========== */
.tab-bar { display: flex; gap: 0; border-bottom: 2px solid var(--border-medium); margin-bottom: 20px; }
.tab-item { padding: 10px 20px; font-size: 0.88rem; font-weight: 600; color: var(--text-secondary); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
.tab-item:hover { color: var(--text-primary); }
.tab-item.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-header { display: flex; justify-content: flex-end; margin-bottom: 16px; }
.qb-header { justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }

/* ========== 课时卡片 ========== */
.lesson-card {
  background: var(--bg-card); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1.8px solid var(--accent); border-radius: 12px; margin-bottom: 10px;
  overflow: hidden; transition: all 0.3s ease; box-shadow: 0 0 12px var(--accent-soft);
}
.lesson-card:hover { border-color: var(--accent); box-shadow: 0 4px 20px var(--accent-glow); }
.lesson-header { display: flex; align-items: center; padding: 14px 18px; cursor: pointer; gap: 10px; }
.lesson-header:hover { background: var(--accent-soft); }
.lesson-order { font-size: 0.8rem; color: var(--accent); font-weight: 700; min-width: 30px; }
.lesson-title { flex: 1; font-weight: 600; font-size: 0.92rem; color: var(--text-primary); }
.lesson-toggle { font-size: 0.7rem; color: var(--text-muted); }
.lesson-body { padding: 0 18px 16px; border-top: 1px solid var(--divider); }
.lesson-desc { color: var(--text-secondary); font-size: 0.82rem; margin: 10px 0; }
.plan-content { font-size: 0.85rem; line-height: 1.7; color: var(--text-primary); }

/* ========== 作业卡片 ========== */
.hw-card {
  background: var(--bg-card); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1.8px solid var(--accent); border-radius: 12px; margin-bottom: 10px;
  overflow: hidden; transition: all 0.3s; box-shadow: 0 0 12px var(--accent-soft);
}
.hw-card.hw-draft { border-left: 4px solid var(--warning); }
.hw-header { padding: 14px 18px; cursor: pointer; }
.hw-header:hover { background: var(--accent-soft); }
.hw-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; gap: 8px; }
.hw-title { font-weight: 600; font-size: 0.92rem; color: var(--text-primary); }
.hw-status-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.hw-status-badge.draft { background: rgba(245,158,12,0.12); color: var(--warning); }
.hw-status-badge.published { background: rgba(13,148,136,0.12); color: var(--success); }
.hw-deadline { font-size: 0.75rem; color: var(--warning); }
.hw-meta-row { display: flex; justify-content: space-between; align-items: center; }
.hw-questions { font-size: 0.78rem; color: var(--text-secondary); }
.hw-actions-row { display: flex; gap: 8px; }
.btn-publish-hw { background: none; border: 1px solid var(--success); color: var(--success); font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
.btn-publish-hw:hover { background: var(--success); color: #fff; }
.btn-delete-hw { background: none; border: 1px solid var(--danger); color: var(--danger); font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
.btn-delete-hw:hover { background: var(--danger); color: #fff; }
.hw-body { padding: 0 18px 16px; border-top: 1px solid var(--divider); }
.hw-question { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px dashed var(--divider); align-items: flex-start; }
.hw-question:last-child { border-bottom: none; }
.q-label { font-weight: 700; color: var(--accent); min-width: 24px; }
.q-content { flex: 1; font-size: 0.85rem; color: var(--text-primary); }
.q-points { font-size: 0.75rem; color: var(--text-muted); }
.hw-actions { margin-top: 12px; }
.hint-text { font-size: 0.78rem; color: var(--text-muted); font-style: italic; }

/* ========== 题库 ========== */
.qb-filter-row { display: flex; align-items: center; gap: 10px; }
.qb-filter-select { padding: 6px 12px; background: var(--bg-card); backdrop-filter: blur(8px); border: 1.5px solid var(--border-medium); border-radius: 8px; font-size: 0.82rem; outline: none; color: var(--text-primary); transition: border 0.2s; }
.qb-filter-select:focus { border-color: var(--accent); }
.question-count { font-size: 0.78rem; color: var(--text-muted); background: var(--accent-soft); padding: 2px 10px; border-radius: 20px; white-space: nowrap; }
.qb-question-card {
  background: var(--bg-card); backdrop-filter: blur(12px); border: 1.8px solid var(--accent);
  border-radius: 12px; padding: 12px; margin-bottom: 10px; transition: all 0.3s; box-shadow: 0 0 12px var(--accent-soft);
}
.qb-question-card.qb-editing { border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow); }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.q-num { font-weight: 700; color: var(--accent); font-size: 0.85rem; min-width: 20px; }
.q-type-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: rgba(107,93,240,0.1); color: var(--accent); }
.q-source { font-size: 0.78rem; color: var(--text-muted); }
.q-content { color: var(--text-primary); }
.q-answer, .q-explanation { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; }
.q-actions { margin-left: auto; display: flex; gap: 4px; }
.btn-edit-q, .btn-delete-q { background: none; border: none; cursor: pointer; font-size: 0.85rem; opacity: 0.5; transition: opacity 0.2s; padding: 2px 4px; color: var(--text-secondary); }
.btn-edit-q:hover, .btn-delete-q:hover { opacity: 1; }
.inline-edit-form { padding: 4px 0; }
.inline-edit-form .form-row { display: flex; gap: 10px; margin-bottom: 10px; }
.inline-edit-form .q-type-select, .inline-edit-form .points-input, .inline-edit-form .q-content-input, .inline-edit-form .explanation-input, .inline-edit-form .option-row input, .inline-edit-form .answer-row select, .inline-edit-form .answer-row textarea { background: rgba(255,255,255,0.4); border: 1.5px solid var(--border-medium); border-radius: 8px; padding: 8px; font-size: 0.85rem; color: var(--text-primary); transition: border 0.2s; }
.dark .inline-edit-form .q-type-select, .dark .inline-edit-form .points-input, .dark .inline-edit-form .q-content-input, .dark .inline-edit-form .explanation-input, .dark .inline-edit-form .option-row input, .dark .inline-edit-form .answer-row select, .dark .inline-edit-form .answer-row textarea { background: rgba(20,20,35,0.6); }
.inline-edit-form .q-type-select:focus, .inline-edit-form .points-input:focus, .inline-edit-form .q-content-input:focus, .inline-edit-form .explanation-input:focus, .inline-edit-form .option-row input:focus, .inline-edit-form .answer-row select:focus, .inline-edit-form .answer-row textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.inline-edit-form .q-type-select { flex: 1; }
.inline-edit-form .points-input { width: 80px; }
.inline-edit-form .q-content-input, .inline-edit-form .explanation-input { width: 100%; resize: vertical; box-sizing: border-box; }
.inline-edit-form .options-section { margin: 10px 0; padding: 10px; background: var(--bg-root); border-radius: 8px; }
.inline-edit-form .option-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.inline-edit-form .option-row span { min-width: 20px; font-weight: 600; color: var(--accent); }
.inline-edit-form .option-row button { background: none; border: none; color: var(--text-muted); cursor: pointer; }
.inline-edit-form .option-row button:hover { color: var(--danger); }
.btn-add-opt { background: none; border: 1px dashed var(--border-medium); border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }
.btn-add-opt:hover { border-color: var(--accent); color: var(--accent); }
.inline-edit-form .answer-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.inline-edit-form .answer-row label { font-size: 0.82rem; color: var(--text-secondary); min-width: 70px; }
.inline-edit-form .answer-row select, .inline-edit-form .answer-row textarea { flex: 1; }
.inline-edit-form .form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 12px; }

/* ========== 提交面板 ========== */
.submissions-panel { margin-top: 16px; padding: 16px; background: var(--bg-card); backdrop-filter: blur(8px); border-radius: 10px; border: 1px solid var(--border-medium); }
.submissions-panel h4 { margin: 0 0 12px; font-size: 0.9rem; color: var(--text-primary); }
.sub-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--divider); }
.sub-row:last-child { border-bottom: none; }
.sub-student { font-weight: 600; font-size: 0.85rem; color: var(--text-primary); flex: 1; }
.sub-status { font-size: 0.78rem; padding: 2px 8px; border-radius: 4px; }
.sub-status.submitted { background: rgba(245,158,12,0.1); color: var(--warning); }
.sub-status.graded { background: rgba(13,148,136,0.1); color: var(--success); }

/* ========== 学生表格 ========== */
.students-table { width: 100%; border-collapse: collapse; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: 12px; overflow: hidden; border: 1px solid var(--border-medium); }
.students-table th, .students-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--divider); font-size: 0.85rem; color: var(--text-primary); }
.students-table th { font-weight: 600; color: var(--text-secondary); background: var(--accent-soft); }

/* ========== 批改对话框 ========== */
.grade-question { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--divider); }
.grade-q-label { font-weight: 600; font-size: 0.85rem; color: var(--text-primary); margin: 0 0 4px; }
.grade-answer { font-size: 0.82rem; color: var(--text-secondary); margin: 0 0 8px; background: var(--bg-root); padding: 8px; border-radius: 6px; }
.grade-input-row { display: flex; gap: 8px; }
.grade-input-row input { flex: 1; padding: 6px 10px; background: rgba(255,255,255,0.4); border: 1.5px solid var(--border-medium); border-radius: 6px; font-size: 0.82rem; outline: none; color: var(--text-primary); transition: border 0.2s; }
.dark .grade-input-row input { background: rgba(20,20,35,0.6); }
.grade-input-row input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.grade-input-row input:first-child { max-width: 80px; }

/* ========== 通用对话框 ========== */
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: var(--bg-card); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1.8px solid var(--accent); border-radius: 16px; padding: 32px; width: 520px; max-height: 85vh; overflow-y: auto; box-shadow: 0 0 24px var(--accent-glow); }
.dialog-card h3 { margin: 0 0 20px; font-size: 1.15rem; font-weight: 700; color: var(--text-primary); }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

/* ========== 按钮 ========== */
.btn-primary { padding: 8px 20px; background: linear-gradient(135deg, var(--accent), var(--accent-deep)); color: #fff; border: none; border-radius: 10px; font-size: 0.85rem; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px var(--accent-glow); transition: all 0.3s; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }
.btn-primary:not(:disabled):hover { transform: translateY(-1px); box-shadow: 0 6px 20px var(--accent-glow); }
.btn-secondary { padding: 8px 20px; background: rgba(107,93,240,0.08); color: var(--text-primary); border: 1.5px solid var(--border-medium); border-radius: 10px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.btn-secondary:hover { background: var(--accent-soft); border-color: var(--accent); }
.btn-small { padding: 4px 12px; background: var(--accent); color: #fff; border: none; border-radius: 6px; font-size: 0.75rem; cursor: pointer; transition: background 0.2s; }
.btn-small:hover { background: var(--accent-deep); }
.btn-small.secondary { background: rgba(107,93,240,0.1); color: var(--text-primary); }
.btn-small.secondary:hover { background: var(--accent-soft); }

/* ========== 空状态 ========== */
.empty-hint, .loading-hint { text-align: center; padding: 40px; color: var(--text-muted); background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-medium); }
</style>