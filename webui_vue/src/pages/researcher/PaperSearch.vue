<template>
<div class="app">
  <ResearcherNav active-tab="paper-search" />

  <div class="page-wrapper">
    <!-- Search bar -->
    <div class="search-card">
      <div class="search-row">
        <input
          type="text"
          class="search-input"
          v-model="query"
          placeholder="搜索论文标题、关键词、作者…"
          @keyup.enter="doSearch"
        />
        <select class="source-select" v-model="source">
          <option value="openalex">OpenAlex</option>
          <option value="semantic_scholar">Semantic Scholar</option>
          <option value="arxiv">arXiv</option>
          <option value="crossref">CrossRef</option>
        </select>
        <button class="btn-search" @click="doSearch" :disabled="loading">
          {{ loading ? '搜索中…' : '搜索' }}
        </button>
        <button class="btn-filter" @click="showFilters = !showFilters">
          {{ showFilters ? '收起筛选' : '高级筛选' }}
        </button>
      </div>

      <!-- Advanced filters -->
      <div v-if="showFilters" class="filter-panel">
        <div class="filter-row">
          <div class="filter-group">
            <label>年份范围</label>
            <div class="year-inputs">
              <input type="number" v-model.number="yearFrom" placeholder="起始年" min="1900" max="2099" />
              <span>—</span>
              <input type="number" v-model.number="yearTo" placeholder="结束年" min="1900" max="2099" />
            </div>
          </div>
          <div class="filter-group">
            <label>作者</label>
            <input type="text" v-model="authorFilter" placeholder="作者姓名" />
          </div>
          <button class="btn-reset" @click="resetFilters">重置筛选</button>
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="error-banner">{{ error }}</div>

    <!-- Results stats -->
    <div v-if="results.length > 0" class="results-stats">
      共找到 {{ total.toLocaleString() }} 篇论文，当前显示 {{ results.length }} 篇
      <span class="source-badge">{{ sourceLabel }}</span>
    </div>

    <!-- Results list -->
    <div class="results-list">
      <div
        v-for="(paper, i) in results"
        :key="paper.id + '-' + i"
        class="paper-card"
      >
        <div class="paper-header">
          <h3 class="paper-title">
            <a v-if="paper.url" :href="paper.url" target="_blank" rel="noopener">{{ paper.title }}</a>
            <span v-else>{{ paper.title }}</span>
          </h3>
          <div class="paper-badges">
            <span class="badge-source">{{ paper.source }}</span>
            <span v-if="paper.venue" class="badge-venue">{{ paper.venue }}</span>
          </div>
        </div>

        <div class="paper-authors" v-if="paper.authors?.length">
          {{ Array.isArray(paper.authors) ? paper.authors.slice(0, 4).join(', ') : paper.authors }}
          <span v-if="Array.isArray(paper.authors) && paper.authors.length > 4"> et al.</span>
        </div>

        <div class="paper-meta">
          <span v-if="paper.year" class="meta-item">📅 {{ paper.year }}</span>
          <span v-if="paper.citations" class="meta-item">📊 引用 {{ paper.citations }}</span>
          <span v-if="paper.doi" class="meta-item">🔗 {{ paper.doi }}</span>
        </div>

        <div class="paper-abstract" v-if="paper.abstract">
          {{ paper.abstract.length > 300 ? paper.abstract.substring(0, 300) + '…' : paper.abstract }}
        </div>

        <div class="paper-actions">
          <button
            class="btn-import"
            @click="doImport(paper)"
            :disabled="importingId === paper.id || !paper.pdfUrl"
            :title="!paper.pdfUrl ? '该论文无可用 PDF' : ''"
          >
            {{ importingId === paper.id ? '导入中…' : '📥 导入到文库' }}
          </button>
          <a v-if="paper.pdfUrl" :href="paper.pdfUrl" target="_blank" class="btn-pdf">📄 查看 PDF</a>
          <span v-if="importedIds.has(paper.id)" class="imported-badge">✅ 已导入</span>
        </div>
      </div>
    </div>

    <!-- Load more -->
    <div v-if="results.length > 0 && results.length < total" class="load-more">
      <button @click="loadMore" :disabled="loading">
        {{ loading ? '加载中…' : '加载更多' }}
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && searched && results.length === 0" class="empty-state">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">未找到相关论文</div>
      <div class="empty-hint">请尝试不同的关键词或数据源</div>
    </div>

    <!-- Initial state -->
    <div v-if="!searched && !loading" class="empty-state">
      <div class="empty-icon">📚</div>
      <div class="empty-text">搜索学术论文</div>
      <div class="empty-hint">支持 Semantic Scholar、arXiv、CrossRef、OpenAlex 四大学术数据源</div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ResearcherNav from '../../components/ResearcherNav.vue'
import { usePaperSearch } from '../../composables/usePaperSearch.js'

const { loading, error, results, total, importing, searchPapers, importPaper, clearResults } = usePaperSearch()

const query = ref('')
const source = ref('openalex')
const showFilters = ref(false)
const yearFrom = ref(null)
const yearTo = ref(null)
const authorFilter = ref('')
const searched = ref(false)
const importingId = ref(null)
const importedIds = ref(new Set())

const sourceLabel = computed(() => {
  const labels = {
    semantic_scholar: 'Semantic Scholar',
    arxiv: 'arXiv',
    crossref: 'CrossRef',
    openalex: 'OpenAlex',
  }
  return labels[source.value] || source.value
})

async function doSearch() {
  if (!query.value.trim()) return
  searched.value = true
  importedIds.value = new Set()
  await searchPapers(query.value, source.value, {
    yearFrom: yearFrom.value,
    yearTo: yearTo.value,
    author: authorFilter.value,
  })
}

async function loadMore() {
  await searchPapers(query.value, source.value, {
    offset: results.value.length,
    yearFrom: yearFrom.value,
    yearTo: yearTo.value,
    author: authorFilter.value,
    append: true,
  })
}

async function doImport(paper) {
  if (!paper.pdfUrl) return
  importingId.value = paper.id
  try {
    await importPaper(paper)
    importedIds.value.add(paper.id)
  } catch {
    // error is handled in composable
  } finally {
    importingId.value = null
  }
}

function resetFilters() {
  yearFrom.value = null
  yearTo.value = null
  authorFilter.value = ''
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
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

/* Search card */
.search-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px var(--shadow);
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 16px;
  border: 1px solid var(--card-border);
  border-radius: 12px;
  background: var(--bg);
  color: var(--text1);
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
}

.source-select {
  padding: 10px 12px;
  border: 1px solid var(--card-border);
  border-radius: 12px;
  background: var(--bg);
  color: var(--text1);
  font-size: 0.85rem;
  outline: none;
  cursor: pointer;
}

.btn-search, .btn-filter {
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-search {
  background: var(--accent);
  color: #fff;
}

.btn-search:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-search:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-filter {
  background: var(--accent-light);
  color: var(--accent);
}

.btn-filter:hover {
  background: var(--accent);
  color: #fff;
}

/* Filter panel */
.filter-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--card-border);
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 0.75rem;
  color: var(--text2);
  font-weight: 600;
}

.filter-group input {
  padding: 8px 12px;
  border: 1px solid var(--card-border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text1);
  font-size: 0.85rem;
  outline: none;
  width: 140px;
}

.filter-group input:focus {
  border-color: var(--accent);
}

.year-inputs {
  display: flex;
  align-items: center;
  gap: 6px;
}

.year-inputs input {
  width: 100px;
}

.year-inputs span {
  color: var(--text3);
}

.btn-reset {
  padding: 8px 16px;
  border: 1px solid var(--card-border);
  border-radius: 10px;
  background: transparent;
  color: var(--text2);
  font-size: 0.8rem;
  cursor: pointer;
}

.btn-reset:hover {
  border-color: var(--accent);
  color: var(--accent);
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

/* Results stats */
.results-stats {
  font-size: 0.8rem;
  color: var(--text2);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-badge {
  background: var(--accent-light);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Paper cards */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 2px 12px var(--shadow);
  transition: transform 0.15s, box-shadow 0.15s;
}

.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px var(--shadow);
}

.paper-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 6px;
}

.paper-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text1);
  margin: 0;
  line-height: 1.4;
  flex: 1;
}

.paper-title a {
  color: var(--text1);
  text-decoration: none;
}

.paper-title a:hover {
  color: var(--accent);
}

.paper-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.badge-source, .badge-venue {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge-source {
  background: var(--accent-light);
  color: var(--accent);
}

.badge-venue {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

:global(body.dark) .badge-venue {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.paper-authors {
  font-size: 0.82rem;
  color: var(--text2);
  margin-bottom: 6px;
}

.paper-meta {
  display: flex;
  gap: 14px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 0.75rem;
  color: var(--text3);
}

.paper-abstract {
  font-size: 0.8rem;
  color: var(--text2);
  line-height: 1.6;
  margin-bottom: 12px;
}

.paper-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.btn-import, .btn-pdf {
  padding: 6px 14px;
  border: none;
  border-radius: 10px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn-import {
  background: var(--accent);
  color: #fff;
}

.btn-import:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-import:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-pdf {
  background: var(--accent-light);
  color: var(--accent);
}

.btn-pdf:hover {
  background: var(--accent);
  color: #fff;
}

.imported-badge {
  font-size: 0.75rem;
  color: #16a34a;
  font-weight: 600;
}

/* Load more */
.load-more {
  text-align: center;
  margin-top: 20px;
}

.load-more button {
  padding: 10px 32px;
  border: 1px solid var(--card-border);
  border-radius: 12px;
  background: var(--card);
  color: var(--accent);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.load-more button:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
}

.load-more button:disabled {
  opacity: 0.5;
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

@media (max-width: 900px) {
  .search-row {
    flex-direction: column;
  }
  .search-input, .source-select {
    width: 100%;
  }
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-group input {
    width: 100%;
  }
  .year-inputs input {
    flex: 1;
  }
  .paper-header {
    flex-direction: column;
  }
}
</style>
