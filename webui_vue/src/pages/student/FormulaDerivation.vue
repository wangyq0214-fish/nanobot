<template>
<div class="app-shell">
<StudentNav active-tab="formula-derivation" />

  <div class="main-split">
    <!-- LEFT COLUMN -->
    <div class="col-left">
      <div class="panel">
        <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
        <div class="panel-hd"><i></i><span class="panel-title">{{ stepPanelTitle }}</span></div>
        <div class="panel-body">
          <div class="step-list">
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
          <div class="trace-panel">{{ currentStep.trace || '' }}</div>
          <div style="font-size:0.66rem;color:var(--text-muted);margin-top:6px;">{{ currentStep.extra || '' }}</div>
        </div>
      </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="panel" style="display:flex;flex-direction:column;">
      <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
      <div class="panel-hd">
        <i></i>
        <span class="panel-title">{{ isOverviewMode ? '📋 推导全貌 · 完整链' : currentStep.name }}</span>
        <div class="mode-chips">
          <button
            v-for="m in modes"
            :key="m.key"
            class="mode-chip"
            :class="{ active: currentMode === m.key }"
            @click="switchMode(m.key)"
          ><span class="chip-icon">{{ m.icon }}</span>{{ m.label }}</button>
        </div>
        <button class="view-toggle-btn" :class="{ rotated: isOverviewMode }" title="切换至推导全貌" @click="isOverviewMode = !isOverviewMode; afterRender()">
          <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/><polyline points="16,2 12,6 8,2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8,22 12,18 16,22" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <!-- STEP DETAIL -->
      <div v-if="!isOverviewMode" class="panel-body" style="flex:1;overflow-y:auto;">
        <div style="display:flex;flex-direction:column;gap:8px;">
          <template v-for="(sec, si) in currentStep.sections" :key="si">
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

      <!-- CHAT AREA -->
      <div class="chat-area">
        <div class="chat-input-group">
          <textarea class="chat-input" v-model="chatInput" rows="1" placeholder="向 Agent 提问，例如：RUE 的单位是什么？" @keypress.enter.exact.prevent="handleSend"></textarea>
          <button class="chat-send" @click="handleSend">发送 ✦</button>
        </div>
        <div class="chat-history" ref="chatHistoryEl">
          <div v-for="(msg, mi) in chatMessages" :key="mi" class="message-bubble" :style="{ backgroundColor: msg.isUser ? 'var(--accent-light)' : 'var(--accent-soft)', borderLeftColor: 'var(--accent)' }">
            <strong>{{ msg.isUser ? '👤 用户' : '🤖 Agent' }}</strong><br>{{ msg.text }}
          </div>
        </div>
      </div>

      <!-- STEP BUTTONS -->
      <div class="btn-group" :class="{ hidden: isOverviewMode }">
        <button class="btn" :disabled="currentIdx === 0" @click="currentIdx--">← 上一步</button>
        <button class="btn btn-primary" :disabled="currentIdx >= currentSteps.length - 1" @click="currentIdx++">下一步 →</button>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import katex from 'katex'
import { useAuth } from '../../composables/useAuth.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}

// ---- DATA ----
const formulaSteps = [
  { id:0, name:"🌿 光合作用方程", shortDesc:"CO₂+H₂O+光→糖+O₂", trace:"基础植物生理学 — 化学反应式。", extra:"光补偿点因作物而异。", sections:[
    { kind:"text", value:"光合作用是作物产量的物质基础，其简化总反应为：" },
    { kind:"formula", value:"$$ 6\\,CO_2 + 6\\,H_2O + \\text{光能} \\rightarrow C_6H_{12}O_6 + 6\\,O_2 $$", tag:"(1)" },
    { kind:"insight", value:"该反应在叶绿体中进行，实际过程分光反应和暗反应，量子效率约 8~10 个光量子固定 1 个 CO₂。" }
  ]},
  { id:1, name:"☀️ 光能利用效率(RUE)", shortDesc:"RUE = 生物量/截获PAR", trace:"Monteith 1977 — 辐射利用效率模型。", extra:"典型值：C3作物1.0-1.5 g/MJ。", sections:[
    { kind:"text", value:"光能利用效率（Radiation Use Efficiency, RUE）是单位截获光合有效辐射所生产的干物质。" },
    { kind:"formula", value:"$$ \\text{RUE} = \\frac{\\Delta \\mathrm{Biomass}}{\\sum \\mathrm{IPAR}} \\quad [\\mathrm{g·MJ}^{-1}] $$", tag:"(2)" },
    { kind:"insight", value:"IPAR 为截获光合有效辐射，可通过冠层光截获模型计算。RUE 受氮素、水分和温度影响。" }
  ]},
  { id:2, name:"📏 叶面积指数(LAI)", shortDesc:"LAI = 叶面积/土地面积", trace:"Watson 1947 — 冠层结构指标。", extra:"最适LAI约3~5，过高反而减产。", sections:[
    { kind:"text", value:"叶面积指数是单位土地面积上总叶面积，决定光截获能力。" },
    { kind:"formula", value:"$$ \\text{LAI} = \\frac{\\text{总叶面积}}{\\text{土地面积}} $$", tag:"(3)" },
    { kind:"insight", value:"根据 Beer-Lambert 定律，光截获比例 = 1 - exp(-k·LAI)，其中 k 为消光系数。" }
  ]},
  { id:3, name:"🌾 生物量积累模型", shortDesc:"ΔB = RUE × IPAR", trace:"适用于作物生长模型。", extra:"需考虑维持呼吸和生长呼吸。", sections:[
    { kind:"formula", value:"$$ \\Delta B = \\text{RUE} \\times \\text{IPAR} $$", tag:"(4)" },
    { kind:"insight", value:"每日生物量增量等于光能利用效率乘以当日截获的 PAR。累积生长曲线呈 S 形。" }
  ]},
  { id:4, name:"🌽 收获指数(HI)", shortDesc:"HI = 经济产量/生物产量", trace:"Donald 1962 — 产量分配。", extra:"小麦HI≈0.4-0.5，玉米≈0.5-0.55。", sections:[
    { kind:"text", value:"收获指数表示生物量向收获器官（籽粒、果实等）分配的比例。" },
    { kind:"formula", value:"$$ \\text{HI} = \\frac{Y_{\\text{economic}}}{B_{\\text{total}}} $$", tag:"(5)" }
  ]},
  { id:5, name:"📊 最终产量估算", shortDesc:"Y = Σ(ΔB) × HI", trace:"产量形成综合分析。", extra:"实际产量受灾害、病虫害影响。", sections:[
    { kind:"formula", value:"$$ \\boxed{Y = \\sum_{t} (\\text{RUE}_t \\times \\text{IPAR}_t) \\times \\text{HI}} $$", tag:"(6)" },
    { kind:"insight", value:"该公式将光合生产、光截获、干物质分配融为一体，是作物产量模拟的基本框架。" }
  ]}
]

const codeSteps = [
  { id:0, name:"🌱 计算叶面积指数", shortDesc:"从株行距与单株叶面积推导", trace:"田间调查常用公式。", extra:"注意单位一致性。", sections:[
    { kind:"code", code:`leaf_area_per_plant = 0.8  # m²
plant_spacing = 0.25 * 0.6  # m²
LAI = leaf_area_per_plant / plant_spacing
print(f"LAI = {LAI:.2f}")`, highlight:[3], annotation:"第3行：计算LAI，结果为每平方米土地上的叶面积。" }
  ]},
  { id:1, name:"📈 光截获与生物量", shortDesc:"根据RUE和PAR估算日增量", trace:"DSSAT模型简化版。", extra:"PAR数据来自气象站或遥感。", sections:[
    { kind:"code", code:`RUE = 1.2  # g/MJ
PAR_daily = 12  # MJ/m²/day
k = 0.65  # 消光系数
LAI = 3.5
fIPAR = 1 - np.exp(-k * LAI)
IPAR = PAR_daily * fIPAR
delta_biomass = RUE * IPAR
print(f"日生物量增量: {delta_biomass:.2f} g/m²")`, highlight:[5,6,7], annotation:"第5-7行：计算光截获比例、实际截获PAR、生物量增量。" }
  ]}
]

const conceptSteps = [
  { id:0, name:"传统农业 vs 精准农业", shortDesc:"管理模式对比", trace:"FAO 2022 — 农业可持续发展报告。", extra:"精准农业投资回报周期2-3年。", sections:[
    { kind:"concept-grid", cards:[
      { badge:"传统", title:"经验管理", desc:"基于农户经验，水肥均匀施用。", pro:"✓ 技术门槛低", con:"✗ 资源浪费大" },
      { badge:"精准", title:"变量投入", desc:"利用传感器和GIS进行斑块级管理。", pro:"✓ 提高效率20%+", con:"✗ 需数据和设备" },
      { badge:"智慧", title:"AI决策", desc:"集成物联网和机器学习，动态优化。", pro:"✓ 自适应、可扩展", con:"✗ 基础设施成本高" }
    ]}
  ]},
  { id:1, name:"有机农业 vs 常规农业", shortDesc:"生产体系对比", trace:"IFOAM 2023 — 有机农业原则。", extra:"有机认证需3年转换期。", sections:[
    { kind:"concept-grid", cards:[
      { badge:"有机", title:"天然投入", desc:"使用有机肥、生物防治，禁止化学农药。", pro:"✓ 环境友好", con:"✗ 产量可能降低" },
      { badge:"常规", title:"高投入高产", desc:"依赖化肥、农药保证产量。", pro:"✓ 短期产量高", con:"✗ 土壤退化风险" },
      { badge:"综合", title:"IPM/INM", desc:"综合病虫害和养分管理，平衡产量与生态。", pro:"✓ 可持续性提升", con:"✗ 技术复杂" }
    ]}
  ]},
  { id:2, name:"滴灌 vs 漫灌", shortDesc:"灌溉方式比较", trace:"ICID 2021 — 灌溉效率报告。", extra:"滴灌节水率可达60%。", sections:[
    { kind:"concept-grid", cards:[
      { badge:"滴灌", title:"精准灌溉", desc:"将水直接输送至根区，蒸发损失极小。", pro:"✓ 节水、增产", con:"✗ 初始投资高" },
      { badge:"漫灌", title:"地面灌溉", desc:"水沿田面流动，覆盖范围大。", pro:"✓ 成本低", con:"✗ 浪费水、易涝" },
      { badge:"喷灌", title:"模拟降雨", desc:"通过喷头将水喷洒到空中。", pro:"✓ 地形适应性强", con:"✗ 风影响均匀度" }
    ]}
  ]},
  { id:3, name:"嫁接技术对比", shortDesc:"砧木与接穗组合", trace:"Horticulture Reviews 2015 — 蔬菜嫁接。", extra:"西瓜嫁接抗枯萎病效果显著。", sections:[
    { kind:"concept-grid", cards:[
      { badge:"劈接", title:"操作简单", desc:"将接穗削成楔形插入砧木切口。", pro:"✓ 成活率高", con:"✗ 速度较慢" },
      { badge:"靠接", title:"双株共育", desc:"两株植物靠近后削皮绑扎。", pro:"✓ 对技术要求低", con:"✗ 占地多" },
      { badge:"插接", title:"快速高效", desc:"用竹签在砧木上打孔插入接穗。", pro:"✓ 适合规模化", con:"✗ 需精准操作" }
    ]}
  ]}
]

const stepDataMap = { formula: formulaSteps, code: codeSteps, concept: conceptSteps }
const modes = [
  { key: 'formula', icon: '📐', label: '公式' },
  { key: 'code', icon: '💻', label: '代码' },
  { key: 'concept', icon: '📖', label: '概念' },
]

// ---- STATE ----
const currentMode = ref('formula')
const currentIdx = ref(0)
const isOverviewMode = ref(false)
const isDark = ref(false)
const chatInput = ref('')
const chatMessages = ref([])
const overviewEl = ref(null)

const currentSteps = computed(() => stepDataMap[currentMode.value] || formulaSteps)
const currentStep = computed(() => currentSteps.value[currentIdx.value] || currentSteps.value[0])
const stepPanelTitle = computed(() => {
  const map = { formula: '🧭 思路指引 · 公式推导', code: '🧭 思路指引 · Python代码', concept: '🧭 思路指引 · 概念辨析' }
  return map[currentMode.value] || map.formula
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

function switchMode(mode) {
  if (mode === currentMode.value) return
  currentMode.value = mode
  currentIdx.value = 0
  isOverviewMode.value = false
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

function handleSend() {
  const q = chatInput.value.trim()
  if (!q) return
  chatMessages.value.push({ text: q, isUser: true })
  chatInput.value = ''
  setTimeout(() => {
    let answer = `根据当前步骤「${currentStep.value.name}」：`
    if (q.includes('RUE')) answer += 'RUE 是光能利用效率，单位 g/MJ。C3作物典型值1.0~1.5。'
    else if (q.includes('LAI')) answer += 'LAI 是叶面积指数，合理范围 3~5。'
    else answer += `这是基于光合作用到产量形成的推导链。`
    chatMessages.value.push({ text: answer, isUser: false })
    if (chatMessages.value.length > 6) chatMessages.value = chatMessages.value.slice(-6)
  }, 400)
}

watch([currentMode, currentIdx, isOverviewMode], () => {
  nextTick(() => {
    document.querySelectorAll('.formula-content').forEach(el => {
      // Formulas already rendered by v-html via renderFormula
    })
  })
})
</script>

<style>
:root {
  --bg-root: #f2f1f6;
  --bg-card: rgba(255,255,255,0.65);
  --bg-nav: rgba(255,255,255,0.88);
  --accent: #5a4cd8;
  --accent-light: rgba(90,76,216,0.28);
  --accent-soft: rgba(90,76,216,0.07);
  --accent-glow: rgba(90,76,216,0.18);
  --accent-deep: #4a3cc0;
  --border-light: rgba(0,0,0,0.07);
  --border-medium: rgba(0,0,0,0.13);
  --border-active: #5a4cd8;
  --text-primary: #18161f;
  --text-secondary: #4a4658;
  --text-muted: #7a7688;
  --divider: rgba(0,0,0,0.05);
  --formula-black-border: #1e1e28;
  --formula-card-bg: #ffffff;
  --overview-step-bg: #ffffff;
  --insight-bg: rgba(90,76,216,0.08);
  --insight-border: #5a4cd8;
  --trace-bg: #ffffff;
  --code-bg: #1a1b26;
  --code-text: #c0caf5;
  --code-border: #2a2740;
  --concept-card-bg: #ffffff;
  --concept-card-border: #d0c8e8;
}
body.dark {
  --bg-root: #06050f;
  --bg-card: rgba(14,13,26,0.55);
  --bg-nav: rgba(8,7,18,0.9);
  --accent: #8B70FF;
  --accent-light: rgba(139,112,255,0.35);
  --accent-soft: rgba(139,112,255,0.10);
  --accent-glow: rgba(139,112,255,0.25);
  --accent-deep: #6B50E0;
  --border-light: rgba(255,255,255,0.06);
  --border-medium: rgba(255,255,255,0.14);
  --border-active: #8B70FF;
  --text-primary: #e4e1f6;
  --text-secondary: #a8a3c0;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.06);
  --formula-black-border: #5a5670;
  --formula-card-bg: #1c1a2e;
  --overview-step-bg: #1c1a2e;
  --insight-bg: rgba(139,112,255,0.15);
  --insight-border: #8B70FF;
  --trace-bg: #1c1a2e;
  --code-bg: #0d0c1a;
  --code-text: #c0caf5;
  --code-border: #2a2740;
  --concept-card-bg: #1c1a2e;
  --concept-card-border: #3d3860;
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
  flex-shrink:0; height:52px; background:var(--bg-nav); backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px); border:2px solid var(--accent);
  display:flex; align-items:center; justify-content:space-between;
  padding:0 28px; border-radius:0;
  box-shadow:0 0 0 2px var(--accent-soft),0 0 18px var(--accent-glow);
}
.nav-left { display:flex; align-items:center; gap:16px; }
.nav-logo {
  font-family:'Playfair Display','Georgia',serif; font-style:italic;
  font-size:1.35rem; font-weight:700; color:var(--accent);
  display:flex; align-items:center; gap:8px;
}
.nav-logo .dot { width:7px; height:7px; background:var(--accent); box-shadow:0 0 14px var(--accent-glow); animation:dotPulse 2.4s infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:0.55} }
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
  background:var(--bg-card); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  border:2px solid var(--accent); border-radius:0;
  box-shadow:0 0 0 1px var(--accent-soft); position:relative; overflow:hidden;
  display:flex; flex-direction:column; transition:all 0.28s; flex:1; min-height:0;
}
.panel:hover { border-color:var(--border-active); box-shadow:0 0 28px var(--accent-glow),0 0 0 2px var(--accent-soft); }
.panel-strip { position:absolute; pointer-events:none; z-index:1; }
.panel-strip.top, .panel-strip.bottom { left:-100%; width:100%; height:2px; background:linear-gradient(90deg,transparent,#C4B0FF,#7B5CFF,#C4B0FF,transparent); }
.panel-strip.right, .panel-strip.left { top:-100%; width:2px; height:100%; background:linear-gradient(180deg,transparent,#C4B0FF,#A78BFA,#C4B0FF,transparent); }
.panel-strip.top { top:0; animation:scanH 3.6s infinite; }
.panel-strip.right { right:0; animation:scanV 3.6s infinite; animation-delay:0.9s; }
.panel-strip.bottom { bottom:0; animation:scanHRev 3.6s infinite; animation-delay:1.8s; }
.panel-strip.left { left:0; animation:scanVRev 3.6s infinite; animation-delay:2.7s; }
@keyframes scanH { 0%{left:-100%;opacity:0} 8%{opacity:1} 92%{opacity:1} 100%{left:100%;opacity:0} }
@keyframes scanHRev { 0%{left:100%;opacity:0} 8%{opacity:1} 92%{opacity:1} 100%{left:-100%;opacity:0} }
@keyframes scanV { 0%{top:-100%;opacity:0} 8%{opacity:1} 92%{opacity:1} 100%{top:100%;opacity:0} }
@keyframes scanVRev { 0%{top:100%;opacity:0} 8%{opacity:1} 92%{opacity:1} 100%{top:-100%;opacity:0} }

.panel-hd {
  flex-shrink:0; display:flex; align-items:center; gap:8px;
  padding:10px 16px; border-bottom:1px solid var(--divider); position:relative; z-index:2;
}
.panel-hd i { width:4px; height:20px; background:linear-gradient(180deg,var(--accent),var(--accent-deep)); box-shadow:0 0 8px var(--accent-glow); flex-shrink:0; }
.panel-title { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; flex:1; min-width:0; }
.panel-body { flex:1; min-height:0; padding:14px 16px; overflow-y:auto; display:flex; flex-direction:column; gap:10px; position:relative; z-index:2; scroll-behavior:smooth; }

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
  .col-left { flex-direction:row; max-height:180px; }
  .concept-grid { grid-template-columns:1fr; }
}
</style>
