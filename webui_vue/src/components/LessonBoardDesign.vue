<template>
  <div class="section-board">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <div v-if="section.content" class="chalkboard">
      <div class="board-frame">
        <div class="board-inner">
          <div class="board-corner tl"></div>
          <div class="board-corner br"></div>

          <div class="board-title">{{ section.content.mainTitle }}</div>

          <!-- Flow rows -->
          <div v-for="(flow, fi) in section.content.flows" :key="fi" class="board-section">
            <div class="board-section-title">{{ flow.title }}</div>
            <div class="board-flow">
              <template v-for="(item, ii) in flow.items" :key="ii">
                <div class="board-box" :class="{ central: item.highlight }">
                  <div class="board-box-title">{{ item.label }}</div>
                  <ul>
                    <li v-for="(d, di) in item.details" :key="di" :class="{ hl: item.highlight && di === 0 }">{{ d }}</li>
                  </ul>
                </div>
                <div v-if="ii < flow.items.length - 1" class="board-arrow">→</div>
              </template>
            </div>
          </div>

          <!-- Side panels -->
          <div v-if="section.content.sidePanels" class="board-section" style="display:flex;gap:16px;flex-wrap:wrap;">
            <div v-for="(panel, pi) in section.content.sidePanels" :key="pi" style="flex:1;min-width:150px;">
              <div class="board-section-title">{{ panel.title }}</div>
              <div class="board-box" :style="pi === 2 ? 'text-align:center;' : 'text-align:left;'">
                <ul>
                  <li v-for="(item, li) in panel.items" :key="li">{{ item }}</li>
                </ul>
                <template v-if="pi === 0 && panel.note">
                  <div style="text-align:center;margin-top:6px;opacity:0.5;font-size:0.72rem;">{{ panel.note }}</div>
                </template>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div v-if="section.content.footer" class="board-footer">
            <span v-for="(f, fi) in section.content.footer" :key="fi">{{ f }}<template v-if="fi < section.content.footer.length - 1"> | </template></span>
          </div>
          <div class="chalk-dust"></div>
        </div>
      </div>
      <div class="board-tray"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({ section: { type: Object, required: true } })
</script>
