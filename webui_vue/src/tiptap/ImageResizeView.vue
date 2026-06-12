<template>
  <NodeViewWrapper
    class="image-resize-wrap"
    :class="{ 'is-selected': selected }"
    draggable="true"
    data-drag-handle
  >
    <div
      ref="containerEl"
      class="image-resize-box"
      :style="boxStyle"
    >
      <img
        ref="imgEl"
        :src="node.attrs.src"
        :alt="node.attrs.alt || ''"
        @load="onLoad"
        draggable="false"
        :style="imgStyle"
      />
      <template v-if="selected">
        <div class="handle nw" @pointerdown.stop.prevent="startResize('nw', $event)" />
        <div class="handle ne" @pointerdown.stop.prevent="startResize('ne', $event)" />
        <div class="handle sw" @pointerdown.stop.prevent="startResize('sw', $event)" />
        <div class="handle se" @pointerdown.stop.prevent="startResize('se', $event)" />
        <div class="handle n"  @pointerdown.stop.prevent="startResize('n',  $event)" />
        <div class="handle s"  @pointerdown.stop.prevent="startResize('s',  $event)" />
        <div class="handle w"  @pointerdown.stop.prevent="startResize('w',  $event)" />
        <div class="handle e"  @pointerdown.stop.prevent="startResize('e',  $event)" />
        <div class="img-delete-btn" @click.stop.prevent="deleteNode" title="删除图片">✕</div>
      </template>
    </div>
  </NodeViewWrapper>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { NodeViewWrapper } from '@tiptap/vue-3'

const props = defineProps({
  node: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  updateAttributes: { type: Function, required: true },
  deleteNode: { type: Function, required: true },
})

const imgEl = ref(null)
const containerEl = ref(null)

const w = ref(props.node.attrs.width || 0)
const h = ref(props.node.attrs.height || 0)

const boxStyle = computed(() => ({
  width: w.value + 'px',
  height: h.value + 'px',
  display: 'inline-block',
  position: 'relative',
  lineHeight: 0,
}))

const imgStyle = computed(() => ({
  width: '100%',
  height: '100%',
  objectFit: 'fill',
  borderRadius: '6px',
  display: 'block',
  pointerEvents: 'none',
}))

watch(() => props.node.attrs.width, (v) => { if (v) w.value = v })
watch(() => props.node.attrs.height, (v) => { if (v) h.value = v })

onMounted(() => {
  if (imgEl.value?.complete) onLoad()
})

function onLoad() {
  if (!imgEl.value || w.value) return
  const nw = imgEl.value.naturalWidth
  const nh = imgEl.value.naturalHeight
  const maxW = 640
  if (nw > maxW) {
    w.value = maxW
    h.value = Math.round(nh * maxW / nw)
  } else {
    w.value = nw
    h.value = nh
  }
  props.updateAttributes({ width: w.value, height: h.value })
}

function startResize(handle, event) {
  const startX = event.clientX
  const startY = event.clientY
  const startW = w.value
  const startH = h.value
  const ratio = startW / startH

  const isCorner = handle.length === 2
  const isHorizontal = handle === 'w' || handle === 'e'
  const isVertical = handle === 'n' || handle === 's'

  function onMove(e) {
    const dx = e.clientX - startX
    const dy = e.clientY - startY

    if (isCorner) {
      // Corner: free stretch, no ratio lock
      let newW, newH
      if (handle === 'se') {
        newW = startW + dx
        newH = startH + dy
      } else if (handle === 'sw') {
        newW = startW - dx
        newH = startH + dy
      } else if (handle === 'ne') {
        newW = startW + dx
        newH = startH - dy
      } else { // nw
        newW = startW - dx
        newH = startH - dy
      }
      w.value = Math.max(40, newW)
      h.value = Math.max(40, newH)
    } else if (isHorizontal) {
      const newW = handle === 'e' ? startW + dx * 2 : startW - dx * 2
      w.value = Math.max(40, newW)
    } else if (isVertical) {
      const newH = handle === 's' ? startH + dy * 2 : startH - dy * 2
      h.value = Math.max(40, newH)
    }
  }

  function onUp() {
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    props.updateAttributes({ width: w.value, height: h.value })
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}
</script>
