<template>
<div class="app-shell">
<StudentNav active-tab="formula-derivation" />

  <div class="main-split">
    <!-- LEFT COLUMN -->
    <div class="col-left">
      <!-- TOPIC INPUT PANEL -->
      <div class="panel" style="flex:0 0 auto;min-height:auto;">
        <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
        <div class="panel-hd"><i></i><span class="panel-title">🔍 推导主题</span></div>
        <div class="panel-body" style="gap:8px;">
          <input
            class="topic-input"
            v-model="topicInput"
            placeholder="输入主题，如：光合作用、牛顿第二定律"
            @keypress.enter.prevent="handleGenerate"
          />
          <div class="mode-chips" style="margin:0;">
            <button
              v-for="m in modes"
              :key="m.key"
              class="mode-chip"
              :class="{ active: currentMode === m.key }"
              @click="currentMode = m.key"
            ><span class="chip-icon">{{ m.icon }}</span>{{ m.label }}</button>
          </div>
          <button
            class="generate-btn"
            :disabled="isGenerating || !topicInput.trim()"
            @click="handleGenerate"
          >
            <span v-if="isGenerating" class="spinner"></span>
            {{ isGenerating ? '生成中...' : '✦ 生成推导链' }}
          </button>
        </div>
      </div>

      <!-- STEP LIST PANEL -->
      <div class="panel">
        <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
        <div class="panel-hd"><i></i><span class="panel-title">{{ stepPanelTitle }}</span></div>
        <div class="panel-body">
          <div v-if="!currentSteps.length && !isGenerating" class="empty-hint">
            输入主题并点击「生成推导链」开始
          </div>
          <div v-else class="step-list">
            <div
              v-for="(step, idx) in currentSteps"
              :key="idx"
              class="step-item"
              :class="{ active: !isOverviewMode && idx === currentIdx }"
              @click="selectStep(idx)"
            >
              <div class="step-num">{{ idx + 1 }}</div>
              <div>
                <div class="step-name">{{ step.name }}</div>
                <div class="step-desc">{{ step.shortDesc }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
        <div class="panel-hd"><i></i><span class="panel-title">📌 可追溯 & 批注</span></div>
        <div class="panel-body">
          <div class="trace-panel">{{ currentStep?.trace || '' }}</div>
          <div style="font-size:0.66rem;color:var(--text-muted);margin-top:6px;">{{ currentStep?.extra || '' }}</div>
        </div>
      </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="panel" style="display:flex;flex-direction:column;">
      <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
      <div class="panel-hd">
        <i></i>
        <span class="panel-title">{{ isOverviewMode ? '📋 推导全貌 · 完整链' : (currentStep?.name || '等待生成') }}</span>
        <button class="view-toggle-btn" :class="{ rotated: isOverviewMode }" title="切换至推导全貌" @click="isOverviewMode = !isOverviewMode; afterRender()">
          <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/><polyline points="16,2 12,6 8,2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8,22 12,18 16,22" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <!-- LOADING STATE -->
      <div v-if="isGenerating" class="panel-body" style="flex:1;overflow-y:auto;align-items:center;justify-content:center;">
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">AI 正在生成推导链...</div>
          <div class="loading-hint">主题：{{ topicInput }}</div>
        </div>
      </div>

      <!-- EMPTY STATE -->
      <div v-else-if="!currentSteps.length" class="panel-body" style="flex:1;overflow-y:auto;align-items:center;justify-content:center;">
        <div class="empty-state">
          <div class="empty-icon">📐</div>
          <div class="empty-title">公式推导链</div>
          <div class="empty-desc">在左侧输入主题，AI 将为你生成完整的推导链</div>
        </div>
      </div>

      <!-- STEP DETAIL -->
      <template v-else>
        <div v-if="!isOverviewMode" class="panel-body" style="flex:1;overflow-y:auto;">
          <div style="display:flex;flex-direction:column;gap:8px;">
            <template v-for="(sec, si) in currentStep?.sections || []" :key="si">
              <div v-if="sec.kind==='text'" class="explanatory-text">{{ sec.value }}</div>
              <div v-else-if="sec.kind==='formula'" class="formula-block">
                <div class="formula-wrapper">
                  <div class="formula-content" v-html="renderFormula(sec.value)"></div>
                  <div v-if="sec.tag" class="formula-tag">{{ sec.tag }}</div>
                </div>
              </div>
              <div v-else-if="sec.kind==='insight'" class="academic-insight">💡 {{ sec.value }}</div>
              <div v-else-if="sec.kind==='code'" class="code-block" v-html="renderCodeLines(sec.code, sec.highlight)"></div>
              <div v-if="sec.kind==='code' && sec.annotation" class="annotation-bubble">📝 {{ sec.annotation }}</div>
              <div v-else-if="sec.kind==='concept-grid'" class="concept-grid">
                <div v-for="(card, ci) in sec.cards" :key="ci" class="concept-card">
                  <span class="concept-badge">{{ card.badge }}</span>
                  <h4>{{ card.title }}</h4>
                  <p>{{ card.desc }}</p>
                  <div style="margin-top:8px;font-size:0.64rem;">
                    <span style="color:#0d9488;">{{ card.pro }}</span><br>
                    <span style="color:#ef4444;">{{ card.con }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- OVERVIEW MODE -->
        <div v-else class="panel-body" style="flex:1;overflow-y:auto;" ref="overviewEl">
          <div style="display:flex;flex-direction:column;gap:0;">
            <template v-for="(step, idx) in currentSteps" :key="'ov-'+idx">
              <div class="overview-step-block" :id="'overview-step-'+idx">
                <div class="overview-step-header">
                  <div class="overview-step-num-badge">{{ idx + 1 }}</div>
                  <div>
                    <div class="overview-step-title">{{ step.name }}</div>
                    <div class="overview-step-shortdesc">{{ step.shortDesc }}</div>
                  </div>
                </div>
                <template v-for="(sec, si) in step.sections" :key="si">
                  <div v-if="sec.kind==='text'" class="explanatory-text">{{ sec.value }}</div>
                  <div v-else-if="sec.kind==='formula'" class="formula-block">
                    <div class="formula-wrapper">
                      <div class="formula-content" v-html="renderFormula(sec.value)"></div>
                      <div v-if="sec.tag" class="formula-tag">{{ sec.tag }}</div>
                    </div>
                  </div>
                  <div v-else-if="sec.kind==='insight'" class="academic-insight">💡 {{ sec.value }}</div>
                  <div v-else-if="sec.kind==='code'" class="code-block" v-html="renderCodeLines(sec.code, sec.highlight)"></div>
                  <div v-if="sec.kind==='code' && sec.annotation" class="annotation-bubble">📝 {{ sec.annotation }}</div>
                  <div v-else-if="sec.kind==='concept-grid'" class="concept-grid">
                    <div v-for="(card, ci) in sec.cards" :key="ci" class="concept-card">
                      <span class="concept-badge">{{ card.badge }}</span>
                      <h4>{{ card.title }}</h4>
                      <p>{{ card.desc }}</p>
                      <div style="margin-top:8px;font-size:0.64rem;">
                        <span style="color:#0d9488;">{{ card.pro }}</span><br>
                        <span style="color:#ef4444;">{{ card.con }}</span>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
              <template v-if="idx < currentSteps.length - 1">
                <div class="overview-connector">
                  <svg viewBox="0 0 24 24"><line x1="12" y1="4" x2="12" y2="16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><polyline points="7,11 12,17 17,11" stroke="currentColor" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </div>
                <div class="overview-divider-line"></div>
              </template>
            </template>
          </div>
        </div>
      </template>

      <!-- CHAT AREA -->
      <div class="chat-area">
        <div class="chat-input-group">
          <textarea class="chat-input" v-model="chatInput" rows="1" placeholder="向 Agent 提问，例如：这个公式的物理意义是什么？" @keypress.enter.exact.prevent="handleSend"></textarea>
          <button class="chat-send" @click="handleSend">发送 ✦</button>
        </div>
        <div class="chat-history" ref="chatHistoryEl">
          <div v-for="(msg, mi) in chatMessages" :key="mi" class="message-bubble" :style="{ backgroundColor: msg.isUser ? 'var(--accent-light)' : 'var(--accent-soft)', borderLeftColor: 'var(--accent)' }">
            <strong>{{ msg.isUser ? '👤 用户' : '🤖 Agent' }}</strong><br>{{ msg.text }}<span v-if="msg.streaming" class="typing-cursor">▊</span>
          </div>
        </div>
      </div>

      <!-- STEP BUTTONS -->
      <div class="btn-group" :class="{ hidden: isOverviewMode || !currentSteps.length }">
        <button class="btn" :disabled="currentIdx === 0" @click="currentIdx--">← 上一步</button>
        <button class="btn btn-primary" :disabled="currentIdx >= currentSteps.length - 1" @click="currentIdx++">下一步 →</button>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import katex from 'katex'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'
import { useDerivation } from '../../composables/useDerivation.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout, user } = useAuth()
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

function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}

// ---- MODES ----
const modes = [
  { key: 'formula', icon: '📐', label: '公式' },
  { key: 'concept', icon: '📖', label: '概念' },
]

// ---- STATE ----
const currentMode = ref('formula')
const currentIdx = ref(0)
const isOverviewMode = ref(false)
const chatInput = ref('')
const topicInput = ref('')
const overviewEl = ref(null)
let unsubChat = null

const currentSteps = computed(() => getSteps(currentMode.value))
const currentStep = computed(() => currentSteps.value[currentIdx.value] || null)
const stepPanelTitle = computed(() => {
  const map = { formula: '🧭 思路指引 · 公式推导', concept: '🧭 思路指引 · 概念辨析' }
  return map[currentMode.value] || map.formula
})

// ---- LIFECYCLE ----
onMounted(async () => {
  // Ensure gateway is connected
  if (!connected.value && user.value) {
    try {
      await connect({ role: user.value.role || 'student', userId: user.value.id || user.value.userId })
    } catch { /* will show connection error */ }
  }
  // Subscribe to chat for streaming responses
  const cid = getChatId()
  if (cid) {
    unsubChat = subscribeToChat(cid)
  }
})

onUnmounted(() => {
  if (unsubChat) unsubChat()
})

// ---- HELPERS ----
function renderFormula(value) {
  if (!value) return ''
  try {
    return value.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex) => {
      return katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })
    }).replace(/\$([^$]+)\$/g, (_, latex) => {
      return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false })
    })
  } catch { return value }
}

function renderCodeLines(code, highlights = []) {
  if (!code) return ''
  return code.split('\n').map((line, i) => {
    const escaped = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    if (highlights && highlights.includes(i + 1)) {
      return `<span class="code-line-highlight">${escaped}</span>`
    }
    return escaped
  }).join('\n')
}

function afterRender() {
  if (isOverviewMode.value) {
    nextTick(() => { if (overviewEl.value) overviewEl.value.scrollTop = 0 })
  }
}

// ---- ACTIONS ----
async function handleGenerate() {
  const topic = topicInput.value.trim()
  if (!topic || isGenerating.value) return

  currentIdx.value = 0
  isOverviewMode.value = false
  clearChat()

  try {
    await generateDerivation(topic)
  } catch { /* error handled in composable */ }
}

function selectStep(idx) {
  if (isOverviewMode.value) {
    nextTick(() => {
      const target = document.getElementById('overview-step-' + idx)
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
      currentIdx.value = idx
    })
  } else {
    currentIdx.value = idx
  }
}

function handleSend() {
  const q = chatInput.value.trim()
  if (!q) return
  askQuestion(q, currentMode.value)
  chatInput.value = ''
}

watch(currentMode, () => {
  currentIdx.value = 0
  isOverviewMode.value = false
})
</script>

<style>
:root {
  --bg-root: #f8f6f1;
  --bg-card: #ffffff;
  --bg-nav: #ffffff;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.3);
  --accent-soft: #eef4ff;
  --accent-glow: rgba(91,141,239,0.15);
  --accent-deep: #4a7de0;
  --border-light: #e8e4db;
  --border-medium: #e0dcd5;
  --border-active: #5b8def;
  --text-primary: #2c2c2c;
  --text-secondary: #666666;
  --text-muted: #999999;
  --divider: #e8e4db;
  --formula-black-border: #1e1e28;
  --formula-card-bg: #ffffff;
  --overview-step-bg: #ffffff;
  --insight-bg: #eef4ff;
  --insight-border: #5b8def;
  --trace-bg: #ffffff;
  --code-bg: #1a1b26;
  --code-text: #c0caf5;
  --code-border: #2a2740;
  --concept-card-bg: #ffffff;
  --concept-card-border: #e0dcd5;
}
body.dark {
  --bg-root: #12121a;
  --bg-card: #1e1e2e;
  --bg-nav: #1e1e2e;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.3);
  --accent-soft: rgba(91,141,239,0.1);
  --accent-glow: rgba(91,141,239,0.2);
  --accent-deep: #4a7de0;
  --border-light: #333333;
  --border-medium: #444444;
  --border-active: #5b8def;
  --text-primary: #e0e0e0;
  --text-secondary: #aaaaaa;
  --text-muted: #777777;
  --divider: #333333;
  --formula-black-border: #5a5670;
  --formula-card-bg: #1e1e2e;
  --overview-step-bg: #1e1e2e;
  --insight-bg: rgba(91,141,239,0.1);
  --insight-border: #5b8def;
  --trace-bg: #1e1e2e;
  --code-bg: #0d0c1a;
  --code-text: #c0caf5;
  --code-border: #2a2740;
  --concept-card-bg: #1e1e2e;
  --concept-card-border: #444444;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  color:var(--text-primary); background:var(--bg-root); height:100vh; overflow:hidden;
  transition:background 0.4s,color 0.4s; letter-spacing:0.01em;
}
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:0; }
</style>
<style scoped>
.app-shell { display:flex; flex-direction:column; height:100vh; width:100%; max-width:1640px; margin:0 auto; padding:8px 14px; gap:8px; }

.top-nav {
  flex-shrink:0; height:52px; background:var(--bg-nav);
  border:1px solid var(--border-light);
  display:flex; align-items:center; justify-content:space-between;
  padding:0 28px; border-radius:0;
}
.nav-left { display:flex; align-items:center; gap:16px; }
.nav-logo {
  font-family:'Playfair Display','Georgia',serif; font-style:italic;
  font-size:1.35rem; font-weight:700; color:var(--accent);
  display:flex; align-items:center; gap:8px;
}
.nav-logo .dot { width:7px; height:7px; background:var(--accent); }
.nav-center { display:flex; align-items:center; gap:4px; }
.nav-tab {
  padding:6px 14px; border-radius:14px; font-size:0.8rem; font-weight:500;
  color:var(--text-secondary); cursor:pointer; transition:all 0.2s;
  border:1.5px solid transparent;
}
.nav-tab:hover { color:var(--text-primary); background:var(--accent-soft); }
.nav-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.nav-right { display:flex; gap:10px; align-items:center; }
.nav-icon {
  width:32px; height:32px; border:1.5px solid var(--border-medium); background:transparent;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  color:var(--text-secondary); transition:0.22s;
}
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; }
.nav-icon:hover { color:var(--accent); border-color:var(--border-active); box-shadow:0 0 16px var(--accent-glow); }
.nav-avatar {
  width:34px; height:34px; background:linear-gradient(135deg,#5a4cd8,#8B70FF);
  display:flex; align-items:center; justify-content:center; color:#fff;
  font-weight:600; font-size:0.72rem; cursor:pointer; box-shadow:0 0 16px var(--accent-glow);
}

.main-split { flex:1; min-height:0; display:grid; grid-template-columns:300px 1fr; gap:10px; }
.col-left { display:flex; flex-direction:column; gap:10px; height:100%; min-height:0; }

.panel {
  background:var(--bg-card);
  border:1px solid var(--border-light); border-radius:0;
  position:relative; overflow:hidden;
  display:flex; flex-direction:column; transition:all 0.28s; flex:1; min-height:0;
}
.panel:hover { border-color:var(--border-active); }
.panel-strip { display:none; }

.panel-hd {
  flex-shrink:0; display:flex; align-items:center; gap:8px;
  padding:10px 16px; border-bottom:1px solid var(--divider); position:relative; z-index:2;
}
.panel-hd i { width:4px; height:20px; background:linear-gradient(180deg,var(--accent),var(--accent-deep)); box-shadow:0 0 8px var(--accent-glow); flex-shrink:0; }
.panel-title { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; flex:1; min-width:0; }
.panel-body { flex:1; min-height:0; padding:14px 16px; overflow-y:auto; display:flex; flex-direction:column; gap:10px; position:relative; z-index:2; scroll-behavior:smooth; }

/* Topic input */
.topic-input {
  width:100%; padding:8px 12px; border:1.5px solid var(--border-light);
  background:var(--bg-card); color:var(--text-primary); font-family:inherit;
  font-size:0.78rem; outline:none; transition:border-color 0.2s;
}
.topic-input:focus { border-color:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.topic-input::placeholder { color:var(--text-muted); }

/* Generate button */
.generate-btn {
  width:100%; padding:8px 16px; border:none; background:var(--accent);
  color:#fff; font-family:inherit; font-size:0.78rem; font-weight:600;
  cursor:pointer; transition:all 0.2s; display:flex; align-items:center;
  justify-content:center; gap:6px;
}
.generate-btn:hover:not(:disabled) { box-shadow:0 0 20px var(--accent-glow); }
.generate-btn:disabled { opacity:0.5; cursor:not-allowed; }

/* Spinner */
.spinner {
  width:14px; height:14px; border:2px solid rgba(255,255,255,0.3);
  border-top-color:#fff; border-radius:50%; animation:spin 0.6s linear infinite;
}
@keyframes spin { to { transform:rotate(360deg); } }

/* Empty hint */
.empty-hint {
  font-size:0.72rem; color:var(--text-muted); text-align:center;
  padding:20px 10px; line-height:1.6;
}

/* Loading state */
.loading-state { display:flex; flex-direction:column; align-items:center; gap:12px; }
.loading-spinner {
  width:40px; height:40px; border:3px solid var(--accent-light);
  border-top-color:var(--accent); border-radius:50%; animation:spin 0.8s linear infinite;
}
.loading-text { font-size:0.82rem; font-weight:600; color:var(--accent); }
.loading-hint { font-size:0.68rem; color:var(--text-muted); }

/* Empty state */
.empty-state { display:flex; flex-direction:column; align-items:center; gap:8px; }
.empty-icon { font-size:2.5rem; }
.empty-title { font-size:1rem; font-weight:700; color:var(--text-primary); }
.empty-desc { font-size:0.72rem; color:var(--text-muted); text-align:center; max-width:280px; }

/* Step list */
.step-list { display:flex; flex-direction:column; gap:8px; }
.step-item { display:flex; align-items:center; gap:14px; padding:10px 14px; background:#ffffff; border:1px solid var(--border-light); cursor:pointer; transition:0.2s; }
.step-item:hover { border-color:var(--accent-light); }
.step-item.active { border-color:var(--accent); background:#ffffff; box-shadow:inset 0 0 0 1px var(--accent-glow),0 0 14px var(--accent-glow); }
.step-num { width:30px; height:30px; background:var(--bg-nav); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem; color:var(--accent); border:1.5px solid var(--accent); flex-shrink:0; }
.step-item.active .step-num { background:var(--accent); color:#fff; border-color:var(--accent); }
.step-name { font-size:0.74rem; font-weight:600; line-height:1.3; }
.step-desc { font-size:0.60rem; color:var(--text-muted); margin-top:2px; }

.trace-panel {
  background:var(--trace-bg); padding:14px; border-left:4px solid var(--accent);
  font-size:0.7rem; line-height:1.5; color:var(--text-secondary);
}

/* Formula display */
.formula-block { margin:0.5rem 0; }
.formula-wrapper {
  display:flex; align-items:baseline; justify-content:space-between; gap:18px;
  background:var(--formula-card-bg); padding:1rem 1.3rem;
  border:2px solid var(--accent-light);
  box-shadow:2px 2px 0 rgba(0,0,0,0.04); transition:0.2s;
}
.formula-wrapper:hover { border-color:var(--accent); box-shadow:0 0 16px var(--accent-glow),2px 2px 0 rgba(0,0,0,0.06); }
.formula-content { flex:1; overflow-x:auto; text-align:center; }
.formula-content .katex { font-size:0.98rem; }
.formula-tag {
  font-family:'Fira Code',monospace; font-size:0.68rem; font-weight:600;
  color:var(--accent); background:var(--accent-soft); padding:3px 12px;
  border:1px solid var(--accent-light); white-space:nowrap;
}

/* Code display */
.code-block { background:var(--code-bg); color:var(--code-text); padding:12px 16px; border-radius:4px; font-family:'JetBrains Mono','Cascadia Code',monospace; font-size:0.70rem; line-height:1.55; overflow-x:auto; white-space:pre; border:1px solid var(--code-border); }
.code-line-highlight { background:rgba(139,112,255,0.25); display:block; margin:0 -16px; padding:0 16px; border-left:3px solid #8B70FF; }

.annotation-bubble { margin-top:6px; padding:5px 10px; font-size:0.64rem; color:var(--text-secondary); background:var(--insight-bg); border-left:3px solid var(--insight-border); border-radius:0 4px 4px 0; }

/* Explanatory text */
.explanatory-text {
  font-size:0.74rem; line-height:1.6; color:var(--text-secondary);
  padding-left:12px; border-left:3px solid var(--accent-light); margin:0.3rem 0;
  background:#ffffff;
}

/* Academic insight */
.academic-insight { background:var(--insight-bg); padding:10px 14px; font-size:0.7rem; border-left:4px solid var(--insight-border); margin:0.4rem 0; color:var(--text-secondary); }

/* Concept grid */
.concept-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.concept-card { background:var(--concept-card-bg); border:1.5px solid var(--concept-card-border); padding:12px; border-radius:4px; transition:0.25s; }
.concept-card:hover { border-color:var(--accent); box-shadow:0 0 16px var(--accent-glow); }
.concept-badge { display:inline-block; padding:2px 8px; font-size:0.60rem; font-weight:600; background:var(--accent-soft); color:var(--accent); border-radius:3px; margin-bottom:6px; }
.concept-card h4 { font-size:0.78rem; font-weight:700; margin-bottom:4px; color:var(--text-primary); }
.concept-card p { font-size:0.68rem; color:var(--text-secondary); line-height:1.5; }

/* Overview */
.overview-step-block { background:var(--overview-step-bg); border:1px solid var(--accent-light); border-left:5px solid var(--accent); padding:16px 18px; margin-bottom:0; scroll-margin-top:12px; }
.overview-step-block:hover { border-color:var(--accent); box-shadow:0 0 20px var(--accent-glow); }
.overview-step-header { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
.overview-step-num-badge { width:36px; height:36px; background:var(--accent); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:0.85rem; box-shadow:0 0 14px var(--accent-glow); }
.overview-step-title { font-size:0.82rem; font-weight:700; }
.overview-step-shortdesc { font-size:0.64rem; color:var(--text-muted); }
.overview-connector { display:flex; justify-content:center; padding:4px 0; }
.overview-connector svg { width:24px; height:20px; stroke:var(--accent); }
.overview-divider-line { width:1.5px; height:14px; background:var(--accent); margin:0 auto; }

/* Mode chips */
.mode-chips { display:flex; gap:4px; flex-shrink:0; margin-right:6px; }
.mode-chip {
  display:inline-flex; align-items:center; gap:3px; padding:5px 10px;
  font-size:0.68rem; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;
  border:1.5px solid var(--border-medium); background:var(--bg-card);
  color:var(--text-secondary); cursor:pointer; transition:all 0.2s; white-space:nowrap; font-family:inherit;
}
.mode-chip .chip-icon { font-size:0.8rem; }
.mode-chip:hover { color:var(--accent); border-color:var(--accent); box-shadow:0 0 10px var(--accent-glow); }
.mode-chip.active { background:var(--accent); border-color:var(--accent); color:#fff; box-shadow:0 0 14px var(--accent-glow); }

/* View toggle */
.view-toggle-btn {
  width:34px; height:34px; border:1.5px solid var(--border-medium);
  background:var(--bg-card); cursor:pointer; display:flex; align-items:center; justify-content:center;
  color:var(--text-secondary); transition:transform 0.45s,border-color 0.22s,color 0.22s,box-shadow 0.22s;
  flex-shrink:0; margin-left:auto;
}
.view-toggle-btn svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:2; }
.view-toggle-btn:hover { color:var(--accent); border-color:var(--border-active); box-shadow:0 0 18px var(--accent-glow); }
.view-toggle-btn.rotated { transform:rotate(180deg); color:var(--accent); border-color:var(--accent); box-shadow:0 0 16px var(--accent-glow),inset 0 0 0 1px var(--accent-glow); }

/* Chat area */
.chat-area { border-top:1px solid var(--divider); padding:8px 10px; flex-shrink:0; }
.chat-input-group { display:flex; gap:6px; align-items:center; }
.chat-input { flex:1; padding:6px 10px; border-radius:4px; border:1.5px solid var(--border-light); background:var(--bg-card); color:var(--text-primary); font-family:inherit; font-size:0.72rem; outline:none; resize:none; }
.chat-input:focus { border-color:var(--accent); }
.chat-send { padding:6px 14px; border-radius:4px; background:var(--accent); color:#fff; border:none; cursor:pointer; font-family:inherit; font-size:0.72rem; font-weight:600; }
.chat-history { max-height:140px; overflow-y:auto; margin-top:6px; display:flex; flex-direction:column; gap:4px; }
.message-bubble { padding:6px 10px; border-radius:4px; font-size:0.68rem; line-height:1.5; border-left:3px solid; }
.typing-cursor { animation:blink 0.8s infinite; color:var(--accent); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* Buttons */
.btn-group { display:flex; gap:8px; padding:8px 10px; border-top:1px solid var(--divider); flex-shrink:0; }
.btn-group.hidden { display:none; }
.btn { padding:6px 16px; border-radius:4px; font-size:0.72rem; font-weight:500; cursor:pointer; border:1.5px solid var(--border-light); background:transparent; color:var(--text-secondary); font-family:inherit; transition:0.2s; }
.btn:hover:not(:disabled) { border-color:var(--accent); color:var(--accent); }
.btn:disabled { opacity:0.4; cursor:not-allowed; }
.btn-primary { background:var(--accent); color:#fff; border-color:var(--accent); }
.btn-primary:hover:not(:disabled) { box-shadow:0 0 16px var(--accent-glow); }

@media(max-width:900px) {
  .main-split { grid-template-columns:1fr; }
  .col-left { flex-direction:row; max-height:220px; }
  .concept-grid { grid-template-columns:1fr; }
}
</style>
