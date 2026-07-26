<template>
<div class="researcher-layout">
  <!-- 左侧导航栏 -->
  <aside class="sidebar">
    <div class="sidebar-content">
      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
          </svg>
        </div>
        <span class="logo-text">Aura Scholar</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="nav-menu">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </div>

    <!-- 最近对话 -->
    <div class="recent-chats">
      <div class="recent-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
        </svg>
        <span>最近对话</span>
        <button class="new-chat-btn" @click="handleNewChat" title="新建对话">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14"/><path d="M5 12h14"/>
          </svg>
        </button>
      </div>
      <div class="recent-list">
        <div
          v-for="s in recentSessions"
          :key="s.key"
          class="recent-item"
          @click="resumeSession(s)"
        >
          <div class="recent-item-content">
            <div class="recent-item-text">{{ s.preview || '新对话' }}</div>
            <div class="recent-item-time">{{ formatTime(s.updatedAt) }}</div>
          </div>
          <button class="delete-btn" @click="(e) => handleDeleteSession(e, s)" title="删除对话">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
        <div v-if="recentSessions.length === 0" class="recent-empty">暂无对话记录</div>
      </div>
    </div>

    <!-- 底部用户操作 -->
    <div class="sidebar-footer">
      <div class="user-info" @click="showSettings = !showSettings">
        <div class="user-avatar">{{ user?.userId?.[0] || '?' }}</div>
        <span class="user-name">{{ user?.userId || '研究员' }}</span>
      </div>
      <div class="footer-actions">
        <button class="action-btn" @click="showSettings = !showSettings" title="设置">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 设置弹窗 -->
    <Teleport to="body">
      <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
        <div class="settings-panel">
          <div class="settings-user">
            <div class="settings-avatar">{{ user?.userId?.[0] || '?' }}</div>
            <div class="settings-user-info">
              <div class="settings-user-name">{{ user?.userId || '研究员' }}</div>
              <div class="settings-user-role">研究员</div>
            </div>
          </div>
          <div class="settings-section">
            <div class="settings-section-label">主题外观</div>
            <div class="theme-options">
              <button v-for="t in themeList" :key="t.key" class="theme-option" :class="{ active: currentTheme === t.key }" @click="setTheme(t.key)">
                <span class="theme-dot" :style="{ background: t.color }"></span>
                <span class="theme-name">{{ t.name }}</span>
                <svg v-if="currentTheme === t.key" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </button>
            </div>
          </div>
          <div class="settings-section">
            <button class="logout-btn" @click="handleLogout">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>

  <!-- 右侧主屏 -->
  <main class="main-content">
    <router-view />
  </main>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useSessions } from '../composables/useSessions.js'
import { useGateway } from '../composables/useGateway.js'

const router = useRouter()
const route = useRoute()
const { user, logout } = useAuth()
const { sessions, fetchSessions, deleteSession } = useSessions()
const { switchSession, newChat } = useGateway()
const currentTheme = ref('green')
const showSettings = ref(false)

const themeList = [
  { key: 'white', name: '纯净素白', color: '#121212' },
  { key: 'dark', name: '深度暗黑', color: '#888' },
  { key: 'green', name: '学术绿', color: '#526e5a' },
]

const recentSessions = computed(() => sessions.value.slice(0, 8))

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function resumeSession(s) {
  if (s.chatId) {
    switchSession(s.chatId)
  }
  // Stay on current page, don't force navigate to workspace
  // Only navigate to workspace if we're not on a researcher page
  if (!route.path.startsWith('/researcher')) {
    router.push('/researcher/workspace')
  }
}

async function handleDeleteSession(e, s) {
  e.stopPropagation()
  if (!confirm('确定要删除这个对话吗？')) return
  try {
    await deleteSession(s.key)
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

async function handleNewChat() {
  try {
    const chatId = await newChat()
    // Immediately add new session to local list so it appears in sidebar
    if (chatId) {
      const newSession = {
        key: `websocket:${chatId}`,
        chatId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        preview: '新对话',
      }
      sessions.value = [newSession, ...sessions.value]
    }
    // Navigate to workspace to start new conversation
    router.push('/researcher/workspace')
    // Also refresh from server in background
    fetchSessions()
  } catch (err) {
    console.error('Failed to create new chat:', err)
  }
}

onMounted(() => {
  // Initialize theme from localStorage
  const savedTheme = localStorage.getItem('nanobot-theme')
  if (savedTheme && ['white', 'dark', 'green'].includes(savedTheme)) {
    currentTheme.value = savedTheme
    applyTheme(savedTheme)
  }

  // Fetch sessions
  const userId = user.value?.userId
  if (userId) {
    fetchSessions()
  }
})

const navItems = [
  {
    path: '/researcher/workspace',
    label: '工作台主页',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>'
  },
  {
    path: '/researcher/results',
    label: '我的研究成果',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>'
  },
  {
    path: '/researcher/agents',
    label: '学术智能体矩阵',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
  },
  {
    path: '/researcher/paper-search',
    label: '全网文献解析',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><circle cx="11" cy="14" r="2"/><path d="m20 17-1.9-1.9"/></svg>'
  },
  {
    path: '/researcher/paper-library',
    label: '结构化知识库',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>'
  },
  {
    path: '/researcher/writing-assistant',
    label: '学术写作助手',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/></svg>'
  },
  {
    path: '/researcher/topic-radar',
    label: '前沿课题雷达',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h6"/><path d="M4 12h8"/><path d="M4 18h10"/><path d="M21.54 15a10 10 0 0 1-3.07 4.93"/><circle cx="12" cy="12" r="2"/><path d="m13.41 10.59 5.66-5.66"/></svg>'
  },
  {
    path: '/researcher/toolbench',
    label: 'AI 工具台中心',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'
  }
]

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function applyTheme(theme) {
  document.body.classList.remove('dark', 'green', 'white')
  if (theme === 'dark') {
    document.body.classList.add('dark')
  } else if (theme === 'green') {
    document.body.classList.add('green')
  }
  // 'white' is default, no class needed
}

function setTheme(theme) {
  currentTheme.value = theme
  applyTheme(theme)
  localStorage.setItem('nanobot-theme', theme)
  // Dispatch custom event for other components to listen
  window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }))
}

function handleLogout() {
  showSettings.value = false
  logout()
  router.push('/login')
}
</script>

<style scoped>
.researcher-layout {
  display: flex;
  height: 100vh;
  background: #ffffff;
  overflow: hidden;
}

/* 左侧导航栏 */
.sidebar {
  width: 260px;
  background: #f8f9f8;
  border-right: 1px solid #eaeaea;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px 16px;
  flex-shrink: 0;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Logo */
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: #121212;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: spin-slow 8s linear infinite;
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #121212;
  letter-spacing: 0.5px;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #666666;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: #f0f0f0;
  color: #121212;
}

.nav-item.active {
  background: #121212;
  color: #ffffff;
  font-weight: 600;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: #999999;
}

.nav-item.active .nav-icon {
  color: #ffffff;
}

/* 最近对话 */
.recent-chats {
  background: #f4f4f4;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid #eaeaea;
  max-height: 280px;
  display: flex;
  flex-direction: column;
}

.recent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #666666;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.new-chat-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #666666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.new-chat-btn:hover {
  background: #e8e8e8;
  color: #121212;
}

.recent-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item {
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.recent-item:hover {
  background: #e8e8e8;
}

.recent-item-content {
  flex: 1;
  min-width: 0;
}

.delete-btn {
  opacity: 0;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.recent-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.recent-item-text {
  font-size: 12px;
  color: #121212;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.recent-item-time {
  font-size: 10px;
  color: #999;
  margin-top: 2px;
}

.recent-empty {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 16px 0;
}

/* 底部用户区域 */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid #eaeaea;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.15s ease;
  flex: 1;
  min-width: 0;
}

.user-info:hover {
  background: #f0f0f0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #121212;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #121212;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #666666;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #e8e8e8;
  color: #121212;
}

/* 右侧主屏 */
.main-content {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
}

/* ===== 绿色主题样式 ===== */
body.green .researcher-layout {
  background: #f7f8f7;
}

body.green .sidebar {
  background: #edf0ed;
  border-right-color: #dee2de;
}

body.green .logo-icon {
  background: #526e5a;
}

body.green .logo-text {
  color: #202b22;
}

body.green .nav-item {
  color: #556056;
}

body.green .nav-item:hover {
  background: #e2e7e2;
  color: #2c332e;
}

body.green .nav-item.active {
  background: #dbe1db;
  color: #1e2720;
}

body.green .nav-icon {
  color: #445c4b;
}

body.green .nav-item.active .nav-icon {
  color: #526e5a;
}

body.green .recent-chats {
  background: #e1e6e1;
  border-color: rgba(207, 226, 207, 0.3);
}

body.green .recent-header {
  color: #4a554b;
}

body.green .new-chat-btn {
  color: #4a554b;
}

body.green .new-chat-btn:hover {
  background: #d4dbd4;
  color: #2c332e;
}

body.green .recent-item:hover {
  background: #d4dbd4;
}

body.green .recent-item-text {
  color: #2c332e;
}

body.green .sidebar-footer {
  border-top-color: #dee2de;
}

body.green .user-avatar {
  background: #526e5a;
}

body.green .user-name {
  color: #2c332e;
}

body.green .action-btn {
  background: #edf0ed;
  border-color: #dee2de;
  color: #556056;
}

body.green .action-btn:hover {
  background: #dbe1db;
  color: #2c332e;
  border-color: #526e5a;
}

body.green .main-content {
  background: linear-gradient(to bottom, #f3f6f3, #f7f8f7, #fafbfa);
}

/* ===== 暗色主题样式 ===== */
body.dark .researcher-layout {
  background: #121212;
}

body.dark .sidebar {
  background: #1a1a1a;
  border-right-color: #2d2d2d;
}

body.dark .logo-icon {
  background: #ffffff;
  color: #121212;
}

body.dark .logo-text {
  color: #e5e5e5;
}

body.dark .nav-item {
  color: #999999;
}

body.dark .nav-item:hover {
  background: #2d2d2d;
  color: #e5e5e5;
}

body.dark .nav-item.active {
  background: #ffffff;
  color: #121212;
}

body.dark .nav-icon {
  color: #999999;
}

body.dark .nav-item.active .nav-icon {
  color: #121212;
}

body.dark .recent-chats {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .recent-header {
  color: #999999;
}

body.dark .new-chat-btn {
  color: #999999;
}

body.dark .new-chat-btn:hover {
  background: #2d2d2d;
  color: #e5e5e5;
}

body.dark .recent-item:hover {
  background: #2d2d2d;
}

body.dark .recent-item-text {
  color: #e5e5e5;
}

body.dark .sidebar-footer {
  border-top-color: #2d2d2d;
}

body.dark .user-avatar {
  background: #ffffff;
  color: #121212;
}

body.dark .user-name {
  color: #e5e5e5;
}

body.dark .action-btn {
  background: #1a1a1a;
  border-color: #2d2d2d;
  color: #999999;
}

body.dark .action-btn:hover {
  background: #2d2d2d;
  color: #e5e5e5;
  border-color: #ffffff;
}

body.dark .main-content {
  background: linear-gradient(to bottom, #141414, #121212, #0f0f0f);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
    padding: 16px 8px;
  }

  .logo-text,
  .nav-label,
  .recent-chats,
  .user-name {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 12px;
  }

  .user-info {
    justify-content: center;
  }

  .footer-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>

<!-- 非 scoped 样式：Teleport 到 body 的设置弹窗 -->
<style>
.settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
}

.settings-panel {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 1001;
}

.settings-panel {
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 20px;
  padding: 24px;
  width: 320px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.settings-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #121212;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
}

.settings-user-info {
  min-width: 0;
}

.settings-user-name {
  font-size: 15px;
  font-weight: 600;
  color: #121212;
}

.settings-user-role {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.settings-section-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.theme-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: all 0.15s ease;
  font-family: inherit;
}

.theme-option:hover {
  background: #f4f4f4;
}

.theme-option.active {
  background: #f4f4f4;
  border-color: #eaeaea;
  color: #121212;
  font-weight: 600;
}

.theme-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid #eaeaea;
}

.theme-option.active .theme-dot {
  border-color: #121212;
}

.theme-name {
  flex: 1;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #fde8e8;
  background: #fef2f2;
  color: #ef4444;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  font-family: inherit;
}

.logout-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
}

/* 设置弹窗 - 绿色主题 */
body.green .settings-panel {
  background: #f7f8f7;
  border-color: #dee2de;
}

body.green .settings-avatar {
  background: #526e5a;
}

body.green .settings-user-name {
  color: #1e2720;
}

body.green .theme-option:hover {
  background: #e2e7e2;
}

body.green .theme-option.active {
  background: #e2e7e2;
  border-color: #d4e0d6;
  color: #1e2720;
}

body.green .theme-option.active .theme-dot {
  border-color: #526e5a;
}

/* 设置弹窗 - 暗色主题 */
body.dark .settings-panel {
  background: #242424;
  border-color: #333;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

body.dark .settings-avatar {
  background: #fff;
  color: #121212;
}

body.dark .settings-user-name {
  color: #e5e5e5;
}

body.dark .settings-user-role {
  color: #888;
}

body.dark .settings-section-label {
  color: #666;
}

body.dark .theme-option {
  color: #999;
}

body.dark .theme-option:hover {
  background: #2d2d2d;
}

body.dark .theme-option.active {
  background: #2d2d2d;
  border-color: #444;
  color: #e5e5e5;
}

body.dark .theme-dot {
  border-color: #444;
}

body.dark .theme-option.active .theme-dot {
  border-color: #fff;
}

body.dark .logout-btn {
  background: #2d1a1a;
  border-color: #4a2020;
  color: #f87171;
}

body.dark .logout-btn:hover {
  background: #3d1a1a;
  border-color: #6b2020;
}
</style>
