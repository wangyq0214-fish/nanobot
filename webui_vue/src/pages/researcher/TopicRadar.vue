<template>
<div class="topic-radar">
  <div class="radar-header">
    <h1 class="radar-title">前沿课题雷达</h1>
    <p class="radar-subtitle">将每一次学术探索转化为可复用的知识图谱谱系 —— 课题热度、文献密度、多源溯源与学科交叉持续追踪</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
        </svg>
      </div>
      <div class="stat-value">48</div>
      <div class="stat-label">追踪前沿课题</div>
      <p class="stat-desc">已有情报沉淀和知识建模的学术方向，覆盖跨学科视野。</p>
    </div>
    <div class="stat-card">
      <div class="stat-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>
        </svg>
      </div>
      <div class="stat-value">3,420</div>
      <div class="stat-label">收录核心论据</div>
      <p class="stat-desc">分布式智能体网联录入，平均每篇文献沉淀 14.6 条核心断言。</p>
    </div>
    <div class="stat-card">
      <div class="stat-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
        </svg>
      </div>
      <div class="stat-value">260</div>
      <div class="stat-label">提炼学术共识</div>
      <p class="stat-desc">经由多智能体交叉判定、去噪重组后输出的确定性结论总数。</p>
    </div>
    <div class="stat-card">
      <div class="stat-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>
        </svg>
      </div>
      <div class="stat-value">94%</div>
      <div class="stat-label">同行评议置信度</div>
      <p class="stat-desc">经由 ≥3 个独立顶会/顶刊来源相互引证的学术结论占比，真实可信。</p>
    </div>
  </div>

  <div class="efficiency-section">
    <div class="section-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>
      </svg>
      <span>科研闭环效能提升</span>
      <span class="section-hint">相比于传统纯人工检索文献的可量化科研效能跃升</span>
    </div>
    <div class="efficiency-grid">
      <div class="efficiency-card">
        <div class="eff-value">128 <span class="eff-unit">小时</span></div>
        <div class="eff-label">累计节约文献检索工时</div>
      </div>
      <div class="efficiency-card">
        <div class="eff-value">45% <span class="eff-trend">↑</span></div>
        <div class="eff-label">课题路径推荐精准度提升</div>
      </div>
      <div class="efficiency-card">
        <div class="eff-value">12<span class="eff-unit">x</span></div>
        <div class="eff-label">平均交叉学科知识图谱覆盖</div>
      </div>
      <div class="efficiency-card">
        <div class="eff-value">4.8<span class="eff-unit">M</span></div>
        <div class="eff-label">累计调度底座学术 Tokens 算力</div>
      </div>
    </div>
  </div>

  <div class="topics-section">
    <div class="section-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>
      </svg>
      <span>最新监测课题与课程演进概览</span>
      <span class="section-hint">每组方向均经多智能体一键探查</span>
    </div>
    <div class="topics-grid">
      <div class="topic-card" v-for="(topic, index) in topics" :key="index">
        <h4 class="topic-title">{{ topic.title }}</h4>
        <div class="topic-tags">
          <span class="tag" v-for="tag in topic.tags" :key="tag">{{ tag }}</span>
        </div>
        <div class="topic-stats">
          <span><b>{{ topic.evidence }}</b> 核心论据</span>
          <span><b>{{ topic.conclusions }}</b> 核心结论</span>
          <span :class="['confidence', topic.confidenceClass]">{{ topic.confidence }}</span>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
const topics = [
  {
    title: 'Cursor, GitHub Copilot, Windsurf, Replit, Trae 等新一代大模型 AI Coding Agent 研发范式演进与多仓联动框架分析',
    tags: ['Cursor', 'AI Coding', '多仓协同'],
    evidence: 155,
    conclusions: 8,
    confidence: '高置信度',
    confidenceClass: 'high'
  },
  {
    title: '大语言模型中高带宽显存（HBM3e）与 SRAM 存算一体（PIM）混合阵列能效边界消融测试与编译器软件协同优化',
    tags: ['HBM3e', 'PIM架构', '软硬件协同'],
    evidence: 94,
    conclusions: 5,
    confidence: '中高置信度',
    confidenceClass: 'medium'
  },
  {
    title: '具身智能机械臂在 3D 高斯泼溅 (3D Gaussian Splatting) 稠密场景重建下的空间实时控制延迟与开题方案评估',
    tags: ['3DGS', '具身智能', '控制延迟'],
    evidence: 210,
    conclusions: 12,
    confidence: '高置信度',
    confidenceClass: 'high'
  }
]
</script>

<style scoped>
.topic-radar {
  padding: 32px 40px;
  overflow-y: auto;
  height: 100%;
  background: #ffffff;
}

.radar-header {
  margin-bottom: 24px;
}

.radar-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 1.5rem;
  font-weight: 400;
  color: #121212;
  margin-bottom: 4px;
}

.radar-subtitle {
  font-size: 0.75rem;
  color: #666666;
  letter-spacing: 0.5px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.01);
}

.stat-icon {
  width: 28px;
  height: 28px;
  background: #f4f4f4;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: #121212;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #121212;
  letter-spacing: -0.5px;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #666666;
  margin-top: 4px;
  margin-bottom: 2px;
}

.stat-desc {
  font-size: 10px;
  color: #9ca3af;
  line-height: 1.4;
}

.efficiency-section {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.01);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #121212;
  margin-bottom: 16px;
}

.section-header svg {
  color: #121212;
}

.section-hint {
  font-size: 10px;
  color: #9ca3af;
  font-weight: 400;
  margin-left: 8px;
}

.efficiency-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.efficiency-card {
  padding: 12px;
  background: #f8f8f8;
  border-radius: 12px;
  border: 1px solid #eaeaea;
}

.eff-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #121212;
}

.eff-unit {
  font-size: 0.75rem;
  font-weight: 400;
  color: #9ca3af;
}

.eff-trend {
  font-size: 0.75rem;
  font-weight: 400;
  color: #10b981;
}

.eff-label {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 2px;
}

.topics-section {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.01);
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.topic-card {
  border: 1px solid #eaeaea;
  background: #fcfcfc;
  padding: 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  transition: border-color 0.2s;
}

.topic-card:hover {
  border-color: #121212;
}

.topic-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #121212;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
  transition: color 0.2s;
}

.topic-card:hover .topic-title {
  color: #121212;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.tag {
  font-size: 9px;
  padding: 2px 6px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
}

.topic-stats {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10px;
  color: #999999;
}

.topic-stats b {
  font-weight: 600;
}

.confidence {
  font-weight: 500;
}

.confidence.high {
  color: #121212;
}

.confidence.medium {
  color: #d97706;
}

/* ===== Green Theme ===== */
body.green .topic-radar {
  background: linear-gradient(to bottom, #f3f6f3, #f7f8f7, #fafbfa);
}

body.green .radar-title {
  color: #1e2720;
}

body.green .radar-subtitle {
  color: #717c72;
}

body.green .stat-card {
  border-color: #e8ebe8;
  box-shadow: 0 2px 10px rgba(30,39,32,0.01);
}

body.green .stat-icon {
  background: #f2f4f2;
  color: #526e5a;
}

body.green .stat-value {
  color: #1e2720;
}

body.green .stat-label {
  color: #4a554b;
}

body.green .efficiency-section {
  border-color: #e8ebe8;
  box-shadow: 0 2px 12px rgba(30,39,32,0.01);
}

body.green .section-header {
  color: #1e2720;
}

body.green .section-header svg {
  color: #526e5a;
}

body.green .efficiency-card {
  background: #f8f9f8;
  border-color: #edf1ed;
}

body.green .eff-value {
  color: #1e2720;
}

body.green .topics-section {
  border-color: #e8ebe8;
  box-shadow: 0 2px 12px rgba(30,39,32,0.01);
}

body.green .topic-card {
  border-color: #edf1ed;
  background: #fdfdfd;
}

body.green .topic-card:hover {
  border-color: #bad2be;
}

body.green .topic-title {
  color: #1e2720;
}

body.green .topic-card:hover .topic-title {
  color: #526e5a;
}

body.green .tag {
  background: #f3f4f6;
  color: #6b7280;
}

body.green .topic-stats {
  border-top-color: #f3f6f3;
  color: #8fa091;
}

body.green .confidence.high {
  color: #526e5a;
}

body.green .stat-card {
  border-color: #e8ebe8;
}

body.green .efficiency-section {
  border-color: #e8ebe8;
}

body.green .efficiency-card {
  border-color: #edf1ed;
}

body.green .topics-section {
  border-color: #e8ebe8;
}

body.green .topic-card {
  border-color: #edf1ed;
}

body.green .topic-card:hover {
  border-color: #bad2be;
}

body.green .topic-stats {
  border-top-color: #f3f6f3;
}

/* ===== Dark Theme ===== */
body.dark .topic-radar {
  background: linear-gradient(to bottom, #141414, #121212, #0f0f0f);
}

body.dark .radar-title {
  color: #ffffff;
}

body.dark .radar-subtitle {
  color: #999999;
}

body.dark .stat-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

body.dark .stat-icon {
  background: #1a1a1a;
  color: #ffffff;
}

body.dark .stat-value {
  color: #ffffff;
}

body.dark .stat-label {
  color: #b3b3b3;
}

body.dark .stat-desc {
  color: #666666;
}

body.dark .efficiency-section {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

body.dark .section-header {
  color: #ffffff;
}

body.dark .section-header svg {
  color: #ffffff;
}

body.dark .section-hint {
  color: #666666;
}

body.dark .efficiency-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .eff-value {
  color: #ffffff;
}

body.dark .eff-unit {
  color: #666666;
}

body.dark .eff-trend {
  color: #10b981;
}

body.dark .eff-label {
  color: #666666;
}

body.dark .topics-section {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

body.dark .topic-card {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .topic-card:hover {
  border-color: #444444;
}

body.dark .topic-title {
  color: #ffffff;
}

body.dark .topic-card:hover .topic-title {
  color: #b3b3b3;
}

body.dark .tag {
  background: #2d2d2d;
  color: #b3b3b3;
}

body.dark .topic-stats {
  border-top-color: #2d2d2d;
  color: #999999;
}

body.dark .confidence.high {
  color: #ffffff;
}
</style>
