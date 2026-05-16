<template>
  <div class="section-process">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-for="(phase, pi) in section.phases" :key="pi" class="process-phase">
      <h3 class="phase-title">{{ phase.name }}<span class="phase-duration" v-if="phase.duration">（{{ phase.duration }}）</span></h3>
      <div v-for="(step, si) in phase.steps" :key="si" class="process-step">
        <h4 class="step-name">{{ step.name }}<span class="step-duration" v-if="step.duration">（{{ step.duration }}）</span></h4>
        <div v-for="(sec, ki) in step.sections" :key="ki">
          <!-- kind-based rendering -->
          <p v-if="sec.kind === 'heading'"><strong>{{ sec.text }}</strong></p>
          <p v-else-if="sec.kind === 'text'" v-html="renderMd(sec.text)"></p>
          <blockquote v-else-if="sec.kind === 'quote'" v-html="renderMd(sec.text)"></blockquote>
          <div v-else-if="sec.kind === 'design_intent'" class="design-intent"><strong>设计意图：</strong>{{ sec.text }}</div>

          <p v-else-if="sec.kind === 'step_title'"><strong>{{ sec.text }}</strong></p>

          <div v-else-if="sec.kind === 'questions'" class="question-list">
            <blockquote v-for="(q, qi) in sec.items" :key="qi" v-html="renderMd(q)"></blockquote>
          </div>

          <div v-else-if="sec.kind === 'activity'" class="activity-row">
            <div class="act-col" v-if="sec.teacher">
              <div class="act-label">教师活动</div>
              <ul><li v-html="renderMd(sec.teacher)"></li></ul>
            </div>
            <div class="act-col" v-if="sec.student">
              <div class="act-label">学生活动</div>
              <ul><li v-html="renderMd(sec.student)"></li></ul>
            </div>
          </div>

          <!-- AI-returned kinds: teacher / student as single-col activities -->
          <div v-else-if="sec.kind === 'teacher'" class="activity-row">
            <div class="act-col">
              <div class="act-label">教师活动</div>
              <ul><li v-html="renderMd(sec.text)"></li></ul>
            </div>
          </div>
          <div v-else-if="sec.kind === 'student'" class="activity-row">
            <div class="act-col">
              <div class="act-label">学生活动</div>
              <ul><li v-html="renderMd(sec.text)"></li></ul>
            </div>
          </div>
          <div v-else-if="sec.kind === 'intention'" class="design-intent"><strong>设计意图：</strong><span v-html="renderMd(sec.text)"></span></div>
          <div v-else-if="sec.kind === 'summary'" class="highlight-box"><strong>📋 课堂总结</strong><p v-html="renderMd(sec.text)"></p></div>
          <div v-else-if="sec.kind === 'homework'" class="highlight-box" style="border-color:var(--accent-teal);background:var(--accent-teal-soft);"><strong>📝 课后作业</strong><p v-html="renderMd(sec.text)"></p></div>

          <table v-else-if="sec.kind === 'table'">
            <tr><th v-for="h in sec.headers" :key="h">{{ h }}</th></tr>
            <tr v-for="(row, ri) in sec.rows" :key="ri">
              <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
            </tr>
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
            <ul>
              <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
            </ul>
          </div>

          <div v-else-if="sec.kind === 'exercise'" class="highlight-box" style="border-color:var(--accent-amber);background:var(--accent-amber-soft);">
            <strong>✏️ 课堂练习</strong>
            <p v-html="renderMd(sec.text)"></p>
          </div>

          <!-- Catch-all: render ANY unrecognized kind so content is never silently dropped.
               Shows a subtle kind label + the text / items / raw content. -->
          <div v-else class="fallback-section">
            <span class="fallback-kind-tag">{{ sec.kind }}</span>
            <div v-if="sec.text" v-html="renderMd(sec.text)"></div>
            <ul v-else-if="sec.items">
              <li v-for="(item, li) in sec.items" :key="li" v-html="renderMd(item)"></li>
            </ul>
            <pre v-else>{{ JSON.stringify(sec, null, 1) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

defineProps({ section: { type: Object, required: true } })

function renderMd(text) {
  return marked.parseInline(text)
}
</script>

<style scoped>
.phase-title { margin: 24px 0 12px; }
.phase-duration { font-weight: 400; font-size: 0.85rem; color: var(--text-muted); }
.step-name { margin: 16px 0 8px; color: var(--text-secondary); }
.step-duration { font-weight: 400; font-size: 0.80rem; color: var(--text-muted); }
.design-intent {
  background: var(--accent-soft); border-left: 3px solid var(--accent);
  padding: 6px 12px; margin: 8px 0; border-radius: 0 6px 6px 0;
  font-size: 0.82rem; color: var(--text-secondary);
}
.question-list blockquote { margin: 6px 0; }
.activity-row { display: flex; gap: 12px; margin: 8px 0; }
.act-col { flex: 1; background: var(--bg-tag); border-radius: 8px; padding: 10px 14px; }
.act-label {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--accent); margin-bottom: 4px;
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
</style>
