<template>
  <div class="login-screen">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo"><span class="dot"></span>Nanobot</div>
        <p class="login-subtitle">智能教学平台</p>
      </div>
      <div class="login-roles">
        <button v-for="r in roleOptions" :key="r.role" class="role-btn" :class="{ active: loginRole === r.role }" @click="loginRole = r.role">
          <span class="role-icon">{{ r.icon }}</span>
          <span class="role-label">{{ r.label }}</span>
        </button>
      </div>
      <input class="login-input" v-model="loginUserId" placeholder="输入用户名" @keydown.enter="handleLogin" autofocus />
      <input class="login-input" v-model="loginPassword" type="password" placeholder="输入密码" @keydown.enter="handleLogin" />
      <p v-if="loginError" class="login-error">{{ loginError }}</p>
      <button class="login-submit" @click="handleLogin" :disabled="!loginRole || !loginUserId.trim() || !loginPassword.trim() || loginLoading">
        {{ loginLoading ? '连接中...' : (authMode === 'login' ? '登录' : '注册') }}
      </button>
      <button class="login-toggle" @click="authMode = authMode === 'login' ? 'register' : 'login'">
        {{ authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useGateway } from '../composables/useGateway.js'

const router = useRouter()
const { login } = useAuth()
const { connect: connectGateway } = useGateway()

const roleOptions = [
  { role: 'teacher', icon: '👨‍🏫', label: '教师' },
  { role: 'student', icon: '📚', label: '学生' },
  { role: 'researcher', icon: '🔬', label: '研究员' },
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
    const params = new URLSearchParams({ role: loginRole.value, user_id: trimmed, password: password })
    const endpoint = authMode.value === 'register'
      ? `/api/users/register?${params}&display_name=${encodeURIComponent(trimmed)}`
      : `/api/users/validate?${params}`
    const res = await fetch(endpoint, { credentials: 'same-origin' })
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
      researcher: '/researcher/hotspot',
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
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: #f8f6f1;
}
.login-card {
  background: #fff; border-radius: 16px; padding: 40px; width: 400px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.login-header { text-align: center; margin-bottom: 28px; }
.login-logo { font-size: 1.6rem; font-weight: 700; color: #2c2c2c; }
.login-logo .dot { display: inline-block; width: 10px; height: 10px; background: #5b8def; border-radius: 50%; margin-right: 6px; }
.login-subtitle { color: #888; font-size: 0.88rem; margin-top: 6px; }
.login-roles { display: flex; gap: 10px; margin-bottom: 20px; }
.role-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 14px 8px; border: 2px solid #e8e4db; border-radius: 12px;
  background: #fff; cursor: pointer; transition: all 0.2s;
}
.role-btn:hover { border-color: #ccc; }
.role-btn.active { border-color: #5b8def; background: #f0f4ff; }
.role-icon { font-size: 1.5rem; }
.role-label { font-size: 0.8rem; font-weight: 600; color: #555; }
.login-input {
  width: 100%; padding: 12px 16px; border: 1.5px solid #e0dcd5; border-radius: 10px;
  font-size: 0.92rem; outline: none; box-sizing: border-box;
}
.login-input:focus { border-color: #5b8def; box-shadow: 0 0 0 3px rgba(91,141,239,0.1); }
.login-error { color: #e74c3c; font-size: 0.82rem; margin-top: 8px; }
.login-submit {
  width: 100%; padding: 12px; background: #5b8def; color: #fff; border: none;
  border-radius: 10px; font-size: 0.92rem; font-weight: 600; cursor: pointer;
  margin-top: 14px; transition: background 0.2s;
}
.login-submit:hover { background: #4a7de0; }
.login-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.login-toggle {
  width: 100%; padding: 8px; background: none; border: none;
  color: #5b8def; font-size: 0.82rem; cursor: pointer; margin-top: 8px;
}
.login-toggle:hover { text-decoration: underline; }

:global(body.dark) .login-screen { background: #12121a; }
:global(body.dark) .login-card { background: #1e1e2e; }
:global(body.dark) .login-logo { color: #e0e0e0; }
:global(body.dark) .role-btn { background: #252535; border-color: #444; }
:global(body.dark) .role-btn.active { border-color: #5b8def; background: #1a2a4a; }
:global(body.dark) .role-label { color: #ccc; }
:global(body.dark) .login-input { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
</style>
