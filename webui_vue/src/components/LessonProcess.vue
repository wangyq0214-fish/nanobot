<template>
  <div class="section-process">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-for="(phase, pi) in section.phases" :key="pi" class="process-phase">
      <h3 class="phase-title">{{ phase.name }}<span class="phase-duration" v-if="phase.duration">（{{ phase.duration }}）</span></h3>
      <div v-for="(step, si) in phase.steps" :key="si" class="process-step">
        <h4 class="step-name">{{ step.name }}<span class="step-duration" v-if="step.duration">（{{ step.duration }}）</span></h4>
        <SectionItem :sections="step.sections" />
      </div>
    </div>
  </div>
</template>

<script setup>
import SectionItem from './SectionItem.vue'

defineProps({ section: { type: Object, required: true } })
</script>

<style scoped>
.phase-title { margin: 24px 0 12px; }
.phase-duration { font-weight: 400; font-size: 0.85rem; color: var(--text-muted); }
.step-name { margin: 16px 0 8px; color: var(--text-secondary); }
.step-duration { font-weight: 400; font-size: 0.80rem; color: var(--text-muted); }
</style>
