<template>
  <div class="app">
    <StudentNav active-tab="courses" />

    <div class="main-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h2>课程中心</h2>
          <span class="header-summary">共 {{ myCourses.length }} 门课程</span>
        </div>
        <div class="header-right">
          <div class="search-box">
            <svg viewBox="0 0 20 20" class="search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
            <input v-model="searchQuery" placeholder="搜索课程名称、学科..." />
          </div>
        </div>
      </div>

      <!-- 加入课程 -->
      <div class="section">
        <h3 class="section-title">加入课程</h3>
        <div class="join-card">
          <div class="join-row">
            <input v-model="joinCode" placeholder="输入 6 位课程码" maxlength="6" @keydown.enter="handleJoin" />
            <button class="btn-primary" @click="handleJoin" :disabled="joining || !joinCode.trim()">
              {{ joining ? '加入中...' : '立即加入' }}
            </button>
          </div>
          <p v-if="joinError" class="error-text">{{ joinError }}</p>
          <p v-if="joinSuccess" class="success-text">{{ joinSuccess }}</p>
        </div>
      </div>

      <!-- 我的课程 -->
      <div class="section">
        <h3 class="section-title">我的课程</h3>
        <div v-if="filteredMyCourses.length === 0 && myCourses.length === 0" class="empty-hint">
          <span class="empty-icon">📚</span>
          <p>还没有加入任何课程</p>
        </div>
        <div v-else-if="filteredMyCourses.length === 0" class="empty-hint">
          <span class="empty-icon">🔍</span>
          <p>没有匹配的课程</p>
        </div>
        <div v-else class="course-grid">
          <div v-for="c in filteredMyCourses" :key="c.courseId" class="course-card" @click="router.push(`/student/courses/${c.courseId}`)">
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

      <!-- 发现课程（轮播） -->
      <div class="section">
        <h3 class="section-title">发现课程</h3>
        <div class="carousel-outer">
          <div class="carousel-viewport" ref="carouselViewport">
            <div class="carousel-track" :style="{ transform: `translateX(-${currentScroll}px)` }">
              <div
                v-for="c in publicCourses"
                :key="c.courseId"
                class="carousel-card"
                @click="router.push(`/student/courses/${c.courseId}`)"
              >
                <div class="carousel-top">
                  <div class="carousel-visual-bar">
                    <span class="carousel-emoji">📖</span>
                    <span class="carousel-subject">{{ c.subject || '未分类' }}</span>
                  </div>
                  <div class="carousel-grade-tag">{{ c.grade }}</div>
                </div>
                <h3 class="carousel-title">{{ c.courseName }}</h3>
                <div class="carousel-teacher-row">
                  <span class="carousel-avatar">{{ (c.teacherName || '?')[0] }}</span>
                  <span class="carousel-teacher">{{ c.teacherName }}</span>
                </div>
                <p class="carousel-desc" v-if="c.description">{{ c.description }}</p>
                <div class="carousel-bottom">
                  <span class="carousel-members">👥 {{ c.memberCount || 0 }} 名学生</span>
                  <span class="carousel-join-hint">点击查看 →</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 箭头 -->
          <button class="carousel-btn prev" @click="scrollLeft" :disabled="!canScrollLeft">‹</button>
          <button class="carousel-btn next" @click="scrollRight" :disabled="!canScrollRight">›</button>

          <!-- 指示点 -->
          <div class="carousel-dots">
            <span
              v-for="(_, idx) in totalPages"
              :key="idx"
              class="dot"
              :class="{ active: idx === currentPage }"
              @click="goToPage(idx)"
            ></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const { user, logout: authLogout } = useAuth()
const { courses, fetchCourses, joinCourse } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

function handleLogout() { authLogout(); router.push('/login') }

const searchQuery = ref('')

// 虚拟公开课程
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

// 加入课程
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

// 轮播控制
const carouselViewport = ref(null)
const cardWidth = 260
const gap = 16
const currentScroll = ref(0)
const currentPage = ref(0)
let cardPerView = 3

const totalPages = computed(() => Math.max(1, Math.ceil(publicCourses.value.length / cardPerView)))
const canScrollLeft = computed(() => currentPage.value > 0)
const canScrollRight = computed(() => currentPage.value < totalPages.value - 1)

function applyScroll(page) {
  currentPage.value = Math.max(0, Math.min(page, totalPages.value - 1))
  const pageWidth = cardPerView * (cardWidth + gap)
  currentScroll.value = currentPage.value * pageWidth
}

function scrollLeft() { if (canScrollLeft.value) applyScroll(currentPage.value - 1) }
function scrollRight() { if (canScrollRight.value) applyScroll(currentPage.value + 1) }
function goToPage(idx) { applyScroll(idx) }

function recalcCards() {
  if (!carouselViewport.value) return
  const vw = carouselViewport.value.clientWidth
  cardPerView = Math.max(1, Math.floor(vw / (cardWidth + gap)))
  applyScroll(Math.min(currentPage.value, totalPages.value - 1))
}

let resizeObserver = null
onMounted(async () => {
  if (!user.value) {
    router.push('/login')
    return
  }
  try {
    await fetchCourses(user.value.role, user.value.userId, getToken())
  } catch (e) { console.warn('[student-courses] load failed:', e.message) }

  await nextTick()
  if (carouselViewport.value) {
    recalcCards()
    resizeObserver = new ResizeObserver(() => recalcCards())
    resizeObserver.observe(carouselViewport.value)
  }
})
onUnmounted(() => { if (resizeObserver) resizeObserver.disconnect() })
</script>

<style>
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255,255,255,0.55);
  --accent: #6b5df0;
  --accent-deep: #5a4ad0;
  --accent-soft: rgba(107,93,240,0.09);
  --accent-glow: rgba(107,93,240,0.22);
  --border-light: rgba(0,0,0,0.08);
  --border-medium: rgba(0,0,0,0.14);
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0,0,0,0.06);
}
body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18,19,34,0.50);
  --accent: #8b70ff;
  --accent-deep: #6b50e0;
  --accent-soft: rgba(139,112,255,0.12);
  --accent-glow: rgba(139,112,255,0.30);
  --border-light: rgba(255,255,255,0.08);
  --border-medium: rgba(255,255,255,0.16);
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.07);
}
</style>

<style scoped>
.app { display:flex; flex-direction:column; height:100vh; background:var(--bg-root); font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif; color:var(--text-primary); transition:background 0.4s,color 0.4s; overflow:hidden; }
.main-content { flex:1; overflow-y:auto; padding:24px 36px 32px 36px; background:var(--bg-card); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); border-radius:20px; margin:6px 10px 6px 10px; }
.main-content::-webkit-scrollbar { width:4px; }
.main-content::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

/* === 页面头部 === */
.page-header {
  display:flex; justify-content:space-between; align-items:center;
  margin-bottom:24px; flex-wrap:wrap; gap:12px;
}
.header-left { display:flex; align-items:baseline; gap:14px; }
.header-left h2 {
  font-size:1.5rem; font-weight:700; margin:0;
  padding-left:12px; border-left:4px solid var(--accent);
  box-shadow:-4px 0 12px var(--accent-soft);
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
  transition:width 0.3s ease;
}
.search-box input:focus { width:300px; }
.search-box input::placeholder { color:var(--text-muted); }

/* === 区域标题 === */
.section { margin-bottom:32px; }
.section-title {
  font-size:1.05rem; font-weight:700; margin:0 0 16px; color:var(--text-primary);
  padding-left:12px; border-left:4px solid var(--accent);
  box-shadow:-4px 0 12px var(--accent-soft);
}

/* === 加入课程 === */
.join-card {
  background:var(--bg-card); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1.8px solid var(--accent); border-radius:14px; padding:18px;
  box-shadow:0 0 16px var(--accent-soft); transition:all 0.3s;
}
.join-card:hover { border-color:var(--accent); box-shadow:0 0 24px var(--accent-glow); }
.join-row { display:flex; gap:10px; }
.join-row input {
  flex:1; padding:12px 18px; background:rgba(255,255,255,0.4);
  border:1.5px solid var(--border-medium); border-radius:10px; font-size:0.9rem;
  font-family:monospace; letter-spacing:2px; text-align:center; outline:none;
  color:var(--text-primary); transition:border 0.2s;
}
.dark .join-row input { background:rgba(20,20,35,0.6); }
.join-row input:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft); }
.btn-primary {
  padding:12px 28px; background:linear-gradient(135deg,var(--accent),var(--accent-deep));
  color:#fff; border:none; border-radius:10px; font-size:0.85rem; font-weight:600;
  cursor:pointer; box-shadow:0 4px 14px var(--accent-glow); transition:all 0.3s;
}
.btn-primary:disabled { opacity:0.4; cursor:not-allowed; box-shadow:none; }
.btn-primary:not(:disabled):hover { transform:translateY(-1px); box-shadow:0 6px 20px var(--accent-glow); }
.error-text { color:#ef4444; font-size:0.8rem; margin-top:8px; }
.success-text { color:#0d9488; font-size:0.8rem; margin-top:8px; }

/* === 我的课程网格 === */
.course-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:14px; }
.course-card {
  background:var(--bg-card); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1.8px solid var(--accent); border-radius:14px; padding:18px;
  cursor:pointer; transition:all 0.3s; box-shadow:0 0 16px var(--accent-soft);
  display:flex; flex-direction:column;
}
.course-card:hover { transform:translateY(-3px); border-color:var(--accent); box-shadow:0 6px 20px var(--accent-glow); }
.card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.badge { background:rgba(107,93,240,0.1); color:var(--accent); font-size:0.7rem; font-weight:600; padding:2px 10px; border-radius:20px; border:1px solid var(--accent); }
.teacher { font-size:0.75rem; color:var(--text-secondary); }
.course-card h4 { margin:0 0 6px; font-size:0.95rem; color:var(--text-primary); font-weight:700; }
.card-meta { display:flex; gap:12px; font-size:0.75rem; color:var(--text-muted); margin-top:auto; }
.empty-hint { text-align:center; padding:30px; color:var(--text-muted); font-size:0.85rem; background:var(--bg-card); border-radius:12px; border:1px dashed var(--border-medium); }
.empty-icon { font-size:1.5rem; display:block; margin-bottom:6px; opacity:0.6; }

/* === 发现课程轮播 === */
.carousel-outer { position:relative; }
.carousel-viewport { overflow:hidden; }
.carousel-track { display:flex; gap:16px; transition:transform 0.5s cubic-bezier(0.25,0.8,0.25,1.2); }
.carousel-card {
  flex:0 0 260px;
  background:var(--bg-card); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1.8px solid var(--accent); border-radius:14px; padding:18px;
  cursor:pointer; transition:all 0.3s;
  box-shadow:0 0 12px var(--accent-soft);
  display:flex; flex-direction:column;
}
.carousel-card:hover { transform:translateY(-4px); border-color:var(--accent-deep); box-shadow:0 8px 24px var(--accent-glow); }
.dark .carousel-card { background:rgba(20,20,35,0.4); }

.carousel-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.carousel-visual-bar { display:flex; align-items:center; gap:8px; }
.carousel-emoji { font-size:1.8rem; }
.carousel-subject {
  font-size:0.7rem; font-weight:600; color:var(--accent);
  background:rgba(107,93,240,0.1); padding:2px 8px; border-radius:10px;
}
.carousel-grade-tag {
  font-size:0.7rem; font-weight:600; color:var(--text-muted);
  background:var(--bg-root); padding:2px 8px; border-radius:8px;
}
.carousel-title { font-size:0.95rem; font-weight:700; margin:0 0 6px; color:var(--text-primary); }
.carousel-teacher-row { display:flex; align-items:center; gap:6px; margin-bottom:6px; }
.carousel-avatar {
  width:22px; height:22px; border-radius:50%;
  background:var(--accent-soft); color:var(--accent);
  display:flex; align-items:center; justify-content:center;
  font-size:0.65rem; font-weight:700; flex-shrink:0;
}
.carousel-teacher { font-size:0.78rem; color:var(--text-secondary); }
.carousel-desc {
  font-size:0.78rem; color:var(--text-muted); line-height:1.5;
  margin:6px 0 12px; flex:1;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}
.carousel-bottom { display:flex; justify-content:space-between; align-items:center; margin-top:auto; padding-top:8px; border-top:1px solid var(--divider); }
.carousel-members { font-size:0.75rem; color:var(--text-muted); }
.carousel-join-hint { font-size:0.72rem; color:var(--accent); font-weight:600; }

/* 按钮 */
.carousel-btn {
  position:absolute; top:50%; transform:translateY(-50%);
  width:40px; height:40px; border-radius:50%;
  background:var(--bg-card); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1.5px solid var(--accent); color:var(--accent); font-size:1.4rem;
  display:flex; align-items:center; justify-content:center; cursor:pointer;
  transition:all 0.2s; z-index:2;
}
.carousel-btn:hover:not(:disabled) { background:var(--accent); color:#fff; box-shadow:0 0 14px var(--accent-glow); }
.carousel-btn:disabled { opacity:0.3; cursor:not-allowed; }
.carousel-btn.prev { left:-8px; }
.carousel-btn.next { right:-8px; }

/* 指示点 */
.carousel-dots { display:flex; justify-content:center; gap:8px; margin-top:16px; }
.carousel-dots .dot {
  width:8px; height:8px; border-radius:50%;
  background:var(--border-medium); cursor:pointer;
  transition:all 0.3s;
}
.carousel-dots .dot.active { background:var(--accent); box-shadow:0 0 8px var(--accent-glow); width:26px; border-radius:4px; }
</style>
