<template>
<!-- ====== 批改考试 ====== -->
<div v-if="activeTab === 'exam'" class="main-area">
  <aside class="panel panel-left" :class="{ collapsed: panelCollapsed.left }">
    <button class="panel-toggle" @click="panelCollapsed.left = !panelCollapsed.left" :title="panelCollapsed.left ? '展开' : '收起'">
      <svg viewBox="0 0 16 16" width="14" height="14"><path d="M10 4L6 8l4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
    <div class="pl-header"><span class="pl-title">考试阅卷</span><span class="pl-badge">{{ examItems.length }} 场考试</span></div>
    <div class="pl-courses"><select v-model="examSelectedCourse" class="course-select" @change="onExamCourseChange"><option value="">选择课程...</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div>
    <div v-if="examSelectedCourse" class="pl-homework-list">
      <div v-for="e in examItems" :key="e.exam_id" class="homework-row" :class="{ active: selectedExamId === e.exam_id }" @click="selectExam(e)">
        <div class="hw-icon">📋</div><div class="hw-body"><div class="hw-title">{{ e.title }}</div><div class="hw-meta">{{ e.duration }}分钟 · {{ examSubCount(e.exam_id) }} 份答卷</div></div>
      </div>
      <div v-if="examItems.length === 0" class="pl-empty">该课程暂无考试</div>
    </div>
    <div v-else class="pl-empty" style="flex:1;display:flex;align-items:center;justify-content:center">请先选择课程</div>
    <template v-if="selectedExamId">
      <div class="pl-search"><svg viewBox="0 0 20 20" class="pl-search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg><input v-model="examSearchQuery" placeholder="搜索学生..." /></div>
      <div class="pl-filters">
        <span class="pl-chip" :class="{ on: examStatusFilter === 'all' }" @click="examStatusFilter = 'all'">全部</span>
        <span class="pl-chip" :class="{ on: examStatusFilter === 'pending' }" @click="examStatusFilter = 'pending'">待批改</span>
        <span class="pl-chip" :class="{ on: examStatusFilter === 'graded' }" @click="examStatusFilter = 'graded'">已批改</span>
      </div>
      <div class="pl-list">
        <div v-for="(sub, si) in filteredExamSubmissions" :key="sub.id" class="submission-row" :class="{ active: examActiveId === sub.id }" @click="selectExamSubmission(sub)" :style="{ animationDelay: si * 0.03 + 's' }">
          <div class="sr-rank">{{ si + 1 }}</div><div class="sr-avatar">{{ (sub.studentName || sub.studentId || '?')[0] }}</div>
          <div class="sr-body"><div class="sr-name">{{ sub.studentName || sub.studentId }}</div><div class="sr-desc">{{ sub.status === 'graded' ? '已批改' : '待批改' }}</div></div>
          <div class="sr-tail"><span v-if="sub.graded" class="sr-score">{{ sub.score }}</span><span v-else class="sr-dot"></span></div>
        </div>
      </div>
    </template>
  </aside>

  <section class="panel panel-center">
    <div v-if="!activeExamSub" class="center-empty"><div class="empty-icon-wrap"><svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg></div><p class="empty-title">选择左侧试卷和学生</p><p class="empty-desc">开始考试阅卷</p></div>
    <div v-else class="center-scroll">
      <div class="student-bar"><div class="sb-left"><div class="sb-avatar">{{ (activeExamSub.studentName||activeExamSub.studentId||'?')[0] }}</div><div><div class="sb-name">{{ activeExamSub.studentName||activeExamSub.studentId }}</div><div class="sb-meta">{{ activeExamSub.examTitle||selectedExam?.title }}</div></div></div><span class="sb-status" :class="{ done: activeExamSub.graded }">{{ activeExamSub.graded ? '✓ 已批改' : '待批改' }}</span></div>
      <div class="q-tabs"><span class="q-tab on">全部 {{ examDisplayAnswers.length }} 题</span></div>
      <div class="q-list">
        <div v-for="(a, ai) in examDisplayAnswers" :key="ai" class="q-card"><div class="q-inner">
          <div class="q-top"><span class="q-idx">{{ ai+1 }}</span><span class="q-kind">{{ a.typeLabel }}</span><span class="q-pts">{{ a.maxScore }} 分</span></div>
          <div class="q-stem">{{ a.stem }}</div>
          <div v-if="a.options?.length" class="q-opts"><div v-for="opt in a.options" :key="opt.key" class="q-opt" :class="{ picked: opt.key === a.studentPick }"><span class="q-opt-letter">{{ opt.key }}</span><span class="q-opt-text">{{ opt.text }}</span></div></div>
          <div class="q-answer-box"><div class="q-answer-label">学生作答</div><p class="q-answer-text">{{ a.studentAnswer || '(未作答)' }}</p></div>
          <div v-if="a.referenceAnswer" class="q-ref-box"><div class="q-ref-label">参考答案</div><p class="q-ref-text">{{ a.referenceAnswer }}</p></div>
        </div></div>
      </div>
    </div>
  </section>

  <aside class="panel panel-right" :class="{ collapsed: panelCollapsed.right }">
    <button class="panel-toggle right-toggle" @click="panelCollapsed.right = !panelCollapsed.right" :title="panelCollapsed.right ? '展开' : '收起'"><svg viewBox="0 0 16 16" width="14" height="14"><path d="M6 4l4 4-4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
    <div v-if="!activeExamSub" class="pr-empty"><svg viewBox="0 0 20 20" width="28" height="28"><circle cx="10" cy="10" r="7"/><path d="M10 6v5M10 13v1"/></svg><p>选择答卷后<br>此处展示评分面板</p></div>
    <div v-else class="pr-scroll">
      <template v-if="!activeExamSub.graded">
        <div class="pr-section"><div class="pr-sec-title">综合评分</div><div class="dim-row"><span class="dim-name">得分</span><div class="dim-bar"><i :style="{ width: examScore + '%' }"></i></div><span class="dim-val">{{ examScore }}<small>/100</small></span></div><input type="range" v-model.number="examScore" min="0" max="100" class="grade-range" /></div>
        <div class="pr-section"><div class="pr-sec-title">评语</div><textarea v-model="examComment" rows="3" class="grade-textarea" placeholder="输入评语..."></textarea></div>
        <div v-if="examFeedback" class="pr-section"><div class="grade-feedback" :class="{ error: examFeedback.startsWith('✗') }">{{ examFeedback }}</div></div>
        <div class="pr-section"><button class="grade-start finish-grade-btn" :disabled="examGrading" @click="submitExamGrade">{{ examGrading ? '保存中...' : '完成批改' }}</button></div>
        <div class="pr-section"><div class="pr-sec-title">AI 双引擎评估</div>
          <button class="grade-start ai-cropgpt-btn" :disabled="!!examAiLoading" @click="submitExamAiCropGpt">
            <span v-if="examAiLoading === 'cropgpt'" class="ai-spinner"></span>
            🌾 CropGPT 视觉评估
          </button>
          <button class="grade-start ai-general-btn" :disabled="!!examAiLoading" @click="submitExamAiGeneral" style="margin-top:6px">
            <span v-if="examAiLoading === 'general'" class="ai-spinner"></span>
            🤖 通用模型评估
          </button>
        </div>
      </template>
      <template v-else><div class="pr-section"><div class="pr-sec-title">成绩</div><div class="notebook"><div class="notebook-score-row"><span class="notebook-score">{{ activeExamSub.score||examScore }}</span><span class="notebook-score-label">/100</span></div></div></div></template>
    </div>
  </aside>
</div>

<!-- ====== 实习报告批改 ====== -->
<div v-else class="report-layout">
  <!-- 左侧：课程 + 报告列表 -->
  <aside class="panel panel-left" :class="{ collapsed: panelCollapsed.left }">
    <button class="panel-toggle" @click="panelCollapsed.left = !panelCollapsed.left" :title="panelCollapsed.left ? '展开' : '收起'"><svg viewBox="0 0 16 16" width="14" height="14"><path d="M10 4L6 8l4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
    <div class="pl-header"><span class="pl-title">📋 实习报告</span><span class="pl-badge">{{ reportHwList.length }} 份</span></div>
    <div class="pl-courses"><select v-model="reportSelectedCourse" class="course-select" @change="onReportCourseChange"><option value="">选择课程...</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div>
    <div v-if="reportSelectedCourse" class="pl-homework-list">
      <div v-for="h in reportHwList" :key="h.hwId" class="homework-row" :class="{ active: selectedReportHwId === h.hwId }" @click="selectReportHw(h)">
        <div class="hw-icon">📄</div><div class="hw-body"><div class="hw-title">{{ h.title }}</div><div class="hw-meta">{{ getHwSubCount(h.hwId) }} 份提交 · {{ getHwGradedCount(h.hwId) }} 已批</div></div>
      </div>
      <div v-if="reportHwList.length === 0" class="pl-empty">该课程暂无报告作业</div>
    </div>
    <div v-else class="pl-empty" style="flex:1;display:flex;align-items:center;justify-content:center">请先选择课程</div>
    <template v-if="selectedReportHwId">
      <div class="pl-search"><svg viewBox="0 0 20 20" class="pl-search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg><input v-model="reportSearchQuery" placeholder="搜索学生..." /></div>
      <div class="pl-filters"><span class="pl-chip" :class="{ on: reportStatusFilter==='all' }" @click="reportStatusFilter='all'">全部</span><span class="pl-chip" :class="{ on: reportStatusFilter==='pending' }" @click="reportStatusFilter='pending'">待批改</span><span class="pl-chip" :class="{ on: reportStatusFilter==='graded' }" @click="reportStatusFilter='graded'">已批改</span></div>
      <div class="pl-list">
        <div v-for="(sub, si) in filteredReportSubmissions" :key="sub.id" class="submission-row" :class="{ active: reportActiveId === sub.id }" @click="selectReportSubmission(sub)" :style="{ animationDelay: si*0.03+'s' }">
          <div class="sr-rank">{{ si+1 }}</div><div class="sr-avatar">{{ (sub.studentName||sub.studentId||'?')[0] }}</div>
          <div class="sr-body"><div class="sr-name">{{ sub.studentName||sub.studentId }}</div><div class="sr-desc">{{ sub.status==='graded'?'已批改 · '+sub.score+'分':'待批改' }}</div></div>
          <div class="sr-tail"><span v-if="sub.graded" class="sr-score">{{ sub.score }}</span><span v-else class="sr-dot"></span></div>
        </div>
      </div>
    </template>
  </aside>

  <!-- 中间：报告正文视图 -->
  <section class="panel panel-center report-center">
    <div v-if="!activeReportSub" class="center-empty">
      <div class="empty-icon-wrap report-empty-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>
      </div>
      <p class="empty-title">选择左侧课程和学生</p>
      <p class="empty-desc">查看实习报告全文 · 多维度评分</p>
    </div>
    <div v-else class="report-reader">
      <!-- 报告头部信息 -->
      <div class="report-header">
        <div class="rh-top">
          <div class="rh-student">
            <div class="rh-avatar">{{ (activeReportSub.studentName||activeReportSub.studentId||'?')[0] }}</div>
            <div>
              <div class="rh-name">{{ activeReportSub.studentName||activeReportSub.studentId }}</div>
              <div class="rh-meta">{{ activeReportSub.hwTitle }} · {{ activeReportSub.submittedAt ? formatDate(activeReportSub.submittedAt) : '未知日期' }}</div>
            </div>
          </div>
          <span class="rh-badge" :class="{ done: activeReportSub.graded }">{{ activeReportSub.graded ? '已批改' : '待批改' }}</span>
        </div>
        <div class="rh-stats">
          <div class="rh-stat"><span class="rh-stat-num">{{ reportWordCount }}</span><span class="rh-stat-label">总字数</span></div>
          <div class="rh-stat"><span class="rh-stat-num">{{ reportSectionCount }}</span><span class="rh-stat-label">章节数</span></div>
          <div class="rh-stat"><span class="rh-stat-num">{{ reportImageCount }}</span><span class="rh-stat-label">附图</span></div>
        </div>
      </div>
      <!-- 报告正文 -->
      <div class="report-body">
        <div v-if="reportSections.length === 0" class="report-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p>该学生尚未提交报告内容</p>
        </div>
        <div v-for="(sec, si) in reportSections" :key="si" class="report-section">
          <h3 class="rs-title">{{ sec.stem || '第'+(si+1)+'部分' }}</h3>
          <div class="rs-content" v-html="renderReportContent(sec.answer)"></div>
          <!-- 图片占位符 -->
          <div v-if="hasImagePlaceholder(sec.answer)" class="report-images">
            <div v-for="(img, ii) in extractImageSlots(sec.answer)" :key="ii" class="report-img-card">
              <div class="report-img-placeholder">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
                <span class="rimg-label">{{ img.label || '附图 '+(ii+1) }}</span>
              </div>
              <span class="rimg-caption">{{ img.caption || '学生上传图片（待查看）' }}</span>
            </div>
          </div>
        </div>
        <!-- 底部图片附件汇总 -->
        <div v-if="reportImageSlots.length > 0" class="report-attachment-bar">
          <div class="rab-title">📸 报告附图（{{ reportImageSlots.length }} 张）</div>
          <div class="rab-grid">
            <div v-for="(img, ii) in reportImageSlots" :key="ii" class="rab-thumb">
              <div class="rab-thumb-inner">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
              </div>
              <span>{{ img.label || '图'+(ii+1) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- 右侧：多维度评分面板 -->
  <aside class="panel panel-right" :class="{ collapsed: panelCollapsed.right }">
    <button class="panel-toggle right-toggle" @click="panelCollapsed.right = !panelCollapsed.right" :title="panelCollapsed.right ? '展开' : '收起'"><svg viewBox="0 0 16 16" width="14" height="14"><path d="M6 4l4 4-4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
    <div v-if="!activeReportSub" class="pr-empty">
      <svg viewBox="0 0 20 20" width="28" height="28"><circle cx="10" cy="10" r="7"/><path d="M10 6v5M10 13v1"/></svg>
      <p>选择报告后<br>此处展示评分面板</p>
    </div>
    <div v-else class="pr-scroll">
      <template v-if="!activeReportSub.graded">
        <!-- 评分维度 -->
        <div class="pr-section">
          <div class="pr-sec-title">📊 评分维度</div>
          <div v-for="dim in reportDimensions" :key="dim.key" class="dim-card">
            <div class="dim-card-head">
              <span class="dim-card-name">{{ dim.label }}</span>
              <span class="dim-card-score">{{ dim.score }}<small>/{{ dim.max }}</small></span>
            </div>
            <input type="range" v-model.number="dim.score" :min="0" :max="dim.max" class="dim-slider" />
            <div class="dim-card-hints">
              <span v-for="hint in dim.hints" :key="hint" class="dim-hint" :class="{ active: dim.score >= hint.threshold }" @click="dim.score = hint.value">{{ hint.label }}</span>
            </div>
          </div>
          <div class="dim-total-row">
            <span class="dim-total-label">综合得分</span>
            <span class="dim-total-score">{{ reportTotalScore }}<small>/100</small></span>
          </div>
        </div>
        <!-- 总评 -->
        <div class="pr-section">
          <div class="pr-sec-title">💬 总评</div>
          <textarea v-model="reportComment" rows="4" class="grade-textarea" placeholder="整体评语与建议..."></textarea>
        </div>
        <!-- 快捷评语 -->
        <div class="pr-section">
          <div class="pr-sec-title">⚡ 快捷评语</div>
          <div class="quick-comments">
            <span v-for="qc in quickComments" :key="qc" class="qc-chip" @click="reportComment = (reportComment ? reportComment + '\n' : '') + qc">{{ qc }}</span>
          </div>
        </div>
        <!-- 操作 -->
        <div v-if="reportFeedback" class="pr-section"><div class="grade-feedback" :class="{ error: reportFeedback.startsWith('✗') }">{{ reportFeedback }}</div></div>
        <div class="pr-section">
          <button class="grade-start save-grade-btn" :disabled="reportGrading" @click="submitReportGrade">{{ reportGrading ? '保存中...' : '✓ 确认评分' }}</button>
        </div>
        <!-- AI 双引擎 -->
        <div class="pr-section">
          <div class="pr-sec-title">🤖 AI 辅助评估</div>
          <button class="grade-start ai-cropgpt-btn" :disabled="!!reportAiLoading" @click="submitReportAiCropGpt">
            <span v-if="reportAiLoading === 'cropgpt'" class="ai-spinner"></span>
            🌾 CropGPT 视觉评估
          </button>
          <button class="grade-start ai-general-btn" :disabled="!!reportAiLoading" @click="submitReportAiGeneral" style="margin-top:6px">
            <span v-if="reportAiLoading === 'general'" class="ai-spinner"></span>
            🤖 通用模型评估
          </button>
        </div>
      </template>
      <template v-else>
        <div class="pr-section"><div class="pr-sec-title">📊 已评定成绩</div>
          <div class="report-score-card">
            <div class="rsc-big">{{ activeReportSub.score||reportScore }}</div>
            <div class="rsc-label">/100</div>
          </div>
        </div>
        <div v-if="activeReportSub.feedback?.comment" class="pr-section">
          <div class="pr-sec-title">💬 评语</div>
          <div class="report-feedback-text">{{ activeReportSub.feedback.comment || activeReportSub.feedback.feedback || '' }}</div>
        </div>
      </template>
    </div>
  </aside>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../../composables/useCourse.js'
import { useAuthFetch } from '../../composables/useAuthFetch.js'

const route = useRoute()
const {
  courses, fetchCourses, fetchHomeworkList, fetchSubmissions,
  gradeSubmission, aiGradeCropGpt, aiGradeGeneral,
} = useCourse()
const { authGet } = useAuthFetch()

const activeTab = ref(route.query.tab || 'exam')
watch(() => route.query.tab, (val) => { if (val) activeTab.value = val })

const panelCollapsed = reactive({ left: false, right: false })
const homeworkItems = ref([])
const submissionItems = ref([])
const examItems = ref([])
const homeworkQuestionMap = ref({})
const loadingCourseData = ref(false)

async function loadCourseData(courseId) {
  homeworkItems.value = []; submissionItems.value = []; examItems.value = []
  homeworkQuestionMap.value = {}; loadingCourseData.value = true
  if (!courseId) { loadingCourseData.value = false; return }
  try {
    // 加载作业列表（含考试用作业）
    const hwList = await fetchHomeworkList(courseId) || []
    homeworkItems.value = hwList
    for (const h of hwList) {
      const questions = (h.settings || {}).questions || h.questions || []
      if (questions.length) homeworkQuestionMap.value[h.hwId] = questions
      try {
        const subs = await fetchSubmissions(courseId, h.hwId) || []
        submissionItems.value.push(...subs.map(s => ({
          ...s, hwId: h.hwId, hwTitle: h.title,
          graded: s.status === 'graded',
          studentName: s.studentName || s.studentId || '',
        })))
      } catch { /* 该作业无提交 */ }
    }
    // 加载考试列表
    try {
      const examData = await authGet(`/api/courses/${courseId}/exams`)
      if (examData.exams) examItems.value = examData.exams
    } catch { /* 无考试 */ }
  } catch (e) { console.warn('loadCourseData failed:', e) }
  finally { loadingCourseData.value = false }
}

// ====== Exams ======
const examSelectedCourse = ref('')
const selectedExamId = ref(null)
const examSearchQuery = ref('')
const examStatusFilter = ref('all')
const examActiveId = ref(null)
const examScore = ref(78)
const examComment = ref('')
const examGrading = ref(false)
const examAiLoading = ref('') // 'cropgpt' | 'general' | ''
const examFeedback = ref('')

const selectedExam = computed(() => examItems.value.find(e => e.exam_id === selectedExamId.value))
function examSubCount() { return submissionItems.value.length }
async function onExamCourseChange() {
  selectedExamId.value = null; examActiveId.value = null
  await loadCourseData(examSelectedCourse.value)
}
function selectExam(e) { selectedExamId.value = e.exam_id; examActiveId.value = null }
const examSubmissions = computed(() =>
  selectedExamId.value
    ? submissionItems.value.map(s => ({ ...s }))
    : []
)
const filteredExamSubmissions = computed(() => {
  let l = examSubmissions.value
  if (examStatusFilter.value === 'pending') l = l.filter(s => !s.graded)
  if (examStatusFilter.value === 'graded') l = l.filter(s => s.graded)
  if (examSearchQuery.value) {
    const q = examSearchQuery.value.toLowerCase()
    l = l.filter(s => (s.studentName || '').toLowerCase().includes(q) || (s.studentId || '').toLowerCase().includes(q))
  }
  return l
})
const activeExamSub = computed(() => examSubmissions.value.find(s => s.id === examActiveId.value))
function selectExamSubmission(sub) {
  examActiveId.value = sub.id
  // 同步当前分数和评语
  examScore.value = sub.score ?? 78
  examComment.value = (sub.feedback && typeof sub.feedback === 'object') ? (sub.feedback.comment || sub.feedback.feedback || '') : ''
}

async function submitExamGrade() {
  const sub = examSubmissions.value.find(x => x.id === examActiveId.value)
  if (!sub) return
  examGrading.value = true
  try {
    const hwId = sub.hwId || selectedExamId.value
    const result = await gradeSubmission(
      examSelectedCourse.value, hwId, sub.studentId,
      examScore.value,
      { comment: examComment.value },
    )
    // 更新本地状态
    sub.graded = true; sub.score = examScore.value
    sub.status = 'graded'
    sub.gradedAt = result.submission?.gradedAt || new Date().toISOString()
    examFeedback.value = '✓ 评分已保存'
  } catch (e) {
    console.error('grade exam failed:', e)
    examFeedback.value = '✗ 保存失败: ' + (e.message || '未知错误')
  } finally { examGrading.value = false }
}

async function submitExamAiCropGpt() {
  const sub = activeExamSub.value; if (!sub) return
  examAiLoading.value = 'cropgpt'
  try {
    const result = await aiGradeCropGpt(examSelectedCourse.value, sub.hwId || selectedExamId.value, sub.studentId)
    if (result.feedback) examComment.value = result.feedback
    if (result.score != null) examScore.value = result.score
    examFeedback.value = '🌾 CropGPT 评估完成（接口预留）'
  } catch (e) { examFeedback.value = '✗ CropGPT 调用失败: ' + (e.message || '') }
  finally { examAiLoading.value = '' }
}

async function submitExamAiGeneral() {
  const sub = activeExamSub.value; if (!sub) return
  examAiLoading.value = 'general'
  try {
    const result = await aiGradeGeneral(examSelectedCourse.value, sub.hwId || selectedExamId.value, sub.studentId)
    if (result.feedback) examComment.value = result.feedback
    if (result.score != null) examScore.value = result.score
    examFeedback.value = '🤖 通用模型评估完成（接口预留）'
  } catch (e) { examFeedback.value = '✗ 通用模型调用失败: ' + (e.message || '') }
  finally { examAiLoading.value = '' }
}

const examDisplayAnswers = computed(() => {
  const sub = activeExamSub.value; if (!sub) return []
  const qs = homeworkQuestionMap.value[sub.hwId] || []
  const ans = typeof sub.answers === 'string' ? JSON.parse(sub.answers || '{}') : (sub.answers || {})
  return qs.map(q => ({
    stem: q.content || q.stem || '', maxScore: q.points || 10,
    typeLabel: q.type === 'choice' ? '选择题' : q.type === 'essay' ? '简答题' : '主观题',
    options: q.options || [],
    studentAnswer: ans[q.id] || '', studentPick: ans[q.id] || '',
    referenceAnswer: q.answer || '',
  }))
})

// ====== Reports ======
const reportSelectedCourse = ref('')
const selectedReportHwId = ref(null)
const reportSearchQuery = ref('')
const reportStatusFilter = ref('all')
const reportActiveId = ref(null)
const reportComment = ref('')
const reportGrading = ref(false)
const reportAiLoading = ref('')
const reportFeedback = ref('')

// 多维度评分
const reportDimensions = reactive([
  { key: 'completeness', label: '内容完整性', score: 22, max: 30, hints: [
    { label: '缺', threshold: 0, value: 8 }, { label: '一般', threshold: 10, value: 18 }, { label: '完整', threshold: 20, value: 26 }
  ]},
  { key: 'accuracy', label: '科学准确性', score: 18, max: 25, hints: [
    { label: '差', threshold: 0, value: 6 }, { label: '一般', threshold: 10, value: 15 }, { label: '准确', threshold: 18, value: 22 }
  ]},
  { key: 'practice', label: '实践应用', score: 14, max: 20, hints: [
    { label: '弱', threshold: 0, value: 5 }, { label: '一般', threshold: 8, value: 12 }, { label: '强', threshold: 14, value: 18 }
  ]},
  { key: 'structure', label: '逻辑结构', score: 11, max: 15, hints: [
    { label: '乱', threshold: 0, value: 4 }, { label: '一般', threshold: 6, value: 9 }, { label: '清晰', threshold: 10, value: 13 }
  ]},
  { key: 'writing', label: '语言表达', score: 7, max: 10, hints: [
    { label: '差', threshold: 0, value: 3 }, { label: '一般', threshold: 4, value: 6 }, { label: '好', threshold: 7, value: 9 }
  ]},
])
const reportTotalScore = computed(() => reportDimensions.reduce((s, d) => s + d.score, 0))

// 快捷评语
const quickComments = [
  '报告结构完整，内容详实。', '症状描述准确，观察细致。', '田间调查数据可靠，记录规范。',
  '病原鉴定方法正确，图片清晰。', '数据分析有深度，结论合理。', '建议补充病害显微照片。',
  '防治建议具有可操作性。', '标本采集数量充足，制作规范。', '发病率和病情指数计算正确。',
  '建议加强对病害发生规律的分析。', '格式规范，语言流畅。', '部分数据需要补充完善。',
]

// 图片占位符检测
function hasImagePlaceholder(answer) {
  if (!answer) return false
  return /\[图[片像]|\[附图\]|\[显微照片\]|\[田间照片\]|\[症状图\]|\[病原图\]|!\[.*?\]\(/i.test(answer)
}

function extractImageSlots(answer) {
  if (!answer) return []
  const slots = []
  // 匹配各种图片标记
  const patterns = [
    /\[图[片像]\s*[:：]?\s*(.+?)\]/g,
    /\[附图\]/g,
    /\[显微照片\]/g,
    /\[田间照片\]/g,
    /\[症状图\]/g,
    /\[病原图\]/g,
    /\[标本照片\]/g,
  ]
  for (const pattern of patterns) {
    let match
    while ((match = pattern.exec(answer)) !== null) {
      const raw = match[0]
      const hasLabel = raw.startsWith('[图') && match[1]
      let label = '附图'
      if (raw === '[显微照片]') label = '显微照片'
      else if (raw === '[田间照片]') label = '田间照片'
      else if (raw === '[症状图]') label = '症状图'
      else if (raw === '[病原图]') label = '病原图'
      else if (raw === '[标本照片]') label = '标本照片'
      else if (raw === '[附图]') label = '附图'
      else if (hasLabel) label = match[1].trim()
      const caption = hasLabel ? match[1].trim() : label
      slots.push({ label, caption, raw })
    }
  }
  return slots
}

const reportImageSlots = computed(() => {
  if (!activeReportSub.value) return []
  const qs = homeworkQuestionMap.value[activeReportSub.value.hwId] || []
  const ans = typeof activeReportSub.value.answers === 'string'
    ? JSON.parse(activeReportSub.value.answers || '{}') : (activeReportSub.value.answers || {})
  const allSlots = []
  for (const q of qs) {
    const answer = ans[q.id] || ''
    allSlots.push(...extractImageSlots(answer))
  }
  return allSlots
})

const reportHwList = computed(() =>
  homeworkItems.value.filter(h =>
    (h.title || '').includes('报告') || (h.title || '').includes('实习') || (h.title || '').includes('实训')
  )
)
function getHwSubCount(hwId) { return submissionItems.value.filter(s => s.hwId === hwId).length }
function getHwGradedCount(hwId) { return submissionItems.value.filter(s => s.hwId === hwId && s.status === 'graded').length }
async function onReportCourseChange() {
  selectedReportHwId.value = null; reportActiveId.value = null
  await loadCourseData(reportSelectedCourse.value)
}
function selectReportHw(h) { selectedReportHwId.value = h.hwId; reportActiveId.value = null }

const reportSubmissions = computed(() =>
  selectedReportHwId.value
    ? submissionItems.value.filter(s => s.hwId === selectedReportHwId.value).map(s => ({ ...s, graded: s.status === 'graded' }))
    : []
)
const filteredReportSubmissions = computed(() => {
  let l = reportSubmissions.value
  if (reportStatusFilter.value === 'pending') l = l.filter(s => !s.graded)
  if (reportStatusFilter.value === 'graded') l = l.filter(s => s.graded)
  if (reportSearchQuery.value) {
    const q = reportSearchQuery.value.toLowerCase()
    l = l.filter(s => (s.studentName || '').toLowerCase().includes(q) || (s.studentId || '').toLowerCase().includes(q))
  }
  return l
})
const activeReportSub = computed(() => reportSubmissions.value.find(s => s.id === reportActiveId.value))

// 报告正文：将所有题目答案拼接为文档
const reportSections = computed(() => {
  const sub = activeReportSub.value; if (!sub) return []
  const qs = homeworkQuestionMap.value[sub.hwId] || []
  const ans = typeof sub.answers === 'string' ? JSON.parse(sub.answers || '{}') : (sub.answers || {})
  return qs.map(q => ({
    stem: q.content || q.stem || '',
    answer: ans[q.id] || '',
  })).filter(s => s.answer) // 只显示有内容的章节
})
const reportWordCount = computed(() => reportSections.value.reduce((c, s) => c + (s.answer || '').length, 0))
const reportSectionCount = computed(() => reportSections.value.length)
const reportImageCount = computed(() => {
  // 统计答案中的图片标记 [image] 或 base64 图片
  let count = 0
  for (const s of reportSections.value) {
    const matches = (s.answer || '').match(/\[image\]|!\[.*?\]\(.*?\)|<img|data:image/gi)
    if (matches) count += matches.length
  }
  return count
})

function renderReportContent(text) {
  if (!text) return '<span style="color:var(--text-muted)">（未作答）</span>'
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 图片占位符高亮
    .replace(/\[图[片像]\s*[:：]?\s*(.+?)\]/gi, '<span class="inline-img-tag">📷 $1</span>')
    .replace(/\[附图\]/gi, '<span class="inline-img-tag">📷 附图</span>')
    .replace(/\[显微照片\]/gi, '<span class="inline-img-tag">🔬 显微照片</span>')
    .replace(/\[田间照片\]/gi, '<span class="inline-img-tag">🌾 田间照片</span>')
    .replace(/\[症状图\]/gi, '<span class="inline-img-tag">🦠 症状图</span>')
    .replace(/\[病原图\]/gi, '<span class="inline-img-tag">🧫 病原图</span>')
    .replace(/\[标本照片\]/gi, '<span class="inline-img-tag">📋 标本照片</span>')
    // 表格标记
    .replace(/\[表格\s*[:：]?\s*(.+?)\]/gi, '<span class="inline-table-tag">📊 $1</span>')
    // 数据高亮
    .replace(/(发病率|病情指数|调查面积|调查株数)[:：]\s*([\d.%]+)/g, '<span class="data-point"><strong>$1</strong>: <em>$2</em></span>')
  return '<p>' + html + '</p>'
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function selectReportSubmission(sub) {
  reportActiveId.value = sub.id
  reportComment.value = (sub.feedback && typeof sub.feedback === 'object') ? (sub.feedback.comment || sub.feedback.feedback || '') : ''
  // 从已保存的 feedback 恢复维度评分
  const fb = sub.feedback || {}
  const saved = fb.dimensions || fb.scores || null
  if (saved) {
    for (const dim of reportDimensions) {
      if (saved[dim.key] != null) dim.score = saved[dim.key]
    }
  } else {
    // 无历史评分，重置为默认值
    reportDimensions.forEach(d => { d.score = Math.round(d.max * 0.7) })
  }
}

async function submitReportGrade() {
  const sub = reportSubmissions.value.find(x => x.id === reportActiveId.value)
  if (!sub) return
  reportGrading.value = true
  try {
    const dimensions = {}
    reportDimensions.forEach(d => { dimensions[d.key] = d.score })
    const feedback = {
      comment: reportComment.value,
      dimensions,
      gradedAt: new Date().toISOString(),
    }
    const result = await gradeSubmission(
      reportSelectedCourse.value, sub.hwId, sub.studentId,
      reportTotalScore.value,
      feedback,
    )
    sub.graded = true; sub.score = reportTotalScore.value
    sub.status = 'graded'
    sub.feedback = feedback
    sub.gradedAt = result.submission?.gradedAt || new Date().toISOString()
    reportFeedback.value = '✓ 评分已保存'
  } catch (e) {
    console.error('grade report failed:', e)
    reportFeedback.value = '✗ 保存失败: ' + (e.message || '未知错误')
  } finally { reportGrading.value = false }
}

async function submitReportAiCropGpt() {
  const sub = activeReportSub.value; if (!sub) return
  reportAiLoading.value = 'cropgpt'
  try {
    const result = await aiGradeCropGpt(reportSelectedCourse.value, sub.hwId, sub.studentId)
    if (result.feedback) reportComment.value = (reportComment.value ? reportComment.value + '\n' : '') + '🌾 CropGPT: ' + result.feedback
    reportFeedback.value = '🌾 CropGPT 评估完成（接口预留）'
  } catch (e) { reportFeedback.value = '✗ CropGPT 调用失败: ' + (e.message || '') }
  finally { reportAiLoading.value = '' }
}

async function submitReportAiGeneral() {
  const sub = activeReportSub.value; if (!sub) return
  reportAiLoading.value = 'general'
  try {
    const result = await aiGradeGeneral(reportSelectedCourse.value, sub.hwId, sub.studentId)
    if (result.feedback) reportComment.value = (reportComment.value ? reportComment.value + '\n' : '') + '🤖 AI: ' + result.feedback
    reportFeedback.value = '🤖 通用模型评估完成（接口预留）'
  } catch (e) { reportFeedback.value = '✗ 通用模型调用失败: ' + (e.message || '') }
  finally { reportAiLoading.value = '' }
}

onMounted(() => { fetchCourses() })
</script>

<style scoped>
* { margin:0; padding:0; box-sizing:border-box; }
.main-area { flex:1; min-height:0; display:flex; gap:8px; }
.panel { background:var(--bg-card); border:1px solid var(--border-light); border-radius:16px; position:relative; overflow:hidden; display:flex; flex-direction:column; }
.panel-left { width:278px; min-width:250px; flex-shrink:0; background:var(--bg-soft,#fafbfa); }
.panel-center { flex:1; min-width:0; }
.panel-right { width:288px; min-width:260px; flex-shrink:0; }
.panel-toggle { position:absolute; top:50%; transform:translateY(-50%); z-index:10; width:22px; height:44px; border-radius:6px; border:1px solid var(--border-medium,#dcdcdc); background:var(--bg-card); color:var(--text-muted); cursor:pointer; display:flex; align-items:center; justify-content:center; padding:0; }
.panel-left .panel-toggle { right:2px; } .panel-right .panel-toggle { left:2px; }
.panel-toggle:hover { color:var(--accent,#121212); }
.panel.collapsed { width:38px !important; min-width:38px !important; }
.panel.collapsed > *:not(.panel-toggle) { display:none; }

.pl-header { flex-shrink:0; display:flex; align-items:center; justify-content:space-between; padding:14px 14px 0; z-index:2; }
.pl-title { font-size:0.84rem; font-weight:700; color:var(--text-primary); }
.pl-badge { font-size:0.66rem; color:var(--text-muted); background:var(--bg-tag,#f0f0f0); padding:2px 10px; border-radius:8px; font-weight:600; }
.pl-courses { padding:10px 14px; z-index:2; }
.course-select { width:100%; padding:8px 12px; border-radius:12px; border:1px solid var(--border-light); background:var(--bg-input,#fff); font-size:0.76rem; color:var(--text-primary); outline:none; cursor:pointer; }
.pl-homework-list { flex:1; overflow-y:auto; padding:0 10px; z-index:2; }
.homework-row { display:flex; align-items:center; gap:8px; padding:10px; border-radius:12px; cursor:pointer; transition:all 0.2s; border:1px solid transparent; margin-bottom:4px; }
.homework-row:hover { background:var(--bg-card); }
.homework-row.active { border-color:var(--border-light); background:var(--bg-card); }
.hw-icon { font-size:1.1rem; flex-shrink:0; } .hw-body { flex:1; min-width:0; }
.hw-title { font-size:0.76rem; font-weight:600; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.hw-meta { font-size:0.64rem; color:var(--text-muted); margin-top:2px; }
.hw-status { font-size:0.64rem; font-weight:600; color:var(--text-muted); flex-shrink:0; }

.pl-search { display:flex; align-items:center; gap:6px; margin:10px 14px; padding:7px 10px; background:var(--bg-input,#fff); border:1px solid var(--border-light); border-radius:10px; z-index:2; }
.pl-search-icon { width:13px; height:13px; stroke:var(--text-muted); fill:none; stroke-width:1.8; flex-shrink:0; }
.pl-search input { border:none; outline:none; background:transparent; font-size:0.72rem; color:var(--text-primary); width:100%; }
.pl-filters { display:flex; gap:5px; padding:0 14px 10px; z-index:2; }
.pl-chip { padding:4px 12px; border-radius:16px; font-size:0.66rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.2s; border:1px solid transparent; }
.pl-chip:hover { color:var(--text-secondary); background:var(--bg-tag); }
.pl-chip.on { color:var(--text-primary); background:var(--bg-card); border-color:var(--border-light); }
.pl-list { flex:1; overflow-y:auto; padding:0 10px; z-index:2; }
.submission-row { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:10px; cursor:pointer; transition:all 0.2s; border:1px solid transparent; animation: fadeIn 0.35s ease both; }
@keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
.submission-row:hover { background:var(--bg-card); } .submission-row.active { border-color:var(--border-light); background:var(--bg-card); }
.sr-rank { font-size:0.64rem; color:var(--text-muted); width:16px; text-align:center; flex-shrink:0; }
.sr-avatar { width:28px; height:28px; border-radius:50%; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; flex-shrink:0; color:var(--text-primary); font-weight:700; font-size:0.68rem; }
.sr-body { flex:1; min-width:0; } .sr-name { font-size:0.76rem; font-weight:600; color:var(--text-primary); } .sr-desc { font-size:0.64rem; color:var(--text-muted); margin-top:1px; }
.sr-tail { flex-shrink:0; } .sr-score { font-size:0.82rem; font-weight:700; color:var(--text-primary); } .sr-dot { display:block; width:6px; height:6px; border-radius:50%; background:var(--text-muted); opacity:0.3; }
.pl-empty { text-align:center; padding:32px 0; color:var(--text-muted); font-size:0.72rem; }

.center-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:10px; z-index:3; }
.empty-icon-wrap { width:52px; height:52px; border-radius:14px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; }
.center-scroll { flex:1; overflow-y:auto; padding:20px 24px; z-index:3; }
.student-bar { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--divider,#f0f0f0); }
.sb-left { display:flex; align-items:center; gap:10px; }
.sb-avatar { width:28px; height:28px; border-radius:6px; background:var(--accent,#121212); color:var(--bg-root,#fff); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.72rem; }
.sb-name { font-size:0.82rem; font-weight:600; color:var(--text-primary); } .sb-meta { font-size:0.64rem; color:var(--text-muted); margin-top:2px; }
.sb-status { font-size:0.68rem; font-weight:600; padding:4px 12px; border-radius:8px; border:1px solid var(--border-light); color:var(--text-muted); }
.sb-status.done { color:var(--text-primary); background:var(--bg-tag); }
.q-tabs { display:flex; align-items:center; gap:4px; margin-bottom:14px; }
.q-tab { padding:6px 15px; border-radius:18px; font-size:0.73rem; font-weight:500; color:var(--text-muted); } .q-tab.on { color:var(--text-primary); background:var(--bg-card); border:1px solid var(--border-light); }
.q-list { display:flex; flex-direction:column; gap:14px; }
.q-card { border-radius:16px; background:var(--bg-card); border:1px solid var(--border-light); }
.q-inner { padding:16px 20px; }
.q-top { display:flex; align-items:center; gap:8px; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid var(--divider,#f0f0f0); }
.q-idx { width:18px; height:18px; border-radius:50%; background:var(--accent,#121212); color:var(--bg-root,#fff); font-size:0.6rem; font-weight:700; display:flex; align-items:center; justify-content:center; }
.q-kind { font-size:0.66rem; color:var(--text-primary); font-weight:600; } .q-pts { font-size:0.66rem; color:var(--text-muted); margin-left:auto; }
.q-stem { font-size:0.82rem; color:var(--text-primary); font-weight:600; line-height:1.7; margin-bottom:8px; }
.q-opts { display:flex; flex-direction:column; gap:6px; margin-bottom:8px; }
.q-opt { display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:12px; border:1px solid var(--border-light); font-size:0.78rem; color:var(--text-secondary); }
.q-opt.picked { border-color:var(--accent); background:var(--bg-card); color:var(--text-primary); font-weight:600; }
.q-opt-letter { width:22px; height:22px; border-radius:50%; border:1.5px solid var(--border-medium); display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:600; color:var(--text-secondary); flex-shrink:0; }
.q-opt.picked .q-opt-letter { border-color:var(--accent); color:var(--accent); }
.q-answer-box { padding:12px 14px; border-radius:12px; border:1px solid var(--accent); background:var(--bg-card); margin-top:8px; }
.q-answer-label { font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--accent); margin-bottom:6px; }
.q-answer-text { font-size:0.82rem; color:var(--text-primary); line-height:1.8; }
.q-ref-box { padding:12px 14px; border-radius:12px; border:1px solid var(--border-light); background:var(--bg-soft); margin-top:8px; }
.q-ref-label { font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--text-secondary); margin-bottom:6px; }
.q-ref-text { font-size:0.82rem; color:var(--text-secondary); line-height:1.8; }

.pr-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:10px; color:var(--text-muted); z-index:3; }
.pr-scroll { flex:1; overflow-y:auto; padding:18px; display:flex; flex-direction:column; gap:16px; z-index:3; }
.pr-section { } .pr-sec-title { font-size:0.66rem; font-weight:700; letter-spacing:0.05em; color:var(--text-muted); margin-bottom:10px; text-transform:uppercase; display:flex; align-items:center; gap:10px; }
.pr-sec-title::after { content:''; flex:1; height:1px; background:var(--divider,#f0f0f0); }
.dim-row { display:flex; align-items:center; gap:10px; margin-bottom:9px; }
.dim-name { font-size:0.7rem; color:var(--text-secondary); width:56px; flex-shrink:0; }
.dim-bar { flex:1; height:6px; background:var(--border-light); border-radius:4px; overflow:hidden; }
.dim-bar i { display:block; height:100%; background:#526e5a; border-radius:4px; }
.dim-val { font-size:0.7rem; font-weight:600; color:var(--text-primary); width:44px; text-align:right; }
.dim-val small { font-size:0.6rem; color:var(--text-muted); }
.grade-range { width:100%; accent-color:#526e5a; }
.grade-textarea { width:100%; padding:10px; border:1px solid var(--border-light); border-radius:10px; font-size:0.78rem; resize:vertical; outline:none; background:var(--bg-card); color:var(--text-primary); }
.grade-start { width:100%; padding:10px; border-radius:12px; background:#526e5a; color:#fff; border:none; font-weight:600; font-size:0.8rem; cursor:pointer; }
.grade-start:hover { opacity:0.9; }
.notebook { background:var(--bg-soft); border:1px solid var(--border-light); border-radius:12px; padding:18px 16px; }
.notebook-score-row { display:flex; align-items:baseline; gap:6px; }
.notebook-score { font-size:1.5rem; font-weight:700; color:var(--accent); }
.notebook-score-label { font-size:0.78rem; color:var(--text-muted); }
.notebook-text { font-size:0.82rem; color:var(--text-muted); line-height:1.8; margin:8px 0 0; }
.grade-feedback { font-size:0.72rem; padding:8px 12px; border-radius:8px; background:rgba(82,110,90,0.06); color:#526e5a; border:1px solid rgba(82,110,90,0.15); }
.grade-feedback.error { background:rgba(220,38,38,0.06); color:#dc2626; border-color:rgba(220,38,38,0.15); }
.ai-cropgpt-btn { background:linear-gradient(135deg,#4a7c3f,#6b9e5a) !important; }
.ai-general-btn { background:linear-gradient(135deg,#4a5568,#5a6b7c) !important; }
.ai-spinner { display:inline-block; width:12px; height:12px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:4px; vertical-align:middle; }
@keyframes spin { to{transform:rotate(360deg)} }

/* ====== 实习报告专用样式 ====== */
.report-layout { flex:1; min-height:0; display:flex; gap:8px; }
.report-center { background:#fafbf9; }
.report-empty-icon { background:#f5f0e8 !important; color:#8b7355; }

.report-reader { flex:1; overflow-y:auto; display:flex; flex-direction:column; }
.report-header { padding:20px 24px 0; flex-shrink:0; }
.rh-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.rh-student { display:flex; align-items:center; gap:12px; }
.rh-avatar { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,#8b7355,#a0845c); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.88rem; }
.rh-name { font-size:0.9rem; font-weight:700; color:var(--text-primary); }
.rh-meta { font-size:0.68rem; color:var(--text-muted); margin-top:2px; }
.rh-badge { font-size:0.68rem; font-weight:600; padding:5px 14px; border-radius:8px; border:1px solid rgba(139,115,85,0.3); color:#8b7355; background:rgba(139,115,85,0.06); }
.rh-badge.done { color:#526e5a; border-color:rgba(82,110,90,0.3); background:rgba(82,110,90,0.06); }
.rh-stats { display:flex; gap:12px; padding-bottom:16px; border-bottom:1px solid rgba(139,115,85,0.12); }
.rh-stat { flex:1; text-align:center; padding:12px 8px; background:#fff; border:1px solid rgba(139,115,85,0.1); border-radius:10px; }
.rh-stat-num { display:block; font-size:1.2rem; font-weight:700; color:#8b7355; }
.rh-stat-label { display:block; font-size:0.62rem; color:var(--text-muted); margin-top:2px; }

.report-body { padding:20px 24px; }
.report-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:56px 0; color:var(--text-muted); gap:10px; }
.report-section { margin-bottom:24px; }
.rs-title { font-size:0.82rem; font-weight:700; color:#8b7355; padding:6px 0; border-bottom:2px solid rgba(139,115,85,0.15); margin-bottom:12px; }
.rs-content { font-size:0.84rem; color:var(--text-primary); line-height:2; }
.rs-content :deep(p) { margin-bottom:12px; text-indent:2em; }
.inline-img-tag { display:inline-block; padding:2px 8px; background:rgba(139,115,85,0.08); border:1px solid rgba(139,115,85,0.2); border-radius:4px; font-size:0.72rem; color:#8b7355; }

/* 多维度评分 */
.dim-card { padding:10px 0; border-bottom:1px solid var(--divider,#f0f0f0); }
.dim-card:last-child { border-bottom:none; }
.dim-card-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.dim-card-name { font-size:0.72rem; font-weight:600; color:var(--text-primary); }
.dim-card-score { font-size:0.78rem; font-weight:700; color:#8b7355; }
.dim-card-score small { font-size:0.6rem; color:var(--text-muted); font-weight:400; }
.dim-slider { width:100%; accent-color:#8b7355; margin-bottom:6px; }
.dim-card-hints { display:flex; gap:4px; }
.dim-hint { padding:2px 8px; border-radius:6px; font-size:0.6rem; color:var(--text-muted); border:1px solid var(--border-light); cursor:pointer; transition:all 0.15s; }
.dim-hint:hover { color:#8b7355; border-color:#8b7355; }
.dim-hint.active { color:#fff; background:#8b7355; border-color:#8b7355; }
.dim-total-row { display:flex; align-items:center; justify-content:space-between; padding-top:12px; margin-top:4px; border-top:2px solid rgba(139,115,85,0.2); }
.dim-total-label { font-size:0.78rem; font-weight:700; color:var(--text-primary); }
.dim-total-score { font-size:1.3rem; font-weight:700; color:#8b7355; }
.dim-total-score small { font-size:0.7rem; color:var(--text-muted); font-weight:400; }

/* 报告评分结果 */
.report-score-card { display:flex; align-items:baseline; justify-content:center; gap:4px; padding:20px 0; background:rgba(139,115,85,0.04); border:1px solid rgba(139,115,85,0.12); border-radius:12px; }
.rsc-big { font-size:2.4rem; font-weight:700; color:#8b7355; line-height:1; }
.rsc-label { font-size:1rem; color:var(--text-muted); }
.report-feedback-text { font-size:0.82rem; color:var(--text-secondary); line-height:1.8; padding:12px; background:rgba(139,115,85,0.04); border:1px solid rgba(139,115,85,0.1); border-radius:10px; white-space:pre-wrap; }

/* 快捷评语 */
.quick-comments { display:flex; flex-wrap:wrap; gap:4px; }
.qc-chip { padding:4px 8px; border-radius:12px; font-size:0.62rem; color:var(--text-muted); border:1px solid var(--border-light); cursor:pointer; transition:all 0.15s; }
.qc-chip:hover { color:#8b7355; border-color:rgba(139,115,85,0.4); background:rgba(139,115,85,0.04); }
.save-grade-btn { background:linear-gradient(135deg,#8b7355,#a0845c) !important; }

/* 图片占位符 */
.report-images { display:grid; grid-template-columns:repeat(auto-fill, minmax(140px,1fr)); gap:12px; margin-top:14px; }
.report-img-card { border:1px dashed rgba(139,115,85,0.3); border-radius:10px; overflow:hidden; background:rgba(139,115,85,0.02); }
.report-img-placeholder { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; padding:28px 12px; background:linear-gradient(135deg,rgba(139,115,85,0.04),rgba(139,115,85,0.02)); color:#8b7355; }
.rimg-label { font-size:0.7rem; font-weight:600; color:#8b7355; }
.rimg-caption { display:block; text-align:center; font-size:0.64rem; color:var(--text-muted); padding:8px 10px; }

/* 底部附件栏 */
.report-attachment-bar { margin-top:24px; padding:16px; background:#fff; border:1px solid rgba(139,115,85,0.12); border-radius:12px; }
.rab-title { font-size:0.72rem; font-weight:700; color:#8b7355; margin-bottom:10px; }
.rab-grid { display:flex; gap:8px; flex-wrap:wrap; }
.rab-thumb { display:flex; flex-direction:column; align-items:center; gap:4px; font-size:0.6rem; color:var(--text-muted); }
.rab-thumb-inner { width:52px; height:52px; border-radius:8px; border:1px solid rgba(139,115,85,0.15); background:rgba(139,115,85,0.03); display:flex; align-items:center; justify-content:center; color:#8b7355; }

/* 数据标记 */
.data-point { display:inline-block; padding:1px 6px; background:rgba(139,115,85,0.06); border-radius:4px; margin:0 2px; font-size:0.8rem; }
.data-point strong { color:#8b7355; font-weight:600; }
.data-point em { color:var(--text-primary); font-weight:700; font-style:normal; }

/* 表格标记 */
.inline-table-tag { display:inline-block; padding:2px 8px; background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2); border-radius:4px; font-size:0.72rem; color:#3b82f6; }
</style>
