<template>
  <div class="research-chart">
    <div ref="chartEl" class="chart-canvas"></div>
    <div class="chart-actions">
      <button type="button" title="下载图表图片" @click="downloadImage">下载图片</button>
      <button type="button" title="下载图表数据" @click="downloadData">下载数据</button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import echarts from '../utils/echarts.js'
import { downloadText } from '../composables/useResearchResources.js'

const props = defineProps({ resource: { type: Object, required: true } })
const chartEl = ref(null)
let instance = null
let resizeObserver = null

function render() {
  if (!chartEl.value) return
  if (!instance) instance = echarts.init(chartEl.value)
  const chart = props.resource.chart || {}
  const rows = chart.rows || []
  const series = chart.series || []
  const xData = rows.map(row => row?.[chart.xKey])
  const common = {
    animation: false,
    tooltip: { trigger: chart.kind === 'pie' ? 'item' : 'axis' },
    legend: series.length > 1 ? { bottom: 0 } : undefined,
    grid: { left: 44, right: 20, top: 18, bottom: series.length > 1 ? 44 : 30, containLabel: true },
  }
  if (chart.kind === 'pie') {
    const valueKey = series[0]?.key || 'value'
    common.series = [{
      type: 'pie',
      radius: ['35%', '68%'],
      data: rows.map(row => ({ name: row?.[chart.xKey], value: Number(row?.[valueKey]) || 0 })),
    }]
  } else {
    common.xAxis = { type: chart.kind === 'scatter' ? 'value' : 'category', data: chart.kind === 'scatter' ? undefined : xData }
    common.yAxis = { type: 'value' }
    common.series = series.map(item => ({
      name: item.label,
      type: chart.kind === 'scatter' ? 'scatter' : chart.kind,
      data: chart.kind === 'scatter'
        ? rows.map(row => [Number(row?.[chart.xKey]), Number(row?.[item.key])]).filter(pair => pair.every(Number.isFinite))
        : rows.map(row => row?.[item.key]),
      smooth: chart.kind === 'line',
      barMaxWidth: 42,
    }))
  }
  instance.setOption(common, true)
}

function downloadImage() {
  if (!instance) return
  const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${safeName(props.resource.title)}.png`
  anchor.click()
}

function downloadData() {
  downloadText(`${safeName(props.resource.title)}.json`, JSON.stringify(props.resource.chart || {}, null, 2), 'application/json;charset=utf-8')
}

function safeName(value) {
  return String(value || 'chart').replace(/[\\/:*?"<>|]/g, '_')
}

onMounted(async () => {
  await nextTick()
  render()
  if (typeof ResizeObserver !== 'undefined' && chartEl.value) {
    resizeObserver = new ResizeObserver(() => instance?.resize())
    resizeObserver.observe(chartEl.value)
  }
})
watch(() => props.resource, render, { deep: true })
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  instance?.dispose()
  instance = null
})
</script>

<style scoped>
.research-chart { position: relative; min-width: 0; }
.chart-canvas { width: 100%; height: 280px; min-height: 220px; }
.chart-actions { display: flex; justify-content: flex-end; gap: 8px; }
.chart-actions button { border: 1px solid #dfe5df; background: #fff; color: #536057; padding: 5px 8px; font-size: 11px; cursor: pointer; }
.chart-actions button:hover { border-color: #526e5a; color: #263d2e; }
</style>
