<template>
  <div class="detail-page">
    <!-- 返回按钮 -->
    <button class="back-btn" @click="$router.push('/teacher/courses')">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 19-7-7 7-7"/>
        <path d="M19 12H5"/>
      </svg>
      <span>返回课程列表</span>
    </button>

    <!-- 课程头部 -->
    <section v-if="course" class="course-header">
      <h2>{{ course.courseName }}</h2>
      <div class="course-tags">
        <span class="tag">{{ course.subject || '未分类' }}</span>
        <span class="tag grade-tag">{{ course.grade }}</span>
        <span class="tag code-tag">课程码：{{ course.joinCode }}</span>
      </div>
      <p v-if="course.description" class="course-desc">{{ course.description }}</p>
    </section>

    <!-- 标签栏 -->
    <div class="tab-bar">
      <button class="tab-item" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">课时</button>
      <button class="tab-item" :class="{ active: activeTab === 'homework' }" @click="activeTab = 'homework'">作业</button>
      <button class="tab-item" :class="{ active: activeTab === 'questionBank' }" @click="activeTab = 'questionBank'">题库</button>
      <button class="tab-item" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">
        学生<span class="tab-count">{{ members.length }}</span>
      </button>
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
            <button class="btn-primary" @click="showCreateHw = true">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="M12 5v14"/>
              </svg>
              <span>布置作业</span>
            </button>
          </div>
          <div v-if="homeworkList.length === 0" class="empty-hint">暂无作业</div>
          <div v-for="hw in homeworkList" :key="hw.hwId" class="hw-card-wrapper">
            <div class="hw-card" :class="{ 'hw-draft': hw.status === 'draft' }">
              <div class="hw-left" @click="toggleHomework(hw.hwId)">
                <div class="hw-icon">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                    <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
                    <path d="M10 12h4"/>
                    <path d="M10 16h4"/>
                    <path d="M8 12h.01"/>
                    <path d="M8 16h.01"/>
                  </svg>
                </div>
                <div class="hw-info">
                  <div class="hw-title-row">
                    <span class="hw-title">{{ hw.title }}</span>
                    <span v-if="hw.status === 'draft'" class="hw-status-badge draft">草稿</span>
                    <span v-else class="hw-status-badge published">已发布</span>
                  </div>
                  <span class="hw-meta">{{ hw.questions?.length || 0 }} 题 · {{ hw.totalPoints }} 分</span>
                </div>
              </div>
              <div class="hw-right">
                <span v-if="hw.deadline" class="hw-deadline">截止: {{ formatDate(hw.deadline) }}</span>
                <button class="btn-delete-hw" @click.stop="handleDeleteHomework(hw)" title="删除作业">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    <line x1="10" y1="11" x2="10" y2="17"/>
                    <line x1="14" y1="11" x2="14" y2="17"/>
                  </svg>
                  <span>删除</span>
                </button>
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
            <button class="btn-primary" @click="showQuestionBank = true">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.375 2.625a2.349 2.349 0 1 1 3.327 3.327L12 15.648l-4 1.026 1.026-4Z"/>
              </svg>
              <span>管理题库</span>
            </button>
          </div>
          <div v-if="questionBank.length === 0" class="empty-hint">题库为空，布置作业时可保存题目到题库</div>
          <div v-else-if="filteredQuestionBank.length === 0" class="empty-hint">没有该题型的题目</div>
          <div v-for="(q, qi) in filteredQuestionBank" :key="q.id" class="qb-question-card"
               :class="{ 'qb-editing': editingQuestion && editingQuestion.id === q.id }">

            <!-- 查看模式 -->
            <template v-if="!(editingQuestion && editingQuestion.id === q.id)">
              <div class="q-header">
                <div class="q-header-left">
                  <span class="q-num">{{ qi + 1 }}</span>
                  <span class="q-type-badge">{{ getTypeLabel(q.questionType) }}</span>
                  <span class="q-points">{{ q.points }}分</span>
                  <span v-if="q.source === 'ai'" class="q-source-badge ai">AI</span>
                </div>
                <div class="q-actions">
                  <button class="btn-edit-q" @click.stop="handleEditQ(q)" title="编辑">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                      <path d="m15 5 4 4"/>
                    </svg>
                  </button>
                  <button class="btn-delete-q" @click.stop="handleDeleteQ(q)" title="删除">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 6h18"/>
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="q-content">{{ q.content }}</div>
              <div v-if="q.answer" class="q-answer">
                <span class="q-answer-label">答案：</span>{{ q.answer }}
              </div>
              <div v-if="q.explanation" class="q-explanation">
                <span class="q-answer-label">解析：</span>{{ q.explanation }}
              </div>
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
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
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
  await Promise.all([
    fetchCourseDetail(courseId),
    fetchMembers(courseId),
    fetchLessons(courseId),
    fetchHomeworkList(courseId),
  ])
  try {
    questionBank.value = await fetchQuestionBank(courseId)
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
      const detail = await fetchLessonDetail(courseId, lessonId)
      lessonPlans[lessonId] = detail?.planContent || ''
    } catch { lessonPlans[lessonId] = '(加载失败)' }
  }
}

async function handleDeleteHomework(hw) {
  if (!confirm(`确定要删除作业"${hw.title}"吗？此操作不可恢复。`)) return
  try {
    if (!user.value) return
    await deleteHomework(courseId, hw.hwId)
    await fetchHomeworkList(courseId, t)
    alert('作业已删除')
  } catch (e) { alert('删除失败: ' + (e.message || '未知错误')) }
}

async function handlePublishHomework(hw) {
  if (!confirm(`确定要发布作业"${hw.title}"吗？发布后学生可以看到并提交。`)) return
  try {
    if (!user.value) return
    await publishHomework(courseId, hw.hwId)
    await fetchHomeworkList(courseId, t)
    alert('作业已发布')
  } catch (e) { alert('发布失败: ' + (e.message || '未知错误')) }
}

async function onQuestionBankClose() {
  showQuestionBank.value = false
  try { questionBank.value = await fetchQuestionBank(courseId) } catch {}
}
async function onQuestionBankUpdated() {
  try { questionBank.value = await fetchQuestionBank(courseId) } catch {}
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
    const result = await updateQuestionBank(courseId, editingQuestion.value.id, updateData)
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
    if (!user.value) return
    await deleteFromQuestionBank(courseId, q.id)
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
    const subs = await fetchSubmissions(courseId, hwId)
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
    await gradeSubmission(courseId, hw.hwId, sub.studentId, totalScore, feedback)
    gradingSub.value = null
    await viewSubmissions(hw.hwId)
  } catch (e) { alert('批改失败: ' + e.message) }
}

function viewAnalytics(studentId) {
  router.push(`/teacher/courses/${courseId}/analytics/${studentId}`)
}

function onHomeworkCreated() {
  showCreateHw.value = false
  fetchHomeworkList(courseId)
}

onMounted(async () => {
  if (!user.value) return
  loadAll()
})
</script>

<style>
:root {
  --bg-root: #ffffff;
  --bg-card: #ffffff;
  --bg-card-alt: #fafbfa;
  --accent: #121212;
  --accent-deep: #333333;
  --accent-soft: rgba(18, 18, 18, 0.05);
  --accent-glow: rgba(18, 18, 18, 0.1);
  --border-light: #f0f0f0;
  --border-medium: #e0e0e0;
  --border-card: rgba(186, 210, 190, 0.5);
  --text-primary: #121212;
  --text-secondary: #4a534c;
  --text-muted: #9ca3af;
  --divider: rgba(0, 0, 0, 0.05);
  --danger: #ef4444;
  --success: #059669;
  --warning: #d97706;
  --status-bg: #fbf7ee;
  --status-border: #f5ebd3;
  --status-text: #75684d;
}

body.dark {
  --bg-root: #121212;
  --bg-card: #1a1a1a;
  --bg-card-alt: #242424;
  --accent: #ffffff;
  --accent-deep: #e5e5e5;
  --accent-soft: rgba(255, 255, 255, 0.08);
  --accent-glow: rgba(255, 255, 255, 0.15);
  --border-light: #2d2d2d;
  --border-medium: #3a3a3a;
  --border-card: #2d2d2d;
  --text-primary: #e5e5e5;
  --text-secondary: #999999;
  --text-muted: #666666;
  --divider: #2d2d2d;
  --danger: #f87171;
  --warning: #fbbf24;
  --success: #34d399;
  --status-bg: rgba(255, 255, 255, 0.08);
  --status-border: rgba(255, 255, 255, 0.15);
  --status-text: #999999;
}

body.green {
  --bg-root: #f7f8f7;
  --bg-card: #ffffff;
  --bg-card-alt: #f0f3f0;
  --accent: #526e5a;
  --accent-deep: #415848;
  --accent-soft: rgba(82, 110, 90, 0.09);
  --accent-glow: rgba(82, 110, 90, 0.22);
  --border-light: rgba(0, 0, 0, 0.06);
  --border-medium: rgba(0, 0, 0, 0.1);
  --border-card: rgba(82, 110, 90, 0.2);
  --text-primary: #1e2720;
  --text-secondary: #556056;
  --text-muted: #8fa091;
  --divider: rgba(0, 0, 0, 0.05);
  --status-bg: rgba(82, 110, 90, 0.08);
  --status-border: rgba(82, 110, 90, 0.15);
  --status-text: #526e5a;
}
</style>

<style scoped>
.detail-page {
  width: 100%;
  padding: 24px 36px 28px;
  background: var(--bg-root);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
  height: 100%;
}

/* ========== 返回按钮 ========== */
.back-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 4px 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s;
}

.back-btn:hover {
  color: var(--text-primary);
}

/* ========== 课程头 ========== */
.course-header {
  margin-bottom: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.003);
}

.course-header h2 {
  margin: 0 0 12px;
  font-size: 1.2rem;
  font-weight: 400;
  color: var(--text-primary);
}

.course-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.tag {
  background: #f4f4f4;
  color: var(--text-primary);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
}

.grade-tag {
  color: var(--text-secondary);
}

/* 暗色模式下标签 */
body.dark .tag {
  background: #2d2d2d;
  color: #e5e5e5;
}

body.dark .grade-tag {
  color: #999999;
}

.code-tag {
  background: var(--status-bg);
  color: var(--status-text);
  border: 1px solid var(--status-border);
  font-family: monospace;
  font-size: 0.65rem;
  font-weight: 500;
}

.course-desc {
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: 12px;
}

/* ========== 标签栏 ========== */
.tab-bar {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 20px;
  padding-bottom: 0;
}

.tab-item {
  padding: 8px 0;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border: none;
  background: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-item:hover {
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--text-primary);
  font-weight: 600;
  border-bottom-color: var(--text-primary);
}

/* 暗色模式下标签栏 */
body.dark .tab-item.active {
  color: #ffffff;
  border-bottom-color: #ffffff;
}

.tab-count {
  font-size: 0.65rem;
  background: var(--accent-soft);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.tab-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.qb-header {
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

/* ========== 课时卡片 ========== */
.lesson-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.lesson-card:hover {
  border-color: var(--accent);
}

.lesson-header {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  cursor: pointer;
  gap: 10px;
}

.lesson-header:hover {
  background: var(--accent-soft);
}

/* 暗色模式下课时卡片 */
body.dark .lesson-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .lesson-card:hover {
  border-color: #ffffff;
}

body.dark .lesson-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.lesson-order {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 700;
  min-width: 30px;
}

.lesson-title {
  flex: 1;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.lesson-toggle {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.lesson-body {
  padding: 0 18px 16px;
  border-top: 1px solid var(--divider);
}

.lesson-desc {
  color: var(--text-secondary);
  font-size: 0.82rem;
  margin: 10px 0;
}

.plan-content {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--text-primary);
}

/* ========== 作业卡片 ========== */
.hw-card-wrapper {
  margin-bottom: 10px;
}

.hw-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s;
  cursor: pointer;
}

.hw-card:hover {
  border-color: var(--accent);
}

/* 暗色模式下作业卡片 */
body.dark .hw-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .hw-card:hover {
  border-color: #ffffff;
}

body.dark .hw-body {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

.hw-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.hw-icon {
  width: 36px;
  height: 36px;
  background: var(--bg-card-alt);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.hw-card:hover .hw-icon {
  background: var(--accent);
  color: #ffffff;
}

/* 暗色模式下图标悬停时使用深色背景 */
body.dark .hw-card:hover .hw-icon {
  background: #ffffff;
  color: #121212;
}

.hw-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.hw-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hw-title {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.hw-status-badge {
  font-size: 0.6rem;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.hw-status-badge.draft {
  background: rgba(217, 119, 6, 0.1);
  color: var(--warning);
  border: 1px solid rgba(217, 119, 6, 0.2);
}

.hw-status-badge.published {
  background: rgba(5, 150, 105, 0.1);
  color: var(--success);
  border: 1px solid rgba(5, 150, 105, 0.2);
}

/* 暗色模式下状态标签 */
body.dark .hw-status-badge.draft {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.3);
}

body.dark .hw-status-badge.published {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border-color: rgba(52, 211, 153, 0.3);
}

.hw-meta {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: monospace;
}

.hw-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.hw-deadline {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: monospace;
}

.btn-delete-hw {
  background: none;
  border: 1px solid var(--border-medium);
  color: var(--text-muted);
  font-size: 0.7rem;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn-delete-hw:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: var(--danger);
  color: var(--danger);
}

/* 暗色模式下删除按钮 */
body.dark .btn-delete-hw {
  border-color: #3a3a3a;
  color: #666666;
}

body.dark .btn-delete-hw:hover {
  background: rgba(248, 113, 113, 0.12);
  border-color: #f87171;
  color: #f87171;
}

.hw-body {
  padding: 0 18px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-top: none;
  border-radius: 0 0 12px 12px;
  margin-top: -1px;
}

.hw-question {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--divider);
  align-items: flex-start;
}

.hw-question:last-child {
  border-bottom: none;
}

.q-label {
  font-weight: 700;
  color: var(--accent);
  min-width: 24px;
}

.q-content {
  flex: 1;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.q-points {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.hw-actions {
  margin-top: 12px;
}

.hint-text {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-style: italic;
}

/* ========== 题库 ========== */
.qb-filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qb-filter-select {
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  font-size: 0.8rem;
  outline: none;
  color: var(--text-primary);
  transition: border 0.2s;
}

.qb-filter-select:focus {
  border-color: var(--accent);
}

.question-count {
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--accent-soft);
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
}

.qb-question-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  transition: all 0.3s;
}

.qb-question-card:hover {
  border-color: var(--accent);
}

/* 暗色模式下题库卡片 */
body.dark .qb-question-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .qb-question-card:hover {
  border-color: #ffffff;
}

body.dark .qb-filter-select {
  background: #1a1a1a;
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .qb-filter-select:focus {
  border-color: #ffffff;
}

body.dark .q-num {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

body.dark .q-type-badge {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

body.dark .q-source-badge.ai {
  background: rgba(139, 112, 255, 0.2);
  color: #b0a0ff;
}

body.dark .q-answer,
body.dark .q-explanation {
  background: rgba(255, 255, 255, 0.05);
  color: #999999;
}

body.dark .q-answer-label {
  color: #e5e5e5;
}

body.dark .btn-edit-q:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .btn-delete-q:hover {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.3);
  color: #f87171;
}

.qb-question-card.qb-editing {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.q-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.q-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.q-num {
  font-weight: 700;
  color: var(--accent);
  font-size: 0.9rem;
  min-width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-soft);
  border-radius: 6px;
}

.q-type-badge {
  font-size: 0.65rem;
  padding: 3px 10px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.q-points {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: monospace;
}

.q-source-badge {
  font-size: 0.55rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.q-source-badge.ai {
  background: rgba(139, 112, 255, 0.1);
  color: #8b70ff;
}

.q-content {
  color: var(--text-primary);
  font-size: 0.85rem;
  line-height: 1.6;
  margin-bottom: 8px;
}

.q-answer,
.q-explanation {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--accent-soft);
  border-radius: 6px;
}

.q-answer-label {
  font-weight: 600;
  color: var(--text-primary);
}

.q-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.btn-edit-q,
.btn-delete-q {
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  color: var(--text-muted);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-edit-q:hover {
  background: var(--accent-soft);
  border-color: var(--border-light);
  color: var(--text-primary);
}

.btn-delete-q:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.inline-edit-form {
  padding: 8px 0;
}

.inline-edit-form .form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.inline-edit-form .q-type-select,
.inline-edit-form .points-input,
.inline-edit-form .q-content-input,
.inline-edit-form .explanation-input,
.inline-edit-form .option-row input,
.inline-edit-form .answer-row select,
.inline-edit-form .answer-row textarea {
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  padding: 8px;
  font-size: 0.85rem;
  color: var(--text-primary);
  transition: border 0.2s;
}

.inline-edit-form .q-type-select:focus,
.inline-edit-form .points-input:focus,
.inline-edit-form .q-content-input:focus,
.inline-edit-form .explanation-input:focus,
.inline-edit-form .option-row input:focus,
.inline-edit-form .answer-row select:focus,
.inline-edit-form .answer-row textarea:focus {
  border-color: var(--accent);
  outline: none;
}

/* 暗色模式下编辑表单 */
body.dark .inline-edit-form .q-type-select,
body.dark .inline-edit-form .points-input,
body.dark .inline-edit-form .q-content-input,
body.dark .inline-edit-form .explanation-input,
body.dark .inline-edit-form .option-row input,
body.dark .inline-edit-form .answer-row select,
body.dark .inline-edit-form .answer-row textarea {
  background: #242424;
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .inline-edit-form .q-type-select:focus,
body.dark .inline-edit-form .points-input:focus,
body.dark .inline-edit-form .q-content-input:focus,
body.dark .inline-edit-form .explanation-input:focus,
body.dark .inline-edit-form .option-row input:focus,
body.dark .inline-edit-form .answer-row select:focus,
body.dark .inline-edit-form .answer-row textarea:focus {
  border-color: #ffffff;
}

body.dark .inline-edit-form .options-section {
  background: #121212;
}

.inline-edit-form .q-type-select {
  flex: 1;
  min-width: 120px;
}

.inline-edit-form .points-input {
  width: 80px;
  text-align: center;
}

.inline-edit-form .q-content-input,
.inline-edit-form .explanation-input {
  width: 100%;
  resize: vertical;
  box-sizing: border-box;
  min-height: 80px;
}

.inline-edit-form .options-section {
  margin: 12px 0;
  padding: 12px;
  background: var(--accent-soft);
  border-radius: 8px;
}

.inline-edit-form .option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.inline-edit-form .option-row:last-child {
  margin-bottom: 0;
}

.inline-edit-form .option-row span {
  min-width: 24px;
  font-weight: 600;
  color: var(--accent);
  font-size: 0.85rem;
}

.inline-edit-form .option-row input {
  flex: 1;
}

.inline-edit-form .option-row button {
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.inline-edit-form .option-row button:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.btn-add-opt {
  background: none;
  border: 1px dashed var(--border-medium);
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 8px;
  transition: all 0.2s;
}

.btn-add-opt:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}

.inline-edit-form .answer-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
}

.inline-edit-form .answer-row label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  min-width: 70px;
  padding-top: 8px;
}

.inline-edit-form .answer-row select,
.inline-edit-form .answer-row textarea {
  flex: 1;
}

.inline-edit-form .answer-row textarea {
  min-height: 60px;
}

.inline-edit-form .form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--divider);
}

/* ========== 提交面板 ========== */
.submissions-panel {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: 10px;
  border: 1px solid var(--border-light);
}

.submissions-panel h4 {
  margin: 0 0 12px;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.sub-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--divider);
}

.sub-row:last-child {
  border-bottom: none;
}

.sub-student {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--text-primary);
  flex: 1;
}

.sub-status {
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.sub-status.submitted {
  background: rgba(217, 119, 6, 0.1);
  color: var(--warning);
}

.sub-status.graded {
  background: rgba(5, 150, 105, 0.1);
  color: var(--success);
}

/* 暗色模式下提交面板 */
body.dark .submissions-panel {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .submissions-panel h4 {
  color: #e5e5e5;
}

body.dark .sub-row {
  border-color: #2d2d2d;
}

body.dark .sub-student {
  color: #e5e5e5;
}

body.dark .sub-status.submitted {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

body.dark .sub-status.graded {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

/* ========== 学生表格 ========== */
.students-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-light);
}

.students-table th,
.students-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--divider);
  font-size: 0.85rem;
  color: var(--text-primary);
}

.students-table th {
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--accent-soft);
}

/* 暗色模式下学生表格 */
body.dark .students-table {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .students-table th {
  background: rgba(255, 255, 255, 0.05);
  color: #999999;
}

body.dark .students-table td {
  border-color: #2d2d2d;
  color: #e5e5e5;
}

/* ========== 批改对话框 ========== */
.grade-question {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--divider);
}

.grade-q-label {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.grade-answer {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin: 0 0 8px;
  background: var(--accent-soft);
  padding: 8px;
  border-radius: 6px;
}

.grade-input-row {
  display: flex;
  gap: 8px;
}

.grade-input-row input {
  flex: 1;
  padding: 6px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  font-size: 0.82rem;
  outline: none;
  color: var(--text-primary);
  transition: border 0.2s;
}

.grade-input-row input:focus {
  border-color: var(--accent);
}

.grade-input-row input:first-child {
  max-width: 80px;
}

/* ========== 通用对话框 ========== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.dialog-card {
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 16px;
  padding: 32px;
  width: 520px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.dialog-card h3 {
  margin: 0 0 20px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* 暗色模式下对话框 */
body.dark .dialog-card {
  background: #1a1a1a;
  border-color: #3a3a3a;
}

body.dark .dialog-card h3 {
  color: #e5e5e5;
}

body.dark .grade-input-row input {
  background: #242424;
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .grade-input-row input:focus {
  border-color: #ffffff;
}

body.dark .grade-answer {
  background: #242424;
  color: #999999;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* ========== 按钮 ========== */
.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary:not(:disabled):hover {
  background: var(--accent-deep);
}

.btn-secondary {
  padding: 8px 20px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--accent-soft);
}

/* 暗色模式下按钮 */
body.dark .btn-primary {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-primary:hover {
  background: #e5e5e5;
}

body.dark .btn-secondary {
  background: #2d2d2d;
  border-color: #3a3a3a;
  color: #e5e5e5;
}

body.dark .btn-secondary:hover {
  background: #3a3a3a;
  border-color: #ffffff;
}

body.dark .btn-small {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-small:hover {
  background: #e5e5e5;
}

body.dark .btn-small.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #e5e5e5;
}

body.dark .btn-small.secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-small {
  padding: 4px 12px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-small:hover {
  background: var(--accent-deep);
}

.btn-small.secondary {
  background: var(--accent-soft);
  color: var(--text-primary);
}

.btn-small.secondary:hover {
  background: var(--border-light);
}

/* ========== 空状态 ========== */
.empty-hint,
.loading-hint {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px dashed var(--border-medium);
}

/* 暗色模式下空状态 */
body.dark .empty-hint,
body.dark .loading-hint {
  background: #1a1a1a;
  border-color: #3a3a3a;
  color: #666666;
}

/* 暗色模式下课程头部 */
body.dark .course-header {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .course-header h2 {
  color: #e5e5e5;
}

body.dark .course-desc {
  color: #999999;
}

body.dark .code-tag {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  color: #999999;
}
</style>