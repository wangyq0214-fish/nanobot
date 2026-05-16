<template>
  <div class="section-exercises">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-if="section.content">
      <h3 v-if="section.content.basic?.length">基础练习</h3>
      <ol v-if="section.content.basic?.length">
        <li v-for="(item, i) in section.content.basic" :key="i" v-html="renderMd(item)"></li>
      </ol>
      <p v-if="section.content.advanced"><strong>拓展练习（选做）：</strong><span v-html="renderMd(section.content.advanced)"></span></p>
      <p v-if="section.content.homework"><strong>课后作业：</strong><span v-html="renderMd(section.content.homework)"></span></p>
    </div>
    <!-- fallback: plain markdown -->
    <div v-else-if="typeof section.content === 'string'" class="md-content" v-html="renderMd(section.content)"></div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

defineProps({ section: { type: Object, required: true } })

function renderMd(text) {
  return marked.parseInline(text)
}
</script>
