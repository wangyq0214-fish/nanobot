<template>
  <nav class="app-nav">
    <div class="nav-left">
      <span class="nav-logo">Nano<span class="logo-accent">bot</span></span>
    </div>
    <div class="nav-center">
      <div class="nav-tabs">
        <span class="nav-tab" :class="{ active: activeTab === 'hotspot' }" @click="$router.push('/researcher/hotspot')">研究热点</span>
        <span class="nav-tab" :class="{ active: activeTab === 'paper-search' }" @click="$router.push('/researcher/paper-search')">论文检索</span>
        <span class="nav-tab" :class="{ active: activeTab === 'paper-library' }" @click="$router.push('/researcher/paper-library')">论文库</span>
        <span class="nav-tab" :class="{ active: activeTab === 'writing-assistant' }" @click="$router.push('/researcher/writing-assistant')">写作辅导</span>
        <span class="nav-tab" :class="{ active: activeTab === 'toolbench' }" @click="$router.push('/researcher/toolbench')">工具台中心</span>
      </div>
    </div>
    <div class="nav-right">
      <slot name="nav-extra" />
      <div class="conn-capsule" :class="{ online: connected }">
        <span class="conn-dot"></span>
        <span class="conn-text">{{ connected ? '已连接' : '未连接' }}</span>
      </div>
      <button class="icon-circle" @click="toggleTheme" :title="isDark ? '切换到亮色模式' : '切换到暗色模式'">
        <svg v-if="isDark" class="ui-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32 1.41-1.41"/></svg>
        <svg v-else class="ui-icon" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
      </button>
      <button class="icon-circle" @click="handleLogout" title="退出登录">
        <svg class="ui-icon" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
      </button>
      <div class="avatar-circle" :title="user?.userId || ''">{{ user?.userId?.[0] || '?' }}</div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useGateway } from '../composables/useGateway.js'

defineProps({
  activeTab: { type: String, default: 'hotspot' },
})

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
}
</script>

<style scoped>
.app-nav {
  height: 64px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  flex-shrink: 0;
}

.nav-left { display: flex; align-items: center; }

.nav-logo {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.logo-accent { color: var(--color-primary); }

.nav-center { display: flex; align-items: center; }

.nav-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-tag);
  padding: 4px;
  border-radius: var(--radius-full);
}

.nav-tab {
  padding: 7px 18px;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-tab:hover { color: var(--text-primary); }

.nav-tab.active {
  color: var(--text-primary);
  background: var(--bg-card);
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
}

.nav-right { display: flex; align-items: center; gap: 10px; min-width: 0; }

.conn-capsule {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  background: var(--bg-tag);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
}
.conn-capsule.online {
  background: rgba(34,197,94,0.08);
  border-color: rgba(34,197,94,0.25);
}
.conn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all 0.3s;
}
.conn-capsule.online .conn-dot {
  background: var(--color-success);
  box-shadow: 0 0 0 3px rgba(34,197,94,0.15);
}
.conn-text {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
}
.conn-capsule.online .conn-text { color: #16a34a; }

.icon-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  background: var(--bg-card);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.icon-circle:hover {
  background: var(--bg-tag);
  color: var(--text-primary);
  border-color: var(--border-input);
}
.ui-icon {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.avatar-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}
.avatar-circle:hover { transform: scale(1.05); }
</style>
