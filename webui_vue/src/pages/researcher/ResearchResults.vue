<template>
<div class="research-results-page">
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="header-info">
      <h1 class="page-title">我的研究成果</h1>
      <p class="page-subtitle">从工作台保存的 AI 研究输出 · 结论可追溯、论据可沉淀</p>
    </div>
  </div>

  <!-- 加载状态 -->
  <div v-if="loading && results.length === 0" class="loading-state">
    <div class="loading-spinner"></div>
    <p>加载中...</p>
  </div>

  <!-- 空状态 -->
  <div v-else-if="results.length === 0" class="empty-state">
    <div class="empty-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
      </svg>
    </div>
    <h3>暂无研究成果</h3>
    <p>在工作台与 AI 对话时，点击消息下方的"保存"按钮即可保存到这里</p>
    <button class="btn-go-workspace" @click="router.push('/researcher/workspace')">
      前往工作台
    </button>
  </div>

  <!-- 研究成果列表 -->
  <div v-else class="results-list">
    <div
      v-for="item in results"
      :key="item.id"
      class="result-card"
      @click="openResult(item)"
    >
      <div class="card-header">
        <h3 class="card-title">{{ item.title }}</h3>
        <button class="btn-delete" @click.stop="confirmDelete(item)" title="删除">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
      <div class="card-meta-row">
        <span v-if="item.projectName" class="meta-pill">{{ item.projectName }}</span>
        <span v-for="tag in item.tags || []" :key="tag" class="meta-pill tag">{{ tag }}</span>
      </div>
      <p class="card-preview">{{ item.contentPreview }}</p>
      <div class="card-footer">
        <span class="card-time">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          {{ formatTime(item.createdAt) }}
        </span>
        <span v-if="item.chatId" class="card-source">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          来自对话
        </span>
      </div>
    </div>
  </div>

  <!-- 详情弹窗 -->
  <Teleport to="body">
    <div v-if="selectedResult" class="dialog-overlay" @click.self="selectedResult = null">
      <div class="dialog-card detail-dialog">
        <div class="dialog-header">
          <h3>{{ selectedResult.title }}</h3>
          <button class="btn-close" @click="selectedResult = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="detail-meta">
            <span>保存于 {{ formatTime(selectedResult.createdAt) }}</span>
          </div>
          <div class="detail-content" v-html="renderMarkdown(selectedResult.content)"></div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="selectedResult = null">关闭</button>
          <button class="btn-copy" @click="copyContent">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
            </svg>
            复制内容
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 删除确认弹窗 -->
  <Teleport to="body">
    <div v-if="deleteTarget" class="dialog-overlay" @click.self="deleteTarget = null">
      <div class="dialog-card confirm-dialog">
        <div class="dialog-header">
          <h3>确认删除</h3>
          <button class="btn-close" @click="deleteTarget = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <p>确定要删除「{{ deleteTarget.title }}」吗？此操作不可撤销。</p>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="deleteTarget = null">取消</button>
          <button class="btn-danger" @click="doDelete">删除</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { useResearchResults } from '../../composables/useResearchResults.js'

const router = useRouter()
const { results, loading, fetchResults, fetchResult, deleteResult } = useResearchResults()

const selectedResult = ref(null)
const deleteTarget = ref(null)

onMounted(() => {
  fetchResults()
})

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  // Less than 1 minute
  if (diff < 60000) return '刚刚'
  // Less than 1 hour
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  // Less than 24 hours
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  // Less than 7 days
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  // Format as date
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function openResult(item) {
  // Fetch full content
  const full = await fetchResult(item.id)
  if (full) {
    selectedResult.value = full
  }
}

function confirmDelete(item) {
  deleteTarget.value = item
}

async function doDelete() {
  if (!deleteTarget.value) return
  await deleteResult(deleteTarget.value.id)
  deleteTarget.value = null
}

async function copyContent() {
  if (!selectedResult.value?.content) return
  try {
    await navigator.clipboard.writeText(selectedResult.value.content)
    // Could add a toast notification here
  } catch (err) {
    console.error('Failed to copy:', err)
  }
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

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #999;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #eaeaea;
  border-top-color: #121212;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f4f4f4;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  margin-bottom: 24px;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #121212;
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: #666;
  margin: 0 0 24px;
  max-width: 400px;
}

.btn-go-workspace {
  padding: 10px 24px;
  background: #121212;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-go-workspace:hover {
  background: #333;
}

/* 结果列表 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.result-card:hover {
  border-color: #121212;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #121212;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.btn-delete {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #999;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-delete:hover {
  background: #fee;
  color: #e53e3e;
}

.card-preview {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-time,
.card-source {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

/* 详情弹窗 */
.detail-dialog {
  width: 720px;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.dialog-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

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
  flex: 1;
  padding-right: 16px;
}

.btn-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f4f4f4;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-close:hover {
  background: #e8e8e8;
  color: #121212;
}

.dialog-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.detail-meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
}

.detail-content {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.detail-content :deep(h1),
.detail-content :deep(h2),
.detail-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  color: #121212;
}

.detail-content :deep(p) {
  margin-bottom: 12px;
}

.detail-content :deep(code) {
  background: #f4f4f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.detail-content :deep(pre) {
  background: #f8f8f8;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.detail-content :deep(pre code) {
  background: none;
  padding: 0;
}

.detail-content :deep(ul),
.detail-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 12px;
}

.detail-content :deep(li) {
  margin-bottom: 4px;
}

.detail-content :deep(blockquote) {
  border-left: 3px solid #eaeaea;
  padding-left: 16px;
  color: #666;
  margin: 16px 0;
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
  color: #666;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  border-color: #121212;
  color: #121212;
}

.btn-copy {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  background: #121212;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-copy:hover {
  background: #333;
}

.confirm-dialog {
  width: 400px;
  max-width: 90vw;
}

.confirm-dialog .dialog-body p {
  font-size: 14px;
  color: #333;
  margin: 0;
  line-height: 1.5;
}

.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  background: #e53e3e;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-danger:hover {
  background: #c53030;
}

/* 响应式 */
@media (max-width: 768px) {
  .research-results-page {
    padding: 20px 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .detail-dialog {
    width: 95vw;
    max-height: 90vh;
  }
}

/* ===== Green Theme ===== */
body.green .page-title {
  color: #1e2720;
}

body.green .page-subtitle {
  color: #717c72;
}

body.green .result-card {
  border-color: #e8ebe8;
}

body.green .result-card:hover {
  border-color: #bad2be;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.06);
}

body.green .card-title {
  color: #1e2720;
}

body.green .btn-go-workspace {
  background: #526e5a;
}

body.green .btn-go-workspace:hover {
  background: #415848;
}

body.green .btn-copy {
  background: #526e5a;
}

body.green .btn-copy:hover {
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
  color: #999;
}

body.dark .result-card {
  background: #242424;
  border-color: #333;
}

body.dark .result-card:hover {
  border-color: #555;
}

body.dark .card-title {
  color: #fff;
}

body.dark .card-preview {
  color: #999;
}

body.dark .empty-icon {
  background: #1a1a1a;
  color: #666;
}

body.dark .empty-state h3 {
  color: #fff;
}

body.dark .btn-go-workspace {
  background: #fff;
  color: #121212;
}

body.dark .dialog-card {
  background: #242424;
}

body.dark .dialog-header {
  border-bottom-color: #333;
}

body.dark .dialog-header h3 {
  color: #fff;
}

body.dark .btn-close {
  background: #1a1a1a;
  color: #999;
}

body.dark .btn-close:hover {
  background: #333;
  color: #fff;
}

body.dark .detail-content {
  color: #e5e5e5;
}

body.dark .btn-cancel {
  background: #1a1a1a;
  border-color: #333;
  color: #b3b3b3;
}

body.dark .btn-copy {
  background: #fff;
  color: #121212;
}

body.dark .btn-delete:hover {
  background: #3a1a1a;
  color: #fc8181;
}

.card-meta-row, .detail-tags, .detail-sources { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
.meta-pill, .detail-tags span, .detail-sources span { font-size:11px; padding:4px 8px; border-radius:999px; background:#f2f4f2; color:#526e5a; }
.meta-pill.tag { background:#f6f6f6; color:#666; }
.detail-sources { align-items:center; margin-top:8px; }
.detail-sources strong { font-size:12px; color:#555; margin-right:4px; }
.detail-sections { display:flex; flex-direction:column; gap:16px; }
.detail-sections section { padding:14px; border:1px solid #eee; border-radius:12px; background:#fafafa; }
.detail-sections h4 { margin:0 0 8px; font-size:14px; }
body.dark .meta-pill, body.dark .detail-tags span, body.dark .detail-sources span { background:#333; color:#d7e0d8; }
body.dark .detail-sections section { background:#1f1f1f; border-color:#333; }
</style>
