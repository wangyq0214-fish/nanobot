<template>
<div class="research-results-page">
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="header-info">
      <h1 class="page-title">我的研究成果</h1>
      <p class="page-subtitle">所有已生成的学术研究、文献综述与开题方案 · 结论可追溯、论据可沉淀</p>
    </div>
    <button class="btn-create" @click="showCreateDialog = true">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 12h14"/><path d="M12 5v14"/>
      </svg>
      <span>新建研究课题</span>
    </button>
  </div>

  <!-- 研究成果卡片网格 -->
  <div class="results-grid">
    <div
      v-for="item in researchItems"
      :key="item.id"
      class="result-card"
      @click="openResearch(item)"
    >
      <!-- 卡片封面 -->
      <div class="card-cover" :style="{ background: item.coverColor }">
        <div class="cover-overlay"></div>
        <div class="cover-content">
          <div class="cover-brand">Aura Research Notebook</div>
          <div class="cover-title">{{ item.coverTitle }}</div>
        </div>
        <div class="cover-decoration"></div>
      </div>

      <!-- 卡片内容 -->
      <div class="card-body">
        <h2 class="card-title">{{ item.title }}</h2>
        <p class="card-desc">{{ item.description }}</p>

        <div class="card-footer">
          <div class="footer-time">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>{{ item.date }}</span>
          </div>
          <div class="footer-stats">
            <span class="stat-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 17H7A5 5 0 0 1 7 7h2"/><path d="M15 7h2a5 5 0 1 1 0 10h-2"/><line x1="8" x2="16" y1="12" y2="12"/>
              </svg>
              <b>{{ item.evidence }}</b> 论据
            </span>
            <span class="stat-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
              </svg>
              <b>{{ item.papers }}</b> 文献
            </span>
            <span class="stat-item" v-if="item.hasGraph">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 3v12"/><path d="M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M15 6a9 9 0 0 0-9 9"/><path d="M18 15v6"/><path d="M21 18h-6"/>
              </svg>
              图谱
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建卡片占位 -->
    <div class="result-card card-add" @click="showCreateDialog = true">
      <div class="add-content">
        <div class="add-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/><path d="M12 5v14"/>
          </svg>
        </div>
        <div class="add-text">新建研究课题</div>
        <div class="add-hint">开始一个新的学术探索旅程</div>
      </div>
    </div>
  </div>

  <!-- 创建对话框 -->
  <Teleport to="body">
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog-card">
        <div class="dialog-header">
          <h3>新建研究课题</h3>
          <button class="btn-close" @click="showCreateDialog = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label>课题名称</label>
            <input
              v-model="newResearch.title"
              type="text"
              placeholder="例如：基于 Transformer 的蛋白质结构预测方法综述"
            />
          </div>

          <div class="form-group">
            <label>研究方向</label>
            <select v-model="newResearch.direction">
              <option value="">请选择研究方向</option>
              <option value="ai">人工智能</option>
              <option value="biology">生物信息</option>
              <option value="medicine">医学影像</option>
              <option value="materials">材料科学</option>
              <option value="agriculture">农业科学</option>
              <option value="other">其他</option>
            </select>
          </div>

          <div class="form-group">
            <label>研究描述</label>
            <textarea
              v-model="newResearch.description"
              placeholder="简要描述您的研究目标和关注点..."
              rows="4"
            ></textarea>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn-cancel" @click="showCreateDialog = false">取消</button>
          <button class="btn-confirm" @click="createResearch" :disabled="!newResearch.title">
            创建课题
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showCreateDialog = ref(false)

const newResearch = reactive({
  title: '',
  direction: '',
  description: ''
})

// 示例数据
const researchItems = ref([
  {
    id: 1,
    title: '存算一体架构（PIM）在边缘端侧大模型部署中的能效演进与软硬件协同设计综述',
    coverTitle: '存算一体架构 (PIM) 在边缘大模型部署的能效演进综述报告',
    description: '基于 120 篇 IEEE/ACM 近三年顶会文献，对 SRAM、RRAM 介质在 Llama 类架构下的消融数据进行了高精度交叉验证...',
    date: '2026-06-26',
    evidence: 120,
    papers: 35,
    hasGraph: true,
    coverColor: '#4a5f4f'
  },
  {
    id: 2,
    title: '具身智能多模态大模型（VLM）在机械臂轨迹规划中的端侧控制决策延迟与鲁棒性多维比对报告',
    coverTitle: '具身智能多模态大模型(VLM)的端侧控制决策延迟对比研究',
    description: '对比 RT-1、RT-2 及最新开源架构在不同轻量化剪枝方案下，面对环境噪声时的控制指令输出延迟差距与因果链条。',
    date: '2026-06-20',
    evidence: 84,
    papers: 18,
    hasGraph: true,
    coverColor: '#354338'
  },
  {
    id: 3,
    title: '针对 3D 医学图像多目标分割任务中基于高级 Mamba 骨干网络（State Space Model）的消融实验性能指标深度验证',
    coverTitle: '医学图像多分割任务中基于 Mamba 架构的消融指标核验',
    description: '重组三项主流公开医学数据集，对纯注意力机制与选择性状态空间模型在长序列上下文显存占用层面的理论边界进行推演。',
    date: '2026-06-15',
    evidence: 96,
    papers: 42,
    hasGraph: true,
    coverColor: '#5b6a5e'
  }
])

function openResearch(item) {
  // 跳转到研究详情页或工作台
  router.push('/researcher/workspace')
}

function createResearch() {
  if (!newResearch.title) return

  // 添加新研究到列表
  const colors = ['#4a5f4f', '#354338', '#5b6a5e', '#6b7a6e', '#3d4f42']
  researchItems.value.unshift({
    id: Date.now(),
    title: newResearch.title,
    coverTitle: newResearch.title.substring(0, 30) + (newResearch.title.length > 30 ? '...' : ''),
    description: newResearch.description || '暂无描述',
    date: new Date().toISOString().split('T')[0],
    evidence: 0,
    papers: 0,
    hasGraph: false,
    coverColor: colors[Math.floor(Math.random() * colors.length)]
  })

  // 重置表单
  newResearch.title = ''
  newResearch.direction = ''
  newResearch.description = ''
  showCreateDialog.value = false
}
</script>

<style scoped>
.research-results-page {
  padding: 32px 40px;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 400;
  color: #121212;
  margin: 0;
}

.page-subtitle {
  font-size: 12px;
  color: #666666;
  letter-spacing: 0.5px;
  margin: 0;
}

.btn-create {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #121212;
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-create:hover {
  background: #333333;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 卡片网格 */
.results-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

/* 研究卡片 */
.result-card {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
}

.result-card:hover {
  border-color: #121212;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

/* 卡片封面 */
.card-cover {
  height: 176px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  background: #1a1a1a !important;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(0,0,0,0.2));
  opacity: 0.4;
}

.cover-decoration {
  position: absolute;
  right: -40px;
  bottom: -40px;
  width: 128px;
  height: 128px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  filter: blur(24px);
}

.cover-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cover-brand {
  font-family: monospace;
  font-size: 10px;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
}

.cover-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding: 0 16px;
}

/* 卡片内容 */
.card-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s ease;
}

.result-card:hover .card-title {
  color: #333333;
}

.card-desc {
  font-size: 11px;
  color: #999;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片底部 */
.card-footer {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.footer-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #999999;
}

.footer-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #999999;
}

.stat-item svg {
  color: #121212;
}

.stat-item b {
  color: #121212;
  font-weight: 600;
}

/* 新建卡片 */
.card-add {
  border: 2px dashed #eaeaea;
  background: transparent;
  min-height: 320px;
}

.card-add:hover {
  border-color: #121212;
  background: rgba(0, 0, 0, 0.02);
}

.add-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  padding: 40px;
}

.add-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f4f4f4;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #121212;
  transition: all 0.2s ease;
}

.card-add:hover .add-icon {
  background: #e8e8e8;
  transform: scale(1.05);
}

.add-text {
  font-size: 14px;
  font-weight: 600;
  color: #121212;
}

.add-hint {
  font-size: 12px;
  color: #999;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.dialog-card {
  background: white;
  border-radius: 20px;
  width: 480px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #121212;
}

.btn-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f4f4f4;
  color: #666666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #e8e8e8;
  color: #121212;
}

.dialog-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 14px;
  border: 1px solid #eaeaea;
  border-radius: 10px;
  font-size: 14px;
  color: #121212;
  background: #f8f8f8;
  outline: none;
  transition: all 0.2s ease;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #121212;
  background: white;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel {
  padding: 10px 20px;
  border: 1px solid #eaeaea;
  border-radius: 10px;
  background: white;
  color: #666666;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  border-color: #121212;
  color: #121212;
}

.btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  background: #121212;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-confirm:hover:not(:disabled) {
  background: #333333;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 1024px) {
  .results-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .research-results-page {
    padding: 20px 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .results-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== Green Theme ===== */
body.green .card-cover {
  background: #4a5f4f !important;
}

body.green .page-title {
  color: #1e2720;
}

body.green .page-subtitle {
  color: #717c72;
}

body.green .btn-create {
  background: #526e5a;
  box-shadow: 0 2px 8px rgba(82, 110, 90, 0.1);
}

body.green .btn-create:hover {
  background: #415848;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.2);
}

body.green .result-card {
  border-color: #e8ebe8;
  box-shadow: 0 4px 20px rgba(30, 39, 32, 0.01);
}

body.green .result-card:hover {
  border-color: #bad2be;
  box-shadow: 0 12px 30px rgba(82, 110, 90, 0.06);
}

body.green .card-title {
  color: #1e2720;
}

body.green .result-card:hover .card-title {
  color: #526e5a;
}

body.green .card-footer {
  border-top-color: #f0f3f0;
}

body.green .footer-time,
body.green .stat-item {
  color: #8fa091;
}

body.green .stat-item svg,
body.green .stat-item b {
  color: #526e5a;
}

body.green .card-add {
  border-color: #dee2de;
}

body.green .card-add:hover {
  border-color: #526e5a;
  background: rgba(82, 110, 90, 0.02);
}

body.green .add-icon {
  background: #f0f2f0;
  color: #526e5a;
}

body.green .card-add:hover .add-icon {
  background: #e4e7e4;
}

body.green .add-text {
  color: #1e2720;
}

body.green .dialog-header {
  border-bottom-color: #f0f3f0;
}

body.green .dialog-header h3 {
  color: #1e2720;
}

body.green .btn-close {
  background: #f0f2f0;
  color: #6b756c;
}

body.green .btn-close:hover {
  background: #e4e7e4;
  color: #1e2720;
}

body.green .form-group label {
  color: #2c332e;
}

body.green .form-group input,
body.green .form-group select,
body.green .form-group textarea {
  border-color: #dee2de;
  color: #1e2720;
  background: #f7f8f7;
}

body.green .form-group input:focus,
body.green .form-group select:focus,
body.green .form-group textarea:focus {
  border-color: #526e5a;
  box-shadow: 0 0 0 3px rgba(82, 110, 90, 0.1);
}

body.green .dialog-footer {
  border-top-color: #f0f3f0;
}

body.green .btn-cancel {
  border-color: #dee2de;
  color: #6b756c;
}

body.green .btn-cancel:hover {
  border-color: #526e5a;
  color: #526e5a;
}

body.green .btn-confirm {
  background: #526e5a;
}

body.green .btn-confirm:hover:not(:disabled) {
  background: #415848;
}

/* ===== Dark Theme ===== */
body.dark .research-results-page {
  background: #121212;
}

body.dark .page-title {
  color: #ffffff;
}

body.dark .page-subtitle {
  color: #999999;
}

body.dark .card-cover {
  background: #1a1a1a !important;
  border-bottom: 1px solid #2d2d2d;
}

body.dark .cover-overlay {
  background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(0,0,0,0.3));
}

body.dark .cover-brand {
  color: rgba(255,255,255,0.4);
}

body.dark .cover-title {
  color: rgba(255,255,255,0.8);
}

body.dark .card-body {
  background: #242424;
}

body.dark .card-title {
  color: #ffffff;
}

body.dark .result-card:hover .card-title {
  color: #b3b3b3;
}

body.dark .card-desc {
  color: #666666;
}

body.dark .card-footer {
  border-top-color: #2d2d2d;
}

body.dark .footer-time {
  color: #666666;
}

body.dark .stat-item {
  color: #666666;
}

body.dark .stat-item svg {
  color: #ffffff;
}

body.dark .stat-item b {
  color: #ffffff;
}

body.dark .card-add {
  border-color: #333333;
}

body.dark .card-add:hover {
  border-color: #ffffff;
  background: rgba(255,255,255,0.02);
}

body.dark .add-icon {
  background: #1a1a1a;
  color: #ffffff;
}

body.dark .card-add:hover .add-icon {
  background: #2d2d2d;
}

body.dark .add-text {
  color: #ffffff;
}

body.dark .add-hint {
  color: #666666;
}

body.dark .dialog-overlay {
  background: rgba(0,0,0,0.6);
}

body.dark .dialog-card {
  background: #242424;
}

body.dark .dialog-header {
  border-bottom-color: #2d2d2d;
}

body.dark .dialog-header h3 {
  color: #ffffff;
}

body.dark .btn-close {
  background: #1a1a1a;
  color: #999999;
}

body.dark .btn-close:hover {
  background: #2d2d2d;
  color: #ffffff;
}

body.dark .form-group label {
  color: #e5e5e5;
}

body.dark .form-group input,
body.dark .form-group select,
body.dark .form-group textarea {
  background: #1a1a1a;
  border-color: #333333;
  color: #e5e5e5;
}

body.dark .form-group input:focus,
body.dark .form-group select:focus,
body.dark .form-group textarea:focus {
  background: #242424;
  border-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(255,255,255,0.1);
}

body.dark .dialog-footer {
  border-top-color: #2d2d2d;
}

body.dark .btn-cancel {
  background: #1a1a1a;
  border-color: #333333;
  color: #b3b3b3;
}

body.dark .btn-cancel:hover {
  border-color: #ffffff;
  color: #ffffff;
}

body.dark .btn-confirm {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-confirm:hover:not(:disabled) {
  background: #e5e5e5;
}
</style>
