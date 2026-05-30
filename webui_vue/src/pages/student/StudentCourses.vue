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
  if (!connected.value) {
    try { await connectGateway({ role: user.value.role, userId: user.value.userId }) } catch {}
  }
  try {
    await fetchCourses(user.value.role, user.value.userId, getToken())
  } catch (e) {
    console.warn('[student-courses] load failed:', e.message)
  }
})
</script>

<style scoped>
.app { display: flex; flex-direction: column; height: 100vh; background: var(--bg, #f8f6f1); }

/* Nav */
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 52px; background: #fff; border-bottom: 1px solid #e8e4db; flex-shrink: 0; }
.nav-left { display: flex; align-items: center; }
.nav-logo { font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; background: #5b8def; border-radius: 50%; display: inline-block; }
.nav-center { display: flex; gap: 4px; }
.nav-tab { padding: 6px 16px; font-size: 0.82rem; font-weight: 600; color: #888; cursor: pointer; border-radius: 6px; transition: all 0.2s; }
.nav-tab:hover { background: #f0ede8; }
.nav-tab.active { color: #5b8def; background: #eef4ff; }
.nav-right { display: flex; align-items: center; gap: 8px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; color: #666; display: flex; align-items: center; }
.icon-btn:hover { background: #f0ede8; }
.icon-btn svg { width: 18px; height: 18px; }
.nav-avatar { width: 30px; height: 30px; border-radius: 50%; background: #5b8def; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; }

/* Main */
.main-content { flex: 1; overflow-y: auto; padding: 24px 32px; width: 100%; box-sizing: border-box; }

/* Join */
.join-section { margin-bottom: 32px; }
.join-card { background: #fff; border-radius: 12px; padding: 24px; border: 1px solid #e8e4db; }
.join-card h3 { margin: 0 0 12px; font-size: 1rem; }
.join-row { display: flex; gap: 10px; }
.join-row input { flex: 1; padding: 10px 14px; border: 1.5px solid #e0dcd5; border-radius: 8px; font-size: 0.9rem; outline: none; letter-spacing: 2px; text-align: center; font-family: monospace; }
.join-row input:focus { border-color: #5b8def; }
.error-text { color: #e74c3c; font-size: 0.8rem; margin-top: 8px; }
.success-text { color: #2e7d32; font-size: 0.8rem; margin-top: 8px; }

/* Section */
.section { margin-bottom: 32px; }
.section-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 16px; color: #2c2c2c; }

/* Course grid */
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.course-card { background: #fff; border-radius: 12px; padding: 18px; cursor: pointer; border: 1px solid #e8e4db; transition: all 0.2s; }
.course-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-2px); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.badge { background: #eef4ff; color: #5b8def; font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.teacher { font-size: 0.75rem; color: #888; }
.course-card h4 { margin: 0 0 6px; font-size: 0.95rem; color: #2c2c2c; }
.card-meta { display: flex; gap: 14px; font-size: 0.75rem; color: #999; }
.empty-hint { text-align: center; padding: 30px; color: #999; font-size: 0.85rem; }
.btn-primary { padding: 10px 24px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; }

/* Dark */
:global(body.dark) .app { background: #12121a; }
:global(body.dark) .top-nav { background: #1e1e2e; border-color: #333; }
:global(body.dark) .join-card, :global(body.dark) .course-card { background: #1e1e2e; border-color: #333; }
:global(body.dark) .join-card h3, :global(body.dark) .section-title, :global(body.dark) .course-card h4 { color: #e0e0e0; }
:global(body.dark) .join-row input { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .nav-tab.active { background: #252535; }
</style>
