<template>
  <div class="section-reflection">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <table v-if="section.items && section.items.length">
      <thead><tr><th>可能出现的问题</th><th>应对策略</th></tr></thead>
      <tbody>
        <tr v-for="(item, i) in section.items" :key="i">
          <td>{{ item.label }}</td>
          <td>{{ item.text }}</td>
        </tr>
      </tbody>
    </table>
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
