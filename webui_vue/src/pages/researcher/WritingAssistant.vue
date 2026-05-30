<template>
<div class="app">
  <ResearcherNav active-tab="writing-assistant">
    <template #nav-extra>
      <span class="word-count">字数：{{ wordCount.toLocaleString() }}</span>
    </template>
  </ResearcherNav>

  <div class="workspace">
    <!-- Left sidebar -->
    <div class="sidebar">
      <div class="sidebar-hd"><i></i>
        <select class="sidebar-tab-select" v-model="currentTab" @change="switchTab(currentTab)">
          <option v-for="t in tabs" :key="t.key" :value="t.key">{{ t.icon }} {{ t.label }}</option>
        </select>
      </div>
      <ul class="sidebar-list" @click="onSidebarClick">
        <li
          v-for="(item, i) in sidebarItems"
          :key="i"
          class="sidebar-item"
          :class="{ active: activeSidebarIdx === i }"
          :data-idx="i"
        >
          <span class="ico">{{ item.icon }}</span>{{ item.label }}<span v-if="item.badge" class="badge-dot" :class="item.badge"></span>
        </li>
      </ul>
    </div>

    <!-- Center editor -->
    <div class="editor-panel">
      <div class="editor-toolbar">
        <button title="加粗"><b>B</b></button>
        <button title="斜体"><i>I</i></button>
        <button title="下划线"><u>U</u></button>
        <span class="toolbar-divider"></span>
        <button title="标题2">H2</button>
        <button title="标题3">H3</button>
        <span class="toolbar-divider"></span>
        <button title="插入引用">❝</button>
        <button title="插入图表">📊</button>
        <button title="插入公式">∑</button>
        <span class="toolbar-divider"></span>
        <button title="撤销">↩</button>
        <button title="重做">↪</button>
      </div>
      <div
        class="editor-content"
        ref="editorEl"
        contenteditable="true"
        @input="updateWordCount"
        v-html="editorContent"
      ></div>
    </div>

    <!-- Right AI panel -->
    <div class="ai-panel">
      <div class="panel-hd"><i></i>{{ panelTitle }}</div>
      <div class="panel-scroll" v-html="panelContent"></div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import ResearcherNav from '../../components/ResearcherNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}
const isDark = ref(false)
const currentTab = ref('review')
const activeSidebarIdx = ref(0)
const wordCount = ref(1286)
const editorEl = ref(null)

const tabs = [
  { key: 'review', icon: '📖', label: '文献综述生成' },
  { key: 'outline', icon: '🏗️', label: '论文框架搭建' },
  { key: 'polish', icon: '✨', label: '语言润色' },
  { key: 'format', icon: '✅', label: '格式规范检查' },
]

const editorContent = `<h2>苹果砧木耐盐基因MdNHX1的CRISPR/Cas9编辑及功能验证</h2>
<h3>摘要</h3>
<p>土壤盐渍化是限制苹果产业发展的<span class="hl-suggest" title="建议改为：关键非生物胁迫因子之一">重要因素</span>。本研究以苹果砧木'M9-T337'为材料，利用CRISPR/Cas9技术对<span class="hl-suggest" title="建议补充基因全称及登录号">MdNHX1基因</span>进行定向敲除，获得纯合突变体株系3个。在200 mM NaCl胁迫处理下，突变体植株的叶绿素含量<span class="hl-error" title="语法：'显著低于' 比 '显著的低于' 更规范">显著的低于</span>野生型，丙二醛（MDA）含量升高42.6%，表明MdNHX1在苹果耐盐性中发挥关键作用。</p>
<h3>引言</h3>
<p>苹果（<i>Malus domestica</i> Borkh.）是全球栽培面积最广的果树之一。然而，随着全球气候变化和灌溉农业的扩展，<span class="hl-suggest" title="建议补充具体数据支撑">土壤盐渍化问题日益严峻</span>，已成为制约苹果产量和品质的关键因素<span class="cite-ref">[1]</span>。据统计，我国环渤海湾和西北黄土高原两大苹果主产区均有不同程度的盐碱化分布<span class="cite-ref">[2]</span>。</p>
<p>Na⁺/H⁺反向转运蛋白（NHX）在植物离子稳态和耐盐性调控中具有核心功能。在拟南芥中，AtNHX1通过将Na⁺区隔化至液泡来降低细胞质离子毒性<span class="cite-ref">[3]</span>。<span class="hl-suggest" title="建议增加：然而，苹果MdNHX1的功能尚未通过反向遗传学手段验证">目前关于苹果NHX基因的研究仍较为有限</span>。</p>
<p>CRISPR/Cas9基因编辑技术为果树功能基因组学研究提供了高效工具<span class="cite-ref">[4]</span>。本研究拟通过构建MdNHX1的CRISPR敲除载体，转化苹果砧木，<span class="hl-error" title="表达冗余：'验证其在耐盐性中的功能' 与后文重复">验证该基因在耐盐性中的功能</span>，为苹果耐盐分子育种提供理论依据和种质材料。</p>`

const sidebarData = {
  review: {
    title: '文献资料库',
    items: [
      { icon: '📄', label: '已导入文献 (15)' },
      { icon: '🔍', label: '检索结果 (48)' },
      { icon: '⭐', label: '已标注重要 (6)' },
      { icon: '📁', label: '基因编辑专题' },
      { icon: '📁', label: '耐盐性研究' },
    ]
  },
  outline: {
    title: '推荐框架',
    items: [
      { icon: '📋', label: 'IMRaD标准结构' },
      { icon: '📝', label: '综述型结构' },
      { icon: '🎓', label: '学位论文结构' },
      { icon: '📊', label: '简报/快报结构' },
    ]
  },
  polish: {
    title: '章节导航',
    items: [
      { icon: '📋', label: '摘要', badge: 'warn' },
      { icon: '📝', label: '引言', badge: 'err' },
      { icon: '📚', label: '文献综述' },
    ]
  },
  format: {
    title: '检查项列表',
    items: [
      { icon: '⚠️', label: '引用格式 (3处)', badge: 'err' },
      { icon: '✅', label: '字体段落' },
      { icon: '⚠️', label: '图表编号', badge: 'warn' },
      { icon: '✅', label: '页边距行距' },
      { icon: '✅', label: '作者信息' },
    ]
  }
}

const panelData = {
  review: {
    title: '🤖 综述生成助手',
    content: `<div class="panel-section">
      <div class="panel-label">🔍 主题检索</div>
      <div class="ai-input-row"><input type="text" placeholder="输入研究主题…" value="苹果 CRISPR 耐盐"><button>检索</button></div>
    </div>
    <div class="panel-section">
      <div class="panel-label">📄 AI综述摘要</div>
      <div class="suggestion-item"><span class="sug-tag structure">AI生成</span> 基于48篇文献，CRISPR基因编辑在果树耐盐性改良中的应用正快速增长。MdNHX1、MdSOS1等基因的功能验证成为热点。点击下方按钮生成结构化综述初稿。</div>
      <button class="btn-generate">📝 生成综述初稿</button>
    </div>
    <div class="panel-section">
      <div class="panel-label">📚 核心文献 (4篇)</div>
      <div class="cite-mini"><span class="cite-num">1</span> Zhang et al., Plant Physiol. 2023</div>
      <div class="cite-mini"><span class="cite-num">2</span> Li & Wang, Precision Agric. 2024</div>
      <div class="cite-mini"><span class="cite-num">3</span> Apse et al., Science, 1999</div>
      <div class="cite-mini"><span class="cite-num">4</span> Munns & Tester, Annu. Rev. 2008</div>
    </div>`
  },
  outline: {
    title: '🧱 框架搭建助手',
    content: `<div class="panel-section">
      <div class="panel-label">📋 当前大纲 (IMRaD)</div>
      <div style="font-size:0.64rem;color:var(--text2);line-height:1.8;">
        ✅ 摘要 (已有草稿)<br>
        ⚠️ 引言 (需补充背景)<br>
        ✅ 文献综述<br>
        ⚠️ 材料与方法 (待完善)<br>
        — 结果与分析<br>
        — 讨论<br>
        — 结论
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">💡 章节写作提示</div>
      <div class="suggestion-item"><span class="sug-tag structure">引言</span> 建议先交代盐渍化问题背景，再引出MdNHX1研究空白，最后明确研究目的。</div>
    </div>`
  },
  polish: {
    title: '✨ 语言润色助手',
    content: `<div class="panel-section">
      <div class="panel-label">💡 润色建议 (4条)</div>
      <div class="suggestion-item"><span class="sug-tag grammar">语法</span> "显著的低于" → <strong>"显著低于"</strong></div>
      <div class="suggestion-item"><span class="sug-tag style">表达</span> "重要因素" → <strong>"关键非生物胁迫因子之一"</strong></div>
      <div class="suggestion-item"><span class="sug-tag style">用词</span> "较为有限" → <strong>"尚未通过反向遗传学验证"</strong></div>
      <div class="suggestion-item"><span class="sug-tag structure">结构</span> 引言末段建议补充具体研究目标与假设。</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">✏️ 快捷指令</div>
      <div class="ai-input-row"><input type="text" placeholder="输入润色指令…"><button>执行</button></div>
      <div class="quick-tags">
        <span class="quick-tag">✨ 润色整段</span>
        <span class="quick-tag">📖 学术化改写</span>
        <span class="quick-tag">✂️ 精简表达</span>
        <span class="quick-tag">📝 扩展论述</span>
      </div>
    </div>`
  },
  format: {
    title: '✅ 格式检查助手',
    content: `<div class="panel-section">
      <div class="panel-label">⚠️ 格式问题 (3条)</div>
      <div class="suggestion-item"><span class="sug-tag grammar">引用</span> [1] 缺少DOI号，建议补充</div>
      <div class="suggestion-item"><span class="sug-tag style">引用</span> [2] 期刊名需使用标准缩写</div>
      <div class="suggestion-item"><span class="sug-tag grammar">引用</span> [4] 作者列表格式不一致</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">📏 规范检查概览</div>
      <div style="font-size:0.64rem;color:var(--text2);line-height:1.8;">
        ✅ 字体：宋体/Times New Roman<br>
        ✅ 字号：小四/12pt<br>
        ✅ 行距：1.5倍<br>
        ⚠️ 参考文献格式：GB/T 7714<br>
        ✅ 页边距：上下2.54cm 左右3.17cm
      </div>
    </div>`
  }
}

const sidebarTitle = computed(() => sidebarData[currentTab.value].title)
const sidebarItems = computed(() => sidebarData[currentTab.value].items)
const panelTitle = computed(() => panelData[currentTab.value].title)
const panelContent = computed(() => panelData[currentTab.value].content)

function switchTab(tab) {
  currentTab.value = tab
  activeSidebarIdx.value = 0
}

function onSidebarClick(e) {
  const item = e.target.closest('.sidebar-item')
  if (item && item.dataset.idx !== undefined) {
    activeSidebarIdx.value = parseInt(item.dataset.idx)
  }
}

function updateWordCount() {
  if (editorEl.value) {
    const text = editorEl.value.innerText || editorEl.value.textContent || ''
    wordCount.value = text.replace(/\s/g, '').length
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

onMounted(() => {
  updateWordCount()
})
</script>

<style>
:root {
  --bg: #f2f1f6;
  --card: rgba(255, 255, 255, 0.72);
  --card-solid: #ffffff;
  --nav-bg: rgba(255, 255, 255, 0.92);
  --accent: #5a4cd8;
  --accent-light: rgba(90, 76, 216, 0.08);
  --accent-glow: rgba(90, 76, 216, 0.20);
  --border: rgba(90, 76, 216, 0.38);
  --section-border: #6b5fd5;
  --text2: #4a4658;
  --text3: #7a7688;
  --divider: rgba(90, 76, 216, 0.12);
  --radius: 18px;
  --radius-sm: 8px;
  --tag-bg: rgba(90, 76, 216, 0.05);
  --tag-border: rgba(90, 76, 216, 0.55);
  --editor-bg: #ffffff;
  --highlight-suggest: rgba(232, 168, 40, 0.15);
  --highlight-error: rgba(224, 85, 85, 0.10);
  --highlight-border-suggest: #c28a2a;
  --highlight-border-error: #b84a4a;
  --scrollbar-thumb: rgba(90, 76, 216, 0.28);
  --ai-card-bg: rgba(90, 76, 216, 0.03);
  --panel-section-radius: 0px;
}
body.dark {
  --bg: #06050f;
  --card: rgba(14, 13, 26, 0.60);
  --card-solid: #0f0d1a;
  --nav-bg: rgba(8, 7, 18, 0.92);
  --accent: #8B70FF;
  --accent-light: rgba(139, 112, 255, 0.12);
  --accent-glow: rgba(139, 112, 255, 0.25);
  --border: rgba(139, 112, 255, 0.40);
  --section-border: #9a84ff;
  --text: #e4e1f6;
  --text2: #a8a3c0;
  --text3: #6d6a88;
  --divider: rgba(139, 112, 255, 0.14);
  --tag-bg: rgba(139, 112, 255, 0.08);
  --tag-border: rgba(139, 112, 255, 0.58);
  --editor-bg: #0f0d1e;
  --highlight-suggest: rgba(232, 168, 40, 0.18);
  --highlight-error: rgba(224, 85, 85, 0.15);
  --highlight-border-suggest: #b07828;
  --highlight-border-error: #aa4040;
  --scrollbar-thumb: rgba(139, 112, 255, 0.36);
  --ai-card-bg: rgba(139, 112, 255, 0.05);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg); color: var(--text); height: 100vh; overflow: hidden;
  transition: 0.3s; letter-spacing: 0.01em;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 8px; }

.app { display: flex; flex-direction: column; height: 100vh; max-width: 1600px; margin: 0 auto; padding: 10px 14px; gap: 8px; }

.top-nav {
  flex-shrink: 0; height: 48px; background: var(--nav-bg); backdrop-filter: blur(18px);
  border: 2px solid var(--accent); border-radius: var(--radius);
  padding: 0 16px; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 0 0 1px var(--accent-light), 0 0 18px var(--accent-glow); gap: 10px;
}
.nav-left { display: flex; align-items: center; gap: 16px; }
.nav-logo {
  font-family: 'Playfair Display', serif; font-style: italic; font-size: 1rem; font-weight: 700;
  color: var(--accent); display: flex; align-items: center; gap: 7px; flex-shrink: 0;
}
.nav-logo .dot { width: 7px; height: 7px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 14px var(--accent-glow); animation: dotPulse 2.4s infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:0.5} }
.nav-right { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.nav-center { display: flex; align-items: center; gap: 4px; }
.nav-tab {
  padding: 6px 14px; border-radius: 14px; font-size: 0.64rem; font-weight: 500;
  color: var(--text2); cursor: pointer; transition: all 0.2s; border: 1.5px solid transparent;
}
.nav-tab:hover { color: var(--text); background: var(--accent-light); }
.nav-tab.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow);
}

.tab-nav { display: flex; gap: 2px; flex-wrap: wrap; flex-shrink: 1; overflow-x: auto; }
.tab-btn {
  padding: 7px 16px; border: 1.5px solid transparent; background: transparent;
  color: var(--text2); font-weight: 500; font-size: 0.66rem; cursor: pointer;
  transition: 0.2s; border-radius: 20px; letter-spacing: 0.03em; white-space: nowrap;
  display: flex; align-items: center; gap: 5px; font-family: inherit;
}
.tab-btn .ico { font-size: 0.85rem; }
.tab-btn.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  font-weight: 600; box-shadow: inset 0 0 0 1px var(--accent-glow), 0 0 12px var(--accent-glow);
}
.tab-btn:hover:not(.active) { background: var(--accent-light); color: var(--accent); }
.icon-btn {
  width: 32px; height: 32px; border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; color: var(--text2); font-size: 0.85rem; transition: 0.2s;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.icon-btn svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 1.8; }
.icon-btn:hover { color: var(--accent); border-color: var(--accent); box-shadow: 0 0 14px var(--accent-glow); }
.word-count { font-size: 0.6rem; color: var(--text3); white-space: nowrap; font-weight: 500; }

.workspace { flex: 1; min-height: 0; display: flex; gap: 8px; }

.sidebar {
  width: 220px; min-width: 180px; flex-shrink: 0;
  background: var(--card); backdrop-filter: blur(12px);
  border: 2px solid var(--accent); border-radius: var(--radius);
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 0 0 1px var(--accent-light); transition: box-shadow 0.3s;
}
.sidebar:hover { box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.sidebar-hd {
  padding: 12px 14px; font-weight: 700; font-size: 0.64rem; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--accent); border-bottom: 1px solid var(--divider);
  display: flex; align-items: center; gap: 6px; flex-shrink: 0; background: var(--card-solid);
}
.sidebar-hd i { width: 4px; height: 14px; background: linear-gradient(180deg, var(--accent), #4a3cc0); border-radius: 2px; box-shadow: 0 0 6px var(--accent-glow); flex-shrink: 0; }
.sidebar-tab-select {
  flex: 1; padding: 6px 8px; border: 1.5px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.62rem; font-weight: 600; border-radius: 8px;
  font-family: inherit; cursor: pointer; outline: none; transition: 0.2s;
}
.sidebar-tab-select:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-light); }
.sidebar-list { list-style: none; padding: 4px 6px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 1px; }
.sidebar-item {
  padding: 9px 10px; border-radius: 0; cursor: pointer; font-size: 0.68rem; color: var(--text2);
  transition: all 0.15s; display: flex; align-items: center; gap: 8px; font-weight: 500;
  border-left: 2px solid transparent; background: transparent;
}
.sidebar-item .ico { font-size: 0.85rem; flex-shrink: 0; }
.sidebar-item .badge-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-left: auto; }
.badge-dot.warn { background: #c28a2a; }
.badge-dot.err { background: #b84a4a; }
.sidebar-item:hover { background: var(--accent-light); color: var(--accent); border-left-color: var(--accent); }
.sidebar-item.active { background: var(--accent-light); color: var(--accent); font-weight: 600; border-left-color: var(--accent); border-left-width: 2px; }

.editor-panel {
  flex: 1; min-width: 0; background: var(--card); backdrop-filter: blur(12px);
  border: 2px solid var(--accent); border-radius: var(--radius); display: flex; flex-direction: column;
  overflow: hidden; box-shadow: 0 0 0 1px var(--accent-light); transition: box-shadow 0.3s;
}
.editor-panel:hover { box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.editor-toolbar {
  flex-shrink: 0; display: flex; align-items: center; gap: 2px; padding: 6px 12px;
  border-bottom: 1px solid var(--divider); flex-wrap: wrap; background: var(--card-solid);
}
.editor-toolbar button {
  width: 28px; height: 28px; border: 1px solid transparent; background: transparent;
  border-radius: 4px; cursor: pointer; color: var(--text2); font-size: 0.78rem;
  transition: 0.15s; display: flex; align-items: center; justify-content: center; font-family: inherit;
}
.editor-toolbar button:hover { background: var(--accent-light); color: var(--accent); }
.toolbar-divider { width: 1px; height: 16px; background: var(--divider); margin: 0 4px; flex-shrink: 0; }
.editor-content {
  flex: 1; min-height: 0; overflow-y: auto; padding: 24px 28px; font-size: 0.84rem;
  line-height: 1.95; color: var(--text); outline: none;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', serif;
  letter-spacing: 0.01em; background: var(--editor-bg); transition: background 0.3s;
}
.editor-content h2 { font-size: 1.25rem; margin: 1em 0 0.4em; color: var(--accent); font-weight: 700; text-align: center; }
.editor-content h3 { font-size: 0.95rem; margin: 0.8em 0 0.3em; font-weight: 600; color: var(--text); }
.editor-content p { margin: 0.4em 0; text-indent: 1.6em; }
.editor-content .hl-suggest {
  background: var(--highlight-suggest); border-bottom: 2px dotted var(--highlight-border-suggest);
  cursor: pointer; padding: 0 2px; border-radius: 2px; transition: 0.15s;
}
.editor-content .hl-suggest:hover { background: rgba(232, 168, 40, 0.28); }
.editor-content .hl-error {
  background: var(--highlight-error); border-bottom: 2px dotted var(--highlight-border-error);
  cursor: pointer; padding: 0 2px; border-radius: 2px; transition: 0.15s;
}
.editor-content .hl-error:hover { background: rgba(224, 85, 85, 0.22); }
.editor-content .cite-ref { color: var(--accent); font-weight: 600; font-size: 0.75rem; cursor: pointer; }

.ai-panel {
  width: 270px; min-width: 220px; flex-shrink: 0;
  background: var(--card); backdrop-filter: blur(12px);
  border: 2px solid var(--accent); border-radius: var(--radius);
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 0 0 1px var(--accent-light); transition: box-shadow 0.3s;
}
.ai-panel:hover { box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.panel-hd {
  padding: 12px 14px; font-weight: 700; font-size: 0.64rem; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--accent); border-bottom: 1px solid var(--divider);
  display: flex; align-items: center; gap: 6px; flex-shrink: 0; background: var(--card-solid);
}
.panel-hd i { width: 4px; height: 14px; background: linear-gradient(180deg, var(--accent), #4a3cc0); border-radius: 2px; box-shadow: 0 0 6px var(--accent-glow); }
.panel-scroll { flex: 1; overflow-y: auto; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
.panel-section {
  background: var(--ai-card-bg); border: 2px solid var(--section-border);
  border-radius: var(--panel-section-radius); padding: 12px 14px; flex-shrink: 0;
}
.panel-label {
  font-size: 0.58rem; font-weight: 700; color: var(--accent); text-transform: uppercase;
  letter-spacing: 0.04em; margin-bottom: 6px; display: flex; align-items: center; gap: 5px;
  border-bottom: 1px solid var(--divider); padding-bottom: 4px;
}
.suggestion-item {
  background: var(--card); border: 1px solid var(--border); border-radius: 0;
  padding: 8px 10px; font-size: 0.66rem; color: var(--text2); line-height: 1.5;
  cursor: pointer; transition: 0.15s; margin-bottom: 4px;
}
.suggestion-item:last-child { margin-bottom: 0; }
.suggestion-item:hover { border-color: var(--accent); background: var(--accent-light); box-shadow: 0 2px 10px var(--accent-glow); }
.suggestion-item .sug-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.55rem; font-weight: 600; margin-right: 4px; }
.sug-tag.grammar { background: rgba(184, 74, 74, 0.15); color: #b84a4a; }
body.dark .sug-tag.grammar { background: rgba(184, 74, 74, 0.25); color: #e07070; }
.sug-tag.style { background: rgba(194, 138, 42, 0.15); color: #9e6a1a; }
body.dark .sug-tag.style { background: rgba(194, 138, 42, 0.25); color: #d4952a; }
.sug-tag.structure { background: rgba(90, 76, 216, 0.12); color: var(--accent); }
.cite-mini {
  font-size: 0.64rem; color: var(--text2); padding: 5px 8px; border-radius: 0;
  cursor: pointer; transition: 0.15s; display: flex; align-items: center; gap: 6px;
  border-bottom: 1px solid var(--divider);
}
.cite-mini:last-child { border-bottom: none; }
.cite-mini:hover { background: var(--accent-light); }
.cite-num {
  width: 20px; height: 20px; background: var(--accent-light); color: var(--accent);
  font-weight: 700; font-size: 0.55rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.ai-input-row { display: flex; gap: 5px; margin-top: 6px; }
.ai-input-row input {
  flex: 1; padding: 8px 12px; border: 1.5px solid var(--border); border-radius: 0;
  font-size: 0.64rem; background: var(--editor-bg); color: var(--text); font-family: inherit; outline: none; transition: 0.2s;
}
.ai-input-row input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-light); }
.ai-input-row button {
  padding: 8px 14px; background: var(--accent); color: #fff; border: none; border-radius: 0;
  font-weight: 600; font-size: 0.64rem; cursor: pointer; white-space: nowrap; transition: 0.2s; letter-spacing: 0.02em;
}
.ai-input-row button:hover { opacity: 0.9; box-shadow: 0 4px 12px var(--accent-glow); }
.quick-tags { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
.quick-tag {
  font-size: 0.58rem; padding: 6px 8px; background: var(--tag-bg); border: 1px solid var(--tag-border);
  border-radius: 0; cursor: pointer; color: var(--accent); transition: 0.15s;
  white-space: nowrap; font-weight: 500; text-align: center;
}
.quick-tag:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-generate {
  width: 100%; padding: 10px; background: var(--accent); color: #fff; border: none;
  border-radius: 0; font-weight: 600; font-size: 0.66rem; cursor: pointer; margin-top: 8px;
  transition: 0.2s; letter-spacing: 0.02em;
}
.btn-generate:hover { opacity: 0.9; box-shadow: 0 4px 12px var(--accent-glow); }

@media (max-width: 1000px) {
  .workspace { flex-direction: column; }
  .sidebar { width: 100%; min-width: 0; max-height: 130px; }
  .ai-panel { width: 100%; min-width: 0; max-height: 220px; }
  .editor-content { padding: 16px 18px; font-size: 0.78rem; }
  .tab-btn { padding: 6px 10px; font-size: 0.6rem; }
  .top-nav { flex-wrap: wrap; height: auto; min-height: 44px; padding: 8px 12px; gap: 6px; }
}
</style>
