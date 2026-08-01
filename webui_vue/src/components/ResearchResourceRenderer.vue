<template>
  <div v-if="normalized.length" class="resource-list">
    <article v-for="resource in normalized" :id="`resource-${resource.id}`" :key="resource.id" class="resource-card">
      <header class="resource-head">
        <div>
          <span class="resource-type">{{ typeLabel(resource.type) }}</span>
          <h4>{{ resource.title }}</h4>
        </div>
        <button type="button" class="resource-open" title="在资源侧栏查看" @click="$emit('select', resource)">查看</button>
      </header>
      <figure v-if="resource.type === 'image'" class="resource-image">
        <a :href="safeUrl(resource.image?.url)" target="_blank" rel="noopener noreferrer">
          <img :src="safeUrl(resource.image?.url)" :alt="resource.image?.alt || resource.title" loading="lazy" />
        </a>
        <figcaption v-if="resource.caption || resource.image?.name">{{ resource.caption || resource.image?.name }}</figcaption>
      </figure>
      <ResearchChart v-else-if="resource.type === 'chart'" :resource="resource" />
      <ResearchTable v-else-if="resource.type === 'table'" :resource="resource" />
      <blockquote v-else-if="resource.type === 'citation'" class="resource-citation">
        <p v-if="resource.citation?.evidence">“{{ resource.citation.evidence }}”</p>
        <footer>{{ resource.citation?.author }} {{ resource.citation?.year }}</footer>
      </blockquote>
      <a v-else-if="resource.type === 'file'" class="resource-file" :href="safeUrl(resource.file?.url)" target="_blank" rel="noopener noreferrer">
        <strong>{{ resource.file?.name || resource.title }}</strong><span>打开文件</span>
      </a>
      <div v-if="resource.sourceRefs?.length" class="resource-sources">
        <span v-for="(source, index) in resource.sourceRefs" :key="`${source.type}-${source.id}-${index}`" :title="source.evidence || source.label">
          {{ source.label }}<template v-if="source.page"> · 第 {{ source.page }} 页</template>
        </span>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ResearchChart from './ResearchChart.vue'
import ResearchTable from './ResearchTable.vue'
import { RESOURCE_TYPES, normalizeResource } from '../composables/useResearchResources.js'

const props = defineProps({ resources: { type: Array, default: () => [] } })
defineEmits(['select'])
const normalized = computed(() => props.resources.map(normalizeResource).filter(Boolean))
function typeLabel(type) { return RESOURCE_TYPES.find(item => item.value === type)?.label || '资源' }
function safeUrl(value) {
  try {
    const url = new URL(String(value || ''), window.location.origin)
    if (url.protocol === 'http:' || url.protocol === 'https:') return url.href
  } catch {}
  return '#'
}
</script>

<style scoped>
.resource-list { display: grid; gap: 10px; margin-top: 10px; }
.resource-card { border: 1px solid #e2e8e2; background: #fff; padding: 12px; min-width: 0; }
.resource-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.resource-type { color: #526e5a; font-size: 10px; letter-spacing: .04em; }
.resource-head h4 { margin: 4px 0 10px; font-size: 13px; font-weight: 650; color: #243229; }
.resource-open { border: 0; background: #f0f5f0; color: #526e5a; padding: 4px 8px; font-size: 11px; cursor: pointer; }
.resource-image { margin: 0; text-align: center; }
.resource-image img { display: block; max-width: 100%; max-height: 360px; margin: 0 auto; object-fit: contain; background: #f7f9f7; }
.resource-image figcaption { padding-top: 6px; color: #758078; font-size: 11px; text-align: left; }
.resource-citation { margin: 0; border-left: 3px solid #a9bbaa; padding: 4px 10px; color: #536057; font-size: 12px; }
.resource-citation p { margin: 0 0 6px; }
.resource-citation footer { color: #849087; font-size: 11px; }
.resource-file { display: flex; justify-content: space-between; gap: 10px; color: #526e5a; text-decoration: none; font-size: 12px; }
.resource-file span { color: #849087; }
.resource-sources { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.resource-sources span { background: #f4f7f4; color: #68776b; padding: 3px 6px; font-size: 10px; }
</style>
