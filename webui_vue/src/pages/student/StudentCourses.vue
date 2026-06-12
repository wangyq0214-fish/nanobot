<template>
  <div class="app">
    <StudentNav active-tab="courses" />

    <div class="main-content">
      <!-- Join Section -->
      <div class="join-section">
        <div class="join-card">
          <h3>加入课程</h3>
          <div class="join-row">
            <input v-model="joinCode" placeholder="输入 6 位课程码" maxlength="6" @keydown.enter="handleJoin" />
            <button class="btn-primary" @click="handleJoin" :disabled="joining || !joinCode.trim()">
              {{ joining ? '加入中...' : '加入' }}
            </button>
          </div>
          <p v-if="joinError" class="error-text">{{ joinError }}</p>
          <p v-if="joinSuccess" class="success-text">{{ joinSuccess }}</p>
        </div>
      </div>

      <!-- My Courses -->
      <div class="section">
        <h3 class="section-title">我的课程</h3>
        <div v-if="myCourses.length === 0" class="empty-hint">还没有加入任何课程</div>
        <div v-else class="course-grid">
          <div v-for="c in myCourses" :key="c.courseId" class="course-card" @click="router.push(`/student/courses/${c.courseId}`)">
            <div class="card-header">
              <span class="badge">{{ c.subject || '未分类' }}</span>
              <span class="teacher">{{ c.teacherName }}</span>
            </div>
            <h4>{{ c.courseName }}</h4>
            <div class="card-meta">
              <span>{{ c.grade }}</span>
              <span>{{ c.memberCount || 0 }} 名学生</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Public Courses -->
      <div class="section">
        <h3 class="section-title">发现课程</h3>
        <div v-if="publicCourses.length === 0" class="empty-hint">暂无公开课程</div>
        <div v-else class="course-grid">
          <div v-for="c in publicCourses" :key="c.courseId" class="course-card" @click="router.push(`/student/courses/${c.courseId}`)">
            <div class="card-header">
              <span class="badge">{{ c.subject || '未分类' }}</span>
              <span class="teacher">{{ c.teacherName }}</span>
            </div>
            <h4>{{ c.courseName }}</h4>
            <div class="card-meta">
              <span>{{ c.grade }}</span>
              <span>{{ c.memberCount || 0 }} 名学生</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const { user, logout: authLogout } = useAuth()
const { courses, fetchCourses, joinCourse } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

const isDark = ref(false)
function toggleTheme() { isDark.value = !isDark.value; document.body.classList.toggle('dark', isDark.value) }
function handleLogout() { authLogout(); router.push('/login') }

// Separate my courses from public
const myCourses = computed(() => {
  if (!user.value) return []
  return courses.value.filter(c => {
    // Check if student is a member (courses returned by API for students include joined ones)
    return true // API already filters
  })
})
const publicCourses = computed(() => {
  const myIds = new Set(myCourses.value.map(c => c.courseId))
  return courses.value.filter(c => !myIds.has(c.courseId))
})

// Join
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
    const result = await joinCourse(joinCode.value.trim(), user.value.userId, user.value.role, user.value.userId, getToken())
    joinSuccess.value = `成功加入: ${result.course.courseName}`
    joinCode.value = ''
    await fetchCourses(user.value.role, user.value.userId, getToken())
  } catch (e) {
    joinError.value = e.message
  } finally {
    joining.value = false
  }
}

onMounted(async () => {
  if (!user.value) {
    router.push('/login')
    return
  }
  try {
    await fetchCourses(user.value.role, user.value.userId, getToken())
  } catch (e) {
    console.warn('[student-courses] load failed:', e.message)
  }
})
</script>

<style scoped>
.app { display: flex; flex-direction: column; height: 100vh; background: var(--bg-page); }

/* Nav */
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 52px; background: var(--bg-card); border-bottom: 1px solid var(--border-light); flex-shrink: 0; }
.nav-left { display: flex; align-items: center; }
.nav-logo { font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 6px; color: var(--text-primary); }
.dot { width: 8px; height: 8px; background: var(--color-primary); border-radius: 50%; display: inline-block; }
.nav-center { display: flex; gap: 4px; }
.nav-tab { padding: 6px 16px; font-size: 0.82rem; font-weight: 600; color: var(--text-muted); cursor: pointer; border-radius: var(--radius-sm); transition: all 0.2s; }
.nav-tab:hover { background: var(--bg-tag); }
.nav-tab.active { color: var(--color-primary); background: var(--color-primary-soft); }
.nav-right { display: flex; align-items: center; gap: 8px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 6px; border-radius: var(--radius-sm); color: var(--text-secondary); display: flex; align-items: center; }
.icon-btn:hover { background: var(--bg-tag); }
.icon-btn svg { width: 18px; height: 18px; }
.nav-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #5b8def, #7B5CFF); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; }

/* Main */
.main-content { flex: 1; overflow-y: auto; padding: 24px 32px; width: 100%; box-sizing: border-box; }

/* Join */
.join-section { margin-bottom: 32px; }
.join-card { background: var(--bg-card); border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--border-light); }
.join-card h3 { margin: 0 0 12px; font-size: 1rem; color: var(--text-primary); }
.join-row { display: flex; gap: 10px; }
.join-row input { flex: 1; padding: 10px 14px; border: 1.5px solid var(--border-input); border-radius: var(--radius-md); font-size: 0.9rem; outline: none; letter-spacing: 2px; text-align: center; font-family: monospace; background: var(--bg-input); color: var(--text-primary); }
.join-row input:focus { border-color: var(--color-primary); }
.error-text { color: var(--color-error); font-size: 0.8rem; margin-top: 8px; }
.success-text { color: var(--color-success); font-size: 0.8rem; margin-top: 8px; }

/* Section */
.section { margin-bottom: 32px; }
.section-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 16px; color: var(--text-primary); }

/* Course grid */
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.course-card { background: var(--bg-card); border-radius: var(--radius-lg); padding: 18px; cursor: pointer; border: 1px solid var(--border-light); transition: all 0.2s; }
.course-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.badge { background: var(--color-primary-soft); color: var(--color-primary); font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: var(--radius-sm); }
.teacher { font-size: 0.75rem; color: var(--text-muted); }
.course-card h4 { margin: 0 0 6px; font-size: 0.95rem; color: var(--text-primary); }
.card-meta { display: flex; gap: 14px; font-size: 0.75rem; color: var(--text-muted); }
.empty-hint { text-align: center; padding: 30px; color: var(--text-muted); font-size: 0.85rem; }
.btn-primary { padding: 10px 24px; background: var(--color-primary); color: #fff; border: none; border-radius: var(--radius-md); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.btn-primary:hover { background: var(--color-primary-hover); }
.btn-primary:disabled { opacity: 0.5; }
</style>
