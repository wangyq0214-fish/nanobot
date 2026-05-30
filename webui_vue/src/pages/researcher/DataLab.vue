<template>
<div class="app">
  <ResearcherNav active-tab="datalab" />

  <div class="main-layout">
    <div class="panel-left thin-scrollbar">
      <div class="section-title">数据源</div>
      <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
        <div class="upload-label">点击上传或拖拽文件</div>
        <div class="upload-hint">支持 CSV / Excel (.xlsx .xls)</div>
        <input type="file" id="fileInput" accept=".csv,.xlsx,.xls" @change="onFileChange" style="display:none">
        <div class="file-name" v-if="fileName">{{ fileName }}</div>
      </div>
      <button class="btn" @click="loadSampleData">加载园艺实验数据</button>

      <div class="section-title">变量选择</div>
      <div class="select-group">
        <label>X 轴变量</label>
        <select v-model="xCol" @change="updateAll">
          <option v-for="c in columns" :key="c" :value="c">{{ c }}</option>
          <option v-if="columns.length === 0">请先上传数据</option>
        </select>
      </div>
      <div class="select-group">
        <label>Y 轴变量（可选）</label>
        <select v-model="yCol" @change="updateAll">
          <option value="">— 不选择 —</option>
          <option v-for="c in numericCols" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div class="section-title">图表类型</div>
      <div class="chart-type-grid">
        <button
          v-for="ct in chartTypes"
          :key="ct.key"
          class="chart-type-btn"
          :class="{ active: currentChartType === ct.key }"
          @click="switchChartType(ct.key)"
        >{{ ct.label }}</button>
      </div>
      <button class="btn" @click="updateAll">刷新图表</button>

      <div class="data-preview">
        <div class="section-title">数据预览</div>
        <div v-if="rawData.length === 0" style="font-size:0.5rem;color:var(--text3);">暂无数据</div>
        <template v-else>
          <table class="preview-table">
            <thead><tr><th v-for="c in previewCols" :key="c">{{ c }}</th></tr></thead>
            <tbody>
              <tr v-for="(row, i) in previewRows" :key="i">
                <td v-for="c in previewCols" :key="c">{{ row[c] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="rawData.length > 8" style="font-size:0.45rem;color:var(--text3);margin-top:4px;">显示前8行，共 {{ rawData.length }} 条记录</div>
        </template>
      </div>
    </div>

    <div class="panel-right">
      <div class="chart-card">
        <div class="chart-header">
          <span>{{ chartTitle }}</span>
          <span style="font-size:0.5rem;color:var(--text3);">滚轮缩放 · 拖拽平移</span>
        </div>
        <div ref="chartEl" id="mainChart"></div>
      </div>
      <div class="insight-row">
        <div class="insight-card hide-scrollbar">
          <div class="insight-card-title">描述性统计</div>
          <div v-if="numericCols.length === 0" style="color:var(--text3);">未检测到数值列</div>
          <table v-else class="stat-table">
            <thead><tr><th>变量</th><th>样本数</th><th>均值</th><th>中位数</th><th>标准差</th><th>范围</th></tr></thead>
            <tbody>
              <tr v-for="col in numericCols" :key="col">
                <td class="var-name">{{ col }}</td>
                <td>{{ stats[col]?.n ?? '-' }}</td>
                <td>{{ stats[col]?.mean ?? '-' }}</td>
                <td>{{ stats[col]?.median ?? '-' }}</td>
                <td>{{ stats[col]?.std ?? '-' }}</td>
                <td>{{ stats[col]?.min ?? '-' }} — {{ stats[col]?.max ?? '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="insight-card hide-scrollbar">
          <div class="insight-card-title">相关性分析</div>
          <div v-if="!corrResult" style="color:var(--text3);">请选择两个数值变量以计算相关性</div>
          <template v-else>
            <div class="corr-vars">{{ corrResult.xCol }} <span class="corr-arrow">↔</span> {{ corrResult.yCol }}</div>
            <div class="corr-main">
              <span class="corr-r">r = {{ corrResult.r }}</span>
              <span v-if="corrResult.significant" class="corr-sig">显著</span>
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
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useAuth } from '../../composables/useAuth.js'
import ResearcherNav from '../../components/ResearcherNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}
const isDark = ref(false)

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
  { key: 'scatter', label: '散点图' },
  { key: 'bar', label: '柱状图' },
  { key: 'boxplot', label: '箱线图' },
  { key: 'heatmap', label: '热力图' },
  { key: 'radar', label: '雷达图' },
  { key: 'parallel', label: '平行坐标' },
]

const chartTitle = computed(() => {
  const titles = {
    scatter: `散点图 · ${xCol.value} vs ${yCol.value || '?'}`,
    bar: `柱状图 · ${xCol.value} / ${yCol.value || '?'}`,
    boxplot: `箱线图 · ${xCol.value} / ${yCol.value || '?'}`,
    heatmap: `热力图 · ${xCol.value} / ${yCol.value || '?'}`,
    radar: '雷达图 · 多变量',
    parallel: '平行坐标 · 多变量',
  }
  return titles[currentChartType.value] || ''
})

const previewCols = computed(() => columns.value.slice(0, 5))
const previewRows = computed(() => rawData.value.slice(0, 8))

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
  if (absR >= 0.8) conclusion = '极强相关，可能存在共线性，建议进一步检验'
  else if (absR >= 0.6) conclusion = '强相关，具有重要生物学意义'
  else if (absR >= 0.4) conclusion = '中等程度相关，可结合其他变量综合判断'
  else conclusion = '弱相关或无线性关系，建议尝试非线性模型'
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
  return getComputedStyle(document.body).getPropertyValue('--text2').trim() || '#4a4658'
}

function buildTooltip() {
  return {
    trigger: 'item',
    backgroundColor: 'rgba(30, 10, 60, 0.92)',
    borderColor: '#8B70FF',
    borderWidth: 1,
    textStyle: { color: '#f2eaff', fontSize: 11 }
  }
}

function getGrid() {
  return { left: 55, right: 25, top: 20, bottom: 35, containLabel: true }
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
      xAxis: { type: 'value', name: x, nameTextStyle: { color: textColor, fontSize: 10 } },
      yAxis: { type: 'value', name: y || '', nameTextStyle: { color: textColor, fontSize: 10 } },
      series: [{ type: 'scatter', data, symbolSize: 8, itemStyle: { color: '#8B70FF', opacity: 0.8 } }]
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
      xAxis: { type: 'category', data: groups, name: x, nameTextStyle: { color: textColor, fontSize: 10 } },
      yAxis: { type: 'value', name: y || '', nameTextStyle: { color: textColor, fontSize: 10 } },
      series: [{
        type: 'bar', data: values, barMaxWidth: 48,
        itemStyle: { color: '#5a4cd8', borderRadius: [6, 6, 0, 0] }
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
      xAxis: { type: 'category', data: usedGroups, name: x, nameTextStyle: { color: textColor, fontSize: 10 } },
      yAxis: { type: 'value', name: y || '', nameTextStyle: { color: textColor, fontSize: 10 } },
      series: [{
        type: 'boxplot', data: boxData,
        itemStyle: { color: '#8B70FF', borderColor: '#5a4cd8', borderWidth: 2 }
      }]
    }, opts)
  } else if (ct === 'heatmap') {
    const xVals = [...new Set(dataArr.map(r => r[x]))]
    const yVals = [...new Set(dataArr.map(r => r[y]))]
    const data = []
    let maxVal = 0
    xVals.forEach((xv, i) => yVals.forEach((yv, j) => {
      const cnt = dataArr.filter(r => r[x] === xv && r[y] === yv).length
      data.push([i, j, cnt])
      if (cnt > maxVal) maxVal = cnt
    }))
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: function(p) {
          return xVals[p.data[0]] + ' × ' + yVals[p.data[1]] + '<br/>计数: ' + p.data[2]
        }
      },
      grid: { left: 80, right: 30, top: 20, bottom: 55 },
      xAxis: { type: 'category', data: xVals, axisLabel: { rotate: 30, fontSize: 10, color: textColor } },
      yAxis: { type: 'category', data: yVals, axisLabel: { fontSize: 10, color: textColor } },
      visualMap: {
        min: 0, max: Math.max(maxVal, 1),
        orient: 'horizontal', bottom: 4, left: 'center',
        calculable: true,
        inRange: { color: ['#f2f0fa', '#b8acf0', '#8B70FF', '#5a4cd8', '#3a28b0'] },
        textStyle: { color: textColor, fontSize: 10 }
      },
      series: [{
        type: 'heatmap', data,
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(90, 76, 216, 0.5)' }
        },
        itemStyle: { borderColor: 'rgba(255,255,255,0.3)', borderWidth: 1 }
      }]
    }, opts)
  } else if (ct === 'radar') {
    const inds = numericCols.value.slice(0, 6)
    const indicator = inds.map(c => ({ name: c, max: Math.max(...dataArr.map(r => Number(r[c])).filter(v => !isNaN(v))) * 1.2 }))
    const values = indicator.map(ind => {
      const vals = dataArr.map(r => Number(r[ind.name])).filter(v => !isNaN(v))
      return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2) : 0
    })
    chartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: buildTooltip(),
      radar: {
        indicator,
        center: ['50%', '55%'], radius: '65%',
        axisName: { color: textColor, fontSize: 9 },
        splitArea: { areaStyle: { color: ['rgba(139,112,255,0.04)', 'rgba(139,112,255,0.02)'] } }
      },
      series: [{
        type: 'radar',
        data: [{ value: values, name: '均值', areaStyle: { color: 'rgba(139,112,255,0.15)' } }],
        itemStyle: { color: '#8B70FF' },
        lineStyle: { color: '#8B70FF', width: 2 }
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
        lineStyle: { color: '#8B70FF', opacity: 0.5, width: 1.5 },
        emphasis: { lineStyle: { color: '#c4b5fd', width: 2.5 } }
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

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
  nextTick(() => {
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
      initChart()
    }
  })
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

<style>
:root {
  --bg: #f2f0fa;
  --card: rgba(255,255,255,0.85);
  --card-solid: rgba(255,255,255,0.85);
  --accent: #5a4cd8;
  --accent-deep: #4638b8;
  --accent-light: rgba(90,76,216,0.08);
  --accent-glow: rgba(90,76,216,0.15);
  --border: rgba(0,0,0,0.06);
  --text: #18161f;
  --text2: #4a4658;
  --text3: #7a7688;
  --radius: 18px;
  --divider: rgba(0,0,0,0.05);
}
body.dark {
  --bg: #0c0a1a;
  --card: rgba(18,15,36,0.82);
  --card-solid: rgba(18,15,36,0.82);
  --accent: #8B70FF;
  --accent-deep: #6d5adf;
  --accent-light: rgba(139,112,255,0.10);
  --accent-glow: rgba(139,112,255,0.22);
  --border: rgba(255,255,255,0.07);
  --text: #e4e1f6;
  --text2: #b0acd0;
  --text3: #7e7a98;
  --divider: rgba(255,255,255,0.05);
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Inter','PingFang SC','Microsoft YaHei',sans-serif;
  background:var(--bg); color:var(--text); height:100vh; overflow:hidden; transition:0.3s;
}
.hide-scrollbar { scrollbar-width:none; -ms-overflow-style:none; }
.hide-scrollbar::-webkit-scrollbar { width:0; height:0; display:none; }
.thin-scrollbar { scrollbar-width:thin; scrollbar-color:transparent transparent; }
.thin-scrollbar::-webkit-scrollbar { width:3px; }
.thin-scrollbar::-webkit-scrollbar-track { background:transparent; }
.thin-scrollbar::-webkit-scrollbar-thumb { background:transparent; border-radius:3px; }
.thin-scrollbar:hover::-webkit-scrollbar-thumb { background:rgba(128,128,128,0.25); }
.app { display:flex; flex-direction:column; height:100vh; padding:12px 16px; gap:10px; max-width:1920px; margin:0 auto; }

.top-nav {
  display:flex; align-items:center; justify-content:space-between;
  background:var(--card); backdrop-filter:blur(12px);
  border:2px solid var(--accent); border-radius:var(--radius);
  padding:0 24px; height:52px; flex-shrink:0;
  box-shadow:0 0 0 1px var(--accent-light),0 0 24px var(--accent-glow);
}
.nav-left { display:flex; align-items:center; gap:16px; }
.nav-logo {
  font-family:'Playfair Display',serif; font-weight:700; font-size:1.1rem; color:var(--accent);
  display:flex; align-items:center; gap:8px;
}
.nav-logo .dot { width:7px; height:7px; background:var(--accent); border-radius:50%; box-shadow:0 0 14px var(--accent-glow); animation:dotPulse 2.4s infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:0.5} }
.nav-center { display:flex; align-items:center; gap:4px; }
.nav-tab {
  padding:6px 14px; border-radius:14px; font-size:0.64rem; font-weight:500;
  color:var(--text2); cursor:pointer; transition:all 0.2s; border:1.5px solid transparent;
}
.nav-tab:hover { color:var(--text); background:var(--accent-light); }
.nav-tab.active {
  color:var(--accent); background:var(--accent-light); border-color:var(--accent);
  box-shadow:0 0 12px var(--accent-glow);
}
.nav-right { display:flex; gap:8px; align-items:center; }
.icon-btn {
  width:34px; height:34px; border:1.5px solid var(--border); background:transparent;
  cursor:pointer; color:var(--text2); border-radius:50%; display:flex;
  align-items:center; justify-content:center; transition:0.2s;
}
.icon-btn svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; }
.icon-btn:hover { color:var(--accent); border-color:var(--accent); background:var(--accent-light); }

.main-layout { flex:1; display:flex; gap:10px; min-height:0; }
.panel-left {
  width:290px; background:var(--card); backdrop-filter:blur(12px);
  border:2px solid var(--accent); border-radius:var(--radius);
  padding:18px 16px; display:flex; flex-direction:column; gap:14px; overflow-y:auto;
  box-shadow:0 0 0 1px var(--accent-light);
}
.section-title {
  font-weight:700; font-size:0.65rem; color:var(--accent); text-transform:uppercase;
  letter-spacing:0.06em; display:flex; align-items:center; gap:7px;
}
.section-title::before { content:''; width:3px; height:14px; background:var(--accent); border-radius:2px; }
.upload-area {
  border:2px dashed var(--accent); border-radius:14px; padding:20px 12px;
  text-align:center; cursor:pointer; transition:0.25s; background:var(--accent-light); position:relative;
}
.upload-area:hover { background:rgba(90,76,216,0.14); border-style:solid; }
.upload-label { font-size:0.68rem; font-weight:600; color:var(--accent); }
.upload-hint { font-size:0.5rem; color:var(--text3); margin-top:3px; }
.file-name { font-size:0.52rem; color:var(--accent); margin-top:6px; font-weight:500; background:rgba(90,76,216,0.06); display:inline-block; padding:2px 10px; border-radius:10px; }
.select-group { display:flex; flex-direction:column; gap:4px; }
.select-group label { font-size:0.54rem; color:var(--text3); font-weight:500; letter-spacing:0.02em; }
select {
  padding:8px 10px; border:1.5px solid var(--border); border-radius:8px;
  background:var(--card); color:var(--text); font-size:0.6rem; width:100%; font-family:inherit;
}
select:focus { outline:none; border-color:var(--accent); }
.btn {
  padding:9px 16px; background:var(--accent-deep); color:#fff; border:none;
  border-radius:9px; font-weight:600; font-size:0.6rem; cursor:pointer;
  transition:0.2s; width:100%; text-transform:uppercase; letter-spacing:0.04em;
  box-shadow:0 2px 8px rgba(90,76,216,0.25);
}
.btn:hover { opacity:0.9; box-shadow:0 4px 16px var(--accent-glow); }
.chart-type-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:5px; }
.chart-type-btn {
  padding:8px 4px; border:1.5px solid var(--border); border-radius:8px;
  background:transparent; color:var(--text2); font-size:0.54rem; cursor:pointer;
  transition:0.2s; text-align:center; font-weight:500;
}
.chart-type-btn.active { border-color:var(--accent); color:var(--accent); background:var(--accent-light); font-weight:600; }
.chart-type-btn:hover { border-color:var(--accent); }
.data-preview { border-top:1px solid var(--divider); padding-top:10px; margin-top:2px; }
.preview-table {
  width:100%; font-size:0.5rem; border-collapse:collapse; margin-top:6px;
}
.preview-table th { background:var(--accent-light); color:var(--accent); padding:5px 7px; text-align:left; font-weight:600; border-radius:4px; }
.preview-table td { padding:4px 7px; border-bottom:1px solid var(--divider); color:var(--text2); }
.preview-table tr:hover td { background:rgba(90,76,216,0.03); }
.panel-right { flex:1; display:flex; flex-direction:column; gap:10px; min-width:0; }
.chart-card {
  flex:1; background:var(--card); backdrop-filter:blur(12px);
  border:2px solid var(--accent); border-radius:var(--radius);
  padding:16px 18px; display:flex; flex-direction:column;
  box-shadow:0 0 0 1px var(--accent-light);
}
.chart-header {
  display:flex; justify-content:space-between; font-weight:700;
  font-size:0.68rem; color:var(--text2); margin-bottom:6px; flex-shrink:0;
}
#mainChart { flex:1; min-height:0; }
.insight-row { display:flex; gap:10px; height:195px; flex-shrink:0; }
.insight-card {
  flex:1; background:var(--card); backdrop-filter:blur(12px);
  border:2px solid var(--accent); border-radius:var(--radius);
  padding:16px 18px; overflow-y:auto; font-size:0.56rem; color:var(--text2);
  line-height:1.65; box-shadow:0 0 0 1px var(--accent-light);
}
.insight-card-title {
  font-weight:700; font-size:0.64rem; color:var(--accent); margin-bottom:10px;
  letter-spacing:0.03em; display:flex; align-items:center; gap:6px;
}
.insight-card-title::before { content:''; width:3px; height:14px; background:var(--accent); border-radius:2px; }
.stat-table {
  width:100%; border-collapse:collapse; font-size:0.62rem;
}
.stat-table th {
  text-align:left; color:var(--text3); font-weight:500; padding:6px 4px 4px 0;
  border-bottom:1px solid var(--divider); font-size:0.56rem; text-transform:uppercase;
}
.stat-table td {
  padding:5px 4px; border-bottom:1px solid var(--divider); color:var(--text2);
  font-family:'JetBrains Mono','SF Mono','Consolas',monospace; font-size:0.6rem;
}
.stat-table tr:last-child td { border-bottom:none; }
.stat-table .var-name { color:var(--accent); font-weight:600; font-family:inherit; }
.corr-vars {
  font-size:0.62rem; font-weight:600; color:var(--text); margin-bottom:12px;
  display:flex; align-items:center; gap:8px;
}
.corr-arrow { color:var(--accent); font-size:1rem; }
.corr-main {
  display:flex; align-items:baseline; gap:12px; margin-bottom:8px;
}
.corr-r {
  font-size:1.5rem; font-weight:800; color:var(--accent); line-height:1;
}
.corr-sig {
  background:var(--accent); color:#fff; padding:2px 10px; border-radius:6px;
  font-size:0.55rem; font-weight:700; letter-spacing:0.03em;
}
.corr-stats {
  font-size:0.52rem; color:var(--text3); margin-bottom:10px;
  display:flex; gap:12px; flex-wrap:wrap;
}
.corr-stats span { white-space:nowrap; }
.corr-conclusion {
  padding:8px 12px; background:var(--accent-light); border-radius:8px;
  font-weight:500; color:var(--accent); font-size:0.55rem; line-height:1.4;
}
@media(max-width:900px) {
  .main-layout { flex-direction:column; }
  .panel-left { width:100%; flex-direction:row; flex-wrap:wrap; max-height:200px; }
  .insight-row { flex-direction:column; height:auto; }
}
</style>
