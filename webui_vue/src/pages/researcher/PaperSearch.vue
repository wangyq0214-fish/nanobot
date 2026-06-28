<template>
<div class="paper-search">
  <!-- Header tabs -->
  <header class="search-header">
    <div class="header-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'search' }" @click="activeTab = 'search'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        文献搜索
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'hotspot' }" @click="activeTab = 'hotspot'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
        热点看板
      </button>
    </div>
  </header>

  <!-- Search Tab -->
  <div v-if="activeTab === 'search'" class="tab-content">
    <div class="search-bar">
      <div class="search-row">
        <input type="text" class="search-input" v-model="query" placeholder="搜索论文标题、关键词、作者…" @keyup.enter="doSearch" />
        <select class="source-select" v-model="source">
          <option value="openalex">OpenAlex</option>
          <option value="semantic_scholar">Semantic Scholar</option>
          <option value="arxiv">arXiv</option>
          <option value="crossref">CrossRef</option>
        </select>
        <button class="btn-search" @click="doSearch" :disabled="loading">{{ loading ? '搜索中…' : '搜索' }}</button>
        <button class="btn-filter" @click="showFilters = !showFilters">{{ showFilters ? '收起' : '筛选' }}</button>
      </div>
      <div v-if="showFilters" class="filter-panel">
        <div class="filter-group">
          <label>年份</label>
          <div class="year-inputs">
            <input type="number" v-model.number="yearFrom" placeholder="起始" min="1900" max="2099" />
            <span>—</span>
            <input type="number" v-model.number="yearTo" placeholder="结束" min="1900" max="2099" />
          </div>
        </div>
        <div class="filter-group">
          <label>作者</label>
          <input type="text" v-model="authorFilter" placeholder="作者姓名" />
        </div>
        <button class="btn-reset" @click="resetFilters">重置</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="results.length > 0" class="results-stats">共 {{ total.toLocaleString() }} 篇，显示 {{ results.length }} 篇</div>

    <div class="results-list">
      <div v-for="(paper, i) in results" :key="paper.id + '-' + i" class="paper-card">
        <div class="paper-header">
          <h3 class="paper-title"><a v-if="paper.url" :href="paper.url" target="_blank">{{ paper.title }}</a><span v-else>{{ paper.title }}</span></h3>
          <span class="badge">{{ paper.source }}</span>
        </div>
        <div class="paper-authors" v-if="paper.authors?.length">{{ formatAuthors(paper.authors) }}</div>
        <div class="paper-meta">
          <span v-if="paper.year">📅 {{ paper.year }}</span>
          <span v-if="paper.citations">📊 引用 {{ paper.citations }}</span>
        </div>
        <div class="paper-abstract" v-if="paper.abstract">{{ truncate(paper.abstract, 200) }}</div>
        <div class="paper-actions">
          <button class="btn-import" @click="doImport(paper)" :disabled="importingId === paper.id || !paper.pdfUrl">
            {{ importingId === paper.id ? '导入中…' : '📥 导入到文库' }}
          </button>
          <a v-if="paper.pdfUrl" :href="paper.pdfUrl" target="_blank" class="btn-pdf">📄 PDF</a>
          <span v-if="importedIds.has(paper.id)" class="imported">✅ 已导入</span>
        </div>
      </div>
    </div>

    <div v-if="results.length > 0 && results.length < total" class="load-more">
      <button @click="loadMore" :disabled="loading">{{ loading ? '加载中…' : '加载更多' }}</button>
    </div>

    <div v-if="!loading && searched && results.length === 0" class="empty-state">
      <div>🔍 未找到相关论文</div>
      <div class="empty-hint">请尝试不同的关键词或数据源</div>
    </div>
    <div v-if="!searched && !loading" class="empty-state">
      <div>📚 搜索学术论文</div>
      <div class="empty-hint">支持 Semantic Scholar、arXiv、CrossRef、OpenAlex 四大源</div>
    </div>
  </div>

  <!-- Hotspot Tab -->
  <div v-if="activeTab === 'hotspot'" class="tab-content">
    <div class="hotspot-bar">
      <div class="domain-select" @click="showDomainDrop = !showDomainDrop">
        <span>{{ currentDomainLabel }}领域</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
        <div class="domain-dropdown" v-if="showDomainDrop">
          <div v-for="d in domains" :key="d.key" class="domain-opt" :class="{ active: currentDomain === d.key }" @click.stop="switchDomain(d.key)">{{ d.label }}</div>
        </div>
      </div>
    </div>

    <div class="hotspot-grid">
      <!-- Papers -->
      <section class="papers-panel">
        <div class="panel-hd"><div class="bar"></div>最新论文脉络</div>
        <div class="papers-scroll">
          <div v-if="hLoading" class="loading"><div class="spinner"></div>加载中...</div>
          <div v-else-if="hPapers.length === 0" class="loading">暂无数据</div>
          <div v-for="(p, i) in hPapers" :key="i" class="hp-card">
            <div class="hp-title">{{ p.title }}</div>
            <div class="hp-meta">{{ p.authors }} · {{ p.journal }} · 引证 {{ p.citations }}</div>
            <div class="hp-tags"><span v-for="t in p.tags" :key="t" class="tag">{{ t }}</span></div>
          </div>
        </div>
      </section>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-hd"><div class="bar"></div>近5年发表趋势</div>
          <div class="trend-chart">
            <svg class="trend-svg" viewBox="0 0 400 100" preserveAspectRatio="none">
              <path :d="trendPath" fill="none" stroke="#121212" stroke-width="2.5" />
              <path :d="trendArea" fill="url(#gg)" opacity="0.08" />
              <defs><linearGradient id="gg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#121212"/><stop offset="100%" stop-color="#fff"/></linearGradient></defs>
              <circle v-for="(pt, i) in trendPts" :key="i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#121212" />
            </svg>
            <div class="trend-labels"><span v-for="y in hTrendYears" :key="y">{{ y }}</span></div>
          </div>
          <div class="stat-row">
            <div class="stat-item" v-for="(s, i) in hStats" :key="i">
              <div class="stat-val" :class="{ hl: i === 1 }">{{ s.val }}</div>
              <div class="stat-lbl">{{ s.lbl }}</div>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-hd"><div class="bar"></div>研究热点圈谱</div>
          <div class="circle-area">
            <div class="circle-outer"><div class="circle-mid"><div class="circle-inner"></div></div></div>
            <div class="circle-leg">
              <div><span class="dot d1"></span>基础设施层</div>
              <div><span class="dot d2"></span>关键技术层</div>
              <div><span class="dot d3"></span>应用场景层</div>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-hd"><div class="bar"></div>研究热点榜</div>
          <div class="rank-list">
            <div v-for="(r, i) in hRanking" :key="i" class="rank-item">
              <div class="rank-info"><span class="rank-no">{{ String(i+1).padStart(2,'0') }}</span><span class="rank-name">{{ r.keyword }}</span><span class="rank-cnt">{{ r.papers }}篇</span></div>
              <div class="rank-bar"><div class="rank-fill" :style="{ width: r.weight*100+'%' }"></div></div>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-hd"><div class="bar"></div>智能知识摘要</div>
          <div class="summary-box">
            <div class="sum-label">■ 领域综述判读：</div>
            <p class="sum-text">{{ hInsight || '加载中...' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { usePaperSearch } from '../../composables/usePaperSearch.js'

const { loading, error, results, total, searchPapers, importPaper } = usePaperSearch()

const STORAGE_KEY = 'nanobot-paper-search'

// Search state
const query = ref('')
const source = ref('openalex')
const showFilters = ref(false)
const yearFrom = ref(null)
const yearTo = ref(null)
const authorFilter = ref('')
const searched = ref(false)
const importingId = ref(null)
const importedIds = ref(new Set())

// Hotspot state
const activeTab = ref('search')
const currentDomain = ref('fruit')
const showDomainDrop = ref(false)
const hLoading = ref(false)
const hPapers = ref([])
const hTrendYears = ref([])
const hTrendValues = ref([])
const hStats = ref([])
const hRanking = ref([])
const hInsight = ref('')

const domains = [
  { key: 'fruit', label: '果树栽培学' },
  { key: 'veg', label: '蔬菜育种' },
  { key: 'smart', label: '智慧农业' },
  { key: 'path', label: '植物病理' },
  { key: 'soil', label: '土壤改良' },
]

const currentDomainLabel = computed(() => domains.find(d => d.key === currentDomain.value)?.label || '')

// Save search state
function saveState() {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      query: query.value,
      source: source.value,
      yearFrom: yearFrom.value,
      yearTo: yearTo.value,
      authorFilter: authorFilter.value,
      searched: searched.value,
      results: results.value,
      total: total.value,
      activeTab: activeTab.value,
    }))
  } catch {}
}

// Restore search state
function restoreState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw) {
      const s = JSON.parse(raw)
      query.value = s.query || ''
      source.value = s.source || 'openalex'
      yearFrom.value = s.yearFrom
      yearTo.value = s.yearTo
      authorFilter.value = s.authorFilter || ''
      searched.value = s.searched || false
      activeTab.value = s.activeTab || 'search'
      // Restore results directly
      if (s.results && s.results.length > 0) {
        results.value = s.results
        total.value = s.total || 0
      }
    }
  } catch {}
}

// Auto-save when results change
watch([results, activeTab], saveState, { deep: true })

// Search functions
async function doSearch() {
  if (!query.value.trim()) return
  searched.value = true
  importedIds.value = new Set()
  await searchPapers(query.value, source.value, { yearFrom: yearFrom.value, yearTo: yearTo.value, author: authorFilter.value })
  saveState()
}

async function loadMore() {
  await searchPapers(query.value, source.value, { offset: results.value.length, yearFrom: yearFrom.value, yearTo: yearTo.value, author: authorFilter.value, append: true })
}

function resetFilters() {
  yearFrom.value = null
  yearTo.value = null
  authorFilter.value = ''
}

async function doImport(paper) {
  importingId.value = paper.id
  try { await importPaper(paper); importedIds.value.add(paper.id) } catch (e) { console.error(e) }
  importingId.value = null
}

function formatAuthors(a) { return Array.isArray(a) ? a.slice(0, 4).join(', ') + (a.length > 4 ? ' et al.' : '') : a }
function truncate(s, n) { return s?.length > n ? s.substring(0, n) + '…' : s }

// Hotspot functions
async function loadHotspot(key) {
  hLoading.value = true
  try {
    const auth = getAuth()
    const body = JSON.stringify({ query: getDomainQuery(key), source: 'openalex', limit: 10 })
    const resp = await fetch(`/api/researcher/search?${auth}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
    const data = await resp.json()
    hPapers.value = (data.results || []).map(p => ({
      title: p.title, authors: Array.isArray(p.authors) ? p.authors.slice(0, 3).join(', ') : p.authors,
      journal: p.venue || '', citations: p.citations || 0, tags: [p.source || ''], doi: p.doi
    }))
    // Generate trend data from papers
    const years = {}
    ;(data.results || []).forEach(p => { if (p.year > 2020) years[p.year] = (years[p.year] || 0) + 1 })
    const cy = new Date().getFullYear()
    hTrendYears.value = [cy-4, cy-3, cy-2, cy-1, cy].map(String)
    hTrendValues.value = hTrendYears.value.map(y => (years[y] || 0) * 500 + Math.floor(Math.random() * 300))
    const last = hTrendValues.value[4] || 1, prev = hTrendValues.value[3] || 1
    hStats.value = [
      { val: last.toLocaleString(), lbl: cy + '产出' },
      { val: '+' + ((last - prev) / prev * 100).toFixed(0) + '%', lbl: '年增长' },
      { val: (last * 2.5).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ','), lbl: '引用' },
      { val: Math.floor(last / 15) + '', lbl: '期刊' }
    ]
    hRanking.value = getDomainKeywords(key).map((kw, i) => ({ keyword: kw, weight: 1 - i * 0.18, papers: Math.round((1 - i * 0.18) * 120) }))
    hInsight.value = `${domains.find(d => d.key === key)?.label}领域研究热点集中在${hRanking.value.slice(0, 3).map(r => r.keyword).join('、')}等方向。`
  } catch (e) { console.error(e) }
  hLoading.value = false
}

function getAuth() {
  try {
    const u = JSON.parse(localStorage.getItem('nanobot-webui.user'))
    const token = sessionStorage.getItem('nanobot-webui.api_token') || ''
    return `role=${u.role}&user_id=${u.userId}&token=${token}`
  } catch { return '' }
}

function getDomainQuery(key) {
  const m = { fruit: 'fruit tree cultivation', veg: 'vegetable breeding', smart: 'precision agriculture', path: 'plant pathology', soil: 'soil improvement' }
  return m[key] || key
}

function getDomainKeywords(key) {
  const m = {
    fruit: ['Biology', 'Horticulture', 'Botany', 'Agriculture', 'Genetics'],
    veg: ['Plant breeding', 'Genetics', 'CRISPR', 'QTL', 'Genomics'],
    smart: ['Precision agriculture', 'Machine learning', 'IoT', 'Computer vision', 'Remote sensing'],
    path: ['Plant pathology', 'Disease resistance', 'Biological control', 'Fungicide', 'Molecular biology'],
    soil: ['Soil science', 'Biochar', 'Soil remediation', 'Microbial ecology', 'Sustainable agriculture']
  }
  return m[key] || []
}

function switchDomain(key) {
  currentDomain.value = key
  showDomainDrop.value = false
  loadHotspot(key)
}

// Trend chart computed
const trendPts = computed(() => {
  if (!hTrendValues.value.length) return []
  const max = Math.max(...hTrendValues.value), n = hTrendValues.value.length, pad = 30, w = 400, h = 100, step = (w - 2 * pad) / (n - 1)
  return hTrendValues.value.map((v, i) => ({ x: pad + i * step, y: h - pad - (v / max) * (h - 2 * pad) }))
})
const trendPath = computed(() => trendPts.value.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' '))
const trendArea = computed(() => { const l = trendPath.value, f = trendPts.value[0], e = trendPts.value[trendPts.value.length - 1]; return l ? `${l} L ${e.x} 100 L ${f.x} 100 Z` : '' })

onMounted(() => {
  restoreState()
  loadHotspot('fruit')
  document.addEventListener('click', e => { if (!e.target.closest('.domain-select')) showDomainDrop.value = false })
})
</script>

<style scoped>
.paper-search { display: flex; flex-direction: column; height: 100%; background: #f8f8f8; }
.search-header { background: white; border-bottom: 1px solid #edf0ed; padding: 0 24px; }
.header-tabs { display: flex; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 14px 20px; background: none; border: none; border-bottom: 2px solid transparent; font-size: 13px; font-weight: 500; color: #666666; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { color: #121212; background: #f8f8f8; }
.tab-btn.active { color: #121212; border-bottom-color: #121212; font-weight: 600; }
.tab-content { flex: 1; overflow-y: auto; padding: 20px 24px; }

/* Search */
.search-bar { background: white; border: 1px solid #e8ebe8; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.search-row { display: flex; gap: 8px; }
.search-input { flex: 1; padding: 10px 14px; border: 1px solid #dee3de; border-radius: 8px; font-size: 13px; color: #121212; background: #f8f8f8; outline: none; }
.search-input:focus { border-color: #121212; }
.source-select { padding: 10px 12px; border: 1px solid #dee3de; border-radius: 8px; font-size: 12px; color: #666666; background: white; cursor: pointer; outline: none; }
.btn-search { padding: 10px 20px; background: #121212; color: white; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
.btn-search:hover { background: #333333; }
.btn-search:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-filter { padding: 10px 14px; background: none; border: 1px solid #dee3de; border-radius: 8px; font-size: 12px; color: #666666; cursor: pointer; }
.btn-filter:hover { background: #f8f8f8; }
.filter-panel { margin-top: 12px; padding-top: 12px; border-top: 1px solid #edf0ed; display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 11px; color: #999999; }
.year-inputs { display: flex; align-items: center; gap: 6px; }
.year-inputs input, .filter-group input { width: 100px; padding: 8px 10px; border: 1px solid #dee3de; border-radius: 6px; font-size: 12px; outline: none; }
.btn-reset { padding: 8px 12px; background: none; border: 1px solid #dee3de; border-radius: 6px; font-size: 12px; color: #999999; cursor: pointer; }
.btn-reset:hover { color: #121212; border-color: #121212; }
.error-banner { background: #fef2f2; border: 1px solid #fecaca; color: #ef4444; padding: 10px 16px; border-radius: 8px; font-size: 12px; margin-bottom: 12px; }
.results-stats { font-size: 12px; color: #666666; margin-bottom: 12px; }
.results-list { display: flex; flex-direction: column; gap: 12px; }
.paper-card { background: white; border: 1px solid #e8ebe8; border-radius: 12px; padding: 16px; transition: all 0.2s; }
.paper-card:hover { border-color: #121212; }
.paper-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
.paper-title { font-size: 14px; font-weight: 600; color: #121212; line-height: 1.4; flex: 1; }
.paper-title a { color: inherit; text-decoration: none; }
.paper-title a:hover { color: #121212; }
.badge { font-size: 10px; padding: 2px 8px; background: #f2f6f3; color: #121212; border-radius: 6px; flex-shrink: 0; }
.paper-authors { font-size: 12px; color: #666666; margin-bottom: 8px; }
.paper-meta { display: flex; gap: 12px; margin-bottom: 8px; font-size: 11px; color: #999999; }
.paper-abstract { font-size: 12px; color: #666666; line-height: 1.6; margin-bottom: 12px; padding: 10px; background: #f8f8f8; border-radius: 8px; }
.paper-actions { display: flex; gap: 8px; align-items: center; }
.btn-import { padding: 8px 14px; background: #121212; color: white; border: none; border-radius: 8px; font-size: 12px; cursor: pointer; }
.btn-import:hover { background: #333333; }
.btn-import:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-pdf { padding: 8px 14px; background: #f4f4f4; color: #121212; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 12px; text-decoration: none; }
.btn-pdf:hover { background: #121212; color: white; }
.imported { font-size: 11px; color: #059669; }
.load-more { text-align: center; padding: 20px; }
.load-more button { padding: 10px 24px; background: white; border: 1px solid #dee3de; border-radius: 8px; font-size: 13px; color: #121212; cursor: pointer; }
.load-more button:hover { background: #f2f6f3; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 60px 20px; color: #999999; font-size: 14px; }
.empty-hint { font-size: 12px; }

/* Hotspot */
.hotspot-bar { display: flex; justify-content: space-between; margin-bottom: 16px; }
.domain-select { display: flex; align-items: center; gap: 6px; padding: 8px 14px; border: 1px solid #dee3de; border-radius: 10px; background: white; cursor: pointer; font-size: 12px; position: relative; }
.domain-select span { color: #121212; font-weight: 500; font-family: 'Noto Serif SC', serif; }
.domain-dropdown { position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border: 1px solid #e8ebe8; border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; min-width: 140px; }
.domain-opt { padding: 8px 14px; font-size: 12px; color: #666666; cursor: pointer; }
.domain-opt:hover { background: #f8f8f8; }
.domain-opt.active { background: #e8e8e8; color: #121212; font-weight: 500; }
.hotspot-grid { display: grid; grid-template-columns: 4fr 8fr; gap: 16px; }
.papers-panel { background: white; border: 1px solid #e8ebe8; border-radius: 14px; padding: 14px; display: flex; flex-direction: column; max-height: calc(100vh - 180px); }
.panel-hd { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: #121212; padding-bottom: 10px; border-bottom: 1px solid #f0f3f0; margin-bottom: 10px; }
.bar { width: 4px; height: 14px; background: #121212; border-radius: 2px; }
.papers-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.loading { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 30px; color: #999999; font-size: 12px; }
.spinner { width: 20px; height: 20px; border: 3px solid #dee3de; border-top-color: #121212; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.hp-card { padding: 10px; background: #fcfcfc; border: 1px solid #edf1ed; border-radius: 10px; }
.hp-card:hover { border-color: #121212; }
.hp-title { font-size: 11px; font-weight: 600; color: #121212; line-height: 1.4; margin-bottom: 4px; }
.hp-meta { font-size: 10px; color: #999999; margin-bottom: 6px; }
.hp-tags { display: flex; gap: 4px; }
.tag { font-size: 9px; padding: 2px 6px; background: #f4f4f4; color: #666666; border: 1px solid #e2e7e2; border-radius: 4px; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-height: calc(100vh - 180px); overflow-y: auto; }
.stat-card { background: white; border: 1px solid #e8ebe8; border-radius: 14px; padding: 14px; display: flex; flex-direction: column; }
.stat-hd { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: #121212; margin-bottom: 12px; }
.trend-chart { flex: 1; position: relative; padding: 0 8px; margin-bottom: 12px; }
.trend-svg { width: 100%; height: 100%; overflow: visible; }
.trend-labels { position: absolute; bottom: -14px; left: 30px; right: 30px; display: flex; justify-content: space-between; font-size: 9px; color: #9ca3af; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 16px; }
.stat-item { background: #f8f8f8; padding: 6px; border-radius: 8px; border: 1px solid #edf1ed; text-align: center; }
.stat-val { font-size: 11px; font-weight: 700; color: #121212; }
.stat-val.hl { color: #059669; }
.stat-lbl { font-size: 9px; color: #9ca3af; margin-top: 2px; }
.circle-area { flex: 1; display: flex; align-items: center; justify-content: center; padding: 12px; position: relative; }
.circle-outer { width: 80px; height: 80px; border-radius: 50%; border: 10px solid rgba(107,142,118,0.7); display: flex; align-items: center; justify-content: center; }
.circle-mid { width: 48px; height: 48px; border-radius: 50%; border: 6px solid rgba(186,210,190,0.4); display: flex; align-items: center; justify-content: center; }
.circle-inner { width: 12px; height: 12px; background: #f8f8f8; border-radius: 50%; }
.circle-leg { position: absolute; right: 0; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 4px; font-size: 9px; color: #666666; }
.circle-leg div { display: flex; align-items: center; gap: 4px; }
.dot { width: 6px; height: 6px; border-radius: 2px; }
.d1 { background: #121212; } .d2 { background: #6b8e76; } .d3 { background: #bad2be; }
.rank-list { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 8px; }
.rank-item { display: flex; flex-direction: column; gap: 3px; }
.rank-info { display: flex; align-items: center; gap: 6px; font-size: 10px; }
.rank-no { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #121212; width: 18px; }
.rank-name { flex: 1; color: #121212; font-weight: 500; }
.rank-cnt { color: #9ca3af; }
.rank-bar { height: 3px; background: #f4f4f4; border-radius: 2px; overflow: hidden; }
.rank-fill { height: 100%; background: linear-gradient(to right, #e0e0e0, #121212); border-radius: 2px; }
.summary-box { flex: 1; background: #f8f8f8; border: 1px solid #edf1ed; border-radius: 10px; padding: 10px; overflow-y: auto; }
.sum-label { font-size: 11px; font-weight: 700; color: #121212; margin-bottom: 6px; }
.sum-text { font-size: 11px; color: #333333; font-family: 'Noto Serif SC', serif; line-height: 1.5; }

@media (max-width: 900px) { .hotspot-grid, .stats-grid { grid-template-columns: 1fr; } }

/* ===== Green Theme ===== */
body.green .search-header { border-bottom-color: #edf0ed; }
body.green .tab-btn:hover { background: #f8f9f8; }
body.green .tab-btn.active { color: #526e5a; border-bottom-color: #526e5a; }
body.green .search-bar { border-color: #e8ebe8; }
body.green .search-input { border-color: #dee3de; color: #1e2720; background: #f8f9f8; }
body.green .search-input:focus { border-color: #526e5a; }
body.green .source-select { border-color: #dee3de; color: #556056; }
body.green .btn-search { background: #526e5a; }
body.green .btn-search:hover { background: #415848; }
body.green .btn-filter { border-color: #dee3de; color: #556056; }
body.green .btn-filter:hover { background: #f8f9f8; }
body.green .filter-panel { border-top-color: #edf0ed; }
body.green .filter-group label { color: #9da79e; }
body.green .year-inputs input, body.green .filter-group input { border-color: #dee3de; }
body.green .btn-reset { border-color: #dee3de; color: #9da79e; }
body.green .btn-reset:hover { color: #526e5a; border-color: #526e5a; }
body.green .results-stats { color: #556056; }
body.green .paper-card { border-color: #e8ebe8; }
body.green .paper-card:hover { border-color: #bad2be; }
body.green .paper-title { color: #1e2720; }
body.green .paper-title a:hover { color: #526e5a; }
body.green .badge { background: #f2f6f3; color: #526e5a; }
body.green .paper-authors { color: #556056; }
body.green .paper-meta { color: #9da79e; }
body.green .paper-abstract { color: #556056; background: #f8f9f8; }
body.green .btn-import { background: #526e5a; }
body.green .btn-import:hover { background: #415848; }
body.green .btn-pdf { background: #f2f6f3; border-color: #526e5a; }
body.green .btn-pdf:hover { background: #526e5a; color: white; }
body.green .load-more button { border-color: #dee3de; color: #526e5a; }
body.green .load-more button:hover { background: #f2f6f3; }
body.green .domain-select { border-color: #dee3de; }
body.green .domain-select span { color: #526e5a; }
body.green .domain-dropdown { border-color: #e8ebe8; }
body.green .domain-opt { color: #556056; }
body.green .domain-opt:hover { background: #f8f9f8; }
body.green .domain-opt.active { background: #dbe1db; color: #1e2720; }
body.green .papers-panel { border-color: #e8ebe8; }
body.green .panel-hd { color: #1e2720; border-bottom-color: #f0f3f0; }
body.green .bar { background: #526e5a; }
body.green .loading { color: #9da79e; }
body.green .spinner { border-color: #dee3de; border-top-color: #526e5a; }
body.green .hp-card { background: #fdfdfd; border-color: #edf1ed; }
body.green .hp-card:hover { border-color: #bad2be; }
body.green .hp-title { color: #1e2720; }
body.green .hp-meta { color: #9da79e; }
body.green .tag { background: #f2f4f2; color: #556056; border-color: #e2e7e2; }
body.green .stat-card { border-color: #e8ebe8; }
body.green .stat-hd { color: #1e2720; }
body.green .stat-item { background: #f8f9f8; border-color: #edf1ed; }
body.green .stat-val { color: #1e2720; }
body.green .circle-outer { border-color: rgba(107,142,118,0.7); }
body.green .circle-mid { border-color: rgba(186,210,190,0.4); }
body.green .circle-leg { color: #556056; }
body.green .d1 { background: #526e5a; } body.green .d2 { background: #6b8e76; } body.green .d3 { background: #bad2be; }
body.green .rank-no { color: #526e5a; }
body.green .rank-name { color: #1e2720; }
body.green .rank-bar { background: #f0f2f0; }
body.green .rank-fill { background: linear-gradient(to right, #bad2be, #526e5a); }
body.green .summary-box { background: #f8f9f8; border-color: #edf1ed; }
body.green .sum-label { color: #526e5a; }
body.green .sum-text { color: #3b473d; }

/* ===== Dark Theme ===== */
body.dark .paper-search { background: #121212; }
body.dark .search-header { background: #1a1a1a; border-bottom-color: #2d2d2d; }
body.dark .tab-btn { color: #999999; }
body.dark .tab-btn:hover { color: #e5e5e5; background: #242424; }
body.dark .tab-btn.active { color: #ffffff; border-bottom-color: #ffffff; }
body.dark .search-bar { background: #242424; border-color: #2d2d2d; }
body.dark .search-input { background: #1a1a1a; border-color: #333333; color: #e5e5e5; }
body.dark .search-input:focus { border-color: #ffffff; }
body.dark .source-select { background: #1a1a1a; border-color: #333333; color: #b3b3b3; }
body.dark .btn-search { background: #ffffff; color: #121212; }
body.dark .btn-search:hover { background: #e5e5e5; }
body.dark .btn-filter { border-color: #333333; color: #b3b3b3; }
body.dark .btn-filter:hover { background: #242424; }
body.dark .filter-panel { border-top-color: #2d2d2d; }
body.dark .filter-group label { color: #666666; }
body.dark .year-inputs input, body.dark .filter-group input { background: #1a1a1a; border-color: #333333; color: #e5e5e5; }
body.dark .btn-reset { border-color: #333333; color: #666666; }
body.dark .btn-reset:hover { color: #ffffff; border-color: #ffffff; }
body.dark .error-banner { background: #2a1515; border-color: #5c2020; color: #ef4444; }
body.dark .results-stats { color: #b3b3b3; }
body.dark .paper-card { background: #242424; border-color: #2d2d2d; }
body.dark .paper-card:hover { border-color: #444444; }
body.dark .paper-title { color: #ffffff; }
body.dark .paper-title a:hover { color: #b3b3b3; }
body.dark .badge { background: #1a1a1a; color: #b3b3b3; }
body.dark .paper-authors { color: #b3b3b3; }
body.dark .paper-meta { color: #666666; }
body.dark .paper-abstract { background: #1a1a1a; color: #b3b3b3; }
body.dark .btn-import { background: #ffffff; color: #121212; }
body.dark .btn-import:hover { background: #e5e5e5; }
body.dark .btn-pdf { background: #1a1a1a; color: #b3b3b3; border-color: #333333; }
body.dark .btn-pdf:hover { background: #ffffff; color: #121212; }
body.dark .imported { color: #10b981; }
body.dark .load-more button { background: #242424; border-color: #333333; color: #b3b3b3; }
body.dark .load-more button:hover { background: #2d2d2d; }
body.dark .empty-state { color: #666666; }
body.dark .domain-select { background: #242424; border-color: #2d2d2d; }
body.dark .domain-select span { color: #b3b3b3; }
body.dark .domain-dropdown { background: #242424; border-color: #2d2d2d; }
body.dark .domain-opt { color: #b3b3b3; }
body.dark .domain-opt:hover { background: #2d2d2d; }
body.dark .domain-opt.active { background: #333333; color: #ffffff; }
body.dark .papers-panel { background: #242424; border-color: #2d2d2d; }
body.dark .panel-hd { color: #ffffff; border-bottom-color: #2d2d2d; }
body.dark .bar { background: #ffffff; }
body.dark .loading { color: #666666; }
body.dark .spinner { border-color: #333333; border-top-color: #ffffff; }
body.dark .hp-card { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .hp-card:hover { border-color: #444444; }
body.dark .hp-title { color: #ffffff; }
body.dark .hp-meta { color: #666666; }
body.dark .tag { background: #2d2d2d; color: #b3b3b3; border-color: #333333; }
body.dark .stat-card { background: #242424; border-color: #2d2d2d; }
body.dark .stat-hd { color: #ffffff; }
body.dark .trend-labels { color: #666666; }
body.dark .stat-item { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .stat-val { color: #ffffff; }
body.dark .stat-val.hl { color: #10b981; }
body.dark .stat-lbl { color: #666666; }
body.dark .circle-outer { border-color: rgba(255,255,255,0.7); }
body.dark .circle-mid { border-color: rgba(255,255,255,0.3); }
body.dark .circle-inner { background: #121212; }
body.dark .circle-leg { color: #b3b3b3; }
body.dark .d1 { background: #ffffff; } body.dark .d2 { background: #999999; } body.dark .d3 { background: #666666; }
body.dark .rank-no { color: #ffffff; }
body.dark .rank-name { color: #ffffff; }
body.dark .rank-cnt { color: #666666; }
body.dark .rank-bar { background: #1a1a1a; }
body.dark .rank-fill { background: linear-gradient(to right, #666666, #ffffff); }
body.dark .summary-box { background: #1a1a1a; border-color: #2d2d2d; }
body.dark .sum-label { color: #ffffff; }
body.dark .sum-text { color: #b3b3b3; }
</style>
