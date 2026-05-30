<template>
  <nav class="researcher-nav">
    <div class="nav-left">
      <span class="nav-logo"><span class="dot"></span>AgriScholar</span>
    </div>
    <div class="nav-center">
      <span class="nav-tab" :class="{ active: activeTab === 'hotspot' }" @click="$router.push('/researcher/hotspot')">研究热点</span>
      <span class="nav-tab" :class="{ active: activeTab === 'writing-assistant' }" @click="$router.push('/researcher/writing-assistant')">写作辅导</span>
      <span class="nav-tab" :class="{ active: activeTab === 'datalab' }" @click="$router.push('/researcher/datalab')">实验可视化</span>
    </div>
    <div class="nav-right">
      <slot name="nav-extra" />
      <button class="nav-icon" @click="toggleTheme" title="切换主题">
        <svg v-if="!isDark" viewBox="0 0 20 20"><circle cx="10" cy="10" r="4"/><path d="M10 2v2m0 12v2M2 10h2m12 0h2M4.5 4.5l1.5 1.5m8 8l1.5 1.5M4.5 15.5l1.5-1.5m8-8l1.5-1.5"/></svg>
        <svg v-else viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16 7 7 0 0 1 0-14"/></svg>
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

defineProps({
  activeTab: { type: String, default: 'hotspot' },
})

const router = useRouter()
const { user, logout } = useAuth()
const isDark = ref(false)

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.researcher-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 50px; flex-shrink: 0;
  background: #fff; border-bottom: 1px solid #e8e4db;
}
.nav-left { display: flex; align-items: center; }
.nav-logo { font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 6px; color: #2c2c2c; }
.dot { width: 8px; height: 8px; background: #5b8def; border-radius: 50%; display: inline-block; }
.nav-center { display: flex; gap: 4px; }
.nav-tab {
  padding: 6px 16px; font-size: 0.82rem; font-weight: 600; color: #888;
  cursor: pointer; border-radius: 6px; transition: all 0.2s;
}
.nav-tab:hover { background: #f0ede8; }
.nav-tab.active { color: #5b8def; background: #eef4ff; }
.nav-right { display: flex; align-items: center; gap: 8px; min-width: 0; }
.nav-icon {
  background: none; border: none; cursor: pointer; padding: 6px;
  border-radius: 6px; color: #666; display: flex; align-items: center;
  flex-shrink: 0;
}
.nav-icon:hover { background: #f0ede8; }
.nav-icon svg { width: 18px; height: 18px; }
.nav-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: #5b8def;
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 600; flex-shrink: 0;
}

:global(body.dark) .researcher-nav { background: #1e1e2e; border-color: #333; }
:global(body.dark) .nav-logo { color: #e0e0e0; }
:global(body.dark) .nav-tab { color: #888; }
:global(body.dark) .nav-tab:hover { background: #252535; }
:global(body.dark) .nav-tab.active { background: #252535; color: #5b8def; }
:global(body.dark) .nav-icon { color: #888; flex-shrink: 0; }
:global(body.dark) .nav-icon:hover { background: #252535; }
:global(body.dark) .nav-avatar { flex-shrink: 0; }
</style>
