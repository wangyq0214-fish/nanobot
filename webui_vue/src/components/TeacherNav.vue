<template>
  <nav class="teacher-nav">
    <div class="nav-left">
      <span class="nav-logo"><span class="dot"></span>Nanobot</span>
    </div>
    <div class="nav-center">
      <span
        class="nav-tab"
        :class="{ active: activeTab === 'courses' }"
        @click="$router.push('/teacher/courses')"
      >课程管理</span>
      <span
        class="nav-tab"
        :class="{ active: activeTab === 'lesson-plan' }"
        @click="$router.push('/teacher/lesson-plan')"
      >教案与活动</span>
      <span
        class="nav-tab"
        :class="{ active: activeTab === 'homework' }"
        @click="$router.push('/teacher/exam')"
      >作业批改</span>
      <span
        class="nav-tab"
        :class="{ active: activeTab === 'analytics' }"
        @click="$router.push('/teacher/analytics')"
      >学情分析</span>
    </div>
    <div class="nav-right">
      <span class="conn-status" :class="{ online: connected }" :title="connected ? 'Gateway 已连接' : 'Gateway 未连接'">
        <span class="conn-dot"></span>
        <span class="conn-label">{{ connected ? '已连接' : '未连接' }}</span>
      </span>
      <button class="nav-icon" @click="toggleTheme" title="切换主题">
        <svg v-if="!isDark" viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16 7 7 0 0 1 0-14"/></svg>
        <svg v-else viewBox="0 0 20 20"><circle cx="10" cy="10" r="4"/><path d="M10 2v2m0 12v2M2 10h2m12 0h2M4.5 4.5l1.5 1.5m8 8l1.5 1.5M4.5 15.5l1.5-1.5m8-8l1.5-1.5"/></svg>
      </button>
      <button class="nav-icon" @click="handleLogout" title="退出登录">
        <svg viewBox="0 0 20 20"><path d="M7 17H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h3M13 14l4-4-4-4M17 10H7"/></svg>
      </button>
      <div class="nav-avatar" :title="user?.userId || ''">{{ user?.userId?.[0] || '?' }}</div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useGateway } from '../composables/useGateway.js'

defineProps({
  activeTab: { type: String, default: 'lesson-plan' },
})

const emit = defineEmits(['logout'])
const router = useRouter()
const { user, logout } = useAuth()
const { connected } = useGateway()
const isDark = ref(false)

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

function handleLogout() {
  logout()
  router.push('/login')
  emit('logout')
}
</script>

<style scoped>
.teacher-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 50px; flex-shrink: 0;
  background: var(--bg-card, #fff); border-bottom: 1px solid var(--border-light, #e8e4db);
}
.nav-left { display: flex; align-items: center; }
.nav-logo {
  font-family: 'Playfair Display', 'Georgia', serif; font-style: italic;
  font-weight: 700; font-size: 1.05rem; color: var(--text-primary, #2c2c2c);
  display: flex; align-items: center; gap: 6px;
}
.dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent, #5b8def); box-shadow: 0 0 12px var(--accent-glow, rgba(91,141,239,0.4));
}
.nav-center { display: flex; align-items: center; gap: 3px; }
.nav-tab {
  padding: 6px 14px; border-radius: 13px; font-size: 0.82rem; font-weight: 500;
  color: var(--text-secondary, #888); cursor: pointer; transition: all 0.25s;
  border: 1.5px solid transparent; white-space: nowrap;
}
.nav-tab:hover { color: var(--text-primary, #2c2c2c); background: var(--bg-tag, #f0ede8); }
.nav-tab.active {
  color: var(--accent, #5b8def); background: var(--accent-soft, #eef4ff);
  border-color: var(--accent-light, rgba(91,141,239,0.3));
  box-shadow: 0 0 14px var(--accent-glow, rgba(91,141,239,0.2));
}
.nav-right { display: flex; align-items: center; gap: 8px; }
.conn-status {
  display: flex; align-items: center; gap: 5px; padding: 4px 10px;
  border-radius: 12px; font-size: 0.72rem; color: var(--text-muted, #999);
  border: 1px solid var(--border-light, #e8e4db); background: var(--bg-card, #fff);
  cursor: default;
}
.conn-status.online { color: var(--green, #16a34a); border-color: rgba(22,163,74,0.25); }
.conn-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted, #ccc); transition: all 0.3s;
}
.conn-status.online .conn-dot { background: var(--green, #16a34a); box-shadow: 0 0 6px rgba(22,163,74,0.5); }
.conn-label { font-weight: 500; }
.nav-icon {
  background: none; border: none; cursor: pointer; padding: 6px;
  border-radius: 8px; color: var(--text-secondary, #888);
  display: flex; align-items: center; transition: all 0.2s;
}
.nav-icon:hover { background: var(--bg-tag, #f0ede8); color: var(--text-primary, #2c2c2c); }
.nav-icon svg { width: 17px; height: 17px; }
.nav-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #7B5CFF, #A78BFA);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 600; font-size: 0.72rem; cursor: pointer;
  border: 2px solid transparent; box-shadow: 0 0 16px var(--accent-glow, rgba(91,141,239,0.3));
  transition: all 0.25s;
}
.nav-avatar:hover { transform: scale(1.06); }

/* Dark theme */
:global(body.dark) .teacher-nav { background: #1e1e2e; border-color: #333; }
:global(body.dark) .nav-logo { color: #e0e0e0; }
:global(body.dark) .nav-tab { color: #888; }
:global(body.dark) .nav-tab:hover { background: #252535; color: #ccc; }
:global(body.dark) .nav-tab.active { background: #1a2a4a; color: #5b8def; }
:global(body.dark) .conn-status { background: #252535; border-color: #444; }
:global(body.dark) .nav-icon { color: #888; }
:global(body.dark) .nav-icon:hover { background: #252535; color: #ccc; }
</style>
