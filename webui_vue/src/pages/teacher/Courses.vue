<template>
  <div class="app-shell">
    <TeacherNav active-tab="courses" @logout="onLogout" />

    <div class="main-area">
      <div class="courses-page">
        <!-- 页面头部 -->
        <div class="page-header">
          <div class="header-left">
            <h2>我的课程</h2>
            <span class="header-summary">
              共 {{ filteredCourses.length }} 门 · {{ totalStudents }} 名学生
            </span>
          </div>
          <div class="header-right">
            <div class="search-box">
              <svg viewBox="0 0 20 20" class="search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
              <input v-model="searchQuery" placeholder="搜索课程名称、学科..." />
            </div>
            <button class="btn-primary" @click="showCreate = true">+ 创建课程</button>
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
              <div class="course-card-header">
                <span class="course-badge">{{ c.subject || '未分类' }}</span>
                <span class="course-code">码: {{ c.joinCode }}</span>
              </div>
              <h3 class="course-title">{{ c.courseName }}</h3>
              <div class="course-meta">
                <span>{{ c.grade }}</span>
                <span>{{ c.memberCount || 0 }} 名学生</span>
              </div>
              <div class="course-activity">
                <div class="activity-bar" :style="{ width: Math.min(100, (c.memberCount || 0) * 5) + '%' }"></div>
              </div>
              <div class="course-footer">
                <span class="course-status">进行中</span>
              </div>
            </div>
          </div>

          <!-- 统一小标题 -->
          <h4 class="section-subtitle"><i class="title-bar"></i>课程数据</h4>

          <!-- 四个框：高度统一（stretch 默认） -->
          <div class="info-row">
            <!-- 框1：课程概况 -->
            <div class="info-box">
              <div class="overview-pending">
                <span class="pending-num">{{ pendingCount }}</span>
                <span class="pending-label">份待批改作业</span>
                <div class="pending-bar">
                  <div class="pending-bar-fill" :style="{ width: gradedPercent + '%' }"></div>
                </div>
                <span class="pending-sub">已批改 {{ gradedPercent }}%</span>
              </div>
              <div class="overview-stats">
                <div class="stat-item">
                  <span class="stat-icon">📚</span>
                  <span class="stat-num">{{ activeCourses }}</span>
                  <span class="stat-label">活跃课程</span>
                </div>
                <div class="stat-item">
                  <span class="stat-icon">✉️</span>
                  <span class="stat-num">{{ todaySubmissions }}</span>
                  <span class="stat-label">今日提交</span>
                </div>
                <div class="stat-item">
                  <span class="stat-icon">⏱️</span>
                  <span class="stat-num">{{ avgGradingTime }}</span>
                  <span class="stat-label">平均批时</span>
                </div>
              </div>
            </div>

            <!-- 框2：即将截止 -->
            <div class="info-box">
              <h5 class="col-title">⏰ 即将截止</h5>
              <div class="deadline-list">
                <div v-for="(d, idx) in upcomingDeadlines" :key="d.id" class="deadline-card" :class="'urgency-' + d.urgency">
                  <div class="deadline-left">
                    <div class="deadline-icon">
                      <span v-if="d.urgency === 'urgent'">🔥</span>
                      <span v-else-if="d.urgency === 'normal'">📝</span>
                      <span v-else>📋</span>
                    </div>
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

            <!-- 框3：最新动态 -->
            <div class="info-box">
              <h5 class="col-title">🔔 最新动态</h5>
              <div class="activity-timeline">
                <div v-for="(act, idx) in courseActivities" :key="'act'+idx" class="timeline-item">
                  <div class="timeline-marker" :class="act.type">
                    <span class="marker-icon">
                      <template v-if="act.type === 'join'">👤</template>
                      <template v-else-if="act.type === 'submission'">📤</template>
                      <template v-else-if="act.type === 'notice'">📢</template>
                      <template v-else>✅</template>
                    </span>
                  </div>
                  <div class="timeline-content">
                    <div class="timeline-header">
                      <span class="timeline-course">{{ act.course }}</span>
                      <span class="timeline-time">{{ act.time }}</span>
                    </div>
                    <span class="timeline-desc">{{ act.desc }}</span>
                  </div>
                </div>
                <div v-if="courseActivities.length === 0" class="empty-mini">暂无动态</div>
              </div>
            </div>

            <!-- 框4：切换显示 -->
            <div class="info-box">
              <div class="box4-header">
                <h5 class="col-title" style="margin-bottom:0; border-bottom:none;">{{ calendarTab === 'countdown' ? '结课倒计时' : '本周课程' }}</h5>
                <div class="tab-switch">
                  <button class="switch-btn" :class="{ active: calendarTab === 'countdown' }" @click="calendarTab = 'countdown'" title="结课倒计时">📅</button>
                  <button class="switch-btn" :class="{ active: calendarTab === 'schedule' }" @click="calendarTab = 'schedule'" title="本周课程">📋</button>
                </div>
              </div>
              <div v-if="calendarTab === 'countdown'" class="calendar-section">
                <div class="countdown-grid">
                  <div v-for="(item, idx) in countdowns" :key="'cd'+idx" class="countdown-card" :class="'cd-card-' + (idx % 3)">
                    <div class="cd-inner">
                      <div class="cd-ring">
                        <svg viewBox="0 0 100 100" class="cd-ring-svg">
                          <circle cx="50" cy="50" r="42" class="cd-ring-bg" />
                          <circle cx="50" cy="50" r="42" class="cd-ring-fill" :class="'cd-fill-' + (idx % 3)"
                            :style="{ strokeDashoffset: 264 - (264 * Math.min(item.remaining, 90) / 90) }" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import TeacherNav from '../../components/TeacherNav.vue'

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
    await fetchCourses(user.value.role, user.value.userId, getToken())
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
    await createCourse(data, user.value.role, user.value.userId, getToken())
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
  --bg-root: #f4f3f9;
  --bg-card: rgba(255, 255, 255, 0.55);
  --accent: #6b5df0;
  --accent-deep: #5a4ad0;
  --accent-soft: rgba(107, 93, 240, 0.09);
  --accent-glow: rgba(107, 93, 240, 0.22);
  --border-light: rgba(0, 0, 0, 0.08);
  --border-medium: rgba(0, 0, 0, 0.14);
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0, 0, 0, 0.06);
  --danger: #ef4444;
  --success: #0d9488;
  --warning: #f59e0b;
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
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255, 255, 255, 0.07);
}
</style>

<style scoped>
.app-shell {
  display:flex; flex-direction:column; height:100vh; gap:8px;
  padding:6px 10px; background:var(--bg-root);
  font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif;
  color:var(--text-primary); transition:background 0.4s,color 0.4s; overflow:hidden;
}

.main-area {
  flex:1; overflow-y:auto; padding:24px 36px 28px 36px;
  background:var(--bg-card); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  border-radius:20px;
}
.main-area::-webkit-scrollbar { width:4px; }
.main-area::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

.courses-page { width:100%; }

/* 头部 */
.page-header {
  display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;
  flex-wrap:wrap; gap:12px;
}
.header-left { display:flex; align-items:baseline; gap:12px; }
.header-left h2 {
  font-size:1.5rem; font-weight:700; color:var(--text-primary); margin:0;
  padding-left:12px; border-left:4px solid var(--accent); box-shadow:-4px 0 12px var(--accent-soft);
}
.header-summary { font-size:0.9rem; color:var(--text-muted); font-weight:500; }

.header-right { display:flex; align-items:center; gap:12px; }

.search-box {
  display:flex; align-items:center; gap:6px;
  padding:8px 14px; background:var(--bg-card);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1.5px solid var(--accent); border-radius:10px;
  box-shadow:0 0 8px var(--accent-soft);
  transition:all 0.3s;
}
.search-box:focus-within { border-color:var(--accent-deep); box-shadow:0 0 12px var(--accent-glow); }
.search-icon { width:14px; height:14px; stroke:var(--text-muted); fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.search-box input {
  border:none; background:transparent; outline:none; font-size:0.85rem;
  color:var(--text-primary); font-family:inherit; width:260px;
  transition: width 0.3s ease;
}
.search-box input:focus { width: 300px; }
.search-box input::placeholder { color:var(--text-muted); }

/* 课程网格 */
.course-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr)); gap:14px; margin-bottom:20px; }
.course-card {
  background:var(--bg-card); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1.8px solid var(--accent); border-radius:14px; padding:18px;
  cursor:pointer; transition:all 0.3s ease; box-shadow:0 0 16px var(--accent-soft);
  display:flex; flex-direction:column;
}
.course-card:hover { transform:translateY(-3px); border-color:var(--accent); box-shadow:0 6px 24px var(--accent-glow); }
.course-card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.course-badge { background:rgba(107,93,240,0.1); color:var(--accent); font-size:0.75rem; font-weight:600; padding:2px 8px; border-radius:12px; border:1px solid var(--accent); }
.course-code { font-size:0.75rem; color:var(--text-muted); font-family:monospace; }
.course-title { font-size:1rem; font-weight:700; color:var(--text-primary); margin:0 0 6px; }
.course-meta { display:flex; gap:12px; font-size:0.8rem; color:var(--text-secondary); margin-bottom:8px; }
.course-activity { width:100%; height:3px; background:var(--divider); border-radius:2px; margin:4px 0 8px; overflow:hidden; }
.activity-bar { height:100%; background:linear-gradient(90deg,var(--accent-deep),var(--accent)); border-radius:2px; transition:width 0.6s; box-shadow:0 0 6px var(--accent-glow); }
.course-footer { margin-top:auto; display:flex; justify-content:flex-end; }
.course-status { font-size:0.7rem; font-weight:500; color:var(--success); background:rgba(13,148,136,0.1); padding:2px 8px; border-radius:4px; border:1px solid rgba(13,148,136,0.2); }

/* 统一小标题 */
.section-subtitle {
  font-size:1.4rem; font-weight:700; color:var(--text-primary);
  display:flex; align-items:center; gap:8px;
  margin:0 0 14px 0; padding-left:12px;
  border-left:4px solid var(--accent); box-shadow:-4px 0 12px var(--accent-soft);
}

/* 四个框：高度统一（flex stretch） */
.info-row {
  display:flex; gap:14px; margin-top:4px;
  align-items: stretch; /* 保证等高 */
}

.info-box {
  flex:1;                     /* 横向等分 */
  background:var(--bg-card);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:2px solid var(--accent);
  border-radius:14px;
  padding:12px 14px;
  box-shadow:0 0 12px var(--accent-soft);
  transition:all 0.3s;
  display:flex; flex-direction:column;
  overflow: hidden; /* 防止内容溢出边框 */
}
.info-box:hover { border-color:var(--accent-deep); box-shadow:0 4px 16px var(--accent-glow); }

/* 框1：概况 */
.overview-pending { text-align:center; margin-bottom:6px; }
.pending-num { font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:700; color:var(--accent); text-shadow:0 0 12px var(--accent-glow); line-height:1; }
.pending-label { font-size:0.85rem; font-weight:600; color:var(--text-secondary); display:block; margin:2px 0; }
.pending-bar { width:75%; height:5px; background:var(--divider); border-radius:3px; overflow:hidden; margin:6px auto; }
.pending-bar-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--accent-deep)); border-radius:3px; transition:width 0.6s; }
.pending-sub { font-size:0.75rem; color:var(--text-muted); }

.overview-stats { display:flex; justify-content:space-around; padding-top:6px; border-top:1px solid var(--divider); margin-top:6px; }
.stat-item { text-align:center; display:flex; flex-direction:column; align-items:center; }
.stat-icon { font-size:1.1rem; margin-bottom:2px; }
.stat-num { font-size:1.1rem; font-weight:700; color:var(--text-primary); }
.stat-label { font-size:0.7rem; color:var(--text-muted); }

/* 框2：即将截止 - 卡片式设计 */
.col-title {
  font-size:0.9rem; font-weight:700; color:var(--text-secondary);
  margin:0 0 8px 0; padding-bottom:4px;
  border-bottom:1px solid var(--divider);
}
.deadline-list { display:flex; flex-direction:column; gap:7px; flex:1; }
.deadline-card {
  display:flex; align-items:center; justify-content:space-between;
  padding:9px 10px; border-radius:10px;
  background:rgba(255,255,255,0.6); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px);
  border:1px solid var(--border-light);
  transition:all 0.25s ease; gap:6px;
}
body.dark .deadline-card { background:rgba(30,30,50,0.5); }
.deadline-card:hover { transform:translateX(3px); box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.deadline-card.urgency-urgent {
  border-left:3px solid var(--danger);
  background:linear-gradient(135deg, rgba(239,68,68,0.06), rgba(255,255,255,0.6));
}
.deadline-card.urgency-normal {
  border-left:3px solid var(--warning);
  background:linear-gradient(135deg, rgba(245,158,11,0.06), rgba(255,255,255,0.6));
}
.deadline-card.urgency-relax {
  border-left:3px solid var(--text-muted);
}
.deadline-left { display:flex; align-items:center; gap:10px; flex:1; min-width:0; }
.deadline-icon { font-size:1.2rem; flex-shrink:0; width:30px; height:30px; display:flex; align-items:center; justify-content:center; background:var(--bg-root); border-radius:8px; }
.deadline-info { display:flex; flex-direction:column; min-width:0; }
.deadline-course { font-size:0.83rem; font-weight:700; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.deadline-task { font-size:0.73rem; color:var(--text-secondary); }
.deadline-right { flex-shrink:0; }
.deadline-badge {
  padding:3px 10px; border-radius:20px; font-size:0.73rem; font-weight:700;
  letter-spacing:0.02em;
}
.deadline-badge.urgent { background:rgba(239,68,68,0.12); color:#dc2626; }
.deadline-badge.normal { background:rgba(245,158,11,0.12); color:#d97706; }
.deadline-badge.relax { background:rgba(0,0,0,0.06); color:var(--text-muted); }
.empty-mini { text-align:center; color:var(--text-muted); font-size:0.8rem; padding:16px 0; }

/* 框3：最新动态 - 时间线设计 */
.activity-timeline { display:flex; flex-direction:column; gap:0px; flex:1; position:relative; padding-left:4px; }
.timeline-item { display:flex; gap:10px; padding:5px 0; position:relative; }
.timeline-item::before {
  content:''; position:absolute; left:13px; top:28px; bottom:-5px;
  width:1.5px; background:var(--divider);
}
.timeline-item:last-child::before { display:none; }
.timeline-marker {
  width:26px; height:26px; border-radius:50%; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  border:2px solid var(--border-light); background:var(--bg-card);
  z-index:1; font-size:0.7rem;
}
.timeline-marker.join { border-color:var(--accent); background:rgba(107,93,240,0.1); }
.timeline-marker.submission { border-color:var(--success); background:rgba(13,148,136,0.1); }
.timeline-marker.notice { border-color:var(--warning); background:rgba(245,158,11,0.1); }
.timeline-marker.grade { border-color:var(--accent-deep); background:rgba(90,74,208,0.1); }
.timeline-content { flex:1; min-width:0; display:flex; flex-direction:column; }
.timeline-header { display:flex; justify-content:space-between; align-items:baseline; }
.timeline-course { font-size:0.83rem; font-weight:700; color:var(--text-primary); }
.timeline-time {
  font-size:0.68rem; font-weight:600; color:var(--text-muted);
  background:var(--bg-root); padding:1px 7px; border-radius:10px;
  flex-shrink:0; margin-left:6px;
}
.timeline-desc { font-size:0.76rem; color:var(--text-secondary); margin-top:1px; }

/* 框4 切换 */
.box4-header {
  display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;
}
.tab-switch { display:flex; gap:5px; }
.switch-btn {
  background:var(--bg-card); border:1.5px solid var(--border-medium); border-radius:6px;
  padding:2px 8px; cursor:pointer; font-size:0.85rem; transition:all 0.2s; color:var(--text-muted);
}
.switch-btn:hover { border-color:var(--accent); color:var(--accent); }
.switch-btn.active { border-color:var(--accent); background:var(--accent-soft); color:var(--accent); box-shadow:0 0 6px var(--accent-soft); }

/* 结课倒计时 - 环形进度卡片 */
.countdown-grid { display:flex; gap:8px; justify-content:space-around; margin-top:6px; flex:1; align-items:stretch; }
.countdown-card {
  flex:1; border-radius:16px; overflow:hidden;
  border:1.5px solid var(--border-light);
  background:linear-gradient(145deg, rgba(255,255,255,0.7), rgba(255,255,255,0.3));
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  transition:all 0.35s ease;
}
body.dark .countdown-card { background:linear-gradient(145deg, rgba(40,40,70,0.6), rgba(20,20,40,0.4)); }
.countdown-card:hover { transform:translateY(-3px); box-shadow:0 6px 20px rgba(0,0,0,0.08); }
.countdown-card.cd-card-0 { border-top:3px solid #ef4444; }
.countdown-card.cd-card-1 { border-top:3px solid #f59e0b; }
.countdown-card.cd-card-2 { border-top:3px solid #0d9488; }
.cd-inner { padding:12px 8px 10px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; }
.cd-ring { position:relative; width:70px; height:70px; }
.cd-ring-svg { width:70px; height:70px; transform:rotate(-90deg); }
.cd-ring-bg { fill:none; stroke:var(--divider); stroke-width:5; }
.cd-ring-fill { fill:none; stroke-width:5; stroke-linecap:round; stroke-dasharray:264; stroke-dashoffset:0; transition:stroke-dashoffset 1s ease; }
.cd-fill-0 { stroke:#ef4444; }
.cd-fill-1 { stroke:#f59e0b; }
.cd-fill-2 { stroke:#0d9488; }
.cd-number { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.cd-num { font-family:'Playfair Display','Georgia',serif; font-size:1.5rem; font-weight:800; color:var(--text-primary); line-height:1; }
.cd-unit { font-size:0.65rem; color:var(--text-muted); font-weight:600; }
.cd-label { text-align:center; }
.cd-course-name { font-size:0.78rem; font-weight:700; color:var(--text-primary); display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100px; }
.cd-sub-text { font-size:0.65rem; color:var(--text-muted); }

/* 本周课程信纸 */
.todo-list {
  background: linear-gradient(to bottom, transparent 85%, var(--divider) 85%);
  background-size: 100% 2.2em;
  padding:2px 6px; border-radius:6px;
  border:1px solid var(--border-light);
  margin-top:4px;
}
.todo-item {
  display:flex; align-items:baseline; padding:3px 0; line-height:1.8em;
}
.todo-time { font-size:0.8rem; font-weight:600; color:var(--accent); margin-right:8px; min-width:90px; }
.todo-course { font-size:0.8rem; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* 空状态 */
.loading-hint,.empty-hint { text-align:center; padding:60px 20px; color:var(--text-muted); background:var(--bg-card); border-radius:12px; border:1px dashed var(--border-medium); }

/* 对话框 */
.dialog-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100; }
.dialog-card { background:#fff; border:1.8px solid var(--accent); border-radius:16px; padding:32px; width:460px; max-height:90vh; overflow-y:auto; box-shadow:0 0 24px var(--accent-glow); }
.dialog-card h3 { margin:0 0 20px; font-size:1.15rem; font-weight:700; color:var(--text-primary); }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:0.82rem; font-weight:600; color:var(--text-secondary); margin-bottom:6px; }
.form-group input,.form-group select,.form-group textarea { width:100%; padding:10px 14px; background:#fff; border:1.5px solid var(--border-medium); border-radius:10px; font-size:0.88rem; outline:none; box-sizing:border-box; font-family:inherit; color:var(--text-primary); transition:border 0.2s; }
.dark .form-group input,.dark .form-group select,.dark .form-group textarea { background:#252535; }
.form-group input:focus,.form-group select:focus,.form-group textarea:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft); }
.form-row { display:flex; gap:12px; } .form-row .form-group { flex:1; }
.checkbox-label { display:flex!important; align-items:center; gap:8px; font-size:0.85rem!important; color:var(--text-primary); cursor:pointer; }
.checkbox-label input[type='checkbox'] { width:auto!important; accent-color:var(--accent); }
.btn-primary { padding:10px 24px; background:linear-gradient(135deg,var(--accent),var(--accent-deep)); color:#fff; border:none; border-radius:10px; font-size:0.85rem; font-weight:600; cursor:pointer; box-shadow:0 4px 14px var(--accent-glow); transition:all 0.3s; }
.btn-primary:disabled { opacity:0.4; cursor:not-allowed; }
.btn-primary:not(:disabled):hover { transform:translateY(-1px); box-shadow:0 6px 20px var(--accent-glow); }
.btn-secondary { padding:10px 24px; background:var(--bg-root); color:var(--text-primary); border:1.5px solid var(--border-medium); border-radius:10px; font-size:0.85rem; font-weight:500; cursor:pointer; transition:all 0.2s; }
.btn-secondary:hover { background:var(--accent-soft); border-color:var(--accent); }
.dark .dialog-card { background:#1e1e2e; }
.dialog-actions { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; }
.login-error { color:var(--danger); font-size:0.8rem; margin-top:8px; }
</style>
