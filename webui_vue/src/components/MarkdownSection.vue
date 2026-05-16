<template>
  <div class="markdown-section">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-if="htmlContent" class="md-content" v-html="htmlContent"></div>
    <div v-else-if="section.content" class="md-content">{{ section.content }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const props = defineProps({
  section: { type: Object, required: true },
})

const htmlContent = computed(() => {
  const md = props.section.content
  if (typeof md === 'string') return marked.parse(md)
  return null
})
</script>
