<template>
<div class="app">
  <ResearcherNav active-tab="hotspot">
    <template #nav-extra>
      <select class="domain-select" v-model="currentDomain" @change="switchDomain(currentDomain)">
        <option v-for="d in domains" :key="d.key" :value="d.key">{{ d.label }}</option>
      </select>
      <input type="text" class="search-input" v-model="searchQuery" placeholder="检索论文、基因、品种…" @keyup.enter="handleSearch">
    </template>
  </ResearcherNav>

  <div class="main-wrapper" ref="mainWrapper">
    <!-- 左栏：最新论文 -->
    <div class="column col-left" ref="colLeft">
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>📄 最新论文 · <span>{{ domainData.label }}</span>
          <span v-if="isLoading" class="loading-badge">加载中...</span>
          <span v-if="loadError" class="error-badge" :title="loadError">API错误</span>
        </div>
        <div class="card-body">
          <div v-if="isLoading && !domainData.papers?.length" class="loading-state">
            <div class="loading-spinner"></div>
            <div>正在从OpenAlex获取数据...</div>
          </div>
          <div v-else class="paper-grid">
            <div v-for="(p, i) in domainData.papers" :key="i" class="paper-mini" @click="openPaper(p)">
              <div class="paper-title">{{ p.title }}</div>
              <div class="paper-meta">{{ p.authors }} · {{ p.journal }} · 引用{{ p.citations }}</div>
              <div class="paper-tags">
                <span v-for="t in p.tags" :key="t" class="paper-tag">{{ t }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 拖拽条1 -->
    <div class="resize-bar" ref="bar1" @mousedown="startResize($event, 'bar1')"></div>
    <!-- 中栏：趋势图 + 热搜榜 -->
    <div class="column col-mid" ref="colMid">
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>📈 近5年发表趋势</div>
        <div class="card-body">
          <div class="chart-wrap"><svg viewBox="0 0 400 130" preserveAspectRatio="xMidYMid meet" v-html="trendSvg"></svg></div>
          <div class="stat-row">
            <div v-for="(s, i) in domainData.stats" :key="i" class="stat-card">
              <div class="stat-val">{{ s.val }}</div>
              <div class="stat-lbl">{{ s.lbl }}</div>
            </div>
          </div>
          <div class="trend-extra">{{ domainData.trendAnalysis }}</div>
        </div>
      </div>
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>🔥 研究热搜榜</div>
        <div class="card-body">
          <div class="hot-search-list">
            <div v-for="(item, idx) in hotSearchItems" :key="idx" class="hot-item">
              <div class="hot-rank" :class="idx === 0 ? 'top1' : idx === 1 ? 'top2' : idx === 2 ? 'top3' : 'normal'">{{ idx + 1 }}</div>
              <div class="hot-info">
                <div class="hot-toprow">
                  <span class="hot-keyword">{{ item.kw }}</span>
                  <span class="hot-index">{{ Math.round(item.w * 100) }}</span>
                </div>
                <div class="hot-botrow">
                  <div class="hot-bar-wrap"><div class="hot-bar-fill" :style="{ width: item.w * 100 + '%' }"></div></div>
                  <span class="hot-papers">{{ Math.round(item.w * 120) }}篇</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 拖拽条2 -->
    <div class="resize-bar" ref="bar2" @mousedown="startResize($event, 'bar2')"></div>
    <!-- 右栏：旭日图 + 知识摘要 -->
    <div class="column col-right" ref="colRight">
      <div class="card flex-half">
        <div class="card-hd"><i></i>📊 研究热点图谱</div>
        <div class="card-body sunburst-card-body">
          <div ref="sunburstEl" id="sunburstChart"></div>
          <div class="sunburst-legend">
            <div class="legend-row"><span class="legend-dot infra"></span> 基础设施层</div>
            <div class="legend-row"><span class="legend-dot tech"></span> 关键技术层</div>
            <div class="legend-row"><span class="legend-dot scene"></span> 应用场景层</div>
          </div>
        </div>
      </div>
      <div class="card flex-half">
        <div class="card-hd"><i></i>📋 智能知识摘要</div>
        <div class="card-body insight-card-body">
          <div class="insight-scroll-wrap">
            <div class="insight-card">
              <div class="insight-title">📋 领域趋势总结</div>
              <div class="insight-text">{{ domainData.insight }}</div>
              <div class="insight-sources">
                <span v-for="s in domainData.insightSources" :key="s" class="insight-source">📄 {{ s }}</span>
              </div>
              <div class="insight-recommend">
                <div class="rec-title">📚 推荐阅读经典文献</div>
                <div v-for="(p, i) in domainData.recPapers" :key="i" class="rec-item">
                  • {{ p.title }} <span style="color:var(--text3);font-size:0.5rem;">— {{ p.authors }}, {{ p.journal }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Paper Detail Modal -->
  <Teleport to="body">
    <div v-if="showPaperModal" class="paper-modal-overlay" @click.self="closePaperModal">
      <div class="paper-modal">
        <div class="paper-modal-header">
          <h2 class="paper-modal-title">{{ selectedPaper?.title }}</h2>
          <button class="paper-modal-close" @click="closePaperModal">✕</button>
        </div>

        <div v-if="paperDetailLoading" class="paper-modal-loading">
          <div class="loading-spinner"></div>
          <span>加载论文详情...</span>
        </div>

        <div v-else-if="selectedPaper" class="paper-modal-content">
          <!-- Authors -->
          <div class="paper-detail-section">
            <div class="paper-detail-label">作者</div>
            <div class="paper-detail-authors">
              <span v-for="(auth, i) in selectedPaper.fullAuthorships.slice(0, 5)" :key="i" class="author-chip">
                {{ auth.author?.display_name }}
                <span v-if="auth.institutions?.[0]" class="author-inst"> · {{ auth.institutions[0].display_name }}</span>
              </span>
              <span v-if="selectedPaper.fullAuthorships.length > 5" class="author-more">
                等{{ selectedPaper.fullAuthorships.length }}位作者
              </span>
            </div>
          </div>

          <!-- Meta info -->
          <div class="paper-meta-grid">
            <div class="paper-meta-item">
              <span class="meta-icon">📰</span>
              <span class="meta-label">期刊</span>
              <span class="meta-value">{{ selectedPaper.sourceName }}</span>
            </div>
            <div class="paper-meta-item">
              <span class="meta-icon">📅</span>
              <span class="meta-label">发表日期</span>
              <span class="meta-value">{{ selectedPaper.publicationDate || selectedPaper.year }}</span>
            </div>
            <div class="paper-meta-item">
              <span class="meta-icon">📊</span>
              <span class="meta-label">引用次数</span>
              <span class="meta-value">{{ selectedPaper.citedByCount }} 次</span>
            </div>
            <div class="paper-meta-item">
              <span class="meta-icon">🔗</span>
              <span class="meta-label">DOI</span>
              <span class="meta-value doi-link" @click="openDoi(selectedPaper.doi)">
                {{ selectedPaper.doi ? selectedPaper.doi.replace('https://doi.org/', '') : '无' }}
              </span>
            </div>
          </div>

          <!-- Abstract -->
          <div v-if="selectedPaper.abstract" class="paper-detail-section">
            <div class="paper-detail-label">摘要</div>
            <div class="paper-abstract">{{ selectedPaper.abstract }}</div>
          </div>

          <!-- Keywords/Concepts -->
          <div v-if="selectedPaper.concepts?.length" class="paper-detail-section">
            <div class="paper-detail-label">关键词/概念</div>
            <div class="paper-keywords">
              <span v-for="(kw, i) in selectedPaper.concepts" :key="i" class="keyword-tag">
                {{ typeof kw === 'string' ? kw : kw.display_name }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="paper-actions">
            <a v-if="selectedPaper.pdfUrl" :href="selectedPaper.pdfUrl" target="_blank" class="paper-action-btn primary">
              📄 下载PDF
            </a>
            <a v-if="selectedPaper.oaUrl" :href="selectedPaper.oaUrl" target="_blank" class="paper-action-btn secondary">
              🔓 开放获取
            </a>
            <a v-if="selectedPaper.doi" :href="selectedPaper.doi" target="_blank" class="paper-action-btn secondary">
              🔗 原文链接
            </a>
            <button class="paper-action-btn outline" @click="closePaperModal">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import echarts from '../../utils/echarts.js'
import { useAuth } from '../../composables/useAuth.js'
import { useOpenAlex } from '../../composables/useOpenAlex.js'
import ResearcherNav from '../../components/ResearcherNav.vue'

const isDark = ref(false)
const currentDomain = ref('fruit')
const searchQuery = ref('')
const mainWrapper = ref(null)
const colLeft = ref(null)
const colMid = ref(null)
const colRight = ref(null)
const bar1 = ref(null)
const bar2 = ref(null)
const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
const { loading: apiLoading, error: apiError, fetchDomainData, searchPapers, getWorkDetails, reconstructAbstract, DOMAIN_QUERIES } = useOpenAlex()

// Paper detail modal
const selectedPaper = ref(null)
const paperDetailLoading = ref(false)
const showPaperModal = ref(false)

function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}
const sunburstEl = ref(null)
let chartInstance = null

const domains = [
  { key: 'fruit', label: '果树栽培' },
  { key: 'veg', label: '蔬菜育种' },
  { key: 'smart', label: '智慧农业' },
  { key: 'path', label: '植物病理' },
  { key: 'soil', label: '土壤改良' },
]

// Real data from OpenAlex API
const agriData = ref({})
const isLoading = ref(false)
const loadError = ref(null)

// Fallback mock data for when API fails
const fallbackData = {
  fruit: {
    label: '果树栽培',
    papers: [
      { id: null, title: '苹果砧木耐盐性分子机制及MdNHX1基因功能解析', authors: '张立新 等', journal: '园艺学报 2025', citations: 38, tags: ['苹果', '耐盐', '基因功能'] },
      { id: null, title: '基于多光谱遥感的柑橘黄龙病早期诊断模型', authors: '李慧 等', journal: 'Comput. Electron. Agric. 2025', citations: 27, tags: ['柑橘', '病害诊断', '遥感'] },
    ],
    keywords: ['基因编辑', '耐盐性', '砧木育种', '采后保鲜', '遥感监测'],
    kwWeights: [0.92, 0.82, 0.88, 0.75, 0.80],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [420, 560, 780, 1050, 1380],
    stats: [{ val: '1,380', lbl: '2025' }, { val: '↑31%', lbl: '年增长' }, { val: '3.2万', lbl: '引用' }, { val: '86', lbl: '核心期刊' }],
    trendAnalysis: '数据加载中，请稍候...',
    insight: '正在从OpenAlex获取最新研究数据...',
    insightSources: [],
    recPapers: []
  }
}

// Dynamic sunburst data based on real keywords
const sunburstData = computed(() => {
  const data = domainData.value
  if (!data || !data.keywords || data.keywords.length === 0) {
    return {
      name: "root",
      children: [{
        name: "加载中",
        children: [{ name: "请稍候", value: 50 }]
      }]
    }
  }

  // Generate sunburst from real keywords
  const topKeywords = data.keywords.slice(0, 6)
  const weights = data.kwWeights?.slice(0, 6) || topKeywords.map(() => 0.5)

  return {
    name: "root",
    children: [{
      name: data.label || "研究热点",
      children: topKeywords.map((kw, i) => ({
        name: kw,
        value: Math.round(weights[i] * 100) || 50
      }))
    }]
  }
})

const domainData = computed(() => {
  return agriData.value[currentDomain.value] || fallbackData[currentDomain.value] || fallbackData.fruit
})

// Fetch data from OpenAlex API
async function loadDomainData(domainKey) {
  isLoading.value = true
  loadError.value = null

  try {
    const data = await fetchDomainData(domainKey)
    agriData.value[domainKey] = data
  } catch (err) {
    console.error('Failed to load domain data:', err)
    loadError.value = err.message
    // Use fallback data if API fails
    if (!agriData.value[domainKey]) {
      agriData.value[domainKey] = fallbackData[domainKey] || fallbackData.fruit
    }
  } finally {
    isLoading.value = false
  }
}

const hotSearchItems = computed(() => {
  const data = domainData.value
  return data.keywords.map((kw, i) => ({ kw, w: data.kwWeights[i] }))
    .sort((a, b) => b.w - a.w)
    .slice(0, 6)
})

const trendSvg = computed(() => {
  const data = domainData.value
  const w = 400, h = 130, pad = 30
  const maxV = Math.max(...data.trendValues)
  const n = data.trendValues.length, xStep = (w - 2 * pad) / (n - 1)
  let html = ''
  for (let i = 0; i <= 4; i++) {
    const y = pad + (h - 2 * pad) * i / 4
    html += `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" stroke="var(--divider)" stroke-width="0.5"/>`
  }
  html += `<line x1="${pad}" y1="${h - pad}" x2="${w - pad}" y2="${h - pad}" stroke="var(--divider)" stroke-width="1"/>`
  let areaPts = `${pad},${h - pad} `
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep
    const y = h - pad - (v / maxV) * (h - 2 * pad)
    areaPts += `${x},${y} `
  })
  areaPts += `${pad + (n - 1) * xStep},${h - pad}`
  html += `<defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--chart-line)" stop-opacity="0.18"/><stop offset="100%" stop-color="var(--chart-line)" stop-opacity="0.02"/></linearGradient></defs>`
  html += `<polygon points="${areaPts}" fill="url(#ag)"/>`
  let linePts = ''
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep
    const y = h - pad - (v / maxV) * (h - 2 * pad)
    linePts += `${x},${y} `
  })
  html += `<polyline points="${linePts.trim()}" fill="none" stroke="var(--chart-line)" stroke-width="2" stroke-linejoin="round"/>`
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep, y = h - pad - (v / maxV) * (h - 2 * pad)
    html += `<circle cx="${x}" cy="${y}" r="3.5" fill="var(--card)" stroke="var(--chart-line)" stroke-width="2"/>`
    html += `<text x="${x}" y="${y - 10}" text-anchor="middle" font-size="7.5" fill="var(--accent)" font-weight="600">${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}</text>`
  })
  data.trendYears.forEach((yr, i) => {
    html += `<text x="${pad + i * xStep}" y="${h - 6}" text-anchor="middle" font-size="7" fill="var(--text3)">${yr}</text>`
  })
  return html
})

function switchDomain(key) {
  currentDomain.value = key
  // Load data if not already cached
  if (!agriData.value[key]) {
    loadDomainData(key)
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
  nextTick(() => {
    updateSunburstTheme()
    if (chartInstance) chartInstance.resize()
  })
}

function getSunBorderColor() {
  return document.body.classList.contains('dark') ? '#2d1b4e' : '#ffffff'
}

let initRetries = 0
function initSunburst() {
  if (!sunburstEl.value) return
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  const w = sunburstEl.value.clientWidth
  const h = sunburstEl.value.clientHeight
  if (w === 0 || h === 0) {
    initRetries++
    if (initRetries < 20) {
      requestAnimationFrame(() => initSunburst())
    }
    return
  }
  initRetries = 0
  chartInstance = echarts.init(sunburstEl.value)
  const borderColor = getSunBorderColor()
  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 10, 60, 0.95)',
      borderColor: '#a855f7',
      borderWidth: 1,
      textStyle: { color: '#f2eaff', fontSize: 11 },
      formatter: function(params) {
        if (!params.name || params.name === 'root') return ''
        const pathNodes = params.treePathInfo || []
        let pathStr = ''
        if (pathNodes.length > 1) {
          const names = pathNodes.slice(1).map(p => p.name)
          pathStr = names.join(' > ')
        }
        return '<strong>' + params.name + '</strong><br/>热度指数: ' + params.value +
          '<br/><span style="font-size:10px;color:#c4b5fd;">' + pathStr + '</span>'
      }
    },
    series: [{
      type: 'sunburst',
      data: [sunburstData.value],
      radius: [0, '78%'],
      center: ['50%', '52%'],
      sort: undefined,
      nodeClick: false,
      label: { show: false },
      emphasis: {
        focus: 'descendant',
        scale: true,
        label: {
          show: true,
          position: 'inside',
          fontSize: 8,
          fontWeight: '600',
          color: '#ffffff',
          textShadowBlur: 4,
          textShadowColor: 'rgba(0,0,0,0.6)',
          formatter: function(params) {
            if (params.name === 'root') return ''
            var n = params.name
            return n.length > 8 ? n.slice(0, 8) + '…' : n
          }
        },
        itemStyle: {
          shadowBlur: 14,
          shadowColor: 'rgba(130, 80, 200, 0.25)',
          borderWidth: 2,
          borderColor: '#ffffff'
        }
      },
      levels: [
        { r0: '0%', r: '18%', itemStyle: { color: '#4a3cc0', borderRadius: 0, borderWidth: 2.5, borderColor: borderColor } },
        { r0: '18%', r: '42%', itemStyle: { color: '#5a4cd8', borderRadius: 0, borderWidth: 2, borderColor: borderColor } },
        { r0: '42%', r: '60%', itemStyle: { color: '#6B5DF0', borderRadius: 0, borderWidth: 1.8, borderColor: borderColor } },
        { r0: '60%', r: '72%', itemStyle: { color: '#8B70FF', borderRadius: 0, borderWidth: 1.2, borderColor: borderColor } },
        { r0: '72%', r: '78%', itemStyle: { color: '#A78BFA', borderRadius: 0, borderWidth: 1, borderColor: borderColor } }
      ],
      itemStyle: { borderRadius: 0, borderColor: borderColor, borderWidth: 2 },
      animation: true,
      animationDuration: 800
    }]
  })
}

function updateSunburstTheme() {
  if (!chartInstance) return
  const borderColor = getSunBorderColor()
  chartInstance.setOption({
    series: [{
      levels: [
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } }
      ],
      itemStyle: { borderColor: borderColor }
    }]
  })
}

// ---- Resize bars ----
let resizingBar = null, startX, startLW, startRW

function startResize(e, barId) {
  resizingBar = barId
  e.target.classList.add('active')
  startX = e.clientX
  if (barId === 'bar1') {
    startLW = colLeft.value.getBoundingClientRect().width
    startRW = colMid.value.getBoundingClientRect().width
  } else {
    startLW = colMid.value.getBoundingClientRect().width
    startRW = colRight.value.getBoundingClientRect().width
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMove(e) {
  if (!resizingBar) return
  const dx = e.clientX - startX
  const ww = mainWrapper.value.getBoundingClientRect().width
  let nl = startLW + dx, nr = startRW - dx
  if (nl < 200) nl = 200
  if (nr < 200) nr = 200
  if (resizingBar === 'bar1') {
    colLeft.value.style.width = (nl / ww * 100) + '%'
    colMid.value.style.width = (nr / ww * 100) + '%'
  } else {
    colMid.value.style.width = (nl / ww * 100) + '%'
    colRight.value.style.width = (nr / ww * 100) + '%'
  }
}

function onMouseUp() {
  if (resizingBar) {
    document.querySelectorAll('.resize-bar').forEach(b => b.classList.remove('active'))
    resizingBar = null
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    if (chartInstance) chartInstance.resize()
  }
}

function onWindowResize() {
  if (chartInstance) chartInstance.resize()
}

// Handle search
async function handleSearch() {
  if (!searchQuery.value.trim()) return

  isLoading.value = true
  try {
    const results = await searchPapers(searchQuery.value, 10)
    // Update current domain's papers with search results
    if (agriData.value[currentDomain.value]) {
      agriData.value[currentDomain.value].papers = results
    }
  } catch (err) {
    console.error('Search failed:', err)
  } finally {
    isLoading.value = false
  }
}

// Open paper detail modal
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
    // Fetch full details from OpenAlex if we have an ID
    if (paper.id) {
      const details = await getWorkDetails(paper.id)
      const abstract = reconstructAbstract(details.abstract_inverted_index)

      selectedPaper.value = {
        ...selectedPaper.value,
        abstract: abstract,
        oaUrl: details.open_access?.oa_url || null,
        pdfUrl: details.best_oa_location?.pdf_url || details.open_access?.oa_url || null,
        doi: details.doi || paper.doi,
        fullAuthorships: details.authorships || [],
        concepts: details.concepts?.slice(0, 8) || paper.tags,
        referencedWorks: details.referenced_works_count || 0,
        citedByCount: details.cited_by_count || paper.citations,
        publicationDate: details.publication_date || null,
        type: details.type || 'article',
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

// Watch for search input changes with debounce
let searchTimeout = null
watch(searchQuery, (newVal) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  if (newVal.trim()) {
    searchTimeout = setTimeout(() => handleSearch(), 500)
  }
})

// Re-render sunburst when domain data changes
watch(domainData, () => {
  nextTick(() => {
    if (chartInstance) {
      chartInstance.setOption({
        series: [{ data: [sunburstData.value] }]
      })
    }
  })
}, { deep: true })

onMounted(async () => {
  // Load initial domain data from OpenAlex
  await loadDomainData(currentDomain.value)

  nextTick(() => {
    requestAnimationFrame(() => {
      initSunburst()
    })
  })
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('resize', onWindowResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style>
:root {
  --bg: #f8f6f1;
  --card: #ffffff;
  --nav-bg: #ffffff;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.15);
  --accent-glow: rgba(91,141,239,0.15);
  --border: #e8e4db;
  --text: #2c2c2c;
  --text2: #666666;
  --text3: #999999;
  --divider: #e8e4db;
  --radius: 16px;
  --radius-sm: 10px;
  --chart-line: #5b8def;
  --tag-bg: #eef4ff;
  --tag-border: rgba(91,141,239,0.25);
  --insight-accent: #5b8def;
  --scrollbar-thumb: rgba(0,0,0,0.15);
  --insight-scroll-thumb: rgba(91,141,239,0.35);
  --insight-scroll-track: rgba(91,141,239,0.06);
}
body.dark {
  --bg: #12121a;
  --card: #1e1e2e;
  --nav-bg: #1e1e2e;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.2);
  --accent-glow: rgba(91,141,239,0.2);
  --border: #333333;
  --text: #e0e0e0;
  --text2: #aaaaaa;
  --text3: #777777;
  --divider: #333333;
  --chart-line: #5b8def;
  --tag-bg: rgba(91,141,239,0.1);
  --tag-border: rgba(91,141,239,0.3);
  --insight-accent: #5b8def;
  --scrollbar-thumb: rgba(255,255,255,0.15);
  --insight-scroll-thumb: rgba(91,141,239,0.45);
  --insight-scroll-track: rgba(91,141,239,0.08);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg); color: var(--text); height: 100vh; overflow: hidden;
  transition: 0.3s; letter-spacing: 0.01em;
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 10px; }
.insight-scroll-wrap::-webkit-scrollbar { width: 8px; }
.insight-scroll-wrap::-webkit-scrollbar-track { background: var(--insight-scroll-track); border-radius: 10px; margin: 4px 0; }
.insight-scroll-wrap::-webkit-scrollbar-thumb { background: var(--insight-scroll-thumb); border-radius: 10px; border: 2px solid transparent; background-clip: padding-box; min-height: 40px; }
.insight-scroll-wrap::-webkit-scrollbar-thumb:hover { background: var(--accent); border: 2px solid transparent; background-clip: padding-box; }
.insight-scroll-wrap { scrollbar-width: thin; scrollbar-color: var(--insight-scroll-thumb) var(--insight-scroll-track); }

.app { display: flex; flex-direction: column; height: 100vh; max-width: 1832px; margin: 0 auto; padding: 6px 10px; gap: 4px; }

/* Top nav */
.top-nav {
  flex-shrink: 0; height: 48px; background: var(--nav-bg);
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0 20px; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 0 0 1px var(--accent-light), 0 0 18px var(--accent-glow);
}
.nav-left { display: flex; align-items: center; gap: 16px; }
.nav-logo {
  font-family: 'Playfair Display', serif; font-style: italic;
  font-size: 1.1rem; font-weight: 700; color: var(--accent);
  display: flex; align-items: center; gap: 8px;
}
.nav-logo .dot { width: 7px; height: 7px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 14px var(--accent-glow); animation: dotPulse 2.4s infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:0.5} }
.nav-right { display: flex; gap: 8px; align-items: center; }
.nav-center { display: flex; align-items: center; gap: 4px; }
.nav-tab {
  padding: 6px 14px; border-radius: 14px; font-size: 0.78rem; font-weight: 500;
  color: var(--text2); cursor: pointer; transition: all 0.2s; border: 1.5px solid transparent;
}
.nav-tab:hover { color: var(--text); background: var(--accent-light); }
.nav-tab.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow);
}

.domain-nav { display: flex; gap: 2px; flex-wrap: wrap; }
.domain-btn {
  padding: 6px 14px; border: 1.5px solid transparent; background: transparent;
  color: var(--text2); font-weight: 500; font-size: 0.78rem; cursor: pointer;
  transition: 0.2s; border-radius: 20px; letter-spacing: 0.03em; white-space: nowrap;
}
.domain-btn.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  font-weight: 600; box-shadow: inset 0 0 0 1px var(--accent-glow), 0 0 12px var(--accent-glow);
}
.search-input {
  padding: 7px 14px; border: 2px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.75rem; width: 170px; border-radius: 20px;
  font-family: inherit; transition: 0.2s;
}
.search-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
.domain-select {
  padding: 7px 10px; border: 2px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.75rem; border-radius: 20px;
  font-family: inherit; cursor: pointer; transition: 0.2s; outline: none;
}
.domain-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
.icon-btn {
  width: 32px; height: 32px; border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; color: var(--text2); font-size: 0.85rem; transition: 0.2s;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.icon-btn svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 1.8; }
.icon-btn:hover { color: var(--accent); border-color: var(--accent); box-shadow: 0 0 14px var(--accent-glow); }

.main-wrapper { flex: 1; min-height: 0; display: flex; gap: 0; position: relative; }
.column { display: flex; flex-direction: column; gap: 4px; padding: 0 3px; }
.col-left { width: 28.4%; min-width: 260px; }
.col-mid { width: 38.6%; min-width: 280px; }
.col-right { width: 33%; min-width: 260px; }
.resize-bar {
  width: 5px; cursor: col-resize; background: transparent; position: relative; z-index: 10;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: background 0.2s;
}
.resize-bar:hover, .resize-bar.active { background: var(--accent-light); }
.resize-bar::after {
  content: ''; width: 2px; height: 40px; background: var(--accent);
  border-radius: 1px; opacity: 0.4;
}
.resize-bar:hover::after { opacity: 0.8; }

.card {
  background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden;
  display: flex; flex-direction: column;
  transition: box-shadow 0.3s;
}
.card:hover { border-color: var(--accent); box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.card-hd {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  border-bottom: 1px solid var(--divider); font-weight: 700; font-size: 0.8rem;
  text-transform: uppercase; letter-spacing: 0.04em; flex-shrink: 0;
}
.card-hd i { width: 4px; height: 16px; background: linear-gradient(180deg, var(--accent), #4a3cc0); border-radius: 2px; box-shadow: 0 0 6px var(--accent-glow); }
.card-body { padding: 8px 12px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 3px; flex: 1; min-height: 0; }
.card.flex-half { flex: 1; min-height: 0; max-height: 50%; }

.sunburst-card-body { overflow: hidden; padding: 4px 6px 6px 6px; display: flex; align-items: center; justify-content: center; position: relative; }
#sunburstChart { width: 100%; height: 100%; min-height: 180px; }

.sunburst-legend {
  position: absolute; top: 8px; right: 10px; display: flex; flex-direction: column; gap: 4px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 6px 10px; z-index: 20; pointer-events: none;
}
.legend-row { display: flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 500; color: var(--text); white-space: nowrap; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.legend-dot.infra { background: #4a3cc0; }
.legend-dot.tech { background: #5a4cd8; }
.legend-dot.scene { background: #8B70FF; }
body.dark .legend-dot.infra { background: #6d28d9; }
body.dark .legend-dot.tech { background: #7c3aed; }
body.dark .legend-dot.scene { background: #a78bfa; }

.card-body.insight-card-body { overflow-y: hidden; padding: 8px 8px 8px 12px; }

.paper-grid { display: flex; flex-direction: column; gap: 4px; }
.paper-mini {
  background: var(--tag-bg); border: 1px solid var(--tag-border); padding: 8px 10px;
  cursor: pointer; transition: 0.2s; font-size: 0.75rem; border-radius: var(--radius-sm); flex-shrink: 0;
}
.paper-mini:hover { border-color: var(--accent); background: var(--accent-light); box-shadow: 0 0 10px var(--accent-glow); transform: translateY(-1px); }
.paper-title { font-weight: 600; color: var(--text); font-size: 0.75rem; line-height: 1.4; }
.paper-meta { font-size: 0.72rem; color: var(--text3); margin-top: 2px; }
.paper-tags { margin-top: 4px; display: flex; gap: 3px; flex-wrap: wrap; }
.paper-tag {
  display: inline-block; padding: 2px 6px; border: 1px solid var(--accent);
  color: var(--accent); font-size: 0.72rem; font-weight: 500; cursor: pointer;
  transition: 0.15s; border-radius: 12px; background: var(--tag-bg);
}
.paper-tag:hover { background: var(--accent); color: #fff; }

/* Loading states */
.loading-badge {
  font-size: 0.72rem;
  background: var(--accent-light);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  animation: pulse 1.5s infinite;
}

.error-badge {
  font-size: 0.72rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  cursor: help;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text3);
  font-size: 0.75rem;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3px; margin-top: 2px; flex-shrink: 0; }
.stat-card { background: var(--tag-bg); border: 1px solid var(--tag-border); padding: 8px 4px 6px; text-align: center; border-radius: var(--radius-sm); transition: 0.2s; }
.stat-val { font-weight: 700; font-size: 0.75rem; color: var(--accent); }
.stat-lbl { font-size: 0.72rem; color: var(--text3); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.03em; }
.chart-wrap { display: flex; align-items: center; justify-content: center; flex: 1; min-height: 0; }
.chart-wrap svg { width: 100%; height: auto; max-height: 100%; }
.trend-extra { font-size: 0.72rem; color: var(--text2); line-height: 1.6; padding: 6px 0 0; border-top: 1px solid var(--divider); margin-top: 2px; flex-shrink: 0; }

.hot-search-list { display: flex; flex-direction: column; gap: 1px; }
.hot-item { display: flex; align-items: center; gap: 8px; padding: 3px 6px; border-radius: var(--radius-sm); transition: background 0.2s; cursor: pointer; flex-shrink: 0; }
.hot-item:hover { background: var(--accent-light); }
.hot-rank { width: 20px; height: 20px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.75rem; flex-shrink: 0; }
.hot-rank.top1 { background: linear-gradient(135deg, #6d28d9, #7c3aed); color: #fff; }
.hot-rank.top2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); color: #fff; }
.hot-rank.top3 { background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: #fff; }
.hot-rank.normal { background: var(--accent-light); color: var(--accent); }
.hot-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.hot-toprow { display: flex; align-items: baseline; gap: 8px; }
.hot-keyword { font-weight: 600; font-size: 0.75rem; color: var(--text); }
.hot-index { font-weight: 700; color: var(--accent); font-size: 0.72rem; flex-shrink: 0; }
.hot-botrow { display: flex; align-items: center; gap: 8px; }
.hot-bar-wrap { flex: 1; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
.hot-bar-fill { height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--accent), #A78BFA); }
.hot-papers { font-size: 0.72rem; color: var(--text3); flex-shrink: 0; }

.heat-matrix { display: flex; flex-wrap: wrap; gap: 4px; align-content: flex-start; justify-content: center; padding: 4px 0; }

.insight-scroll-wrap { flex: 1; min-height: 0; overflow-y: auto; padding-right: 4px; display: flex; flex-direction: column; gap: 6px; }
.insight-card {
  background: var(--card); border: 1px solid var(--tag-border); border-radius: var(--radius-sm);
  padding: 12px 14px; position: relative; overflow: hidden; flex-shrink: 0;
}
.insight-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--insight-accent); border-radius: 2px 0 0 2px; }
.insight-title { font-weight: 700; font-size: 0.7rem; color: var(--accent); margin-bottom: 6px; letter-spacing: 0.03em; }
.insight-text { font-size: 0.75rem; color: var(--text2); line-height: 1.7; margin-bottom: 8px; }
.insight-sources { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px; }
.insight-source { font-size: 0.72rem; padding: 2px 7px; border: 1px solid var(--accent); color: var(--accent); border-radius: 12px; background: var(--tag-bg); }
.insight-recommend { border-top: 1px solid var(--divider); padding-top: 6px; margin-top: 3px; }
.rec-title { font-weight: 700; font-size: 0.75rem; color: var(--accent); margin-bottom: 3px; }
.rec-item { font-size: 0.72rem; color: var(--text2); line-height: 1.5; padding: 1px 0; cursor: pointer; transition: 0.2s; }
.rec-item:hover { color: var(--accent); text-decoration: underline; }

@media(max-width:900px) {
  .main-wrapper { flex-direction: column; overflow-y: auto; }
  .resize-bar { display: none; }
  .col-left, .col-mid, .col-right { width: 100% !important; min-width: 0; flex: none; }
  #sunburstChart { min-height: 240px; }
}

/* Paper Detail Modal */
.paper-modal-overlay {
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

.paper-modal {
  background: var(--card);
  border: 2px solid var(--accent);
  border-radius: var(--radius);
  max-width: 700px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px var(--accent-glow);
  animation: slideUp 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.paper-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--divider);
  gap: 16px;
}

.paper-modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.4;
  flex: 1;
}

.paper-modal-close {
  width: 32px;
  height: 32px;
  border: 1.5px solid var(--border);
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text3);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.paper-modal-close:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-light);
}

.paper-modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--text3);
}

.paper-modal-content {
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.paper-detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.paper-detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.paper-detail-authors {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.author-chip {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 14px;
  color: var(--text);
}

.author-inst {
  color: var(--text3);
  font-size: 0.72rem;
}

.author-more {
  font-size: 0.75rem;
  color: var(--text3);
  padding: 4px 8px;
}

.paper-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.paper-meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: var(--radius-sm);
}

.meta-icon {
  font-size: 0.9rem;
}

.meta-label {
  font-size: 0.72rem;
  color: var(--text3);
  min-width: 50px;
}

.meta-value {
  font-size: 0.75rem;
  color: var(--text);
  font-weight: 500;
}

.doi-link {
  color: var(--accent);
  cursor: pointer;
  text-decoration: underline;
}

.doi-link:hover {
  opacity: 0.8;
}

.paper-abstract {
  font-size: 0.75rem;
  line-height: 1.7;
  color: var(--text2);
  padding: 12px 14px;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: var(--radius-sm);
  text-align: justify;
}

.paper-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword-tag {
  font-size: 0.72rem;
  padding: 4px 10px;
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 14px;
  background: var(--tag-bg);
}

.paper-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.paper-action-btn {
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.paper-action-btn.primary {
  background: var(--accent);
  color: #fff;
  border: 2px solid var(--accent);
}

.paper-action-btn.primary:hover {
  opacity: 0.9;
  box-shadow: 0 4px 12px var(--accent-glow);
}

.paper-action-btn.secondary {
  background: var(--accent-light);
  color: var(--accent);
  border: 2px solid var(--accent);
}

.paper-action-btn.secondary:hover {
  background: var(--accent);
  color: #fff;
}

.paper-action-btn.outline {
  background: transparent;
  color: var(--text3);
  border: 2px solid var(--border);
}

.paper-action-btn.outline:hover {
  border-color: var(--accent);
  color: var(--accent);
}

@media(max-width: 600px) {
  .paper-modal {
    max-height: 95vh;
    margin: 10px;
  }

  .paper-meta-grid {
    grid-template-columns: 1fr;
  }

  .paper-actions {
    flex-direction: column;
  }

  .paper-action-btn {
    justify-content: center;
  }
}
</style>
