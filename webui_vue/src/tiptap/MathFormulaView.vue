<template>
  <NodeViewWrapper
    as="span"
    class="math-inline"
    :class="{ 'math-block-host': node.attrs.displayMode }"
    :data-formula="node.attrs.formula"
  >
    <span ref="mathEl" class="math-render"></span>
  </NodeViewWrapper>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { NodeViewWrapper } from '@tiptap/vue-3'
import katex from 'katex'

const props = defineProps({
  node: { type: Object, required: true },
  updateAttributes: { type: Function, required: true },
})

const mathEl = ref(null)

function renderMath() {
  if (!mathEl.value) return
  try {
    katex.render(props.node.attrs.formula, mathEl.value, {
      throwOnError: false,
      displayMode: props.node.attrs.displayMode,
    })
  } catch {
    mathEl.value.textContent = props.node.attrs.formula
  }
}

onMounted(renderMath)
watch(() => props.node.attrs.formula, renderMath)
</script>
