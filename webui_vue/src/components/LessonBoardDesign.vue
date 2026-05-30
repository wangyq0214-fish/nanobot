<template>
  <div class="section-board">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div class="chalkboard">
      <div class="board-frame">
        <div class="board-inner">
          <div class="board-corner tl"></div>
          <div class="board-corner br"></div>
          <div class="board-markdown" v-html="renderBoard(section.content?.markdown || '')"></div>
          <div class="chalk-dust"></div>
        </div>
      </div>
      <div class="board-tray"></div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'
import { isAsciiArt, convertAsciiBoard } from '../composables/useBoardArt.js'

defineProps({ section: { type: Object, required: true } })

function renderBoard(md) {
  if (!md) return ''
  // Strip code fences — AI sometimes wraps markdown in ``` fences
  let processed = md
    .replace(/^```[\s\S]*?\n([\s\S]*?)\n```$/g, '$1')
    .replace(/^```\w*\n?|```$/gm, '')

  // Detect Unicode box-drawing art → convert to glass-card HTML
  if (isAsciiArt(processed)) {
    return convertAsciiBoard(processed)
  }

  // Pre-process arrow notation → markdown structures
  processed = processed.replace(/^[↓⬇]$/gm, '---')
  processed = processed.replace(/^[→←]\s*(.+)$/gm, '> $1')
  processed = processed.replace(/^(?!>|\|)(.+[→←].+)$/gm, '> $1')
  let html = marked.parse(processed)
  // Blockquotes ending with ？ → large chalk highlight
  html = html.replace(/<blockquote>\s*<p>([^<]*？)<\/p>\s*<\/blockquote>/g,
    '<blockquote class="is-question"><p>$1</p></blockquote>')
  // QA pairs
  html = html.replace(
    /<p><strong>(.{1,12}?(?:批评|问|质疑|反驳|攻击).{0,6}?)[：:]<\/strong>\s*(.+?)<\/p>\s*<p><strong>(.{1,12}?(?:回应|答|回复|辩解|辩护|说).{0,6}?)[：:]<\/strong>\s*(.+?)<\/p>/g,
    '<div class="qa-bubble q"><strong>$1：</strong>$2</div><div class="qa-bubble a"><strong>$3：</strong>$4</div>'
  )
  return html
}
</script>

<style scoped>
.section-board h2 {
  margin-bottom: 12px;
  border-left: 3px solid #8b7355 !important;
  color: var(--text-primary, #2c2c2c) !important;
}

/* ── Chalkboard frame ── */
.chalkboard {
  margin: 20px 0;
  border-radius: 12px;
  overflow: hidden;
}
.board-frame {
  background: #3b3b2f;
  border-radius: 12px 12px 0 0;
  padding: 6px;
}
.board-inner {
  background: #2d4a3e;
  border-radius: 8px;
  padding: 28px 32px;
  position: relative;
  min-height: 80px;
}
.board-corner {
  position: absolute;
  width: 24px; height: 24px;
  border-radius: 3px;
  border: 2px solid rgba(255,255,255,0.10);
}
.board-corner.tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
.board-corner.br { bottom: 10px; right: 10px; border-left: none; border-top: none; }
.board-tray {
  height: 10px;
  background: linear-gradient(to bottom, #5a5a46, #4a4a3a);
  border-radius: 0 0 12px 12px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.chalk-dust {
  position: absolute;
  bottom: 4px; right: 18px;
  width: 60px; height: 2px;
  background: rgba(255,255,255,0.04);
  border-radius: 2px;
}

/* ── Chalkboard markdown content ── */
.board-markdown {
  /* Reset CSS variables so global .doc-content selectors resolve to chalk colors */
  --accent: #f0e6c0;
  --accent-deep: #e0d4a0;
  --accent-soft: rgba(255,255,255,0.04);
  --accent-light: rgba(255,255,255,0.12);
  --accent-amber: rgba(240,216,96,0.20);
  --text-primary: rgba(255,255,255,0.90);
  --text-secondary: rgba(255,255,255,0.78);
  --divider: rgba(255,255,255,0.10);
  --bg-tag: rgba(255,255,255,0.05);

  color: rgba(255,255,255,0.90);
  font-family: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
  line-height: 1.9;
  font-size: 0.92rem;
}

/* h3 = main title on chalkboard */
.board-markdown :deep(h3) {
  text-align: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: #f0e6c0 !important;
  margin: 0 0 18px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}

.board-markdown :deep(h4) {
  font-size: 1rem;
  font-weight: 700;
  color: #e8dca0 !important;
  margin: 16px 0 8px;
}

/* Table — complete override of .doc-content table styles */
.board-markdown :deep(table) {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate !important;
  border-spacing: 12px 6px;
  margin: 0 0 18px;
  overflow: visible !important;
  border-radius: 0 !important;
  background: transparent !important;
  font-size: inherit;
}
.board-markdown :deep(thead th),
.board-markdown :deep(tbody td),
.board-markdown :deep(tr th),
.board-markdown :deep(tr td) {
  text-align: center !important;
  vertical-align: middle;
  padding: 8px 10px;
  font-size: 0.85rem;
  line-height: 1.7;
  border-radius: 5px;
  border: none !important;
  color: rgba(255,255,255,0.85) !important;
  background: transparent !important;
  font-weight: 400 !important;
}
.board-markdown :deep(thead th) {
  font-weight: 700 !important;
  color: #f0e6c0 !important;
  border-bottom: 1px solid rgba(255,255,255,0.18) !important;
  background: transparent !important;
  letter-spacing: 0 !important;
}
.board-markdown :deep(tbody td) {
  background: rgba(255,255,255,0.04) !important;
  color: rgba(255,255,255,0.85) !important;
}
.board-markdown :deep(tbody tr:hover td) {
  background: rgba(255,255,255,0.04) !important;
}

/* blockquote → centered chalk highlight bar */
.board-markdown :deep(blockquote) {
  text-align: center;
  margin: 10px 0;
  padding: 10px 20px;
  background: rgba(255,255,255,0.06) !important;
  border-left: none !important;
  border-radius: 6px !important;
  font-size: 0.88rem;
  color: #e0d4a0 !important;
}
.board-markdown :deep(blockquote.is-question) {
  font-size: 1.05rem;
  font-weight: 600;
  color: #f0d860 !important;
  padding: 14px 24px;
  background: rgba(240,216,96,0.08) !important;
  border: 1px solid rgba(240,216,96,0.25);
}
.board-markdown :deep(blockquote p) {
  margin: 0;
}

/* QA bubbles */
.board-markdown :deep(.qa-bubble) {
  padding: 8px 14px;
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  font-size: 0.85rem;
  margin: 5px 0;
  max-width: 85%;
  color: rgba(255,255,255,0.85);
}
.board-markdown :deep(.qa-bubble.q) {
  border-bottom-left-radius: 2px;
  border-left: 2px solid rgba(220,190,130,0.4);
}
.board-markdown :deep(.qa-bubble.a) {
  border-bottom-right-radius: 2px;
  border-right: 2px solid rgba(170,200,210,0.4);
  margin-left: auto;
}

/* unordered list */
.board-markdown :deep(ul) {
  list-style: none;
  padding: 0;
  margin: 6px 0 14px;
}
.board-markdown :deep(ul li) {
  padding: 3px 0 3px 22px;
  font-size: 0.85rem;
  line-height: 1.7;
  position: relative;
  color: rgba(255,255,255,0.82) !important;
}
.board-markdown :deep(ul li::before) {
  content: '◇';
  position: absolute;
  left: 2px; top: 3px;
  font-size: 0.4rem;
  color: rgba(240,230,192,0.40);
}

/* ordered list */
.board-markdown :deep(ol) {
  padding-left: 22px;
  margin: 6px 0 14px;
}
.board-markdown :deep(ol li) {
  font-size: 0.85rem;
  line-height: 1.7;
  padding: 3px 0;
  color: rgba(255,255,255,0.82) !important;
}

/* paragraphs */
.board-markdown :deep(p) {
  font-size: 0.85rem;
  line-height: 1.8;
  margin: 0 0 6px;
  color: rgba(255,255,255,0.82) !important;
}

/* hr divider */
.board-markdown :deep(hr) {
  border: none !important;
  border-top: 1px dashed rgba(255,255,255,0.12);
  margin: 14px 0;
  background: none !important;
}

/* bold & emphasis */
.board-markdown :deep(strong) { color: #f0e6c0 !important; font-weight: 700; }
.board-markdown :deep(em)     { color: #e0d4a0 !important; }

/* code */
.board-markdown :deep(code) {
  background: rgba(255,255,255,0.08);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 0.82rem;
  color: #e0d4a0 !important;
}
.board-markdown :deep(pre) {
  background: rgba(0,0,0,0.15);
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
}

/* ── ASCII board → glass cards ── */
.board-markdown :deep(.bb-card) {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 10px;
  padding: 14px 18px;
  margin: 10px 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
}
.board-markdown :deep(.bb-card-inner) {
  /* flex column for internal layout */
}
.board-markdown :deep(.bb-title) {
  font-weight: 700;
  color: #f0e6c0 !important;
  font-size: 0.92rem;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 6px;
}
.board-markdown :deep(.bb-subtitle) {
  font-weight: 700;
  color: #e8dca0 !important;
  font-size: 0.85rem;
  margin: 6px 0 2px;
}
.board-markdown :deep(.bb-body) {
  margin: 0 0 2px;
  line-height: 1.7;
}
.board-markdown :deep(.bb-table) {
  width: 100%;
  border-collapse: separate !important;
  border-spacing: 6px 4px;
  margin: 8px 0;
  background: transparent !important;
}
.board-markdown :deep(.bb-table td),
.board-markdown :deep(.bb-table th) {
  text-align: center !important;
  padding: 6px 8px;
  font-size: 0.82rem;
  border-radius: 5px;
  border: none !important;
  color: rgba(255,255,255,0.85) !important;
  background: rgba(255,255,255,0.04) !important;
}
.board-markdown :deep(.bb-table th) {
  font-weight: 700;
  color: #f0e6c0 !important;
  border-bottom: 1px solid rgba(255,255,255,0.14) !important;
  background: transparent !important;
}
.board-markdown :deep(.bb-arrow) {
  text-align: center;
  color: rgba(240,232,200,0.55);
  font-size: 1rem;
  margin: 6px 0;
  user-select: none;
}
</style>
