<template>
  <!-- ====== LOGIN SCREEN ====== -->
  <div v-if="!user" class="login-screen">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo"><span class="dot"></span>Nanobot</div>
        <p class="login-subtitle">智能助学助手</p>
      </div>
      <div class="login-roles">
        <button v-for="r in roleOptions" :key="r.role" class="role-btn" :class="{ active: loginRole === r.role }" @click="loginRole = r.role">
          <span class="role-icon">{{ r.icon }}</span>
          <span class="role-label">{{ r.label }}</span>
        </button>
      </div>
      <input class="login-input" v-model="loginUserId" placeholder="输入用户名" @keydown.enter="handleLogin" autofocus />
      <p v-if="loginError" class="login-error">{{ loginError }}</p>
      <button class="login-submit" @click="handleLogin" :disabled="!loginRole || !loginUserId.trim() || loginLoading">
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
        <span class="nav-tab" :class="{ active: activeTab === 'path' }" @click="activeTab = 'path'">学习路径规划</span>
        <span class="nav-tab" :class="{ active: activeTab === 'qa' }" @click="activeTab = 'qa'">知识问答与讲解</span>
        <span class="nav-tab" :class="{ active: activeTab === 'companion' }" @click="activeTab = 'companion'">学习过程陪伴</span>
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

    <!-- ====== MAIN CONTENT AREA ====== -->
    <div class="main-area">

      <!-- ====== PAGE 1: 学习路径规划 ====== -->
      <div v-if="activeTab === 'path'" class="page-content path-page">

        <!-- Hero / 知识诊断概览 -->
        <section class="diagnosis-section">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 2"/></svg>
              知识诊断概览
            </h2>
            <span class="section-badge">上次诊断：{{ lastDiagnosisTime }}</span>
          </div>
          <div class="diagnosis-grid">
            <div class="diag-card" v-for="item in diagnosisData" :key="item.subject">
              <div class="diag-card-header">
                <span class="diag-subject">{{ item.subject }}</span>
                <span class="diag-rate" :style="{ color: rateColor(item.rate) }">{{ item.rate }}%</span>
              </div>
              <div class="diag-bar-track">
                <div class="diag-bar-fill" :style="{ width: item.rate + '%', background: rateGradient(item.rate) }"></div>
              </div>
              <div class="diag-tags">
                <span class="diag-tag weak" v-for="w in item.weakPoints" :key="w">{{ w }}</span>
              </div>
              <div class="diag-hint">薄弱环节</div>
            </div>
          </div>
        </section>

        <!-- 学习路径 -->
        <section class="path-section">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 20 20"><path d="M2 18L10 2l3 5 5 3-8 8z"/></svg>
              个性化学习路径
            </h2>
            <span class="section-badge">{{ pathProgress }} / {{ pathSteps.length }} 节点已完成</span>
          </div>
          <div class="path-timeline">
            <div class="path-node" v-for="(step, i) in pathSteps" :key="i" :class="{ done: step.done, current: step.current }">
              <div class="path-node-marker">
                <svg v-if="step.done" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/><path d="M6 10l3 3 5-5"/></svg>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <div class="path-node-body">
                <div class="path-node-title">{{ step.title }}</div>
                <div class="path-node-desc">{{ step.desc }}</div>
                <div class="path-node-meta">
                  <span class="pn-tag" :style="{ background: step.tagBg, color: step.tagColor }">{{ step.tag }}</span>
                  <span class="pn-time">{{ step.time }}</span>
                </div>
              </div>
              <div v-if="i < pathSteps.length - 1" class="path-connector" :class="{ done: step.done }"></div>
            </div>
          </div>
        </section>

        <!-- 推荐资源 -->
        <section class="resource-section">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
              推荐学习资源
            </h2>
            <span class="section-badge">基于你的知识诊断智能推荐</span>
          </div>
          <div class="resource-grid">
            <div class="res-card" v-for="r in resources" :key="r.id">
              <div class="res-card-icon" :style="{ background: r.iconBg }">
                <svg viewBox="0 0 20 20" v-html="r.icon"></svg>
              </div>
              <div class="res-card-body">
                <div class="res-card-title">{{ r.title }}</div>
                <div class="res-card-desc">{{ r.desc }}</div>
                <div class="res-card-footer">
                  <span class="res-type" :style="{ color: r.typeColor, background: r.typeBg }">{{ r.type }}</span>
                  <span class="res-dur">{{ r.duration }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 知识盲区预警 -->
        <section class="risk-section">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 20 20"><path d="M10 2l8 14H2z"/><circle cx="10" cy="13" r="1"/><path d="M10 7v4"/></svg>
              知识盲区风险预警
            </h2>
            <span class="section-badge">预判后续学习易踩坑难点</span>
          </div>
          <div class="risk-list">
            <div class="risk-item" v-for="(risk, i) in riskWarnings" :key="i" :class="risk.level">
              <div class="risk-level-dot"></div>
              <div class="risk-body">
                <div class="risk-title">{{ risk.title }}</div>
                <div class="risk-desc">{{ risk.desc }}</div>
              </div>
              <div class="risk-action">
                <span class="risk-level-label">{{ risk.levelLabel }}</span>
              </div>
            </div>
          </div>
        </section>

      </div>

      <!-- ====== PAGE 2: 知识问答与讲解 (placeholder) ====== -->
      <div v-if="activeTab === 'qa'" class="page-content placeholder-page">
        <div class="placeholder-card">
          <div class="placeholder-icon">
            <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/><path d="M8 8a2 2 0 1 1 4 0c0 3-4 4-4 4 M10 14h.01"/></svg>
          </div>
          <h3>知识问答与讲解</h3>
          <p>问答 · 解析 · 引导 — 针对学科问题提供分步解析与准确答案</p>
          <span class="placeholder-tag">即将上线</span>
        </div>
      </div>

      <!-- ====== PAGE 3: 学习过程陪伴 (placeholder) ====== -->
      <div v-if="activeTab === 'companion'" class="page-content placeholder-page">
        <div class="placeholder-card">
          <div class="placeholder-icon">
            <svg viewBox="0 0 20 20"><circle cx="10" cy="7" r="4"/><path d="M3 18c0-4 3-7 7-7s7 3 7 7"/></svg>
          </div>
          <h3>学习过程陪伴</h3>
          <p>陪伴 · 归因 · 优化 — 错题归因分析、学习策略指导与全程陪伴</p>
          <span class="placeholder-tag">即将上线</span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// ====== User / Login ======
const USER_KEY = 'nanobot-webui.user'
const roleOptions = [
  { role: 'student', icon: '📚', label: '学生' },
  { role: 'teacher', icon: '👨‍🏫', label: '教师' },
  { role: 'researcher', icon: '🔬', label: '研究员' },
]
const user = ref(null)
const authMode = ref('login')
const loginRole = ref('student')
const loginUserId = ref('')
const loginError = ref('')
const loginLoading = ref(false)
const connected = ref(false)
const connectionError = ref('')

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
  if (!loginRole.value || !trimmed) return
  if (trimmed.length > 64) { loginError.value = '用户名过长'; return }
  loginError.value = ''
  loginLoading.value = true
  try {
    const params = new URLSearchParams({ role: loginRole.value, user_id: trimmed })
    const endpoint = authMode.value === 'register'
      ? `/api/users/register?${params}&display_name=${encodeURIComponent(trimmed)}`
      : `/api/users/validate?${params}`
    const res = await fetch(endpoint, { credentials: 'same-origin' })
    const data = await res.json()
    if (!data.ok) {
      if (data.error === 'User not found') loginError.value = '用户不存在，请先注册'
      else if (data.error === 'User already exists') loginError.value = '用户已存在，请直接登录'
      else loginError.value = data.error || '验证失败'
      return
    }
    connected.value = true
    const u = { role: loginRole.value, userId: trimmed }
    saveUser(u)
    user.value = u
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
  connected.value = false
  clearUser()
  user.value = null
  loginUserId.value = ''
  loginRole.value = 'student'
  authMode.value = 'login'
}

// ====== Theme ======
const isDark = ref(false)
function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

// ====== Navigation ======
const activeTab = ref('path')

// ====== Page 1: 学习路径规划 Data ======
const lastDiagnosisTime = ref('2026-05-20 14:30')

const diagnosisData = ref([
  { subject: '数学', rate: 82, weakPoints: ['二次函数综合应用', '圆的几何证明'] },
  { subject: '语文', rate: 88, weakPoints: ['文言文虚词辨析', '议论文论证结构'] },
  { subject: '英语', rate: 75, weakPoints: ['定语从句', '完形填空上下文推断'] },
  { subject: '物理', rate: 68, weakPoints: ['浮力综合计算', '电路动态分析'] },
])

function rateColor(rate) {
  if (rate >= 85) return 'var(--green)'
  if (rate >= 70) return 'var(--accent-amber)'
  return 'var(--red)'
}

function rateGradient(rate) {
  if (rate >= 85) return 'linear-gradient(90deg, #16A34A, #4ADE80)'
  if (rate >= 70) return 'linear-gradient(90deg, #F59E0B, #FBBF24)'
  return 'linear-gradient(90deg, #F04438, #FB923C)'
}

const pathProgress = ref(2)
const pathSteps = ref([
  {
    title: '基础知识巩固 — 二次函数',
    desc: '回顾二次函数图像性质、顶点式、交点式，完成基础练习',
    tag: '必修', tagBg: 'rgba(107,93,240,0.08)', tagColor: 'var(--accent)',
    time: '预计 45 分钟', done: true, current: false,
  },
  {
    title: '二次函数综合应用突破',
    desc: '掌握二次函数与几何图形综合题的解题思路，精练 8 道典型例题',
    tag: '重点', tagBg: 'rgba(240,68,56,0.06)', tagColor: 'var(--red)',
    time: '预计 90 分钟', done: true, current: false,
  },
  {
    title: '圆的几何证明专项训练',
    desc: '系统梳理圆中角度、弦、切线的证明方法，归纳常见辅助线做法',
    tag: '当前', tagBg: 'rgba(14,165,185,0.08)', tagColor: 'var(--accent-teal)',
    time: '预计 60 分钟', done: false, current: true,
  },
  {
    title: '函数与几何压轴题综合',
    desc: '二次函数与圆、三角形的综合压轴题训练，提升综合解题能力',
    tag: '进阶', tagBg: 'rgba(245,158,11,0.08)', tagColor: 'var(--accent-amber)',
    time: '预计 120 分钟', done: false, current: false,
  },
  {
    title: '阶段性诊断评估',
    desc: '完成综合测试卷，检验本阶段学习成果，生成新的学习路径',
    tag: '评估', tagBg: 'rgba(16,185,129,0.08)', tagColor: 'var(--accent-mint)',
    time: '预计 90 分钟', done: false, current: false,
  },
])

const resources = ref([
  {
    id: 1,
    icon: '<rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/>',
    iconBg: 'linear-gradient(135deg, rgba(107,93,240,0.12), rgba(167,139,250,0.12))',
    title: '二次函数综合题精讲',
    desc: '含 12 道典型例题的分步解析，覆盖图像变换、最值问题、几何综合',
    type: '视频课程', typeColor: 'var(--accent)', typeBg: 'rgba(107,93,240,0.08)',
    duration: '约 45 分钟',
  },
  {
    id: 2,
    icon: '<path d="M5 3v14l5-3 5 3V3a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1z"/>',
    iconBg: 'linear-gradient(135deg, rgba(14,165,185,0.12), rgba(34,184,207,0.12))',
    title: '圆的几何证明方法汇编',
    desc: '归纳 6 大类辅助线做法与 18 道经典证明题，含详细解题思路',
    type: '习题集', typeColor: 'var(--accent-teal)', typeBg: 'rgba(14,165,185,0.08)',
    duration: '约 60 分钟',
  },
  {
    id: 3,
    icon: '<circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 2"/>',
    iconBg: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(251,191,36,0.12))',
    title: '中考函数压轴题历年真题',
    desc: '近 5 年中考函数与几何综合压轴题汇编，适合进阶冲刺',
    type: '真题卷', typeColor: 'var(--accent-amber)', typeBg: 'rgba(245,158,11,0.08)',
    duration: '约 120 分钟',
  },
  {
    id: 4,
    icon: '<path d="M2 4h16v2H2zM2 9h12v2H2zM2 14h8v2H2z"/>',
    iconBg: 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.12))',
    title: '知识图谱 — 函数专题',
    desc: '函数知识体系的可视化图谱，标注易错点与知识点关联关系',
    type: '知识图谱', typeColor: 'var(--accent-mint)', typeBg: 'rgba(16,185,129,0.08)',
    duration: '交互浏览',
  },
  {
    id: 5,
    icon: '<rect x="4" y="4" width="12" height="12" rx="1.5"/><path d="M8 9l2 2 4-4"/>',
    iconBg: 'linear-gradient(135deg, rgba(224,68,112,0.12), rgba(240,96,144,0.12))',
    title: '易错题专项训练 — 浮力计算',
    desc: '精选浮力章节 10 道高频易错题，附带详细错因分析与避坑指南',
    type: '专项练习', typeColor: 'var(--accent-rose)', typeBg: 'rgba(224,68,112,0.08)',
    duration: '约 40 分钟',
  },
  {
    id: 6,
    icon: '<path d="M10 2a8 8 0 1 0 0 16 7 7 0 0 1 0-14"/><circle cx="10" cy="10" r="3"/>',
    iconBg: 'linear-gradient(135deg, rgba(56,168,232,0.12), rgba(56,168,232,0.12))',
    title: 'AI 互动诊断 — 定语从句',
    desc: '通过 AI 对话式诊断定位定语从句薄弱点，实时生成针对性练习',
    type: 'AI 诊断', typeColor: 'var(--accent-sky)', typeBg: 'rgba(56,168,232,0.08)',
    duration: '约 20 分钟',
  },
])

const riskWarnings = ref([
  {
    title: '二次函数与几何综合：辅助线构造思维不足',
    desc: '后续"二次函数与圆综合"专题需先巩固圆的常见辅助线做法，建议在进入综合训练前完成圆的证明专项练习。',
    level: 'high', levelLabel: '高风险',
  },
  {
    title: '浮力计算：受力分析习惯不完整',
    desc: '浮力章节的错误集中在"漏画力"和"方向混淆"，这将直接影响后续压强浮力综合题以及高中力学入门。',
    level: 'high', levelLabel: '高风险',
  },
  {
    title: '英语定语从句：关系词选择凭语感',
    desc: '目前关系词选择正确率仅 62%，后续名词性从句、强调句等语法点易产生混淆，建议先系统梳理从句体系。',
    level: 'medium', levelLabel: '中风险',
  },
  {
    title: '文言文虚词：语境推断能力待加强',
    desc: '"之""其""而"等高频虚词的用法辨析不清晰，将影响课外文言文阅读的理解速度和准确率。',
    level: 'medium', levelLabel: '中风险',
  },
])

// Init
user.value = loadUser()
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
  --accent-sky-soft: rgba(56,168,232,0.07);
  --accent-rose-soft: rgba(224,68,112,0.07);
  --border-light: rgba(0,0,0,0.08);
  --border-medium: rgba(0,0,0,0.14);
  --border-active: #6B5DF0;
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0,0,0,0.06);
  --red: #F04438;
  --green: #16A34A;
  --panel-radius: 16px;
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
  --accent-sky-soft: rgba(56,168,232,0.09);
  --accent-rose-soft: rgba(240,96,144,0.09);
  --border-light: rgba(255,255,255,0.09);
  --border-medium: rgba(255,255,255,0.16);
  --border-active: #8B70FF;
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.07);
  --red: #F04438;
  --green: #16A34A;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg-root); color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}
</style>

<style scoped>
/* ====== Layout ====== */
.app-shell {
  display: flex; flex-direction: column; height: 100vh; width: 100%;
  overflow: hidden; padding: 6px 10px; gap: 6px; min-width: 960px;
}

/* ====== Login Screen ====== */
.login-screen {
  display: flex; align-items: center; justify-content: center;
  height: 100vh; width: 100%; background: var(--bg-root);
}
.login-card {
  width: 380px; padding: 36px 32px;
  background: var(--bg-card); border: 1.5px solid var(--border-active);
  border-radius: 18px; text-align: center;
  box-shadow: 0 0 40px var(--accent-soft), 0 0 80px var(--accent-glow);
}
.login-header { margin-bottom: 28px; }
.login-logo {
  font-family: 'Playfair Display', 'Georgia', serif; font-style: italic;
  font-size: 1.8rem; font-weight: 700; color: var(--accent);
  letter-spacing: -0.01em; display: flex; align-items: center;
  justify-content: center; gap: 8px; margin-bottom: 8px;
}
.login-logo .dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--accent);
  box-shadow: 0 0 14px var(--accent-glow); animation: dotPulse 2s ease-in-out infinite;
}
@keyframes dotPulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.6); opacity: 0.6; } }
.login-subtitle { font-size: 0.82rem; color: var(--text-muted); margin-top: 4px; }
.login-roles { display: flex; gap: 8px; margin-bottom: 18px; }
.role-btn {
  flex: 1; padding: 10px; border-radius: 10px; cursor: pointer; text-align: center;
  border: 1.5px solid var(--border-light); background: var(--bg-tag);
  font-size: 0.80rem; font-weight: 500; color: var(--text-secondary);
  transition: all 0.25s; font-family: inherit;
}
.role-btn:hover { border-color: var(--border-active); color: var(--text-primary); }
.role-btn.active {
  color: var(--accent); background: var(--accent-soft);
  border-color: var(--accent-light); box-shadow: 0 0 12px var(--accent-glow);
}
.role-icon { font-size: 1.4rem; display: block; margin-bottom: 4px; }
.role-label { font-weight: 600; display: block; }
.login-input {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid var(--border-light); background: var(--bg-input);
  color: var(--text-primary); font-family: inherit; font-size: 0.84rem;
  outline: none; transition: all 0.25s; margin-bottom: 6px; box-sizing: border-box;
}
.login-input:focus { border-color: var(--border-active); box-shadow: 0 0 12px var(--accent-soft); }
.login-input::placeholder { color: var(--text-muted); }
.login-error { font-size: 0.74rem; color: var(--red); min-height: 20px; margin-bottom: 8px; }
.login-submit {
  width: 100%; padding: 11px; border-radius: 10px; border: none; cursor: pointer;
  background: var(--accent); color: #fff; font-family: inherit; font-size: 0.88rem;
  font-weight: 600; transition: all 0.25s; box-shadow: 0 0 16px var(--accent-glow);
}
.login-submit:hover { box-shadow: 0 0 28px var(--accent-bright); transform: translateY(-1px); }
.login-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.login-toggle {
  background: none; border: none; cursor: pointer; margin-top: 12px;
  font-family: inherit; font-size: 0.78rem; color: var(--text-muted); transition: color 0.2s;
}
.login-toggle:hover { color: var(--accent); }

/* ====== Top Nav ====== */
.top-nav {
  flex-shrink: 0; height: 50px; display: flex; align-items: center; justify-content: space-between;
  background: var(--bg-nav); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border: 1.5px solid var(--border-medium); border-radius: var(--panel-radius);
  padding: 0 24px; position: relative;
  box-shadow: 0 0 16px var(--accent-soft);
}
.top-nav::before {
  content: ''; position: absolute; pointer-events: none; top: -1px; left: 28px; right: 28px;
  height: 1.5px; border-radius: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-light), transparent); opacity: 0.55;
}
.nav-left { display: flex; align-items: center; gap: 20px; }
.nav-logo {
  font-family: 'Playfair Display', 'Georgia', serif; font-style: italic;
  font-size: 1.4rem; font-weight: 700; color: var(--accent);
  letter-spacing: -0.01em; display: flex; align-items: center; gap: 7px;
}
.nav-logo .dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow); animation: dotPulse 2s ease-in-out infinite;
}
.nav-center { display: flex; align-items: center; gap: 3px; }
.nav-tab {
  padding: 6px 14px; border-radius: 13px; font-size: 0.82rem; font-weight: 500;
  color: var(--text-secondary); cursor: pointer; transition: all 0.25s;
  border: 1.5px solid transparent; white-space: nowrap;
}
.nav-tab:hover { color: var(--text-primary); background: var(--bg-tag); }
.nav-tab.active {
  color: var(--accent); background: var(--accent-soft);
  border-color: var(--accent-light); box-shadow: 0 0 14px var(--accent-glow);
}
.nav-right { display: flex; align-items: center; gap: 8px; }
.nav-icon {
  width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid var(--border-medium);
  background: transparent; cursor: pointer; display: flex; align-items: center;
  justify-content: center; color: var(--text-secondary); transition: all 0.25s; flex-shrink: 0;
}
.nav-icon svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.nav-icon:hover { color: var(--accent); border-color: var(--border-active); box-shadow: 0 0 16px var(--accent-glow); }
.nav-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #7B5CFF, #A78BFA);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 600; font-size: 0.74rem; cursor: pointer;
  border: 2px solid transparent; box-shadow: 0 0 16px var(--accent-glow); transition: all 0.25s;
}
.nav-avatar:hover { transform: scale(1.06); }
.conn-status {
  display: flex; align-items: center; gap: 5px; padding: 4px 10px;
  border-radius: 12px; font-size: 0.72rem; color: var(--text-muted);
  border: 1px solid var(--border-light); background: var(--bg-card); cursor: default;
}
.conn-status.online { color: var(--green); border-color: rgba(22,163,74,0.25); }
.conn-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); flex-shrink: 0; }
.conn-status.online .conn-dot { background: var(--green); box-shadow: 0 0 6px rgba(22,163,74,0.5); }
.conn-label { font-weight: 500; }

/* ====== Main Area ====== */
.main-area {
  flex: 1; min-height: 0; overflow-y: auto;
  background: var(--bg-card); border: 1.5px solid var(--border-medium);
  border-radius: var(--panel-radius); padding: 28px 32px;
}
.main-area::-webkit-scrollbar { width: 4px; }
.main-area::-webkit-scrollbar-thumb { background: var(--accent-soft); border-radius: 4px; }

/* ====== Section Header ====== */
.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 18px;
}
.section-title {
  font-size: 1.02rem; font-weight: 700; color: var(--text-primary);
  display: flex; align-items: center; gap: 8px;
}
.section-title svg { width: 20px; height: 20px; stroke: var(--accent); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.section-badge {
  font-size: 0.72rem; color: var(--text-muted);
  padding: 4px 12px; border-radius: 10px;
  background: var(--bg-tag); border: 1px solid var(--border-light);
}

/* ====== Page Layout ====== */
.page-content { display: flex; flex-direction: column; gap: 32px; }
.page-content > section { animation: fadeSlide 0.4s ease-out; }
@keyframes fadeSlide { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* ====== Diagnosis Section ====== */
.diagnosis-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.diag-card {
  background: var(--bg-card); border: 1.5px solid var(--border-light);
  border-radius: 14px; padding: 18px 16px;
  transition: all 0.3s;
}
.diag-card:hover { border-color: var(--accent-light); box-shadow: 0 4px 20px var(--accent-soft); transform: translateY(-2px); }
.diag-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.diag-subject { font-size: 0.90rem; font-weight: 700; color: var(--text-primary); }
.diag-rate { font-size: 1.4rem; font-weight: 800; }
.diag-bar-track {
  height: 7px; border-radius: 4px; background: var(--border-light);
  margin-bottom: 12px; overflow: hidden;
}
.diag-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease-out; }
.diag-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px; }
.diag-tag {
  font-size: 0.66rem; padding: 2px 8px; border-radius: 5px;
  background: rgba(240,68,56,0.06); color: var(--red);
  border: 1px solid rgba(240,68,56,0.12);
}
.diag-hint { font-size: 0.64rem; color: var(--text-muted); margin-top: 6px; }

/* ====== Path Timeline ====== */
.path-timeline { position: relative; padding-left: 28px; }
.path-node {
  position: relative; padding-bottom: 28px;
  display: flex; align-items: flex-start; gap: 14px;
}
.path-node:last-child { padding-bottom: 0; }
.path-node-marker {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700;
  border: 2px solid var(--border-light); background: var(--bg-card);
  color: var(--text-muted); z-index: 1; transition: all 0.3s;
}
.path-node.done .path-node-marker {
  background: var(--accent); border-color: var(--accent); color: #fff;
}
.path-node.done .path-node-marker svg { width: 18px; height: 18px; stroke: #fff; fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.path-node.current .path-node-marker {
  border-color: var(--accent-teal); color: var(--accent-teal);
  box-shadow: 0 0 14px rgba(14,165,185,0.3);
}
.path-node-body {
  flex: 1; background: var(--bg-card); border: 1.5px solid var(--border-light);
  border-radius: 12px; padding: 14px 18px; transition: all 0.3s;
}
.path-node.current .path-node-body {
  border-color: var(--accent-teal); box-shadow: 0 0 16px var(--accent-teal-soft);
}
.path-node.done .path-node-body { opacity: 0.75; }
.path-node-title { font-size: 0.88rem; font-weight: 650; color: var(--text-primary); margin-bottom: 4px; }
.path-node-desc { font-size: 0.76rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 8px; }
.path-node-meta { display: flex; align-items: center; gap: 8px; }
.pn-tag { font-size: 0.64rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.pn-time { font-size: 0.66rem; color: var(--text-muted); }
.path-connector {
  position: absolute; left: 17px; top: 38px;
  width: 2px; height: calc(100% - 38px);
  background: var(--border-light); transition: background 0.3s;
}
.path-connector.done { background: var(--accent); }

/* ====== Resource Grid ====== */
.resource-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.res-card {
  background: var(--bg-card); border: 1.5px solid var(--border-light);
  border-radius: 14px; padding: 18px; display: flex; gap: 14px;
  transition: all 0.3s; cursor: pointer;
}
.res-card:hover { border-color: var(--accent-light); box-shadow: 0 4px 20px var(--accent-soft); transform: translateY(-2px); }
.res-card-icon {
  width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.res-card-icon svg { width: 22px; height: 22px; stroke: var(--accent); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.res-card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.res-card-title { font-size: 0.84rem; font-weight: 650; color: var(--text-primary); margin-bottom: 4px; }
.res-card-desc { font-size: 0.72rem; color: var(--text-secondary); line-height: 1.5; flex: 1; margin-bottom: 8px; }
.res-card-footer { display: flex; align-items: center; justify-content: space-between; }
.res-type { font-size: 0.64rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.res-dur { font-size: 0.66rem; color: var(--text-muted); }

/* ====== Risk Warnings ====== */
.risk-list { display: flex; flex-direction: column; gap: 10px; }
.risk-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px 18px; border-radius: 12px;
  border: 1.5px solid var(--border-light); background: var(--bg-card);
  transition: all 0.25s;
}
.risk-item:hover { border-color: var(--accent-light); }
.risk-item.high { border-left: 3px solid var(--red); background: rgba(240,68,56,0.02); }
.risk-item.medium { border-left: 3px solid var(--accent-amber); background: rgba(245,158,11,0.02); }
.risk-level-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px;
}
.risk-item.high .risk-level-dot { background: var(--red); box-shadow: 0 0 8px rgba(240,68,56,0.4); }
.risk-item.medium .risk-level-dot { background: var(--accent-amber); box-shadow: 0 0 8px rgba(245,158,11,0.4); }
.risk-body { flex: 1; }
.risk-title { font-size: 0.84rem; font-weight: 650; color: var(--text-primary); margin-bottom: 4px; }
.risk-desc { font-size: 0.74rem; color: var(--text-secondary); line-height: 1.6; }
.risk-action { flex-shrink: 0; }
.risk-level-label {
  font-size: 0.66rem; font-weight: 650; padding: 4px 10px; border-radius: 6px;
}
.risk-item.high .risk-level-label { color: var(--red); background: rgba(240,68,56,0.06); border: 1px solid rgba(240,68,56,0.15); }
.risk-item.medium .risk-level-label { color: var(--accent-amber); background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.15); }

/* ====== Placeholder Pages ====== */
.placeholder-page {
  display: flex; align-items: center; justify-content: center; height: 100%;
}
.placeholder-card {
  text-align: center; padding: 48px;
}
.placeholder-icon {
  width: 72px; height: 72px; margin: 0 auto 20px;
  border-radius: 50%; background: var(--accent-soft);
  display: flex; align-items: center; justify-content: center;
}
.placeholder-icon svg { width: 32px; height: 32px; stroke: var(--accent); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.placeholder-card h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }
.placeholder-card p { font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 18px; }
.placeholder-tag {
  font-size: 0.72rem; padding: 5px 16px; border-radius: 10px;
  color: var(--accent); background: var(--accent-soft); border: 1px solid var(--accent-light);
}

/* ====== Responsive ====== */
@media (max-width: 1280px) {
  .diagnosis-grid { grid-template-columns: repeat(2, 1fr); }
  .resource-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 900px) {
  .app-shell { padding: 4px 6px; min-width: 0; }
  .diagnosis-grid { grid-template-columns: 1fr; }
  .resource-grid { grid-template-columns: 1fr; }
  .main-area { padding: 16px; }
}
</style>
