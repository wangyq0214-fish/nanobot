<template>
  <div class="main-content">

    <!-- 头部：标题 + 搜索 -->
    <header class="page-header">
      <div class="header-left">
        <h2>课程中心</h2>
        <span class="header-summary">共 {{ myCourses.length }} 门课程</span>
      </div>
      <div class="search-box">
        <svg viewBox="0 0 20 20" class="search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
        <input v-model="searchQuery" placeholder="搜索课程名称、学科..." />
      </div>
    </header>

    <!-- 加入课程 -->
    <section class="section">
      <h3 class="section-title">加入课程</h3>
      <div class="join-bar">
        <svg viewBox="0 0 24 24" class="join-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" r=".5" fill="currentColor"/></svg>
        <input v-model="joinCode" placeholder="输入 6 位课程码" maxlength="6" @keydown.enter="handleJoin" />
        <button class="btn-join" @click="handleJoin" :disabled="joining || !joinCode.trim()">
          {{ joining ? '加入中...' : '立即加入' }}
        </button>
      </div>
      <p v-if="joinError" class="error-text">{{ joinError }}</p>
      <p v-if="joinSuccess" class="success-text">{{ joinSuccess }}</p>
    </section>

    <!-- 我的课程 -->
    <section class="section">
      <h3 class="section-title">我的课程</h3>
      <div v-if="filteredMyCourses.length === 0 && myCourses.length === 0" class="empty-hint">
        还没有加入任何课程
      </div>
      <div v-else-if="filteredMyCourses.length === 0" class="empty-hint">
        没有匹配的课程
      </div>
      <div v-else class="card-grid">
        <div
          v-for="c in filteredMyCourses"
          :key="c.courseId"
          class="course-card"
          @click="router.push(`/student/courses/${c.courseId}`)"
        >
          <div class="card-top">
            <span class="card-badge">{{ c.subject || '未分类' }}</span>
            <span class="card-teacher">{{ c.teacherName }}</span>
          </div>
          <h4 class="card-name">{{ c.courseName }}</h4>
          <div class="card-bottom">
            <span class="card-grade">{{ c.grade }}</span>
            <span>{{ c.memberCount || 0 }} 名学生</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 发现课程 -->
    <section class="section">
      <h3 class="section-title">发现课程</h3>
      <div class="card-grid">
        <div
          v-for="c in publicCourses"
          :key="c.courseId"
          class="discover-card"
          @click="router.push(`/student/courses/${c.courseId}`)"
        >
          <div class="card-top">
            <span class="card-badge">{{ c.subject || '未分类' }}</span>
            <span class="card-grade-tag">{{ c.grade }}</span>
          </div>
          <h4 class="card-name">{{ c.courseName }}</h4>
          <p v-if="c.description" class="card-desc">{{ c.description }}</p>
          <div class="card-bottom">
            <span class="card-teacher-row">
              <svg viewBox="0 0 24 24" class="icon-sm" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>
              <span>{{ c.teacherName }}</span>
            </span>
            <span class="card-students">
              {{ c.memberCount || 0 }} 名学生
              <svg viewBox="0 0 24 24" class="icon-xs" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </span>
          </div>
        </div>
      </div>
      <!-- 分页点 -->
      <div class="dots">
        <span class="dot"></span>
        <span class="dot active"></span>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'

const router = useRouter()
const { user } = useAuth()
const { courses, fetchCourses, joinCourse } = useCourse()

const searchQuery = ref('')

const virtualPublicCourses = [
  { courseId: 'pub-001', courseName: '植物生理学', subject: '农学', teacherName: '李教授', grade: '大二', description: '深入研究植物的生命活动规律，掌握光合作用、呼吸作用等核心概念。', memberCount: 42 },
  { courseId: 'pub-002', courseName: '土壤肥料学', subject: '园艺', teacherName: '王老师', grade: '大三', description: '系统学习土壤形成过程与肥料科学施用方法。', memberCount: 35 },
  { courseId: 'pub-003', courseName: '作物栽培学', subject: '农学', teacherName: '张教授', grade: '大三', description: '掌握主要农作物的现代化栽培技术与田间管理。', memberCount: 58 },
  { courseId: 'pub-004', courseName: '园艺植物保护', subject: '园艺', teacherName: '赵教授', grade: '大二', description: '学习园艺作物病虫害的综合防控策略。', memberCount: 28 },
  { courseId: 'pub-005', courseName: '智慧农业概论', subject: '智慧农业', teacherName: '陈博士', grade: '大一', description: '了解物联网、大数据与AI在现代农业中的前沿应用。', memberCount: 65 },
  { courseId: 'pub-006', courseName: '动物营养学', subject: '畜牧兽医', teacherName: '孙教授', grade: '大三', description: '系统学习动物营养需求与科学饲料配方设计。', memberCount: 40 },
]

const myCourses = computed(() => {
  if (!user.value) return []
  return courses.value.filter(() => true)
})

const filteredMyCourses = computed(() => {
  if (!searchQuery.value.trim()) return myCourses.value
  const q = searchQuery.value.trim().toLowerCase()
  return myCourses.value.filter(c =>
    (c.courseName || '').toLowerCase().includes(q) ||
    (c.subject || '').toLowerCase().includes(q) ||
    (c.teacherName || '').toLowerCase().includes(q)
  )
})

const publicCourses = computed(() => {
  const myIds = new Set(myCourses.value.map(c => c.courseId))
  const serverPublic = courses.value.filter(c => !myIds.has(c.courseId))
  return serverPublic.length > 0 ? serverPublic : virtualPublicCourses
})

// Join course
const joinCode = ref('')
const joining = ref(false)
const joinError = ref('')
const joinSuccess = ref('')

async function handleJoin() {
  if (!joinCode.value.trim()) return
  joining.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    const result = await joinCourse(joinCode.value.trim(), user.value.userId)
    joinSuccess.value = `成功加入: ${result.course.courseName}`
    joinCode.value = ''
    await fetchCourses()
  } catch (e) {
    joinError.value = e.message
  } finally {
    joining.value = false
  }
}

onMounted(async () => {
  if (!user.value) { router.push('/login'); return }
  try { await fetchCourses() } catch (e) { console.warn('[student-courses] load failed:', e.message) }
})
</script>

<style>
:root {
  --bg-root: #ffffff;
  --bg-card: #ffffff;
  --bg-subtle: #f8f9f8;
  --accent: #121212;
  --accent-deep: #333333;
  --accent-soft: rgba(18,18,18,0.04);
  --btn-text: #ffffff;
  --border-light: #f0f0f0;
  --border-medium: #eaeaea;
  --border-hover: #121212;
  --text-primary: #121212;
  --text-secondary: #4a534c;
  --text-muted: #9ca3af;
  --divider: #f5f5f5;
  --serif: 'Noto Serif SC', 'PingFang SC', serif;
}
body.dark {
  --bg-root: #0a0a0a;
  --bg-card: #141414;
  --bg-subtle: #1a1a1a;
  --accent: #e0e0e0;
  --accent-deep: #ffffff;
  --accent-soft: rgba(255,255,255,0.05);
  --btn-text: #121212;
  --border-light: #222;
  --border-medium: #2a2a2a;
  --border-hover: #e0e0e0;
  --text-primary: #e5e5e5;
  --text-secondary: #a0a0a0;
  --text-muted: #666;
  --divider: #222;
}
</style>

<style scoped>
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background: var(--bg-card);
  border-radius: 20px;
  margin: 6px 10px;
}
.main-content::-webkit-scrollbar { width: 4px; }
.main-content::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 2px; }

/* === Header === */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.header-left h2 {
  font-family: var(--serif);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.05em;
}
.header-summary {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: monospace;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  width: 260px;
  transition: border-color 0.2s;
}
.search-box:focus-within { border-color: var(--border-hover); }
.search-icon {
  width: 14px; height: 14px;
  stroke: var(--text-muted); fill: none;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  flex-shrink: 0;
}
.search-box input {
  border: none; background: transparent; outline: none;
  font-size: 0.78rem; color: var(--text-primary);
  font-family: inherit; width: 100%;
}
.search-box input::placeholder { color: var(--text-muted); }

/* === Section === */
.section { margin-bottom: 28px; }
.section-title {
  font-size: 0.78rem;
  font-weight: 700;
  margin: 0 0 10px;
  color: var(--text-primary);
}

/* === Join bar === */
.join-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 4px 12px;
  transition: all 0.2s;
}
.join-bar:focus-within {
  border-color: var(--border-hover);
  background: var(--bg-card);
}
.join-icon {
  width: 16px; height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}
.join-bar input {
  flex: 1;
  border: none; background: transparent; outline: none;
  font-size: 0.78rem; color: var(--text-primary);
  padding: 8px 0;
}
.join-bar input::placeholder { color: var(--text-muted); }
.btn-join {
  background: var(--accent);
  color: var(--btn-text);
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  letter-spacing: 0.03em;
  transition: background 0.2s;
  flex-shrink: 0;
}
.btn-join:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-join:not(:disabled):hover { background: var(--accent-deep); }
.error-text { color: #ef4444; font-size: 0.72rem; margin-top: 6px; }
.success-text { color: #0d9488; font-size: 0.72rem; margin-top: 6px; }

/* === Card grid === */
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 900px) { .card-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .card-grid { grid-template-columns: 1fr; } }

/* === Course card === */
.course-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.2s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.002);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 140px;
}
.course-card:hover { border-color: var(--border-hover); }

/* === Discover card === */
.discover-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.2s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.002);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 176px;
  position: relative;
}
.discover-card:hover { border-color: var(--border-hover); }

/* === Shared card internals === */
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.card-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 8px;
  background: var(--bg-subtle);
  color: var(--text-primary);
  border-radius: 6px;
}
.card-teacher {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: monospace;
}
.card-grade-tag {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: monospace;
}
.card-name {
  font-family: var(--serif);
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}
.card-desc {
  font-size: 0.65rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 6px 0 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid var(--divider);
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: auto;
}
.card-grade {
  display: flex;
  align-items: center;
  gap: 4px;
}
.card-teacher-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.card-students {
  display: flex;
  align-items: center;
  gap: 2px;
  color: var(--text-primary);
  font-weight: 500;
}
.icon-sm { width: 14px; height: 14px; flex-shrink: 0; }
.icon-xs { width: 12px; height: 12px; flex-shrink: 0; }

/* === Empty === */
.empty-hint {
  text-align: center;
  padding: 30px;
  color: var(--text-muted);
  font-size: 0.78rem;
  border: 1px dashed var(--border-light);
  border-radius: 12px;
}

/* === Dots === */
.dots {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  padding-top: 16px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-medium);
}
.dot.active {
  width: 12px;
  height: 6px;
  border-radius: 3px;
  background: var(--accent);
}
</style>
