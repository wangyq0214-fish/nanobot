<template>
  <div class="tool-bench">
    <!-- Landing: tool grid (no active tool) -->
    <div v-if="!activeTool" class="landing">
      <div class="landing-inner">
        <div class="landing-header">
          <h1 class="landing-title">AI 学术工具台</h1>
          <p class="landing-subtitle">专为学生、导师及独立研究员量身打造的多模态轻量化工具矩阵</p>
        </div>

        <div class="tool-grid">
          <!-- Tool 1: Data Analysis -->
          <div class="tool-card" @click="activeTool = 'data'">
            <div class="tool-card-body">
              <div class="tool-icon-wrap">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>
                </svg>
              </div>
              <h3 class="tool-card-title">数据图谱分析</h3>
              <p class="tool-card-desc">一键导入测产或消融矩阵，自动渲染散点谱系与三线核验矩阵。</p>
            </div>
            <div class="tool-card-footer">
              <span>适用：全员 · 实验实证</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Data Analysis tool (embeds DataLab) -->
    <div v-if="activeTool === 'data'" class="tool-active">
      <DataLab @back="activeTool = null" />
    </div>

    <div v-if="false" class="placeholder-view">
      <button class="back-btn" @click="activeTool = null">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
        <span>返回工具选单</span>
      </button>
      <div class="placeholder-content">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
          <path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        </svg>
        <h3 class="placeholder-title">版面分割 OCR 解析层已挂载</h3>
        <p class="placeholder-desc">支持将 PDF 截图一键转化为排版对齐的标准 LaTeX 公式块与 JSON 键值对</p>
      </div>
    </div>

    <div v-if="false" class="placeholder-view">
      <button class="back-btn" @click="activeTool = null">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
        <span>返回工具选单</span>
      </button>
      <div class="placeholder-content">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
          <polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>
        </svg>
        <h3 class="placeholder-title">Pyodide 浏览器沙箱终端</h3>
        <p class="placeholder-desc">在浏览器中直接运行 Python 脚本，无需后端算力支持，即将上线</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DataLab from './DataLab.vue'

const activeTool = ref(null)
</script>

<style scoped>
.tool-bench {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ===== Landing ===== */
.landing {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow-y: auto;
}

.landing-inner {
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
  padding: 48px 32px;
}

.landing-header {
  text-align: center;
  margin-bottom: 40px;
}

.landing-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 400;
  color: #121212;
  letter-spacing: 2px;
  margin: 0 0 8px;
}

.landing-subtitle {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

/* ===== Tool Grid ===== */
.tool-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.tool-card {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.005);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 160px;
  transition: all 0.2s ease;
}

.tool-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
  border-color: #121212;
}

.tool-card-body {
  display: flex;
  flex-direction: column;
}

.tool-icon-wrap {
  width: 32px;
  height: 32px;
  background: #f4f4f4;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: #121212;
  transition: background 0.2s;
}

.tool-card:hover .tool-icon-wrap {
  background: #f0f0f0;
}

.tool-card-title {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  margin: 0 0 4px;
}

.tool-card-desc {
  font-size: 11px;
  color: #9ca3af;
  line-height: 1.5;
  margin: 0;
}

.tool-card-footer {
  font-size: 9px;
  color: #666666;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ===== Active tool view ===== */
.tool-active {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ===== Placeholder ===== */
.placeholder-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
}

.back-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-bottom: 24px;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #121212;
}

.placeholder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  opacity: 0.6;
}

.placeholder-icon {
  color: #121212;
  margin-bottom: 12px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.placeholder-title {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  margin: 0 0 4px;
}

.placeholder-desc {
  font-size: 10px;
  color: #9ca3af;
  margin: 0;
}

/* ===== Dark Theme ===== */
body.dark .landing-title {
  color: #ffffff;
}

body.dark .landing-subtitle {
  color: #666666;
}

body.dark .tool-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

body.dark .tool-card:hover {
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  border-color: #444444;
}

body.dark .tool-icon-wrap {
  background: #1a1a1a;
  color: #ffffff;
}

body.dark .tool-card:hover .tool-icon-wrap {
  background: #2d2d2d;
}

body.dark .tool-card-title {
  color: #ffffff;
}

body.dark .tool-card-desc {
  color: #999999;
}

body.dark .tool-card-footer {
  color: #b3b3b3;
}

body.dark .back-btn {
  color: #999999;
}

body.dark .back-btn:hover {
  color: #ffffff;
}

body.dark .placeholder-icon {
  color: #ffffff;
}

body.dark .placeholder-title {
  color: #ffffff;
}

body.dark .placeholder-desc {
  color: #999999;
}
</style>
