<template>
  <div class="section-reflection">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <ul v-if="section.items">
      <li v-for="(item, i) in section.items" :key="i" class="refl-item" :class="'refl-' + item.kind">
        <strong :class="'tag tag-' + item.kind">{{ item.label }}</strong>
        <span>{{ item.text }}</span>
      </li>
    </ul>
    <!-- fallback: plain markdown -->
    <div v-else-if="typeof section.content === 'string'" class="md-content" v-html="renderMd(section.content)"></div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

defineProps({ section: { type: Object, required: true } })

function renderMd(text) {
  return marked.parse(text)
}
</script>

<style scoped>
.refl-item { margin: 8px 0; line-height: 1.7; display: flex; align-items: flex-start; gap: 8px; }
.tag {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 0.72rem; font-weight: 600; flex-shrink: 0; margin-top: 2px;
}
.tag-difficulty { background: rgba(245,158,11,0.08); color: #E09000; }
.tag-contingency { background: rgba(14,165,185,0.08); color: var(--accent-teal); }
.tag-improvement { background: rgba(107,93,240,0.08); color: var(--accent); }
</style>
