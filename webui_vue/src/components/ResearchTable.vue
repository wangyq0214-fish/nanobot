<template>
  <div class="research-table-tool">
    <div class="table-toolbar">
      <input v-model="query" type="search" placeholder="Filter rows" aria-label="Filter table rows" />
      <span class="table-count">{{ visibleRows.length }}/{{ rows.length }}</span>
      <button type="button" title="Copy visible rows" @click="copyRows">{{ copied ? 'Copied' : 'Copy' }}</button>
      <button type="button" title="Download CSV" @click="downloadCsv">CSV</button>
    </div>
    <div class="resource-table-wrap">
      <table class="resource-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">
              <button type="button" class="sort-button" @click="sortBy(column.key)">
                {{ column.label }}
                <span v-if="sortKey === column.key">{{ sortDirection === 'asc' ? '^' : 'v' }}</span>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in visibleRows" :key="rowIndex">
            <td v-for="column in columns" :key="column.key">{{ row?.[column.key] ?? '' }}</td>
          </tr>
          <tr v-if="!visibleRows.length">
            <td :colspan="Math.max(columns.length, 1)" class="table-empty">No matching rows</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { downloadText } from '../composables/useResearchResources.js'

const props = defineProps({ resource: { type: Object, required: true } })
const query = ref('')
const sortKey = ref('')
const sortDirection = ref('asc')
const copied = ref(false)

const columns = computed(() => props.resource.table?.columns || [])
const rows = computed(() => props.resource.table?.rows || [])
const visibleRows = computed(() => {
  const needle = query.value.trim().toLowerCase()
  const filtered = needle
    ? rows.value.filter(row => columns.value.some(column => String(row?.[column.key] ?? '').toLowerCase().includes(needle)))
    : [...rows.value]
  if (!sortKey.value) return filtered
  return filtered.sort((left, right) => {
    const a = left?.[sortKey.value]
    const b = right?.[sortKey.value]
    const aNumber = Number(a)
    const bNumber = Number(b)
    const comparison = Number.isFinite(aNumber) && Number.isFinite(bNumber)
      ? aNumber - bNumber
      : String(a ?? '').localeCompare(String(b ?? ''), undefined, { numeric: true, sensitivity: 'base' })
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

function sortBy(key) {
  if (sortKey.value === key) sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

function toTsv(data) {
  return [
    columns.value.map(column => column.label).join('\t'),
    ...data.map(row => columns.value.map(column => String(row?.[column.key] ?? '')).join('\t')),
  ].join('\n')
}

async function copyRows() {
  const text = toTsv(visibleRows.value)
  if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text)
  copied.value = true
  window.setTimeout(() => { copied.value = false }, 1400)
}

function csvCell(value) {
  const text = String(value ?? '')
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

function downloadCsv() {
  const content = [
    columns.value.map(column => csvCell(column.label)).join(','),
    ...visibleRows.value.map(row => columns.value.map(column => csvCell(row?.[column.key])).join(',')),
  ].join('\n')
  downloadText(`${safeName(props.resource.title)}.csv`, `\ufeff${content}`, 'text/csv;charset=utf-8')
}

function safeName(value) {
  return String(value || 'table').replace(/[\\/:*?"<>|]/g, '_')
}
</script>

<style scoped>
.research-table-tool { min-width: 0; }
.table-toolbar { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.table-toolbar input { flex: 1; min-width: 80px; border: 1px solid #dfe5df; padding: 6px 8px; font-size: 11px; color: #344339; }
.table-toolbar button { border: 1px solid #dfe5df; background: #fff; color: #536057; padding: 5px 8px; font-size: 11px; cursor: pointer; }
.table-toolbar button:hover { border-color: #526e5a; color: #263d2e; }
.table-count { color: #849087; font-size: 10px; white-space: nowrap; }
.sort-button { border: 0; background: transparent; color: inherit; padding: 0; font: inherit; cursor: pointer; }
.sort-button span { margin-left: 4px; color: #526e5a; }
.resource-table-wrap { max-width: 100%; overflow: auto; }
.resource-table { width: 100%; min-width: 420px; border-collapse: collapse; font-size: 12px; }
.resource-table th, .resource-table td { border: 1px solid #e2e8e2; padding: 7px 9px; text-align: left; white-space: nowrap; }
.resource-table th { background: #f3f7f3; color: #536057; font-weight: 650; }
.table-empty { color: #849087; text-align: center !important; }
</style>
