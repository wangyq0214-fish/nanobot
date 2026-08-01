<template>
  <aside class="resource-sidebar" :class="{ open }">
    <header class="sidebar-head">
      <div><span class="eyebrow">RESEARCH OUTPUT</span><h3>研究资源</h3></div>
      <button type="button" title="关闭资源栏" @click="$emit('close')">×</button>
    </header>
    <nav class="resource-tabs" aria-label="资源类型">
      <button v-for="tab in tabs" :key="tab.value" type="button" :class="{ active: filter === tab.value }" @click="filter = tab.value">{{ tab.label }}<span>{{ count(tab.value) }}</span></button>
    </nav>
    <div class="sidebar-content">
      <ResearchResourceRenderer :resources="filtered" @select="scrollToResource" />
      <p v-if="!filtered.length" class="empty">当前对话还没有结构化资源</p>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import ResearchResourceRenderer from './ResearchResourceRenderer.vue'
import { RESOURCE_TYPES } from '../composables/useResearchResources.js'

const props = defineProps({ open: Boolean, resources: { type: Array, default: () => [] } })
defineEmits(['close'])
const filter = ref('all')
const tabs = [{ value: 'all', label: '全部' }, ...RESOURCE_TYPES]
const filtered = computed(() => filter.value === 'all' ? props.resources : props.resources.filter(item => item.type === filter.value))
function count(type) { return type === 'all' ? props.resources.length : props.resources.filter(item => item.type === type).length }
function scrollToResource(resource) {
  document.getElementById(`resource-${resource.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<style scoped>
.resource-sidebar { width: 320px; flex: 0 0 320px; min-height: 0; border-left: 1px solid #e3e9e3; background: #fbfcfb; display: none; flex-direction: column; }
.resource-sidebar.open { display: flex; }
.sidebar-head { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 18px 12px; border-bottom: 1px solid #e7ece7; }
.sidebar-head h3 { margin: 5px 0 0; color: #243229; font-size: 18px; }
.sidebar-head button { border: 0; background: transparent; color: #68776b; font-size: 24px; line-height: 1; cursor: pointer; }
.eyebrow { color: #7a8a7c; font-size: 9px; letter-spacing: .12em; }
.resource-tabs { display: flex; gap: 3px; overflow-x: auto; padding: 10px 12px; border-bottom: 1px solid #e7ece7; }
.resource-tabs button { border: 0; background: transparent; color: #7a887c; padding: 5px 7px; white-space: nowrap; font-size: 11px; cursor: pointer; }
.resource-tabs button.active { background: #e6efe7; color: #35583e; }
.resource-tabs span { margin-left: 3px; opacity: .65; }
.sidebar-content { flex: 1; min-height: 0; overflow-y: auto; padding: 12px; }
.empty { color: #849087; font-size: 12px; text-align: center; padding: 45px 14px; }
@media (max-width: 980px) {
  .resource-sidebar { position: fixed; inset: 0 0 0 auto; z-index: 30; max-width: min(360px, 92vw); transform: translateX(105%); display: flex; box-shadow: -12px 0 30px rgba(30, 50, 35, .12); transition: transform .2s ease; }
  .resource-sidebar.open { transform: translateX(0); }
}
</style>
