<template>
<div class="research-hotspot">
  <!-- Header -->
  <header class="hotspot-header">
    <div class="domain-selector" @click="showDomainDropdown = !showDomainDropdown">
      <span class="domain-current">{{ currentDomainData.label }}领域</span>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m6 9 6 6 6-6"/>
      </svg>
      <div class="domain-dropdown" v-if="showDomainDropdown">
        <div
          v-for="d in domains"
          :key="d.key"
          class="domain-option"
          :class="{ active: currentDomain === d.key }"
          @click.stop="switchDomain(d.key)"
        >{{ d.label }}</div>
      </div>
    </div>
    <div class="search-box">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
      <input
        type="text"
        v-model="searchQuery"
        placeholder="检索论文、知识网络、特定流派..."
        @keyup.enter="handleSearch"
      >
    </div>
  </header>

  <!-- Main Content -->
  <main class="hotspot-main">
    <!-- Left: Papers List -->
    <section class="papers-panel">
      <div class="panel-header">
        <div class="header-bar"></div>
        <span>最新论文脉络</span>
        <span v-if="isLoading" class="loading-badge">加载中...</span>
      <span v-if="dataSource && !isLoading" class="source-badge">{{ dataSource === 'openalex' ? 'OpenAlex' : 'Semantic Scholar' }}</span>
      </div>
      <div class="papers-list">
        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>正在获取学术数据...</span>
        </div>
        <div v-else-if="apiError" class="error-state">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>
          </svg>
          <span>数据源暂不可用</span>
          <button class="retry-btn" @click="loadDomainData(currentDomain)">重试</button>
        </div>
        <div v-else-if="currentDomainData.papers.length === 0" class="empty-state">
          暂无论文数据
        </div>
        <div
          v-for="(paper, index) in currentDomainData.papers"
          :key="index"
          class="paper-card"
          @click="openPaper(paper)"
        >
          <h4 class="paper-title">{{ paper.title }}</h4>
          <p class="paper-meta">{{ paper.authors }} · {{ paper.journal }} · 引证 {{ paper.citations }}</p>
          <div class="paper-tags">
            <span v-for="tag in paper.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Right: 2x2 Grid -->
    <div class="insights-grid">
      <!-- Trend Chart -->
      <div class="insight-card trend-card">
        <div class="card-header">
          <div class="header-bar"></div>
          <span>近5年发表趋势</span>
        </div>
        <div class="trend-chart">
          <svg class="trend-svg" viewBox="0 0 400 100" preserveAspectRatio="none">
            <path :d="trendPath" fill="none" stroke="#6b8e76" stroke-width="2.5" />
            <path :d="trendAreaPath" fill="url(#green-gradient)" opacity="0.08" />
            <defs>
              <linearGradient id="green-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#6b8e76" />
                <stop offset="100%" stop-color="#ffffff" />
              </linearGradient>
            </defs>
            <circle
              v-for="(point, i) in trendPoints"
              :key="i"
              :cx="point.x"
              :cy="point.y"
              r="3.5"
              fill="#526e5a"
            />
          </svg>
          <div class="trend-labels">
            <span v-for="(year, i) in currentDomainData.trendYears" :key="i">{{ year }}</span>
          </div>
        </div>
        <div class="trend-stats">
          <div class="stat-item">
            <div class="stat-value">{{ currentDomainData.stats[0]?.val || '5,336' }}</div>
            <div class="stat-label">{{ currentDomainData.stats[0]?.lbl || '2026产出' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value highlight">{{ currentDomainData.stats[1]?.val || '+14.6%' }}</div>
            <div class="stat-label">{{ currentDomainData.stats[1]?.lbl || '年增长率' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ currentDomainData.stats[2]?.val || '13,340' }}</div>
            <div class="stat-label">{{ currentDomainData.stats[2]?.lbl || '引证频次' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ currentDomainData.stats[3]?.val || '355' }}</div>
            <div class="stat-label">{{ currentDomainData.stats[3]?.lbl || '核心期刊' }}</div>
          </div>
        </div>
      </div>

      <!-- Hotspot Circle -->
      <div class="insight-card circle-card">
        <div class="card-header">
          <div class="header-bar"></div>
          <span>研究热点圈谱</span>
        </div>
        <div class="circle-chart">
          <div class="circle-outer">
            <div class="circle-middle">
              <div class="circle-inner"></div>
            </div>
          </div>
          <div class="circle-legend">
            <div class="legend-item">
              <span class="legend-dot infra"></span>
              <span>基础设施层</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot tech"></span>
              <span>关键技术层</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot scene"></span>
              <span>应用场景层</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Hotspot Ranking -->
      <div class="insight-card ranking-card">
        <div class="card-header">
          <div class="header-bar"></div>
          <span>研究热点榜</span>
        </div>
        <div class="ranking-list">
          <div v-for="(item, index) in hotSearchItems" :key="index" class="ranking-item">
            <div class="ranking-info">
              <span class="ranking-number">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="ranking-name">{{ item.keyword }}</span>
              <span class="ranking-count">{{ item.papers }} 篇</span>
            </div>
            <div class="ranking-bar">
              <div class="ranking-bar-fill" :style="{ width: item.weight * 100 + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Summary -->
      <div class="insight-card summary-card">
        <div class="card-header">
          <div class="header-bar"></div>
          <span>智能知识摘要</span>
        </div>
        <div class="summary-content">
          <div class="summary-label">■ 领域综述判读：</div>
          <p class="summary-text">{{ currentDomainData.insight || '本季度大模型推荐热点高度聚焦在 Biology 和 Horticulture 软硬件交叉演化方向。当前阶段控制变量设置与消融范式仍有长序列优化的突破余地。' }}</p>
        </div>
      </div>
    </div>
  </main>

  <!-- Paper Detail Modal -->
  <Teleport to="body">
    <div v-if="showPaperModal" class="modal-overlay" @click.self="closePaperModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title">{{ selectedPaper?.title }}</h2>
          <button class="modal-close" @click="closePaperModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <div v-if="paperDetailLoading" class="modal-loading">
          <div class="loading-spinner"></div>
          <span>加载论文详情...</span>
        </div>

        <div v-else-if="selectedPaper" class="modal-body">
          <div class="detail-section">
            <div class="detail-label">作者</div>
            <div class="authors-list">
              <span v-for="(auth, i) in selectedPaper.fullAuthorships?.slice(0, 5)" :key="i" class="author-chip">
                {{ auth.author?.display_name }}
                <span v-if="auth.institutions?.[0]" class="author-inst"> · {{ auth.institutions[0].display_name }}</span>
              </span>
              <span v-if="selectedPaper.fullAuthorships?.length > 5" class="author-more">
                等{{ selectedPaper.fullAuthorships.length }}位作者
              </span>
            </div>
          </div>

          <div class="meta-grid">
            <div class="meta-item">
              <span class="meta-icon">📰</span>
              <span class="meta-label">期刊</span>
              <span class="meta-value">{{ selectedPaper.sourceName }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-icon">📅</span>
              <span class="meta-label">发表日期</span>
              <span class="meta-value">{{ selectedPaper.publicationDate || selectedPaper.year }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-icon">📊</span>
              <span class="meta-label">引用次数</span>
              <span class="meta-value">{{ selectedPaper.citedByCount }} 次</span>
            </div>
            <div class="meta-item">
              <span class="meta-icon">🔗</span>
              <span class="meta-label">DOI</span>
              <span class="meta-value doi-link" @click="openDoi(selectedPaper.doi)">
                {{ selectedPaper.doi ? selectedPaper.doi.replace('https://doi.org/', '') : '无' }}
              </span>
            </div>
          </div>

          <div v-if="selectedPaper.abstract" class="detail-section">
            <div class="detail-label">摘要</div>
            <div class="abstract-content">{{ selectedPaper.abstract }}</div>
          </div>

          <div v-if="selectedPaper.concepts?.length" class="detail-section">
            <div class="detail-label">关键词/概念</div>
            <div class="keywords-list">
              <span v-for="(kw, i) in selectedPaper.concepts" :key="i" class="keyword-tag">
                {{ typeof kw === 'string' ? kw : kw.display_name }}
              </span>
            </div>
          </div>

          <div class="modal-actions">
            <a v-if="selectedPaper.pdfUrl" :href="selectedPaper.pdfUrl" target="_blank" class="action-btn primary">
              📄 下载PDF
            </a>
            <a v-if="selectedPaper.oaUrl" :href="selectedPaper.oaUrl" target="_blank" class="action-btn secondary">
              🔓 开放获取
            </a>
            <a v-if="selectedPaper.doi" :href="selectedPaper.doi" target="_blank" class="action-btn secondary">
              🔗 原文链接
            </a>
            <button class="action-btn outline" @click="closePaperModal">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useOpenAlex } from '../../composables/useOpenAlex.js'

const { loading: apiLoading, error: apiError, dataSource, fetchDomainData, searchPapers, getWorkDetails, reconstructAbstract } = useOpenAlex()

const currentDomain = ref('fruit')
const searchQuery = ref('')
const showDomainDropdown = ref(false)
const isLoading = ref(false)
const agriData = ref({})

// Paper modal
const selectedPaper = ref(null)
const paperDetailLoading = ref(false)
const showPaperModal = ref(false)

const domains = [
  { key: 'fruit', label: '果树栽培学' },
  { key: 'veg', label: '蔬菜育种' },
  { key: 'smart', label: '智慧农业' },
  { key: 'path', label: '植物病理' },
  { key: 'soil', label: '土壤改良' },
]

const currentDomainData = computed(() => {
  return agriData.value[currentDomain.value] || {
    label: '加载中...',
    papers: [],
    keywords: [],
    kwWeights: [],
    trendYears: [],
    trendValues: [],
    stats: [],
    insight: ''
  }
})

const hotSearchItems = computed(() => {
  const data = currentDomainData.value
  if (!data.keywords) return []
  return data.keywords.map((kw, i) => ({
    keyword: kw,
    weight: data.kwWeights[i] || 0.5,
    papers: Math.round((data.kwWeights[i] || 0.5) * 120)
  })).slice(0, 5)
})

// Trend chart calculations
const trendPoints = computed(() => {
  const data = currentDomainData.value
  if (!data.trendValues || data.trendValues.length === 0) return []
  const maxV = Math.max(...data.trendValues)
  const n = data.trendValues.length
  const pad = 30
  const w = 400, h = 100
  const xStep = (w - 2 * pad) / (n - 1)

  return data.trendValues.map((v, i) => ({
    x: pad + i * xStep,
    y: h - pad - (v / maxV) * (h - 2 * pad)
  }))
})

const trendPath = computed(() => {
  if (trendPoints.value.length === 0) return ''
  return trendPoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
})

const trendAreaPath = computed(() => {
  if (trendPoints.value.length === 0) return ''
  const line = trendPoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const last = trendPoints.value[trendPoints.value.length - 1]
  const first = trendPoints.value[0]
  return `${line} L ${last.x} 100 L ${first.x} 100 Z`
})

async function loadDomainData(domainKey) {
  isLoading.value = true
  try {
    const data = await fetchDomainData(domainKey)
    agriData.value[domainKey] = data
  } catch (err) {
    console.error('Failed to load domain data:', err)
  } finally {
    isLoading.value = false
  }
}

function switchDomain(key) {
  currentDomain.value = key
  showDomainDropdown.value = false
  if (!agriData.value[key]) {
    loadDomainData(key)
  }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  isLoading.value = true
  try {
    const results = await searchPapers(searchQuery.value, 10)
    if (agriData.value[currentDomain.value]) {
      agriData.value[currentDomain.value].papers = results
    }
  } catch (err) {
    console.error('Search failed:', err)
  } finally {
    isLoading.value = false
  }
}

async function openPaper(paper) {
  paperDetailLoading.value = true
  showPaperModal.value = true
  selectedPaper.value = {
    ...paper,
    abstract: null,
    oaUrl: null,
    pdfUrl: null,
    fullAuthorships: [],
    citedByCount: paper.citations,
    sourceName: paper.journal,
    concepts: paper.tags || []
  }

  try {
    if (paper.id) {
      const details = await getWorkDetails(paper.id)
      const abstract = reconstructAbstract(details.abstract_inverted_index)
      selectedPaper.value = {
        ...selectedPaper.value,
        abstract,
        oaUrl: details.open_access?.oa_url || null,
        pdfUrl: details.best_oa_location?.pdf_url || details.open_access?.oa_url || null,
        doi: details.doi || paper.doi,
        fullAuthorships: details.authorships || [],
        concepts: details.concepts?.slice(0, 8) || paper.tags,
        citedByCount: details.cited_by_count || paper.citations,
        publicationDate: details.publication_date || null,
        sourceName: details.primary_location?.source?.display_name || paper.journal
      }
    }
  } catch (err) {
    console.error('Failed to load paper details:', err)
  } finally {
    paperDetailLoading.value = false
  }
}

function closePaperModal() {
  showPaperModal.value = false
  selectedPaper.value = null
}

function openDoi(doi) {
  if (doi) window.open(doi, '_blank')
}

// Close dropdown on click outside
onMounted(() => {
  loadDomainData(currentDomain.value)
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.domain-selector')) {
      showDomainDropdown.value = false
    }
  })
})
</script>

<style scoped>
.research-hotspot {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(to bottom, #f5f7f5, #fafbfa);
  overflow: hidden;
}

/* Header */
.hotspot-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #edf0ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  flex-shrink: 0;
}

.domain-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #dee3de;
  border-radius: 12px;
  background: #f8f9f8;
  cursor: pointer;
  font-size: 12px;
  position: relative;
  transition: all 0.2s;
}

.domain-selector:hover {
  background: #edf0ed;
}

.domain-current {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  color: #526e5a;
  font-weight: 500;
}

.domain-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  z-index: 100;
  min-width: 150px;
  overflow: hidden;
}

.domain-option {
  padding: 8px 16px;
  font-size: 12px;
  color: #556056;
  cursor: pointer;
  transition: all 0.2s;
}

.domain-option:hover {
  background: #f8f9f8;
  color: #1e2720;
}

.domain-option.active {
  background: #dbe1db;
  color: #1e2720;
  font-weight: 500;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 288px;
  padding: 8px 12px;
  background: #f8f9f8;
  border: 1px solid #dee3de;
  border-radius: 12px;
  font-size: 12px;
}

.search-box svg {
  color: #9da79e;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #1e2720;
  font-size: 12px;
}

.search-box input::placeholder {
  color: #9da79e;
}

/* Main Content */
.hotspot-main {
  flex: 1;
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 20px;
  padding: 24px;
  overflow-y: auto;
}

/* Papers Panel */
.papers-panel {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(30,39,32,0.01);
  max-height: calc(100vh - 120px);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #1e2720;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f3f0;
  margin-bottom: 12px;
}

.header-bar {
  width: 4px;
  height: 14px;
  background: #526e5a;
  border-radius: 2px;
}

.loading-badge {
  font-size: 10px;
  background: #f2f6f3;
  color: #526e5a;
  padding: 2px 8px;
  border-radius: 8px;
  margin-left: auto;
  animation: pulse 1.5s infinite;
}

.source-badge {
  font-size: 10px;
  background: #dbe1db;
  color: #556056;
  padding: 2px 8px;
  border-radius: 8px;
  margin-left: 8px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.papers-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loading-state,
.empty-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: #9da79e;
  font-size: 12px;
}

.error-state {
  color: #ef4444;
}

.retry-btn {
  padding: 6px 16px;
  background: #526e5a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #415848;
}

.paper-card {
  padding: 12px;
  background: #fdfdfd;
  border: 1px solid #edf1ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.paper-card:hover {
  border-color: #bad2be;
  background: white;
}

.paper-title {
  font-size: 12px;
  font-weight: 700;
  color: #1e2720;
  line-height: 1.4;
  transition: color 0.2s;
}

.paper-card:hover .paper-title {
  color: #526e5a;
}

.paper-meta {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 4px;
  margin-bottom: 8px;
}

.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  font-size: 9px;
  padding: 2px 8px;
  background: #f2f4f2;
  color: #556056;
  border: 1px solid #e2e7e2;
  border-radius: 6px;
}

/* Insights Grid */
.insights-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.insight-card {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(30,39,32,0.01);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #1e2720;
  margin-bottom: 16px;
}

/* Trend Card */
.trend-chart {
  flex: 1;
  position: relative;
  padding: 0 8px;
  margin-bottom: 16px;
}

.trend-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.trend-labels {
  position: absolute;
  bottom: -20px;
  left: 30px;
  right: 30px;
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: #9ca3af;
  font-family: 'JetBrains Mono', monospace;
}

.trend-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 24px;
}

.stat-item {
  background: #f8f9f8;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid #edf1ed;
  text-align: center;
}

.stat-value {
  font-size: 12px;
  font-weight: 700;
  color: #1e2720;
  font-family: 'JetBrains Mono', monospace;
}

.stat-value.highlight {
  color: #059669;
}

.stat-label {
  font-size: 9px;
  color: #9ca3af;
  margin-top: 2px;
}

/* Circle Card */
.circle-chart {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  position: relative;
}

.circle-outer {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  border: 12px solid rgba(107, 142, 118, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);
}

.circle-middle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 8px solid rgba(186, 210, 190, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-inner {
  width: 16px;
  height: 16px;
  background: #f7f8f7;
  border-radius: 50%;
}

.circle-legend {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  color: #556056;
  font-weight: 500;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.infra {
  background: #526e5a;
}

.legend-dot.tech {
  background: #6b8e76;
}

.legend-dot.scene {
  background: #bad2be;
}

/* Ranking Card */
.ranking-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.ranking-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
}

.ranking-number {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: #526e5a;
  width: 20px;
}

.ranking-name {
  flex: 1;
  color: #1e2720;
  font-weight: 500;
}

.ranking-count {
  color: #9ca3af;
  font-family: 'JetBrains Mono', monospace;
}

.ranking-bar {
  height: 4px;
  background: #f0f2f0;
  border-radius: 2px;
  overflow: hidden;
}

.ranking-bar-fill {
  height: 100%;
  background: linear-gradient(to right, #bad2be, #526e5a);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Summary Card */
.summary-content {
  flex: 1;
  background: #f8f9f8;
  border: 1px solid #edf1ed;
  border-radius: 12px;
  padding: 12px;
  overflow-y: auto;
}

.summary-label {
  font-size: 11px;
  font-weight: 700;
  color: #526e5a;
  margin-bottom: 8px;
}

.summary-text {
  font-size: 11px;
  color: #3b473d;
  font-family: 'Noto Serif SC', 'SimSun', serif;
  line-height: 1.6;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border: 2px solid #526e5a;
  border-radius: 16px;
  max-width: 700px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #edf0ed;
  gap: 16px;
}

.modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e2720;
  line-height: 1.4;
  flex: 1;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: 1.5px solid #dee3de;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #9da79e;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.modal-close:hover {
  border-color: #526e5a;
  color: #526e5a;
  background: #f2f6f3;
}

.modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: #9da79e;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #dee3de;
  border-top-color: #526e5a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.modal-body {
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: #526e5a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.authors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.author-chip {
  font-size: 12px;
  padding: 4px 10px;
  background: #f2f6f3;
  border: 1px solid #bad2be;
  border-radius: 14px;
  color: #1e2720;
}

.author-inst {
  color: #9da79e;
  font-size: 10px;
}

.author-more {
  font-size: 12px;
  color: #9da79e;
  padding: 4px 8px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f2f6f3;
  border: 1px solid #bad2be;
  border-radius: 10px;
}

.meta-icon {
  font-size: 14px;
}

.meta-label {
  font-size: 10px;
  color: #9da79e;
  min-width: 50px;
}

.meta-value {
  font-size: 12px;
  color: #1e2720;
  font-weight: 500;
}

.doi-link {
  color: #526e5a;
  cursor: pointer;
  text-decoration: underline;
}

.doi-link:hover {
  opacity: 0.8;
}

.abstract-content {
  font-size: 12px;
  line-height: 1.7;
  color: #556056;
  padding: 12px 14px;
  background: #f2f6f3;
  border: 1px solid #bad2be;
  border-radius: 10px;
  text-align: justify;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword-tag {
  font-size: 10px;
  padding: 4px 10px;
  border: 1px solid #526e5a;
  color: #526e5a;
  border-radius: 14px;
  background: #f2f6f3;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-btn.primary {
  background: #526e5a;
  color: #fff;
  border: 2px solid #526e5a;
}

.action-btn.primary:hover {
  background: #415848;
  border-color: #415848;
}

.action-btn.secondary {
  background: #f2f6f3;
  color: #526e5a;
  border: 2px solid #526e5a;
}

.action-btn.secondary:hover {
  background: #526e5a;
  color: #fff;
}

.action-btn.outline {
  background: transparent;
  color: #9da79e;
  border: 2px solid #dee3de;
}

.action-btn.outline:hover {
  border-color: #526e5a;
  color: #526e5a;
}

@media (max-width: 900px) {
  .hotspot-main {
    grid-template-columns: 1fr;
  }

  .insights-grid {
    grid-template-columns: 1fr;
  }
}
</style>
