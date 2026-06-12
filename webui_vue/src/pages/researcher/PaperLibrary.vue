<template>
<div class="app">
  <ResearcherNav active-tab="paper-library" />

  <div class="page-wrapper">
    <!-- Header -->
    <div class="header-card">
      <div class="header-row">
        <div class="header-left">
          <h2 class="page-title">📚 论文库</h2>
          <span class="paper-count">{{ papers.length }} 篇论文</span>
        </div>
        <div class="header-right">
          <input
            type="text"
            class="search-input"
            v-model="searchText"
            placeholder="搜索论文标题…"
          />
          <button class="btn-upload" @click="showUpload = !showUpload">
            {{ showUpload ? '收起' : '📤 上传 PDF' }}
          </button>
        </div>
      </div>

      <!-- Upload area -->
      <div v-if="showUpload" class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
        <div v-if="uploading" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <span>{{ uploadProgress }}%</span>
        </div>
        <div v-else class="upload-hint">
          <div class="upload-icon">📄</div>
          <div>点击选择或拖拽 PDF 文件到此处</div>
          <div class="upload-sub">支持 .pdf 格式</div>
        </div>
        <input type="file" ref="fileInput" accept=".pdf" @change="onFileChange" style="display:none" />
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">{{ error }}</div>

    <!-- Paper grid -->
    <div v-if="filteredPapers.length > 0" class="paper-grid">
      <div
        v-for="paper in filteredPapers"
        :key="paper.id"
        class="paper-card"
      >
        <div class="card-header">
          <button
            class="btn-fav"
            :class="{ active: paper.isFavorite }"
            @click="doToggleFavorite(paper.id)"
            :title="paper.isFavorite ? '取消收藏' : '收藏'"
          >
            {{ paper.isFavorite ? '⭐' : '☆' }}
          </button>
          <button class="btn-delete" @click="confirmDelete(paper)" title="删除">×</button>
        </div>

        <div class="card-body" @click="viewPaper(paper)">
          <h3 class="paper-title">{{ paper.title }}</h3>
          <div class="paper-authors" v-if="paper.authors">{{ paper.authors }}</div>
          <div class="paper-meta">
            <span v-if="paper.pageCount" class="meta-item">📄 {{ paper.pageCount }} 页</span>
            <span v-if="paper.year" class="meta-item">📅 {{ paper.year }}</span>
            <span v-if="paper.source" class="meta-item">📌 {{ paper.source }}</span>
          </div>
          <div class="paper-tags" v-if="paper.tags?.length">
            <span v-for="tag in paper.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>

        <div class="card-footer">
          <span class="time">{{ formatTime(paper.createdAt) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && papers.length === 0" class="empty-state">
      <div class="empty-icon">📚</div>
      <div class="empty-text">论文库为空</div>
      <div class="empty-hint">上传 PDF 文件或从搜索页面导入论文</div>
    </div>

    <!-- No search results -->
    <div v-if="!loading && papers.length > 0 && filteredPapers.length === 0" class="empty-state">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">未找到匹配的论文</div>
      <div class="empty-hint">请尝试不同的搜索词</div>
    </div>

    <!-- Delete confirmation -->
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
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ResearcherNav from '../../components/ResearcherNav.vue'
import { usePaperLibrary } from '../../composables/usePaperLibrary.js'

const router = useRouter()
const {
  loading, error, papers, uploading, uploadProgress,
  fetchPapers, uploadPaper, deletePaper, toggleFavorite
} = usePaperLibrary()

const searchText = ref('')
const showUpload = ref(false)
const fileInput = ref(null)
const deleteTarget = ref(null)

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
  // TODO: navigate to paper workspace in phase 2
  // For now, just show detail
  console.log('View paper:', paper.id)
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
.app {
  min-height: 100vh;
  background: var(--bg, #f5f3ff);
}

:root {
  --bg: #f8f6f1;
  --card: #ffffff;
  --card-border: #e8e4db;
  --text1: #2c2c2c;
  --text2: #666;
  --text3: #999;
  --accent: #5b8def;
  --accent-light: #eef4ff;
  --accent-hover: #4a7de0;
  --shadow: rgba(91,141,239,0.08);
}

:global(body.dark) .app {
  --bg: #12121a;
  --card: #1e1e2e;
  --card-border: #333;
  --text1: #e0e0e0;
  --text2: #aaa;
  --text3: #777;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.1);
  --accent-hover: #4a7de0;
  --shadow: rgba(91,141,239,0.1);
}

.page-wrapper {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

/* Header */
.header-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 18px 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px var(--shadow);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text1);
}

.paper-count {
  font-size: 0.8rem;
  color: var(--text3);
  background: var(--accent-light);
  padding: 2px 10px;
  border-radius: 8px;
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-input {
  padding: 8px 14px;
  border: 1px solid var(--card-border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text1);
  font-size: 0.85rem;
  outline: none;
  width: 200px;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
}

.btn-upload {
  padding: 8px 16px;
  border: none;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-upload:hover {
  background: var(--accent-hover);
}

/* Upload area */
.upload-area {
  margin-top: 14px;
  padding: 28px;
  border: 2px dashed var(--card-border);
  border-radius: 14px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.upload-area:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}

.upload-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.upload-hint {
  color: var(--text2);
  font-size: 0.85rem;
}

.upload-sub {
  color: var(--text3);
  font-size: 0.75rem;
  margin-top: 4px;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.progress-bar {
  width: 200px;
  height: 6px;
  background: var(--bg);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.3s;
}

/* Error */
.error-banner {
  background: #fee;
  color: #c33;
  padding: 10px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  font-size: 0.85rem;
}

:global(body.dark) .error-banner {
  background: #3a2020;
  color: #ff8888;
}

/* Paper grid */
.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.paper-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px var(--shadow);
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
}

.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px var(--shadow);
}

.card-header {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-bottom: 4px;
}

.btn-fav, .btn-delete {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 2px 6px;
  border-radius: 6px;
  transition: background 0.15s;
}

.btn-fav {
  color: var(--text3);
}

.btn-fav.active {
  color: #f59e0b;
}

.btn-fav:hover {
  background: var(--accent-light);
}

.btn-delete {
  color: var(--text3);
  font-size: 1.2rem;
  line-height: 1;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.card-body {
  flex: 1;
  cursor: pointer;
}

.paper-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text1);
  margin: 0 0 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-authors {
  font-size: 0.78rem;
  color: var(--text2);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.paper-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 0.7rem;
  color: var(--text3);
}

.paper-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  background: var(--accent-light);
  color: var(--accent);
  padding: 1px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.card-footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--card-border);
}

.time {
  font-size: 0.7rem;
  color: var(--text3);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 1.1rem;
  color: var(--text1);
  font-weight: 600;
  margin-bottom: 6px;
}

.empty-hint {
  font-size: 0.85rem;
  color: var(--text3);
}

/* Delete modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-card h3 {
  margin: 0 0 10px;
  color: var(--text1);
  font-size: 1rem;
}

.modal-card p {
  color: var(--text2);
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0 0 18px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm-delete {
  padding: 8px 18px;
  border: none;
  border-radius: 10px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: var(--bg);
  color: var(--text2);
  border: 1px solid var(--card-border);
}

.btn-confirm-delete {
  background: #ef4444;
  color: #fff;
}

.btn-confirm-delete:hover {
  background: #dc2626;
}

@media (max-width: 900px) {
  .header-row {
    flex-direction: column;
    align-items: stretch;
  }
  .header-right {
    flex-direction: column;
  }
  .search-input {
    width: 100%;
  }
  .paper-grid {
    grid-template-columns: 1fr;
  }
}
</style>
