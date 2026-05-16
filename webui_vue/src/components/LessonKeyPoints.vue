<template>
  <div class="section-key-points">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-for="(group, i) in section.content" :key="i" class="kp-group">
      <h3>{{ group.label }}</h3>
      <ol>
        <li v-for="(item, j) in group.items" :key="j" v-html="renderMd(item)"></li>
      </ol>
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
