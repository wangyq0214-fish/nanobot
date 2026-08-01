import { computed } from 'vue'

export const RESOURCE_TYPES = [
  { value: 'image', label: '图片' },
  { value: 'chart', label: '图表' },
  { value: 'table', label: '表格' },
  { value: 'citation', label: '引用' },
  { value: 'file', label: '文件' },
]

const RESOURCE_BLOCK_RE = /```(?:research-resource|json)?\s*\r?\n([\s\S]*?)\r?\n```/gi

export function parseResearchResources(value) {
  const resources = []
  const text = String(value || '')
  let match
  while ((match = RESOURCE_BLOCK_RE.exec(text))) {
    try {
      const parsed = JSON.parse(match[1])
      const candidates = Array.isArray(parsed) ? parsed : parsed?.resources || [parsed]
      for (const candidate of candidates) {
        const normalized = normalizeResource(candidate)
        if (normalized) resources.push(normalized)
      }
    } catch {
      // Keep malformed blocks as ordinary Markdown/code so the answer is not lost.
    }
  }
  RESOURCE_BLOCK_RE.lastIndex = 0
  // Also accept responses where the assistant returns the resource document
  // directly, without wrapping it in a research-resource code fence.
  for (const candidate of extractResourceDocuments(text).flatMap(item => item.candidates)) {
    const normalized = normalizeResource(candidate)
    if (normalized) resources.push(normalized)
  }
  return dedupeResources(resources)
}

export function stripResearchResourceBlocks(value) {
  let text = String(value || '').replace(RESOURCE_BLOCK_RE, '')
  const documents = extractResourceDocuments(text)
  for (const document of documents.reverse()) {
    text = `${text.slice(0, document.start)}${text.slice(document.end)}`
  }
  return text.replace(/\n{3,}/g, '\n\n').trim()
}

export function normalizeResource(value, fallbackId = '') {
  if (!value || typeof value !== 'object') return null
  const type = String(value.type || '').trim().toLowerCase()
  if (!RESOURCE_TYPES.some(item => item.value === type)) return null
  const id = String(value.id || fallbackId || `${type}-${Math.random().toString(36).slice(2, 9)}`)
  const resource = {
    ...value,
    id,
    type,
    title: String(value.title || typeLabel(type)),
    caption: String(value.caption || ''),
    sourceRefs: normalizeSourceRefs(value.sourceRefs || value.sources),
  }
  if (type === 'image') {
    const image = value.image && typeof value.image === 'object' ? value.image : value
    resource.image = {
      url: String(image.url || image.src || ''),
      alt: String(image.alt || resource.title),
      name: String(image.name || ''),
    }
    if (!resource.image.url) return null
  } else if (type === 'chart') {
    const chart = value.chart && typeof value.chart === 'object' ? value.chart : value
    const rows = Array.isArray(chart.rows || chart.data) ? (chart.rows || chart.data) : []
    const series = Array.isArray(chart.series) ? chart.series : []
    resource.chart = {
      kind: ['line', 'bar', 'scatter', 'pie'].includes(chart.kind || chart.chartType) ? (chart.kind || chart.chartType) : 'bar',
      xKey: String(chart.xKey || chart.x || ''),
      series: series.map((item, index) => ({
        key: String(item.key || item.field || (index === 0 ? 'value' : `value_${index}`)),
        label: String(item.label || item.name || item.key || `系列 ${index + 1}`),
      })),
      rows: rows.slice(0, 1000),
    }
    if (!resource.chart.series.length && resource.chart.rows[0]) {
      resource.chart.series = Object.keys(resource.chart.rows[0])
        .filter(key => key !== resource.chart.xKey)
        .slice(0, 6)
        .map(key => ({ key, label: key }))
    }
    if (!resource.chart.rows.length) return null
  } else if (type === 'table') {
    const table = value.table && typeof value.table === 'object' ? value.table : value
    const rows = Array.isArray(table.rows) ? table.rows : []
    const first = rows.find(row => row && typeof row === 'object' && !Array.isArray(row))
    const columns = Array.isArray(table.columns)
      ? table.columns.map((column, index) => typeof column === 'string'
        ? { key: column, label: column }
        : { key: String(column.key || column.label || `column_${index}`), label: String(column.label || column.key || `列 ${index + 1}`) })
      : first ? Object.keys(first).map(key => ({ key, label: key })) : []
    resource.table = { columns, rows: rows.slice(0, 2000) }
    if (!resource.table.columns.length) return null
  } else if (type === 'file') {
    const file = value.file && typeof value.file === 'object' ? value.file : value
    resource.file = {
      url: String(file.url || ''),
      name: String(file.name || resource.title),
      mime: String(file.mime || ''),
    }
    if (!resource.file.url) return null
  } else if (type === 'citation') {
    resource.citation = {
      author: String(value.author || ''),
      year: String(value.year || ''),
      evidence: String(value.evidence || value.quote || ''),
    }
  }
  return resource
}

export function resourcesForMessage(message) {
  const declared = Array.isArray(message?.resources) ? message.resources : []
  const parsed = parseResearchResources(message?.content)
  const media = Array.isArray(message?.mediaUrls)
    ? message.mediaUrls.map((item, index) => {
        const value = typeof item === 'string' ? { url: item } : item || {}
        return normalizeResource({
          id: `media-${message?.id || 'message'}-${index}`,
          type: 'image',
          title: value.name || '研究图片',
          image: { url: value.url, name: value.name, alt: value.name || '研究图片' },
        })
      })
    : []
  return dedupeResources([...declared.map(normalizeResource).filter(Boolean), ...parsed, ...media.filter(Boolean)])
}

export function researchMessageParts(message) {
  const text = String(message?.content || '')
  const documents = []
  let match
  while ((match = RESOURCE_BLOCK_RE.exec(text))) {
    try {
      const parsed = JSON.parse(match[1])
      const candidates = Array.isArray(parsed) ? parsed : parsed?.resources || [parsed]
      const resources = candidates.map(normalizeResource).filter(Boolean)
      if (resources.length) documents.push({ start: match.index, end: RESOURCE_BLOCK_RE.lastIndex, resources })
    } catch {
      // Keep malformed resource blocks as ordinary Markdown.
    }
  }
  RESOURCE_BLOCK_RE.lastIndex = 0

  for (const document of extractResourceDocuments(text)) {
    if (documents.some(item => document.start < item.end && document.end > item.start)) continue
    const resources = document.candidates.map(normalizeResource).filter(Boolean)
    if (resources.length) documents.push({ start: document.start, end: document.end, resources })
  }

  documents.sort((left, right) => left.start - right.start)
  const parts = []
  let cursor = 0
  const used = new Set()
  for (const document of documents) {
    const textPart = text.slice(cursor, document.start)
    if (textPart.trim()) parts.push({ type: 'text', content: textPart })
    parts.push({ type: 'resources', resources: document.resources })
    document.resources.forEach(resource => used.add(resource.id))
    cursor = document.end
  }
  const tail = text.slice(cursor)
  if (tail.trim()) parts.push({ type: 'text', content: tail })

  const remaining = resourcesForMessage(message).filter(resource => !used.has(resource.id))
  if (remaining.length) parts.push({ type: 'resources', resources: remaining })
  return parts
}

export function useResearchResources(messages) {
  const resources = computed(() => messages.value.flatMap(resourcesForMessage))
  return { resources }
}

export function downloadText(filename, content, mime = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([content], { type: mime }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function normalizeSourceRefs(value) {
  if (!Array.isArray(value)) return []
  return value.filter(item => item && typeof item === 'object').slice(0, 20).map(item => ({
    type: String(item.type || item.sourceType || 'source'),
    id: item.id ?? item.sourceId ?? '',
    label: String(item.label || item.title || item.sourceName || '来源'),
    page: item.page || item.pageNumber || '',
    url: String(item.url || ''),
    evidence: String(item.evidence || item.evidenceText || ''),
  }))
}

function dedupeResources(items) {
  const seen = new Set()
  return items.filter(item => {
    if (!item || seen.has(item.id)) return false
    seen.add(item.id)
    return true
  })
}

function extractResourceDocuments(value) {
  const text = String(value || '')
  const documents = []
  for (let start = 0; start < text.length; start += 1) {
    if (text[start] !== '{' && text[start] !== '[') continue
    const end = findJsonValueEnd(text, start)
    if (end < 0) continue
    try {
      const parsed = JSON.parse(text.slice(start, end))
      const candidates = Array.isArray(parsed) ? parsed : parsed?.resources || [parsed]
      if (Array.isArray(candidates) && candidates.some(candidate => normalizeResource(candidate))) {
        documents.push({ start, end, candidates })
        start = end - 1
      }
    } catch {
      // Ignore braces that are not a complete JSON resource document.
    }
  }
  return documents
}

function findJsonValueEnd(text, start) {
  const stack = []
  let quoted = false
  let escaped = false
  for (let index = start; index < text.length; index += 1) {
    const char = text[index]
    if (quoted) {
      if (escaped) escaped = false
      else if (char === '\\') escaped = true
      else if (char === '"') quoted = false
      continue
    }
    if (char === '"') {
      quoted = true
      continue
    }
    if (char === '{' || char === '[') stack.push(char)
    else if (char === '}' || char === ']') {
      const expected = char === '}' ? '{' : '['
      if (stack.pop() !== expected) return -1
      if (!stack.length) return index + 1
    }
  }
  return -1
}

function typeLabel(type) {
  return RESOURCE_TYPES.find(item => item.value === type)?.label || '研究资源'
}
