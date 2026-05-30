<template>
<div class="app">
<StudentNav active-tab="tutoring-assistant" />

  <div class="main-wrapper" ref="mainWrapper">
    <div class="left-area" ref="leftArea">
      <!-- 知识点巩固 -->
      <div class="panel" ref="knowledgePanel" :style="{ height: panelHeights.knowledge + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>📐 知识点巩固</div>
          <span class="size-badge">{{ panelHeights.knowledge }}px</span>
        </div>
        <div class="panel-body">
          <div v-for="(item, i) in knowledgeItems" :key="'k'+i" class="knowledge-mini">
            <div class="k-icon">📐</div>
            <div class="k-info">
              <div class="k-title">{{ item.title }}</div>
              <div class="k-formula" v-html="renderFormula(item.formula)"></div>
              <div class="k-mastery">掌握度：{{ item.mastery }}</div>
            </div>
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'knowledge')"></div>
      </div>
      <!-- 错题归因 -->
      <div class="panel" ref="errorPanel" :style="{ height: panelHeights.error + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>🔬 错题归因</div>
          <span class="size-badge">{{ panelHeights.error }}px</span>
        </div>
        <div class="panel-body">
          <div v-for="(item, i) in errorItems" :key="'e'+i" class="error-entry">
            <span class="e-tag">{{ item.type }}</span>
            <div><strong>{{ item.title }}</strong><br>{{ item.detail }}</div>
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'error')"></div>
      </div>
      <!-- 学习策略 -->
      <div class="panel" ref="strategyPanel" :style="{ height: panelHeights.strategy + 'px' }">
        <div class="panel-hd">
          <div class="panel-title-group"><i></i>💡 学习策略</div>
          <span class="size-badge">{{ panelHeights.strategy }}px</span>
        </div>
        <div class="panel-body">
          <div v-for="(item, i) in strategyItems" :key="'s'+i" class="strategy-entry">
            <span class="s-dot"></span>{{ item }}
          </div>
        </div>
        <div class="resize-handle-v" @mousedown="startVerticalResize($event, 'strategy')"></div>
      </div>
    </div>
    <div
      class="resize-handle-h"
      :class="{ locked: isLockedH, unlocked: !isLockedH }"
      @dblclick="isLockedH = !isLockedH"
      @mousedown="startHorizontalResize"
      ref="resizeHandleH"
      title="双击解锁拖拽左右宽度"
    ></div>
    <div class="right-area" ref="rightArea">
      <div class="tutor-panel">
        <div class="tutor-header">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="tutor-avatar">🧑‍🏫</div>
            <span>AI 导师</span>
          </div>
          <div class="header-right">
            <div class="mode-switch">
              <button class="mode-btn" :class="{ active: currentMode === 'my' }" @click="switchMode('my')">📝 我的题目</button>
              <button class="mode-btn" :class="{ active: currentMode === 'ai' }" @click="switchMode('ai')">🤖 AI推题</button>
            </div>
            <button class="view-toggle-btn" :class="{ answering: currentView === 'answer' }" @click="toggleView">
              {{ currentView === 'chat' ? '✏️ 答题' : '💬 对话' }}
            </button>
          </div>
        </div>
        <!-- 对话视图 -->
        <div class="chat-view" :class="{ hidden: currentView !== 'chat' }">
          <div class="tutor-messages" ref="tutorMessages">
            <div v-for="(msg, i) in tutorMsgs" :key="i" class="tutor-msg" v-html="msg"></div>
          </div>
          <div class="chat-bottom-bar">
            <input type="text" class="student-input" v-model="studentQuestion" placeholder="向导师提问，例如：什么是消光系数？" @keyup.enter="askQuestion">
            <button class="send-btn" @click="askQuestion">发送</button>
            <button class="start-answer-btn" @click="switchToAnswer">✏️ 答题</button>
          </div>
        </div>
        <!-- 答题视图 -->
        <div class="answer-view" :class="{ hidden: currentView !== 'answer' }">
          <div class="qa-top">
            <div class="question-box" v-html="questionContent"></div>
            <div class="upload-row" v-show="currentMode === 'my'">
              <input type="file" id="fileInput" ref="fileInput" style="display:none;" accept=".txt,.doc,.docx,.pdf" multiple @change="handleFileUpload">
              <label for="fileInput" class="file-label">📎 上传题目（可多选）</label>
              <span style="font-size:0.55rem;color:var(--text3);">支持一次上传多道题</span>
            </div>
          </div>
          <div class="qa-bottom">
            <textarea class="answer-input" v-model="answerInput" placeholder="✏️ 在这里写下你的解答..."></textarea>
            <div class="submit-row">
              <button class="submit-btn" @click="submitAnswer">✅ 提交回答</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="progress-bar">
    <span>📊 辅导进度</span>
    <div style="flex:1;background:var(--border);height:6px;border-radius:3px;"><div class="progress-fill" :style="{ width: Math.min(submissionCount * 25, 100) + '%' }"></div></div>
    <span>{{ submissionCount }} 次提交</span>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
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
const isDark = ref(false)
const currentMode = ref('my')
const currentView = ref('chat')
const isLockedH = ref(true)
const studentQuestion = ref('')
const answerInput = ref('')
const questionContent = ref('')
const submissionCount = ref(2)
const tutorMsgs = ref([])
const knowledgeItems = ref([])
const errorItems = ref([])
const strategyItems = ref([])
const panelHeights = reactive({ knowledge: 378, error: 277, strategy: 200 })
const mainWrapper = ref(null)
const leftArea = ref(null)
const rightArea = ref(null)
const resizeHandleH = ref(null)
const tutorMessages = ref(null)
const fileInput = ref(null)

const aiQuestionBank = [
  "某果园测得叶面积指数 LAI=4.2，消光系数 k=0.6，求光截获比例 fIPAR。",
  "已知小麦 RUE=1.2 g/MJ，日PAR=14 MJ/m²，LAI=3.5，k=0.5，估算日生物量增量。",
  "推导收获指数 HI = Y_economic / B_total，并说明其农学意义。",
  "比较滴灌与漫灌的水分利用效率，列出至少三个优缺点。"
]

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

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

function addTutorMsg(html) {
  tutorMsgs.value.push(html)
  nextTick(() => {
    if (tutorMessages.value) tutorMessages.value.scrollTop = tutorMessages.value.scrollHeight
  })
}

function switchMode(mode) {
  currentMode.value = mode
  if (mode === 'ai') {
    questionContent.value = aiQuestionBank[Math.floor(Math.random() * aiQuestionBank.length)]
  } else {
    questionContent.value = ''
  }
}

function toggleView() {
  if (currentView.value === 'chat') switchToAnswer()
  else switchToChat()
}

function switchToAnswer() {
  currentView.value = 'answer'
  if (currentMode.value === 'ai' && !questionContent.value.trim()) {
    questionContent.value = aiQuestionBank[Math.floor(Math.random() * aiQuestionBank.length)]
  }
}

function switchToChat() {
  currentView.value = 'chat'
}

function handleFileUpload(event) {
  const files = event.target.files
  if (!files.length) return
  const firstFile = files[0]
  const reader = new FileReader()
  reader.onload = function(e) {
    let content = e.target.result
    if (content.length > 300) content = content.substring(0, 300) + '…'
    questionContent.value = content
    addTutorMsg('📄 已读取文件：' + firstFile.name + (files.length > 1 ? ' 等' + files.length + '个文件' : ''))
  }
  reader.readAsText(firstFile, 'UTF-8')
}

function askQuestion() {
  const q = studentQuestion.value.trim()
  if (!q) return
  addTutorMsg(`<strong>👤 学生：</strong>${q}`)
  studentQuestion.value = ''
  setTimeout(() => {
    let reply = ''
    if (q.includes('消光系数')) reply = '消光系数 k 描述了冠层对光的衰减能力，典型值在0.3~0.8之间。'
    else if (q.includes('RUE')) reply = 'RUE 是光能利用效率，单位g/MJ，C3作物约1.0-1.5。'
    else reply = '这是一个很好的问题，导师正在查阅资料中…'
    addTutorMsg(`<strong>🤖 导师：</strong>${reply}`)
  }, 500)
}

function submitAnswer() {
  const answer = answerInput.value.trim()
  if (!answer) { alert('请输入你的解答'); return }
  let questionText = questionContent.value.replace(/<[^>]*>/g, '').trim()
  if (!questionText) { alert('请先设置题目'); return }

  const qLow = questionText.toLowerCase()
  const aLow = answer.toLowerCase()
  let analysis = '', isCorrect = false, errorType = '', knowTitle = '', knowFormula = '', mastery = '', errTitle = '', errDetail = ''

  if (qLow.includes('lai') || qLow.includes('叶面积指数')) {
    knowTitle = '叶面积指数(LAI)'
    knowFormula = 'LAI = 总叶面积/土地面积'
    if (aLow.includes('0.8') || aLow.includes('0.9') || aLow.includes('fipar')) {
      isCorrect = true; mastery = '🟢 已掌握 (85%)'; analysis = '光截获比例计算正确。'
    } else { isCorrect = false; errorType = '📏 概念错误'; mastery = '🔴 需加强 (50%)'; errTitle = 'LAI与光截获'; errDetail = 'fIPAR = 1 - exp(-k·LAI)，应代入LAI=4.2, k=0.6得0.92。'; analysis = '未正确应用 Beer-Lambert 定律。'; }
  } else if (qLow.includes('rue') || qLow.includes('生物量')) {
    knowTitle = '光能利用效率(RUE)'
    knowFormula = 'ΔB = RUE × IPAR'
    if (aLow.includes('1.2') && aLow.includes('14')) {
      isCorrect = true; mastery = '🟢 已掌握 (80%)'; analysis = '日生物量估算正确。'
    } else { isCorrect = false; errorType = '🔢 计算疏忽'; mastery = '🔴 需加强 (60%)'; errTitle = 'RUE计算'; errDetail = 'IPAR = PAR × fIPAR，fIPAR = 1 - exp(-0.5×3.5)≈0.83，ΔB=1.2×14×0.83≈13.9 g/m²。'; analysis = '计算步骤遗漏光截获比例。'; }
  } else if (qLow.includes('收获指数') || qLow.includes('hi')) {
    knowTitle = '收获指数(HI)'
    knowFormula = 'HI = Y_economic / B_total'
    if (aLow.includes('经济产量') || aLow.includes('生物产量')) {
      isCorrect = true; mastery = '🟢 已掌握 (90%)'; analysis = '收获指数概念清晰。'
    } else { isCorrect = false; errorType = '🧠 概念模糊'; mastery = '🔴 需加强 (55%)'; errTitle = '收获指数定义'; errDetail = 'HI = 经济器官产量 / 总生物量，反映了作物将干物质分配到收获器官的能力。'; analysis = '概念表述不够准确。'; }
  } else {
    knowTitle = '园艺基础概念'; knowFormula = '—'
    if (aLow.length > 20) { isCorrect = true; mastery = '🟢 回答合理'; analysis = '解答有一定道理。'; }
    else { isCorrect = false; errorType = '📝 回答不完整'; mastery = '🔴 需加强'; errTitle = '解答过于简略'; errDetail = '请写出具体公式或分析过程。'; analysis = '解答太简略，无法判断。'; }
  }

  addTutorMsg(`📝 <strong>题目：</strong>${questionText}<br>💭 <strong>你的解答：</strong>${answer}`)
  setTimeout(() => {
    addTutorMsg(`🔍 <strong>导师分析：</strong>${analysis}`)
    knowledgeItems.value.push({ title: knowTitle, formula: knowFormula, mastery })
    if (!isCorrect && errorType) {
      errorItems.value.push({ title: errTitle, type: errorType, detail: errDetail })
      strategyItems.value.push(`⚠️ 建议复习"${knowTitle}"，重点关注${errorType.includes('计算')?'公式代入步骤':'概念理解'}`)
    } else if (isCorrect) { strategyItems.value.push(`✅ "${knowTitle}"掌握良好，可以挑战更高难度题目。`) }
    else { strategyItems.value.push('📌 请提供更详细的解答过程，以便精准分析。') }
    submissionCount.value++
  }, 800)

  answerInput.value = ''
  switchToChat()
  addTutorMsg('✅ 回答已提交，导师正在分析中…')
}

// ---- Horizontal resize ----
let isResizingH = false, startX, startLeftW, startRightW

function startHorizontalResize(e) {
  if (isLockedH.value) return
  isResizingH = true
  startX = e.clientX
  startLeftW = leftArea.value.getBoundingClientRect().width
  startRightW = rightArea.value.getBoundingClientRect().width
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMove(e) {
  if (!isResizingH) return
  const dx = e.clientX - startX
  const ww = mainWrapper.value.getBoundingClientRect().width
  let nl = startLeftW + dx, nr = startRightW - dx
  if (nl < 280) nl = 280
  if (nr < 420) nr = 420
  leftArea.value.style.width = (nl / ww * 100) + '%'
  rightArea.value.style.width = (nr / ww * 100) + '%'
}

function onMouseUp() {
  if (isResizingH) { isResizingH = false; document.body.style.cursor = ''; document.body.style.userSelect = '' }
}

// ---- Vertical resize ----
let isResizingV = false, resizingPanelKey = '', startY, startHeight

function startVerticalResize(e, panelKey) {
  isResizingV = true
  resizingPanelKey = panelKey
  startY = e.clientY
  startHeight = panelHeights[panelKey]
  document.body.style.cursor = 'row-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMoveV(e) {
  if (!isResizingV) return
  const dy = e.clientY - startY
  let newH = startHeight + dy
  if (newH < 120) newH = 120
  if (newH > 500) newH = 500
  panelHeights[resizingPanelKey] = Math.round(newH)
}

function onMouseUpV() {
  if (isResizingV) { isResizingV = false; resizingPanelKey = ''; document.body.style.cursor = ''; document.body.style.userSelect = '' }
}

// ---- Init mock data ----
onMounted(() => {
  knowledgeItems.value.push(
    { title: '叶面积指数(LAI)', formula: 'LAI = 总叶面积/土地面积', mastery: '🟡 待巩固' },
    { title: '光能利用效率(RUE)', formula: 'RUE = ΔB / ΣIPAR [g/MJ]', mastery: '🟢 已掌握 (82%)' },
    { title: '收获指数(HI)', formula: 'HI = Y_economic / B_total', mastery: '🟢 已掌握 (88%)' },
    { title: '光合作用总反应', formula: '6CO_2+6H_2O+光→C_6H_{12}O_6+6O_2', mastery: '🟢 已掌握 (95%)' },
    { title: '光截获比例', formula: 'fIPAR = 1 - exp(-k·LAI)', mastery: '🔴 需加强 (52%)' }
  )
  errorItems.value.push(
    { title: 'LAI计算光截获', type: '📏 概念错误', detail: '未正确使用消光系数k，直接以LAI代替fIPAR。' },
    { title: 'RUE单位换算', type: '🔢 计算疏忽', detail: '混淆MJ与J，导致生物量高估1000倍。' },
    { title: '收获指数应用', type: '🧠 概念混淆', detail: '误将HI用于营养器官作物，HI仅适用于以籽粒/果实为收获对象的作物。' }
  )
  strategyItems.value.push(
    '📌 建议优先掌握LAI与光截获的关系，这是产量估算的基础',
    '⚠️ 连续两次在RUE计算上出错，重点练习PAR → IPAR → ΔB 三步走',
    '💪 光合反应方程式记忆牢固，可挑战光反应与暗反应细节',
    '📝 收获指数需结合具体作物理解，推荐查阅小麦、玉米、水稻的典型HI值'
  )
  addTutorMsg('👋 欢迎回来！你上次在<strong>叶面积指数(LAI)</strong>和<strong>光能利用效率(RUE)</strong>上出现了错误，今天我们重点巩固。')
  addTutorMsg('📝 点击右上角<strong>"答题"</strong>按钮进入答题模式，题目框与答题框已为你准备好。')
  addTutorMsg('💡 你也可以切换到<strong>"AI推题"</strong>模式，让我为你智能出题。')
  questionContent.value = '某苹果园 LAI=3.8，消光系数 k=0.55，请计算光截获比例 fIPAR。'
  answerInput.value = '解：根据 Beer-Lambert 定律，fIPAR = 1 - exp(-k·LAI) = 1 - exp(-0.55×3.8) = 1 - exp(-2.09) ≈ 1 - 0.123 = 0.877。\n因此光截获比例约为 87.7%。'

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('mousemove', onMouseMoveV)
  window.addEventListener('mouseup', onMouseUpV)
})
</script>

<style>
:root {
  --bg: #f2f1f6;
  --card: rgba(255,255,255,0.82);
  --nav-bg: rgba(255,255,255,0.95);
  --accent: #5a4cd8;
  --accent-light: rgba(90,76,216,0.12);
  --accent-glow: rgba(90,76,216,0.22);
  --border: rgba(0,0,0,0.1);
  --text: #18161f;
  --text2: #4a4658;
  --text3: #7a7688;
  --divider: rgba(0,0,0,0.08);
  --tutor-msg-bg: #f0edff;
  --green: #0d9488;
  --red: #ef4444;
  --radius: 12px;
  --panel-radius: 14px;
  --card-radius: 10px;
  --quiz-border: #5a4cd8;
  --quiz-bg: #f8f7ff;
  --resize-handle-color: rgba(90,76,216,0.3);
}
body.dark {
  --bg: #06050f;
  --card: rgba(20,18,30,0.85);
  --nav-bg: rgba(10,8,18,0.96);
  --accent: #8B70FF;
  --accent-light: rgba(139,112,255,0.18);
  --accent-glow: rgba(139,112,255,0.28);
  --border: rgba(255,255,255,0.1);
  --text: #e4e1f6;
  --text2: #b0abc8;
  --text3: #6d6a88;
  --divider: rgba(255,255,255,0.08);
  --tutor-msg-bg: #1e1b2e;
  --quiz-border: #8B70FF;
  --quiz-bg: #1a1830;
  --resize-handle-color: rgba(139,112,255,0.35);
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',sans-serif;
  background:var(--bg); color:var(--text); height:100vh; overflow:hidden;
  transition:0.3s; letter-spacing:0.01em;
}
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:8px; }
</style>
<style scoped>
.app { display:flex; flex-direction:column; height:100vh; max-width:1800px; margin:0 auto; padding:10px 14px; gap:10px; }

/* Student nav bar */
.top-nav {
  flex-shrink:0; height:48px; display:flex; align-items:center; justify-content:space-between;
  background:var(--nav-bg); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  border:2px solid var(--accent); border-radius:24px; padding:0 24px;
  box-shadow:0 0 0 2px var(--accent-light),0 0 18px var(--accent-glow);
}
.nav-left { display:flex; align-items:center; gap:16px; }
.nav-logo {
  font-family:'Playfair Display',serif; font-style:italic; font-size:1.1rem; font-weight:700;
  color:var(--accent); display:flex; align-items:center; gap:6px;
}
.nav-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 8px var(--accent-glow); animation:dot 2.4s infinite; }
@keyframes dot { 0%,100%{opacity:1} 50%{opacity:0.4} }
.nav-center { display:flex; align-items:center; gap:4px; }
.nav-tab {
  padding:6px 14px; border-radius:14px; font-size:0.8rem; font-weight:500;
  color:var(--text2); cursor:pointer; transition:all 0.2s; border:1.5px solid transparent;
}
.nav-tab:hover { color:var(--text); background:var(--accent-light); }
.nav-tab.active { color:var(--accent); background:var(--accent-light); border-color:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.nav-right { display:flex; align-items:center; gap:8px; }
.nav-icon {
  width:32px; height:32px; border-radius:50%; border:1.5px solid var(--border);
  background:transparent; cursor:pointer; display:flex; align-items:center;
  justify-content:center; color:var(--text2); transition:all 0.2s;
}
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; }
.nav-icon:hover { color:var(--accent); border-color:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.nav-avatar {
  width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg,#5a4cd8,#8B70FF);
  display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600;
  font-size:0.7rem; cursor:pointer; box-shadow:0 0 14px var(--accent-glow);
}
.main-wrapper { flex:1; min-height:0; display:flex; gap:0; position:relative; }
.left-area {
  width:25%; min-width:280px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;
  padding-right:1px;
}
.right-area {
  width:75%; min-width:420px; display:flex; flex-direction:column; gap:0;
  padding-left:1px;
}
.resize-handle-h {
  width:4px; cursor:default; background:transparent; position:relative; z-index:10;
  flex-shrink:0; display:flex; align-items:center; justify-content:center; transition:background 0.2s;
  margin:0; border-radius:var(--card-radius);
}
.resize-handle-h.locked::after { content:'🔒'; font-size:0.7rem; opacity:0.6; }
.resize-handle-h.unlocked::after { content:'🔓'; font-size:0.7rem; opacity:0.6; }
.resize-handle-h.unlocked:hover { background:var(--accent-light); cursor:col-resize; }

.panel {
  background:var(--card); backdrop-filter:blur(10px);
  border:2px solid var(--accent); border-radius:var(--panel-radius);
  overflow:hidden; box-shadow:0 0 0 1px var(--accent-light);
  display:flex; flex-direction:column; flex-shrink:0; position:relative;
}
.panel-hd {
  display:flex; align-items:center; gap:8px; padding:10px 14px;
  border-bottom:1px solid var(--divider); font-weight:700; font-size:0.7rem;
  text-transform:uppercase; letter-spacing:0.04em; background:var(--card);
  flex-shrink:0; border-radius:var(--panel-radius) var(--panel-radius) 0 0;
  justify-content:space-between;
}
.panel-hd i { width:3px; height:16px; background:var(--accent); border-radius:2px; box-shadow:0 0 6px var(--accent-glow); }
.panel-title-group { display:flex; align-items:center; gap:8px; }
.size-badge {
  font-size:0.55rem; font-weight:500; background:var(--accent-light);
  padding:2px 8px; border-radius:6px; color:var(--accent); white-space:nowrap;
}
.panel-body {
  padding:12px 14px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;
  flex:1; min-height:0;
}
.resize-handle-v {
  height:6px; background:transparent; cursor:row-resize; flex-shrink:0;
  transition:background 0.2s; border-radius:0 0 var(--panel-radius) var(--panel-radius);
  display:flex; align-items:center; justify-content:center;
}
.resize-handle-v::after {
  content:''; width:30px; height:2px; background:var(--resize-handle-color);
  border-radius:1px; transition:0.2s;
}
.resize-handle-v:hover { background:var(--accent-light); }
.resize-handle-v:hover::after { background:var(--accent); }

.knowledge-mini {
  background:var(--card); border:1.5px solid var(--accent); border-radius:var(--card-radius);
  padding:12px 14px; display:flex; align-items:center; gap:12px;
  animation:slideIn 0.4s; flex-shrink:0;
}
@keyframes slideIn { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
.k-icon { width:36px; height:36px; background:var(--accent-light); border-radius:var(--card-radius); display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }
.k-info { flex:1; min-width:0; }
.k-title { font-weight:700; font-size:0.68rem; color:var(--accent); }
.k-formula { font-size:0.7rem; margin-top:2px; }
.k-mastery { font-size:0.55rem; color:var(--text3); margin-top:2px; }
.error-entry {
  background:rgba(239,68,68,0.06); border-left:3px solid var(--red); border-radius:var(--card-radius);
  padding:10px 12px; font-size:0.62rem; display:flex; align-items:flex-start; gap:8px;
  animation:slideIn 0.4s; flex-shrink:0;
}
.e-tag { background:rgba(239,68,68,0.12); color:var(--red); font-weight:700; font-size:0.55rem; padding:3px 8px; border-radius:6px; white-space:nowrap; flex-shrink:0; }
.strategy-entry {
  background:var(--accent-light); border-radius:var(--card-radius); padding:10px 12px;
  font-size:0.62rem; display:flex; align-items:center; gap:8px;
  animation:slideIn 0.4s; flex-shrink:0;
}
.s-dot { width:8px; height:8px; background:var(--accent); border-radius:2px; flex-shrink:0; }

.tutor-panel {
  background:var(--card); backdrop-filter:blur(10px);
  border:2px solid var(--accent); border-radius:var(--panel-radius);
  overflow:hidden; box-shadow:0 0 0 1px var(--accent-light);
  display:flex; flex-direction:column; flex:1; min-height:0;
}
.tutor-header {
  padding:8px 16px; border-bottom:1px solid var(--divider);
  display:flex; align-items:center; gap:10px; font-weight:700; font-size:0.7rem;
  background:var(--card); justify-content:space-between; flex-shrink:0;
  border-radius:var(--panel-radius) var(--panel-radius) 0 0;
}
.tutor-avatar { width:34px; height:34px; background:var(--accent); border-radius:var(--card-radius); display:flex; align-items:center; justify-content:center; font-size:1.2rem; color:#fff; box-shadow:0 0 10px var(--accent-glow); }
.header-right { display:flex; gap:6px; align-items:center; }
.mode-switch { display:flex; gap:4px; }
.mode-btn {
  padding:5px 12px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-weight:700; font-size:0.62rem; cursor:pointer;
  transition:0.2s; border-radius:var(--card-radius);
}
.mode-btn.active { background:var(--accent); color:#fff; }
.view-toggle-btn {
  padding:5px 14px; border:2px solid var(--accent); background:transparent;
  color:var(--accent); font-weight:700; font-size:0.62rem; cursor:pointer;
  transition:0.2s; border-radius:var(--card-radius);
}
.view-toggle-btn:hover { background:var(--accent-light); }
.view-toggle-btn.answering { background:var(--accent); color:#fff; }
.chat-view { flex:1; display:flex; flex-direction:column; min-height:0; }
.chat-view.hidden { display:none; }
.tutor-messages { flex:1; overflow-y:auto; padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
.tutor-msg {
  background:var(--tutor-msg-bg); border-left:3px solid var(--accent);
  padding:10px 12px; font-size:0.63rem; line-height:1.6;
  animation:slideIn 0.35s; border-radius:0 var(--card-radius) var(--card-radius) 0;
}
.tutor-msg .highlight { background:var(--accent-light); padding:2px 6px; border-radius:4px; font-weight:600; }
.chat-bottom-bar {
  padding:8px 14px; border-top:1px solid var(--divider);
  display:flex; gap:8px; align-items:center; flex-shrink:0;
}
.student-input {
  flex:1; padding:8px 12px; border:2px solid var(--accent); border-radius:var(--card-radius);
  background:var(--card); color:var(--text); font-size:0.65rem; font-family:inherit;
}
.student-input:focus { outline:none; border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-light); }
.send-btn {
  padding:8px 14px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.65rem; border:none; cursor:pointer; border-radius:var(--card-radius);
  white-space:nowrap;
}
.start-answer-btn {
  padding:10px 22px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.7rem; border:none; cursor:pointer; box-shadow:0 0 10px var(--accent-glow);
  border-radius:var(--card-radius); white-space:nowrap;
}
.answer-view { flex:1; display:flex; flex-direction:column; min-height:0; }
.answer-view.hidden { display:none; }
.qa-top { flex:1; display:flex; flex-direction:column; padding:14px 16px; gap:6px; border-bottom:1px solid var(--divider); min-height:0; }
.qa-bottom { flex:1; padding:14px 16px; display:flex; flex-direction:column; gap:8px; min-height:0; }
.question-box {
  flex:1; border:2px solid var(--quiz-border); padding:16px 18px; font-size:0.7rem;
  font-weight:500; display:flex; align-items:flex-start; overflow-y:auto;
  background:var(--quiz-bg); color:var(--text); border-radius:var(--card-radius);
  line-height:1.6; min-height:0;
}
.answer-input {
  flex:1; border:2px solid var(--quiz-border); padding:16px 18px;
  font-size:0.68rem; font-family:inherit; resize:none; border-radius:var(--card-radius);
  line-height:1.6; background:var(--card); color:var(--text); min-height:0;
}
.upload-row { display:flex; gap:6px; align-items:center; margin-top:4px; flex-shrink:0; }
.file-label {
  padding:5px 12px; border:2px solid var(--accent); background:transparent;
  cursor:pointer; font-size:0.6rem; font-weight:600; color:var(--accent);
  border-radius:var(--card-radius); transition:0.2s;
}
.file-label:hover { background:var(--accent-light); }
.submit-row { display:flex; gap:8px; justify-content:flex-end; flex-shrink:0; }
.submit-btn {
  padding:10px 26px; background:var(--accent); color:#fff; font-weight:700;
  font-size:0.68rem; border:none; cursor:pointer; box-shadow:0 0 8px var(--accent-glow);
  border-radius:var(--card-radius);
}
.progress-bar {
  flex-shrink:0; height:32px; background:var(--card); border:2px solid var(--accent);
  border-radius:var(--panel-radius); display:flex; align-items:center; padding:0 14px;
  gap:8px; font-size:0.58rem;
}
.progress-fill { height:6px; background:var(--accent); border-radius:3px; transition:width 0.5s; }
@media (max-width:768px) {
  .main-wrapper { flex-direction:column; }
  .resize-handle-h { display:none; }
  .left-area, .right-area { width:100%!important; min-width:0; }
  .left-area { max-height:40%; }
  .right-area { flex:1; }
}
</style>
