<template>
<!-- ====== MAIN AREA ====== -->
<div class="main-area">

<!-- ====== LEFT: SUBMISSION LIST ====== -->
<aside class="panel panel-left" :class="{ collapsed: panelCollapsed.left }">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
  <button class="panel-toggle" @click="panelCollapsed.left = !panelCollapsed.left" :title="panelCollapsed.left ? '展开' : '收起'">
    <svg viewBox="0 0 16 16" width="14" height="14"><path d="M10 4L6 8l4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>

  <!-- Course selector -->
  <div class="pl-header">
    <span class="pl-title">课程作业</span>
    <span class="pl-badge">{{ totalSubmissions }} 份提交</span>
  </div>
  <div class="pl-courses">
    <select v-model="selectedCourseId" class="course-select" @change="onCourseChange">
      <option value="">选择课程...</option>
      <option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option>
    </select>
  </div>
  <div v-if="selectedCourseId" class="pl-homework-list">
    <div v-for="hw in homeworkItems" :key="hw.hwId"
      class="homework-row" :class="{ active: selectedHwId === hw.hwId }"
      @click="selectHomework(hw)">
      <div class="hw-icon">
        <svg viewBox="0 0 16 16" width="14" height="14"><rect x="2" y="1" width="12" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M5 5h6M5 8h6M5 11h3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
      </div>
      <div class="hw-body">
        <div class="hw-title">{{ hw.title }}</div>
        <div class="hw-meta">{{ hw.submissionCount || 0 }} 份提交 · {{ hw.gradedCount || 0 }} 已批</div>
      </div>
      <div class="hw-status" :class="{ done: hw.allGraded }">
        {{ hw.allGraded ? '✓' : hw.pendingCount + '待批' }}
      </div>
    </div>
    <div v-if="homeworkItems.length === 0" class="pl-empty">该课程暂无作业</div>
  </div>
  <div v-else class="pl-empty" style="flex:1; display:flex; align-items:center; justify-content:center;">
    请先选择课程
  </div>

  <!-- Submissions list for selected homework -->
  <template v-if="selectedHwId">
    <div class="pl-search">
      <svg viewBox="0 0 20 20" class="pl-search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
      <input v-model="searchQuery" placeholder="搜索学生..." />
    </div>
    <div class="pl-filters">
      <span class="pl-chip" :class="{ on: statusFilter === 'all' }" @click="statusFilter = 'all'">全部</span>
      <span class="pl-chip" :class="{ on: statusFilter === 'pending' }" @click="statusFilter = 'pending'">待批改</span>
      <span class="pl-chip" :class="{ on: statusFilter === 'graded' }" @click="statusFilter = 'graded'">已批改</span>
    </div>
    <div class="pl-list">
      <div v-for="(sub, si) in filteredSubmissions" :key="sub.id"
        class="submission-row" :class="{ active: activeId === sub.id }"
        @click="selectSubmission(sub)" :style="{ animationDelay: si * 0.03 + 's' }">
        <div class="sr-rank">{{ si + 1 }}</div>
        <div class="sr-avatar">{{ (sub.studentName || sub.studentId || '?')[0] }}</div>
        <div class="sr-body">
          <div class="sr-name">{{ sub.studentName || sub.studentId }}</div>
          <div class="sr-desc">{{ sub.status === 'graded' ? '已批改' : '待批改' }}</div>
        </div>
        <div class="sr-tail">
          <span v-if="sub.status === 'graded'" class="sr-score">{{ sub.score }}</span>
          <span v-else class="sr-dot"></span>
        </div>
      </div>
      <div v-if="filteredSubmissions.length === 0" class="pl-empty">暂无匹配项</div>
    </div>
    <div class="pl-footer">
      <div class="pl-stats-row">
        <div class="pl-stat">
          <div class="pl-stat-val">{{ submissions.length }}</div>
          <div class="pl-stat-lbl">总提交</div>
        </div>
        <div class="pl-stat">
          <div class="pl-stat-val">{{ gradedCount }}</div>
          <div class="pl-stat-lbl">已批改</div>
        </div>
        <div class="pl-stat">
          <div class="pl-stat-val">{{ avgScore }}</div>
          <div class="pl-stat-lbl">平均分</div>
        </div>
      </div>
      <button class="batch-btn" :disabled="ungradedCount === 0" @click="batchGradeAll">
        一键批改 {{ ungradedCount }} 份
      </button>
    </div>
  </template>
</aside>

<!-- ====== CENTER: QUESTION VIEWER ====== -->
<section class="panel panel-center">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>

  <div v-if="!activeSubmission" class="center-empty">
    <div class="empty-icon-wrap">
      <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
    </div>
    <p class="empty-title">选择左侧作业</p>
    <p class="empty-desc">开始 AI 辅助批改</p>
  </div>

  <div v-else class="center-scroll">
    <!-- Student info -->
    <div class="student-bar">
      <div class="sb-left">
        <div class="sb-avatar">{{ (activeSubmission.studentName || activeSubmission.studentId || '?')[0] }}</div>
        <div>
          <div class="sb-name">{{ activeSubmission.studentName || activeSubmission.studentId }}</div>
          <div class="sb-meta">{{ activeSubmission.submittedAt }}</div>
        </div>
      </div>
      <span class="sb-status" :class="{ done: activeSubmission.status === 'graded' }">
        {{ activeSubmission.status === 'graded' ? '✓ 已批改' : '待批改' }}
      </span>
    </div>

    <!-- Question type tabs -->
    <div class="q-tabs">
      <span class="q-tab" :class="{ on: questionType === 'all' }" @click="questionType = 'all'">全部</span>
      <span class="q-tab" :class="{ on: questionType === 'subjective' }" @click="questionType = 'subjective'">主观题</span>
      <span class="q-tab" :class="{ on: questionType === 'objective' }" @click="questionType = 'objective'">客观题</span>
      <span class="q-tab-summary">{{ displayQuestions.length }} 题</span>
    </div>

    <!-- Question cards -->
    <div class="q-list">
      <div v-for="(q, qi) in displayQuestions" :key="q.id" class="q-card" :class="{ graded: q.graded, 'q-obj': q.objType, 'q-sub': !q.objType }">
        <div class="q-inner">
          <!-- Header -->
          <div class="q-top">
            <span class="q-idx">{{ qi + 1 }}</span>
            <span class="q-kind">{{ q.typeLabel }}</span>
            <span class="q-pts">{{ q.maxScore }} 分</span>
          </div>

          <!-- Stem -->
          <div class="q-stem">{{ q.stem }}</div>

          <!-- 客观题: 选择题 -->
          <div v-if="q.objType === 'choice'" class="q-opts">
            <div v-for="opt in q.options" :key="opt.key" class="q-opt"
              :class="{ correct: q.graded && opt.key === q.answerKey, wrong: q.graded && opt.key === q.studentPick && opt.key !== q.answerKey, picked: opt.key === q.studentPick }">
              <span class="q-opt-letter">{{ opt.key }}</span>
              <span class="q-opt-text">{{ opt.text }}</span>
              <span v-if="q.graded && opt.key === q.studentPick && opt.key !== q.answerKey" class="q-opt-badge">学生答选 (未得分)</span>
              <span v-if="q.graded && opt.key === q.studentPick && opt.key === q.answerKey" class="q-opt-badge correct">回答正确 (+{{ q.maxScore }})</span>
            </div>
          </div>

          <!-- 客观题: 判断题 -->
          <div v-if="q.objType === 'tf'" class="q-tf">
            <span class="q-tf-label">学生答案</span>
            <span class="q-tf-val" :class="{ 'is-correct': q.graded && q.studentPick === q.answerKey, 'is-wrong': q.graded && q.studentPick !== q.answerKey }">{{ q.studentPick }}</span>
            <span v-if="q.graded && q.studentPick !== q.answerKey" class="q-tf-ref">正确答案：{{ q.answerKey }}</span>
          </div>

          <!-- 客观题: 填空题 -->
          <div v-if="q.objType === 'fill'" class="q-fill">
            <span class="q-fill-label">学生答案</span>
            <code class="q-fill-val" :class="{ 'is-correct': q.graded && q.studentPick === q.answerKey, 'is-wrong': q.graded && q.studentPick !== q.answerKey }">{{ q.studentPick || '(空)' }}</code>
            <span v-if="q.graded && q.studentPick !== q.answerKey" class="q-fill-ref">参考答案：{{ q.answerKey }}</span>
          </div>

          <!-- 客观题得分展示 -->
          <div v-if="q.objType && q.graded" class="q-obj-score">
            得分：{{ q.studentScore }}/{{ q.maxScore }} <span v-if="q.answerKey">| 正确选项：{{ q.answerKey }}</span>
          </div>

          <!-- 主观题: 学生作答 -->
          <div v-if="!q.objType" class="q-answer-area">
            <div class="q-answer-box">
              <div class="q-answer-label">学生作答</div>
              <p class="q-answer-text">{{ q.studentAnswer }}</p>
            </div>
            <div v-if="q.referenceAnswer" class="q-ref-box">
              <div class="q-ref-label">参考答案</div>
              <p class="q-ref-text">{{ q.referenceAnswer }}</p>
            </div>
            <!-- 手动批改输入框 (pending 状态) -->
            <div v-if="activeSubmission.status !== 'graded' && manualGrades[q.id] !== undefined" class="manual-grade-input">
              <div class="manual-grade-row">
                <label class="manual-grade-label">得分</label>
                <input type="number" class="manual-grade-score" v-model.number="manualGrades[q.id].score" :min="0" :max="q.maxScore" :placeholder="'0-' + q.maxScore" />
                <span class="manual-grade-max">/ {{ q.maxScore }}</span>
                <button class="ai-grade-q-btn" @click="aiGradeSingleQuestion(q)" :disabled="aiGradingQuestionIds.has(q.id)" :title="aiGradingQuestionIds.has(q.id) ? 'AI 评阅中…' : 'AI 智能评分'">
                  <span v-if="aiGradingQuestionIds.has(q.id)" class="grade-spinner"></span>
                  <span v-else>🤖</span>
                  {{ aiGradingQuestionIds.has(q.id) ? '评阅中…' : 'AI 评分' }}
                </button>
              </div>
              <div class="manual-grade-row">
                <label class="manual-grade-label">评语</label>
                <textarea class="manual-grade-comment" v-model="manualGrades[q.id].comment" rows="2" placeholder="输入评语（可选）"></textarea>
              </div>
            </div>
          </div>

          <!-- 评分结果 (主观题) -->
          <div v-if="!q.objType && q.graded" class="q-footer">
            <span class="q-footer-score" :class="{ full: q.studentScore === q.maxScore, half: q.studentScore > 0 && q.studentScore < q.maxScore, zero: q.studentScore === 0 }">{{ q.studentScore }}/{{ q.maxScore }}</span>
            <span class="q-footer-note">{{ q.comment }}</span>
          </div>
        </div>
      </div>
      <div v-if="displayQuestions.length === 0" class="q-empty">该分类下暂无题目</div>
    </div>
  </div>
</section>

<!-- ====== RIGHT: GRADING DASHBOARD ====== -->
<aside class="panel panel-right" :class="{ collapsed: panelCollapsed.right }">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
  <button class="panel-toggle right-toggle" @click="panelCollapsed.right = !panelCollapsed.right" :title="panelCollapsed.right ? '展开' : '收起'">
    <svg viewBox="0 0 16 16" width="14" height="14"><path d="M6 4l4 4-4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>

  <div v-if="!activeSubmission" class="pr-empty">
    <svg viewBox="0 0 20 20" width="28" height="28"><circle cx="10" cy="10" r="7"/><path d="M10 6v5M10 13v1"/></svg>
    <p>选择作业后<br>此处展示批改仪表盘</p>
  </div>

  <div v-else class="pr-scroll">
    <!-- Pending state -->
    <template v-if="activeSubmission.status !== 'graded'">
      <div class="pr-section">
        <div class="pr-sec-title">逐题评分</div>
        <p class="grade-intro">在左侧题目区域点击 <b>🤖 AI 评分</b> 为主观题智能打分，或手动输入得分和评语。</p>
        <div class="grade-summary" v-if="gradedQuestionCount > 0">
          <span class="grade-summary-icon">✓</span>
          已评分 {{ gradedQuestionCount }} / {{ subjectiveQuestionCount }} 道主观题
        </div>
      </div>
      <div class="pr-section">
        <button class="grade-start finish-grade-btn" @click="submitManualGrade(activeSubmission)" :disabled="manualGradingInProgress || gradedQuestionCount === 0">
          <span v-if="manualGradingInProgress" class="grade-spinner"></span>
          {{ manualGradingInProgress ? '提交中…' : '完成批改' }}
        </button>
        <p class="grade-hint" v-if="gradedQuestionCount === 0">请先为主观题评分</p>
      </div>
      <div class="pr-section">
        <div class="pr-sec-title">AI 整体批改</div>
        <p class="grade-intro">AI 助教将对客观题自动判分，主观题根据评分标准智能评阅，并生成多维分析报告。</p>
        <button class="grade-start" @click="gradeSubmission(activeSubmission)" :disabled="gradingInProgress">
          <span v-if="gradingInProgress" class="grade-spinner"></span>
          {{ gradingInProgress ? 'AI 正在批改…' : '开始 AI 批改' }}
        </button>
      </div>
    </template>

    <!-- Graded dashboard -->
    <template v-if="activeSubmission.status === 'graded'">
      <!-- Score distribution histogram -->
      <div class="pr-section">
        <div class="pr-sec-title">成绩分布直方图</div>
        <div class="histogram">
          <div v-for="bar in scoreDist" :key="bar.range" class="hist-col">
            <div class="hist-bar-wrap">
              <div class="hist-bar-spacer" :style="{ flex: (100 - bar.pct) + ' 0 0' }"></div>
              <div class="hist-bar" :style="{ flex: bar.pct + ' 0 0' }" :class="{ highlight: bar.isCurrent }"></div>
            </div>
            <div class="hist-label">{{ bar.range }}</div>
          </div>
        </div>
        <div class="hist-legend">
          <span class="hist-avg">班级均分 {{ classAvg }} · 最高 {{ classMax }} · 最低 {{ classMin }}</span>
        </div>
      </div>

      <div class="pr-divider"></div>

      <!-- Notebook review -->
      <div class="pr-section">
        <div class="pr-sec-title">综合学术评语</div>
        <div class="notebook">
          <p class="notebook-text">{{ typeof activeSubmission.feedback === 'object' ? (activeSubmission.feedback?.feedback || '暂无综合评语') : activeSubmission.feedback }}</p>
        </div>
      </div>

      <!-- Export -->
      <div class="pr-section">
        <div class="export-row">
          <button class="exp-btn" @click="exportReport('pdf')">
            <svg viewBox="0 0 20 20" width="13" height="13"><path d="M5 3v14l5-3 5 3V3a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1z"/></svg>导出 PDF
          </button>
          <button class="exp-btn" @click="exportReport('excel')">
            <svg viewBox="0 0 20 20" width="13" height="13"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>导出 Excel
          </button>
        </div>
      </div>
    </template>
  </div>
</aside>

</div><!-- end main-area -->
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useCourse } from '../../composables/useCourse.js'
import { useRouter } from 'vue-router'

// ====== User ======
const USER_KEY = 'nanobot-webui.user'
const { user, logout: authLogout } = useAuth()
const { connect: connectGateway, connected, getToken, sendAiGradeQuestion, sendAiGradeSubmission } = useGateway()
const router = useRouter()
function loadUser() { try { const r = localStorage.getItem(USER_KEY); if (!r) return null; const p = JSON.parse(r); return p?.role && p?.userId ? p : null } catch { return null } }
function handleLogout() { authLogout(); router.push('/login') }

// ====== Theme ======
const isDark = ref(false)
function toggleTheme() { isDark.value = !isDark.value; document.body.classList.toggle('dark', isDark.value) }
function goToLessonPlan() { router.push('/teacher/lesson-plan') }
function goToAnalytics() { router.push('/teacher/analytics') }

// ====== Course API ======
const { courses, fetchCourses: apiFetchCourses, fetchHomeworkList: apiFetchHomeworkList, fetchSubmissions: apiFetchSubmissions, fetchHomeworkDetail: apiFetchHomeworkDetail, gradeSubmission: apiGrade, aiGradeSubmission: apiAiGrade, aiGradeQuestion: apiAiGradeQuestion } = useCourse()
const selectedCourseId = ref('')
const selectedHwId = ref('')
const homeworkItems = ref([])
const currentHomework = ref(null)

async function loadCourses() {
  const saved = loadUser()
  if (!saved) return
  try {
    await apiFetchCourses(saved.role, saved.userId, getToken())
  } catch (e) {
    console.error('Failed to load courses:', e)
  }
}

async function onCourseChange() {
  selectedHwId.value = ''
  homeworkItems.value = []
  submissions.value = []
  currentHomework.value = null
  if (!selectedCourseId.value) return
  try {
    const hwList = await apiFetchHomeworkList(selectedCourseId.value, getToken())
    homeworkItems.value = hwList || []
  } catch (e) {
    console.error('Failed to load homework:', e)
  }
}

async function selectHomework(hw) {
  selectedHwId.value = hw.hwId
  activeId.value = null
  submissions.value = []
  currentHomework.value = null
  try {
    // Load homework detail
    const hwDetail = await apiFetchHomeworkDetail(selectedCourseId.value, hw.hwId, getToken())
    currentHomework.value = hwDetail

    // Load submissions (already normalized by useCourse)
    const subs = await apiFetchSubmissions(selectedCourseId.value, hw.hwId, getToken())
    submissions.value = (subs || []).map(s => ({
      ...s,
      id: s.id || `${s.hwId}-${s.studentId}`,
    }))

    // Update homework stats
    hw.submissionCount = submissions.value.length
    hw.gradedCount = submissions.value.filter(s => s.status === 'graded').length
    hw.pendingCount = submissions.value.filter(s => s.status !== 'graded').length
    hw.allGraded = hw.submissionCount > 0 && hw.pendingCount === 0
  } catch (e) {
    console.error('Failed to load homework detail:', e)
  }
}

// ====== State ======
const submissions = ref([])
const activeId = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const questionType = ref('all')
const gradingInProgress = ref(false)
const manualGradingInProgress = ref(false)
const aiGradingQuestionIds = ref(new Set())
const gradeOptions = reactive({ detailed: true, rubric: true, suggestions: true })
const manualGrades = reactive({})  // { [qid]: { score: number, comment: string } }

// Auto-save grades to localStorage on change
let _saveTimer = null
watch(manualGrades, () => {
  if (_saveTimer) clearTimeout(_saveTimer)
  _saveTimer = setTimeout(_saveGrades, 500)
}, { deep: true })

// Stats
const totalSubmissions = computed(() => submissions.value.length)
const ungradedCount = computed(() => submissions.value.filter(s => s.status !== 'graded').length)
const gradedCount = computed(() => submissions.value.filter(s => s.status === 'graded').length)
const avgScore = computed(() => {
  const g = submissions.value.filter(s => s.status === 'graded')
  return g.length ? Math.round(g.reduce((a, b) => a + (b.score || 0), 0) / g.length) : '--'
})

const activeSubmission = computed(() => submissions.value.find(s => s.id === activeId.value) || null)

// Map API question type → template objType
function _mapObjType(type) {
  if (type === 'choice') return 'choice'
  if (type === 'true_false') return 'tf'
  if (type === 'fill' || type === 'blank') return 'fill'
  return null // subjective
}

const TYPE_LABELS = { choice: '选择题', tf: '判断题', fill: '填空题', short_answer: '简答题' }

// Parse questions from homework or submission
const displayQuestions = computed(() => {
  if (!activeSubmission.value) return []

  // Try to get questions from homework detail
  let questions = []
  if (currentHomework.value?.questions) {
    questions = currentHomework.value.questions.map((q, idx) => ({
      id: q.id,
      stem: q.content || q.stem || `题目 ${idx + 1}`,
      maxScore: q.points ?? q.maxScore ?? 10,
      objType: _mapObjType(q.type || q.objType),
      typeLabel: TYPE_LABELS[q.type || q.objType] || '主观题',
      options: q.options || [],
      answerKey: q.answer || q.answerKey || '',
      referenceAnswer: q.referenceAnswer || q.reference_answer || '',
    }))
  } else if (activeSubmission.value.answers) {
    // Fallback: convert answers to question format
    const answers = activeSubmission.value.answers
    questions = Object.entries(answers).map(([qid, answer], idx) => ({
      id: qid,
      stem: `题目 ${idx + 1}`,
      studentAnswer: typeof answer === 'string' ? answer : JSON.stringify(answer),
      maxScore: 10,
      objType: null,
      typeLabel: '主观题',
      graded: activeSubmission.value.status === 'graded',
      studentScore: 0,
      comment: '',
    }))
  }

  // Enrich with student answers from submission
  if (activeSubmission.value.answers && questions.length > 0) {
    const answers = activeSubmission.value.answers
    questions = questions.map((q, idx) => {
      const studentAns = answers[q.id] || answers[`q${idx + 1}`] || answers[idx] || ''
      const isObj = !!q.objType
      // Auto-grade objective questions based on answer key
      let graded = activeSubmission.value.status === 'graded'
      let studentScore = q.studentScore ?? 0
      let comment = q.comment ?? ''
      if (isObj && q.answerKey) {
        graded = true
        if (q.objType === 'choice' || q.objType === 'tf') {
          studentScore = studentAns === q.answerKey ? q.maxScore : 0
          comment = studentScore > 0 ? '回答正确' : '回答错误'
        } else if (q.objType === 'fill') {
          const a = (studentAns || '').trim()
          const b = (q.answerKey || '').trim()
          if (!a) { studentScore = 0; comment = '未作答' }
          else if (a === b) { studentScore = q.maxScore; comment = '回答正确' }
          else if (b.includes(a) || a.includes(b)) { studentScore = Math.ceil(q.maxScore * 0.5); comment = '部分正确' }
          else { studentScore = 0; comment = '回答错误' }
        }
      }
      return {
        ...q,
        studentAnswer: typeof studentAns === 'string' ? studentAns : JSON.stringify(studentAns),
        studentPick: studentAns,
        graded,
        studentScore,
        comment,
      }
    })
  }

  // Merge graded results from submission feedback
  if (activeSubmission.value.status === 'graded') {
    const fb = activeSubmission.value.feedback
    const gradedQs = fb?.questions || (Array.isArray(fb) ? fb : [])
    if (gradedQs.length > 0) {
      const qMap = Object.fromEntries(gradedQs.map(gq => [gq.id, gq]))
      questions = questions.map(q => ({
        ...q,
        graded: true,
        studentScore: qMap[q.id]?.studentScore ?? q.studentScore ?? 0,
        comment: qMap[q.id]?.comment ?? q.comment ?? '',
      }))
    }
  }

  if (questionType.value === 'subjective') questions = questions.filter(q => !q.objType)
  if (questionType.value === 'objective') questions = questions.filter(q => q.objType)
  return questions
})

// Count questions that have been graded (via AI or manual)
const subjectiveQuestionCount = computed(() => displayQuestions.value.filter(q => !q.objType).length)
const gradedQuestionCount = computed(() => {
  return Object.keys(manualGrades).filter(qid => {
    const g = manualGrades[qid]
    return g && (g.score > 0 || g.comment)
  }).length
})

const filteredSubmissions = computed(() => {
  let list = submissions.value
  if (statusFilter.value === 'pending') list = list.filter(s => s.status !== 'graded')
  if (statusFilter.value === 'graded') list = list.filter(s => s.status === 'graded')
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(s =>
      (s.studentName || '').toLowerCase().includes(q) ||
      (s.studentId || '').toLowerCase().includes(q)
    )
  }
  return list
})

// Calculate real score distribution from submissions
const scoreDist = computed(() => {
  const ranges = ['0-59', '60-69', '70-79', '80-89', '90-100']
  const counts = [0, 0, 0, 0, 0]
  const gradedSubs = submissions.value.filter(s => s.status === 'graded')
  gradedSubs.forEach(s => {
    const score = s.score || 0
    if (score < 60) counts[0]++
    else if (score < 70) counts[1]++
    else if (score < 80) counts[2]++
    else if (score < 90) counts[3]++
    else counts[4]++
  })
  const maxCount = Math.max(...counts, 1)
  const curScore = activeSubmission.value?.score || 0
  return ranges.map((r, i) => {
    const [lo, hi] = r.split('-').map(Number)
    return { range: r, count: counts[i], pct: Math.round((counts[i] / maxCount) * 100), isCurrent: curScore >= lo && curScore <= hi }
  })
})

const classAvg = computed(() => avgScore.value)
const classMax = computed(() => {
  const g = submissions.value.filter(s => s.status === 'graded')
  return g.length ? Math.max(...g.map(s => s.score || 0)) : '--'
})
const classMin = computed(() => {
  const g = submissions.value.filter(s => s.status === 'graded')
  return g.length ? Math.min(...g.map(s => s.score || 0)) : '--'
})

// ====== Panel collapse ======
const panelCollapsed = reactive({ left: false, right: false })

// ====== Grade persistence (localStorage) ======
const GRADE_STORAGE_KEY = 'nanobot-webui.manualGrades'

function _saveGrades() {
  try {
    const key = `${GRADE_STORAGE_KEY}.${selectedCourseId.value}.${selectedHwId.value}.${activeId.value}`
    localStorage.setItem(key, JSON.stringify(manualGrades))
  } catch {}
}

function _loadGrades(subId) {
  try {
    const key = `${GRADE_STORAGE_KEY}.${selectedCourseId.value}.${selectedHwId.value}.${subId}`
    const saved = localStorage.getItem(key)
    return saved ? JSON.parse(saved) : null
  } catch { return null }
}

// ====== Actions ======
function selectSubmission(sub) {
  activeId.value = sub.id
  questionType.value = 'all'
  // Reset manual grades for pending submissions
  Object.keys(manualGrades).forEach(k => delete manualGrades[k])
  if (sub.status !== 'graded' && currentHomework.value?.questions) {
    const saved = _loadGrades(sub.id)
    currentHomework.value.questions.forEach(q => {
      if (!['choice', 'true_false', 'fill', 'blank'].includes(q.type || q.objType)) {
        const s = saved?.[q.id]
        manualGrades[q.id] = s ? { score: s.score || 0, comment: s.comment || '' } : { score: 0, comment: '' }
      }
    })
  }
}
function autoGradeObj(q) {
  if (q.objType === 'choice' || q.objType === 'tf') return q.studentPick === q.answerKey ? q.maxScore : 0
  if (q.objType === 'fill') { const a = (q.studentPick||'').trim(), b = (q.answerKey||'').trim(); if (!a) return 0; if (a === b) return q.maxScore; if (b.includes(a)||a.includes(b)) return Math.ceil(q.maxScore*0.5); return 0 }
  return 0
}
function autoGradeSub(q) { const l = (q.studentAnswer||'').length; if (l > 150) return { score: Math.round(q.maxScore*0.9), comment:'回答详细，条理清晰。' }; if (l > 80) return { score: Math.round(q.maxScore*0.72), comment:'回答基本完整，可进一步展开。' }; if (l > 30) return { score: Math.round(q.maxScore*0.5), comment:'回答偏简略，建议展开论述。' }; return { score: Math.round(q.maxScore*0.3), comment:'回答过于简略，需充分展开。' } }

async function gradeSubmission(sub) {
  // AI grade all subjective questions in parallel, fill into manualGrades
  const subjectiveQuestions = displayQuestions.value.filter(q => !q.objType)
  if (subjectiveQuestions.length === 0) {
    alert('没有主观题需要 AI 批改')
    return
  }
  gradingInProgress.value = true
  // Show loading on each question button
  subjectiveQuestions.forEach(q => aiGradingQuestionIds.value.add(q.id))
  try {
    const promises = subjectiveQuestions.map(q =>
      sendAiGradeQuestion({
        content: q.stem,
        maxScore: q.maxScore,
        referenceAnswer: q.referenceAnswer || '',
        studentAnswer: q.studentAnswer || '',
      }).then(result => ({ qid: q.id, ...result }))
        .catch(e => { console.error(`AI grade ${q.id} failed:`, e); return null })
        .finally(() => aiGradingQuestionIds.value.delete(q.id))
    )
    const results = await Promise.all(promises)
    for (const r of results) {
      if (r && manualGrades[r.qid]) {
        manualGrades[r.qid].score = r.score ?? 0
        manualGrades[r.qid].comment = r.comment ?? ''
      }
    }
  } catch (e) {
    console.error('AI grading failed:', e)
    alert('AI 批改失败: ' + (e.message || '未知错误'))
  } finally {
    gradingInProgress.value = false
  }
}

async function batchGradeAll() {
  // AI grade all subjective questions for all ungraded students, fill into localStorage
  const pending = submissions.value.filter(s => s.status !== 'graded')
  if (!pending.length) return
  const hwQuestions = currentHomework.value?.questions || []
  const subjectiveQs = hwQuestions.filter(q => {
    const t = (q.type || q.objType || '').toLowerCase()
    return t !== 'choice' && t !== 'true_false'
  })
  if (subjectiveQs.length === 0) {
    alert('没有主观题需要 AI 批改')
    return
  }
  gradingInProgress.value = true
  try {
    // Build all promises: each student x each subjective question
    const allPromises = []
    for (const sub of pending) {
      const answers = sub.answers || {}
      for (const q of subjectiveQs) {
        allPromises.push(
          sendAiGradeQuestion({
            content: q.content || q.stem || '',
            maxScore: q.points ?? q.maxScore ?? 10,
            referenceAnswer: q.referenceAnswer || q.reference_answer || '',
            studentAnswer: answers[q.id] || '',
          }).then(r => ({ subId: sub.id, qid: q.id, ...r }))
            .catch(e => { console.error(`AI grade ${sub.studentId}/${q.id} failed:`, e); return null })
        )
      }
    }
    const results = await Promise.all(allPromises)
    // Group results by submission
    const bySub = {}
    for (const r of results) {
      if (!r) continue
      if (!bySub[r.subId]) bySub[r.subId] = {}
      bySub[r.subId][r.qid] = { score: r.score ?? 0, comment: r.comment ?? '' }
    }
    // Save to localStorage (active submission fills manualGrades directly)
    for (const sub of pending) {
      const grades = bySub[sub.id]
      if (!grades) continue
      if (sub.id === activeId.value) {
        // Fill into manualGrades for current active submission
        for (const [qid, g] of Object.entries(grades)) {
          manualGrades[qid] = { score: g.score, comment: g.comment }
        }
      } else {
        // Save to localStorage for other submissions
        const key = `${GRADE_STORAGE_KEY}.${selectedCourseId.value}.${selectedHwId.value}.${sub.id}`
        localStorage.setItem(key, JSON.stringify(grades))
      }
    }
  } catch (e) {
    console.error('Batch AI grading failed:', e)
    alert('批量 AI 批改失败: ' + (e.message || '未知错误'))
  } finally {
    gradingInProgress.value = false
  }
}

async function submitManualGrade(sub) {
  manualGradingInProgress.value = true
  try {
    const saved = loadUser()
    if (!saved) throw new Error('未登录')
    // Collect per-question grades
    const questions = Object.entries(manualGrades).map(([qid, g]) => ({
      id: qid, score: g.score || 0, comment: g.comment || '',
    }))
    if (questions.length === 0) { alert('请至少为一道主观题评分'); return }
    const result = await apiGrade(selectedCourseId.value, selectedHwId.value, sub.studentId, 0, '', saved.role, saved.userId, getToken(), questions)
    const idx = submissions.value.findIndex(s => s.id === sub.id)
    if (idx !== -1) {
      const updated = {
        ...sub,
        status: 'graded',
        score: result.submission?.score ?? 0,
        feedback: result.submission?.feedback || {},
      }
      // Merge graded questions into submission
      const gradedQs = result.submission?.feedback?.questions
      if (gradedQs) {
        const qMap = Object.fromEntries(gradedQs.map(q => [q.id, q]))
        updated.questions = (sub.questions || []).map(q => ({
          ...q,
          graded: true,
          studentScore: qMap[q.id]?.studentScore ?? q.studentScore ?? 0,
          comment: qMap[q.id]?.comment ?? q.comment ?? '',
        }))
      }
      submissions.value.splice(idx, 1, updated)
      // Clear saved grades from localStorage after successful submission
      try {
        const key = `${GRADE_STORAGE_KEY}.${selectedCourseId.value}.${selectedHwId.value}.${sub.id}`
        localStorage.removeItem(key)
      } catch {}
    }
  } catch (e) {
    console.error('Manual grading failed:', e)
    alert('手动批改失败: ' + (e.message || '未知错误'))
  } finally {
    manualGradingInProgress.value = false
  }
}

async function aiGradeSingleQuestion(q) {
  aiGradingQuestionIds.value.add(q.id)
  try {
    const result = await sendAiGradeQuestion({
      content: q.stem,
      maxScore: q.maxScore,
      referenceAnswer: q.referenceAnswer || '',
      studentAnswer: q.studentAnswer || '',
    })
    if (manualGrades[q.id]) {
      manualGrades[q.id].score = result.score ?? 0
      manualGrades[q.id].comment = result.comment ?? ''
    }
  } catch (e) {
    console.error('AI question grading failed:', e)
    alert('AI 评分失败: ' + (e.message || '未知错误'))
  } finally {
    aiGradingQuestionIds.value.delete(q.id)
  }
}

function exportReport(f) { alert(`导出 ${f.toUpperCase()}（Demo 模式暂不可用）`) }

onMounted(async () => {
  await loadCourses()
})
</script>

<style>
/* ====== Theme — 极简素白风格 ====== */
:root {
  --bg-root: #ffffff;
  --bg-card: #ffffff;
  --bg-card-hover: #fafafa;
  --bg-nav: #f8f9f8;
  --bg-input: #ffffff;
  --bg-tag: #f0f0f0;
  --bg-soft: #fafbfa;
  --accent: #121212;
  --accent-light: rgba(18,18,18,0.15);
  --accent-soft: #f0f0f0;
  --accent-glow: rgba(18,18,18,0.08);
  --accent-bright: rgba(18,18,18,0.2);
  --accent-deep: #121212;
  --accent-dim: rgba(18,18,18,0.03);
  --border-light: #e0e0e0;
  --border-medium: #dcdcdc;
  --border-active: #121212;
  --border-active-glow: rgba(18,18,18,0.15);
  --text-primary: #121212;
  --text-secondary: #4a534c;
  --text-muted: #999999;
  --divider: #f0f0f0;
  --panel-radius: 16px;
  --trans: 0.25s ease;
}
body.dark {
  --bg-root: #121212;
  --bg-card: #1a1a1a;
  --bg-card-hover: #222222;
  --bg-nav: #1a1a1a;
  --bg-input: #222222;
  --bg-tag: #2a2a2a;
  --bg-soft: #1e1e1e;
  --accent: #e0e0e0;
  --accent-light: rgba(224,224,224,0.2);
  --accent-soft: #2a2a2a;
  --accent-glow: rgba(224,224,224,0.1);
  --accent-bright: rgba(224,224,224,0.25);
  --accent-deep: #ffffff;
  --accent-dim: rgba(224,224,224,0.05);
  --border-light: #333333;
  --border-medium: #444444;
  --border-active: #e0e0e0;
  --border-active-glow: rgba(224,224,224,0.2);
  --text-primary: #e8e8e8;
  --text-secondary: #b0b0b0;
  --text-muted: #888888;
  --divider: #333333;
}
body.green {
  --bg-root: #f7f8f7;
  --bg-card: #ffffff;
  --bg-card-hover: #f3f6f3;
  --bg-nav: #ffffff;
  --bg-input: #ffffff;
  --bg-tag: #edf0ed;
  --bg-soft: #eef3ee;
  --accent: #526e5a;
  --accent-light: rgba(82,110,90,0.3);
  --accent-soft: #eef3ee;
  --accent-glow: rgba(82,110,90,0.15);
  --accent-bright: rgba(82,110,90,0.32);
  --accent-deep: #415848;
  --accent-dim: rgba(82,110,90,0.04);
  --border-light: #dee2de;
  --border-medium: #d6ded6;
  --border-active: #526e5a;
  --border-active-glow: rgba(82,110,90,0.3);
  --text-primary: #1e2720;
  --text-secondary: #556056;
  --text-muted: #8fa091;
  --divider: #edf0ed;
  --panel-radius: 16px;
  --trans: 0.25s ease;
}

* { margin:0; padding:0; box-sizing:border-box; }
html { font-size: 15px; }
body {
  font-family: 'Noto Serif SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--text-primary); background: var(--bg-root);
  -webkit-font-smoothing: antialiased; min-height: 100vh;
  transition: background 0.4s, color 0.4s; overflow: hidden;
}

/* ====== Login ====== */
.login-screen { display:flex; align-items:center; justify-content:center; height:100vh; background:var(--bg-root); }
.login-card { width:380px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:16px; padding:36px 28px; box-shadow:var(--shadow-md); }
.login-header { text-align:center; margin-bottom:24px; }
.login-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.6rem; font-weight:700; color:var(--accent); display:flex; align-items:center; justify-content:center; gap:6px; }
.login-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.login-subtitle { font-size:0.82rem; color:var(--text-muted); margin-top:4px; }
.login-roles { display:flex; gap:8px; margin-bottom:16px; justify-content:center; }
.role-btn { flex:1; padding:10px 8px; border-radius:12px; border:1.5px solid var(--border-light); background:transparent; cursor:pointer; transition:all 0.25s; text-align:center; }
.role-btn:hover { border-color:var(--border-medium); }
.role-btn.active { border-color:var(--accent); background:var(--accent-soft); box-shadow:0 0 12px var(--accent-soft); }
.role-icon { font-size:1.2rem; display:block; margin-bottom:2px; }
.role-label { font-size:0.72rem; color:var(--text-secondary); }
.login-input { width:100%; padding:12px; border-radius:12px; border:1.5px solid var(--border-light); background:var(--bg-input); font-size:0.88rem; color:var(--text-primary); outline:none; transition:all 0.25s; text-align:center; }
.login-input:focus { border-color:var(--border-active); box-shadow:0 0 20px var(--accent-glow); }
.login-error { color:#E07B30; font-size:0.76rem; text-align:center; margin-top:8px; }
.login-submit { width:100%; padding:11px; border-radius:12px; background:var(--accent); color:#fff; border:none; font-weight:600; font-size:0.88rem; cursor:pointer; margin-top:12px; transition:all 0.25s; }
.login-submit:hover:not(:disabled) { box-shadow:0 0 20px var(--accent-glow); }
.login-submit:disabled { opacity:0.45; cursor:not-allowed; }
.login-toggle { width:100%; padding:8px; border-radius:12px; background:transparent; border:none; color:var(--text-muted); font-size:0.74rem; cursor:pointer; margin-top:6px; }
.login-toggle:hover { color:var(--accent); }

/* ====== Layout ====== */
.app-shell { display:flex; flex-direction:column; height:100vh; width:100%; overflow:hidden; padding:6px 10px; gap:6px; min-width:1100px; }

/* ====== NAV ====== */
.teacher-nav {
  flex-shrink:0; height:50px; display:flex; align-items:center; justify-content:space-between;
  background:var(--bg-nav);
  border:1px solid var(--border-light); border-radius:var(--panel-radius);
  padding:0 24px; position:relative;
}
.top-nav {
  flex-shrink:0; height:50px; display:flex; align-items:center; justify-content:space-between;
  background:var(--bg-nav);
  border:1px solid var(--border-light); border-radius:var(--panel-radius);
  padding:0 24px; position:relative;
}
.nav-left { display:flex; align-items:center; gap:20px; }
.nav-logo { font-family:'Noto Serif SC',serif; font-size:1.4rem; font-weight:700; color:var(--accent); letter-spacing:-0.01em; display:flex; align-items:center; gap:7px; }
.nav-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); }
.nav-center { display:flex; align-items:center; gap:3px; }
.nav-tab { padding:6px 14px; border-radius:13px; font-size:0.82rem; font-weight:500; color:var(--text-secondary); cursor:pointer; transition:all 0.25s; border:1.5px solid transparent; white-space:nowrap; }
.nav-tab:hover { color:var(--text-primary); background:var(--bg-tag); }
.nav-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); }
.nav-right { display:flex; align-items:center; gap:8px; }
.nav-icon { width:32px; height:32px; border-radius:50%; border:1.5px solid var(--border-medium); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--text-secondary); transition:all 0.25s; flex-shrink:0; }
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.nav-icon:hover { color:var(--accent); border-color:var(--border-active); }
.nav-avatar { width:34px; height:34px; border-radius:50%; background:var(--accent); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:0.74rem; cursor:pointer; border:2px solid transparent; transition:all 0.25s; }
.nav-avatar:hover { transform:scale(1.06); }
.conn-status { display:flex; align-items:center; gap:5px; padding:4px 10px; border-radius:12px; font-size:0.72rem; color:var(--text-muted); border:1px solid var(--border-light); background:var(--bg-card); cursor:default; }
.conn-dot { width:7px; height:7px; border-radius:50%; background:var(--text-muted); flex-shrink:0; }
.conn-label { font-weight:500; }

/* ====== MAIN AREA ====== */
.main-area { flex:1; min-height:0; display:flex; gap:8px; }

/* ====== UNIVERSAL PANEL ====== */
.panel {
  background:var(--bg-card);
  border:1px solid var(--border-light); border-radius:var(--panel-radius);
  position:relative; overflow:hidden; display:flex; flex-direction:column;
}
.panel-strip { display:none; }

/* Panel sizing */
.panel-left { width:278px; min-width:250px; flex-shrink:0; background:var(--bg-soft); }
.panel-center { flex:1; min-width:0; }
.panel-right { width:288px; min-width:260px; flex-shrink:0; }

/* ====== LEFT PANEL ====== */
.pl-header { flex-shrink:0; display:flex; align-items:center; justify-content:space-between; padding:14px 14px 0; position:relative; z-index:2; }
.pl-title { font-size:0.84rem; font-weight:700; color:var(--text-primary); }
.pl-badge { font-size:0.66rem; color:var(--text-muted); background:var(--bg-tag); padding:2px 10px; border-radius:8px; font-weight:600; }

/* Course selector */
.pl-courses { padding:10px 14px; position:relative; z-index:2; }
.course-select { width:100%; padding:8px 12px; border-radius:12px; border:1px solid var(--border-light); background:var(--bg-input); font-size:0.76rem; color:var(--text-primary); outline:none; cursor:pointer; }
.course-select:focus { border-color:var(--border-active); }

/* Homework list */
.pl-homework-list { flex:1; overflow-y:auto; padding:0 10px; position:relative; z-index:2; }
.pl-homework-list::-webkit-scrollbar { width:3px; }
.pl-homework-list::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
.homework-row { display:flex; align-items:center; gap:8px; padding:10px 10px; border-radius:12px; cursor:pointer; transition:all 0.2s; border:1px solid transparent; margin-bottom:4px; }
.homework-row:hover { background:var(--bg-card); }
.homework-row.active { border-color:var(--accent); background:var(--bg-card); }
.hw-icon { font-size:1.1rem; flex-shrink:0; }
.hw-body { flex:1; min-width:0; }
.hw-title { font-size:0.76rem; font-weight:600; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.hw-meta { font-size:0.64rem; color:var(--text-muted); margin-top:2px; }
.hw-status { font-size:0.64rem; font-weight:600; color:var(--text-muted); flex-shrink:0; }
.hw-status.done { color:var(--accent); }

.pl-search { display:flex; align-items:center; gap:6px; margin:10px 14px; padding:7px 10px; background:var(--bg-input); border:1px solid var(--border-light); border-radius:10px; transition:all 0.25s; position:relative; z-index:2; }
.pl-search:focus-within { border-color:var(--border-active); }
.pl-search-icon { width:13px; height:13px; stroke:var(--text-muted); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0; }
.pl-search input { border:none; outline:none; background:transparent; font-family:inherit; font-size:0.72rem; color:var(--text-primary); width:100%; }
.pl-search input::placeholder { color:var(--text-muted); }
.pl-filters { display:flex; gap:5px; padding:0 14px 10px; position:relative; z-index:2; }
.pl-chip { padding:4px 12px; border-radius:16px; font-size:0.66rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.2s; border:1px solid transparent; }
.pl-chip:hover { color:var(--text-secondary); background:var(--bg-tag); }
.pl-chip.on { color:var(--text-primary); background:var(--bg-card); border-color:var(--border-light); }

.pl-list { flex:1; overflow-y:auto; padding:0 10px; position:relative; z-index:2; }
.pl-list::-webkit-scrollbar { width:3px; }
.pl-list::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
.submission-row {
  display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:10px;
  cursor:pointer; transition:all 0.2s; border:1px solid transparent; position:relative; overflow:hidden;
  animation: fadeIn 0.35s ease both;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
.submission-row:hover { background:var(--bg-card); }
.submission-row.active { border-color:var(--border-light); background:var(--bg-card); }
.sr-rank { font-size:0.64rem; color:var(--text-muted); width:16px; text-align:center; flex-shrink:0; }
.sr-avatar { width:28px; height:28px; border-radius:50%; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; flex-shrink:0; color:var(--text-primary); font-weight:700; font-size:0.68rem; font-family:monospace; }
.sr-body { flex:1; min-width:0; }
.sr-name { font-size:0.76rem; font-weight:600; color:var(--text-primary); }
.sr-desc { font-size:0.64rem; color:var(--text-muted); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-tail { flex-shrink:0; }
.sr-score { font-size:0.82rem; font-weight:700; color:var(--text-primary); font-family:monospace; }
.sr-dot { display:block; width:6px; height:6px; border-radius:50%; background:var(--text-muted); opacity:0.3; }
.pl-empty { text-align:center; padding:32px 0; color:var(--text-muted); font-size:0.72rem; }

.pl-footer { flex-shrink:0; padding:10px 14px 14px; position:relative; z-index:2; }
.pl-stats-row { display:flex; gap:8px; margin-bottom:10px; }
.pl-stat {
  flex:1; text-align:center; padding:12px 6px; border-radius:12px;
  background:var(--bg-card);
  border:1px solid var(--border-light);
  transition:all 0.25s;
}
.pl-stat-val { font-size:1.05rem; font-weight:700; color:var(--text-primary); letter-spacing:-0.02em; font-family:monospace; }
.pl-stat-lbl { font-size:0.62rem; color:var(--text-muted); margin-top:2px; font-weight:500; }
.batch-btn {
  width:100%; padding:11px; border-radius:12px;
  border:1px solid var(--border-light);
  background:var(--bg-card);
  color:var(--text-secondary); font-size:0.76rem; font-weight:600;
  cursor:pointer; transition:all 0.25s; font-family:inherit;
}
.batch-btn:hover:not(:disabled) {
  border-color:var(--accent);
  color:var(--accent);
}
.batch-btn:disabled { opacity:0.25; cursor:not-allowed; }

/* ====== CENTER PANEL ====== */
.center-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:10px; position:relative; z-index:3; }
.empty-icon-wrap { width:52px; height:52px; border-radius:14px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; }
.empty-icon-wrap svg { width:24px; height:24px; stroke:var(--text-muted); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }
.empty-title { font-size:0.84rem; font-weight:600; color:var(--text-secondary); }
.empty-desc { font-size:0.72rem; color:var(--text-muted); }

.center-scroll { flex:1; overflow-y:auto; padding:20px 24px 24px; position:relative; z-index:3; }
.center-scroll::-webkit-scrollbar { width:4px; }
.center-scroll::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

/* Student bar */
.student-bar { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--divider); }
.sb-left { display:flex; align-items:center; gap:10px; }
.sb-avatar {
  width:28px; height:28px; border-radius:6px;
  background: var(--accent);
  color:var(--bg-root); display:flex; align-items:center; justify-content:center;
  font-weight:700; font-size:0.72rem; flex-shrink:0;
  font-family:monospace;
}
.sb-name { font-size:0.82rem; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:8px; letter-spacing:0.02em; }
.sb-class { font-size:0.64rem; font-weight:500; color:var(--text-muted); background:var(--bg-tag); padding:3px 10px; border-radius:10px; }
.sb-meta { font-size:0.64rem; color:var(--text-muted); margin-top:2px; font-weight:500; font-family:monospace; }
.sb-status { font-size:0.68rem; font-weight:600; padding:4px 12px; border-radius:8px; border:1px solid var(--border-light); color:var(--text-muted); }
.sb-status.done { color:var(--text-primary); background:var(--bg-tag); border-color:var(--border-light); }

/* Question tabs */
.q-tabs { display:flex; align-items:center; gap:4px; margin-bottom:14px; }
.q-tab { padding:6px 15px; border-radius:18px; font-size:0.73rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.2s; border:1px solid transparent; background:transparent; }
.q-tab:hover { color:var(--text-secondary); background:var(--bg-tag); }
.q-tab.on { color:var(--text-primary); background:var(--bg-card); border-color:var(--border-light); }
.q-tab-summary { margin-left:auto; font-size:0.66rem; color:var(--text-muted); }

/* Question cards */
.q-list { display:flex; flex-direction:column; gap:14px; }
.q-card {
  position:relative; border-radius:16px;
  background:var(--bg-card);
  border:1px solid var(--border-light);
  transition:all 0.2s;
}
.q-card:hover { border-color:var(--border-medium); }
.q-inner { padding:16px 20px; position:relative; z-index:1; }

.q-top { display:flex; align-items:center; gap:8px; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid var(--divider); }
.q-idx {
  width:18px; height:18px; border-radius:50%; background:var(--accent);
  color:var(--bg-root); font-size:0.60rem; font-weight:700;
  display:flex; align-items:center; justify-content:center;
  font-family:monospace;
}
.q-kind { font-size:0.66rem; color:var(--text-primary); font-weight:600; }
.q-pts { font-size:0.66rem; color:var(--text-muted); margin-left:auto; font-weight:500; font-family:monospace; }

.q-stem { font-size:0.82rem; color:var(--text-primary); font-weight:600; line-height:1.7; margin-bottom:8px; }

/* Options */
.q-opts { display:flex;flex-direction:column;gap:6px;margin-bottom:8px; }
.q-opt { display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:12px;border:1px solid var(--border-light);font-size:0.78rem;transition:all 0.15s;color:var(--text-secondary); }
.q-opt.picked { border-color:var(--accent); background:var(--bg-card); color:var(--text-primary); font-weight:600; }
.q-opt.correct { border-color:var(--accent); background:var(--bg-soft); color:var(--text-primary); font-weight:600; }
.q-opt.wrong { border:2px solid var(--accent); background:var(--bg-card); color:var(--text-primary); font-weight:600; }
.q-opt-letter { width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border-medium);display:flex;align-items:center;justify-content:center;font-size:0.70rem;font-weight:600;color:var(--text-secondary);flex-shrink:0; }
.q-opt.picked .q-opt-letter { border-color:var(--accent);color:var(--accent);background:var(--bg-card); }
.q-opt.correct .q-opt-letter { border-color:var(--accent);color:var(--bg-root);background:var(--accent); }
.q-opt.wrong .q-opt-letter { border-color:var(--accent);color:var(--accent);background:var(--bg-card); }
.q-opt-text { flex:1;color:var(--text-secondary); }
.q-opt.picked .q-opt-text, .q-opt.correct .q-opt-text, .q-opt.wrong .q-opt-text { color:var(--text-primary); }
.q-opt-badge { font-size:9px; padding:2px 6px; border-radius:4px; background:var(--bg-tag); color:var(--text-secondary); font-weight:500; flex-shrink:0; }
.q-opt-badge.correct { background:var(--bg-tag); color:var(--text-primary); }

/* TF / Fill */
.q-tf, .q-fill { display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap; }
.q-tf-label, .q-fill-label { font-size:0.62rem;font-weight:700;letter-spacing:0.05em;color:var(--text-muted);text-transform:uppercase; }
.q-tf-val, .q-fill-val { font-size:0.80rem;font-weight:600;padding:4px 12px;border-radius:8px;background:var(--bg-tag); }
.q-tf-val.is-correct, .q-fill-val.is-correct { color:var(--text-primary); }
.q-tf-val.is-wrong, .q-fill-val.is-wrong { color:var(--text-primary); }
.q-fill-val { font-family:monospace; }
.q-tf-ref, .q-fill-ref { font-size:0.70rem;color:var(--text-secondary); }

/* Subjective answer */
.q-answer-area { margin-bottom:8px; display:flex; flex-direction:column; gap:8px; }
.q-answer-box {
  padding:12px 14px; border-radius:12px;
  border:1px solid var(--accent); background:var(--bg-card);
}
.q-answer-label {
  font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--accent);
  margin-bottom:6px; display:inline-block;
  border-bottom:1px solid var(--bg-tag); padding-bottom:3px;
}
.q-answer-text { font-size:0.82rem; color:var(--text-primary); line-height:1.8; margin:0; }
.q-ref-box {
  padding:12px 14px; border-radius:12px;
  border:1px solid var(--accent); background:var(--bg-soft);
}
.q-ref-label {
  font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--text-secondary);
  margin-bottom:6px; display:inline-block;
  border-bottom:1px solid var(--bg-tag); padding-bottom:3px;
}
.q-ref-text { font-size:0.82rem; color:var(--text-secondary); line-height:1.8; margin:0; }

/* Manual grading inputs */
.manual-grade-input {
  margin-top:8px; padding:12px 14px; border-radius:12px;
  border:1px dashed var(--border-light); background:var(--bg-soft);
}
.manual-grade-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.manual-grade-row:last-child { margin-bottom:0; }
.manual-grade-label {
  font-size:0.68rem; font-weight:700; color:var(--text-secondary); flex-shrink:0; width:32px;
}
.manual-grade-score {
  width:60px; padding:4px 8px; border-radius:8px; border:1px solid var(--border-light);
  background:var(--bg-card); font-size:0.82rem; color:var(--text-primary);
  text-align:center;
}
.manual-grade-score:focus { outline:none; border-color:var(--accent); }
.manual-grade-max { font-size:0.72rem; color:var(--text-muted); }
.manual-grade-comment {
  flex:1; padding:6px 10px; border-radius:8px; border:1px solid var(--border-light);
  background:var(--bg-card); font-size:0.78rem; color:var(--text-primary);
  resize:vertical; font-family:inherit;
}
.manual-grade-comment:focus { outline:none; border-color:var(--accent); }
.manual-grade-btn { background:var(--accent) !important; }
.ai-grade-q-btn {
  display:inline-flex; align-items:center; gap:4px;
  padding:4px 10px; border-radius:8px; border:1px solid var(--border-light);
  background:var(--bg-card); color:var(--text-secondary);
  font-size:0.68rem; font-weight:600; cursor:pointer;
  transition:all 0.2s; flex-shrink:0; white-space:nowrap;
}
.ai-grade-q-btn:hover:not(:disabled) { border-color:var(--accent); color:var(--accent); }
.ai-grade-q-btn:disabled { opacity:0.6; cursor:not-allowed; }
.ai-grade-q-btn .grade-spinner { width:12px; height:12px; }

/* Footer */
.q-footer { display:flex;align-items:center;gap:8px;padding-top:10px;border-top:1px solid var(--divider);margin-top:4px; }
.q-footer-score { font-size:0.70rem;font-weight:700;padding:2px 8px;border-radius:5px;flex-shrink:0; font-family:monospace; }
.q-footer-score.full { color:var(--text-primary);background:var(--bg-tag); }
.q-footer-score.half { color:var(--text-primary);background:var(--bg-tag); }
.q-footer-score.zero { color:var(--text-muted);background:var(--bg-tag); }
.q-footer-note { font-size:0.68rem;color:var(--text-muted); }
.q-empty { text-align:center;padding:32px 0;color:var(--text-muted);font-size:0.74rem; }

/* ====== RIGHT PANEL ====== */
.pr-empty { display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:10px;color:var(--text-muted);position:relative;z-index:3; }
.pr-empty svg { stroke:var(--text-muted);fill:none;stroke-width:1.5; }
.pr-empty p { font-size:0.72rem;text-align:center;line-height:1.6; }

.pr-scroll { flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:16px;position:relative;z-index:3; }
.pr-scroll::-webkit-scrollbar { width:3px; }
.pr-scroll::-webkit-scrollbar-thumb { background:var(--border-light);border-radius:2px; }

.pr-section { }
.pr-sec-title {
  font-size:0.66rem; font-weight:700; letter-spacing:0.05em;
  color:var(--text-muted); margin-bottom:10px; text-transform:uppercase;
  display:flex; align-items:center; gap:10px;
}
.pr-sec-title::after {
  content:''; flex:1; height:1px;
  background: var(--divider);
}

/* Score hero */

/* Dimensions */
.dim-row { display:flex; align-items:center; gap:10px; margin-bottom:9px; }
.dim-name { font-size:0.70rem; color:var(--text-secondary); width:56px; flex-shrink:0; }
.dim-bar { flex:1; height:6px; background:var(--border-light); border-radius:4px; overflow:hidden; }
.dim-bar i { display:block; height:100%; background: linear-gradient(90deg, var(--accent-deep), var(--accent)); border-radius:4px; transition: width 0.8s var(--trans); box-shadow: 0 0 8px var(--accent-soft); }
.dim-val { font-size:0.70rem; font-weight:600; color:var(--text-primary); width:44px; text-align:right; flex-shrink:0; }
.dim-val small { font-size:0.60rem; color:var(--text-muted); font-weight:400; }

/* Histogram */
.histogram {
	  display:flex; align-items:flex-end; gap:14px; height:96px; padding:0 8px;
	  position:relative;
	  border-bottom:1px solid var(--border-light);
	}
.hist-col { flex:1; display:flex; flex-direction:column; align-items:center; gap:5px; z-index:1; min-width:0; }
.hist-bar-wrap { flex:1; width:100%; display:flex; flex-direction:column; align-items:center; }
.hist-bar-spacer { min-height:0; width:100%; }
.hist-bar {
	  width:64%; max-width:48px; min-height:4px;
	  background: var(--bg-tag);
	  border-radius:4px 4px 2px 2px;
	  transition: all 0.6s var(--trans);
	}
.hist-bar.highlight {
	  background: var(--accent);
	}
.hist-label { font-size:0.62rem; color:var(--text-muted); font-weight:500; white-space:nowrap; font-family:monospace; }
.hist-count { font-size:0.64rem; font-weight:700; color:var(--text-secondary); white-space:nowrap; display:none; }
.hist-legend { text-align:center; margin-top:8px; }
.hist-avg { font-size:0.66rem; color:var(--text-muted); font-family:monospace; }

/* Feedback */
.feedback-card { padding:12px 14px;border-radius:10px;background:var(--bg-tag);border:1px solid var(--border-light); }
.feedback-card p { font-size:0.76rem;color:var(--text-secondary);line-height:1.8; }

/* Strengths */
.plus-item { font-size:0.74rem;color:var(--text-secondary);padding:8px 12px;background:var(--bg-soft);border-radius:8px;line-height:1.6; }
.plus-item::before { content:'+ ';color:var(--accent);font-weight:700;font-size:0.9rem; }

/* Improvements */
.imp-item { display:flex;gap:10px;padding:12px 14px;border-radius:10px;background:var(--bg-tag);border:1px solid var(--border-light); }
.imp-n { width:20px;height:20px;border-radius:50%;background:var(--accent-soft);color:var(--accent);font-size:0.66rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0; }
.imp-t { font-size:0.74rem;font-weight:600;color:var(--text-primary);margin-bottom:3px; }
.imp-d { font-size:0.70rem;color:var(--text-muted);line-height:1.6; }

/* Grade action */
.grade-intro { font-size:0.76rem;color:var(--text-secondary);line-height:1.75;margin-bottom:14px; }
.grade-opts { display:flex;flex-direction:column;gap:5px;margin-bottom:14px; }
.grade-opt { display:flex;align-items:center;gap:7px;font-size:0.72rem;color:var(--text-secondary);cursor:pointer; }
.grade-opt input[type="checkbox"] { accent-color:var(--accent); }
.grade-start {
  width:100%;padding:10px;border-radius:12px;background:var(--accent);color:#fff;
  border:1px solid var(--accent);font-weight:600;font-size:0.80rem;cursor:pointer;transition:all 0.25s;
  display:flex;align-items:center;justify-content:center;gap:8px;font-family:inherit;
}
.grade-start:hover:not(:disabled) { opacity:0.9;transform:translateY(-1px); }
.grade-start:disabled { opacity:0.55;cursor:not-allowed; }
.grade-spinner { width:15px;height:15px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.6s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

/* Grade summary & finish button */
.grade-summary {
  display:flex;align-items:center;gap:8px;padding:10px 12px;border-radius:12px;
  background:var(--bg-soft);border:1px solid var(--border-light);
  font-size:0.74rem;color:var(--text-primary);font-weight:600;margin-bottom:14px;
}
.grade-summary-icon { font-size:0.82rem; }
.finish-grade-btn {
  background:var(--accent) !important;
}
.finish-grade-btn:hover:not(:disabled) { opacity:0.9 !important; }
.grade-hint { font-size:0.68rem;color:var(--text-muted);text-align:center;margin-top:6px; }

/* Export */
.export-row { display:flex;gap:8px; }
.exp-btn {
  flex:1;padding:9px;border-radius:12px;border:1px solid var(--border-light);
  background:var(--bg-card);color:var(--text-muted);font-size:0.73rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:6px;transition:all 0.25s;font-family:inherit;
}
.exp-btn:hover { border-color:var(--accent); color:var(--accent); }
.exp-btn svg { stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round; }

/* ====== RADAR CHART ====== */
.radar-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; }
.radar-svg { width:100%; max-width:210px; }
.radar-ring { fill:none; stroke:var(--border-light); stroke-width:1; }
.radar-ring.rl-2 { stroke:var(--divider); }
.radar-ring.rl-4 { stroke:var(--border-medium); stroke-width:1.2; }
.radar-axis { stroke:var(--border-light); stroke-width:0.8; }
.radar-data { fill:var(--bg-soft); stroke:var(--accent); stroke-width:1.6; stroke-linejoin:round; }
.radar-dot { fill:var(--accent); stroke:#fff; stroke-width:1.5; }
body.dark .radar-dot { stroke:var(--bg-root); }
.radar-label { font-size:0.66rem; fill:var(--text-secondary); font-weight:600; }
.radar-label-top { dominant-baseline:auto; }
.radar-label-bot { dominant-baseline:hanging; }
.radar-legend { display:flex; flex-wrap:wrap; gap:4px 10px; justify-content:center; }
.radar-legend-item { font-size:0.70rem; color:var(--text-muted); display:flex; align-items:center; gap:4px; }
.radar-legend-dot { width:6px; height:6px; border-radius:50%; background:var(--accent); display:inline-block; flex-shrink:0; }

/* ====== NOTEBOOK ====== */
.notebook {
  position:relative;
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 18px 16px 20px 20px;
  font-family: 'Noto Serif SC', "STSong", "SimSun", "Songti SC", serif;
  min-height: 80px;
}
.notebook-score-row {
  display: flex; align-items: baseline; gap: 6px; margin-bottom: 4px;
}
.notebook-score {
  font-size: 1.5rem; font-weight: 700; color: var(--accent);
  font-family: 'Noto Serif SC', "STSong", "SimSun", "Songti SC", serif; line-height: 1;
}
.notebook-score-label {
  font-size: 0.78rem; color: var(--text-muted);
  font-family: 'Noto Serif SC', "STSong", "SimSun", "Songti SC", serif;
}
.notebook-text {
  font-size: 0.82rem; color: var(--text-muted); line-height: 1.8; margin: 0;
  font-weight: 400; letter-spacing: 0.01em;
}
.notebook-li {
  font-size: 0.78rem; color: var(--text-secondary); line-height: 1.8;
  padding-left: 4px; position: relative; font-weight: 400;
}
.notebook-li::before {
  content: "+"; color: var(--text-muted); font-weight: 700; margin-right: 8px;
}
.notebook-imp { display: flex; gap: 10px; }
.notebook-imp:not(:last-child) { margin-bottom: 8px; }
.notebook-imp-n {
  font-size: 0.82rem; font-weight: 700; color: var(--text-primary);
  line-height: 1.8; flex-shrink: 0;
}
.notebook-imp-t {
  font-size: 0.82rem; font-weight: 700; color: var(--text-primary);
  letter-spacing: 0.01em; line-height: 1.8;
}
.notebook-imp-d {
  font-size: 0.78rem; color: var(--text-secondary); line-height: 1.8; margin-top: 2px; font-weight: 400;
}

/* Objective question score */
.q-obj-score {
  font-size: 0.72rem;
  color: var(--text-muted);
  background: var(--bg-soft);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  font-family: monospace;
  margin-top: 8px;
}

/* Right panel divider */
.pr-divider {
  height: 1px;
  background: var(--divider);
  margin: 4px 0;
}

/* ====== PANEL COLLAPSE ====== */
.panel-toggle {
  position:absolute; top:50%; transform:translateY(-50%); z-index:10;
  width:22px; height:44px; border-radius:6px; border:1px solid var(--border-medium);
  background:var(--bg-card); color:var(--text-muted); cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.25s; padding:0;
}
.panel-left .panel-toggle { right:2px; }
.panel-right .panel-toggle { left:2px; }
.panel-toggle:hover { color:var(--accent); border-color:var(--accent-light); }
.panel-toggle svg { transition:transform 0.3s; }
.panel.collapsed .panel-toggle { transform:translateY(-50%); }

.panel.collapsed {
  width:38px !important; min-width:38px !important; flex-shrink:0;
  transition:width 0.35s var(--trans), min-width 0.35s var(--trans);
}
.panel.collapsed > *:not(.panel-strip):not(.panel-toggle) { display:none; }
.panel.collapsed .panel-toggle svg { transform:rotate(180deg); }
.exp-btn:hover { border-color:var(--border-active);color:var(--accent);box-shadow:0 0 12px var(--accent-soft); }
</style>
