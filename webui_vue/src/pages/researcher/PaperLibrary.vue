<template>
<div class="knowledge-base-page">
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="header-left">
      <div class="header-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
        </svg>
      </div>
      <div class="header-info">
        <h1 class="page-title">结构化知识库</h1>
        <p class="page-subtitle">从各项研究课题中抽取的关键论据 · 每条核心结论均可一键追溯至论文原始出处</p>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn-upload" @click="showUpload = !showUpload">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
        </svg>
        <span>上传 PDF</span>
      </button>
    </div>
  </div>

  <!-- 上传区域 -->
  <div v-if="showUpload" class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <span class="progress-text">{{ uploadProgress }}%</span>
    </div>
    <div v-else class="upload-content">
      <div class="upload-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>
        </svg>
      </div>
      <div class="upload-text">点击选择或拖拽 PDF 文件到此处</div>
      <div class="upload-hint">支持 .pdf 格式</div>
    </div>
    <input type="file" ref="fileInput" accept=".pdf" @change="onFileChange" style="display:none" />
  </div>

  <!-- 搜索和筛选 -->
  <div class="search-section">
    <div class="search-box">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
      <input
        type="text"
        v-model="searchText"
        placeholder="搜索知识库内容、核心论据或文献标签..."
      />
    </div>
    <div class="filter-tabs">
      <button
        class="filter-tab"
        :class="{ active: viewMode === 'papers' }"
        @click="viewMode = 'papers'"
      >
        全部 ({{ papers.length }})
      </button>
      <button
        class="filter-tab"
        :class="{ active: viewMode === 'knowledge' }"
        @click="viewMode = 'knowledge'"
      >
        精选摘录 ({{ knowledgeItems.length }})
      </button>
    </div>
  </div>

  <!-- 错误提示 -->
  <div v-if="error" class="error-banner">{{ error }}</div>

  <!-- 论文视图 -->
  <template v-if="viewMode === 'papers'">
    <!-- 论文网格 -->
    <div v-if="filteredPapers.length > 0" class="paper-grid">
      <div
        v-for="paper in filteredPapers"
        :key="paper.id"
        class="paper-card"
      >
        <div class="card-cover" :style="{ background: getCoverColor(paper.id) }">
          <div class="cover-overlay"></div>
          <div class="cover-content">
            <div class="cover-brand">Research Notebook</div>
            <div class="cover-title">{{ paper.title?.substring(0, 40) }}{{ paper.title?.length > 40 ? '...' : '' }}</div>
          </div>
        </div>

        <div class="card-body" @click="viewPaper(paper)">
          <h3 class="card-title">{{ paper.title }}</h3>
          <div class="card-authors" v-if="paper.authors">{{ paper.authors }}</div>
          <div class="card-meta">
            <span v-if="paper.pageCount" class="meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/></svg>
              {{ paper.pageCount }} 页
            </span>
            <span v-if="paper.year" class="meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
              {{ paper.year }}
            </span>
            <span v-if="paper.source" class="meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
              {{ paper.source }}
            </span>
          </div>
          <div class="card-tags" v-if="paper.tags?.length">
            <span v-for="tag in paper.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>

        <div class="card-footer">
          <div class="footer-left">
            <button
              class="btn-fav"
              :class="{ active: paper.isFavorite }"
              @click.stop="doToggleFavorite(paper.id)"
            >
              <svg v-if="paper.isFavorite" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </button>
            <span class="time">{{ formatTime(paper.createdAt) }}</span>
          </div>
          <div class="footer-right">
            <button class="btn-summary" @click.stop="showAiSummary(paper)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
              AI 摘要
            </button>
            <button class="btn-delete" @click.stop="confirmDelete(paper)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && papers.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
        </svg>
      </div>
      <div class="empty-text">论文库为空</div>
      <div class="empty-hint">上传 PDF 文件或从搜索页面导入论文</div>
    </div>

    <!-- 无搜索结果 -->
    <div v-if="!loading && papers.length > 0 && filteredPapers.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </div>
      <div class="empty-text">未找到匹配的论文</div>
      <div class="empty-hint">请尝试不同的搜索词</div>
    </div>
  </template>

  <!-- 知识摘录视图 -->
  <template v-if="viewMode === 'knowledge'">
    <div class="knowledge-list">
      <div
        v-for="item in knowledgeItems"
        :key="item.id"
        class="knowledge-card"
      >
        <div class="knowledge-type" :class="item.type">
          <svg v-if="item.type === 'core'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
          <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
          <span>{{ item.typeLabel }}</span>
        </div>

        <div class="knowledge-content">
          <div class="content-border"></div>
          <p class="content-text">{{ item.content }}</p>
        </div>

        <div class="knowledge-source" v-if="item.source">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/></svg>
          <span>{{ item.source }}</span>
        </div>

        <div class="knowledge-tags">
          <span v-for="tag in item.tags" :key="tag" class="knowledge-tag">{{ tag }}</span>
        </div>
      </div>

      <!-- 加载更多提示 -->
      <div class="load-more-hint">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        <span>仅展示近期高频引用段落 · 完整论据请访问原始研究课题</span>
      </div>
    </div>
  </template>

  <!-- 删除确认弹窗 -->
  <Teleport to="body">
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal-card">
        <h3>确认删除</h3>
        <p>确定要删除论文「{{ deleteTarget.title }}」吗？此操作不可撤销。</p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="deleteTarget = null">取消</button>
          <button class="btn-confirm-delete" @click="doDelete">删除</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- AI 摘要弹窗 -->
  <Teleport to="body">
    <div v-if="summaryTarget" class="modal-overlay" @click.self="summaryTarget = null">
      <div class="modal-card summary-modal">
        <div class="summary-header">
          <h3>AI 摘要</h3>
          <button class="btn-close" @click="summaryTarget = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <div class="summary-title">{{ summaryTarget.title }}</div>
        <div class="summary-body">
          <div v-if="summaryLoading" class="summary-loading">
            <div class="spinner"></div>
            <span>AI 正在分析论文，请稍候...</span>
          </div>
          <div v-else-if="summaryError && !summaryContent" class="summary-error">
            {{ summaryError }}
          </div>
          <div v-else class="summary-content" v-html="renderMarkdown(summaryContent)"></div>
        </div>
        <div v-if="summaryError && summaryContent" class="summary-warning">
          ⚠️ {{ summaryError }}
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePaperLibrary } from '../../composables/usePaperLibrary.js'
import { useGateway } from '../../composables/useGateway.js'

const router = useRouter()
const {
  loading, error, papers, uploading, uploadProgress,
  fetchPapers, uploadPaper, deletePaper, toggleFavorite
} = usePaperLibrary()

const searchText = ref('')
const showUpload = ref(false)
const fileInput = ref(null)
const deleteTarget = ref(null)
const viewMode = ref('papers') // 'papers' | 'knowledge'

// AI summary state
const summaryTarget = ref(null)
const summaryContent = ref('')
const summaryLoading = ref(false)
const summaryError = ref('')

// 知识摘录示例数据
const knowledgeItems = ref([
  {
    id: 1,
    type: 'core',
    typeLabel: '核心数据论据',
    content: '经软硬件交叉验证表明，基于 RRAM 介质的存算一体阵列在部署 7B 规模的 Llama 类矩阵乘法时，整体吞吐量相比传统高带宽显存（HBM2e）方案可提升近 4.2 倍。在端侧处于极端低功耗限制（功率 < 15W）的场景下，其能效比保持在 28.4 TOPS/W，成功规避了传统的冯·诺依曼架构显存瓶颈带来的延迟损耗。',
    source: '存算一体架构（PIM）在边缘端侧大模型部署中的能效演进与软硬件协同设计综述.pdf',
    tags: ['RRAM 介质', 'Llama 架构', '能效消融比对', '冯·诺依曼瓶颈']
  },
  {
    id: 2,
    type: 'method',
    typeLabel: '方法论节点',
    content: '在 SRAM 阵列权重映射阶段，采用分级流水线量化（Block-wise Quantization）可以大幅度消除非线性 ADC 引入的溢出误差，使 INT4 精度的激活损耗逼近 FP16 的基准水平。',
    source: '存算一体架构（PIM）在边缘端侧大模型部署中的能效演进与软硬件协同设计综述.pdf',
    tags: ['SRAM 阵列', '分级流水线量化', 'ADC 误差修正']
  },
  {
    id: 3,
    type: 'core',
    typeLabel: '核心数据论据',
    content: '在机械臂轨迹规划任务中，RT-2 架构在轻量化剪枝 50% 后，面对环境噪声时的控制指令输出延迟仅增加 12ms，而 RT-1 架构在相同条件下延迟增加了 47ms。这表明基于 VLM 的架构在端侧部署时具有更好的鲁棒性。',
    source: '具身智能多模态大模型（VLM）的端侧控制决策延迟对比研究.pdf',
    tags: ['RT-2 架构', '轻量化剪枝', '控制延迟', '鲁棒性']
  },
  {
    id: 4,
    type: 'method',
    typeLabel: '方法论节点',
    content: '在 3D 医学图像分割任务中，基于 Mamba 架构的选择性状态空间模型在处理长序列时，显存占用仅为纯注意力机制的 1/3，同时保持了相当的分割精度。这一优势在处理高分辨率体积数据时尤为明显。',
    source: '医学图像多分割任务中基于 Mamba 架构的消融指标核验.pdf',
    tags: ['Mamba 架构', '状态空间模型', '显存优化', '医学图像分割']
  }
])

const filteredPapers = computed(() => {
  if (!searchText.value.trim()) return papers.value
  const q = searchText.value.toLowerCase()
  return papers.value.filter(p =>
    (p.title || '').toLowerCase().includes(q) ||
    (p.authors || '').toLowerCase().includes(q) ||
    (p.fileName || '').toLowerCase().includes(q)
  )
})

onMounted(() => {
  fetchPapers()
})

function getCoverColor(id) {
  const colors = ['#4a5f4f', '#354338', '#5b6a5e', '#6b7a6e', '#3d4f42']
  return colors[id % colors.length]
}

function triggerUpload() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  await uploadPaper(file)
  e.target.value = ''
}

async function onDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  await uploadPaper(file)
}

function viewPaper(paper) {
  router.push(`/researcher/paper/${paper.id}`)
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/<\/li><br>/g, '</li>')
    .replace(/^(.+)$/gm, (m) => m.startsWith('<') ? m : m)
}

async function showAiSummary(paper) {
  summaryTarget.value = paper
  summaryContent.value = ''
  summaryError.value = ''
  summaryLoading.value = true

  if (paper.aiSummary) {
    summaryContent.value = paper.aiSummary
    summaryLoading.value = false
    return
  }

  try {
    const { sendAiPaperSummary } = useGateway()
    const result = await sendAiPaperSummary(paper.id)
    summaryContent.value = result.summary || ''
    if (result.error) {
      summaryError.value = result.error
    }
    if (result.summary) {
      paper.aiSummary = result.summary
    }
  } catch (err) {
    summaryError.value = err.message || 'AI 摘要生成失败'
  } finally {
    summaryLoading.value = false
  }
}

async function doToggleFavorite(paperId) {
  await toggleFavorite(paperId)
}

function confirmDelete(paper) {
  deleteTarget.value = paper
}

async function doDelete() {
  if (!deleteTarget.value) return
  await deletePaper(deleteTarget.value.id)
  deleteTarget.value = null
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap');

.knowledge-base-page {
  padding: 32px 40px;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: #e8e8e8;
  border: 1px solid #d6ded6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #121212;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 20px;
  font-weight: 400;
  color: #121212;
  margin: 0;
}

.page-subtitle {
  font-size: 12px;
  color: #666666;
  margin: 0;
}

.btn-upload {
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
}

.btn-upload:hover {
  background: #333333;
}

/* 上传区域 */
.upload-area {
  margin-bottom: 24px;
  padding: 32px;
  border: 2px dashed #dee2de;
  border-radius: 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.upload-area:hover {
  border-color: #121212;
  background: #f8f8f8;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  color: #121212;
  margin-bottom: 4px;
}

.upload-text {
  font-size: 14px;
  color: #121212;
}

.upload-hint {
  font-size: 12px;
  color: #999;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
}

.progress-bar {
  width: 200px;
  height: 6px;
  background: #e8e8e8;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #121212;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
}

/* 搜索和筛选 */
.search-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  border: 1px solid #dee3de;
  border-radius: 12px;
  padding: 10px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01);
  transition: all 0.2s ease;
}

.search-box:focus-within {
  border-color: #121212;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.search-box svg {
  color: #999999;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: #121212;
  background: transparent;
  font-family: inherit;
  letter-spacing: 0.5px;
}

.search-box input::placeholder {
  color: #999999;
}

.filter-tabs {
  display: flex;
  gap: 6px;
}

.filter-tab {
  padding: 10px 16px;
  border: 1px solid #dee3de;
  border-radius: 12px;
  background: white;
  font-size: 13px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-tab:hover {
  background: #f0f0f0;
}

.filter-tab.active {
  background: #121212;
  color: white;
  border-color: #121212;
}

/* 错误提示 */
.error-banner {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  font-size: 13px;
}

/* 论文网格 */
.paper-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.paper-card {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.01);
}

.paper-card:hover {
  border-color: #121212;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

/* 卡片封面 */
.card-cover {
  height: 120px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  text-align: center;
  background: #1a1a1a !important;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(0,0,0,0.2));
  opacity: 0.4;
}

.cover-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cover-brand {
  font-family: monospace;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
}

.cover-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片内容 */
.card-body {
  padding: 14px;
  cursor: pointer;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: #121212;
  margin: 0 0 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s ease;
  letter-spacing: 0.5px;
}

.paper-card:hover .card-title {
  color: #121212;
}

.card-authors {
  font-size: 12px;
  color: #666666;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #999999;
}

.meta-item svg {
  color: #121212;
}

.card-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  background: #f4f4f4;
  color: #666666;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  border: 1px solid #e2e7e2;
}

/* 卡片底部 */
.card-footer {
  padding: 12px 14px;
  border-top: 1px solid #f0f3f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-fav {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  color: #999;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-fav:hover {
  background: #f4f4f4;
}

.btn-fav.active {
  color: #f59e0b;
}

.time {
  font-size: 11px;
  color: #999;
}

.btn-summary {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid #526e5a;
  color: #121212;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-summary:hover {
  background: #121212;
  color: white;
}

.btn-delete {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  color: #999;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-delete:hover {
  background: #fef2f2;
  color: #ef4444;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  color: #e0e0e0;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #121212;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 13px;
  color: #999;
}

/* 知识摘录列表 */
.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
}

.knowledge-card {
  background: white;
  border: 1px solid #edf1ed;
  border-radius: 16px;
  padding: 20px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.01);
}

.knowledge-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.03);
}

.knowledge-type {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 14px;
}

.knowledge-type.core {
  background: #fbf7ee;
  color: #cda052;
  border: 1px solid #f5ebd3;
}

.knowledge-type.method {
  background: #f0f0f0;
  color: #121212;
  border: 1px solid #e2eae2;
}

.knowledge-content {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.content-border {
  width: 2px;
  background: #bad2be;
  border-radius: 1px;
  flex-shrink: 0;
}

.content-text {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 14px;
  line-height: 1.7;
  color: #333333;
  margin: 0;
  letter-spacing: 0.5px;
}

.knowledge-source {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #666666;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: #f8f8f8;
  border-radius: 6px;
}

.knowledge-source svg {
  color: #121212;
  flex-shrink: 0;
}

.knowledge-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.knowledge-tag {
  background: #f4f4f4;
  color: #666666;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 10px;
  border: 1px solid #e2e7e2;
}

/* 加载更多提示 */
.load-more-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #999;
  font-size: 12px;
}

.load-more-hint svg {
  color: #e0e0e0;
}

/* 弹窗 */
.modal-overlay {
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

.modal-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-card h3 {
  margin: 0 0 12px;
  color: #121212;
  font-size: 16px;
}

.modal-card p {
  color: #666666;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 20px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm-delete {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background: #f4f4f4;
  color: #666666;
}

.btn-cancel:hover {
  background: #e4e7e4;
}

.btn-confirm-delete {
  background: #ef4444;
  color: white;
}

.btn-confirm-delete:hover {
  background: #dc2626;
}

/* AI 摘要弹窗 */
.summary-modal {
  max-width: 700px;
  width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-header h3 {
  margin: 0;
  font-size: 18px;
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
  background: #e4e7e4;
  color: #121212;
}

.summary-title {
  font-size: 14px;
  color: #666666;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #edf1ed;
  line-height: 1.5;
}

.summary-body {
  flex: 1;
  overflow-y: auto;
  min-height: 120px;
}

.summary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: #666666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e4eae4;
  border-top-color: #121212;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.summary-error {
  padding: 20px;
  text-align: center;
  color: #ef4444;
}

.summary-content {
  font-size: 14px;
  line-height: 1.8;
  color: #121212;
}

.summary-content :deep(h3) {
  font-size: 15px;
  margin: 16px 0 8px;
  color: #121212;
}

.summary-content :deep(h4) {
  font-size: 14px;
  margin: 12px 0 6px;
  color: #121212;
}

.summary-content :deep(li) {
  margin-left: 16px;
  margin-bottom: 4px;
}

.summary-content :deep(code) {
  background: #f4f4f4;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}

.summary-warning {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fef3cd;
  border-radius: 8px;
  font-size: 13px;
  color: #856404;
}

/* 响应式 */
@media (max-width: 1024px) {
  .paper-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .knowledge-base-page {
    padding: 20px 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .search-section {
    flex-direction: column;
  }

  .filter-tabs {
    width: 100%;
  }

  .filter-tab {
    flex: 1;
    text-align: center;
  }

  .paper-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== Green Theme ===== */
body.green .card-cover {
  background: #4a5f4f !important;
}

body.green .header-icon {
  background: #e4eae4;
  border-color: #d6ded6;
  color: #526e5a;
}

body.green .page-title {
  color: #1e2720;
}

body.green .page-subtitle {
  color: #717c72;
}

body.green .btn-upload {
  background: #526e5a;
}

body.green .btn-upload:hover {
  background: #415848;
}

body.green .upload-area {
  border-color: #dee2de;
}

body.green .upload-area:hover {
  border-color: #526e5a;
  background: #f7f8f7;
}

body.green .upload-icon {
  color: #526e5a;
}

body.green .upload-text {
  color: #2c332e;
}

body.green .progress-bar {
  background: #e4eae4;
}

body.green .progress-fill {
  background: #526e5a;
}

body.green .progress-text {
  color: #526e5a;
}

body.green .search-box {
  border-color: #dee3de;
}

body.green .search-box:focus-within {
  border-color: #bad2be;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.04);
}

body.green .search-box svg {
  color: #9da79e;
}

body.green .search-box input {
  color: #1e2720;
}

body.green .search-box input::placeholder {
  color: #9da79e;
}

body.green .filter-tab {
  border-color: #dee3de;
  color: #556056;
}

body.green .filter-tab:hover {
  background: #edf0ed;
}

body.green .filter-tab.active {
  background: #526e5a;
  color: white;
  border-color: #526e5a;
}

body.green .paper-card {
  border-color: #e8ebe8;
  box-shadow: 0 4px 16px rgba(30, 39, 32, 0.01);
}

body.green .paper-card:hover {
  border-color: #bad2be;
  box-shadow: 0 8px 24px rgba(82, 110, 90, 0.06);
}

body.green .card-title {
  color: #1e2720;
}

body.green .paper-card:hover .card-title {
  color: #526e5a;
}

body.green .card-authors {
  color: #717c72;
}

body.green .meta-item {
  color: #8fa091;
}

body.green .meta-item svg {
  color: #526e5a;
}

body.green .tag {
  background: #f2f4f2;
  color: #556056;
  border-color: #e2e7e2;
}

body.green .card-footer {
  border-top-color: #f0f3f0;
}

body.green .btn-fav:hover {
  background: #f0f2f0;
}

body.green .btn-summary {
  border-color: #526e5a;
  color: #526e5a;
}

body.green .btn-summary:hover {
  background: #526e5a;
}

body.green .empty-icon {
  color: #cbd2cb;
}

body.green .empty-text {
  color: #1e2720;
}

body.green .knowledge-card {
  border-color: #edf1ed;
  box-shadow: 0 4px 16px rgba(30, 39, 32, 0.01);
}

body.green .knowledge-card:hover {
  box-shadow: 0 6px 20px rgba(82, 110, 90, 0.03);
}

body.green .knowledge-type.method {
  background: #eef3ee;
  color: #526e5a;
  border-color: #e2eae2;
}

body.green .content-border {
  background: #bad2be;
}

body.green .content-text {
  color: #3b473d;
}

body.green .knowledge-source {
  color: #717c72;
  background: #f7f8f7;
}

body.green .knowledge-source svg {
  color: #526e5a;
}

body.green .knowledge-tag {
  background: #f2f4f2;
  color: #556056;
  border-color: #e2e7e2;
}

body.green .load-more-hint svg {
  color: #cbd2cb;
}

body.green .modal-card h3 {
  color: #1e2720;
}

body.green .modal-card p {
  color: #556056;
}

body.green .btn-cancel {
  background: #f0f2f0;
  color: #556056;
}

body.green .btn-cancel:hover {
  background: #e4e7e4;
}

body.green .btn-close {
  background: #f0f2f0;
  color: #6b756c;
}

body.green .btn-close:hover {
  background: #e4e7e4;
  color: #1e2720;
}

body.green .summary-header h3 {
  color: #1e2720;
}

body.green .summary-title {
  color: #556056;
  border-bottom-color: #edf1ed;
}

body.green .spinner {
  border-color: #e4eae4;
  border-top-color: #526e5a;
}

body.green .summary-content {
  color: #1e2720;
}

body.green .summary-content :deep(h3) {
  color: #526e5a;
}

body.green .summary-content :deep(h4) {
  color: #1e2720;
}

/* ===== Dark Theme ===== */
body.dark .knowledge-base-page {
  background: #121212;
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

body.dark .header-icon {
  background: #242424;
  border-color: #2d2d2d;
  color: #ffffff;
}

body.dark .page-title {
  color: #ffffff;
}

body.dark .page-subtitle {
  color: #999999;
}

body.dark .btn-upload {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-upload:hover {
  background: #e5e5e5;
}

body.dark .upload-area {
  background: #242424;
  border-color: #333333;
}

body.dark .upload-area:hover {
  background: #2d2d2d;
  border-color: #ffffff;
}

body.dark .upload-icon {
  color: #ffffff;
}

body.dark .upload-text {
  color: #e5e5e5;
}

body.dark .upload-hint {
  color: #666666;
}

body.dark .progress-bar {
  background: #1a1a1a;
}

body.dark .progress-fill {
  background: #ffffff;
}

body.dark .progress-text {
  color: #ffffff;
}

body.dark .search-box {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

body.dark .search-box:focus-within {
  border-color: #444444;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

body.dark .search-box svg {
  color: #666666;
}

body.dark .search-box input {
  color: #e5e5e5;
}

body.dark .search-box input::placeholder {
  color: #666666;
}

body.dark .filter-tab {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .filter-tab:hover {
  background: #2d2d2d;
}

body.dark .filter-tab.active {
  background: #ffffff;
  color: #121212;
  border-color: #ffffff;
}

body.dark .error-banner {
  background: #2a1515;
  color: #ef4444;
}

body.dark .paper-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

body.dark .paper-card:hover {
  border-color: #444444;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

body.dark .card-title {
  color: #ffffff;
}

body.dark .paper-card:hover .card-title {
  color: #b3b3b3;
}

body.dark .card-authors {
  color: #999999;
}

body.dark .meta-item {
  color: #999999;
}

body.dark .meta-item svg {
  color: #ffffff;
}

body.dark .tag {
  background: #2d2d2d;
  color: #b3b3b3;
  border-color: #333333;
}

body.dark .card-footer {
  border-top-color: #2d2d2d;
}

body.dark .btn-fav {
  color: #666666;
}

body.dark .btn-fav:hover {
  background: #2d2d2d;
}

body.dark .btn-fav.active {
  color: #f59e0b;
}

body.dark .time {
  color: #666666;
}

body.dark .btn-summary {
  border-color: #ffffff;
  color: #ffffff;
}

body.dark .btn-summary:hover {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-delete {
  color: #666666;
}

body.dark .btn-delete:hover {
  background: #2a1515;
  color: #ef4444;
}

body.dark .empty-icon {
  color: #333333;
}

body.dark .empty-text {
  color: #ffffff;
}

body.dark .empty-hint {
  color: #666666;
}

body.dark .knowledge-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

body.dark .knowledge-card:hover {
  box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

body.dark .knowledge-type.core {
  background: #2a2515;
  color: #f59e0b;
  border-color: #3d3520;
}

body.dark .knowledge-type.method {
  background: #1a2420;
  color: #b3b3b3;
  border-color: #2d3d30;
}

body.dark .content-border {
  background: #444444;
}

body.dark .content-text {
  color: #e5e5e5;
}

body.dark .knowledge-source {
  background: #1a1a1a;
  color: #999999;
}

body.dark .knowledge-source svg {
  color: #ffffff;
}

body.dark .knowledge-tag {
  background: #2d2d2d;
  color: #b3b3b3;
  border-color: #333333;
}

body.dark .load-more-hint {
  color: #666666;
}

body.dark .load-more-hint svg {
  color: #333333;
}

body.dark .modal-overlay {
  background: rgba(0,0,0,0.6);
}

body.dark .modal-card {
  background: #242424;
}

body.dark .modal-card h3 {
  color: #ffffff;
}

body.dark .modal-card p {
  color: #b3b3b3;
}

body.dark .btn-cancel {
  background: #1a1a1a;
  color: #b3b3b3;
}

body.dark .btn-cancel:hover {
  background: #2d2d2d;
}

body.dark .btn-confirm-delete {
  background: #ef4444;
}

body.dark .btn-close {
  background: #1a1a1a;
  color: #999999;
}

body.dark .btn-close:hover {
  background: #2d2d2d;
  color: #ffffff;
}

body.dark .summary-title {
  color: #b3b3b3;
  border-bottom-color: #2d2d2d;
}

body.dark .summary-loading {
  color: #b3b3b3;
}

body.dark .spinner {
  border-color: #333333;
  border-top-color: #ffffff;
}

body.dark .summary-error {
  color: #ef4444;
}

body.dark .summary-content {
  color: #e5e5e5;
}

body.dark .summary-content :deep(h3) {
  color: #ffffff;
}

body.dark .summary-content :deep(h4) {
  color: #e5e5e5;
}

body.dark .summary-content :deep(code) {
  background: #1a1a1a;
}

body.dark .summary-warning {
  background: #2a2515;
  color: #f59e0b;
}
</style>
