<template>

  <!-- ====== LOGIN SCREEN ====== -->
  <div v-if="!user" class="login-screen">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo"><span class="dot"></span>Nanobot</div>
        <p class="login-subtitle">教案智能助手</p>
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
      <button class="login-toggle" @click="toggleAuthMode">
        {{ authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
      </button>
    </div>
  </div>

  <!-- ====== MAIN APP SHELL ====== -->
  <div v-else class="app-shell">

  <!-- ====== TOP NAV ====== -->
  <nav class="top-nav">
    <div class="nav-left"><span class="nav-logo"><span class="dot"></span>Nanobot</span></div>
    <div class="nav-center">
      <span class="nav-tab active">教案与活动</span>
      <span class="nav-tab">作业批改</span>
      <span class="nav-tab">学情分析</span>
    </div>
    <div class="nav-right">
      <span class="conn-status" :class="{ online: connected }" :title="connected ? 'Gateway 已连接' : (connectionError || 'Gateway 未连接')">
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

  <!-- ====== MAIN AREA ====== -->
  <div class="main-area" ref="mainArea">

  <!-- ====== LEFT TOOL STRIP ====== -->
  <div class="tool-strip">
    <div class="tool-btn active" title="教案编辑">
      <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
      <span class="tooltip">教案编辑</span>
    </div>
    <div class="tool-btn" title="模板">
      <svg viewBox="0 0 20 20"><rect x="3" y="2" width="6" height="7" rx="1"/><rect x="11" y="2" width="6" height="7" rx="1"/><path d="M5 11v7h10v-7"/></svg>
      <span class="tooltip">模板</span>
    </div>
    <div class="tool-btn" title="AI 工具箱">
      <svg viewBox="0 0 20 20"><path d="M10 2v4M10 14v4M2 10h4M14 10h4"/><circle cx="10" cy="10" r="4"/></svg>
      <span class="tooltip">AI 工具箱</span>
    </div>
    <div class="tool-divider"></div>
    <div class="tool-btn" title="保存草稿" @click="handleSaveDraft">
      <svg viewBox="0 0 20 20"><path d="M5 3v14l5-3 5 3V3a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1z"/></svg>
      <span class="tooltip">保存草稿</span>
    </div>
    <div class="tool-btn" title="完成" style="color:var(--green);">
      <svg viewBox="0 0 20 20"><path d="M5 11l4 4 7-8"/></svg>
      <span class="tooltip">完成</span>
    </div>
    <div class="tool-spacer"></div>
    <div class="tool-stats">
      <div class="ts-item" style="color:var(--green);"><div class="ts-val">82%</div><div class="ts-lbl">掌握率</div></div>
      <div class="ts-item" style="color:var(--accent);"><div class="ts-val">93%</div><div class="ts-lbl">完成度</div></div>
    </div>
  </div>

  <!-- ====== LEFT PANEL ====== -->
  <aside class="left-panel" ref="leftPanel">
    <div class="lp-strip top"></div><div class="lp-strip right"></div><div class="lp-strip bottom"></div><div class="lp-strip left"></div>

    <div class="lp-header">
      <div class="lp-header-left">
        <div class="lp-ai-avatar">AI</div>
        <span style="font-size:0.82rem;font-weight:600;">Nanobot 助教</span>
      </div>
      <div class="lp-mode-tabs">
        <span class="lp-mode-tab" :class="{ active: leftMode === 'chat' }" @click="leftMode = 'chat'"><span class="lp-mode-dot"></span>对话</span>
        <span class="lp-mode-tab" :class="{ active: leftMode === 'sessions' }" @click="leftMode = 'sessions'; loadSessions()"><span class="lp-mode-dot"></span>会话</span>
        <span class="lp-mode-tab" :class="{ active: leftMode === 'tpl' }" @click="leftMode = 'tpl'"><span class="lp-mode-dot"></span>模板</span>
        <span class="lp-mode-tab" :class="{ active: leftMode === 'cmd' }" @click="leftMode = 'cmd'"><span class="lp-mode-dot"></span>指令</span>
      </div>
    </div>

    <div class="lp-body">
      <!-- CHAT MODE -->
      <div class="lp-mode-panel" :class="{ active: leftMode === 'chat' }" id="panel-chat">
        <div class="chat-messages" ref="chatMessagesEl">
          <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
            <div class="msg-avatar">{{ msg.role === 'ai' ? 'AI' : msg.role === 'user' ? '师' : '?' }}</div>
            <div>
              <div class="msg-bubble" v-html="msg.text"></div>
              <div v-if="msg.saved" class="msg-saved-tag">已保存到教案库</div>
              <span v-if="msg.streaming" class="stream-cursor"></span>
              <div class="msg-time">{{ msg.time }}</div>
            </div>
          </div>
          <div class="chat-typing" :class="{ show: isTyping }"><span></span><span></span><span></span></div>
        </div>
        <div class="chat-chips">
          <span class="chat-chip" @click="sendQuickCmd('polish')"><svg viewBox="0 0 20 20"><path d="M13 2L4 11l-1 4 4-1 9-9-3-3z"/><path d="M4 11l3 3"/></svg> 语言润色</span>
          <span class="chat-chip" @click="sendQuickCmd('adapt')"><svg viewBox="0 0 20 20"><path d="M2 18L10 2l3 5 5 3-8 8z"/></svg> 难度适配</span>
          <span class="chat-chip" @click="sendQuickCmd('evaluate')"><svg viewBox="0 0 20 20"><rect x="3" y="12" width="3" height="6" rx="0.5"/><rect x="8.5" y="7" width="3" height="11" rx="0.5"/><rect x="14" y="3" width="3" height="15" rx="0.5"/></svg> 智能评估</span>
          <span class="chat-chip" @click="sendQuickCmd('export')"><svg viewBox="0 0 20 20"><path d="M10 3v10M6 9l4 4 4-4M3 15v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2"/></svg> 导出教案</span>
        </div>
        <div class="chat-input-wrap">
          <textarea class="chat-input" v-model="chatInput" :placeholder="connected ? '描述你想要生成的教案…' : '正在连接 Gateway…'" rows="1" @keydown="handleChatKey"></textarea>
          <button class="chat-send" @click="sendMessage" :disabled="!connected" title="发送">
            <svg viewBox="0 0 20 20"><path d="M2 18L18 10 2 2v7l11 1-11 1v7z"/></svg>
          </button>
        </div>
      </div>

      <!-- SESSIONS MODE -->
      <div class="lp-mode-panel" :class="{ active: leftMode === 'sessions' }" id="panel-sessions">
        <div class="sessions-panel-body">
          <div v-if="sessionsLoading" class="sessions-loading">加载中...</div>
          <div v-else-if="sessionsError" class="sessions-error">{{ sessionsError }}</div>
          <div v-else-if="sessions.length === 0" class="sessions-empty">
            <svg viewBox="0 0 20 20" width="32" height="32"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
            <p>暂无历史会话</p>
          </div>
          <div v-else class="sessions-list">
            <div v-for="s in sessions" :key="s.key" class="session-item" :class="{ active: activeSessionKey === s.key }" @click="resumeSession(s)">
              <div class="session-icon">
                <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
              </div>
              <div class="session-info">
                <div class="session-title">{{ s.preview || '新会话' }}</div>
                <div class="session-meta">{{ formatSessionTime(s.updatedAt || s.createdAt) }}</div>
              </div>
              <button class="session-delete" @click.stop="handleDeleteSession(s.key)" title="删除">
                <svg viewBox="0 0 20 20"><path d="M6 4V3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v1M4 4h12M5 4v12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V4"/></svg>
              </button>
            </div>
          </div>
          <button class="sessions-new-btn" @click="createNewSession">
            <svg viewBox="0 0 20 20"><path d="M10 4v12M4 10h12"/></svg>
            新建会话
          </button>
        </div>
      </div>

      <!-- TEMPLATE MODE -->
      <div class="lp-mode-panel" :class="{ active: leftMode === 'tpl' }" id="panel-tpl">
        <div class="tpl-panel-body">
          <input class="lp-title-input" type="text" v-model="tplTitle" placeholder="输入教案标题...">
          <div class="lp-meta">
            <div class="lp-field"><label>学科</label><select v-model="tplSubject"><option>语文</option><option>数学</option><option>英语</option></select></div>
            <div class="lp-field"><label>年级</label><select v-model="tplGrade"><option>八年级（上册）</option><option>七年级（上册）</option><option>九年级（上册）</option></select></div>
            <div class="lp-field"><label>课时</label><select v-model="tplHours"><option>2课时（90分钟）</option><option>1课时（45分钟）</option><option>3课时（135分钟）</option></select></div>
            <div class="lp-field"><label>教材</label><select v-model="tplTextbook"><option>部编版（人教版）</option><option>苏教版</option><option>北师大版</option></select></div>
          </div>
          <div v-for="(section, idx) in tplSections" :key="idx" class="lp-section" :class="{ open: section.open }">
            <div class="lp-section-header" @click="section.open = !section.open">
              <span>
                <svg width="14" height="14" viewBox="0 0 20 20" style="stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;vertical-align:middle;margin-right:5px;" v-html="section.icon"></svg>
                {{ section.label }}
              </span>
              <svg class="lp-chevron" width="14" height="14" viewBox="0 0 20 20" style="stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;"><path d="M5 8l5 5 5-5"/></svg>
            </div>
            <div class="lp-section-body"><textarea class="lp-textarea" v-model="section.content"></textarea></div>
          </div>
        </div>
        <div class="tpl-actions">
          <button class="wb-btn" @click="handleNewTemplate">新建</button>
          <button class="wb-btn" @click="handleSaveDraft">保存草稿</button>
          <button class="wb-btn primary" @click="handleAIGenerate" :disabled="tplGenerating">{{ tplGenerating ? '生成中…' : 'AI 完善' }}</button>
        </div>
      </div>

      <!-- COMMAND MODE -->
      <div class="lp-mode-panel" :class="{ active: leftMode === 'cmd' }" id="panel-cmd">
        <div class="cmd-panel-body">
          <div style="font-size:0.72rem;color:var(--text-muted);">选择快捷指令或添加自定义操作：</div>
          <div class="cmd-cat-tabs">
            <span v-for="cat in cmdCategories" :key="cat.key"
              class="cmd-cat-tab" :class="{ active: activeCmdCat === cat.key }"
              :data-cat="cat.key" @click="activeCmdCat = cat.key">{{ cat.label }}</span>
          </div>
          <div class="cmd-grid">
            <div v-for="cmd in filteredCmds" :key="cmd.name"
              class="cmd-card" :class="{ 'cmd-disabled': cmdGenerating }" :data-cat="cmd.cat" @click="!cmdGenerating && executeCmd(cmd.name)">
              <div class="cmd-icon"><svg width="16" height="16" viewBox="0 0 20 20" style="stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;" v-html="cmdIcons[cmd.icon] || ''"></svg></div>
              <div class="cmd-name">{{ cmd.name }}</div>
              <div class="cmd-desc">{{ cmd.desc }}</div>
            </div>
          </div>
          <div class="cmd-custom-list">
            <div v-if="customCmds.length && (activeCmdCat === 'custom' || activeCmdCat === 'all')" style="font-size:0.68rem;color:var(--text-muted);margin-top:4px;">自定义指令：</div>
            <div v-for="(cmd, i) in (activeCmdCat === 'custom' || activeCmdCat === 'all' ? customCmds : [])" :key="'c'+i" class="cmd-custom-item">
              <span :style="{ cursor: cmdGenerating ? 'default' : 'pointer', opacity: cmdGenerating ? 0.5 : 1 }" @click="!cmdGenerating && executeCmd(cmd)">{{ cmd }}</span>
              <span class="cmd-custom-del" @click="customCmds.splice(i, 1)">×</span>
            </div>
          </div>
        </div>
        <div class="cmd-add-row">
          <input class="cmd-add-input" v-model="cmdAddInput" placeholder="输入自定义指令名称…" @keydown.enter="addCustomCmd">
          <button class="cmd-add-btn" @click="addCustomCmd">+ 添加</button>
        </div>
      </div>
    </div>
  </aside>

  <!-- ====== RESIZER ====== -->
  <div class="resizer" ref="resizer" @mousedown="startResize"></div>

  <!-- ====== RIGHT: DISPLAY AREA ====== -->
  <section class="display-area" ref="displayArea">
    <div class="display-header">
      <span class="display-title"><span class="dot"></span>教案预览 · 实时同步</span>
      <div v-if="sourceFiles.length > 0" class="source-file-selector">
        <select class="source-select" :value="selectedSourceFile" @change="selectSourceFile(sourceFiles.find(f => f.path === $event.target.value))">
          <option v-for="f in sourceFiles" :key="f.path" :value="f.path">{{ f.name.replace(/\.(md|json)$/, '') }}</option>
        </select>
      </div>
      <div class="display-actions">
        <button class="da-btn" :class="{ active: displayMode === 'preview' }" @click="displayMode = 'preview'">完整预览<span class="da-tip">查看完整教案</span></button>
        <button class="da-btn" :class="{ active: displayMode === 'board' }" @click="displayMode = 'board'">板书模式<span class="da-tip">仅展示板书设计</span></button>
        <button class="da-btn" :class="{ active: displayMode === 'class' }" @click="displayMode = 'class'">课堂模式<span class="da-tip">适合投影展示</span></button>
        <button class="da-btn" :class="{ editing: isEditing }" @click="toggleEditMode">{{ isEditing ? '锁定' : '编辑' }}<span class="da-tip">直接修改教案内容</span></button>
        <button class="da-btn" @click="handleExport">导出 PDF<span class="da-tip">下载打印版本</span></button>
        <button class="da-btn" @click="downloadRawResponse" v-if="lastRawResponse" title="下载AI原始回复">📥 原始<span class="da-tip">下载AI返回的原始文本用于核对</span></button>
      </div>
    </div>
    <div class="display-body doc-content" ref="displayBody" :contenteditable="isEditing" :style="displayBodyStyle">
      <!-- DEBUG: shows lessonPlan state -->
      <div v-if="!lessonPlan" class="empty-display">
        <div class="empty-icon">
          <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
        </div>
        <p class="empty-title">尚未生成教案 (lessonPlan = {{ lessonPlan === null ? 'null' : 'undefined' }})</p>
        <p class="empty-desc">在左侧对话区输入指令，让 AI 助教为你生成教案内容</p>
        <button class="wb-btn primary" @click="setLessonPlan(MOCK_LESSON_PLAN)" style="margin-top:16px;">手动加载 Demo 教案</button>
      </div>

      <!-- Dynamic lesson plan rendering -->
      <template v-if="lessonPlan">
        <h1 v-if="lessonPlan.title">教案：{{ lessonPlan.title }}</h1>
        <template v-for="(section, si) in lessonPlan.sections" :key="si">
          <component
            :is="sectionComponents[section.type] || sectionComponents[FALLBACK_TYPE]"
            :section="section"
          />
          <hr v-if="si < lessonPlan.sections.length - 1">
        </template>
      </template>
    </div>
  </section>

  </div><!-- end main-area -->

  <!-- ====== BOTTOM WIDGET BAR ====== -->
  <div class="widget-bar" style="position:relative;">
    <span v-for="w in widgets" :key="w.key"
      class="widget-pill" :class="{ active: activeWidget === w.key }"
      :data-widget="w.key" @click="toggleWidget(w.key)">
      <span class="pill-dot" :style="{ background: w.color }"></span>{{ w.label }}
    </span>
    <span style="margin-left:auto;font-size:0.66rem;color:var(--text-muted);padding-right:4px;">点击切换面板</span>

    <!-- Widget popups would go here - simplified for Vue SFC -->
    <div class="widget-popup" :class="{ show: activeWidget === 'signals' }">
      <div class="sig-r active"><div class="sig-l"><span class="sdot g"></span><div><div class="sname">《背影》阅读教学</div><div class="sdesc">八语·上册 · 已发布</div></div></div><span class="spct st">已发布</span></div>
      <div class="sig-r"><div class="sig-l"><span class="sdot p"></span><div><div class="sname">议论文写作结构训练</div><div class="sdesc">八语·第5单元 · 编辑中</div></div></div><span class="spct st">编辑中</span></div>
    </div>
    <div class="widget-popup" :class="{ show: activeWidget === 'gauge' }">
      <div class="gauge-wrap">
        <svg class="gauge-svg" viewBox="0 0 100 70"><defs><linearGradient id="gGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#7B5CFF"/><stop offset="100%" stop-color="#D4C0FF"/></linearGradient></defs><path d="M7,49 A40 40 0 0,1 87,49" class="g-track"/><path d="M7,49 A40 40 0 0,1 87,49" class="g-fill"/><circle cx="87" cy="49" r="4.5" class="g-endpoint"/><circle cx="87" cy="49" r="2" fill="#7B5CFF"/></svg>
        <div><div class="g-val">78%</div><div class="g-lbl">整体备课进度</div><div class="g-stats"><div class="gs-item"><div class="gs-val" style="color:var(--accent);">12</div><div class="gs-lbl">已完成</div></div><div class="gs-item"><div class="gs-val" style="color:var(--accent-amber);">3</div><div class="gs-lbl">进行中</div></div><div class="gs-item"><div class="gs-val" style="color:var(--text-muted);">2</div><div class="gs-lbl">未开始</div></div></div></div>
      </div>
    </div>
    <div class="widget-popup" :class="{ show: activeWidget === 'alerts' }">
      <div class="alert-row" style="background:rgba(240,68,56,0.04);"><span class="alert-dot" style="background:var(--red);box-shadow:0 0 6px rgba(240,68,56,0.5);"></span><div><div class="alert-name" style="color:var(--red);">成绩下滑预警</div><div class="alert-sub">陈小明 · 连续3次下降 92→78→65</div></div></div>
    </div>
  </div>

</div><!-- end app-shell -->
</template>

<script setup>
import { ref, reactive, computed, nextTick, watch, onMounted } from 'vue'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'

// Configure marked with GFM + KaTeX
marked.setOptions({ breaks: true, gfm: true })
marked.use(markedKatex({ throwOnError: false, output: 'html' }))
import { lessonPlan, setLessonPlan, clearLessonPlan, MOCK_LESSON_PLAN } from './src/composables/useLessonPlan.js'
import { sectionComponents, FALLBACK_TYPE } from './src/components/index.js'
import { useGateway } from './src/composables/useGateway.js'
import { useSessions } from './src/composables/useSessions.js'
import { useSource } from './src/composables/useSource.js'

const { connected, connectionError, connect: connectGateway, sendMessage: gwSend, disconnect: disconnectGateway, switchSession, getChatId, getToken, onChat, newChat } = useGateway()
const { sessions, loading: sessionsLoading, error: sessionsError, activeKey: activeSessionKey, fetchSessions, fetchSessionMessages, deleteSession: deleteSessionApi, setActive } = useSessions()
const { fetchSourceFiles, fetchSourceFile } = useSource()

// ====== User / Login ======
const USER_KEY = 'nanobot-webui.user'
const roleOptions = [
  { role: 'teacher', icon: '👨‍🏫', label: '教师' },
  { role: 'student', icon: '📚', label: '学生' },
  { role: 'researcher', icon: '🔬', label: '研究员' },
]
const user = ref(null)
const authMode = ref('login') // 'login' | 'register'
const loginRole = ref('teacher')
const loginUserId = ref('')
const loginPassword = ref('')
const loginError = ref('')
const loginLoading = ref(false)

function loadUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.role && parsed?.userId ? parsed : null
  } catch { return null }
}

function saveUser(u) { localStorage.setItem(USER_KEY, JSON.stringify(u)) }
function clearUser() { localStorage.removeItem(USER_KEY) }

async function handleLogin() {
  const trimmed = loginUserId.value.trim()
  const password = loginPassword.value.trim()
  if (!loginRole.value || !trimmed || !password) return
  if (trimmed.length > 64) { loginError.value = '用户名过长'; return }
  if (password.length < 6) { loginError.value = '密码至少6位'; return }
  loginError.value = ''
  loginLoading.value = true
  try {
    // Validate or register via API
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
    // Connect gateway
    await connectGateway({ role: loginRole.value, userId: trimmed })
    setupStreamHandler()
    const u = { role: loginRole.value, userId: trimmed }
    saveUser(u)
    user.value = u
    // Load user sessions
    loadSessions()
  } catch (err) {
    loginError.value = `连接失败: ${err.message}`
  } finally {
    loginLoading.value = false
  }
}

function toggleAuthMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login'
  loginError.value = ''
}

function handleLogout() {
  disconnectGateway()
  clearUser()
  // Clear stored chatId on logout
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  user.value = null
  loginUserId.value = ''
  loginPassword.value = ''
  loginRole.value = 'teacher'
  authMode.value = 'login'
}

// ====== Sessions ======
function loadSessions() {
  if (user.value) {
    const token = getToken()
    fetchSessions(user.value.role, user.value.userId, token)
  }
}

async function resumeSession(session) {
  setActive(session.key)
  // Switch to this session via WebSocket
  try {
    switchSession(session.chatId)
    setupStreamHandler(session.chatId)
  } catch (e) {
    console.error('Failed to switch session:', e)
  }
  // Load historical messages
  try {
    const token = getToken()
    const data = await fetchSessionMessages(session.key, user.value?.role, user.value?.userId, token)
    if (data?.messages?.length) {
      chatMessages.value = data.messages
        .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content && m.content.trim())
        .map(m => ({
          role: m.role === 'assistant' ? 'ai' : 'user',
          text: renderMarkdown(m.content),
          time: m.timestamp
            ? new Date(m.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
            : '',
        }))
    } else {
      chatMessages.value = [
        { role: 'ai', text: '您好！我是 Nanobot 助教，可以帮您生成和优化教案。<br><br>请告诉我您需要的 <strong>学科、年级和课题</strong>，我就可以开始工作了。', time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) },
      ]
    }
  } catch (e) {
    console.error('Failed to load session messages:', e)
  }
  // Switch to chat mode
  leftMode.value = 'chat'
  scrollChat()
}

async function handleDeleteSession(key) {
  if (!user.value) return
  if (!confirm('确定删除此会话？')) return
  const token = getToken()
  await deleteSessionApi(key, user.value.role, user.value.userId, token)
}

async function createNewSession() {
  setActive(null)
  // Ask server to create a new chat session
  try {
    const newChatId = await newChat()
    setupStreamHandler(newChatId)
  } catch (e) {
    console.error('Failed to create new session:', e)
  }
  // Reset chat to welcome message
  chatMessages.value = [
    { role: 'ai', text: '您好！我是 Nanobot 助教，可以帮您生成和优化教案。<br><br>请告诉我您需要的 <strong>学科、年级和课题</strong>，我就可以开始工作了。', time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) },
  ]
  leftMode.value = 'chat'
}

function formatSessionTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// ====== Theme ======
const isDark = ref(false)
function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

// ====== Left panel mode ======
const leftMode = ref('chat')

// ====== Chat ======
const chatInput = ref('')
const chatMessages = ref([
  { role: 'ai', text: '您好！我是 Nanobot 助教，可以帮您生成和优化教案。<br><br>请告诉我您需要的 <strong>学科、年级和课题</strong>，我就可以开始工作了。', time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) },
])
const isTyping = ref(false)
const chatMessagesEl = ref(null)

// Store the last raw AI response for download / debug
const lastRawResponse = ref('')

// Streaming state — mirrors React webui's StreamBuffer pattern
let streamBuffer = null   // { messageId, parts[] } while streaming, null otherwise
let streamUnsub = null    // unsubscribe from onChat

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }
}

function scrollChat() {
  nextTick(() => {
    const el = chatMessagesEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function appendMessage(role, text) {
  const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  chatMessages.value.push({ role, text, time })
  scrollChat()
}

// Debug log helper — dumps to browser console
function debugLog(label, data) {
  console.group(`[teach_dashboard] ${label}`)
  console.log(data)
  console.groupEnd()
}

/** Register the event handler for the current chat. */
function setupStreamHandler(targetChatId) {
  if (streamUnsub) streamUnsub()
  streamBuffer = null
  const id = targetChatId || getChatId()
  if (!id) return
  streamUnsub = onChat(id, handleStreamEvent)
}

/** Per-chat event handler — mirrors React webui's useNanobotStream handle(). */
function handleStreamEvent(ev) {
  if (ev.event === 'delta') {
    const msgId = streamBuffer?.messageId ?? ('msg_' + Date.now())
    if (!streamBuffer) {
      streamBuffer = { messageId: msgId, lastText: '' }
      isTyping.value = false
      tplGenerating.value = false
      cmdGenerating.value = false
      const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      chatMessages.value.push({ role: 'ai', text: '', time, streaming: true, _id: msgId })
    }
    // Delta may contain incremental chunk OR full accumulated text.
    // Detect which: if delta starts with lastText, it's full text (replace).
    // Otherwise it's a new chunk (append).
    const chunk = ev.text || ''
    let newText
    if (chunk.length > streamBuffer.lastText.length && chunk.startsWith(streamBuffer.lastText)) {
      // Full accumulated text — replace
      newText = chunk
    } else if (chunk.length > 0) {
      // Incremental chunk — append
      newText = streamBuffer.lastText + chunk
    } else {
      return
    }
    if (newText === streamBuffer.lastText) return
    streamBuffer.lastText = newText
    const targetId = streamBuffer.messageId
    const msg = chatMessages.value.find(m => m._id === targetId)
    if (msg) msg.text = renderMarkdown(newText)
    scrollChat()
    return
  }

  if (ev.event === 'stream_end') {
    if (streamBuffer) {
      const finalText = streamBuffer.lastText || streamBuffer.parts.join('')
      const msg = chatMessages.value.find(m => m._id === streamBuffer.messageId)
      if (msg) {
        msg.streaming = false
        lastRawResponse.value = finalText
        const planParsed = tryParseLessonPlan(finalText)
        if (planParsed) {
          msg.text = planToChatMarkdown(finalText)
          msg.rawMd = finalText
          msg.planTitle = extractPlanTitle(finalText)
          msg.saved = true
          leftMode.value = 'chat'
          refreshSourceFiles()
        } else {
          msg.text = renderMarkdown(finalText)
        }
      }
    }
    streamBuffer = null
    isTyping.value = false
    tplGenerating.value = false
    cmdGenerating.value = false
    return
  }

  if (ev.event === 'message') {
    if (ev.kind === 'tool_hint' || ev.kind === 'progress') return
    // Non-streamed complete message
    streamBuffer = null
    isTyping.value = false
    tplGenerating.value = false
    cmdGenerating.value = false
    const text = ev.text || ''
    lastRawResponse.value = text
    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    const planParsed = tryParseLessonPlan(text)
    const msg = {
      role: 'ai',
      text: planParsed ? planToChatMarkdown(text) : renderMarkdown(text),
      time,
    }
    if (planParsed) {
      msg.rawMd = text
      msg.planTitle = extractPlanTitle(text)
      msg.saved = true
      leftMode.value = 'chat'
      refreshSourceFiles()
    }
    chatMessages.value.push(msg)
    scrollChat()
    return
  }

  if (ev.event === 'error') {
    streamBuffer = null
    isTyping.value = false
    tplGenerating.value = false
    cmdGenerating.value = false
    appendMessage('ai', `❌ ${ev.detail || 'Gateway error'}`)
  }
}

// Re-register stream handler on session switch
function onSessionSwitched() {
  setupStreamHandler()
}


function sendMessage() {
  if (!connected.value) { appendMessage('ai', '⚠️ 未连接到 Gateway，请等待连接…'); return }
  const text = chatInput.value.trim()
  if (!text) return
  appendMessage('user', text)
  chatInput.value = ''
  isTyping.value = true
  scrollChat()

  try {
    gwSend(text)
  } catch (err) {
    isTyping.value = false
    appendMessage('ai', `❌ 发送失败 — ${err.message}`)
  }
}

// Normalize AI-returned plan data to fix common formatting issues:
//  - board_design: split →-containing labels into separate flow items
//    so arrows render between boxes (via template) instead of inside them
function normalizePlan(plan) {
  if (!plan?.sections) return plan
  for (const section of plan.sections) {
    if (section.type === 'board_design' && section.content?.flows) {
      section.content = { ...section.content, flows: section.content.flows.map(fixFlow) }
    }
  }
  return plan
}

function fixFlow(flow) {
  const newItems = []
  for (const item of flow.items || []) {
    const label = item.label || ''
    if (label.includes('→')) {
      const parts = label.split('→').map(p => p.trim()).filter(Boolean)
      for (let i = 0; i < parts.length; i++) {
        newItems.push({
          label: parts[i],
          details: i === parts.length - 1 ? (item.details || []) : [],
          highlight: i === parts.length - 1 ? (item.highlight || false) : false
        })
      }
    } else {
      newItems.push(item)
    }
  }
  return { ...flow, items: newItems }
}

function tryParseLessonPlan(text) {
  console.group('[teach_dashboard] tryParseLessonPlan')
  console.log('输入文本长度:', text.length)
  console.log('前 400 字符:', text.slice(0, 400))

  // ── Strategy 1: ```json code block (case insensitive) ──
  const jsonBlockMatch = text.match(/```(?:json|JSON|Json)\s*([\s\S]*?)```/)
  if (jsonBlockMatch) {
    console.log('✓ 策略1: 找到 json 代码块, 长度:', jsonBlockMatch[1].length)
    try {
      const plan = JSON.parse(jsonBlockMatch[1])
      console.log('  解析成功, sections 数量:', plan?.sections?.length)
      if (plan?.sections?.length) {
        console.log('  ✓ 设置 lessonPlan')
        setLessonPlan(normalizePlan(plan))
        console.groupEnd()
        return true
      }
      console.log('  ✗ sections 为空或不存在')
    } catch (e) {
      console.log('  ✗ JSON 解析失败:', e.message)
    }
  } else {
    console.log('✗ 策略1: 未找到 json 代码块')
  }

  // ── Strategy 2: raw JSON with "sections" key ──
  const rawJsonMatch = text.match(/\{\s*"title"\s*:\s*".*?"\s*,\s*"sections"\s*:\s*\[[\s\S]*?\]\s*\}/)
  if (rawJsonMatch) {
    console.log('✓ 策略2: 找到原始 JSON, 长度:', rawJsonMatch[0].length)
    try {
      const plan = JSON.parse(rawJsonMatch[0])
      console.log('  解析成功, sections 数量:', plan?.sections?.length)
      if (plan?.sections?.length) {
        console.log('  ✓ 设置 lessonPlan')
        setLessonPlan(normalizePlan(plan))
        console.groupEnd()
        return true
      }
    } catch (e) {
      console.log('  ✗ JSON 解析失败:', e.message)
      const biggerMatch = text.match(/\{[\s\S]*?"sections"\s*:[\s\S]*\}/)
      if (biggerMatch) {
        console.log('  尝试更大的匹配, 长度:', biggerMatch[0].length)
        try {
          const plan = JSON.parse(biggerMatch[0])
          if (plan?.sections?.length) {
            console.log('  ✓ 设置 lessonPlan (大块匹配)')
            setLessonPlan(normalizePlan(plan))
            console.groupEnd()
            return true
          }
        } catch (e2) {
          console.log('  ✗ 大块匹配也失败:', e2.message)
        }
      }
    }
  } else {
    console.log('✗ 策略2: 未找到原始 JSON')
  }

  // ── Strategy 3: markdown → structured plan ──
  const keywords = ['教案', '教学设计', '教学目标', '教学重难点', '教学过程', '板书设计']
  const matchedCount = keywords.filter(k => text.includes(k)).length
  if (matchedCount >= 2 && text.length > 200) {
    console.log('✓ 策略3: 检测到教案关键词, 从 markdown 构建')
    const plan = buildPlanFromMarkdown(text)
    console.log('  构建结果: title="' + (plan?.title || '') + '", sections=' + (plan?.sections?.length || 0))
    console.log('  section types:', plan?.sections?.map(s => s.type).join(', '))
    if (plan && plan.sections?.length) {
      console.log('  ✓ 设置 lessonPlan')
      setLessonPlan(normalizePlan(plan))
      console.groupEnd()
      return true
    }
  } else {
    console.log('✗ 策略3: 未检测到教案关键词, 不更新 lessonPlan')
  }

  console.groupEnd()
  return false
}

// ── Lesson plan helpers ──
function extractPlanTitle(text) {
  const m = text.match(/^#\s+(.+)$/m)
  if (m) return m[1].replace(/^教案[：:]\s*/, '').trim()
  // Try JSON
  try {
    const json = extractJson(text)
    if (json?.title) return json.title
  } catch {}
  return '未命名教案'
}

function extractJson(text) {
  const block = text.match(/```(?:json|JSON|Json)\s*([\s\S]*?)```/)
  if (block) return JSON.parse(block[1])
  const raw = text.match(/\{\s*"title"\s*:.*"sections"\s*:\s*\[[\s\S]*\]\s*\}/)
  if (raw) return JSON.parse(raw[0])
  return null
}

/** Convert a JSON lesson plan to readable markdown for chat preview */
function planToChatMarkdown(text) {
  try {
    const plan = extractJson(text)
    if (!plan?.sections?.length) return renderMarkdown(text)
    let md = ''
    if (plan.title) md += `**教案：${plan.title}**\n\n`
    for (const sec of plan.sections) {
      md += `**${sec.title || ''}**\n`
      if (sec.type === 'basic_info' && sec.data) {
        for (const [k, v] of Object.entries(sec.data)) md += `- ${k}：${v}\n`
      } else if ((sec.type === 'objectives' || sec.type === 'key_points') && Array.isArray(sec.content)) {
        for (const group of sec.content) {
          if (group.label) md += `*${group.label}*\n`
          for (const item of (group.items || [])) md += `- ${item}\n`
        }
      } else if (sec.type === 'teaching_process' && Array.isArray(sec.phases)) {
        for (const phase of sec.phases) md += `- ${phase.name || ''}（${phase.duration || ''}）\n`
      } else if (sec.type === 'reflection' && Array.isArray(sec.items)) {
        for (const item of sec.items) md += `- **${item.label || ''}**：${(item.text || '').slice(0, 80)}…\n`
      } else if (sec.type === 'markdown' && sec.content) {
        md += sec.content.slice(0, 200) + '\n'
      }
      md += '\n'
    }
    md += `\n> 完整教案已渲染在右侧面板，可点击下方按钮保存到教案库。`
    return renderMarkdown(md)
  } catch {
    return renderMarkdown(text)
  }
}

function refreshSourceFiles() {
  const saved = loadUser()
  if (saved) setTimeout(() => loadSourceLessonPlan(saved.role, saved.userId), 1000)
}

// ── Markdown → structured lesson plan ──
// Parses AI markdown response and produces a plan compatible with
// the styled section components (tables, chalkboard, highlight boxes, etc.)
function buildPlanFromMarkdown(text) {
  const sections = []

  // Extract title from # heading
  const titleMatch = text.match(/^#\s+(.+)$/m)
  const title = titleMatch ? titleMatch[1].replace(/^教案[：:]\s*/, '').trim() : ''

  // Split by ## headings, tracking heading start position for clean slicing
  const headingRegex = /^##\s+(.+)$/gm
  const headings = []
  let hm
  while ((hm = headingRegex.exec(text)) !== null) {
    headings.push({ title: hm[1].trim(), start: hm.index, end: hm.index + hm[0].length })
  }

  if (headings.length === 0) {
    // No ## headings → wrap whole response as a markdown section
    return {
      title,
      sections: [{ type: 'markdown', title: title || '教案内容', content: text }]
    }
  }

  // Map heading keywords → section type
  const headingTypeMap = [
    { keys: ['基本信息', '课程信息', '课题信息'], type: 'basic_info' },
    { keys: ['教学目标', '学习目标', '课程目标'], type: 'objectives' },
    { keys: ['教学重难点', '重难点', '重点难点', '重点与难点'], type: 'key_points' },
    { keys: ['教学过程', '教学流程', '教学环节', '教学步骤', '教学安排'], type: 'teaching_process' },
    { keys: ['板书设计', '板书', '黑板设计'], type: 'board_design' },
    { keys: ['知识框架', '知识树', '知识体系', '思维导图', '知识结构'], type: 'knowledge_tree' },
    { keys: ['练习', '作业', '习题', '巩固练习', '练习与作业', '课后练习'], type: 'exercises' },
    { keys: ['反思', '教学反思', '课后反思', '教后反思'], type: 'reflection' },
  ]

  for (let i = 0; i < headings.length; i++) {
    const h = headings[i]
    const contentStart = h.end + 1  // skip past the heading line + newline
    const contentEnd = i + 1 < headings.length ? headings[i + 1].start : text.length
    const rawContent = text.slice(contentStart, contentEnd).trim()

    // Determine section type
    let type = 'markdown'
    for (const mapping of headingTypeMap) {
      if (mapping.keys.some(k => h.title.includes(k))) {
        type = mapping.type
        break
      }
    }

    // ── Build section data according to type ──
    switch (type) {
      case 'basic_info': {
        const data = parseKeyValueTable(rawContent)
        if (Object.keys(data).length > 0) {
          sections.push({ type: 'basic_info', title: h.title, data })
        } else {
          sections.push({ type: 'markdown', title: h.title, content: rawContent })
        }
        break
      }
      case 'objectives':
      case 'key_points': {
        const content = parseLabeledItems(rawContent)
        if (content.length > 0) {
          sections.push({ type, title: h.title, content })
        } else {
          sections.push({ type: 'markdown', title: h.title, content: rawContent })
        }
        break
      }
      case 'teaching_process': {
        const phases = parsePhases(rawContent)
        if (phases.length > 0) {
          sections.push({ type: 'teaching_process', title: h.title, phases })
        } else {
          sections.push({ type: 'markdown', title: h.title, content: rawContent })
        }
        break
      }
      case 'board_design': {
        const content = parseBoardDesign(rawContent)
        sections.push({ type: 'board_design', title: h.title, content })
        break
      }
      case 'knowledge_tree': {
        const content = parseKnowledgeTree(rawContent)
        sections.push({ type: 'knowledge_tree', title: h.title, content })
        break
      }
      case 'exercises': {
        const content = parseExercises(rawContent)
        sections.push({ type: 'exercises', title: h.title, content })
        break
      }
      case 'reflection': {
        const items = parseReflection(rawContent)
        if (items.length > 0) {
          sections.push({ type: 'reflection', title: h.title, items })
        } else {
          sections.push({ type: 'markdown', title: h.title, content: rawContent })
        }
        break
      }
      default:
        sections.push({ type: 'markdown', title: h.title, content: rawContent })
    }
  }

  return { title, sections }
}

// ── Sub-parsers ──

function parseKeyValueTable(text) {
  const data = {}
  // Match: "- key：value", "- key: value", "* key：value", "key：value", "| key | value |"
  const lines = text.split('\n')
  for (const line of lines) {
    // Skip markdown table separators
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue
    // Try | key | value | format
    const tableMatch = line.match(/^\|\s*(.+?)\s*\|\s*(.+?)\s*\|/)
    if (tableMatch) {
      const k = tableMatch[1].replace(/\*+/g, '').trim()
      const v = tableMatch[2].replace(/\*+/g, '').trim()
      if (k && v && !['项目', '内容', '--'].includes(k)) data[k] = v
      continue
    }
    // Try "- key：value" or "* key: value"
    const kvMatch = line.match(/^[-*]\s*(.+?)[：:]\s*(.+)/)
    if (kvMatch) {
      const k = kvMatch[1].replace(/\*+/g, '').trim()
      const v = kvMatch[2].replace(/\*+/g, '').trim()
      if (k && v) data[k] = v
    }
  }
  return data
}

function parseLabeledItems(text) {
  // Split by ### sub-headings, or by **Bold Label:** patterns
  const content = []

  // Try ### sub-headings first
  const subRegex = /^###\s+(.+)$/gm
  const subs = []
  let sm
  while ((sm = subRegex.exec(text)) !== null) {
    subs.push({ label: sm[1].trim(), start: sm.index + sm[0].length })
  }

  if (subs.length > 0) {
    for (let j = 0; j < subs.length; j++) {
      const s = subs[j]
      const nextStart = j + 1 < subs.length ? subs[j + 1].start - subs[j + 1].label.length - 5 : text.length
      const subText = text.slice(s.start, nextStart).trim()
      const items = extractListItems(subText)
      content.push({ label: s.label, items: items.length > 0 ? items : [subText] })
    }
  } else {
    // Try **Bold Label:** patterns
    const boldRegex = /\*\*(.+?)\*\*[：:]\s*([\s\S]*?)(?=\n\*\*|$)/g
    let bm
    while ((bm = boldRegex.exec(text)) !== null) {
      const label = bm[1].trim()
      const body = bm[2].trim()
      const items = extractListItems(body)
      content.push({ label, items: items.length > 0 ? items : [body] })
    }
  }

  // If still nothing, try single-level list items as a flat section
  if (content.length === 0) {
    const items = extractListItems(text)
    if (items.length > 0) {
      content.push({ label: '', items })
    }
  }

  return content
}

function extractListItems(text) {
  const items = []
  const lines = text.split('\n')
  for (const line of lines) {
    const m = line.match(/^[-*\d]+[.)]\s+(.+)/)
    if (m) items.push(m[1].trim())
  }
  return items
}

function parsePhases(text) {
  console.group('[parsePhases]')
  const phases = []
  const phaseRegex = /^###\s+(.+)$/gm
  const phaseMatches = []
  let pm
  while ((pm = phaseRegex.exec(text)) !== null) {
    phaseMatches.push({ name: pm[1].trim(), start: pm.index + pm[0].length })
  }
  console.log('phase headings found:', phaseMatches.length, phaseMatches.map(p => p.name))

  if (phaseMatches.length === 0) {
    console.log('no ### phases, wrapping entire text as one phase (len=' + text.length + ')')
    const steps = parseSteps(text)
    phases.push({
      name: '教学过程',
      duration: '',
      steps: steps.length > 0 ? steps : [{ name: '', duration: '', sections: [{ kind: 'text', text }] }]
    })
  } else {
    for (let j = 0; j < phaseMatches.length; j++) {
      const p = phaseMatches[j]
      const nextStart = j + 1 < phaseMatches.length ? phaseMatches[j + 1].start - phaseMatches[j + 1].name.length - 5 : text.length
      const phaseText = text.slice(p.start, nextStart).trim()
      console.log(`phase[${j}] "${p.name}" — text length=${phaseText.length}, preview="${phaseText.slice(0, 120)}"`)
      const steps = parseSteps(phaseText)
      console.log(`  → steps extracted: ${steps.length}, names: [${steps.map(s => s.name).join(', ')}]`)
      for (const s of steps) {
        console.log(`    step "${s.name}" sections=${s.sections.length} content_len=${s.sections[0]?.text?.length || 0}`)
      }
      phases.push({
        name: p.name,
        duration: '',
        steps: steps.length > 0 ? steps : [{ name: '', duration: '', sections: [{ kind: 'text', text: phaseText }] }]
      })
    }
  }

  console.log('parsePhases result:', phases.length, 'phases')
  console.groupEnd()
  return phases
}

function parseSteps(text) {
  const allMatches = []

  // Pattern 1: #### heading (Markdown h4)
  let m
  const mdRegex = /^#{4}\s+(.+)$/gm
  while ((m = mdRegex.exec(text)) !== null) {
    allMatches.push({ name: m[1].trim(), start: m.index, end: m.index + m[0].length })
  }

  // Pattern 2: Chinese numbered lines — 一、xxx, 三、巩固练习（10分钟）etc.
  const cnRegex = /^[\s]*([一二三四五六七八九十]+)[、.]\s*(.+)$/gm
  while ((m = cnRegex.exec(text)) !== null) {
    const full = m[0].trim()
    if (full.length < 3 || full.length > 40) continue
    // Avoid matching lines that are inside list items
    if (m[0].match(/^[-*]/)) continue
    allMatches.push({ name: full, start: m.index, end: m.index + m[0].length })
  }

  // Pattern 3: Western numbered — 1. xxx, 2) xxx (at line start)
  const numRegex = /^(\d+)[.)]\s+(.+)$/gm
  while ((m = numRegex.exec(text)) !== null) {
    const full = m[0].trim()
    if (full.length > 3 && full.length < 40) {
      allMatches.push({ name: full, start: m.index, end: m.index + m[0].length })
    }
  }

  // Deduplicate by position and sort
  allMatches.sort((a, b) => a.start - b.start)
  const unique = []
  for (const item of allMatches) {
    if (unique.length === 0 || item.start !== unique[unique.length - 1].start) {
      unique.push(item)
    }
  }

  // Build steps from matched headers
  const steps = []
  if (unique.length > 0) {
    for (let j = 0; j < unique.length; j++) {
      const s = unique[j]
      const contentStart = s.end + 1  // right after the header line
      const contentEnd = j + 1 < unique.length ? unique[j + 1].start : text.length
      const stepText = text.slice(contentStart, contentEnd).trim()
      steps.push({
        name: s.name,
        duration: '',
        sections: stepText ? [{ kind: 'text', text: stepText }] : []
      })
    }
  }

  return steps
}

function parseBoardDesign(text) {
  // Try to extract structured board content from text
  const lines = text.split('\n').filter(l => l.trim())

  // Extract main title — first non-empty line or bold text
  let mainTitle = ''
  const boldTitleMatch = text.match(/\*\*(.+?)\*\*/)
  if (boldTitleMatch) {
    mainTitle = boldTitleMatch[1].trim()
  } else if (lines.length > 0) {
    mainTitle = lines[0].replace(/^[-*#]+\s*/, '').trim()
  }

  // Group items into flows — anything with → arrows or numbered sequences
  const flows = []
  const flowItems = []
  for (const line of lines) {
    const trimmed = line.replace(/^[-*#]+\s*/, '').trim()
    if (!trimmed || trimmed === mainTitle) continue
    const arrowMatch = trimmed.match(/^(.+?)\s*→\s*(.+)/)
    if (arrowMatch) {
      flowItems.push({ label: arrowMatch[1], details: [arrowMatch[2]], highlight: false })
    }
  }

  if (flowItems.length > 0) {
    flows.push({ title: '', items: flowItems })
  } else {
    // Fallback: treat all lines as a single flow
    const items = lines.slice(1).map(l => ({
      label: l.replace(/^[-*#]+\s*/, '').trim(),
      details: [],
      highlight: false
    })).filter(i => i.label)
    if (items.length > 0) {
      flows.push({ title: '', items })
    }
  }

  // Extract side panels — look for bold headings followed by lists
  const sidePanels = []
  const panelRegex = /\*\*(.+?)\*\*[：:]?\s*([\s\S]*?)(?=\n\*\*|$)/g
  let panelMatch
  while ((panelMatch = panelRegex.exec(text)) !== null) {
    const panelTitle = panelMatch[1].trim()
    const panelBody = panelMatch[2].trim()
    const panelItems = extractListItems(panelBody)
    if (panelTitle && panelItems.length > 0) {
      sidePanels.push({ title: panelTitle, items: panelItems })
    }
  }

  // Footer from last lines
  const footerLines = lines.slice(-3).filter(l => l.replace(/^[-*#]+\s*/, '').trim())
  const footer = footerLines.length > 0 ? footerLines.map(l => l.replace(/^[-*#]+\s*/, '').trim()) : []

  return {
    mainTitle: mainTitle || '板书设计',
    flows: flows.length > 0 ? flows : [{ title: '', items: [{ label: '内容', details: [text.slice(0, 200)], highlight: false }] }],
    sidePanels: sidePanels.length > 0 ? sidePanels : [{ title: '要点', items: extractListItems(text).slice(0, 5) }],
    footer: footer.length > 0 ? footer : []
  }
}

function parseKnowledgeTree(text) {
  const lines = text.split('\n').filter(l => l.trim())
  const rootMatch = text.match(/\*\*(.+?)\*\*/)
  const root = rootMatch ? rootMatch[1].trim() : (lines[0] || '知识框架').replace(/^[-*#]+\s*/, '').trim()

  // Try to extract cards from bold headings
  const cards = []
  const cardRegex = /\*\*(.+?)\*\*[：:]?\s*([\s\S]*?)(?=\n\*\*|$)/g
  let cardMatch
  while ((cardMatch = cardRegex.exec(text)) !== null) {
    const cardTitle = cardMatch[1].trim()
    const cardBody = cardMatch[2].trim()
    const cardLines = extractListItems(cardBody)
    cards.push({
      title: cardTitle,
      lines: cardLines.slice(0, 3),
      sub: cardLines.length > 3 ? cardLines[3] : ''
    })
  }

  if (cards.length === 0) {
    // Fallback: create card for each non-empty line
    for (let i = 1; i < Math.min(lines.length, 6); i++) {
      const line = lines[i].replace(/^[-*#]+\s*/, '').trim()
      if (line) cards.push({ title: line, lines: [], sub: '' })
    }
  }

  return { root, cards }
}

function parseExercises(text) {
  const basic = []
  const advancedParts = []
  const homeworkParts = []

  // Try to split by ### or ** labels
  const sections = text.split(/(?:^###\s+|^\*\*)/m)
  let currentSection = 'basic'

  for (const sec of sections) {
    const trimmed = sec.trim()
    if (!trimmed) continue

    if (trimmed.startsWith('基础') || trimmed.includes('基础练习')) {
      currentSection = 'basic'
      const items = extractListItems(trimmed.replace(/^基础[练习题]*[：:]*\**\s*/, ''))
      basic.push(...items)
    } else if (trimmed.startsWith('拓展') || trimmed.startsWith('提高') || trimmed.includes('拓展练习')) {
      currentSection = 'advanced'
      const content = trimmed.replace(/^拓展[练习题]*[：:]*\**\s*/, '').trim()
      if (content) advancedParts.push(content)
    } else if (trimmed.startsWith('作业') || trimmed.startsWith('课后') || trimmed.includes('课后作业')) {
      currentSection = 'homework'
      const content = trimmed.replace(/^(课后)?作业[：:]*\**\s*/, '').trim()
      if (content) homeworkParts.push(content)
    } else {
      // Assign to current section
      const items = extractListItems(trimmed)
      if (currentSection === 'basic') basic.push(...items)
      else if (currentSection === 'advanced') advancedParts.push(trimmed)
      else homeworkParts.push(trimmed)
    }
  }

  return {
    basic: basic.length > 0 ? basic : extractListItems(text).slice(0, 3),
    advanced: advancedParts.join('\n') || '拓展练习（见上方内容）',
    homework: homeworkParts.join('\n') || '完成课后练习题'
  }
}

function parseReflection(text) {
  const items = []

  // Split by ### sub-headings
  const subRegex = /^###\s+(.+)$/gm
  const subs = []
  let sm
  while ((sm = subRegex.exec(text)) !== null) {
    subs.push({ label: sm[1].trim(), start: sm.index + sm[0].length })
  }

  const kindMap = {
    '难点': 'difficulty', '预期': 'difficulty', '困难': 'difficulty',
    '应急': 'contingency', '方案': 'contingency', '对策': 'contingency',
    '改进': 'improvement', '优化': 'improvement', '方向': 'improvement', '提升': 'improvement'
  }

  if (subs.length > 0) {
    for (let j = 0; j < subs.length; j++) {
      const s = subs[j]
      const nextStart = j + 1 < subs.length ? subs[j + 1].start - subs[j + 1].label.length - 5 : text.length
      const subText = text.slice(s.start, nextStart).trim()
      let kind = 'difficulty'
      for (const [kw, kt] of Object.entries(kindMap)) {
        if (s.label.includes(kw)) { kind = kt; break }
      }
      items.push({ kind, label: s.label, text: subText })
    }
  } else {
    // Try **Bold Label:** patterns
    const boldRegex = /\*\*(.+?)\*\*[：:]?\s*([\s\S]*?)(?=\n\*\*|$)/g
    let bm
    while ((bm = boldRegex.exec(text)) !== null) {
      const label = bm[1].trim()
      const body = bm[2].trim()
      let kind = 'difficulty'
      for (const [kw, kt] of Object.entries(kindMap)) {
        if (label.includes(kw)) { kind = kt; break }
      }
      items.push({ kind, label, text: body })
    }
  }

  return items
}

function sendQuickCmd(cmd) {
  const map = {
    polish: ['请帮我润色当前教案的语言表达', '语言润色任务已完成！'],
    adapt: ['请帮我调整教案难度，分别给出基础版和提高版', '难度适配完成！'],
    evaluate: ['请评估当前教案的质量，给出改进建议', '评估报告已生成！'],
    export: ['请帮我导出教案为可打印格式', '已准备导出！'],
  }
  const [ut, at] = map[cmd] || ['执行快捷指令', '指令完成']
  appendMessage('user', ut)
  isTyping.value = true
  scrollChat()
  setTimeout(() => {
    isTyping.value = false
    appendMessage('ai', at)
    // 如果是生成类指令且还没有教案，加载 mock 数据演示
    if (['polish', 'adapt', 'evaluate'].includes(cmd) && !lessonPlan.value) {
      setLessonPlan(MOCK_LESSON_PLAN)
    }
  }, 1500)
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ====== Template ======
const tplTitle = ref('《背影》——朱自清')
const tplSubject = ref('语文')
const tplGrade = ref('八年级（上册）')
const tplHours = ref('2课时（90分钟）')
const tplTextbook = ref('部编版（人教版）')

const sectionIcons = {
  '教学目标': '<circle cx="10" cy="10" r="3"/><circle cx="10" cy="10" r="7"/><path d="M10 3v3M10 14v3M3 10h3M14 10h3"/>',
  '教学重难点': '<path d="M10 2l6 6-6 10L4 8z"/>',
  '教学过程': '<path d="M3 10h3l2-5 4 10 2-5h3"/>',
  '板书设计': '<path d="M3 17h14M7 3v4l-4 8h14l-4-8V3"/>',
  '练习与作业': '<rect x="4" y="2" width="12" height="16" rx="1.5"/><path d="M7 2v3h6V2M7 8h6M7 11h6M7 14h3"/>',
  '教学反思': '<path d="M8 2c-3 0-5 2.5-5 5 0 2 1.5 3.5 2 5h6c0.5-1.5 2-3 2-5 0-2.5-2-5-5-5z"/><path d="M8 15h0M7 18h2"/>',
}

const tplSections = reactive([
  { label: '教学目标', open: true, content: '知识目标：了解朱自清生平及写作背景；掌握重点字词；理清叙事线索和结构层次。\n能力目标：学习以"背影"为线索、以小见大的写作手法；品味朴素深情的语言；运用细节描写进行片段写作。\n素养目标：感受父子深挚亲情，理解中国式父爱的含蓄深沉；培养感恩意识。', get icon() { return sectionIcons[this.label] } },
  { label: '教学重难点', open: false, content: '重点：品读"望父买橘"等经典段落，体会细节描写中蕴含的深情。\n难点：体会朴素文字背后复杂的父子情感。\n突破策略：朗读感悟法、情境还原法、对比分析法、问题链驱动。', get icon() { return sectionIcons[this.label] } },
  { label: '教学过程', open: false, content: '第一课时（45分钟）：导入→初读扫清障碍→整体感知理清结构→聚焦"背影"精读品味→练习→总结\n第二课时（45分钟）：温故导入→探究"背影"深层意蕴→品味语言特色→练习→总结', get icon() { return sectionIcons[this.label] } },
  { label: '板书设计', open: false, content: '《背影》——朱自清\n线索：背影（点题 / 买橘详写 / 离别 / 思念）\n手法：以小见大 / 细节描写 / 铺垫蓄势 / 朴素语言\n主题：父子深情 + 成长中的理解与愧疚', get icon() { return sectionIcons[this.label] } },
  { label: '练习与作业', open: false, content: '基础练习：四次"背影"分析、四次"流泪"分析、选择题、简答题\n拓展练习：仿写片段《那一刻，我读懂了你》（200字）\n课后作业：背诵第6段；采访家人亲情故事', get icon() { return sectionIcons[this.label] } },
  { label: '教学反思', open: false, content: '预期难点：学生对家庭变故部分可能感到枯燥；青春期学生对父子深情主题有距离感\n应急方案：播放《父亲》MV渲染情感；出示明确讨论任务单\n改进方向：布置亲情主题大作文；开展对比阅读和分享会', get icon() { return sectionIcons[this.label] } },
])

const DRAFT_KEY = 'teach_dashboard_draft'
const tplGenerating = ref(false)

function handleNewTemplate() {
  tplTitle.value = ''
  tplSubject.value = '语文'
  tplGrade.value = '八年级（上册）'
  tplHours.value = '2课时（90分钟）'
  tplTextbook.value = '部编版（人教版）'
  for (const s of tplSections) {
    s.content = ''
    s.open = false
  }
}

function handleSaveDraft() {
  const draft = {
    title: tplTitle.value,
    subject: tplSubject.value,
    grade: tplGrade.value,
    hours: tplHours.value,
    textbook: tplTextbook.value,
    sections: tplSections.map(s => ({ label: s.label, content: s.content, open: s.open }))
  }
  localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
  appendMessage('sys', '💾 草稿已保存到本地')
  scrollChat()
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const draft = JSON.parse(raw)
    if (draft.title !== undefined) tplTitle.value = draft.title
    if (draft.subject) tplSubject.value = draft.subject
    if (draft.grade) tplGrade.value = draft.grade
    if (draft.hours) tplHours.value = draft.hours
    if (draft.textbook) tplTextbook.value = draft.textbook
    if (draft.sections) {
      for (let i = 0; i < Math.min(draft.sections.length, tplSections.length); i++) {
        if (draft.sections[i].content !== undefined) tplSections[i].content = draft.sections[i].content
        if (draft.sections[i].open !== undefined) tplSections[i].open = draft.sections[i].open
      }
    }
  } catch { /* ignore corrupt draft */ }
}

function buildTemplatePrompt() {
  const sections = tplSections.map(s =>
    `### ${s.label}\n${s.content.trim() || '（请根据上下文合理补全此部分）'}`
  ).join('\n\n')

  return `你是一个专业的教案生成助手。请根据以下教师填写的教案框架，生成完整教案。

【基本信息】
- 课题：${tplTitle.value || '（待定）'}
- 学科：${tplSubject.value}
- 年级：${tplGrade.value}
- 课时：${tplHours.value}
- 教材版本：${tplTextbook.value}

【教师草稿——已有内容请保留核心思路并润色扩充，空白部分请根据上下文和学科特点合理补全】

${sections}

【输出要求】
请以 Markdown 格式返回完整教案。使用 # 标题、| 表格、有序/无序列表等标准 Markdown 语法。不要用代码块包裹教案内容，不要返回 JSON。`
}

function handleAIGenerate() {
  const prompt = buildTemplatePrompt()
  tplGenerating.value = true
  isTyping.value = true
  appendMessage('user', '📋 通过模板生成教案：' + (tplTitle.value || '未命名'))
  scrollChat()

  debugLog('模板生成请求', { prompt_preview: prompt.slice(0, 400), prompt_length: prompt.length })

  try {
    gwSend(prompt)
  } catch (err) {
    isTyping.value = false
    tplGenerating.value = false
    debugLog('模板生成失败', { message: err.message })
    appendMessage('ai', `❌ 模板生成失败 — ${err.message}`)
  }
  scrollChat()
}

// ====== Command mode ======
const cmdIcons = {
  '语言润色': '<path d="M13 2L4 11l-1 4 4-1 9-9-3-3z"/><path d="M4 11l3 3"/>',
  '难度适配': '<path d="M2 18L10 2l3 5 5 3-8 8z"/>',
  '生成板书': '<rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/>',
  '智能评估': '<rect x="3" y="12" width="3" height="6" rx="0.5"/><rect x="8.5" y="7" width="3" height="11" rx="0.5"/><rect x="14" y="3" width="3" height="15" rx="0.5"/>',
  '导出PDF': '<path d="M10 3v10M6 9l4 4 4-4M3 15v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2"/>',
  '扩写活动': '<path d="M10 3v14M3 10h14"/>',
  '对标课标': '<circle cx="10" cy="10" r="7"/><path d="M7 10l2 2 4-4"/>',
  '补充阅读': '<path d="M2 6h4l3-4 3 4h4v12H2z"/>',
  '分层设计': '<path d="M3 4h14M3 8h10M3 12h6M3 16h12"/>',
  '设计提问链': '<circle cx="10" cy="10" r="7"/><path d="M9 9a1 1 0 0 1 2 0c0 1.5-2 2-2 3"/><circle cx="10" cy="14" r="0.5"/>',
}

const cmdCategories = [
  { key: 'all', label: '全部' },
  { key: 'polish', label: '润色' },
  { key: 'adapt', label: '适配' },
  { key: 'generate', label: '生成' },
  { key: 'export', label: '导出' },
  { key: 'custom', label: '自定义' },
]

const presetCmds = [
  { icon: '语言润色', name: '语言润色', desc: '优化教学语言表达', cat: 'polish' },
  { icon: '难度适配', name: '难度适配', desc: '生成基础版+提高版', cat: 'adapt' },
  { icon: '生成板书', name: '生成板书', desc: '设计精美板书', cat: 'generate' },
  { icon: '智能评估', name: '智能评估', desc: '评估教案质量', cat: 'polish' },
  { icon: '扩写活动', name: '扩写活动', desc: '补充课堂互动', cat: 'generate' },
  { icon: '导出PDF', name: '导出PDF', desc: '导出打印版本', cat: 'export' },
  { icon: '对标课标', name: '对标课标', desc: '检查课标符合度', cat: 'polish' },
  { icon: '补充阅读', name: '补充阅读', desc: '推荐相关阅读材料', cat: 'generate' },
  { icon: '分层设计', name: '分层设计', desc: '快班/慢班分别设计', cat: 'adapt' },
  { icon: '设计提问链', name: '设计提问链', desc: '生成递进式问题', cat: 'generate' },
]

const customCmds = ref([])
const activeCmdCat = ref('all')
const cmdAddInput = ref('')

const cmdGenerating = ref(false)

const filteredCmds = computed(() => {
  if (activeCmdCat.value === 'custom') return []
  return presetCmds.filter(c => activeCmdCat.value === 'all' || c.cat === activeCmdCat.value)
})

// Map preset command names to detailed AI instructions.
// If the command is not in this map, the name itself is used as the instruction.
const CMD_INSTRUCTIONS = {
  '语言润色': '请对教案中所有文字进行语言润色，使表达更加专业、流畅、富有教学感染力。保留原有的结构和内容要点，不要改变教学环节的先后顺序。',
  '难度适配': '请为当前教案生成基础版和提高版两个版本。基础版降低练习难度、增加引导步骤；提高版增加思维深度题、开放性问题。',
  '生成板书': '请重点优化教案中的板书设计部分，使板书结构化、层次分明、重点突出，便于学生理解和记忆。',
  '智能评估': '请从教学目标、内容深度、活动设计、时间分配四个维度评估当前教案质量，给出具体评分和改进建议。请以评估报告文本格式回复，不要返回教案JSON。',
  '扩写活动': '请为教案的教学过程补充更多课堂互动活动，包括小组讨论、角色扮演、游戏化练习等，增加学生参与度和课堂趣味性。',
  '导出PDF': '请将当前教案整理为适合打印的清晰格式，只保留核心内容。请以纯文本/Markdown格式回复，不要返回JSON。',
  '对标课标': '请检查当前教案与课程标准的符合程度，标注哪些部分已达标、哪些需要加强，并给出具体调整建议。',
  '补充阅读': '请为教案推荐3-5个相关的补充阅读材料或背景知识资源，简要说明每个资源的推荐理由。',
  '分层设计': '请为教案设计快班和慢班两个版本的教学方案，在进度、深度、练习量上做出区分。快班增加探究性内容，慢班增加脚手架和示范。',
  '设计提问链': '请为教案设计一套递进式问题链，覆盖识记→理解→应用→分析→评价→创造六个层次，每个层次给出2-3个具体问题。',
}

function buildCmdPrompt(name) {
  const instruction = CMD_INSTRUCTIONS[name] || name

  // Include current lesson plan as context so AI can modify it
  let planContext = ''
  if (lessonPlan.value) {
    // Limit serialized size to avoid huge payloads
    const planStr = JSON.stringify(lessonPlan.value)
    planContext = planStr.length > 8000
      ? `\n\n【当前教案（已截断）】\n${planStr.slice(0, 8000)}\n...（后续内容省略）`
      : `\n\n【当前教案——请在此基础之上进行修改】\n${planStr}`
  }

  // Commands that should NOT return JSON lesson plan format
  const textOnlyCmds = ['智能评估', '导出PDF', '补充阅读', '对标课标']
  const isTextOnly = textOnlyCmds.includes(name)

  let outputReq = ''
  if (isTextOnly) {
    outputReq = '\n\n【输出要求】请以清晰的Markdown格式回复，使用标题、列表等结构化排版。不要返回JSON教案。'
  } else {
    outputReq = `\n\n【输出要求】请以 Markdown 格式返回修改后的完整教案。使用 # 标题、| 表格、有序/无序列表等标准 Markdown 语法。不要用代码块包裹教案内容，不要返回 JSON。`
  }

  return `你是一个专业的教案优化助手。请执行以下操作：

【操作指令】${name}
【详细要求】${instruction}${planContext}${outputReq}`
}

function executeCmd(name) {
  appendMessage('user', `⚡ ${name}`)
  isTyping.value = true
  cmdGenerating.value = true
  scrollChat()

  const prompt = buildCmdPrompt(name)
  debugLog('指令执行', { command: name, prompt_preview: prompt.slice(0, 300), prompt_length: prompt.length })

  try {
    gwSend(prompt)
  } catch (err) {
    isTyping.value = false
    cmdGenerating.value = false
    debugLog('指令失败', { message: err.message })
    appendMessage('ai', `❌ 指令执行失败 — ${err.message}`)
  }
  scrollChat()
}

function addCustomCmd() {
  const val = cmdAddInput.value.trim()
  if (!val) return
  customCmds.value.push(val)
  cmdAddInput.value = ''
}

// ====== Resizer ======
const leftPanel = ref(null)
const mainArea = ref(null)
const resizer = ref(null)

function startResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startW = leftPanel.value.getBoundingClientRect().width
  resizer.value.classList.add('active')
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  function onMove(e) {
    const dx = e.clientX - startX
    const newW = startW + dx
    const totalW = mainArea.value.getBoundingClientRect().width
    const pct = (newW / totalW) * 100
    if (pct > 20 && pct < 60) {
      leftPanel.value.style.width = pct + '%'
      leftPanel.value.style.minWidth = '0'
    }
  }
  function onUp() {
    resizer.value.classList.remove('active')
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// ====== Display modes ======
const displayMode = ref('preview')
const sourceFiles = ref([])
const selectedSourceFile = ref(null)
const isEditing = ref(false)
const displayBody = ref(null)

const displayBodyStyle = computed(() => {
  if (displayMode.value === 'class') {
    return { fontSize: '1.05rem', padding: '32px 48px', maxWidth: '900px', margin: '0 auto' }
  }
  return {}
})

function toggleEditMode() {
  isEditing.value = !isEditing.value
}

// ====== Export ======
function handleExport() {
  setTimeout(() => {}, 1000)
}

function downloadRawResponse() {
  if (!lastRawResponse.value) return
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const blob = new Blob([lastRawResponse.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai_response_${ts}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ====== Widget popups ======
const activeWidget = ref(null)
const widgets = [
  { key: 'signals', label: '教案列表', color: 'var(--accent)' },
  { key: 'gauge', label: '备课进度', color: 'var(--green)' },
  { key: 'alerts', label: '学情预警', color: 'var(--red)' },
]

function toggleWidget(key) {
  activeWidget.value = activeWidget.value === key ? null : key
}

// Close widget popups when clicking outside
function onDocClick(e) {
  if (!e.target.closest('.widget-pill') && !e.target.closest('.widget-popup')) {
    activeWidget.value = null
  }
}

// ====== Knowledge tree cards ======
const treeCards = [
  {
    title: '结构线索',
    icon: '<circle cx="7" cy="7" r="2"/><circle cx="13" cy="13" r="2"/><path d="M8.5 8l3 3"/>',
    lines: ['以"背影"为线索', '点题 → 回忆 → 思念'],
    sub: '四次背影 · 情感递进',
  },
  {
    title: '写作手法',
    icon: '<path d="M13 2L4 11l-1 4 4-1 9-9-3-3z"/>',
    lines: ['以小见大（买橘→父爱）', '细节描写（攀·缩·倾…）', '铺垫蓄势 / 朴素语言'],
    sub: '真挚美学的典范',
  },
  {
    title: '主题思想',
    icon: '<path d="M10 4a4 4 0 0 0-4 4v1a3 3 0 0 0 0 6h8a3 3 0 0 0 0-6v-1a4 4 0 0 0-4-4z"/>',
    lines: ['父子深情', '成长中的理解与愧疚'],
    sub: '跨越时代的共情力量',
  },
  {
    title: '文学价值',
    icon: '<polygon points="10,3 12,8 17,9 13,13 14,18 10,15 6,18 7,13 3,9 8,8"/>',
    lines: ['中国现代散文典范', '真挚情感 + 语言美学'],
    sub: '朴素自然 · 字字含情',
  },
  {
    title: '情感线索',
    icon: '<path d="M10 17c-4-3-8-5-8-9 0-2.5 2-4.5 4.5-4.5C8.5 3.5 10 5 10 5s1.5-1.5 3.5-1.5C16 3.5 18 5.5 18 8c0 4-4 6-8 9z"/>',
    lines: ['惦念 → 感动', '→ 惜别 → 思念'],
    sub: '从"不理解"到"理解"',
  },
]

// ====== Keyboard shortcuts ======
function onKeyDown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); handleSaveDraft() }
  if ((e.ctrlKey || e.metaKey) && e.key === 'e') { e.preventDefault(); toggleEditMode() }
}

// ====== Source lesson plan loading ======
async function loadSourceLessonPlan(role, userId) {
  try {
    const token = getToken()
    console.log('[source] fetching files, role=%s userId=%s token=%s', role, userId, token ? 'yes' : 'no')
    const data = await fetchSourceFiles(role, userId, token)
    console.log('[source] response:', data)
    sourceFiles.value = (data.files || []).filter(f => f.category === 'lesson-plans')
    console.log('[source] lesson-plan files:', sourceFiles.value)
    if (sourceFiles.value.length > 0) {
      await selectSourceFile(sourceFiles.value[0])
    }
  } catch (e) {
    console.warn('Failed to load source lesson plan:', e)
    // Fallback to mock
    setLessonPlan(MOCK_LESSON_PLAN)
  }
}

async function selectSourceFile(file) {
  try {
    const saved = loadUser()
    if (!saved) return
    const token = getToken()
    const data = await fetchSourceFile(file.path, saved.role, saved.userId, token)
    if (data?.content) {
      const content = data.content
      console.log('[selectSourceFile] content length:', content.length, 'starts with:', content.slice(0, 50))
      let plan = null
      // Try JSON first
      try {
        const parsed = JSON.parse(content)
        console.log('[selectSourceFile] JSON parsed, sections:', parsed?.sections?.length)
        if (parsed?.sections?.length) plan = normalizePlan(parsed)
      } catch (e) {
        console.log('[selectSourceFile] JSON parse failed:', e.message)
      }
      // Fallback to markdown
      if (!plan) {
        plan = buildPlanFromMarkdown(content)
        console.log('[selectSourceFile] markdown parse, sections:', plan?.sections?.length)
      }
      if (plan) {
        setLessonPlan(plan)
        selectedSourceFile.value = file.path
        console.log('[selectSourceFile] lesson plan set')
      } else {
        console.warn('[selectSourceFile] no plan could be parsed')
      }
    }
  } catch (e) {
    console.warn('Failed to load source file:', e)
  }
}

// ====== Lifecycle ======
onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKeyDown)
  loadDraft()
  scrollChat()
  const saved = loadUser()
  if (saved) {
    connectGateway({ role: saved.role, userId: saved.userId })
      .then(() => {
        setupStreamHandler()
        user.value = saved
        loadSessions()
        loadSourceLessonPlan(saved.role, saved.userId)
      })
      .catch(() => { clearUser(); setLessonPlan(MOCK_LESSON_PLAN) })
  } else {
    setLessonPlan(MOCK_LESSON_PLAN)
  }
})
</script>

<style>
/* ====== Theme ====== */
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255,255,255,0.55);
  --bg-card-hover: rgba(255,255,255,0.86);
  --bg-nav: rgba(255,255,255,0.82);
  --bg-input: rgba(255,255,255,0.50);
  --bg-tag: rgba(107,93,240,0.05);
  --bg-display: #fefeff;
  --bg-sidebar: rgba(250,249,254,0.70);
  --accent: #6B5DF0;
  --accent-light: rgba(107,93,240,0.20);
  --accent-soft: rgba(107,93,240,0.07);
  --accent-glow: rgba(107,93,240,0.16);
  --accent-bright: rgba(107,93,240,0.32);
  --accent-deep: #5A4AD0;
  --accent-teal: #0EA5B9;
  --accent-amber: #F59E0B;
  --accent-orange: #F97316;
  --accent-mint: #10B981;
  --accent-sky: #38A8E8;
  --accent-rose: #E04470;
  --accent-teal-soft: rgba(14,165,185,0.07);
  --accent-amber-soft: rgba(245,158,11,0.07);
  --accent-orange-soft: rgba(249,115,22,0.07);
  --accent-mint-soft: rgba(16,185,129,0.07);
  --accent-rose-soft: rgba(224,68,112,0.07);
  --accent-teal-light: rgba(14,165,185,0.20);
  --accent-amber-light: rgba(245,158,11,0.20);
  --accent-orange-light: rgba(249,115,22,0.20);
  --accent-mint-light: rgba(16,185,129,0.20);
  --accent-rose-light: rgba(224,68,112,0.20);
  --border-light: rgba(0,0,0,0.08);
  --border-medium: rgba(0,0,0,0.14);
  --border-active: #6B5DF0;
  --border-active-glow: rgba(107,93,240,0.38);
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0,0,0,0.06);
  --red: #F04438; --green: #16A34A;
  --card-radius: 16px;
  --panel-radius: 16px;
  --trans: 0.35s cubic-bezier(0.22,0.08,0.22,1);
  --trans-spring: 0.45s cubic-bezier(0.34,1.56,0.64,1);
  --bubble-ai: rgba(107,93,240,0.06);
  --bubble-ai-border: rgba(107,93,240,0.14);
  --bubble-user: rgba(14,165,185,0.07);
  --bubble-user-border: rgba(14,165,185,0.18);
  --board-bg: #2a4a2f;
  --board-frame: #8B6914;
  --board-chalk: #e8e4d8;
}
body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18,19,34,0.50);
  --bg-card-hover: rgba(24,25,44,0.72);
  --bg-nav: rgba(10,11,22,0.88);
  --bg-input: rgba(18,16,36,0.50);
  --bg-tag: rgba(123,92,255,0.06);
  --bg-display: #0f0f1a;
  --bg-sidebar: rgba(12,13,24,0.65);
  --accent: #8B70FF;
  --accent-light: rgba(139,112,255,0.24);
  --accent-soft: rgba(139,112,255,0.09);
  --accent-glow: rgba(139,112,255,0.22);
  --accent-bright: rgba(139,112,255,0.40);
  --accent-deep: #6B50E0;
  --accent-teal: #22B8CF;
  --accent-amber: #FBBF24;
  --accent-orange: #FB923C;
  --accent-mint: #34D399;
  --accent-sky: #38A8E8;
  --accent-rose: #F06090;
  --accent-teal-soft: rgba(34,184,207,0.09);
  --accent-amber-soft: rgba(251,191,36,0.09);
  --accent-orange-soft: rgba(251,146,60,0.09);
  --accent-mint-soft: rgba(52,211,153,0.09);
  --accent-rose-soft: rgba(240,96,144,0.09);
  --accent-teal-light: rgba(34,184,207,0.24);
  --accent-amber-light: rgba(251,191,36,0.24);
  --accent-orange-light: rgba(251,146,60,0.24);
  --accent-mint-light: rgba(52,211,153,0.24);
  --accent-rose-light: rgba(240,96,144,0.24);
  --border-light: rgba(255,255,255,0.09);
  --border-medium: rgba(255,255,255,0.16);
  --border-active: #8B70FF;
  --border-active-glow: rgba(139,112,255,0.48);
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.07);
  --bubble-ai: rgba(139,112,255,0.08);
  --bubble-ai-border: rgba(139,112,255,0.18);
  --bubble-user: rgba(34,184,207,0.09);
  --bubble-user-border: rgba(34,184,207,0.22);
  --board-bg: #1a2f1e;
  --board-frame: #6B5010;
  --board-chalk: #d8d4c8;
  --panel-radius: 4px;
}
body.dark .msg-bubble code { background:rgba(255,255,255,0.08); }
body.dark .msg-bubble pre { background:rgba(255,255,255,0.06); }
body.dark .msg-bubble th { background:rgba(255,255,255,0.06); }
body.dark .msg-bubble th, body.dark .msg-bubble td { border-color:rgba(255,255,255,0.1); }
* { margin:0; padding:0; box-sizing:border-box; }
html { font-size: 15px; }
body {
  font-family: 'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  color: var(--text-primary); background: var(--bg-root);
  -webkit-font-smoothing: antialiased; min-height: 100vh;
  transition: background 0.4s, color 0.4s, border-radius 0.4s;
  overflow: hidden;
}

/* ====== Document content (global — applied to dynamic section components) ====== */
.doc-content h1 { font-family:'Playfair Display','Georgia',serif; font-size:1.6rem; font-weight:700; color:var(--accent); margin-bottom:20px; padding-bottom:12px; border-bottom:2px solid var(--accent-light); letter-spacing:0.02em; }
.doc-content h2 { font-size:1.15rem; font-weight:700; margin:28px 0 14px; padding-left:12px; border-left:3px solid var(--accent); color:var(--text-primary); letter-spacing:0.01em; }
.doc-content h3 { font-size:1rem; font-weight:650; margin:20px 0 10px; color:var(--accent-deep); letter-spacing:0.01em; }
.doc-content h4 { font-size:0.90rem; font-weight:600; margin:14px 0 8px; color:var(--text-secondary); }
.doc-content p { margin:8px 0; }
.doc-content strong { color:var(--text-primary); font-weight:650; }
.doc-content ul, .doc-content ol { margin:8px 0; padding-left:22px; }
.doc-content li { margin:3px 0; }
.doc-content table { width:100%; border-collapse:collapse; margin:12px 0; font-size:0.84rem; border-radius:8px; overflow:hidden; }
.doc-content table th { background:var(--accent-soft); color:var(--accent); font-weight:600; padding:8px 12px; text-align:left; border-bottom:2px solid var(--accent-light); font-size:0.78rem; letter-spacing:0.03em; }
.doc-content table td { padding:7px 12px; border-bottom:1px solid var(--divider); color:var(--text-secondary); }
.doc-content table tr:last-child td { border-bottom:none; }
.doc-content table tbody tr:hover td { background:var(--accent-soft); }
.doc-content table td:first-child { font-weight:550; color:var(--accent-deep); }
.doc-content blockquote { margin:10px 0; padding:8px 14px; border-left:3px solid var(--accent-amber); background:rgba(245,158,11,0.04); border-radius:0 6px 6px 0; color:var(--text-secondary); }
.doc-content hr { border:none; height:1px; background:var(--divider); margin:20px 0; }
.doc-content code { font-family:'JetBrains Mono','Cascadia Code',monospace; font-size:0.78rem; background:var(--bg-tag); padding:1px 5px; border-radius:3px; color:var(--accent-deep); }
.doc-content .highlight-box { background:var(--accent-soft); border:1.5px solid var(--accent-light); border-radius:10px; padding:12px 16px; margin:12px 0; }

/* Empty state */
.empty-display { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text-muted); text-align:center; }
.empty-icon { width:64px; height:64px; border-radius:16px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.empty-icon svg { width:28px; height:28px; stroke:var(--text-muted); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }
.empty-title { font-size:0.94rem; font-weight:600; color:var(--text-secondary); margin-bottom:6px; }
.empty-desc { font-size:0.76rem; max-width:260px; line-height:1.6; }

/* Chalkboard */
.chalkboard { margin:20px 0; position:relative; }
.board-frame { background:linear-gradient(180deg,#C4943C 0%,#A0722A 4%,#8B6018 8%,#6B4810 12%,#8B6018 16%,#A0722A 20%,#C4943C 24%,#B8862A 50%,#C4943C 76%,#A0722A 80%,#8B6018 84%,#6B4810 88%,#8B6018 92%,#A0722A 96%,#C4943C 100%); border-radius:14px; padding:10px; box-shadow:0 4px 20px rgba(0,0,0,0.18),inset 0 1px 2px rgba(255,255,255,0.08); }
.board-frame::after { content:''; position:absolute; inset:8px; border-radius:6px; border:1px solid rgba(0,0,0,0.18); pointer-events:none; }
.board-inner { background:var(--board-bg); background-image: radial-gradient(ellipse at 20% 15%, rgba(255,255,255,0.03) 0%,transparent 50%), radial-gradient(ellipse at 80% 85%, rgba(0,0,0,0.08) 0%,transparent 50%), repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.008) 2px,rgba(255,255,255,0.008) 4px); border-radius:6px; padding:24px 28px; color:var(--board-chalk); font-family:'STKaiti','KaiTi','楷体','Noto Serif SC',serif; letter-spacing:0.03em; line-height:1.9; position:relative; overflow:hidden; }
.board-inner::before { content:''; position:absolute; inset:0; pointer-events:none; background:radial-gradient(circle at 50% 0%,rgba(255,255,255,0.04),transparent 60%), radial-gradient(circle at 30% 80%,rgba(200,220,200,0.05),transparent 50%); border-radius:6px; }
.board-tray { height:6px; background:linear-gradient(180deg,#C4943C,#8B6018); border-radius:0 0 3px 3px; margin:0 20px; box-shadow:0 2px 6px rgba(0,0,0,0.15); }
.board-title { font-size:1.3rem; font-weight:700; text-align:center; letter-spacing:0.08em; margin-bottom:20px; text-shadow:0 1px 2px rgba(0,0,0,0.2); position:relative; z-index:1; }
.board-title::after { content:''; display:block; width:60%; height:1px; margin:8px auto 0; background:linear-gradient(90deg,transparent,rgba(232,228,216,0.3),transparent); }
.board-section { position:relative; z-index:1; margin-bottom:16px; }
.board-section-title { font-size:0.82rem; font-weight:700; letter-spacing:0.05em; padding:3px 10px; border-left:3px solid rgba(232,228,216,0.55); margin-bottom:8px; color:rgba(255,255,240,0.9); }
.board-flow { display:flex; align-items:flex-start; gap:12px; flex-wrap:wrap; position:relative; z-index:1; }
.board-box { background:rgba(255,255,255,0.04); border:1px dashed rgba(232,228,216,0.22); border-radius:10px; padding:12px 14px; flex:1; min-width:130px; text-align:center; }
.board-box.central { border-style:solid; border-color:rgba(232,228,216,0.35); background:rgba(255,255,255,0.06); flex:1.4; }
.board-box-title { font-size:0.80rem; font-weight:700; margin-bottom:6px; color:rgba(255,255,245,0.95); }
.board-box ul { list-style:none; padding:0; margin:0; font-size:0.76rem; }
.board-box li { margin:3px 0; opacity:0.82; }
.board-box li.hl { color:#FFD580; font-weight:600; opacity:1; }
.board-arrow { display:flex; align-items:center; font-size:1.2rem; color:rgba(232,228,216,0.4); flex-shrink:0; padding-top:20px; }
.board-footer { text-align:center; font-size:0.80rem; margin-top:14px; letter-spacing:0.05em; opacity:0.7; position:relative; z-index:1; }
.board-footer span { margin:0 10px; }
.board-corner { position:absolute; width:40px; height:40px; pointer-events:none; z-index:2; }
.board-corner.tl { top:2px; left:2px; border-top:1.5px solid rgba(232,228,216,0.15); border-left:1.5px solid rgba(232,228,216,0.15); border-radius:4px 0 0 0; }
.board-corner.br { bottom:2px; right:2px; border-bottom:1.5px solid rgba(232,228,216,0.15); border-right:1.5px solid rgba(232,228,216,0.15); border-radius:0 0 4px 0; }
.chalk-dust { position:absolute; bottom:4px; left:10%; right:10%; height:20px; background:radial-gradient(ellipse at center,rgba(220,210,180,0.15),transparent 70%); pointer-events:none; border-radius:50%; }

/* Knowledge tree */
.knowledge-tree { margin:16px 0; position:relative; }
.tree-root { display:inline-flex; align-items:center; gap:8px; padding:10px 20px; border-radius:20px; margin:0 auto 22px; background:linear-gradient(135deg,var(--accent-soft),var(--bg-tag)); border:2px solid var(--accent-light); font-weight:700; font-size:0.92rem; position:relative; left:50%; transform:translateX(-50%); box-shadow:0 0 16px var(--accent-soft); }
.tree-root svg { width:18px; height:18px; stroke:var(--accent); fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.tree-root::after { content:''; position:absolute; bottom:-18px; left:50%; width:1.5px; height:16px; background:var(--accent); transform:translateX(-50%); opacity:0.22; border-radius:1px; }
.tree-branches { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; padding-top:4px; position:relative; }
.tree-branch { flex:1; min-width:140px; max-width:220px; position:relative; padding-top:18px; }
.tree-branch::before { content:''; position:absolute; top:0; left:50%; width:1.5px; height:16px; background:var(--accent); transform:translateX(-50%); opacity:0.18; border-radius:1px; }
.tree-card { background:var(--bg-card); border:1.5px solid var(--border-light); border-radius:12px; padding:12px; transition:all 0.3s var(--trans-spring); cursor:default; box-shadow:0 2px 8px rgba(0,0,0,0.02); min-width:140px; flex:1; }
.tree-card:hover { box-shadow:0 4px 16px var(--accent-soft); transform:translateY(-2px); border-color:var(--accent-light); }
.tree-card-title { font-size:0.78rem; font-weight:700; margin-bottom:6px; display:flex; align-items:center; gap:5px; color:var(--accent); }
.tree-card-title svg { width:16px; height:16px; stroke:var(--accent); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.tree-card-body { font-size:0.72rem; color:var(--text-secondary); line-height:1.6; }
.tree-card-body .tcl { padding:2px 0; display:flex; align-items:flex-start; gap:4px; }
.tree-card-body .tcl::before { content:'·'; color:var(--accent); font-weight:700; flex-shrink:0; }
.tree-card-sub { margin-top:6px; padding-top:6px; border-top:1px dashed var(--divider); font-size:0.68rem; color:var(--text-muted); }
</style>

<style scoped>
/* ====== Layout ====== */
.app-shell { display:flex; flex-direction:column; height:100vh; width:100%; overflow:hidden; padding:6px 10px; gap:6px; min-width:1100px; }

/* ====== TOP NAV ====== */
.top-nav {
  flex-shrink:0; height:50px; display:flex; align-items:center; justify-content:space-between;
  background:var(--bg-nav); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  border:1.5px solid var(--border-medium); border-radius:var(--panel-radius);
  padding:0 24px; position:relative;
  box-shadow:0 0 16px var(--accent-soft);
  transition: border-radius 0.4s;
}
.top-nav::before { content:''; position:absolute; pointer-events:none; top:-1px; left:28px; right:28px; height:1.5px; border-radius:1px; background:linear-gradient(90deg,transparent,var(--accent-light),transparent); opacity:0.55; }
.nav-left { display:flex; align-items:center; gap:20px; }
.nav-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.4rem; font-weight:700; color:var(--accent); letter-spacing:-0.01em; display:flex; align-items:center; gap:7px; }
.nav-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); animation:dotPulse 2s ease-in-out infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.6);opacity:0.6} }
.nav-center { display:flex; align-items:center; gap:3px; }
.nav-tab { padding:6px 14px; border-radius:13px; font-size:0.82rem; font-weight:500; color:var(--text-secondary); cursor:pointer; transition:all 0.25s; border:1.5px solid transparent; white-space:nowrap; }
.nav-tab:hover { color:var(--text-primary); background:var(--bg-tag); }
.nav-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 14px var(--accent-glow); }
.nav-right { display:flex; align-items:center; gap:8px; }
.nav-icon { width:32px; height:32px; border-radius:50%; border:1.5px solid var(--border-medium); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--text-secondary); transition:all 0.25s; flex-shrink:0; }
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.nav-icon:hover { color:var(--accent); border-color:var(--border-active); box-shadow:0 0 16px var(--accent-glow); }
.nav-avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,#7B5CFF,#A78BFA); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:0.74rem; cursor:pointer; border:2px solid transparent; box-shadow:0 0 16px var(--accent-glow); transition:all 0.25s; }
.nav-avatar:hover { transform:scale(1.06); }
.conn-status { display:flex; align-items:center; gap:5px; padding:4px 10px; border-radius:12px; font-size:0.72rem; color:var(--text-muted); border:1px solid var(--border-light); background:var(--bg-card); cursor:default; }
.conn-status.online { color:var(--green); border-color:rgba(22,163,74,0.25); }
.conn-dot { width:7px; height:7px; border-radius:50%; background:var(--text-muted); flex-shrink:0; }
.conn-status.online .conn-dot { background:var(--green); box-shadow:0 0 6px rgba(22,163,74,0.5); }
.conn-label { font-weight:500; }

/* ====== MAIN AREA ====== */
.main-area { flex:1; min-height:0; display:flex; gap:1px; position:relative; }

/* ====== LEFT TOOL STRIP ====== */
.tool-strip {
  width:48px; flex-shrink:0; display:flex; flex-direction:column; gap:4px;
  background:var(--bg-sidebar); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1.5px solid var(--border-light); border-radius:var(--panel-radius);
  padding:6px; position:relative; z-index:10;
  transition: border-radius 0.4s;
}
.tool-btn {
  width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center;
  cursor:pointer; transition:all 0.25s; border:1px solid transparent;
  color:var(--text-muted); position:relative;
}
.tool-btn svg { width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.tool-btn:hover { color:var(--text-primary); background:var(--bg-card-hover); border-color:var(--border-light); }
.tool-btn.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 10px var(--accent-soft); }
.tool-btn .tooltip {
  position:absolute; left:44px; top:50%; transform:translateY(-50%);
  background:var(--bg-card); border:1px solid var(--border-medium); border-radius:7px;
  padding:4px 10px; font-size:0.72rem; white-space:nowrap; pointer-events:none;
  opacity:0; transition:opacity 0.2s; z-index:20; color:var(--text-primary);
}
.tool-btn:hover .tooltip { opacity:1; }
.tool-divider { height:1px; background:var(--divider); margin:4px 6px; flex-shrink:0; }
.tool-spacer { flex:1; }
.tool-stats { margin-top:auto; display:flex; flex-direction:column; gap:3px; }
.ts-item { text-align:center; padding:5px 2px; border-radius:6px; font-size:0.64rem; font-weight:600; cursor:pointer; transition:all 0.2s; border:1px solid transparent; }
.ts-item:hover { background:var(--bg-card-hover); }
.ts-val { font-size:0.80rem; }
.ts-lbl { font-size:0.56rem; color:var(--text-muted); }

/* ====== LEFT PANEL ====== */
.left-panel {
  width:38%; min-width:380px; flex-shrink:0; display:flex; flex-direction:column;
  background:var(--bg-card); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1.5px solid var(--border-active); border-radius:var(--panel-radius);
  position:relative; overflow:hidden;
  box-shadow:0 0 18px var(--accent-glow),0 0 40px var(--accent-soft);
  transition: border-radius 0.4s;
}
/* Glow strips — clockwise rotation */
.lp-strip { position:absolute; pointer-events:none; z-index:1; }
.lp-strip.top, .lp-strip.bottom { left:-100%; width:100%; height:1.5px; background:linear-gradient(90deg,transparent,#C4B0FF,#7B5CFF,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
.lp-strip.right, .lp-strip.left { top:-100%; width:1.5px; height:100%; background:linear-gradient(180deg,transparent,#C4B0FF,#A78BFA,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
/* clockwise: top→right→bottom→left */
.lp-strip.top    { top:0;    animation:scanH 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); }
.lp-strip.right  { right:0;  animation:scanV 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:0.8s; }
.lp-strip.bottom { bottom:0; animation:scanHRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:1.6s; }
.lp-strip.left   { left:0;   animation:scanVRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:2.4s; }
@keyframes scanH    { 0%{left:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:100%;opacity:0} }
@keyframes scanHRev { 0%{left:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:-100%;opacity:0} }
@keyframes scanV    { 0%{top:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:100%;opacity:0} }
@keyframes scanVRev { 0%{top:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:-100%;opacity:0} }

.lp-header {
  flex-shrink:0; display:flex; align-items:center; justify-content:space-between;
  padding:10px 14px; border-bottom:1px solid var(--divider); background:var(--bg-card);
}
.lp-header-left { display:flex; align-items:center; gap:8px; }
.lp-ai-avatar { width:28px; height:28px; border-radius:8px; background:linear-gradient(135deg,var(--accent),#A78BFA); display:flex; align-items:center; justify-content:center; color:#fff; font-size:0.7rem; font-weight:700; }
.lp-mode-tabs { display:flex; gap:2px; }
.lp-mode-tab {
  padding:5px 12px; border-radius:8px; font-size:0.76rem; font-weight:500;
  color:var(--text-muted); cursor:pointer; transition:all 0.25s;
  border:1.5px solid transparent; display:flex; align-items:center; gap:5px;
}
.lp-mode-tab:hover { color:var(--text-primary); background:var(--bg-tag); }
.lp-mode-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 12px var(--accent-glow); }
.lp-mode-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
.lp-mode-tab.active .lp-mode-dot { background:var(--accent); box-shadow:0 0 6px var(--accent-glow); }

.lp-body { flex:1; min-height:0; overflow-y:auto; }
.lp-body::-webkit-scrollbar { width:3px; }
.lp-body::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }

.lp-mode-panel { display:none; height:100%; animation:fadeSlide 0.3s ease-out; }
.lp-mode-panel.active { display:flex; flex-direction:column; }
@keyframes fadeSlide { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }

/* ---- CHAT MODE ---- */
.chat-messages { flex:1; min-height:0; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:10px; }
.chat-messages::-webkit-scrollbar { width:3px; }
.chat-messages::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }
.chat-msg { display:flex; gap:8px; animation:msgIn 0.35s ease-out; max-width:92%; }
@keyframes msgIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.chat-msg.ai { align-self:flex-start; }
.chat-msg.user { align-self:flex-end; flex-direction:row-reverse; }
.chat-msg.sys { align-self:flex-start; }
.chat-msg .msg-avatar { width:30px; height:30px; border-radius:8px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:0.68rem; font-weight:700; color:#fff; margin-top:2px; }
.chat-msg.ai .msg-avatar { background:linear-gradient(135deg,var(--accent),#A78BFA); }
.chat-msg.user .msg-avatar { background:linear-gradient(135deg,var(--accent-teal),#5CCFCF); }
.chat-msg.sys .msg-avatar { background:linear-gradient(135deg,#F59E0B,#F0A050); font-size:0.75rem; }
.chat-msg .msg-bubble { padding:9px 13px; border-radius:12px; font-size:0.80rem; line-height:1.6; word-break:break-word; }
.msg-bubble p { margin:0 0 0.5em; } .msg-bubble p:last-child { margin-bottom:0; }
.msg-bubble h1,.msg-bubble h2,.msg-bubble h3,.msg-bubble h4 { margin:0.6em 0 0.3em; font-weight:600; }
.msg-bubble h1 { font-size:1.1em; } .msg-bubble h2 { font-size:1.0em; } .msg-bubble h3 { font-size:0.95em; }
.msg-bubble ul,.msg-bubble ol { margin:0.3em 0; padding-left:1.5em; }
.msg-bubble li { margin:0.15em 0; }
.msg-bubble code { background:rgba(0,0,0,0.06); padding:1px 4px; border-radius:3px; font-size:0.9em; }
.msg-bubble pre { background:rgba(0,0,0,0.06); padding:8px 10px; border-radius:6px; overflow-x:auto; margin:0.4em 0; }
.msg-bubble pre code { background:none; padding:0; }
.msg-bubble blockquote { border-left:3px solid var(--accent); padding-left:10px; margin:0.4em 0; color:var(--text-muted); }
.msg-bubble table { border-collapse:collapse; margin:0.4em 0; font-size:0.85em; }
.msg-bubble th,.msg-bubble td { border:1px solid var(--bubble-ai-border); padding:4px 8px; }
.msg-bubble th { background:rgba(0,0,0,0.04); }
.msg-bubble strong { font-weight:600; }
.msg-bubble .katex { font-size:1em; }
.msg-bubble .katex-display { margin:0.5em 0; overflow-x:auto; overflow-y:hidden; }
.msg-bubble .katex-display>.katex { text-align:left; }
.chat-msg.ai .msg-bubble { background:var(--bubble-ai); border:1px solid var(--bubble-ai-border); border-top-left-radius:3px; color:var(--text-primary); }
.chat-msg.user .msg-bubble { background:var(--bubble-user); border:1px solid var(--bubble-user-border); border-top-right-radius:3px; color:var(--text-primary); }
.chat-msg.sys .msg-bubble { background:rgba(245,158,11,0.05); border:1px dashed rgba(245,158,11,0.22); border-radius:8px; font-size:0.72rem; color:var(--text-muted); font-style:italic; }
.chat-msg .msg-time { font-size:0.60rem; color:var(--text-muted); margin-top:3px; padding:0 4px; }
.chat-msg.user .msg-time { text-align:right; }
.msg-actions { margin-top:6px; padding:0 4px; }
.msg-save-btn {
  padding:5px 14px; border-radius:6px; font-size:0.72rem; font-weight:550;
  border:1.5px solid var(--accent); background:var(--accent-soft); color:var(--accent);
  cursor:pointer; font-family:inherit; transition:all 0.2s;
}
.msg-save-btn:hover { background:var(--accent); color:#fff; }
.msg-saved-tag {
  display:inline-block; margin-top:6px; padding:2px 10px; border-radius:4px;
  font-size:0.66rem; color:var(--green); background:rgba(22,163,74,0.08);
  border:1px solid rgba(22,163,74,0.2); margin-left:4px;
}
.chat-typing { align-self:flex-start; display:none; gap:6px; padding:6px 12px; background:var(--bubble-ai); border:1px solid var(--bubble-ai-border); border-radius:12px; border-top-left-radius:3px; margin-left:38px; }
.chat-typing.show { display:flex; }
.chat-typing span { width:6px; height:6px; border-radius:50%; background:var(--accent); animation:typeBounce 1.2s ease-in-out infinite; }
.chat-typing span:nth-child(2) { animation-delay:0.2s; } .chat-typing span:nth-child(3) { animation-delay:0.4s; }
.stream-cursor { display:inline-block; width:3px; height:1em; background:var(--accent); margin-left:2px; vertical-align:text-bottom; animation:streamBlink 0.8s ease-in-out infinite; }
@keyframes streamBlink { 0%,100% { opacity:1; } 50% { opacity:0.2; } }
@keyframes typeBounce { 0%,60%,100%{transform:translateY(0);opacity:0.4} 30%{transform:translateY(-6px);opacity:1} }

.chat-chips { flex-shrink:0; display:flex; gap:6px; padding:4px 14px 8px; flex-wrap:wrap; border-top:1px solid var(--divider); justify-content:center; }
.chat-chip { padding:5px 12px; border-radius:14px; font-size:0.68rem; font-weight:500; cursor:pointer; transition:all 0.22s; white-space:nowrap; border:1.5px solid var(--border-light); background:var(--bg-tag); color:var(--text-secondary); display:flex; align-items:center; gap:5px; }
.chat-chip svg { width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.chat-chip:hover { border-color:var(--border-active); color:var(--accent); box-shadow:0 0 10px var(--accent-soft); transform:translateY(-1px); }

.chat-input-wrap { flex-shrink:0; display:flex; align-items:center; gap:6px; padding:8px 14px; border-top:1px solid var(--divider); background:var(--bg-card); }
.chat-input { flex:1; padding:8px 12px; border-radius:20px; min-height:38px; max-height:100px; border:1.5px solid var(--border-light); background:var(--bg-input); color:var(--text-primary); font-family:inherit; font-size:0.80rem; outline:none; resize:none; transition:all 0.25s; line-height:1.5; }
.chat-input:focus { border-color:var(--border-active); box-shadow:0 0 12px var(--accent-soft); }
.chat-send { width:36px; height:36px; border-radius:50%; border:none; cursor:pointer; background:var(--accent); color:#fff; display:flex; align-items:center; justify-content:center; transition:all 0.25s; flex-shrink:0; box-shadow:0 0 10px var(--accent-glow); }
.chat-send:hover { box-shadow:0 0 22px var(--accent-bright); transform:scale(1.06); }
.chat-send svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; }

/* ---- TEMPLATE MODE ---- */
.tpl-panel-body { padding:12px 14px; flex:1; overflow-y:auto; }
.tpl-panel-body::-webkit-scrollbar { width:3px; }
.tpl-panel-body::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }
.lp-meta { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }
.lp-field { display:flex; flex-direction:column; gap:2px; min-width:80px; }
.lp-field label { font-size:0.62rem; font-weight:600; color:var(--text-muted); letter-spacing:0.04em; text-transform:uppercase; }
.lp-field input, .lp-field select { padding:6px 9px; border-radius:7px; border:1.5px solid var(--border-light); background:var(--bg-input); color:var(--text-primary); font-family:inherit; font-size:0.80rem; outline:none; transition:all 0.25s; min-width:90px; }
.lp-field input:focus, .lp-field select:focus { border-color:var(--border-active); box-shadow:0 0 8px var(--accent-soft); }
.lp-title-input { width:100%; padding:9px 12px; border-radius:8px; border:1.5px solid var(--border-light); background:var(--bg-input); color:var(--text-primary); font-family:inherit; font-size:1rem; font-weight:600; outline:none; transition:all 0.25s; margin-bottom:10px; }
.lp-title-input:focus { border-color:var(--border-active); box-shadow:0 0 14px var(--accent-soft); }
.lp-section { margin-bottom:8px; border:1.5px solid var(--border-light); border-radius:9px; background:var(--bg-tag); overflow:hidden; transition:all 0.25s; position:relative; }
.lp-section:hover { border-color:var(--border-medium); }
.lp-section.open { border-color:var(--accent-light); background:var(--accent-soft); }
.lp-section-header { display:flex; align-items:center; justify-content:space-between; padding:7px 10px; cursor:pointer; user-select:none; font-size:0.80rem; font-weight:600; color:var(--text-secondary); transition:all 0.25s; }
.lp-section-header:hover { color:var(--text-primary); }
.lp-section.open .lp-section-header { color:var(--accent); border-bottom:1px solid var(--divider); }
.lp-section-body { display:none; padding:8px 10px; }
.lp-section.open .lp-section-body { display:block; animation:fadeSlide 0.25s ease-out; }
.lp-textarea { width:100%; min-height:70px; padding:7px 10px; border-radius:7px; border:1.5px solid var(--border-light); background:var(--bg-input); color:var(--text-primary); font-family:inherit; font-size:0.78rem; outline:none; resize:vertical; transition:all 0.25s; line-height:1.6; }
.lp-textarea:focus { border-color:var(--border-active); box-shadow:0 0 10px var(--accent-soft); }
.lp-chevron { transition:transform 0.3s; color:var(--text-muted); }
.lp-section.open .lp-chevron { transform:rotate(180deg); color:var(--accent); }
.tpl-actions { display:flex; gap:5px; padding:8px 14px; border-top:1px solid var(--divider); }
.wb-btn { padding:5px 11px; border-radius:7px; font-size:0.72rem; font-weight:500; cursor:pointer; border:1.5px solid var(--border-medium); background:transparent; color:var(--text-secondary); transition:all 0.25s; font-family:inherit; display:flex; align-items:center; gap:4px; }
.wb-btn:hover { border-color:var(--border-active); color:var(--accent); }
.wb-btn.primary { background:var(--accent); color:#fff; border-color:transparent; box-shadow:0 0 12px var(--accent-glow); }
.wb-btn.primary:hover { box-shadow:0 0 22px var(--accent-bright); transform:translateY(-1px); }

/* ---- SESSIONS MODE ---- */
.sessions-panel-body { padding:10px 14px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:8px; }
.sessions-panel-body::-webkit-scrollbar { width:3px; }
.sessions-panel-body::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }
.sessions-loading { text-align:center; padding:20px; color:var(--text-muted); font-size:0.78rem; }
.sessions-error { text-align:center; padding:20px; color:var(--red); font-size:0.78rem; }
.sessions-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:30px 10px; color:var(--text-muted); }
.sessions-empty svg { stroke:var(--text-muted); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; margin-bottom:10px; opacity:0.5; }
.sessions-empty p { font-size:0.78rem; }
.sessions-list { display:flex; flex-direction:column; gap:4px; }
.session-item {
  display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:10px;
  cursor:pointer; transition:all 0.2s; border:1.5px solid transparent;
  background:var(--bg-tag);
}
.session-item:hover { border-color:var(--border-light); background:var(--bg-card-hover); }
.session-item.active { border-color:var(--accent-light); background:var(--accent-soft); }
.session-icon { width:28px; height:28px; border-radius:7px; background:var(--bg-card); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.session-icon svg { width:14px; height:14px; stroke:var(--text-muted); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.session-item.active .session-icon { background:var(--accent-soft); }
.session-item.active .session-icon svg { stroke:var(--accent); }
.session-info { flex:1; min-width:0; }
.session-title { font-size:0.78rem; font-weight:550; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.session-item.active .session-title { color:var(--accent); }
.session-meta { font-size:0.66rem; color:var(--text-muted); margin-top:2px; }
.session-delete {
  width:24px; height:24px; border-radius:5px; border:none; background:transparent;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  opacity:0; transition:all 0.2s; flex-shrink:0;
}
.session-item:hover .session-delete { opacity:1; }
.session-delete:hover { background:rgba(240,68,56,0.08); }
.session-delete svg { width:12px; height:12px; stroke:var(--text-muted); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.session-delete:hover svg { stroke:var(--red); }
.sessions-new-btn {
  display:flex; align-items:center; justify-content:center; gap:6px;
  padding:10px; border-radius:10px; border:1.5px dashed var(--border-light);
  background:transparent; cursor:pointer; font-family:inherit; font-size:0.78rem;
  font-weight:500; color:var(--text-muted); transition:all 0.2s; margin-top:4px;
}
.sessions-new-btn svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2; stroke-linecap:round; }
.sessions-new-btn:hover { border-color:var(--accent-light); color:var(--accent); background:var(--accent-soft); }

/* ---- COMMAND MODE ---- */
.cmd-panel-body { padding:10px 14px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; }
.cmd-panel-body::-webkit-scrollbar { width:3px; }
.cmd-panel-body::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }
.cmd-cat-tabs { display:flex; gap:3px; flex-wrap:wrap; }
.cmd-cat-tab { padding:4px 10px; border-radius:14px; font-size:0.68rem; font-weight:500; cursor:pointer; transition:all 0.2s; border:1.5px solid var(--border-light); background:transparent; color:var(--text-muted); white-space:nowrap; }
.cmd-cat-tab:hover { border-color:var(--border-medium); color:var(--text-primary); }
.cmd-cat-tab.active { color:#fff; }
.cmd-cat-tab[data-cat="all"].active { background:var(--accent); border-color:var(--accent); }
.cmd-cat-tab[data-cat="polish"].active { background:var(--accent-teal); border-color:var(--accent-teal); }
.cmd-cat-tab[data-cat="adapt"].active { background:var(--accent-orange); border-color:var(--accent-orange); }
.cmd-cat-tab[data-cat="generate"].active { background:var(--accent-mint); border-color:var(--accent-mint); }
.cmd-cat-tab[data-cat="export"].active { background:var(--accent-amber); border-color:var(--accent-amber); }
.cmd-cat-tab[data-cat="custom"].active { background:var(--accent-rose); border-color:var(--accent-rose); }
.cmd-grid { display:grid; grid-template-columns:1fr 1fr; gap:5px; }
.cmd-card { padding:10px; border-radius:9px; border:1.5px solid var(--border-light); background:var(--bg-tag); cursor:pointer; transition:all 0.25s var(--trans-spring); display:flex; flex-direction:column; gap:4px; position:relative; overflow:hidden; }
.cmd-card::after { content:''; position:absolute; top:0; left:0; width:3px; height:100%; border-radius:3px 0 0 3px; opacity:0; transition:opacity 0.25s; }
.cmd-card:hover { transform:translateY(-2px); }
.cmd-card:hover::after { opacity:1; }
.cmd-card[data-cat="polish"]:hover { border-color:var(--accent-teal); box-shadow:0 0 14px var(--accent-teal-light); }
.cmd-card[data-cat="polish"]::after { background:var(--accent-teal); }
.cmd-card[data-cat="polish"] .cmd-icon svg { stroke:var(--accent-teal); }
.cmd-card[data-cat="adapt"]:hover { border-color:var(--accent-orange); box-shadow:0 0 14px var(--accent-orange-light); }
.cmd-card[data-cat="adapt"]::after { background:var(--accent-orange); }
.cmd-card[data-cat="adapt"] .cmd-icon svg { stroke:var(--accent-orange); }
.cmd-card[data-cat="generate"]:hover { border-color:var(--accent-mint); box-shadow:0 0 14px var(--accent-mint-light); }
.cmd-card[data-cat="generate"]::after { background:var(--accent-mint); }
.cmd-card[data-cat="generate"] .cmd-icon svg { stroke:var(--accent-mint); }
.cmd-card[data-cat="export"]:hover { border-color:var(--accent-amber); box-shadow:0 0 14px var(--accent-amber-light); }
.cmd-card[data-cat="export"]::after { background:var(--accent-amber); }
.cmd-card[data-cat="export"] .cmd-icon svg { stroke:var(--accent-amber); }
.cmd-card[data-cat="polish"] .cmd-name { color:var(--accent-teal); }
.cmd-card[data-cat="adapt"] .cmd-name { color:var(--accent-orange); }
.cmd-card[data-cat="generate"] .cmd-name { color:var(--accent-mint); }
.cmd-card[data-cat="export"] .cmd-name { color:var(--accent-amber); }
.cmd-card .cmd-icon { display:flex; align-items:center; gap:4px; }
.cmd-card .cmd-icon svg { width:16px; height:16px; stroke:var(--accent); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.cmd-card .cmd-name { font-size:0.78rem; font-weight:600; color:var(--accent); }
.cmd-card .cmd-desc { font-size:0.64rem; color:var(--text-muted); }
.cmd-card.cmd-disabled { opacity:0.45; pointer-events:none; cursor:not-allowed; }
.cmd-add-row { display:flex; gap:6px; padding:0 14px 10px; border-top:1px solid var(--divider); padding-top:8px; }
.cmd-add-input { flex:1; padding:5px 9px; border-radius:7px; border:1.5px solid var(--border-light); background:var(--bg-input); color:var(--text-primary); font-family:inherit; font-size:0.72rem; outline:none; transition:all 0.2s; }
.cmd-add-input:focus { border-color:var(--border-active); }
.cmd-add-btn { padding:5px 12px; border-radius:7px; font-size:0.70rem; font-weight:500; cursor:pointer; border:1.5px dashed var(--border-medium); background:transparent; color:var(--text-muted); transition:all 0.2s; white-space:nowrap; }
.cmd-add-btn:hover { border-color:var(--border-active); color:var(--accent); background:var(--bg-tag); }
.cmd-custom-list { display:flex; flex-direction:column; gap:3px; }
.cmd-custom-item { display:flex; align-items:center; justify-content:space-between; padding:5px 8px; border-radius:6px; font-size:0.72rem; background:var(--bg-tag); border:1px solid transparent; transition:all 0.2s; }
.cmd-custom-item:hover { border-color:var(--border-light); }
.cmd-custom-del { cursor:pointer; color:var(--text-muted); font-size:0.8rem; padding:2px 5px; border-radius:4px; transition:all 0.2s; }
.cmd-custom-del:hover { color:var(--red); background:rgba(240,68,56,0.06); }

/* ====== RESIZER ====== */
.resizer { width:8px; flex-shrink:0; cursor:col-resize; position:relative; z-index:15; background:transparent; transition:background 0.2s; }
.resizer:hover, .resizer.active { background:var(--accent-light); }
.resizer::after { content:''; position:absolute; left:50%; top:10%; bottom:10%; width:2px; border-radius:1px; background:var(--border-light); transform:translateX(-50%); transition:all 0.2s; }
.resizer:hover::after, .resizer.active::after { background:var(--accent); width:3px; box-shadow:0 0 10px var(--accent-glow); }

/* ====== DISPLAY AREA (right) ====== */
.display-area {
  flex:1; min-width:340px; display:flex; flex-direction:column;
  background:var(--bg-display); border:1.5px solid var(--border-light);
  border-radius:var(--panel-radius); position:relative; overflow:hidden;
  box-shadow:0 0 14px rgba(0,0,0,0.03);
  transition: border-radius 0.4s;
}
.display-header {
  flex-shrink:0; display:flex; align-items:center; justify-content:space-between;
  padding:8px 16px; border-bottom:1px solid var(--divider); background:var(--bg-card);
}
.display-title { font-size:0.80rem; font-weight:600; color:var(--text-secondary); display:flex; align-items:center; gap:6px; }
.display-title .dot { width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 6px rgba(22,163,74,0.3); }
.display-actions { display:flex; gap:5px; align-items:center; }
.source-file-selector { display:flex; align-items:center; gap:6px; }
.source-select {
  padding:4px 10px; border-radius:6px; font-size:0.72rem; font-weight:500;
  border:1.5px solid var(--border-light); background:var(--bg-card); color:var(--text-primary);
  cursor:pointer; font-family:inherit; outline:none; max-width:200px;
}
.source-select:focus { border-color:var(--accent); }
.da-btn {
  padding:4px 10px; border-radius:6px; font-size:0.70rem; font-weight:500; cursor:pointer;
  border:1.5px solid var(--border-light); background:transparent; color:var(--text-muted);
  transition:all 0.25s; font-family:inherit; position:relative;
}
.da-btn:hover { border-color:var(--border-medium); color:var(--text-primary); }
.da-btn.active { color:var(--accent); border-color:var(--accent-light); background:var(--accent-soft); }
.da-btn.editing { color:var(--green); border-color:rgba(22,163,74,0.25); background:rgba(22,163,74,0.05); }
.da-btn .da-tip { display:none; position:absolute; top:110%; left:50%; transform:translateX(-50%); background:var(--bg-card); border:1px solid var(--border-medium); border-radius:6px; padding:3px 8px; font-size:0.60rem; white-space:nowrap; z-index:10; color:var(--text-secondary); }
.da-btn:hover .da-tip { display:block; }

.display-body {
  flex:1; min-height:0; overflow-y:auto; padding:24px 32px;
  font-size:0.88rem; line-height:1.85; color:var(--text-primary);
}
.display-body::-webkit-scrollbar { width:4px; }
.display-body::-webkit-scrollbar-thumb { background:var(--border-medium); border-radius:4px; }

/* Document content */
.doc-content h1 { font-family:'Playfair Display','Georgia',serif; font-size:1.6rem; font-weight:700; color:var(--accent); margin-bottom:20px; padding-bottom:12px; border-bottom:2px solid var(--accent-light); letter-spacing:0.02em; }
.doc-content h2 { font-size:1.15rem; font-weight:700; margin:28px 0 14px; padding-left:12px; border-left:3px solid var(--accent); color:var(--text-primary); letter-spacing:0.01em; }
.doc-content h3 { font-size:1rem; font-weight:650; margin:20px 0 10px; color:var(--accent-deep); letter-spacing:0.01em; }
.doc-content h4 { font-size:0.90rem; font-weight:600; margin:14px 0 8px; color:var(--text-secondary); }
.doc-content p { margin:8px 0; }
.doc-content strong { color:var(--text-primary); font-weight:650; }
.doc-content ul, .doc-content ol { margin:8px 0; padding-left:22px; }
.doc-content li { margin:3px 0; }
.doc-content table { width:100%; border-collapse:collapse; margin:12px 0; font-size:0.84rem; border-radius:8px; overflow:hidden; }
.doc-content table th { background:var(--accent-soft); color:var(--accent); font-weight:600; padding:8px 12px; text-align:left; border-bottom:2px solid var(--accent-light); font-size:0.78rem; letter-spacing:0.03em; }
.doc-content table td { padding:7px 12px; border-bottom:1px solid var(--divider); color:var(--text-secondary); }
.doc-content table tr:last-child td { border-bottom:none; }
.doc-content table tbody tr:hover td { background:var(--accent-soft); }
.doc-content table td:first-child { font-weight:550; color:var(--accent-deep); }
.doc-content blockquote { margin:10px 0; padding:8px 14px; border-left:3px solid var(--accent-amber); background:rgba(245,158,11,0.04); border-radius:0 6px 6px 0; color:var(--text-secondary); }
.doc-content hr { border:none; height:1px; background:var(--divider); margin:20px 0; }
.doc-content code { font-family:'JetBrains Mono','Cascadia Code',monospace; font-size:0.78rem; background:var(--bg-tag); padding:1px 5px; border-radius:3px; color:var(--accent-deep); }
.doc-content .highlight-box { background:var(--accent-soft); border:1.5px solid var(--accent-light); border-radius:10px; padding:12px 16px; margin:12px 0; }
.doc-content .tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:600; margin-right:4px; }
.doc-content .tag.obj { background:rgba(107,93,240,0.08); color:var(--accent); }
.doc-content .tag.act { background:rgba(14,165,185,0.08); color:var(--accent-teal); }
.doc-content .tag.ref { background:rgba(245,158,11,0.08); color:#E09000; }

/* Empty state */
.empty-display { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text-muted); text-align:center; }
.empty-icon { width:64px; height:64px; border-radius:16px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.empty-icon svg { width:28px; height:28px; stroke:var(--text-muted); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }
.empty-title { font-size:0.94rem; font-weight:600; color:var(--text-secondary); margin-bottom:6px; }
.empty-desc { font-size:0.76rem; max-width:260px; line-height:1.6; }

/* Editing mode */
.display-body[contenteditable="true"]:focus { outline:2px dashed var(--accent-light); outline-offset:4px; border-radius:4px; }
.display-body[contenteditable="true"]:hover { background:rgba(107,93,240,0.01); }

/* ====== CHALKBOARD ====== */
.chalkboard { margin:20px 0; position:relative; }
.board-frame { background:linear-gradient(180deg,#C4943C 0%,#A0722A 4%,#8B6018 8%,#6B4810 12%,#8B6018 16%,#A0722A 20%,#C4943C 24%,#B8862A 50%,#C4943C 76%,#A0722A 80%,#8B6018 84%,#6B4810 88%,#8B6018 92%,#A0722A 96%,#C4943C 100%); border-radius:14px; padding:10px; box-shadow:0 4px 20px rgba(0,0,0,0.18),inset 0 1px 2px rgba(255,255,255,0.08); }
.board-frame::after { content:''; position:absolute; inset:8px; border-radius:6px; border:1px solid rgba(0,0,0,0.18); pointer-events:none; }
.board-inner { background:var(--board-bg); background-image: radial-gradient(ellipse at 20% 15%, rgba(255,255,255,0.03) 0%,transparent 50%), radial-gradient(ellipse at 80% 85%, rgba(0,0,0,0.08) 0%,transparent 50%), repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.008) 2px,rgba(255,255,255,0.008) 4px); border-radius:6px; padding:24px 28px; color:var(--board-chalk); font-family:'STKaiti','KaiTi','楷体','Noto Serif SC',serif; letter-spacing:0.03em; line-height:1.9; position:relative; overflow:hidden; }
.board-inner::before { content:''; position:absolute; inset:0; pointer-events:none; background:radial-gradient(circle at 50% 0%,rgba(255,255,255,0.04),transparent 60%), radial-gradient(circle at 30% 80%,rgba(200,220,200,0.05),transparent 50%); border-radius:6px; }
.board-tray { height:6px; background:linear-gradient(180deg,#C4943C,#8B6018); border-radius:0 0 3px 3px; margin:0 20px; box-shadow:0 2px 6px rgba(0,0,0,0.15); }
.board-title { font-size:1.3rem; font-weight:700; text-align:center; letter-spacing:0.08em; margin-bottom:20px; text-shadow:0 1px 2px rgba(0,0,0,0.2); position:relative; z-index:1; }
.board-title::after { content:''; display:block; width:60%; height:1px; margin:8px auto 0; background:linear-gradient(90deg,transparent,rgba(232,228,216,0.3),transparent); }
.board-section { position:relative; z-index:1; margin-bottom:16px; }
.board-section-title { font-size:0.82rem; font-weight:700; letter-spacing:0.05em; padding:3px 10px; border-left:3px solid rgba(232,228,216,0.55); margin-bottom:8px; color:rgba(255,255,240,0.9); }
.board-flow { display:flex; align-items:flex-start; gap:12px; flex-wrap:wrap; position:relative; z-index:1; }
.board-box { background:rgba(255,255,255,0.04); border:1px dashed rgba(232,228,216,0.22); border-radius:10px; padding:12px 14px; flex:1; min-width:130px; text-align:center; }
.board-box.central { border-style:solid; border-color:rgba(232,228,216,0.35); background:rgba(255,255,255,0.06); flex:1.4; }
.board-box-title { font-size:0.80rem; font-weight:700; margin-bottom:6px; color:rgba(255,255,245,0.95); }
.board-box ul { list-style:none; padding:0; margin:0; font-size:0.76rem; }
.board-box li { margin:3px 0; opacity:0.82; }
.board-box li.hl { color:#FFD580; font-weight:600; opacity:1; }
.board-arrow { display:flex; align-items:center; font-size:1.2rem; color:rgba(232,228,216,0.4); flex-shrink:0; padding-top:20px; }
.board-footer { text-align:center; font-size:0.80rem; margin-top:14px; letter-spacing:0.05em; opacity:0.7; position:relative; z-index:1; }
.board-footer span { margin:0 10px; }
.board-corner { position:absolute; width:40px; height:40px; pointer-events:none; z-index:2; }
.board-corner.tl { top:2px; left:2px; border-top:1.5px solid rgba(232,228,216,0.15); border-left:1.5px solid rgba(232,228,216,0.15); border-radius:4px 0 0 0; }
.board-corner.br { bottom:2px; right:2px; border-bottom:1.5px solid rgba(232,228,216,0.15); border-right:1.5px solid rgba(232,228,216,0.15); border-radius:0 0 4px 0; }
.chalk-dust { position:absolute; bottom:4px; left:10%; right:10%; height:20px; background:radial-gradient(ellipse at center,rgba(220,210,180,0.15),transparent 70%); pointer-events:none; border-radius:50%; }

/* ====== KNOWLEDGE TREE ====== */
.knowledge-tree { margin:16px 0; position:relative; }
.tree-root {
  display:inline-flex; align-items:center; gap:8px;
  padding:10px 20px; border-radius:20px; margin:0 auto 22px;
  background:linear-gradient(135deg,var(--accent-soft),var(--bg-tag));
  border:2px solid var(--accent-light); font-weight:700; font-size:0.92rem;
  position:relative; left:50%; transform:translateX(-50%);
  box-shadow:0 0 16px var(--accent-soft);
}
.tree-root svg { width:18px; height:18px; stroke:var(--accent); fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.tree-root::after { content:''; position:absolute; bottom:-18px; left:50%; width:1.5px; height:16px; background:var(--accent); transform:translateX(-50%); opacity:0.22; border-radius:1px; }
.tree-branches { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; padding-top:4px; position:relative; }
.tree-branch { flex:1; min-width:140px; max-width:220px; position:relative; padding-top:18px; }
.tree-branch::before { content:''; position:absolute; top:0; left:50%; width:1.5px; height:16px; background:var(--accent); transform:translateX(-50%); opacity:0.18; border-radius:1px; }
.tree-card { background:var(--bg-card); border:1.5px solid var(--border-light); border-radius:12px; padding:12px; transition:all 0.3s var(--trans-spring); cursor:default; box-shadow:0 2px 8px rgba(0,0,0,0.02); min-width:140px; flex:1; }
.tree-card:hover { box-shadow:0 4px 16px var(--accent-soft); transform:translateY(-2px); border-color:var(--accent-light); }
.tree-card-title { font-size:0.78rem; font-weight:700; margin-bottom:6px; display:flex; align-items:center; gap:5px; color:var(--accent); }
.tree-card-title svg { width:16px; height:16px; stroke:var(--accent); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.tree-card-body { font-size:0.72rem; color:var(--text-secondary); line-height:1.6; }
.tree-card-body .tcl { padding:2px 0; display:flex; align-items:flex-start; gap:4px; }
.tree-card-body .tcl::before { content:'·'; color:var(--accent); font-weight:700; flex-shrink:0; }
.tree-card-sub { margin-top:6px; padding-top:6px; border-top:1px dashed var(--divider); font-size:0.68rem; color:var(--text-muted); }

/* ====== BOTTOM WIDGET BAR ====== */
.widget-bar {
  flex-shrink:0; display:flex; align-items:center; gap:2px;
  background:var(--bg-card); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1.5px solid var(--border-light); border-radius:var(--panel-radius);
  padding:4px 8px; height:42px; overflow:hidden;
  transition: border-radius 0.4s;
}
.widget-pill { padding:4px 10px; border-radius:6px; font-size:0.70rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.25s; border:1px solid transparent; white-space:nowrap; flex-shrink:0; display:flex; align-items:center; gap:4px; }
.widget-pill:hover { color:var(--text-primary); background:var(--bg-tag); border-color:var(--border-light); }
.widget-pill.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 8px var(--accent-glow); }
.widget-pill .pill-dot { width:4px; height:4px; border-radius:50%; flex-shrink:0; }
.widget-popup { display:none; position:absolute; bottom:50px; left:50%; transform:translateX(-50%); background:var(--bg-card); border:1.5px solid var(--border-active); border-radius:var(--panel-radius); box-shadow:0 0 24px var(--accent-glow),0 8px 32px rgba(0,0,0,0.12); padding:14px 18px; z-index:50; min-width:340px; max-width:500px; animation:popIn 0.3s cubic-bezier(0.34,1.56,0.64,1); max-height:280px; overflow-y:auto; }
@keyframes popIn { from{opacity:0;transform:translateX(-50%) translateY(10px) scale(0.95)} to{opacity:1;transform:translateX(-50%) translateY(0) scale(1)} }
.widget-popup.show { display:block; }
.widget-popup::-webkit-scrollbar { width:3px; }
.widget-popup::-webkit-scrollbar-thumb { background:var(--accent-soft); border-radius:3px; }

.sig-r { display:flex; align-items:center; justify-content:space-between; padding:5px 8px; border-radius:6px; transition:all 0.2s; cursor:pointer; border:1px solid transparent; }
.sig-r:hover { background:var(--bg-card-hover); border-color:var(--border-light); }
.sig-r.active { border-color:var(--accent-light); background:var(--accent-soft); }
.sig-l { display:flex; align-items:center; gap:6px; min-width:0; }
.sdot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.sdot.r{ background:var(--red); box-shadow:0 0 7px rgba(240,68,56,0.45); }
.sdot.g{ background:var(--green); box-shadow:0 0 5px rgba(22,163,74,0.35); }
.sdot.a{ background:var(--accent-amber); box-shadow:0 0 5px rgba(245,158,11,0.40); }
.sdot.p{ background:var(--accent); box-shadow:0 0 5px var(--accent-glow); }
.sname { font-size:0.76rem; font-weight:550; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sdesc { font-size:0.64rem; color:var(--text-muted); }
.spct { font-size:0.76rem; font-weight:650; }
.spct.up{ color:var(--green); } .spct.dn{ color:var(--red); } .spct.st{ color:var(--text-muted); }
.gauge-wrap { display:flex; align-items:center; gap:10px; }
.gauge-svg { width:100px; height:70px; }
.g-track { fill:none; stroke:var(--divider); stroke-width:6; stroke-linecap:round; }
.g-fill { fill:none; stroke:url(#gGrad); stroke-width:6; stroke-linecap:round; stroke-dasharray:130; stroke-dashoffset:130; animation:gFill 1.2s ease-out forwards; }
@keyframes gFill { to { stroke-dashoffset:18; } }
.g-endpoint { fill:#fff; stroke:#7B5CFF; stroke-width:2; filter:drop-shadow(0 0 6px rgba(123,92,255,0.55)); }
.g-val { font-size:1.8rem; font-weight:700; letter-spacing:-0.03em; color:var(--accent); }
.g-lbl { font-size:0.62rem; color:var(--text-muted); letter-spacing:0.05em; }
.g-stats { display:flex; gap:12px; margin-top:5px; }
.gs-item { text-align:center; }
.gs-val { font-size:0.80rem; font-weight:650; }
.gs-lbl { font-size:0.58rem; color:var(--text-muted); }
.alert-row { display:flex; align-items:center; gap:6px; padding:5px 7px; border-radius:5px; transition:all 0.2s; cursor:pointer; border:1px solid transparent; }
.alert-row:hover { background:var(--bg-card-hover); border-color:var(--border-light); }
.alert-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.alert-name { font-size:0.76rem; font-weight:550; }
.alert-sub { font-size:0.64rem; color:var(--text-muted); }

/* ====== LOGIN SCREEN ====== */
.login-screen {
  display:flex; align-items:center; justify-content:center;
  height:100vh; width:100%; background:var(--bg-body);
}
.login-card {
  width:380px; padding:36px 32px;
  background:var(--bg-card); border:1.5px solid var(--border-active);
  border-radius:18px; text-align:center;
  box-shadow:0 0 40px var(--accent-soft),0 0 80px var(--accent-glow);
}
.login-header { margin-bottom:28px; }
.login-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.8rem; font-weight:700; color:var(--accent); letter-spacing:-0.01em; display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:8px; }
.login-logo .dot { width:8px; height:8px; border-radius:50%; background:var(--accent); box-shadow:0 0 14px var(--accent-glow); animation:dotPulse 2s ease-in-out infinite; }
.login-subtitle { font-size:0.82rem; color:var(--text-muted); margin-top:4px; }
.login-roles { display:flex; gap:8px; margin-bottom:18px; }
.role-btn {
  flex:1; padding:10px; border-radius:10px; cursor:pointer; text-align:center;
  border:1.5px solid var(--border-light); background:var(--bg-tag);
  font-size:0.80rem; font-weight:500; color:var(--text-secondary);
  transition:all 0.25s; font-family:inherit;
}
.role-btn:hover { border-color:var(--border-active); color:var(--text-primary); }
.role-btn.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 12px var(--accent-glow); }
.role-btn .role-label { font-weight:600; display:block; }
.role-btn .role-desc { font-size:0.66rem; color:var(--text-muted); margin-top:2px; display:block; }
.role-btn.active .role-desc { color:var(--accent); opacity:0.7; }
.login-input {
  width:100%; padding:10px 14px; border-radius:10px;
  border:1.5px solid var(--border-light); background:var(--bg-input);
  color:var(--text-primary); font-family:inherit; font-size:0.84rem;
  outline:none; transition:all 0.25s; margin-bottom:6px; box-sizing:border-box;
}
.login-input:focus { border-color:var(--border-active); box-shadow:0 0 12px var(--accent-soft); }
.login-input::placeholder { color:var(--text-muted); }
.login-error { font-size:0.74rem; color:var(--red); min-height:20px; margin-bottom:8px; }
.login-submit {
  width:100%; padding:11px; border-radius:10px; border:none; cursor:pointer;
  background:var(--accent); color:#fff; font-family:inherit; font-size:0.88rem; font-weight:600;
  transition:all 0.25s; box-shadow:0 0 16px var(--accent-glow);
}
.login-submit:hover { box-shadow:0 0 28px var(--accent-bright); transform:translateY(-1px); }
.login-submit:disabled { opacity:0.5; cursor:not-allowed; transform:none; box-shadow:none; }
.login-toggle {
  background:none; border:none; cursor:pointer; margin-top:12px;
  font-family:inherit; font-size:0.78rem; color:var(--text-muted);
  transition:color 0.2s;
}
.login-toggle:hover { color:var(--accent); }

@media(max-width:1280px){ .app-shell{ padding:4px 6px; gap:4px; min-width:0; } .tool-strip{ width:40px; } .left-panel{ width:36%; min-width:340px; } .display-body{ padding:16px 20px; } }
@media(max-width:900px){ .app-shell{ min-height:auto; } .main-area{ flex-direction:column; } .tool-strip{ flex-direction:row; width:100%; height:44px; } .left-panel{ width:100%; min-width:0; max-height:45%; } .resizer{ display:none; } .display-area{ flex:1; min-height:350px; } }
</style>

