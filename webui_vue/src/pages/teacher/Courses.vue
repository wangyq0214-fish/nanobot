<template>
  <div class="app-shell">
    <TeacherNav active-tab="courses" @logout="onLogout" />

    <div class="main-area">
      <div class="courses-page">
        <div class="page-header">
          <h2>我的课程</h2>
          <button class="btn-primary" @click="showCreate = true">+ 创建课程</button>
        </div>

        <div v-if="loading" class="loading-hint">加载中...</div>
        <div v-else-if="courses.length === 0" class="empty-hint">
          <p>还没有课程，点击上方按钮创建</p>
        </div>
        <div v-else class="course-grid">
          <div v-for="c in courses" :key="c.courseId" class="course-card" @click="openCourse(c.courseId)">
            <div class="course-card-header">
              <span class="course-badge">{{ c.subject || '未分类' }}</span>
              <span class="course-code">码: {{ c.joinCode }}</span>
            </div>
            <h3 class="course-title">{{ c.courseName }}</h3>
            <div class="course-meta">
              <span>{{ c.grade }}</span>
              <span>{{ c.memberCount || 0 }} 名学生</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CREATE COURSE DIALOG -->
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import TeacherNav from '../../components/TeacherNav.vue'

const router = useRouter()
const { user, logout: authLogout } = useAuth()
const { courses, fetchCourses, createCourse } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

function onLogout() {
  authLogout()
  router.push('/login')
}

// Course list
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

function openCourse(courseId) {
  router.push(`/teacher/courses/${courseId}`)
}

// Create course
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const subjects = ['农学', '园艺', '植物保护', '土壤肥料', '智慧农业', '畜牧兽医', '食品科学', '农业经济']
const grades = ['大一', '大二', '大三', '大四', '研一', '研二']

const form = reactive({
  courseName: '',
  subject: '',
  grade: '',
  description: '',
  isPublic: true,
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
    form.courseName = ''
    form.subject = ''
    form.grade = ''
    form.description = ''
    form.isPublic = true
    await loadCourses()
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  if (!user.value) return
  if (!connected.value) {
    try { await connectGateway({ role: user.value.role, userId: user.value.userId }) } catch {}
  }
  loadCourses()
})
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; background: var(--bg, #f8f6f1); }
.main-area { flex: 1; overflow-y: auto; padding: 24px 32px; }

/* Login */
.login-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--bg, #f8f6f1); }
.login-card { background: #fff; border-radius: 16px; padding: 40px; width: 380px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.login-header { text-align: center; margin-bottom: 24px; }
.login-logo { font-size: 1.5rem; font-weight: 700; }
.login-logo .dot { display: inline-block; width: 8px; height: 8px; background: #5b8def; border-radius: 50%; margin-right: 6px; }
.login-subtitle { color: #888; font-size: 0.85rem; margin-top: 4px; }
.login-roles { display: flex; gap: 8px; margin-bottom: 16px; }
.role-btn { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 8px; border: 2px solid #e8e4db; border-radius: 10px; background: #fff; cursor: pointer; transition: all 0.2s; }
.role-btn.active { border-color: #5b8def; background: #f0f4ff; }
.role-icon { font-size: 1.4rem; }
.role-label { font-size: 0.78rem; font-weight: 600; }
.login-input { width: 100%; padding: 10px 14px; border: 1.5px solid #e0dcd5; border-radius: 8px; font-size: 0.9rem; outline: none; box-sizing: border-box; }
.login-input:focus { border-color: #5b8def; }
.login-error { color: #e74c3c; font-size: 0.8rem; margin-top: 8px; }
.login-submit { width: 100%; padding: 10px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-top: 12px; }
.login-submit:disabled { opacity: 0.5; }

/* Page */
.courses-page { width: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 1.3rem; font-weight: 700; color: #2c2c2c; margin: 0; }

/* Course grid */
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.course-card { background: #fff; border-radius: 12px; padding: 20px; cursor: pointer; border: 1px solid #e8e4db; transition: all 0.2s; }
.course-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-2px); }
.course-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.course-badge { background: #eef4ff; color: #5b8def; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.course-code { font-size: 0.72rem; color: #999; font-family: monospace; }
.course-title { font-size: 1.05rem; font-weight: 600; color: #2c2c2c; margin: 0 0 8px; }
.course-meta { display: flex; gap: 16px; font-size: 0.8rem; color: #888; }

/* Empty / Loading */
.loading-hint, .empty-hint { text-align: center; padding: 60px 20px; color: #999; }

/* Dialog */
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #fff; border-radius: 16px; padding: 32px; width: 460px; max-height: 90vh; overflow-y: auto; }
.dialog-card h3 { margin: 0 0 20px; font-size: 1.15rem; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: #555; margin-bottom: 6px; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 8px 12px; border: 1.5px solid #e0dcd5; border-radius: 8px;
  font-size: 0.88rem; outline: none; box-sizing: border-box; font-family: inherit;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #5b8def; }
.form-row { display: flex; gap: 12px; }
.form-row .form-group { flex: 1; }
.checkbox-label { display: flex !important; align-items: center; gap: 8px; font-size: 0.85rem !important; cursor: pointer; }
.checkbox-label input { width: auto !important; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-primary { padding: 8px 20px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; }
.btn-primary:hover { background: #4a7de0; }
.btn-secondary { padding: 8px 20px; background: #f0ede8; color: #555; border: none; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-secondary:hover { background: #e5e0d8; }

/* Dark theme */
:global(body.dark) .login-card,
:global(body.dark) .dialog-card,
:global(body.dark) .course-card { background: #1e1e2e; border-color: #333; }
:global(body.dark) .login-logo,
:global(body.dark) .course-title,
:global(body.dark) .dialog-card h3 { color: #e0e0e0; }
:global(body.dark) .login-input,
:global(body.dark) .form-group input,
:global(body.dark) .form-group select,
:global(body.dark) .form-group textarea { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .app-shell { background: #12121a; }
:global(body.dark) .page-header h2 { color: #e0e0e0; }
:global(body.dark) .btn-secondary { background: #2a2a3a; color: #ccc; }
</style>
