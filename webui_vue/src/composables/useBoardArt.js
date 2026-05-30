// Shared ASCII board-art → HTML converter.
// AI models often generate Unicode box-drawing characters (┌─┐└┘├┤│)
// for 板书设计 instead of markdown tables. This module detects and
// converts that format into styled glass-card HTML.

const BOX_CHARS_RE = /[┌└├┐┘┤┬┴┼│]/

export function isAsciiArt(text) {
  return BOX_CHARS_RE.test(text)
}

export function convertAsciiBoard(text) {
  // 1. Split into blocks by standalone ↓ / ⬇ arrows
  const rawLines = text.split('\n')
  const blocks = []
  let current = []
  for (const line of rawLines) {
    if (/^\s*[↓⬇]\s*$/.test(line)) {
      if (current.length > 0) { blocks.push(current.join('\n')); current = [] }
      continue
    }
    current.push(line)
  }
  if (current.length > 0) blocks.push(current.join('\n'))

  // 2. Clean each block: strip box-drawing border characters
  const cleaned = blocks.map(block => {
    const lines = block.split('\n')
    return lines
      .map(line => {
        let s = line
        s = s.replace(/^[\s]*[│┌└├┐┘┤┬┴┼]?[\s]*/, '')
        s = s.replace(/[\s]*[│┌└├┐┘┤┬┴┼]?[\s]*$/, '')
        return s
      })
      .filter(line => !/^[\s─━═┬┴├┤┼│]*$/.test(line) && line.trim().length > 0)
      .join('\n')
  }).filter(text => text.trim().length > 0)

  // 3. Render each block as a glass card
  const cards = cleaned.map(block => renderGlassCard(block))
  return cards.join('<div class="bb-arrow">↓</div>')
}

function renderGlassCard(text) {
  const lines = text.split('\n').filter(l => l.trim().length > 0)
  if (lines.length === 0) return ''

  const items = parseBlockItems(lines)

  // Merge consecutive text items into compact groups.
  // Group boundary = line ending with ：or : (sub-headers) or table/blockquote items.
  const merged = []
  let group = []
  for (const item of items) {
    if (item.kind !== 'text') {
      if (group.length) { merged.push({ kind: 'group', lines: group.splice(0) }) }
      merged.push(item)
      continue
    }
    const t = item.text
    // Blockquote-like lines handled separately
    if (/^[→←↓⬇]/.test(t)) {
      if (group.length) { merged.push({ kind: 'group', lines: group.splice(0) }) }
      merged.push(item)
      continue
    }
    // Line ending with ：or : starts a new group (sub-header)
    if (/[：:]$/.test(t) && group.length > 0) {
      merged.push({ kind: 'group', lines: group.splice(0) })
    }
    group.push(t)
  }
  if (group.length) { merged.push({ kind: 'group', lines: group.splice(0) }) }

  // Render merged items
  const parts = []
  let isFirst = true
  for (const item of merged) {
    if (item.kind === 'table') {
      parts.push(renderMiniTable(item.rows))
      isFirst = false
      continue
    }
    if (item.kind === 'group') {
      const texts = item.lines
      if (texts.length === 1) {
        const tag = isFirst ? 'p class="bb-title"' : 'p'
        parts.push(`<${tag}>${esc(texts[0])}</p>`)
        isFirst = false
      } else {
        // First line = sub-header (bold), rest = body lines joined with ｜
        const title = texts[0]
        const body = texts.slice(1).map(esc).join(' ｜ ')
        if (isFirst) {
          parts.push(`<p class="bb-title">${esc(title)}</p>`)
          isFirst = false
        } else {
          parts.push(`<p class="bb-subtitle">${esc(title)}</p>`)
        }
        if (body) parts.push(`<p class="bb-body">${body}</p>`)
      }
      continue
    }
    // Blockquote
    const t = item.text
    parts.push(`<blockquote><p>${esc(t.replace(/^[→←↓⬇]\s*/, ''))}</p></blockquote>`)
  }
  return `<div class="bb-card"><div class="bb-card-inner">${parts.join('')}</div></div>`
}

function parseBlockItems(lines) {
  const items = []
  let tableRows = []
  let inTable = false
  let sawTableSep = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()

    // Skip pure border lines (horizontal rules, junctions, etc.)
    if (/^[\s─━═┬┴├┤┼│]+$/.test(line)) continue

    // Horizontal rule like ───── or ────  ────  = table separator
    if (/^[─━]{2,}$/.test(line) || /^[─━]{2,}\s+[─━]{2,}$/.test(line)) {
      sawTableSep = true
      // If we already have rows, they're a header-less table; flush
      if (tableRows.length > 0) {
        items.push({ kind: 'table', rows: tableRows.splice(0) })
      }
      continue
    }

    // Try to split into 2 columns
    const cols = splitTwoCols(line)
    if (cols.length === 2) {
      tableRows.push(cols)
      inTable = true
      continue
    }

    // Line doesn't fit table pattern → flush table if collecting
    if (tableRows.length > 0) {
      items.push({ kind: 'table', rows: tableRows.splice(0) })
      inTable = false
      sawTableSep = false
    }

    // Regular text line
    items.push({ kind: 'text', text: line })
  }

  // Flush remaining
  if (tableRows.length > 0) {
    items.push({ kind: 'table', rows: tableRows.splice(0) })
  }

  return items
}

function splitTwoCols(line) {
  // Find the largest gap of whitespace and split there
  const gaps = []
  let gapStart = -1
  for (let i = 0; i < line.length; i++) {
    if (line[i] === ' ' || line[i] === '\t') {
      if (gapStart === -1) gapStart = i
    } else {
      if (gapStart !== -1) {
        gaps.push({ start: gapStart, end: i, len: i - gapStart })
        gapStart = -1
      }
    }
  }
  if (gapStart !== -1) gaps.push({ start: gapStart, end: line.length, len: line.length - gapStart })
  if (gaps.length === 0) return []
  gaps.sort((a, b) => b.len - a.len)
  const best = gaps[0]
  if (best.len < 2) return []
  const col1 = line.slice(0, best.start).trim()
  const col2 = line.slice(best.end).trim()
  if (!col1 || !col2) return []
  return [col1, col2]
}

function renderMiniTable(rows) {
  if (rows.length === 0) return ''
  const hasHeader = rows.length >= 2
  let html = '<table class="bb-table"><tbody>'
  for (let i = 0; i < rows.length; i++) {
    const tag = (hasHeader && i === 0) ? 'th' : 'td'
    html += `<tr><${tag}>${esc(rows[i][0])}</${tag}><${tag}>${esc(rows[i][1])}</${tag}></tr>`
  }
  html += '</tbody></table>'
  return html
}

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
