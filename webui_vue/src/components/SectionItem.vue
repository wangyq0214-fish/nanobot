<template>
  <template v-for="(sec, ki) in sections" :key="ki">
    <!-- Container sections with children — each child gets its own sub-card -->
    <div v-if="sec.kind === 'teacher'" class="activity-row">
      <div class="act-col">
        <div class="act-label">{{ sec.label || '教师活动' }}</div>
        <template v-if="sec.children && sec.children.length">
          <div v-for="(child, ci) in sec.children" :key="ci" class="sub-card">
            <SectionItem :sections="[child]" />
          </div>
        </template>
        <div v-else-if="sec.text" v-html="renderBlock(sec.text)"></div>
      </div>
    </div>

    <div v-else-if="sec.kind === 'student'" class="activity-row">
      <div class="act-col">
        <div class="act-label">学生活动</div>
        <template v-if="sec.children && sec.children.length">
          <div v-for="(child, ci) in sec.children" :key="ci" class="sub-card">
            <SectionItem :sections="[child]" />
          </div>
        </template>
        <div v-else-if="sec.text" v-html="renderBlock(sec.text)"></div>
      </div>
    </div>

    <div v-else-if="sec.kind === 'design_intent'" class="design-intent">
      <strong>设计意图：</strong>
      <template v-if="sec.children && sec.children.length">
        <div v-for="(child, ci) in sec.children" :key="ci" class="sub-card" style="margin-top:6px;">
          <SectionItem :sections="[child]" />
        </div>
      </template>
      <span v-else-if="sec.text" v-html="renderBlock(sec.text)"></span>
    </div>

    <div v-else-if="sec.kind === 'activity'" class="activity-row">
      <div class="act-col" v-if="sec.teacherChildren ? sec.teacherChildren.length : sec.teacher">
        <div class="act-label">教师活动</div>
        <template v-if="sec.teacherChildren && sec.teacherChildren.length">
          <div v-for="(child, ci) in sec.teacherChildren" :key="ci" class="sub-card">
            <SectionItem :sections="[child]" />
          </div>
        </template>
        <div v-else-if="sec.teacher" v-html="renderBlock(sec.teacher)"></div>
      </div>
      <div class="act-col" v-if="sec.studentChildren ? sec.studentChildren.length : sec.student">
        <div class="act-label">学生活动</div>
        <template v-if="sec.studentChildren && sec.studentChildren.length">
          <div v-for="(child, ci) in sec.studentChildren" :key="ci" class="sub-card">
            <SectionItem :sections="[child]" />
          </div>
        </template>
        <div v-else-if="sec.student" v-html="renderBlock(sec.student)"></div>
      </div>
    </div>

    <!-- Leaf sections -->
    <p v-else-if="sec.kind === 'heading'"><strong>{{ sec.text }}</strong></p>
    <div v-else-if="sec.kind === 'text'" v-html="renderBlock(sec.text)"></div>
    <blockquote v-else-if="sec.kind === 'quote'" v-html="renderMd(sec.text)"></blockquote>
    <div v-else-if="sec.kind === 'intention'" class="design-intent"><strong>设计意图：</strong><span v-html="renderMd(sec.text)"></span></div>
    <div v-else-if="sec.kind === 'step_title'" class="highlight-box" style="border-color:var(--accent-amber);background:var(--accent-amber-soft);"><strong>{{ sec.text }}</strong></div>

    <div v-else-if="sec.kind === 'summary'" class="highlight-box" style="border-color:var(--accent-amber);background:var(--accent-amber-soft);">
      <strong>📋 课堂总结</strong>
      <template v-if="sec.children && sec.children.length">
        <div v-for="(child, ci) in sec.children" :key="ci" class="sub-card" style="margin-top:8px;">
          <SectionItem :sections="[child]" />
        </div>
      </template>
      <p v-else-if="sec.text" v-html="renderBlock(sec.text)"></p>
    </div>
    <div v-else-if="sec.kind === 'homework'" class="highlight-box" style="border-color:var(--accent-amber);background:var(--accent-amber-soft);">
      <strong>📝 课后作业</strong>
      <template v-if="sec.children && sec.children.length">
        <div v-for="(child, ci) in sec.children" :key="ci" class="sub-card" style="margin-top:8px;">
          <SectionItem :sections="[child]" />
        </div>
      </template>
      <p v-else-if="sec.text" v-html="renderBlock(sec.text)"></p>
    </div>

    <div v-else-if="sec.kind === 'homework_item'" class="sub-card">
      <strong>{{ sec.label }}</strong>
      <div v-html="renderBlock(sec.text)"></div>
    </div>

    <div v-else-if="sec.kind === 'questions'" class="question-list">
      <blockquote v-for="(q, qi) in sec.items" :key="qi" v-html="renderMd(q)"></blockquote>
    </div>

    <table v-else-if="sec.kind === 'table'">
      <thead><tr><th v-for="h in sec.headers" :key="h">{{ h }}</th></tr></thead>
      <tbody>
        <tr v-for="(row, ri) in sec.rows" :key="ri">
          <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
        </tr>
      </tbody>
    </table>

    <ol v-else-if="sec.kind === 'ordered_list'">
      <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
    </ol>
    <ol v-else-if="sec.kind === 'ordered_list_start'" :start="sec.start">
      <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
    </ol>

    <ul v-else-if="sec.kind === 'list'">
      <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
    </ul>

    <div v-else-if="sec.kind === 'highlight_box'" class="highlight-box">
      <p v-if="sec.title"><strong>{{ sec.title }}</strong></p>
      <ul><li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li></ul>
    </div>

    <div v-else-if="sec.kind === 'exercise'" class="highlight-box" style="border-color:var(--accent-amber);background:var(--accent-amber-soft);">
      <strong>✏️ 课堂练习</strong>
      <p v-html="renderMd(sec.text)"></p>
    </div>

    <div v-else-if="sec.kind === 'board_note'" class="mini-board">
      <template v-for="(node, ni) in sec.nodes" :key="ni">
        <div class="mini-fc-box">
          <div class="mini-fc-title">{{ node.title }}</div>
          <ul v-if="node.items && node.items.length" class="mini-fc-items">
            <li v-for="(item, ii) in node.items" :key="ii">{{ item }}</li>
          </ul>
        </div>
        <span v-if="ni < sec.nodes.length - 1" class="mini-fc-arrow">→</span>
      </template>
    </div>

    <div v-else-if="sec.kind === 'board_card'" class="board-card">
      <div class="board-card-label">板书</div>
      <div class="board-card-body" v-html="renderBoardCard(sec.markdown)"></div>
    </div>

    <div v-else class="fallback-section">
      <span class="fallback-kind-tag">{{ sec.kind }}</span>
      <div v-if="sec.text" v-html="renderMd(sec.text)"></div>
      <ul v-else-if="sec.items">
        <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
      </ul>
      <pre v-else>{{ JSON.stringify(sec, null, 1) }}</pre>
    </div>
  </template>
</template>

<script setup>
import { marked } from 'marked'
import { isAsciiArt, convertAsciiBoard } from '../composables/useBoardArt.js'

defineProps({ sections: { type: Array, required: true } })

function renderMd(text) { return marked.parseInline(text) }
function renderBlock(text) {
  if (isAsciiArt(text)) return convertAsciiBoard(text)
  return marked.parse(text)
}
function renderBoardCard(md) {
  if (!md) return ''
  let p = md.replace(/^```[\s\S]*?\n([\s\S]*?)\n```$/g, '$1').replace(/^```\w*\n?|```$/gm, '')
  if (isAsciiArt(p)) return convertAsciiBoard(p)
  p = p.replace(/^[↓⬇]$/gm, '---')
  p = p.replace(/^[→←]\s*(.+)$/gm, '> $1')
  p = p.replace(/^(?!>|\|)(.+[→←].+)$/gm, '> $1')
  let html = marked.parse(p)
  html = html.replace(/<blockquote>\s*<p>([^<]*？)<\/p>\s*<\/blockquote>/g, '<blockquote class="is-question"><p>$1</p></blockquote>')
  html = html.replace(/<p><strong>(.{1,12}?(?:批评|问|质疑|反驳|攻击).{0,6}?)[：:]<\/strong>\s*(.+?)<\/p>\s*<p><strong>(.{1,12}?(?:回应|答|回复|辩解|辩护|说).{0,6}?)[：:]<\/strong>\s*(.+?)<\/p>/g, '<div class="qa-bubble q"><strong>$1：</strong>$2</div><div class="qa-bubble a"><strong>$3：</strong>$4</div>')
  return html
}
</script>

<style scoped>
.design-intent {
  background: var(--accent-soft); border-left: 3px solid var(--accent);
  padding: 6px 12px; margin: 8px 0; border-radius: 0 6px 6px 0;
  font-size: 0.82rem; color: var(--text-secondary);
}
.question-list blockquote { margin: 6px 0; }
.activity-row { display: flex; gap: 12px; margin: 8px 0; }
.act-col { flex: 1; background: var(--accent-teal-soft); border-left: 3px solid var(--accent-teal); border-radius: 0 8px 8px 0; padding: 10px 14px; }
.act-col :deep(ol) { padding-left: 22px; margin: 0; }
.act-col :deep(ol li) {
  font-size: 0.95rem; line-height: 1.8;
  padding: 6px 0; margin-bottom: 6px;
  border-bottom: 1px dashed var(--border-light, #e0dcd5);
}
.act-col :deep(ol li:last-child) { border-bottom: none; margin-bottom: 0; }
.act-col :deep(ul) { font-size: 0.95rem; }
.act-col :deep(ul li) { font-size: 0.95rem; line-height: 1.8; padding: 2px 0; }
.act-col :deep(table) { margin: 8px 0; font-size: 0.85rem; }
.act-col :deep(blockquote) { margin: 6px 0; font-size: 0.88rem; }
.act-col :deep(.design-intent) { margin: 8px 0; }
/* Each child section inside act-col gets its own mini card */
.sub-card {
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--border-light, #e8e4db);
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
}
.sub-card:last-child { margin-bottom: 0; }
.act-label {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--accent-teal); margin-bottom: 4px;
}
.highlight-box {
  background: var(--accent-soft); border: 1.5px solid var(--accent-light);
  border-radius: 10px; padding: 12px 16px; margin: 12px 0;
}
.fallback-section {
  margin: 8px 0; padding: 10px 14px;
  border: 1px dashed var(--border-medium);
  border-radius: 8px; background: var(--bg-tag);
}
.fallback-kind-tag {
  display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-size: 0.62rem; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--text-muted);
  background: var(--border-light); margin-bottom: 6px;
}
.mini-board {
  display: flex; flex-wrap: wrap; align-items: flex-start; gap: 4px;
  margin: 10px 0; padding: 10px;
  background: rgba(139,122,200,0.04);
  border: 1.5px dashed rgba(139,122,200,0.25);
  border-radius: 10px;
}
.mini-fc-box {
  background: rgba(139,122,200,0.08);
  border: 2px solid rgba(139,122,200,0.45);
  border-radius: 10px;
  padding: 8px 12px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(139,122,200,0.08);
  min-width: 80px;
}
.mini-fc-title {
  font-size: 0.82rem; font-weight: 700;
  color: rgba(100,70,180,0.95);
  margin-bottom: 4px; padding-bottom: 4px;
  border-bottom: 1px dashed rgba(139,122,200,0.25);
}
.mini-fc-items {
  list-style: none; padding: 0; margin: 0;
  font-size: 0.78rem; color: var(--text-secondary);
}
.mini-fc-items li { line-height: 1.6; }
.mini-fc-items li::before {
  content: '·'; color: rgba(139,122,200,0.35); margin-right: 4px;
}
.mini-fc-arrow {
  font-size: 1.2rem; color: rgba(139,122,200,0.55); font-weight: 700;
  align-self: center; flex-shrink: 0;
}
.board-card {
  margin: 16px 0;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
  padding: 24px 28px;
  border: 1px solid #e0dcd5;
}
.board-card-label {
  font-size: 0.68rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #b0a89a;
  margin-bottom: 14px;
  text-align: center;
}
.board-card-body :deep(h3) {
  text-align: center;
  font-size: 1.05rem;
  font-weight: 700;
  color: #2c2c2c;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e8e4db;
}
.board-card-body :deep(table) {
  width: 100%; table-layout: fixed;
  border-collapse: separate !important;
  border-spacing: 14px 5px; margin: 0 0 16px 0;
}
.board-card-body :deep(thead th) {
  font-size: 0.92rem; font-weight: 700;
  padding: 8px 0 6px; text-align: center;
  border-bottom: 2px solid #e8e4db; color: #2c2c2c !important;
  background: transparent !important;
}
.board-card-body :deep(thead th:first-child) { color: #8b6914; }
.board-card-body :deep(thead th:last-child)  { color: #3a5a8c; }
.board-card-body :deep(tbody td) {
  padding: 10px 14px; text-align: center; vertical-align: middle;
  font-size: 0.88rem; line-height: 1.65; border-radius: 6px;
  border-bottom: none !important; color: #2c2c2c !important;
}
.board-card-body :deep(tbody td:first-child) {
  background: #f7f4f0; border-left: 3px solid #c4b99a;
  font-weight: normal !important; color: #2c2c2c !important;
}
.board-card-body :deep(tbody td:last-child) {
  background: #f0f2f7; border-left: 3px solid #9aacb9;
  color: #2c2c2c !important;
}
.board-card-body :deep(blockquote) {
  text-align: center; margin: 14px 0; padding: 14px 24px;
  background: #fdf8f0 !important; border: 1px solid #e8dcc8 !important;
  border-radius: 8px; font-size: 0.92rem; color: #5c4300 !important;
}
.board-card-body :deep(blockquote p) { margin: 0; }
.board-card-body :deep(blockquote.is-question) {
  font-size: 1.15rem; font-weight: 600; color: #6b3a0a;
  padding: 18px 30px;
  background: linear-gradient(135deg, #fef9f0 0%, #fef5e4 100%);
  border: 1.5px solid #d4a853; border-radius: 10px;
}
.board-card-body :deep(.qa-bubble) {
  padding: 10px 16px; border-radius: 8px;
  background: #f9f8f5; border: 1px solid #d0cbc0;
  font-size: 0.88rem; margin: 6px 0; max-width: 88%;
}
.board-card-body :deep(.qa-bubble.q) { border-bottom-left-radius: 2px; }
.board-card-body :deep(.qa-bubble.a) {
  border-bottom-right-radius: 2px; background: #f4f2fa;
  border-color: #d5d0e8; margin-left: auto;
}
.board-card-body :deep(ul) { list-style: none; padding: 0; margin: 8px 0 16px; }
.board-card-body :deep(ul li) {
  padding: 6px 0 6px 28px; font-size: 0.88rem; line-height: 1.65; position: relative;
}
.board-card-body :deep(ul li::before) {
  content: '◆'; position: absolute; left: 4px; top: 6px;
  font-size: 0.5rem; color: #8b6f47; opacity: 0.55;
}
.board-card-body :deep(ol) { padding-left: 24px; margin: 8px 0 16px; }
.board-card-body :deep(ol li) { font-size: 0.88rem; line-height: 1.65; padding: 4px 0; }
.board-card-body :deep(p) { font-size: 0.88rem; line-height: 1.75; margin: 0 0 6px; }
.board-card-body :deep(hr) { border: none; border-top: 1px dashed #e8e4db; margin: 16px 0; }
.board-card-body :deep(strong) { color: #4a3520; }
.board-card-body :deep(.bb-card) {
  background: #faf9f6; border: 1px solid #e0dcd5;
  border-radius: 10px; padding: 14px 18px; margin: 10px 0;
}
.board-card-body :deep(.bb-title) {
  font-weight: 700; color: #4a3520 !important;
  font-size: 0.92rem; margin-bottom: 8px; padding-bottom: 6px;
  border-bottom: 1px solid #e8e4db;
}
.board-card-body :deep(.bb-subtitle) {
  font-weight: 700; color: #5c4300; font-size: 0.85rem; margin: 6px 0 2px;
}
.board-card-body :deep(.bb-body) { margin: 0 0 2px; line-height: 1.7; }
.board-card-body :deep(.bb-table) {
  width: 100%; border-collapse: separate; border-spacing: 8px 4px;
  margin: 8px 0; background: transparent;
}
.board-card-body :deep(.bb-table td), .board-card-body :deep(.bb-table th) {
  text-align: center; padding: 8px 10px; font-size: 0.82rem;
  border-radius: 5px; color: #2c2c2c;
}
.board-card-body :deep(.bb-table td:first-child) {
  background: #f7f4f0; border-left: 3px solid #c4b99a;
}
.board-card-body :deep(.bb-table td:last-child) {
  background: #f0f2f7; border-left: 3px solid #9aacb9;
}
.board-card-body :deep(.bb-table th) {
  font-weight: 700; color: #5c4300; border-bottom: 2px solid #e8e4db;
  background: transparent;
}
.board-card-body :deep(.bb-arrow) {
  text-align: center; color: #b0a89a; font-size: 1rem; margin: 6px 0; user-select: none;
}
</style>
