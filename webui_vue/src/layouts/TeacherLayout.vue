<template>
<div class="teacher-layout">
  <!-- 左侧导航栏 -->
  <aside class="sidebar">
    <div class="sidebar-content">
      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 6.5 3 12 0v-5"/>
          </svg>
        </div>
        <span class="logo-text">Aura Teacher</span>
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
        <span class="user-name">{{ user?.userId || '教师' }}</span>
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
              <div class="settings-user-name">{{ user?.userId || '教师' }}</div>
              <div class="settings-user-role">教师</div>
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

function setTheme(theme) {
  currentTheme.value = theme
  applyTheme(theme)
  localStorage.setItem('nanobot-theme', theme)
}

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
  router.push('/teacher/lesson-plan')
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
    await newChat()
    router.push('/teacher/lesson-plan')
    fetchSessions()
  } catch (err) {
    console.error('Failed to create new chat:', err)
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('nanobot-theme')
  if (savedTheme && ['white', 'dark', 'green'].includes(savedTheme)) {
    currentTheme.value = savedTheme
    applyTheme(savedTheme)
  }

  const userId = user.value?.userId
  if (userId) {
    fetchSessions()
  }
})

const navItems = [
  {
    path: '/teacher/lesson-plan',
    label: '教案与活动',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/></svg>'
  },
  {
    path: '/teacher/courses',
    label: '课程管理',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>'
  },
  {
    path: '/teacher/exam',
    label: '作业批改',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg>'
  },
  {
    path: '/teacher/analytics',
    label: '学情分析',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="m19 9-5 5-4-4-3 3"/></svg>'
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
}

function handleLogout() {
  showSettings.value = false
  logout()
  router.push('/login')
}
</script>

<style scoped>
.teacher-layout {
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
  overflow: hidden;
  background: #ffffff;
  display: flex;
  flex-direction: column;
}

/* ===== 绿色主题样式 ===== */
body.green .teacher-layout {
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
body.dark .teacher-layout {
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

/* 设置弹窗样式 (Teleport to body) */
:global(.settings-overlay) {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  z-index: 1000;
  padding: 20px;
}

:global(.settings-panel) {
  background: var(--bg-card, #ffffff);
  border-radius: 16px;
  padding: 24px;
  width: 300px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-light, #eaeaea);
  margin-bottom: 60px;
  margin-left: 220px;
}

:global(.settings-user) {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light, #eaeaea);
}

:global(.settings-avatar) {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent, #121212);
  color: var(--bg-primary, white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

:global(.settings-user-name) {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #121212);
}

:global(.settings-user-role) {
  font-size: 12px;
  color: var(--text-muted, #999);
  margin-top: 2px;
}

:global(.settings-section) {
  margin-bottom: 20px;
}

:global(.settings-section:last-child) {
  margin-bottom: 0;
}

:global(.settings-section-label) {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #999);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

:global(.theme-options) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

:global(.theme-option) {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-light, #eaeaea);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  font-size: 13px;
  color: var(--text-primary, #121212);
}

:global(.theme-option:hover) {
  background: var(--bg-hover, #f0f0f0);
  border-color: var(--border-color, #d0d0d0);
}

:global(.theme-option.active) {
  background: var(--accent-soft, #f8f8f8);
  border-color: var(--accent, #121212);
}

:global(.theme-option.active) {
  background: var(--accent-soft, #f8f8f8);
  border-color: var(--accent, #121212);
}

:global(.theme-dot) {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--border-light, #eaeaea);
}

:global(.theme-name) {
  flex: 1;
}

:global(.logout-btn) {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-light, #eaeaea);
  background: transparent;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
}

:global(.logout-btn:hover) {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.3);
}
</style>
