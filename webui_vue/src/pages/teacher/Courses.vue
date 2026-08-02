<template>
  <div class="courses-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>我的课程</h2>
        <span class="header-summary">
          共 {{ filteredCourses.length }} 门课程 · {{ totalStudents }} 名学生
        </span>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg viewBox="0 0 20 20" class="search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
          <input v-model="searchQuery" placeholder="搜索课程名称、学科..." />
        </div>
        <button class="btn-primary" @click="showCreate = true">
          <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="10" y1="4" x2="10" y2="16"/><line x1="4" y1="10" x2="16" y2="10"/></svg>
          <span>创建课程</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-hint">加载中...</div>
    <div v-else-if="courses.length === 0" class="empty-hint">
      <p>还没有课程，点击上方按钮创建</p>
    </div>
    <div v-else>
      <!-- 课程网格 -->
      <div class="course-grid">
        <div v-for="c in filteredCourses" :key="c.courseId" class="course-card" @click="openCourse(c.courseId)">
          <div>
            <div class="course-card-header">
              <span class="course-badge">{{ c.subject || '未分类' }}</span>
              <span class="course-code">码：{{ c.joinCode }}</span>
            </div>
            <h3 class="course-title">{{ c.courseName }}</h3>
            <div class="course-meta">
              <span>{{ c.grade }}</span>
              <span>{{ c.memberCount || 0 }} 名学生</span>
            </div>
          </div>
          <div class="course-footer">
            <div class="course-activity">
              <div class="activity-bar" :style="{ width: Math.min(100, (c.memberCount || 0) * 5) + '%' }"></div>
            </div>
            <span class="course-status">进行中</span>
          </div>
        </div>
      </div>

      <!-- 课程数据监控 -->
      <h4 class="section-subtitle"><i class="title-bar"></i>课程数据监控</h4>
      <div class="info-row">
        <div class="info-box">
          <div class="overview-pending">
            <span class="pending-num">{{ pendingCount }}</span>
            <span class="pending-label">份待批改作业</span>
            <div class="pending-bar"><div class="pending-bar-fill" :style="{ width: gradedPercent + '%' }"></div></div>
          </div>
          <div class="overview-stats">
            <div class="stat-col"><div class="stat-num">{{ courses.length }}</div><div class="stat-lbl">活跃课程</div></div>
            <div class="stat-col"><div class="stat-num">{{ totalStudents }}</div><div class="stat-lbl">在读学生</div></div>
            <div class="stat-col"><div class="stat-num">{{ courses.reduce((s,c)=>s+(c.memberCount||0),0) }}</div><div class="stat-lbl">选课人次</div></div>
          </div>
        </div>
        <div class="info-box">
          <h5 class="col-title">即将截止</h5>
          <div class="deadline-list">
            <div v-for="d in upcomingDeadlines" :key="d.hwId" class="deadline-card">
              <div class="deadline-left"><div class="deadline-info"><span class="deadline-course">{{ d.courseName }}</span><span class="deadline-task">{{ d.title }}</span></div></div>
              <span class="deadline-badge">{{ d.deadline }}</span>
            </div>
            <div v-if="!upcomingDeadlines.length" class="empty-mini">暂无截止任务</div>
          </div>
        </div>
        <div class="info-box">
          <h5 class="col-title">最新提交</h5>
          <div class="activity-timeline">
            <div v-for="s in recentSubmissions" :key="s.id" class="timeline-item">
              <span class="timeline-course">{{ s.studentName }} · {{ s.courseName }}</span>
              <span class="timeline-time">{{ s.time }}</span>
            </div>
            <div v-if="!recentSubmissions.length" class="empty-mini">暂无提交</div>
          </div>
        </div>
        <div class="info-box">
          <h5 class="col-title">作业概览</h5>
          <div class="overview-stats" style="grid-template-columns:1fr 1fr">
            <div class="stat-col"><div class="stat-num">{{ totalHomework }}</div><div class="stat-lbl">布置作业</div></div>
            <div class="stat-col"><div class="stat-num">{{ totalSubmissions }}</div><div class="stat-lbl">收到提交</div></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 创建课程对话框 -->
  <div v-if="showCreate" class="dialog-overlay" @click.self="showCreate = false">
    <div class="dialog-card">
      <h3>创建课程</h3>
      <div class="form-group">
        <label>课程名称</label>
        <input v-model="form.courseName" placeholder="如：园艺植物栽培学" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>学科</label>
          <select v-model="form.subject">
            <option value="">请选择</option>
            <option v-for="s in subjects" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>年级</label>
          <select v-model="form.grade">
            <option value="">请选择</option>
            <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>课程简介</label>
        <textarea v-model="form.description" rows="3" placeholder="可选"></textarea>
      </div>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="form.isPublic" />
          公开课程（所有学生可见）
        </label>
      </div>
      <p v-if="createError" class="login-error">{{ createError }}</p>
      <div class="dialog-actions">
        <button class="btn-secondary" @click="showCreate = false">取消</button>
        <button class="btn-primary" @click="handleCreate" :disabled="creating">
          {{ creating ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'

const router = useRouter()
const { user, logout: authLogout } = useAuth()
const { courses, fetchCourses, createCourse, fetchHomeworkList, fetchSubmissions } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

function onLogout() { authLogout(); router.push('/login') }

const searchQuery = ref('')
const loading = ref(false)

async function loadCourses() {
  if (!user.value) return
  loading.value = true
  try {
    await fetchCourses()
    await loadMonitoringData()
  } catch (e) {
    console.warn('[courses] load failed:', e.message)
  } finally {
    loading.value = false
  }
}

function openCourse(courseId) { router.push(`/teacher/courses/${courseId}`) }

const filteredCourses = computed(() => {
  if (!searchQuery.value.trim()) return courses.value
  const q = searchQuery.value.trim().toLowerCase()
  return courses.value.filter(c =>
    (c.courseName || '').toLowerCase().includes(q) ||
    (c.subject || '').toLowerCase().includes(q)
  )
})

const totalStudents = computed(() => courses.value.reduce((s, c) => s + (c.memberCount || 0), 0))

// Real monitoring data
const homeworkItems = ref([])
const submissionItems = ref([])

async function loadMonitoringData() {
  const allHw = []
  const allSubs = []
  for (const c of courses.value) {
    try {
      const hw = await fetchHomeworkList(c.courseId) || []
      allHw.push(...hw.map(h => ({ ...h, courseName: c.courseName })))
      for (const h of hw) {
        try {
          const subs = await fetchSubmissions(c.courseId, h.hwId) || []
          allSubs.push(...subs.map(s => ({ ...s, courseName: c.courseName, hwTitle: h.title })))
        } catch {}
      }
    } catch {}
  }
  homeworkItems.value = allHw
  submissionItems.value = allSubs
}

const totalHomework = computed(() => homeworkItems.value.length)
const totalSubmissions = computed(() => submissionItems.value.length)
const pendingCount = computed(() => submissionItems.value.filter(s => s.status !== 'graded').length)
const gradedCount = computed(() => submissionItems.value.filter(s => s.status === 'graded').length)
const gradedPercent = computed(() => {
  const total = pendingCount.value + gradedCount.value
  return total ? Math.round(gradedCount.value / total * 100) : 0
})
const upcomingDeadlines = computed(() =>
  homeworkItems.value.filter(h => h.deadline).sort((a,b) => (a.deadline||'').localeCompare(b.deadline||'')).slice(0, 4)
)
const recentSubmissions = computed(() =>
  submissionItems.value.slice(-5).reverse().map(s => ({
    id: s.id, studentName: s.studentName||s.studentId, courseName: s.courseName,
    time: s.submittedAt ? new Date(s.submittedAt).toLocaleDateString('zh-CN') : '今天'
  }))
)

const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const subjects = ['农学', '园艺', '植物保护', '土壤肥料', '智慧农业', '畜牧兽医', '食品科学', '农业经济']
const grades = ['大一', '大二', '大三', '大四', '研一', '研二']

const form = reactive({
  courseName: '', subject: '', grade: '', description: '', isPublic: true,
})

async function handleCreate() {
  if (!form.courseName.trim()) { createError.value = '请输入课程名称'; return }
  creating.value = true
  createError.value = ''
  try {
    const data = {
      courseName: form.courseName.trim(),
      subject: form.subject,
      grade: form.grade,
      description: form.description.trim(),
      isPublic: form.isPublic,
      teacherName: user.value.userId,
    }
    await createCourse(data)
    showCreate.value = false
    Object.assign(form, { courseName: '', subject: '', grade: '', description: '', isPublic: true })
    await loadCourses()
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  if (!user.value) return
  loadCourses()
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
  --success: #0d9488;
  --warning: #f59e0b;
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
  --bg-card: rgba(255, 255, 255, 0.85);
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
.courses-page {
  width: 100%;
  padding: 20px 24px;
  background: var(--bg-root);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
  height: 100%;
  border: 1px solid var(--border-light);
  border-radius: 16px;
  background: var(--bg-card);
  margin: 8px;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.header-left h2 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-summary {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: monospace;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 12px;
  transition: all 0.3s;
  width: 256px;
}

.search-box:focus-within {
  border-color: var(--accent);
}

.search-icon {
  width: 14px;
  height: 14px;
  stroke: var(--text-muted);
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

.search-box input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.8rem;
  color: var(--text-primary);
  font-family: inherit;
  width: 100%;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

/* 课程网格 */
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.course-card {
  background: var(--bg-card-alt);
  border: 1.5px solid #526e5a;
  border-radius: 14px;
  padding: 18px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.course-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

.course-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.course-badge {
  background: rgba(82,110,90,0.08);
  color: #526e5a;
  font-size: 0.62rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
  flex-shrink: 0;
}

.course-code {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: monospace;
  flex-shrink: 0;
}

.course-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-meta {
  display: flex;
  gap: 10px;
  font-size: 0.68rem;
  color: var(--text-muted);
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--divider);
}

.course-status {
  font-size: 0.6rem;
  font-weight: 600;
  color: #526e5a;
  background: rgba(82,110,90,0.06);
  padding: 2px 8px;
  border-radius: 6px;
}

/* Monitoring */
.section-subtitle { font-size:0.82rem; font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:8px; margin:0 0 14px 0; }
.title-bar { width:4px; height:14px; background:#526e5a; border-radius:2px; display:inline-block; }
.info-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
.info-box { background:var(--bg-card); border:1.5px solid #526e5a; border-radius:14px; padding:16px; display:flex; flex-direction:column; overflow:hidden; }
.col-title { font-size:0.68rem; font-weight:700; color:var(--text-muted); margin:0 0 10px 0; padding-bottom:8px; border-bottom:1px solid var(--divider); }
.overview-pending { text-align:center; margin-bottom:8px; }
.pending-num { font-size:2.2rem; font-weight:700; color:var(--text-primary); line-height:1; }
.pending-label { font-size:0.7rem; color:var(--text-muted); display:block; margin:4px 0; }
.pending-bar { width:80px; height:4px; background:var(--border-light); border-radius:2px; overflow:hidden; margin:8px auto; }
.pending-bar-fill { height:100%; background:#526e5a; border-radius:2px; transition:width 0.6s; }
.overview-stats { display:grid; grid-template-columns:repeat(3,1fr); text-align:center; padding-top:10px; border-top:1px solid var(--divider); margin-top:8px; gap:4px; }
.stat-col { display:flex; flex-direction:column; align-items:center; }
.stat-num { font-size:0.82rem; font-weight:700; color:var(--text-primary); }
.stat-lbl { font-size:0.58rem; color:var(--text-muted); }
.deadline-list { display:flex; flex-direction:column; gap:6px; flex:1; }
.deadline-card { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; border-radius:10px; background:var(--bg-card-alt); border:1px solid var(--border-light); font-size:0.72rem; }
.deadline-course { font-weight:700; color:var(--text-primary); }
.deadline-task { font-size:0.64rem; color:var(--text-muted); margin-top:2px; display:block; }
.deadline-badge { font-size:0.6rem; font-weight:600; color:#526e5a; white-space:nowrap; }
.activity-timeline { display:flex; flex-direction:column; gap:6px; flex:1; }
.timeline-item { display:flex; justify-content:space-between; align-items:center; font-size:0.7rem; padding:4px 0; }
.timeline-course { color:var(--text-secondary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.timeline-time { color:var(--text-muted); font-size:0.64rem; flex-shrink:0; margin-left:8px; }
.empty-mini { text-align:center; color:var(--text-muted); font-size:0.72rem; padding:20px 0; }

/* 空状态 */
.loading-hint,
.empty-hint {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px dashed var(--border-medium);
}

/* 对话框 */
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
  width: 460px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.dialog-card h3 {
  margin: 0 0 20px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: 10px;
  font-size: 0.85rem;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  color: var(--text-primary);
  transition: border 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--accent);
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .form-group {
  flex: 1;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem !important;
  color: var(--text-primary);
  cursor: pointer;
}

.checkbox-label input[type='checkbox'] {
  width: auto !important;
  accent-color: var(--accent);
}

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
  padding: 10px 24px;
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

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.login-error {
  color: var(--danger);
  font-size: 0.8rem;
  margin-top: 8px;
}
</style>
