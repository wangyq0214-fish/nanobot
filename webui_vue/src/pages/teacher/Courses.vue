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

      <!-- 统一小标题 -->
      <h4 class="section-subtitle"><i class="title-bar"></i>课程数据监控</h4>

      <!-- 四个监控舱 -->
      <div class="info-row">
        <!-- 监控舱 1：待批改作业 -->
        <div class="info-box">
          <div class="overview-pending">
            <span class="pending-num">{{ pendingCount }}</span>
            <span class="pending-label">份待批改作业</span>
            <span class="pending-sub">已批改 {{ gradedPercent }}%</span>
            <div class="pending-bar">
              <div class="pending-bar-fill" :style="{ width: gradedPercent + '%' }"></div>
            </div>
          </div>
          <div class="overview-stats">
            <div class="stat-item">
              <div class="stat-num">{{ activeCourses }}</div>
              <div class="stat-label">活跃课程</div>
            </div>
            <div class="stat-item">
              <div class="stat-num">{{ todaySubmissions }}</div>
              <div class="stat-label">今日提交</div>
            </div>
            <div class="stat-item">
              <div class="stat-num">{{ avgGradingTime }}</div>
              <div class="stat-label">平均批时</div>
            </div>
          </div>
        </div>

        <!-- 监控舱 2：即将截止 -->
        <div class="info-box">
          <h5 class="col-title">
            <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="10" r="8"/><polyline points="10 5 10 10 14 12"/></svg>
            即将截止
          </h5>
          <div class="deadline-list">
            <div v-for="d in upcomingDeadlines" :key="d.id" class="deadline-card" :class="'urgency-' + d.urgency">
              <div class="deadline-left">
                <div class="deadline-icon" :class="d.urgency"></div>
                <div class="deadline-info">
                  <span class="deadline-course">{{ d.course }}</span>
                  <span class="deadline-task">{{ d.title }}</span>
                </div>
              </div>
              <div class="deadline-right">
                <span class="deadline-badge" :class="d.urgency">{{ d.due }}</span>
              </div>
            </div>
            <div v-if="upcomingDeadlines.length === 0" class="empty-mini">暂无即将截止的任务</div>
          </div>
        </div>

        <!-- 监控舱 3：最新动态 -->
        <div class="info-box">
          <h5 class="col-title">
            <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            最新动态
          </h5>
          <div class="activity-timeline">
            <div v-for="(act, idx) in courseActivities" :key="'act'+idx" class="timeline-item">
              <div class="timeline-content">
                <span class="timeline-course">{{ act.course }} · {{ act.desc }}</span>
              </div>
              <span class="timeline-time">{{ act.time }}</span>
            </div>
            <div v-if="courseActivities.length === 0" class="empty-mini">暂无动态</div>
          </div>
        </div>

        <!-- 监控舱 4：结课倒计时 -->
        <div class="info-box">
          <div class="box4-header">
            <h5 class="col-title" style="margin-bottom:0; border-bottom:none; padding-bottom:0;">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z"/><path d="M16 2v4M8 2v4M4 10h16"/></svg>
              {{ calendarTab === 'countdown' ? '结课倒计时' : '本周课程' }}
            </h5>
            <div class="tab-switch">
              <button class="switch-btn" :class="{ active: calendarTab === 'countdown' }" @click="calendarTab = 'countdown'">日历</button>
              <button class="switch-btn" :class="{ active: calendarTab === 'schedule' }" @click="calendarTab = 'schedule'">看板</button>
            </div>
          </div>
          <div v-if="calendarTab === 'countdown'" class="calendar-section">
            <div class="countdown-grid">
              <div v-for="(item, idx) in countdowns" :key="'cd'+idx" class="countdown-card">
                <div class="cd-inner">
                  <div class="cd-ring">
                    <svg viewBox="0 0 36 36" class="cd-ring-svg">
                      <path class="cd-ring-bg" stroke-width="2" stroke="currentColor" fill="none"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path class="cd-ring-fill" stroke-width="2.2" stroke-linecap="round" stroke="currentColor" fill="none"
                        :stroke-dasharray="(Math.min(item.remaining, 90) / 90 * 100) + ', 100'"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    </svg>
                    <div class="cd-number">
                      <span class="cd-num">{{ item.remaining }}</span>
                      <span class="cd-unit">天</span>
                    </div>
                  </div>
                  <div class="cd-label">
                    <span class="cd-course-name">{{ item.course }}</span>
                    <span class="cd-sub-text">剩余时间</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="countdowns.length === 0" class="empty-mini">暂无倒计时数据</div>
          </div>
          <div v-if="calendarTab === 'schedule'" class="todo-section">
            <div class="todo-list">
              <div v-for="(item, idx) in weekCourses" :key="'wc'+idx" class="todo-item">
                <span class="todo-time">{{ item.day }} {{ item.time }}</span>
                <span class="todo-course">{{ item.course }}</span>
              </div>
            </div>
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
const { courses, fetchCourses, createCourse } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

function onLogout() { authLogout(); router.push('/login') }

const searchQuery = ref('')
const loading = ref(false)

async function loadCourses() {
  if (!user.value) return
  loading.value = true
  try {
    await fetchCourses()
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

const pendingCount = computed(() => Math.max(0, courses.value.length * 3))
const gradedPercent = computed(() => {
  const total = pendingCount.value + Math.floor(courses.value.length * 2)
  return total ? Math.round(((total - pendingCount.value) / total) * 100) : 0
})

const activeCourses = computed(() => courses.value.length)
const todaySubmissions = computed(() => Math.min(courses.value.length * 2, 8))
const avgGradingTime = computed(() => courses.value.length ? '12 min' : '--')

const upcomingDeadlines = computed(() => {
  if (courses.value.length === 0) return []
  const tasks = ['课后作业', '实验报告', '单元测试', '期中论文']
  const dates = ['明天', '后天', '周五', '下周一']
  return courses.value.slice(0, 4).map((c, i) => ({
    id: i,
    course: c.courseName || `课程${i+1}`,
    title: tasks[i % 4],
    due: dates[i % 4],
    urgency: i < 2 ? 'urgent' : i === 2 ? 'normal' : 'relax',
  }))
})

const courseActivities = computed(() => {
  if (courses.value.length === 0) return []
  const acts = [
    { type: 'join', course: courses.value[0]?.courseName || '园艺学', desc: '新加入 3 名学生', time: '10m' },
    { type: 'submission', course: courses.value.length > 1 ? courses.value[1].courseName : (courses.value[0]?.courseName || '园艺学'), desc: '收到 5 份作业提交', time: '1h' },
    { type: 'notice', course: courses.value[0]?.courseName || '园艺学', desc: '发布了新作业', time: '昨天' },
    { type: 'grade', course: courses.value.length > 1 ? courses.value[1].courseName : (courses.value[0]?.courseName || '园艺学'), desc: '批改了 8 份作业', time: '2天前' },
  ]
  return acts
})

const weekCourses = computed(() => {
  if (courses.value.length === 0) return []
  const days = ['周一', '周二', '周三', '周四', '周五']
  return courses.value.slice(0, 3).map((c, i) => ({
    course: c.courseName,
    day: days[i],
    time: '8:00-9:40',
  }))
})

const countdowns = computed(() => {
  if (courses.value.length === 0) return []
  const daysLeft = [21, 45, 7]
  return courses.value.slice(0, 3).map((c, i) => ({
    course: c.courseName,
    remaining: daysLeft[i % 3],
  }))
})

const calendarTab = ref('countdown')

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
  padding: 24px 36px 28px 36px;
  background: var(--bg-root);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
  height: 100%;
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
  border: 1px solid var(--border-card);
  border-radius: 16px;
  padding: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 128px;
}

.course-card:hover {
  border-color: var(--accent);
}

.course-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.course-badge {
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.6rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
}

.course-code {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: monospace;
}

.course-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 12px 0 4px;
}

.course-meta {
  display: flex;
  gap: 8px;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: monospace;
}

.course-activity {
  width: 100%;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  margin-top: auto;
  overflow: hidden;
}

.activity-bar {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.6s;
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--divider);
}

.course-status {
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--status-text);
  background: var(--status-bg);
  border: 1px solid var(--status-border);
  padding: 2px 8px;
  border-radius: 6px;
}

/* 统一小标题 */
.section-subtitle {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
}

.title-bar {
  width: 4px;
  height: 14px;
  background: var(--accent);
  border-radius: 2px;
  display: inline-block;
}

/* 四个框 */
.info-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-top: 4px;
}

.info-box {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.003);
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 框1：概况 */
.overview-pending {
  text-align: center;
  margin-bottom: 8px;
}

.pending-num {
  font-family: monospace;
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.pending-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
  margin: 4px 0;
}

.pending-bar {
  width: 96px;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  overflow: hidden;
  margin: 8px auto;
}

.pending-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.6s;
}

.pending-sub {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: monospace;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  text-align: center;
  padding-top: 12px;
  border-top: 1px solid var(--divider);
  margin-top: 8px;
  gap: 4px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: monospace;
}

.stat-label {
  font-size: 0.6rem;
  color: var(--text-muted);
}

/* 框2：即将截止 */
.col-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-muted);
  margin: 0 0 8px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--divider);
  display: flex;
  align-items: center;
  gap: 6px;
}

.deadline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.deadline-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--bg-card-alt);
  border: 1px solid var(--border-light);
  transition: all 0.25s ease;
}

.deadline-card:hover {
  transform: translateX(2px);
}

.deadline-card.urgency-urgent {
  border-left: 3px solid var(--danger);
}

.deadline-card.urgency-normal {
  border-left: 3px solid var(--warning);
}

.deadline-card.urgency-relax {
  border-left: 3px solid var(--text-muted);
}

.deadline-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.deadline-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.deadline-icon.urgent {
  background: var(--warning);
}

.deadline-icon.normal {
  background: var(--warning);
}

.deadline-icon.relax {
  background: var(--text-muted);
}

.deadline-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.deadline-course {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.deadline-task {
  font-size: 0.6rem;
  color: var(--text-muted);
}

.deadline-right {
  flex-shrink: 0;
}

.deadline-badge {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.6rem;
  font-weight: 700;
}

.deadline-badge.urgent {
  background: rgba(248, 113, 113, 0.12);
  color: var(--danger);
  border: 1px solid rgba(248, 113, 113, 0.2);
}

.deadline-badge.normal {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.deadline-badge.relax {
  background: var(--accent-soft);
  color: var(--text-muted);
  border: 1px solid var(--border-light);
}

.empty-mini {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 24px 0;
}

/* 框3：最新动态 */
.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.timeline-course {
  font-size: 0.7rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.timeline-time {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: monospace;
  flex-shrink: 0;
  margin-left: 8px;
}

/* 框4 切换 */
.box4-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--divider);
}

.tab-switch {
  display: flex;
  gap: 4px;
  background: var(--accent-soft);
  padding: 2px;
  border-radius: 8px;
}

.switch-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 0.6rem;
  transition: all 0.2s;
  color: var(--text-muted);
  font-weight: 500;
}

.switch-btn:hover {
  color: var(--text-primary);
}

.switch-btn.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 结课倒计时 */
.countdown-grid {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
  flex: 1;
  align-items: center;
}

.countdown-card {
  flex: 1;
  max-width: 120px;
  text-align: center;
}

.cd-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.cd-ring {
  position: relative;
  width: 64px;
  height: 64px;
}

.cd-ring-svg {
  width: 64px;
  height: 64px;
  transform: rotate(-90deg);
}

.cd-ring-bg {
  fill: none;
  stroke: var(--border-light);
  stroke-width: 2;
}

.cd-ring-fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-dasharray: 100;
  transition: stroke-dashoffset 1s ease;
}

.cd-number {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.cd-num {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.cd-unit {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.cd-label {
  text-align: center;
}

.cd-course-name {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-muted);
  display: block;
}

.cd-sub-text {
  font-size: 0.55rem;
  color: var(--text-muted);
}

/* 本周课程 */
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  background: var(--bg-card-alt);
  border: 1px solid var(--border-light);
}

.todo-time {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: monospace;
}

.todo-course {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

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
