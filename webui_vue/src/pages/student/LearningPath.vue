<template>
  <div class="learning-path-page">
    <main class="main-grid">

      <!-- 左侧面板：学生掌握水平 -->
      <section class="panel left-panel">
        <!-- 头部：学生信息 + 综合评分 -->
        <div class="student-header">
          <div class="student-info">
            <div class="student-avatar">{{ studentName[0] }}</div>
            <div>
              <h3 class="student-name">{{ studentName }}</h3>
              <p class="student-meta">{{ studentMajor }} · {{ studentGrade }} · 综合 {{ overallScore }}</p>
            </div>
          </div>
          <div class="score-circle">
            <span class="score-value">{{ overallScore }}</span>
            <span class="score-label">学情分</span>
          </div>
        </div>

        <!-- 技能雷达图 -->
        <div class="section-block">
          <div class="section-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
            </svg>
            <span>技能度推演雷达</span>
          </div>
          <div class="radar-wrapper">
            <svg class="radar-svg" viewBox="0 0 100 100">
              <!-- 外层六边形框架 -->
              <polygon points="50,10 85,30 85,70 50,90 15,70 15,30" fill="none" :stroke="gridStroke" stroke-width="0.8" />
              <polygon points="50,25 76,40 76,60 50,75 24,60 24,40" fill="none" :stroke="gridStroke" stroke-width="0.6" />
              <polygon points="50,40 67,50 67,60 50,70 33,60 33,50" fill="none" :stroke="gridStroke" stroke-width="0.6" />
              <!-- 轴线 -->
              <line x1="50" y1="10" x2="50" y2="90" :stroke="gridStroke" stroke-width="0.5" />
              <line x1="15" y1="30" x2="85" y2="70" :stroke="gridStroke" stroke-width="0.5" />
              <line x1="15" y1="70" x2="85" y2="30" :stroke="gridStroke" stroke-width="0.5" />
              <!-- 数据多边形 -->
              <polygon :points="radarDataPoints" :fill="accentColor" fill-opacity="0.06" :stroke="accentColor" stroke-width="1.2" />
            </svg>
            <!-- 雷达标签 -->
            <span class="radar-label top">{{ radarLabels[0] }}</span>
            <span class="radar-label bottom">{{ radarLabels[1] }}</span>
            <span class="radar-label right">{{ radarLabels[2] }}</span>
            <span class="radar-label left">{{ radarLabels[3] }}</span>
          </div>
        </div>

        <!-- 章节进度 -->
        <div class="section-block border-top">
          <div class="section-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
            </svg>
            <span>章节进度与批注</span>
          </div>
          <div class="progress-list">
            <div v-for="p in chapterProgress" :key="p.name" class="progress-item">
              <div class="progress-header">
                <span class="progress-name">{{ p.name }}</span>
                <span class="progress-pct" :style="{ color: accentColor }">{{ p.pct }}%</span>
              </div>
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: p.pct + '%', background: accentColor }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 薄弱知识点 -->
        <div class="section-block border-top">
          <div class="section-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <span>偏误薄弱知识点</span>
          </div>
          <div class="weak-list">
            <div v-for="w in weakPoints" :key="w.name" class="weak-item">
              <span class="weak-name">{{ w.name }}</span>
              <span class="weak-badge">偏离度 {{ w.deviation }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧面板 -->
      <section class="right-column">

        <!-- 学习路径阶段递进 -->
        <div class="panel path-panel">
          <div class="panel-title">
            <div class="title-bar"></div>
            <span>个性化学习路径 · 阶段递进</span>
          </div>
          <div class="path-stages">
            <div v-for="(s, i) in pathStages" :key="i"
                 class="stage-card"
                 :class="{ done: s.status === 'done', current: s.status === 'current', locked: s.status === 'locked' }">
              <div class="stage-left">
                <div class="stage-num" :class="s.status">
                  <template v-if="s.status === 'done'">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </template>
                  <template v-else-if="s.status === 'locked'">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                  </template>
                  <template v-else>{{ i + 1 }}</template>
                </div>
                <div class="stage-info">
                  <h4 class="stage-title">{{ s.title }}</h4>
                  <p class="stage-desc">{{ s.desc }}</p>
                </div>
              </div>
              <span v-if="s.status === 'done'" class="stage-tag done-tag">已完成 {{ s.progress }}%</span>
              <span v-else-if="s.status === 'current'" class="stage-tag current-tag">当前学练中</span>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lock-icon">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- 智能资源推荐 -->
        <div class="panel resource-panel">
          <div class="panel-title">
            <div class="title-bar"></div>
            <span>智能多模态资源推荐 · 基于因果弱项</span>
          </div>
          <div class="resource-list">
            <div v-for="r in resources" :key="r.title" class="resource-card" @click="handleResourceClick(r)">
              <div class="resource-header">
                <h4 class="resource-title">{{ r.title }}</h4>
                <span class="resource-type-badge" :class="r.typeClass">
                  <svg v-if="r.typeClass === 'video'" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  <svg v-else-if="r.typeClass === 'simulation'" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="M3 9h18"/>
                  </svg>
                  <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                  </svg>
                  <span>{{ r.type }}</span>
                </span>
              </div>
              <p class="resource-desc">{{ r.desc }}</p>
            </div>
          </div>
        </div>

      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

// ====== 学生数据 ======
const studentName = ref('张禾丰')
const studentMajor = ref('园艺技术')
const studentGrade = ref('大三')
const overallScore = ref(81.5)

// ====== 主题适配 ======
const currentTheme = ref('white')

function detectTheme() {
  if (document.body.classList.contains('dark')) return 'dark'
  if (document.body.classList.contains('green')) return 'green'
  return 'white'
}

const accentColor = computed(() => {
  if (currentTheme.value === 'dark') return '#ffffff'
  if (currentTheme.value === 'green') return '#526e5a'
  return '#121212'
})

const gridStroke = computed(() => {
  if (currentTheme.value === 'dark') return 'rgba(255,255,255,0.08)'
  return '#eef0ee'
})

// ====== 雷达图 ======
const radarLabels = ['植物生理', '因果解析', '综合规划', '土壤肥力']
const radarValues = ref([65, 70, 52, 58]) // 百分比

const radarDataPoints = computed(() => {
  // 六个顶点坐标 (从顶部顺时针)
  const vertices = [
    { x: 50, y: 10 }, // top
    { x: 85, y: 30 }, // top-right
    { x: 85, y: 70 }, // bottom-right
    { x: 50, y: 90 }, // bottom
    { x: 15, y: 70 }, // bottom-left
    { x: 15, y: 30 }, // top-left
  ]
  const center = { x: 50, y: 50 }
  const vals = radarValues.value
  // 映射到 6 个点
  return vertices.map((v, i) => {
    const pct = (vals[i] || 50) / 100
    const x = center.x + (v.x - center.x) * pct
    const y = center.y + (v.y - center.y) * pct
    return `${x},${y}`
  }).join(' ')
})

// ====== 章节进度 ======
const chapterProgress = ref([
  { name: '植物生理学基础', pct: 42 },
  { name: '土壤肥料学特征变量', pct: 58 },
  { name: '病虫害智能多维防治', pct: 78 },
])

// ====== 薄弱知识点 ======
const weakPoints = ref([
  { name: '光化作用光反应消融计算', deviation: 35 },
  { name: '土壤阴阳离子交换矩阵跨度', deviation: 40 },
])

// ====== 学习路径阶段 ======
const pathStages = ref([
  {
    title: '土壤基础知识域补完',
    desc: '土壤质地、结构重组、理化归因核验',
    status: 'done',
    progress: 90,
  },
  {
    title: '养分与施肥控制消融',
    desc: '植物养分吸收流转、稀土因子配比',
    status: 'current',
    progress: 58,
  },
  {
    title: '病虫害智能立体防治',
    desc: '前置条件：需攻坚通过节点 2 评估',
    status: 'locked',
    progress: 0,
  },
])

// ====== 推荐资源 ======
const resources = ref([
  {
    title: '光学作用动态树状模拟 · 光反应消融详解',
    desc: '针对你刚才在《个性化学伴》中暴露出的光反应阶段量子效率常微分公式混淆，推荐此消融拆解演示。',
    type: '视频',
    typeClass: 'video',
  },
  {
    title: '测土配方施肥技术 · 实操数字仿真终端',
    desc: '深度绑定左侧"土壤肥力"弱项指标，提供端侧离子交换常数交互推导实训。',
    type: '仿真',
    typeClass: 'simulation',
  },
  {
    title: '病虫害综合防治图谱 · 交互式知识树',
    desc: '基于你当前学习进度，提前预览下一阶段核心知识点结构与因果链路。',
    type: '阅读',
    typeClass: 'reading',
  },
])

function handleResourceClick(r) {
  // TODO: navigate to resource detail
  console.log('Resource clicked:', r.title)
}

// ====== 主题监听 ======
let observer = null

onMounted(() => {
  currentTheme.value = detectTheme()
  observer = new MutationObserver(() => {
    currentTheme.value = detectTheme()
  })
  observer.observe(document.body, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.learning-path-page {
  height: 100%;
  padding: 24px;
  overflow-y: auto;
}

.learning-path-page::-webkit-scrollbar { width: 4px; }
.learning-path-page::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.15);
  border-radius: 4px;
}

/* ====== Grid Layout ====== */
.main-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 20px;
  height: 100%;
}

/* ====== Panel Base ====== */
.panel {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-light, #f0f0f0);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.003);
  transition: border-color 0.25s ease;
}

/* ====== Left Panel ====== */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
}

.left-panel::-webkit-scrollbar { width: 3px; }
.left-panel::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 3px;
}

/* ====== Student Header ====== */
.student-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light, #f8f9f8);
  margin-bottom: 16px;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--border-light, #f4f4f4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary, #121212);
  flex-shrink: 0;
}

.student-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.student-meta {
  font-size: 11px;
  color: var(--text-muted, #999);
  margin-top: 2px;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.score-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 1px solid var(--border-light, rgba(18,18,18,0.1));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-root, #fafbfa);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  flex-shrink: 0;
}

.score-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  font-family: 'SF Mono', 'Menlo', monospace;
  line-height: 1;
}

.score-label {
  font-size: 9px;
  color: var(--text-muted, #999);
  margin-top: 2px;
}

/* ====== Section Block ====== */
.section-block {
  padding: 14px 0;
}

.section-block.border-top {
  border-top: 1px solid var(--border-light, #f8f9f8);
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.section-label svg {
  color: var(--text-muted, #999);
  flex-shrink: 0;
}

/* ====== Radar Chart ====== */
.radar-wrapper {
  position: relative;
  height: 200px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-root, #fafbfa);
  border-radius: 12px;
  padding: 12px;
}

.radar-svg {
  width: 160px;
  height: 160px;
}

.radar-label {
  position: absolute;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-primary, #121212);
}

.radar-label.top { top: 8px; }
.radar-label.bottom { bottom: 8px; }
.radar-label.right { right: 8px; top: 25%; }
.radar-label.left { left: 8px; top: 25%; }

/* ====== Progress ====== */
.progress-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-name {
  font-size: 11px;
  color: var(--text-muted, #999);
}

.progress-pct {
  font-size: 11px;
  font-weight: 700;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.progress-track {
  width: 100%;
  height: 4px;
  background: var(--border-light, #f4f4f4);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

/* ====== Weak Points ====== */
.weak-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.weak-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-root, #fdfbf7);
  border: 1px solid var(--border-light, #f5ebd3);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 11px;
  color: var(--text-secondary, #75684d);
}

.weak-name {
  font-weight: 500;
}

.weak-badge {
  font-size: 10px;
  font-weight: 700;
  font-family: 'SF Mono', 'Menlo', monospace;
  background: var(--border-light, #f5ebd3);
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

/* ====== Right Column ====== */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ====== Panel Title ====== */
.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.title-bar {
  width: 4px;
  height: 16px;
  background: var(--text-primary, #121212);
  border-radius: 4px;
  flex-shrink: 0;
}

/* ====== Path Stages ====== */
.path-stages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--border-light, #eef2ee);
  background: var(--bg-root, #fafbfa);
  transition: all 0.25s ease;
}

.stage-card.current {
  border-color: var(--accent-color, rgba(18,18,18,0.1));
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  background: var(--bg-card, #ffffff);
}

.stage-card.locked {
  opacity: 0.5;
  border-color: var(--border-light, #f5f5f5);
}

.stage-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.stage-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  background: var(--text-primary, #121212);
  color: #fff;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.stage-num.done {
  background: var(--text-primary, #121212);
}

.stage-num.current {
  background: var(--text-primary, #121212);
}

.stage-num.locked {
  background: var(--border-light, #e0e0e0);
  color: var(--text-muted, #999);
}

.stage-info {
  flex: 1;
  min-width: 0;
}

.stage-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.stage-desc {
  font-size: 11px;
  color: var(--text-muted, #999);
  margin-top: 2px;
}

.stage-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 8px;
  flex-shrink: 0;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.done-tag {
  background: var(--border-light, #f0f0f0);
  color: var(--text-muted, #999);
}

.current-tag {
  background: var(--bg-root, #fbf7ee);
  color: var(--text-secondary, #75684d);
  border: 1px solid var(--border-light, #f5ebd3);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.lock-icon {
  color: var(--border-light, #d0d0d0);
  flex-shrink: 0;
}

/* ====== Resources ====== */
.resource-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
}

.resource-list::-webkit-scrollbar { width: 3px; }
.resource-list::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 3px;
}

.resource-card {
  border: 1px solid var(--border-light, #f0f0f0);
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  background: var(--bg-card, #ffffff);
}

.resource-card:hover {
  border-color: var(--text-primary, #121212);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.resource-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.resource-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  flex: 1;
  min-width: 0;
  line-height: 1.4;
}

.resource-type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-light, #edf0ed);
  background: var(--bg-root, #fafbfa);
  color: var(--text-muted, #999);
  flex-shrink: 0;
  white-space: nowrap;
}

.resource-desc {
  font-size: 11px;
  color: var(--text-muted, #999);
  line-height: 1.5;
  margin-top: 8px;
}

/* ====== 暗色主题适配（纯中性灰，无紫色调） ====== */
body.dark .learning-path-page {
  background: #121212;
}

body.dark .panel {
  background: #1a1a1a;
  border-color: #2d2d2d;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

body.dark .student-header {
  border-bottom-color: #2d2d2d;
}

body.dark .student-avatar {
  background: #2d2d2d;
  color: #e5e5e5;
}

body.dark .student-name {
  color: #e5e5e5;
}

body.dark .student-meta {
  color: #777;
}

body.dark .score-circle {
  background: #242424;
  border-color: #3a3a3a;
}

body.dark .score-value {
  color: #e5e5e5;
}

body.dark .section-block.border-top {
  border-top-color: #2d2d2d;
}

body.dark .section-label {
  color: #e5e5e5;
}

body.dark .section-label svg {
  color: #777;
}

body.dark .radar-wrapper {
  background: #242424;
}

body.dark .radar-label {
  color: #c0c0c0;
}

body.dark .progress-name {
  color: #888;
}

body.dark .progress-track {
  background: #2d2d2d;
}

body.dark .weak-item {
  background: #242424;
  border-color: #2d2d2d;
  color: #b0b0b0;
}

body.dark .weak-badge {
  background: #2d2d2d;
  color: #d0d0d0;
}

body.dark .panel-title {
  color: #e5e5e5;
}

body.dark .title-bar {
  background: #ffffff;
}

body.dark .stage-card {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .stage-card.current {
  background: #1e1e1e;
  border-color: #ffffff;
  box-shadow: 0 2px 16px rgba(255,255,255,0.05);
}

body.dark .stage-num {
  background: #ffffff;
  color: #121212;
}

body.dark .stage-num.done {
  background: #ffffff;
  color: #121212;
}

body.dark .stage-num.current {
  background: #ffffff;
  color: #121212;
}

body.dark .stage-num.locked {
  background: #2d2d2d;
  color: #666;
}

body.dark .stage-title {
  color: #e5e5e5;
}

body.dark .stage-desc {
  color: #777;
}

body.dark .done-tag {
  background: #2d2d2d;
  color: #888;
}

body.dark .current-tag {
  background: #2a2a2a;
  border-color: #444;
  color: #d4ba8c;
}

body.dark .lock-icon {
  color: #555;
}

body.dark .resource-card {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .resource-card:hover {
  border-color: #ffffff;
  box-shadow: 0 2px 16px rgba(255,255,255,0.06);
}

body.dark .resource-title {
  color: #e5e5e5;
}

body.dark .resource-desc {
  color: #777;
}

body.dark .resource-type-badge {
  background: #2d2d2d;
  border-color: #3a3a3a;
  color: #aaa;
}

/* ====== 绿色主题适配 ====== */
body.green .learning-path-page {
  background: #f7f8f7;
}

body.green .panel {
  border-color: #dee2de;
}

body.green .student-header {
  border-bottom-color: #dee2de;
}

body.green .student-avatar {
  background: #e2e7e2;
  color: #2c332e;
}

body.green .score-circle {
  background: #edf0ed;
  border-color: #dee2de;
}

body.green .radar-wrapper {
  background: #edf0ed;
}

body.green .section-block.border-top {
  border-top-color: #dee2de;
}

body.green .stage-card {
  background: #f3f6f3;
  border-color: #dee2de;
}

body.green .stage-card.current {
  background: #ffffff;
  border-color: #526e5a;
}

body.green .stage-num {
  background: #526e5a;
}

body.green .stage-num.done {
  background: #526e5a;
}

body.green .stage-num.current {
  background: #526e5a;
}

body.green .stage-num.locked {
  background: #d6ded6;
  color: #8fa091;
}

body.green .weak-item {
  background: #f7f8f0;
  border-color: #d6ded6;
  color: #3b473d;
}

body.green .weak-badge {
  background: #d6ded6;
  color: #3b473d;
}

body.green .title-bar {
  background: #526e5a;
}

body.green .progress-fill {
  background: #526e5a !important;
}

body.green .progress-pct {
  color: #526e5a !important;
}

body.green .resource-card:hover {
  border-color: #526e5a;
}

body.green .done-tag {
  background: #e2e7e2;
  color: #556056;
}

body.green .current-tag {
  background: #f7f8f0;
  border-color: #d6ded6;
  color: #3b473d;
}
</style>
