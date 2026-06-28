<template>
<div class="data-lab">
  <!-- Left: Controls Panel -->
  <section class="controls-panel">
    <div class="controls-content">
      <button class="back-btn" @click="emit('back')">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
        <span>返回工具选单</span>
      </button>
      <div class="control-section">
        <label class="control-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>
          </svg>
          <span>数据源导入</span>
        </label>
        <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          <div class="upload-text">点击或拖拽解析矩阵文件</div>
          <div class="upload-hint" v-if="fileName">{{ fileName }}</div>
          <div class="upload-hint" v-else>支持 CSV / Excel (.xlsx .xls)</div>
          <input type="file" id="fileInput" accept=".csv,.xlsx,.xls" @change="onFileChange" style="display:none">
        </div>
        <button class="btn-sample" @click="loadSampleData">加载园艺实验数据</button>
      </div>

      <div class="control-section">
        <label class="control-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/>
          </svg>
          <span>映射变量选择</span>
        </label>
        <div class="select-group">
          <span class="select-label">X 轴映射变量</span>
          <div class="select-wrapper">
            <select v-model="xCol" @change="updateAll">
              <option v-for="c in columns" :key="c" :value="c">{{ c }}</option>
              <option v-if="columns.length === 0">请先上传数据</option>
            </select>
            <svg class="select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </div>
        </div>
        <div class="select-group">
          <span class="select-label">Y 轴映射变量 (可选)</span>
          <div class="select-wrapper">
            <select v-model="yCol" @change="updateAll">
              <option value="">— 不选择 —</option>
              <option v-for="c in numericCols" :key="c" :value="c">{{ c }}</option>
            </select>
            <svg class="select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="control-section">
        <span class="select-label">图表流派类型</span>
        <div class="chart-type-grid">
          <button
            v-for="ct in chartTypes"
            :key="ct.key"
            class="chart-type-btn"
            :class="{ active: currentChartType === ct.key }"
            @click="switchChartType(ct.key)"
          >{{ ct.label }}</button>
        </div>
      </div>
    </div>

    <button class="btn-render" @click="updateAll">
      同步更新渲染
    </button>
  </section>

  <!-- Main: Visualization Area -->
  <main class="main-content">
    <div class="chart-area">
      <div class="chart-header">
        <span class="chart-title">{{ chartTitle }}</span>
        <span class="chart-hint">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 9l-3 3 3 3"/><path d="M9 5l3-3 3 3"/><path d="M15 19l-3 3-3-3"/><path d="M19 9l3 3-3 3"/><line x1="2" x2="22" y1="12" y2="12"/><line x1="12" x2="12" y1="2" y2="22"/>
          </svg>
          <span>支持画布自由视差拖拽 / 滚轮缩放</span>
        </span>
      </div>
      <div ref="chartEl" class="chart-container"></div>
    </div>

    <div class="insights-row">
      <div class="insight-card stats-card">
        <div class="insight-header">
          <div class="insight-bar"></div>
          <span>描述性静态核验矩阵</span>
        </div>
        <div class="stats-table-wrapper">
          <table class="stats-table" v-if="numericCols.length > 0">
            <thead>
              <tr>
                <th>变量</th>
                <th>样本数</th>
                <th>均值</th>
                <th>中位数</th>
                <th>标准差</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="col in numericCols" :key="col">
                <td class="var-name">{{ col }}</td>
                <td>{{ stats[col]?.n ?? '-' }}</td>
                <td>{{ stats[col]?.mean ?? '-' }}</td>
                <td>{{ stats[col]?.median ?? '-' }}</td>
                <td>{{ stats[col]?.std ?? '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-hint">未检测到数值列</div>
        </div>
      </div>

      <div class="insight-card corr-card">
        <div class="insight-header">
          <div class="insight-bar"></div>
          <span>智能相关性推论</span>
        </div>
        <div v-if="!corrResult" class="empty-hint">请选择两个数值变量以计算相关性</div>
        <template v-else>
          <div class="corr-vars">{{ corrResult.xCol }} ↔ {{ corrResult.yCol }}</div>
          <div class="corr-main">
            <span class="corr-r">r = {{ corrResult.r }}</span>
            <span v-if="corrResult.significant" class="corr-badge">显著相关</span>
          </div>
          <div class="corr-stats">
            <span>n = {{ corrResult.n }}</span>
            <span>t = {{ corrResult.t }}</span>
            <span>p {{ corrResult.p }}</span>
          </div>
          <div class="corr-conclusion">→ {{ corrResult.conclusion }}</div>
        </template>
      </div>
    </div>
  </main>
</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import echarts from '../../utils/echarts.js'

const emit = defineEmits(['back'])

const rawData = ref([])
const columns = ref([])
const numericCols = ref([])
const currentChartType = ref('scatter')
const xCol = ref('')
const yCol = ref('')
const fileName = ref('')
const chartEl = ref(null)
let chartInstance = null

const chartTypes = [
  { key: 'scatter', label: '散点趋势图' },
  { key: 'bar', label: '柱状分布图' },
  { key: 'boxplot', label: '箱线变异图' },
  { key: 'parallel', label: '多维平行坐标' },
]

const chartTitle = computed(() => {
  const titles = {
    scatter: `散点谱系 · ${xCol.value} vs ${yCol.value || '?'}`,
    bar: `柱状分布 · ${xCol.value} / ${yCol.value || '?'}`,
    boxplot: `箱线变异 · ${xCol.value} / ${yCol.value || '?'}`,
    parallel: '平行坐标 · 多变量',
  }
  return titles[currentChartType.value] || ''
})

const stats = computed(() => {
  const result = {}
  numericCols.value.forEach(col => {
    const vals = rawData.value.map(r => Number(r[col])).filter(v => !isNaN(v))
    if (vals.length === 0) return
    const n = vals.length
    const mean = vals.reduce((a, b) => a + b, 0) / n
    const sorted = [...vals].sort((a, b) => a - b)
    const median = sorted[Math.floor(n / 2)]
    const min = sorted[0]
    const max = sorted[n - 1]
    const variance = vals.reduce((s, v) => s + (v - mean) ** 2, 0) / n
    const std = Math.sqrt(variance)
    result[col] = { n, mean: mean.toFixed(2), median: median.toFixed(2), std: std.toFixed(2), min: min.toFixed(2), max: max.toFixed(2) }
  })
  return result
})

const corrResult = computed(() => {
  if (!xCol.value || !yCol.value || !numericCols.value.includes(xCol.value) || !numericCols.value.includes(yCol.value)) return null
  const xVals = rawData.value.map(r => Number(r[xCol.value])).filter(v => !isNaN(v))
  const yVals = rawData.value.map(r => Number(r[yCol.value])).filter(v => !isNaN(v))
  if (xVals.length !== yVals.length || xVals.length <= 2) return null
  const n = xVals.length
  const r = pearsonCorrelation(xVals, yVals)
  const tStat = r * Math.sqrt((n - 2) / (1 - r * r))
  const pVal = tTestPValue(Math.abs(tStat), n - 2)
  const sig = pVal < 0.05
  const absR = Math.abs(r)
  let conclusion = ''
  if (absR >= 0.8) conclusion = '矩阵判定该指数具备极强正相关，可能存在多重共线性风险，建议执行进一步的偏相关消融核验。'
  else if (absR >= 0.6) conclusion = '强相关，具有重要生物学意义，建议结合领域知识进一步验证。'
  else if (absR >= 0.4) conclusion = '中等程度相关，可结合其他变量综合判断。'
  else conclusion = '弱相关或无线性关系，建议尝试非线性模型或增加样本量。'
  return {
    xCol: xCol.value, yCol: yCol.value,
    r: r.toFixed(4), n,
    t: tStat.toFixed(3),
    p: pVal < 0.0001 ? '< 0.0001' : '= ' + pVal.toFixed(4),
    significant: sig, conclusion
  }
})

const sampleData = [
  {品种:'富士',处理:'CK',单果重_g:185,糖度_Brix:13.2,酸度_pH:3.4,VC含量_mg:4.2,产量_kg:22.5},
  {品种:'富士',处理:'A',单果重_g:210,糖度_Brix:15.1,酸度_pH:3.1,VC含量_mg:5.8,产量_kg:25.1},
  {品种:'富士',处理:'B',单果重_g:195,糖度_Brix:14.8,酸度_pH:3.3,VC含量_mg:5.2,产量_kg:24.3},
  {品种:'嘎啦',处理:'CK',单果重_g:155,糖度_Brix:12.8,酸度_pH:3.6,VC含量_mg:3.8,产量_kg:19.2},
  {品种:'嘎啦',处理:'A',单果重_g:172,糖度_Brix:14.0,酸度_pH:3.4,VC含量_mg:4.9,产量_kg:21.8},
  {品种:'嘎啦',处理:'B',单果重_g:168,糖度_Brix:13.9,酸度_pH:3.5,VC含量_mg:4.5,产量_kg:20.9},
  {品种:'金冠',处理:'CK',单果重_g:200,糖度_Brix:14.5,酸度_pH:3.2,VC含量_mg:6.1,产量_kg:27.0},
  {品种:'金冠',处理:'A',单果重_g:225,糖度_Brix:16.3,酸度_pH:2.9,VC含量_mg:7.2,产量_kg:30.2},
  {品种:'金冠',处理:'B',单果重_g:218,糖度_Brix:15.9,酸度_pH:3.0,VC含量_mg:6.8,产量_kg:28.5},
  {品种:'红星',处理:'CK',单果重_g:190,糖度_Brix:13.5,酸度_pH:3.3,VC含量_mg:5.0,产量_kg:23.0},
  {品种:'红星',处理:'A',单果重_g:205,糖度_Brix:14.7,酸度_pH:3.1,VC含量_mg:5.9,产量_kg:24.8},
  {品种:'红星',处理:'B',单果重_g:198,糖度_Brix:14.4,酸度_pH:3.2,VC含量_mg:5.4,产量_kg:24.1}
]

function loadData(dataArray) {
  rawData.value = dataArray
  if (rawData.value.length === 0) return
  columns.value = Object.keys(rawData.value[0])
  numericCols.value = columns.value.filter(col => typeof rawData.value[0][col] === 'number')
  if (numericCols.value.length > 0) {
    xCol.value = numericCols.value[0]
    yCol.value = numericCols.value.length > 1 ? numericCols.value[1] : ''
  }
  nextTick(() => updateAll())
}

function loadSampleData() {
  fileName.value = '园艺实验数据.xlsx'
  loadData(sampleData)
}

function switchChartType(type) {
  currentChartType.value = type
  updateChart()
}

function triggerUpload() {
  document.getElementById('fileInput').click()
}

function onFileChange(e) {
  if (e.target.files[0]) handleFile(e.target.files[0])
}

function onDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) handleFile(file)
}

async function handleFile(file) {
  fileName.value = file.name
  try {
    let data
    if (file.name.endsWith('.csv')) {
      const text = await file.text()
      data = parseCSV(text)
    } else {
      const XLSX = await import('xlsx')
      const buffer = await file.arrayBuffer()
      const wb = XLSX.read(buffer, { type: 'array' })
      const sheet = wb.Sheets[wb.SheetNames[0]]
      data = XLSX.utils.sheet_to_json(sheet)
    }
    if (data.length === 0) throw new Error('文件中无有效数据行')
    loadData(data)
  } catch (err) {
    alert('文件解析失败：' + err.message)
  }
}

function parseCSV(text) {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map(h => h.trim())
  const data = []
  for (let i = 1; i < lines.length; i++) {
    const vals = lines[i].split(',')
    if (vals.length !== headers.length) continue
    const row = {}
    headers.forEach((h, idx) => {
      const v = vals[idx].trim()
      const num = Number(v)
      row[h] = isNaN(num) ? v : num
    })
    data.push(row)
  }
  return data
}

function initChart() {
  if (!chartEl.value) return
  const w = chartEl.value.clientWidth
  const h = chartEl.value.clientHeight
  if (w === 0 || h === 0) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartEl.value)
  renderChart()
}

function getTextColor() {
  return '#556056'
}

function buildTooltip() {
  return {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8ebe8',
    borderWidth: 1,
    textStyle: { color: '#1e2720', fontSize: 11 },
    padding: [8, 12]
  }
}

function getGrid() {
  return { left: 55, right: 25, top: 20, bottom: 45, containLabel: true }
}

function renderChart() {
  if (!chartInstance) return
  const x = xCol.value
  const y = yCol.value
  if (!x) return
  const textColor = getTextColor()
  const dataArr = rawData.value
  const ct = currentChartType.value

  chartInstance.clear()
  const opts = { notMerge: true }

  if (ct === 'scatter') {
    const data = dataArr.map(r => [r[x], r[y] || 0]).filter(d => typeof d[0] === 'number')
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: buildTooltip(),
      grid: getGrid(),
      xAxis: {
        type: 'value', name: x,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } },
        splitLine: { lineStyle: { color: '#f3f6f3', type: 'dashed' } }
      },
      yAxis: {
        type: 'value', name: y || '',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } },
        splitLine: { lineStyle: { color: '#f3f6f3', type: 'dashed' } }
      },
      series: [{
        type: 'scatter', data, symbolSize: 10,
        itemStyle: { color: '#526e5a', opacity: 0.7 },
        emphasis: { itemStyle: { opacity: 1, borderColor: '#526e5a', borderWidth: 2 } }
      }]
    }, opts)
  } else if (ct === 'bar') {
    const groups = [...new Set(dataArr.map(r => r[x]))]
    const values = groups.map(g => {
      const vals = dataArr.filter(r => r[x] === g).map(r => Number(r[y])).filter(v => !isNaN(v))
      return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2) : 0
    })
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: buildTooltip(),
      grid: getGrid(),
      xAxis: {
        type: 'category', data: groups, name: x,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } }
      },
      yAxis: {
        type: 'value', name: y || '',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } },
        splitLine: { lineStyle: { color: '#f3f6f3', type: 'dashed' } }
      },
      series: [{
        type: 'bar', data: values, barMaxWidth: 48,
        itemStyle: { color: '#526e5a', borderRadius: [4, 4, 0, 0] }
      }]
    }, opts)
  } else if (ct === 'boxplot') {
    const groups = [...new Set(dataArr.map(r => r[x]))]
    const rawBoxData = groups.map(g => {
      const vals = dataArr.filter(r => r[x] === g).map(r => Number(r[y])).filter(v => !isNaN(v)).sort((a, b) => a - b)
      if (vals.length < 1) return null
      const n = vals.length
      const median = n % 2 === 0 ? (vals[n / 2 - 1] + vals[n / 2]) / 2 : vals[Math.floor(n / 2)]
      const lowerHalf = vals.slice(0, Math.floor(n / 2))
      const upperHalf = n % 2 === 0 ? vals.slice(n / 2) : vals.slice(Math.floor(n / 2) + 1)
      const q1 = lowerHalf.length > 0 ? (lowerHalf.length % 2 === 0 ? (lowerHalf[lowerHalf.length / 2 - 1] + lowerHalf[lowerHalf.length / 2]) / 2 : lowerHalf[Math.floor(lowerHalf.length / 2)]) : vals[0]
      const q3 = upperHalf.length > 0 ? (upperHalf.length % 2 === 0 ? (upperHalf[upperHalf.length / 2 - 1] + upperHalf[upperHalf.length / 2]) / 2 : upperHalf[Math.floor(upperHalf.length / 2)]) : vals[vals.length - 1]
      return { group: g, data: [vals[0], q1, median, q3, vals[vals.length - 1]] }
    }).filter(d => d !== null)
    const boxData = rawBoxData.map(d => d.data)
    const usedGroups = rawBoxData.map(d => d.group)
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: function(p) {
          const d = p.data
          return p.name + '<br/>' +
            '上限: ' + (typeof d[4] === 'number' ? d[4].toFixed(2) : d[4]) + '<br/>' +
            'Q3: ' + (typeof d[3] === 'number' ? d[3].toFixed(2) : d[3]) + '<br/>' +
            '中位数: ' + (typeof d[2] === 'number' ? d[2].toFixed(2) : d[2]) + '<br/>' +
            'Q1: ' + (typeof d[1] === 'number' ? d[1].toFixed(2) : d[1]) + '<br/>' +
            '下限: ' + (typeof d[0] === 'number' ? d[0].toFixed(2) : d[0])
        }
      },
      grid: getGrid(),
      xAxis: {
        type: 'category', data: usedGroups, name: x,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } }
      },
      yAxis: {
        type: 'value', name: y || '',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: '#dee3de' } },
        splitLine: { lineStyle: { color: '#f3f6f3', type: 'dashed' } }
      },
      series: [{
        type: 'boxplot', data: boxData,
        itemStyle: { color: '#526e5a', borderColor: '#415848', borderWidth: 2 }
      }]
    }, opts)
  } else if (ct === 'parallel') {
    const dims = numericCols.value.slice(0, 5)
    const data = dataArr.map(r => dims.map(d => Number(r[d])).filter(v => !isNaN(v))).filter(arr => arr.length === dims.length)
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: buildTooltip(),
      parallel: { left: 60, right: 50, top: 30, bottom: 30 },
      parallelAxis: dims.map(d => ({
        dim: dims.indexOf(d), name: d,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 9 }
      })),
      series: [{
        type: 'parallel', data,
        lineStyle: { color: '#526e5a', opacity: 0.5, width: 1.5 },
        emphasis: { lineStyle: { color: '#415848', width: 2.5 } }
      }]
    }, opts)
  }
}

function updateChart() {
  if (!chartInstance) { initChart(); return }
  renderChart()
}

function updateAll() {
  nextTick(() => updateChart())
}

function onResize() {
  if (chartInstance) chartInstance.resize()
}

// Pearson correlation
function pearsonCorrelation(x, y) {
  const n = x.length
  const mx = x.reduce((a, b) => a + b, 0) / n
  const my = y.reduce((a, b) => a + b, 0) / n
  let num = 0, dx2 = 0, dy2 = 0
  for (let i = 0; i < n; i++) {
    const dx = x[i] - mx, dy = y[i] - my
    num += dx * dy; dx2 += dx * dx; dy2 += dy * dy
  }
  const den = Math.sqrt(dx2 * dy2)
  return den === 0 ? 0 : num / den
}

function tTestPValue(t, df) {
  const x = df / (df + t * t)
  return incompleteBeta(x, df / 2, 0.5)
}

function incompleteBeta(x, a, b) {
  if (x <= 0) return 0
  if (x >= 1) return 1
  const logBeta = lnBeta(a, b)
  const front = Math.exp(Math.log(x) * a + Math.log(1 - x) * b - logBeta) / a
  let f = 1, c = 1, d = 1 - (a + b) * x / (a + 1)
  if (Math.abs(d) < 1e-30) d = 1e-30
  d = 1 / d; let h = d
  for (let m = 1; m <= 200; m++) {
    const m2 = 2 * m
    let aa = m * (b - m) * x / ((a + m2 - 1) * (a + m2))
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30
    c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30
    d = 1 / d; h *= d * c
    aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30
    c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30
    d = 1 / d; const del = d * c; h *= del
    if (Math.abs(del - 1) < 3e-7) break
  }
  return front * (h - 1)
}

function lnBeta(a, b) { return lnGamma(a) + lnGamma(b) - lnGamma(a + b) }

function lnGamma(z) {
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - lnGamma(1 - z)
  z -= 1
  const g = 7
  const c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
  let x = c[0]
  for (let i = 1; i < g + 2; i++) x += c[i] / (z + i)
  const t = z + g + 0.5
  return Math.log(Math.sqrt(2 * Math.PI)) + (z + 0.5) * Math.log(t) - t + Math.log(x)
}

onMounted(() => {
  loadSampleData()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.data-lab {
  display: flex;
  height: 100%;
  background: #f8f8f8;
  overflow: hidden;
}

/* Controls Panel */
.controls-panel {
  width: 272px;
  background: white;
  border-right: 1px solid #edf0ed;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
  overflow-y: auto;
}

.controls-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #121212;
}

.control-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #121212;
  letter-spacing: 0.5px;
}

.control-label svg {
  color: #121212;
}

.upload-area {
  border: 2px dashed #bad2be;
  background: #fcfcfc;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  background: #f5f7f5;
  border-color: #121212;
}

.upload-area svg {
  color: #666666;
  margin: 0 auto 4px;
  opacity: 0.7;
}

.upload-area:hover svg {
  opacity: 1;
}

.upload-text {
  font-size: 11px;
  color: #666666;
}

.upload-hint {
  font-size: 9px;
  color: #999999;
  margin-top: 4px;
  background: #f4f4f4;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.btn-sample {
  width: 100%;
  padding: 8px;
  background: #f8f8f8;
  border: 1px solid #dee3de;
  border-radius: 8px;
  font-size: 11px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-sample:hover {
  background: #f0f0f0;
  border-color: #121212;
  color: #121212;
}

.select-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.select-label {
  font-size: 10px;
  color: #9ca3af;
}

.select-wrapper {
  position: relative;
}

.select-wrapper select {
  width: 100%;
  background: #f8f8f8;
  border: 1px solid #dee3de;
  border-radius: 8px;
  padding: 6px 28px 6px 8px;
  font-size: 12px;
  color: #121212;
  appearance: none;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.select-wrapper select:focus {
  border-color: #121212;
}

.select-icon {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.5;
  pointer-events: none;
}

.chart-type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.chart-type-btn {
  padding: 6px 8px;
  border: 1px solid #dee3de;
  background: white;
  border-radius: 8px;
  font-size: 10px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.chart-type-btn:hover {
  background: #f8f8f8;
  border-color: #121212;
}

.chart-type-btn.active {
  border: 2px solid #526e5a;
  background: #f2f6f3;
  color: #121212;
  font-weight: 500;
}

.btn-render {
  width: 100%;
  padding: 10px;
  background: #121212;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
  margin-top: 16px;
}

.btn-render:hover {
  background: #333333;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fafafa;
}

.chart-area {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-bottom: 1px solid #edf0ed;
  background: white;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 8px;
}

.chart-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-weight: 500;
  color: #121212;
}

.chart-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #9ca3af;
}

.chart-container {
  flex: 1;
  min-height: 0;
}

/* Insights Row */
.insights-row {
  height: 224px;
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 20px;
  padding: 20px;
  flex-shrink: 0;
}

.insight-card {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0,0,0,0.005);
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #121212;
  margin-bottom: 12px;
}

.insight-bar {
  width: 4px;
  height: 14px;
  background: #121212;
  border-radius: 2px;
}

.stats-table-wrapper {
  flex: 1;
  overflow-x: auto;
}

.stats-table {
  width: 100%;
  font-size: 10px;
  text-align: left;
  color: #666666;
}

.stats-table th {
  padding-bottom: 6px;
  font-weight: 500;
  color: #9ca3af;
  border-bottom: 1px solid #edf0ed;
}

.stats-table td {
  padding: 6px 0;
  font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
  border-bottom: 1px solid #f5f7f5;
}

.stats-table .var-name {
  font-family: inherit;
  color: #121212;
  font-weight: 500;
}

.empty-hint {
  color: #9ca3af;
  font-size: 10px;
}

/* Correlation Card */
.corr-vars {
  font-size: 10px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.corr-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.corr-r {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
  color: #121212;
}

.corr-badge {
  font-size: 9px;
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.corr-stats {
  font-size: 10px;
  color: #9ca3af;
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.corr-conclusion {
  background: #f8f8f8;
  border: 1px solid #edf1ed;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 10px;
  color: #666666;
  font-family: 'Noto Serif SC', 'SimSun', serif;
  line-height: 1.5;
}

/* ===== Dark Theme ===== */
body.dark .data-lab {
  background: #121212;
}

body.dark .controls-panel {
  background: #1a1a1a;
  border-right-color: #2d2d2d;
}

body.dark .back-btn {
  color: #666666;
}

body.dark .back-btn:hover {
  color: #ffffff;
}

body.dark .control-label {
  color: #ffffff;
}

body.dark .control-label svg {
  color: #ffffff;
}

body.dark .upload-area {
  background: #242424;
  border-color: #333333;
}

body.dark .upload-area:hover {
  background: #2d2d2d;
  border-color: #ffffff;
}

body.dark .upload-area svg {
  color: #b3b3b3;
}

body.dark .upload-text {
  color: #b3b3b3;
}

body.dark .upload-hint {
  background: #1a1a1a;
  color: #666666;
}

body.dark .btn-sample {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .btn-sample:hover {
  background: #2d2d2d;
  border-color: #ffffff;
  color: #ffffff;
}

body.dark .select-label {
  color: #666666;
}

body.dark .select-wrapper select {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .select-wrapper select:focus {
  border-color: #ffffff;
}

body.dark .chart-type-btn {
  background: #242424;
  border-color: #2d2d2d;
  color: #b3b3b3;
}

body.dark .chart-type-btn:hover {
  background: #2d2d2d;
  border-color: #ffffff;
}

body.dark .chart-type-btn.active {
  border-color: #ffffff;
  background: #1a1a1a;
  color: #ffffff;
}

body.dark .btn-render {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-render:hover {
  background: #e5e5e5;
}

body.dark .main-content {
  background: #141414;
}

body.dark .chart-area {
  background: #1a1a1a;
  border-bottom-color: #2d2d2d;
}

body.dark .chart-title {
  color: #ffffff;
}

body.dark .chart-hint {
  color: #666666;
}

body.dark .insight-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

body.dark .insight-header {
  color: #ffffff;
}

body.dark .insight-bar {
  background: #ffffff;
}

body.dark .stats-table {
  color: #b3b3b3;
}

body.dark .stats-table th {
  color: #666666;
  border-bottom-color: #2d2d2d;
}

body.dark .stats-table td {
  border-bottom-color: #1a1a1a;
}

body.dark .stats-table .var-name {
  color: #ffffff;
}

body.dark .empty-hint {
  color: #666666;
}

body.dark .corr-vars {
  color: #666666;
}

body.dark .corr-r {
  color: #ffffff;
}

body.dark .corr-badge {
  background: #0a2520;
  color: #10b981;
  border-color: #0d3b2e;
}

body.dark .corr-stats {
  color: #666666;
}

body.dark .corr-conclusion {
  background: #1a1a1a;
  border-color: #2d2d2d;
  color: #b3b3b3;
}
</style>
