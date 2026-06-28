<template>
  <div class="login-screen">
    <!-- Background decoration -->
    <div class="bg-glow bg-glow-top"></div>
    <div class="bg-glow bg-glow-bottom"></div>

    <!-- Login card -->
    <div class="login-card">
      <!-- Header -->
      <div class="login-header">
        <div class="login-logo">
          <div class="logo-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
            </svg>
          </div>
          <span class="logo-text">Nanobot</span>
        </div>
        <p class="login-subtitle">智能教学平台</p>
      </div>

      <!-- Role selection -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="role-section">
          <label class="role-label">选择您的身份</label>
          <div class="role-grid">
            <div
              v-for="r in roleOptions"
              :key="r.role"
              class="role-card"
              :class="{ active: loginRole === r.role }"
              @click="loginRole = r.role"
            >
              <div class="role-icon-wrapper">
                <component :is="r.icon" />
              </div>
              <span class="role-name">{{ r.label }}</span>
            </div>
          </div>
        </div>

        <!-- Form inputs -->
        <div class="input-section">
          <div class="input-group">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <input
              v-model="loginUserId"
              type="text"
              placeholder="输入您的用户名"
              @keydown.enter="handleLogin"
              autofocus
            />
          </div>
          <div class="input-group">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <input
              v-model="loginPassword"
              type="password"
              placeholder="输入密码"
              @keydown.enter="handleLogin"
            />
          </div>
        </div>

        <p v-if="loginError" class="login-error">{{ loginError }}</p>

        <button
          type="submit"
          class="login-submit"
          :disabled="!loginRole || !loginUserId.trim() || !loginPassword.trim() || loginLoading"
        >
          {{ loginLoading ? '连接中...' : (authMode === 'login' ? '开启智能学习' : '注册新账号') }}
        </button>
      </form>

      <div class="login-footer">
        <button class="login-toggle" @click="authMode = authMode === 'login' ? 'register' : 'login'">
          {{ authMode === 'login' ? '尚无账号？申请注册' : '已有账号？去登录' }}
        </button>
      </div>
    </div>

    <!-- Bottom copyright -->
    <div class="copyright">
      Nanobot AI Education Platform © 2026
    </div>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useGateway } from '../composables/useGateway.js'

const router = useRouter()
const { login } = useAuth()
const { connect: connectGateway } = useGateway()

// Icon components
const TeacherIcon = {
  render() {
    return h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
      h('path', { d: 'M22 10v6M2 10l10-5 10 5-10 5z' }),
      h('path', { d: 'M6 12v5c3 3 9 3 12 0v-5' })
    ])
  }
}

const StudentIcon = {
  render() {
    return h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
      h('path', { d: 'M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z' }),
      h('path', { d: 'M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z' })
    ])
  }
}

const ResearcherIcon = {
  render() {
    return h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
      h('path', { d: 'M6 18h8' }),
      h('path', { d: 'M3 22h18' }),
      h('path', { d: 'M14 22a7 7 0 1 0 0-14h-1' }),
      h('path', { d: 'M9 14h2' }),
      h('path', { d: 'M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z' }),
      h('path', { d: 'M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3' })
    ])
  }
}

const roleOptions = [
  { role: 'teacher', icon: TeacherIcon, label: '教师' },
  { role: 'student', icon: StudentIcon, label: '学生' },
  { role: 'researcher', icon: ResearcherIcon, label: '研究员' },
]

const loginRole = ref('teacher')
const loginUserId = ref('')
const loginPassword = ref('')
const loginError = ref('')
const loginLoading = ref(false)
const authMode = ref('login')

async function handleLogin() {
  const trimmed = loginUserId.value.trim()
  const password = loginPassword.value.trim()
  if (!loginRole.value || !trimmed || !password) return
  if (trimmed.length > 64) { loginError.value = '用户名过长'; return }
  if (password.length < 6) { loginError.value = '密码至少6位'; return }
  loginError.value = ''
  loginLoading.value = true
  try {
    const params = new URLSearchParams({ role: loginRole.value, user_id: trimmed })
    if (authMode.value === 'register') params.set('display_name', trimmed)
    const endpoint = authMode.value === 'register'
      ? `/api/users/register?${params}`
      : `/api/users/validate?${params}`
    // Send password via X-Password header to keep it completely out of URL
    const res = await fetch(endpoint, {
      credentials: 'same-origin',
      headers: { 'X-Password': password }
    })
    const data = await res.json()
    if (!data.ok) {
      if (data.error === 'User not found') loginError.value = '用户不存在，请先注册'
      else if (data.error === 'User already exists') loginError.value = '用户已存在，请直接登录'
      else if (data.error === 'Invalid password') loginError.value = '密码错误'
      else loginError.value = data.error || '验证失败'
      return
    }
    await connectGateway({ role: loginRole.value, userId: trimmed })
    const u = { role: loginRole.value, userId: trimmed }
    login(u)
    // Route to role-specific page
    const roleRoutes = {
      teacher: '/teacher/lesson-plan',
      student: '/student/learning-path',
      researcher: '/researcher/workspace',
    }
    router.push(roleRoutes[loginRole.value] || '/')
  } catch (err) {
    loginError.value = `连接失败: ${err.message}`
  } finally {
    loginLoading.value = false
  }
}
</script>

<style scoped>
.login-screen {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  background: #f5f7f5;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  user-select: none;
}

/* Background decorations - exact match */
.bg-glow {
  position: absolute;
  width: 24rem;
  height: 24rem;
  border-radius: 50%;
  filter: blur(72px);
  pointer-events: none;
}

.bg-glow-top {
  top: 0;
  left: 0;
  background: rgba(186, 210, 190, 0.1);
}

.bg-glow-bottom {
  bottom: 0;
  right: 0;
  background: rgba(82, 110, 90, 0.05);
}

/* Login card - exact match: w-[420px] bg-white rounded-3xl border border-[#dee3de] shadow-[0_16px_45px_rgba(30,39,32,0.04)] p-8 */
.login-card {
  position: relative;
  z-index: 10;
  width: 420px;
  background: #ffffff;
  border-radius: 1.5rem;
  border: 1px solid #dee3de;
  box-shadow: 0 16px 45px rgba(30, 39, 32, 0.04);
  padding: 2rem;
}

/* Header - exact match */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  width: 1.5rem;
  height: 1.5rem;
  background: #526e5a;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #202b22;
  letter-spacing: 0.05em;
}

.login-subtitle {
  font-size: 0.75rem;
  color: #9da79e;
  letter-spacing: 0.05em;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Role section - exact match */
.role-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.role-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #717c72;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

/* Role card - exact match from reference */
.role-card {
  border: 2px solid #e8ebe8;
  background: #ffffff;
  border-radius: 0.75rem;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.role-card:hover {
  border-color: #bad2be;
}

.role-card.active {
  border-color: #526e5a;
  background: #f2f6f3;
}

/* Icon wrapper - exact match: w-7 h-7 rounded-lg bg-white border border-[#dee3de]/40 */
.role-icon-wrapper {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.5rem;
  background: #f8f9f8;
  border: 1px solid rgba(222, 227, 222, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.375rem;
  color: #717c72;
  transition: all 0.2s ease;
}

.role-card:hover .role-icon-wrapper {
  color: #526e5a;
}

.role-card.active .role-icon-wrapper {
  background: #ffffff;
  color: #526e5a;
}

.role-name {
  font-size: 0.75rem;
  font-weight: 500;
  color: #556056;
  transition: color 0.2s ease;
}

.role-card:hover .role-name {
  color: #1e2720;
}

.role-card.active .role-name {
  color: #1e2720;
}

/* Input section - exact match */
.input-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Input group - exact match: bg-[#f8f9f8] border border-[#dee3de] rounded-xl px-3.5 py-2.5 shadow-[0_2px_6px_rgba(0,0,0,0.005)] focus-within:border-[#bad2be] focus-within:bg-white */
.input-group {
  background: #f8f9f8;
  border: 1px solid #dee3de;
  border-radius: 0.75rem;
  padding: 0.625rem 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.005);
  transition: all 0.2s ease;
}

.input-group:focus-within {
  border-color: #bad2be;
  background: #ffffff;
}

.input-icon {
  color: #9da79e;
  flex-shrink: 0;
}

.input-group input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.875rem;
  color: #1e2720;
  padding: 0;
}

.input-group input::placeholder {
  color: #9da79e;
}

.login-error {
  color: #c53030;
  font-size: 0.75rem;
  margin-top: -0.25rem;
}

/* Submit button - exact match: bg-[#526e5a] hover:bg-[#415848] text-white py-3 rounded-xl shadow-md shadow-[#526e5a]/10 tracking-widest */
.login-submit {
  width: 100%;
  background: #526e5a;
  color: #ffffff;
  border: none;
  border-radius: 0.75rem;
  padding: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.1);
  letter-spacing: 0.1em;
}

.login-submit:hover {
  background: #415848;
}

.login-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Footer - exact match */
.login-footer {
  text-align: center;
  margin-top: 1.5rem;
}

.login-toggle {
  background: none;
  border: none;
  color: #717c72;
  font-size: 0.75rem;
  cursor: pointer;
  transition: color 0.2s ease;
  text-decoration: underline;
  text-underline-offset: 4px;
  padding: 0;
}

.login-toggle:hover {
  color: #526e5a;
}

/* Copyright - exact match: text-[10px] tracking-widest uppercase text-gray-400 */
.copyright {
  position: absolute;
  bottom: 1.5rem;
  font-size: 0.625rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #9ca3af;
}
</style>
