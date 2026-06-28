<template>
  <div class="derivation-page">
    <!-- 左侧：推导主题控制台与思路指引 -->
    <aside class="control-panel">
      <!-- 推导主题配置区 -->
      <section class="panel-section">
        <div class="section-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <span>推导主题</span>
        </div>

        <!-- 主题输入框 -->
        <div class="input-box">
          <input
            type="text"
            v-model="topicInput"
            placeholder="输入主题，如：牛顿第二定律、光合作用"
            @keyup.enter="handleGenerate"
          >
        </div>

        <!-- 模式切换：公式 / 概念 -->
        <div class="mode-toggle">
          <button
            class="mode-btn"
            :class="{ active: currentMode === 'formula' }"
            @click="currentMode = 'formula'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8h8"/><path d="M8 12h8"/><path d="M8 16h4"/>
            </svg>
            公式
          </button>
          <button
            class="mode-btn"
            :class="{ active: currentMode === 'concept' }"
            @click="currentMode = 'concept'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
            </svg>
            概念
          </button>
        </div>

        <!-- 触发推导链生成按钮 -->
        <button
          class="generate-btn"
          @click="handleGenerate"
          :disabled="isGenerating || !topicInput.trim()"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          <span>{{ isGenerating ? '生成中...' : '生成推导链' }}</span>
        </button>
      </section>

      <!-- 思路指引 · 公式推导 -->
      <section class="panel-section">
        <div class="section-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
          </svg>
          <span>思路指引 · {{ currentMode === 'formula' ? '公式推导' : '概念辨析' }}</span>
        </div>

        <div class="guide-content">
          <div v-if="chainState === 'idle'" class="guide-empty">
            输入主题并点击「生成推导链」开始
          </div>
          <div v-else class="guide-text">
            <p class="guide-title">🔬 {{ currentMode === 'formula' ? '动量定理演进法说明：' : '概念演进法说明：' }}</p>
            <p>{{ guideDescription }}</p>
            <p class="guide-hint">{{ guideHint }}</p>
          </div>
        </div>
      </section>

      <!-- 可追溯 & 批注 -->
      <section class="panel-section flex-1">
        <div class="section-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" x2="12" y1="17" y2="22"/><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"/>
          </svg>
          <span>可追溯 & 批注</span>
        </div>

        <div class="trace-content">
          <div v-if="chainState === 'idle'" class="trace-empty">
            暂无批注记录
          </div>
          <div v-else class="trace-note">
            <span class="trace-label">注释节点 [01]：</span>
            <p>{{ traceNote }}</p>
          </div>
        </div>
      </section>
    </aside>

    <!-- 右侧：公式推导链生成画布 -->
    <main class="canvas-area">
      <!-- 画布头部控制 -->
      <header class="canvas-header">
        <div class="status-indicator">
          <div class="status-dot" :class="chainState === 'idle' ? 'waiting' : 'active'"></div>
          <span class="status-text">
            {{ chainState === 'idle' ? '等待生成' : '公式推导树生成就绪' }}
          </span>
        </div>
        <button class="reset-btn" @click="resetCanvas" title="重置画布">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>
          </svg>
        </button>
      </header>

      <!-- 核心推导树大画布 -->
      <div class="canvas-body">
        <!-- 状态一：Idle - 等待输入 -->
        <div v-if="chainState === 'idle'" class="empty-state">
          <div class="empty-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>
            </svg>
          </div>
          <h3 class="empty-title">公式推导链</h3>
          <p class="empty-desc">在左侧输入主题，AI 将为你生成多模态、可视化的高质量阶梯公式推导链条。</p>
        </div>

        <!-- 状态二：Success - 渲染推导树 -->
        <div v-else class="derivation-tree">
          <div
            v-for="(step, idx) in derivationSteps"
            :key="idx"
            class="tree-node"
            :class="{ 'last-node': idx === derivationSteps.length - 1 }"
          >
            <div class="node-connector">
              <div class="node-dot"></div>
              <div v-if="idx < derivationSteps.length - 1" class="node-line"></div>
            </div>
            <div class="node-card">
              <div class="node-header">
                <span class="node-step">STEP {{ String(idx + 1).padStart(2, '0') }} · {{ step.subtitle }}</span>
                <span class="node-badge" :class="step.badgeType">{{ step.badge }}</span>
              </div>
              <h4 class="node-title">{{ step.title }}</h4>
              <div class="formula-box">
                <code>{{ step.formula }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部 Agent 追问输入条 -->
      <div class="chat-input-bar">
        <div class="chat-input-wrapper">
          <input
            type="text"
            v-model="chatInput"
            placeholder="向 Agent 提问，例如：这个公式的物理边界与物理意义是什么？"
            @keyup.enter="handleSend"
          >
          <button class="send-btn" @click="handleSend">
            <span>发送</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m22 2-7 20-4-9-9-4Z"/><path d="m22 2-11 11"/>
            </svg>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useDerivation } from '../../composables/useDerivation.js'

const router = useRouter()
const { user } = useAuth()
const { connected, connect, getChatId } = useGateway()
const {
  isGenerating,
  chatMessages,
  getSteps,
  generateDerivation,
  askQuestion,
  subscribeToChat,
  clearChat,
} = useDerivation()

// State
const currentMode = ref('formula')
const topicInput = ref('牛顿第二定律')
const chatInput = ref('')
const chainState = ref('idle')
let unsubChat = null

// Computed
const currentSteps = computed(() => getSteps(currentMode.value))

const guideDescription = computed(() => {
  if (currentMode.value === 'formula') {
    return '我们将从经典力学的动量积分守恒定义开始：系统所受合外力等于动量对时间的变化率。'
  }
  return '我们将从基础概念定义开始，逐步展开概念之间的逻辑关系和演化路径。'
})

const guideHint = computed(() => {
  if (currentMode.value === 'formula') {
    return '后续步骤我们将通过对质量 $m$ 采取常数约束，分离出经典的速度变化率导数，最终导向 $F = ma$。'
  }
  return '后续步骤将通过对比分析和实例验证，帮助你深入理解概念的本质和应用场景。'
})

const traceNote = computed(() => {
  if (currentMode.value === 'formula') {
    return '微分运算中质量 dm/dt=0 是该推导成立的前置约束，若在相对论高速场景下，该步骤需重构为多维洛伦兹变换。'
  }
  return '概念辨析中的边界条件定义，是理解该概念适用范围的关键前提。'
})

// Demo derivation steps
const derivationSteps = ref([
  {
    subtitle: '动量变化定义',
    title: '物体受合外力等于其动量变化的时间积分率',
    formula: 'F = d(p) / dt',
    badge: '首要条件就绪',
    badgeType: 'success',
  },
  {
    subtitle: '物理量特征展开',
    title: '展开动量矢量分量公式',
    formula: 'F = d(m * v) / dt',
    badge: '状态特征量: p = m * v',
    badgeType: 'info',
  },
  {
    subtitle: '微分常数拆除',
    title: '将不变质量提至微分算子前方，最终导向 F = ma',
    formula: 'F = m * (dv / dt) = m * a',
    badge: '约束质量 m = 常数',
    badgeType: 'warning',
  },
])

// Lifecycle
onMounted(async () => {
  // Apply saved theme
  const savedTheme = localStorage.getItem('nanobot-theme')
  if (savedTheme && ['white', 'dark', 'green'].includes(savedTheme)) {
    document.body.classList.remove('dark', 'green', 'white')
    if (savedTheme !== 'white') {
      document.body.classList.add(savedTheme)
    }
  }

  if (!connected.value && user.value) {
    try {
      await connect({ role: user.value.role || 'student', userId: user.value.id || user.value.userId })
    } catch { /* will show connection error */ }
  }
  const cid = getChatId()
  if (cid) {
    unsubChat = subscribeToChat(cid)
  }
})

onUnmounted(() => {
  if (unsubChat) unsubChat()
})

// Actions
function handleGenerate() {
  const topic = topicInput.value.trim()
  if (!topic || isGenerating.value) return

  clearChat()
  chainState.value = 'success'

  // Call the actual generation
  generateDerivation(topic)
}

function resetCanvas() {
  chainState.value = 'idle'
}

function handleSend() {
  const q = chatInput.value.trim()
  if (!q) return
  askQuestion(q, currentMode.value)
  chatInput.value = ''
}
</script>

<style scoped>
/* ===== 页面布局 ===== */
.derivation-page {
  display: grid;
  grid-template-columns: 1fr 2fr;
  height: 100%;
  background: #ffffff;
  overflow: hidden;
}

/* ===== 左侧控制面板 ===== */
.control-panel {
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.panel-section {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #121212;
}

.section-header svg {
  color: #999;
}

/* 输入框 */
.input-box {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 10px 12px;
  background: #ffffff;
  transition: border-color 0.15s ease;
}

.input-box:focus-within {
  border-color: #121212;
}

.input-box input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 13px;
  color: #121212;
  background: transparent;
}

.input-box input::placeholder {
  color: #ccc;
}

/* 模式切换 */
.mode-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: #f4f4f4;
  padding: 4px;
  border-radius: 10px;
}

.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #999;
  font-size: 11px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: #121212;
}

.mode-btn.active {
  background: #121212;
  color: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 生成按钮 */
.generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 20px;
  background: #121212;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.generate-btn:hover {
  background: #333;
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 思路指引 */
.guide-content {
  font-size: 12px;
  line-height: 1.6;
  color: #666;
  font-family: 'Noto Serif SC', serif;
}

.guide-empty {
  text-align: center;
  color: #999;
  padding: 24px 0;
}

.guide-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.guide-title {
  font-weight: 600;
  color: #121212;
  padding-bottom: 8px;
  border-bottom: 1px solid #f4f4f4;
}

.guide-hint {
  color: #999;
  font-size: 11px;
}

/* 可追溯批注 */
.trace-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.trace-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #f0f0f0;
  border-radius: 12px;
  color: #999;
  font-size: 12px;
  font-family: 'Noto Serif SC', serif;
}

.trace-note {
  padding-left: 12px;
  border-left: 2px solid #121212;
  font-size: 12px;
  line-height: 1.6;
  color: #4a534c;
}

.trace-label {
  font-weight: 600;
  color: #121212;
}

/* ===== 右侧画布区域 ===== */
.canvas-area {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-header {
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: #ffffff;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.waiting {
  background: #fbbf24;
}

.status-dot.active {
  background: #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(0.95); }
}

.status-text {
  font-size: 11px;
  font-family: monospace;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reset-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #f0f0f0;
  background: #ffffff;
  color: #999;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.reset-btn:hover {
  background: #f8f9f8;
  color: #121212;
  border-color: #e0e0e0;
}

/* 画布主体 */
.canvas-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: linear-gradient(to bottom, #fbfdfb, #fafbfa);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  animation: pulse-subtle 3s infinite ease-in-out;
}

@keyframes pulse-subtle {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.9; transform: scale(0.99); }
}

.empty-icon {
  width: 48px;
  height: 48px;
  background: #f4f4f4;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.empty-title {
  font-size: 14px;
  font-weight: 600;
  color: #121212;
}

.empty-desc {
  font-size: 12px;
  color: #999;
  text-align: center;
  max-width: 280px;
  line-height: 1.5;
}

/* 推导树 */
.derivation-tree {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-width: 640px;
  margin: 0 auto;
  width: 100%;
}

.tree-node {
  display: flex;
  gap: 16px;
  position: relative;
}

.node-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
}

.node-dot {
  width: 12px;
  height: 12px;
  background: #121212;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  box-shadow: 0 0 0 4px #f4f4f4;
}

.node-line {
  width: 2px;
  flex: 1;
  background: #e0e0e0;
  border-style: dashed;
  margin-top: -2px;
  margin-bottom: -2px;
}

.tree-node:not(.last-node) .node-connector {
  padding-bottom: 16px;
}

.node-card {
  flex: 1;
  background: #ffffff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
  transition: border-color 0.15s ease;
}

.node-card:hover {
  border-color: #e0e0e0;
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.node-step {
  font-size: 10px;
  font-family: monospace;
  color: #999;
}

.node-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid;
}

.node-badge.success {
  color: #059669;
  background: #ecfdf5;
  border-color: #a7f3d0;
}

.node-badge.info {
  color: #6b7280;
  background: #f9fafb;
  border-color: #e5e7eb;
}

.node-badge.warning {
  color: #d97706;
  background: #fffbeb;
  border-color: #fde68a;
}

.node-title {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
  margin-bottom: 10px;
  font-family: 'Noto Serif SC', serif;
  line-height: 1.4;
}

.formula-box {
  background: #fcfdfc;
  border: 1px solid #f5f8f5;
  border-radius: 8px;
  padding: 10px 12px;
}

.formula-box code {
  font-family: monospace;
  font-size: 14px;
  color: #121212;
  letter-spacing: 0.5px;
}

/* 底部输入条 */
.chat-input-bar {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
  background: #ffffff;
}

.chat-input-wrapper {
  display: flex;
  align-items: center;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 8px 12px;
  background: #ffffff;
  transition: border-color 0.15s ease;
}

.chat-input-wrapper:focus-within {
  border-color: #121212;
}

.chat-input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 13px;
  color: #121212;
  background: transparent;
}

.chat-input-wrapper input::placeholder {
  color: #ccc;
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #121212;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.send-btn:hover {
  background: #333;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .derivation-page {
    grid-template-columns: 1fr;
  }

  .control-panel {
    display: none;
  }
}

/* ===== 绿色主题 ===== */
body.green .derivation-page { background: #f7f8f7; }
body.green .control-panel { border-right-color: #dee2de; }
body.green .panel-section { border-bottom-color: #dee2de; }
body.green .section-header { color: #2c332e; }
body.green .section-header svg { color: #526e5a; }
body.green .input-box { border-color: #dee2de; background: #f7f8f7; }
body.green .input-box:focus-within { border-color: #526e5a; }
body.green .input-box input { color: #2c332e; }
body.green .input-box input::placeholder { color: #8fa091; }
body.green .mode-toggle { background: #edf0ed; }
body.green .mode-btn { color: #8fa091; }
body.green .mode-btn:hover { color: #2c332e; }
body.green .mode-btn.active { background: #526e5a; color: #ffffff; }
body.green .generate-btn { background: #526e5a; }
body.green .generate-btn:hover { background: #3d5243; }
body.green .guide-content { color: #556056; }
body.green .guide-empty { color: #8fa091; }
body.green .guide-title { color: #2c332e; border-bottom-color: #edf0ed; }
body.green .guide-hint { color: #8fa091; }
body.green .trace-empty { border-color: #dee2de; color: #8fa091; }
body.green .trace-note { border-left-color: #526e5a; color: #556056; }
body.green .trace-label { color: #2c332e; }
body.green .canvas-header { border-bottom-color: #dee2de; background: #f7f8f7; }
body.green .status-text { color: #8fa091; }
body.green .reset-btn { border-color: #dee2de; background: #f7f8f7; color: #8fa091; }
body.green .reset-btn:hover { background: #edf0ed; color: #2c332e; border-color: #526e5a; }
body.green .canvas-body { background: linear-gradient(to bottom, #f3f6f3, #f7f8f7); }
body.green .empty-icon { background: #edf0ed; color: #526e5a; }
body.green .empty-title { color: #2c332e; }
body.green .empty-desc { color: #8fa091; }
body.green .node-dot { background: #526e5a; box-shadow: 0 0 0 4px #edf0ed; }
body.green .node-line { background: #dee2de; }
body.green .node-card { background: #f7f8f7; border-color: #dee2de; }
body.green .node-card:hover { border-color: #526e5a; }
body.green .node-step { color: #8fa091; }
body.green .node-badge.success { color: #526e5a; background: #edf0ed; border-color: #dbe1db; }
body.green .node-badge.info { color: #556056; background: #edf0ed; border-color: #dee2de; }
body.green .node-badge.warning { color: #d97706; background: #fffbeb; border-color: #fde68a; }
body.green .node-title { color: #2c332e; }
body.green .formula-box { background: #f3f6f3; border-color: #dee2de; }
body.green .formula-box code { color: #2c332e; }
body.green .chat-input-bar { border-top-color: #dee2de; background: #f7f8f7; }
body.green .chat-input-wrapper { border-color: #dee2de; background: #f7f8f7; }
body.green .chat-input-wrapper:focus-within { border-color: #526e5a; }
body.green .chat-input-wrapper input { color: #2c332e; }
body.green .chat-input-wrapper input::placeholder { color: #8fa091; }
body.green .send-btn { background: #526e5a; }
body.green .send-btn:hover { background: #3d5243; }

/* ===== 暗色主题 ===== */
body.dark .derivation-page { background: #121212; }
body.dark .control-panel { border-right-color: #2d2d2d; }
body.dark .panel-section { border-bottom-color: #2d2d2d; }
body.dark .section-header { color: #e5e5e5; }
body.dark .section-header svg { color: #999; }
body.dark .input-box { border-color: #333; background: #1a1a1a; }
body.dark .input-box:focus-within { border-color: #fff; }
body.dark .input-box input { color: #e5e5e5; }
body.dark .input-box input::placeholder { color: #777; }
body.dark .mode-toggle { background: #242424; }
body.dark .mode-btn { color: #777; }
body.dark .mode-btn:hover { color: #e5e5e5; }
body.dark .mode-btn.active { background: #fff; color: #121212; }
body.dark .generate-btn { background: #fff; color: #121212; }
body.dark .generate-btn:hover { background: #e5e5e5; }
body.dark .guide-content { color: #aaa; }
body.dark .guide-empty { color: #777; }
body.dark .guide-title { color: #e5e5e5; border-bottom-color: #333; }
body.dark .guide-hint { color: #777; }
body.dark .trace-empty { border-color: #333; color: #777; }
body.dark .trace-note { border-left-color: #fff; color: #aaa; }
body.dark .trace-label { color: #e5e5e5; }
body.dark .canvas-header { border-bottom-color: #2d2d2d; background: #121212; }
body.dark .status-text { color: #777; }
body.dark .reset-btn { border-color: #333; background: #1a1a1a; color: #777; }
body.dark .reset-btn:hover { background: #242424; color: #e5e5e5; border-color: #fff; }
body.dark .canvas-body { background: linear-gradient(to bottom, #0f0f0f, #121212); }
body.dark .empty-icon { background: #242424; color: #777; }
body.dark .empty-title { color: #e5e5e5; }
body.dark .empty-desc { color: #777; }
body.dark .node-dot { background: #fff; box-shadow: 0 0 0 4px #242424; }
body.dark .node-line { background: #333; }
body.dark .node-card { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .node-card:hover { border-color: #fff; }
body.dark .node-step { color: #777; }
body.dark .node-badge.success { color: #4ade80; background: #0f1f0f; border-color: #166534; }
body.dark .node-badge.info { color: #999; background: #1a1a1a; border-color: #333; }
body.dark .node-badge.warning { color: #fbbf24; background: #1f1a0f; border-color: #92400e; }
body.dark .node-title { color: #e5e5e5; }
body.dark .formula-box { background: #0f0f0f; border-color: #2d2d2d; }
body.dark .formula-box code { color: #e5e5e5; }
body.dark .chat-input-bar { border-top-color: #2d2d2d; background: #121212; }
body.dark .chat-input-wrapper { border-color: #333; background: #1a1a1a; }
body.dark .chat-input-wrapper:focus-within { border-color: #fff; }
body.dark .chat-input-wrapper input { color: #e5e5e5; }
body.dark .chat-input-wrapper input::placeholder { color: #777; }
body.dark .send-btn { background: #fff; color: #121212; }
body.dark .send-btn:hover { background: #e5e5e5; }
</style>
