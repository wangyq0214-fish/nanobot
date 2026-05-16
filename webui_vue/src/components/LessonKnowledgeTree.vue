<template>
  <div class="section-knowledge-tree">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-if="section.content" class="knowledge-tree">
      <div class="tree-root">
        <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7"/><path d="M10 6v4l3 2"/></svg>
        {{ section.content.root }}
      </div>
      <div class="tree-branches">
        <div class="tree-branch" v-for="(card, ci) in section.content.cards" :key="ci">
          <div class="tree-card">
            <div class="tree-card-title">
              <svg viewBox="0 0 20 20"><circle cx="7" cy="7" r="2"/><circle cx="13" cy="13" r="2"/><path d="M8.5 8l3 3"/></svg>
              {{ card.title }}
            </div>
            <div class="tree-card-body">
              <div class="tcl" v-for="(line, li) in card.lines" :key="li">{{ line }}</div>
            </div>
            <div class="tree-card-sub">{{ card.sub }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ section: { type: Object, required: true } })
</script>
