<template>
<div class="app">
  <ResearcherNav active-tab="writing-assistant">
    <template #nav-extra>
      <span class="word-count">字数：{{ wordStats.words.toLocaleString() }}</span>
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
        <button title="加粗" :class="{ active: editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()"><b>B</b></button>
        <button title="斜体" :class="{ active: editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()"><i>I</i></button>
        <button title="下划线" :class="{ active: editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()"><u>U</u></button>
        <span class="toolbar-divider"></span>
        <button title="标题2" :class="{ active: editor?.isActive('heading', { level: 2 }) }" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()">H2</button>
        <button title="标题3" :class="{ active: editor?.isActive('heading', { level: 3 }) }" @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()">H3</button>
        <span class="toolbar-divider"></span>
        <div class="toolbar-dropdown-wrap">
          <button title="插入文献引用" @click.stop="toggleCitePicker">❝</button>
          <div v-if="showCitePicker" class="toolbar-dropdown cite-picker" @click.stop>
            <div class="dropdown-hd">选择文献插入引用</div>
            <div v-if="library.papers.length === 0" class="dropdown-empty">文献库为空，请先添加文献</div>
            <div v-for="(paper, idx) in library.papers.slice(0, 20)" :key="paper.id" class="dropdown-item" @click="insertCitation(idx + 1)">
              <span class="cite-idx">[{{ idx + 1 }}]</span>
              <span class="cite-title">{{ paper.title?.substring(0, 40) }}{{ paper.title?.length > 40 ? '...' : '' }}</span>
            </div>
          </div>
        </div>
        <div class="toolbar-dropdown-wrap">
          <button title="插入图表" @click.stop="toggleFigureMenu">📊</button>
          <div v-if="showFigureMenu" class="toolbar-dropdown figure-menu" @click.stop>
            <div class="dropdown-hd">插入</div>
            <div class="dropdown-item" @click="openImageDialog">🖼️ 插入图片</div>
            <div class="dropdown-item" @click="openTableDialog">📋 插入表格</div>
          </div>
        </div>
        <div class="toolbar-dropdown-wrap">
          <button title="插入公式" @click.stop="toggleFormulaMenu">∑</button>
          <div v-if="showFormulaMenu" class="toolbar-dropdown formula-menu" @click.stop>
            <div class="dropdown-hd">插入公式</div>
            <div class="dropdown-item" @click="insertFormula(false)">∑ 行内公式 (inline)</div>
            <div class="dropdown-item" @click="insertFormula(true)">∑ 独立公式 (display)</div>
          </div>
        </div>
        <span class="toolbar-divider"></span>
        <button title="撤销" :disabled="!editor?.can().undo()" @click="editor?.chain().focus().undo().run()">↩</button>
        <button title="重做" :disabled="!editor?.can().redo()" @click="editor?.chain().focus().redo().run()">↪</button>
      </div>
      <EditorContent class="editor-content" :editor="editor" />
    </div>

    <!-- Right AI panel -->
    <div class="ai-panel">
      <div class="panel-hd"><i></i>{{ panelTitle }}</div>
      <div class="panel-scroll">
        <!-- Library Panel -->
        <template v-if="currentTab === 'library'">
          <div class="panel-section">
            <div class="panel-label">📥 导入文献</div>
            <div class="import-actions">
              <button class="btn-import" @click="importDialogVisible = true">📋 从剪贴板导入</button>
              <button class="btn-export" @click="handleExport('ris')">📤 导出RIS</button>
              <button class="btn-export" @click="handleExport('bibtex')">📤 导出BibTeX</button>
            </div>
          </div>
          <div class="panel-section">
            <div class="panel-label">📊 文献库统计</div>
            <div class="stats-grid">
              <div class="stat-item"><span class="stat-icon">📄</span><span class="stat-val">{{ libraryStats.total }}</span><span class="stat-lbl">总文献数</span></div>
              <div class="stat-item"><span class="stat-icon">⭐</span><span class="stat-val">{{ library.papers.filter(p => p.starred).length }}</span><span class="stat-lbl">已收藏</span></div>
              <div class="stat-item"><span class="stat-icon">📁</span><span class="stat-val">{{ libraryStats.collections }}</span><span class="stat-lbl">分类数</span></div>
              <div class="stat-item"><span class="stat-icon">🕐</span><span class="stat-val">{{ libraryStats.recent }}</span><span class="stat-lbl">最近添加</span></div>
            </div>
          </div>
          <div class="panel-section">
            <div class="panel-label">📚 文献列表</div>
            <div class="library-papers">
              <div v-for="paper in getCurrentPapers().slice(0, 10)" :key="paper.id" class="library-paper-item">
                <div class="paper-title" @click="showLiteratureDetail(paper)">{{ paper.title }}</div>
                <div class="paper-meta">{{ paper.authors }}, {{ paper.year }}</div>
                <div class="paper-actions">
                  <span class="action-btn" :class="{ starred: paper.starred }" @click="toggleStar(paper.id)">⭐</span>
                  <span class="action-btn" @click="removeFromLibrary(paper.id)">🗑️</span>
                </div>
              </div>
              <div v-if="getCurrentPapers().length === 0" class="empty-library">
                文献库为空，请通过检索或导入添加文献
              </div>
            </div>
          </div>
        </template>

        <!-- Import Dialog -->
        <div v-if="importDialogVisible" class="import-dialog">
          <div class="import-dialog-content">
            <div class="import-dialog-header">
              <h3>导入文献</h3>
              <button @click="importDialogVisible = false">✕</button>
            </div>
            <div class="import-format-select">
              <label>选择格式：</label>
              <select v-model="importFormat">
                <option value="ris">RIS</option>
                <option value="bibtex">BibTeX</option>
              </select>
            </div>
            <textarea v-model="importText" placeholder="粘贴文献数据..." rows="10"></textarea>
            <div class="import-dialog-actions">
              <button @click="handleImport">导入</button>
              <button @click="importDialogVisible = false">取消</button>
            </div>
          </div>
        </div>

        <!-- Image Insert Dialog -->
        <div v-if="imageDialogVisible" class="import-dialog">
          <div class="import-dialog-content">
            <div class="import-dialog-header">
              <h3>插入图片</h3>
              <button @click="imageDialogVisible = false">✕</button>
            </div>
            <div class="import-format-select">
              <label>图片来源：</label>
              <select v-model="imageSource">
                <option value="url">URL 链接</option>
                <option value="upload">本地上传</option>
              </select>
            </div>
            <div v-if="imageSource === 'url'">
              <input
                v-model="imageUrl"
                type="text"
                placeholder="输入图片 URL（https://...）"
                style="width:100%;padding:8px 12px;border:1.5px solid var(--border);border-radius:4px;font-size:0.64rem;background:var(--editor-bg);color:var(--text);font-family:inherit;outline:none;"
              />
              <div v-if="imageUrl" style="margin-top:10px;text-align:center;">
                <img :src="imageUrl" alt="preview" style="max-width:100%;max-height:160px;border-radius:4px;border:1px solid var(--border);" @error="(e) => e.target.style.display='none'" />
              </div>
            </div>
            <div v-else>
              <input type="file" accept="image/*" @change="onImageFileChange" ref="imageFileInput" style="font-size:0.64rem;" />
              <div v-if="imagePreview" style="margin-top:10px;text-align:center;">
                <img :src="imagePreview" alt="preview" style="max-width:100%;max-height:160px;border-radius:4px;border:1px solid var(--border);" />
              </div>
            </div>
            <input
              v-model="imageCaption"
              type="text"
              placeholder="图注说明（可选，如：图1 实验结果对比）"
              style="width:100%;margin-top:10px;padding:8px 12px;border:1.5px solid var(--border);border-radius:4px;font-size:0.64rem;background:var(--editor-bg);color:var(--text);font-family:inherit;outline:none;"
            />
            <div class="import-dialog-actions">
              <button @click="confirmInsertImage">插入</button>
              <button @click="imageDialogVisible = false">取消</button>
            </div>
          </div>
        </div>

        <!-- Review Panel -->
        <template v-if="currentTab === 'review'">
          <div class="panel-section">
            <div class="panel-label">🔍 主题检索</div>
            <div class="ai-input-row">
              <input type="text" placeholder="输入研究主题…" v-model="searchQuery" @keyup.enter="handleSearch">
              <button @click="handleSearch" :disabled="aiLoading">{{ aiLoading ? '检索中...' : '检索' }}</button>
            </div>
          </div>
          <div class="panel-section">
            <div class="panel-label">📄 检索结果</div>
            <div v-if="literatureResults.length > 0">
              <div v-for="p in literatureResults.slice(0, 8)" :key="p.id" class="cite-mini" @click="showLiteratureDetail(p)">
                <span class="cite-num">{{ p.index }}</span>
                <span>{{ p.authors }}, {{ p.journal }} {{ p.year }} (引用{{ p.citations }})</span>
              </div>
            </div>
            <div v-else class="suggestion-item">输入研究主题并点击"检索"获取文献</div>
          </div>
          <div class="panel-section">
            <div class="panel-label">💡 使用提示</div>
            <div class="suggestion-item">1. 输入研究关键词进行文献检索</div>
            <div class="suggestion-item">2. 点击文献可查看详情和摘要</div>
            <div class="suggestion-item">3. 重要文献可添加到"已标注重要"</div>
          </div>
        </template>

        <!-- Outline Panel -->
        <template v-if="currentTab === 'outline'">
          <div class="panel-section">
            <div class="panel-label">📋 论文结构选择</div>
            <div class="outline-options">
              <div v-for="type in outlineTypes" :key="type.key" class="outline-option" :class="{ active: currentOutlineType === type.key }" @click="selectOutline(type.key)">
                {{ type.icon }} {{ type.label }}
              </div>
            </div>
          </div>
          <div v-if="currentOutline" class="panel-section">
            <div class="panel-label">📋 {{ currentOutline.name }}</div>
            <div class="outline-sections">
              <div v-for="(section, idx) in currentOutline.sections" :key="idx" class="outline-section-item">
                <div class="section-header">
                  <span class="section-icon">{{ section.icon }}</span>
                  <span class="section-title">{{ section.title }}</span>
                </div>
                <div class="section-tips">{{ section.tips }}</div>
              </div>
            </div>
          </div>
        </template>

        <!-- Polish Panel -->
        <template v-if="currentTab === 'polish'">
          <div class="panel-section">
            <div class="panel-label">💡 润色建议 ({{ suggestions.length }}条)</div>
            <div v-if="suggestions.length > 0">
              <div v-for="(s, idx) in suggestions.slice(0, 10)" :key="idx" class="suggestion-item">
                <span class="sug-tag" :class="s.type">{{ s.type === 'grammar' ? '语法' : s.type === 'style' ? '表达' : '结构' }}</span>
                第{{ s.line }}行: "{{ s.text }}" → {{ s.suggestion }}
              </div>
            </div>
            <div v-else class="suggestion-item">编辑器内容将自动检测语法和表达问题</div>
          </div>
          <div class="panel-section">
            <div class="panel-label">✏️ 快捷指令</div>
            <div class="ai-input-row"><input type="text" placeholder="输入润色指令…"><button>执行</button></div>
            <div class="quick-tags">
              <span class="quick-tag" @click="handlePolish('paragraph')">✨ 润色整段</span>
              <span class="quick-tag" @click="handlePolish('academic')">📖 学术化改写</span>
              <span class="quick-tag" @click="handlePolish('concise')">✂️ 精简表达</span>
              <span class="quick-tag" @click="handlePolish('expand')">📝 扩展论述</span>
            </div>
          </div>
        </template>

        <!-- Format Panel -->
        <template v-if="currentTab === 'format'">
          <div class="panel-section">
            <div class="panel-label">⚠️ 格式问题 ({{ referenceCheck.issues.length }}条)</div>
            <div v-if="referenceCheck.issues.length > 0">
              <div v-for="(issue, idx) in referenceCheck.issues" :key="idx" class="suggestion-item">
                <span class="sug-tag grammar">引用</span>
                {{ issue.message }}
              </div>
            </div>
            <div v-else class="suggestion-item">未发现明显的引用格式问题</div>
          </div>
          <div class="panel-section">
            <div class="panel-label">📏 文档统计</div>
            <div class="stats-grid">
              <div class="stat-item"><span class="stat-icon">📝</span><span class="stat-val">{{ wordStats.characters }}</span><span class="stat-lbl">字符数</span></div>
              <div class="stat-item"><span class="stat-icon">📊</span><span class="stat-val">{{ wordStats.words }}</span><span class="stat-lbl">字数</span></div>
              <div class="stat-item"><span class="stat-icon">📄</span><span class="stat-val">{{ wordStats.paragraphs }}</span><span class="stat-lbl">段落数</span></div>
              <div class="stat-item"><span class="stat-icon">✏️</span><span class="stat-val">{{ wordStats.sentences }}</span><span class="stat-lbl">句子数</span></div>
              <div class="stat-item"><span class="stat-icon">📚</span><span class="stat-val">{{ referenceCheck.citationCount }}</span><span class="stat-lbl">引用数</span></div>
            </div>
          </div>
          <div class="panel-section">
            <div class="panel-label">✅ 规范检查概览</div>
            <div style="font-size:0.64rem;color:var(--text2);line-height:1.8;">
              ✅ 字体：宋体/Times New Roman<br>
              ✅ 字号：小四/12pt<br>
              ✅ 行距：1.5倍<br>
              <span :class="referenceCheck.issues.length > 0 ? 'text-warn' : 'text-ok'">{{ referenceCheck.issues.length > 0 ? '⚠️' : '✅' }}</span> 参考文献格式：GB/T 7714<br>
              ✅ 页边距：上下2.54cm 左右3.17cm
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import { ImageResize } from '../../tiptap/ImageResize.js'
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'
import { MathFormula } from '../../tiptap/MathFormula.js'
import { useAuth } from '../../composables/useAuth.js'
import { useWritingAssistant } from '../../composables/useWritingAssistant.js'
import ResearcherNav from '../../components/ResearcherNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
const {
  loading: aiLoading,
  library,
  libraryStats,
  searchLiterature,
  addToLibrary,
  removeFromLibrary,
  toggleStar,
  createCollection,
  getPapersByCollection,
  getStarredPapers,
  importFromRIS,
  importFromBibTeX,
  exportToRIS,
  exportToBibTeX,
  analyzeText,
  checkReferences,
  generateOutline,
  getWordStats
} = useWritingAssistant()

function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}

const isDark = ref(false)
const currentTab = ref('review')
const activeSidebarIdx = ref(0)
const wordStats = ref({ characters: 0, words: 0, paragraphs: 0, sentences: 0 })

// Real data states
const literatureResults = ref([])
const suggestions = ref([])
const referenceCheck = ref({ citationCount: 0, citations: [], issues: [] })
const currentOutline = ref(null)
const currentOutlineType = ref('imrad')
const searchQuery = ref('CRISPR apple salt tolerance')
const selectedLiterature = ref(null)
const selectedCollection = ref(null)
const importDialogVisible = ref(false)
const importFormat = ref('ris')
const importText = ref('')

// Toolbar dropdown states
const showCitePicker = ref(false)
const showFigureMenu = ref(false)
const showFormulaMenu = ref(false)

// Image dialog states
const imageDialogVisible = ref(false)
const imageSource = ref('url')
const imageUrl = ref('')
const imagePreview = ref('')
const imageCaption = ref('')
const imageFileInput = ref(null)

const outlineTypes = [
  { key: 'imrad', icon: '📋', label: 'IMRaD标准结构' },
  { key: 'review', icon: '📝', label: '综述型结构' },
  { key: 'thesis', icon: '🎓', label: '学位论文结构' },
  { key: 'letter', icon: '📊', label: '简报/快报结构' },
]

const tabs = [
  { key: 'library', icon: '📚', label: '文献库管理' },
  { key: 'review', icon: '📖', label: '文献综述生成' },
  { key: 'outline', icon: '🏗️', label: '论文框架搭建' },
  { key: 'polish', icon: '✨', label: '语言润色' },
  { key: 'format', icon: '✅', label: '格式规范检查' },
]

const initialContent = `<h2>苹果砧木耐盐基因MdNHX1的CRISPR/Cas9编辑及功能验证</h2>
<h3>摘要</h3>
<p>土壤盐渍化是限制苹果产业发展的关键非生物胁迫因子之一。本研究以苹果砧木'M9-T337'为材料，利用CRISPR/Cas9技术对液泡膜Na⁺/H⁺逆向转运蛋白基因MdNHX1进行定向敲除，获得纯合突变体株系3个。在200 mM NaCl胁迫处理下，突变体植株的叶绿素含量显著低于野生型，丙二醛（MDA）含量升高42.6%，表明MdNHX1在苹果耐盐性中发挥关键作用。</p>
<h3>引言</h3>
<p>苹果（<i>Malus domestica</i> Borkh.）是全球栽培面积最广的果树之一。然而，随着全球气候变化和灌溉农业的扩展，土壤盐渍化问题日益严峻，已成为制约苹果产量和品质的关键因素[1]。据统计，我国环渤海湾和西北黄土高原两大苹果主产区均有不同程度的盐碱化分布[2]。</p>
<p>Na⁺/H⁺反向转运蛋白（NHX）在植物离子稳态和耐盐性调控中具有核心功能。在拟南芥中，AtNHX1通过将Na⁺区隔化至液泡来降低细胞质离子毒性[3]。然而，苹果MdNHX1的功能尚未通过反向遗传学手段验证，目前关于苹果NHX基因的研究仍较为有限。</p>
<p>CRISPR/Cas9基因编辑技术为果树功能基因组学研究提供了高效工具[4]。本研究拟通过构建MdNHX1的CRISPR敲除载体，转化苹果砧木，验证该基因在耐盐性中的功能，为苹果耐盐分子育种提供理论依据和种质材料。</p>`

const editor = useEditor({
  content: initialContent,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
    }),
    Underline,
    ImageResize.configure({ inline: false, allowBase64: true }),
    Table.configure({ resizable: true }),
    TableRow,
    TableCell,
    TableHeader,
    MathFormula,
  ],
  onUpdate: ({ editor }) => {
    analyzeEditorContent(editor.getText())
  },
})

// Dynamic sidebar data based on current state
const sidebarData = computed(() => ({
  library: {
    title: '文献库',
    items: [
      { icon: '📄', label: `全部文献 (${library.value.papers.length})` },
      { icon: '⭐', label: `已收藏 (${library.value.papers.filter(p => p.starred).length})` },
      { icon: '🕐', label: `最近添加 (${libraryStats.value.recent})` },
      ...library.value.collections.map(c => ({
        icon: '📁',
        label: c.name,
        collectionId: c.id
      })),
      { icon: '➕', label: '新建分类', action: 'create_collection' },
    ]
  },
  review: {
    title: '文献资料库',
    items: [
      { icon: '📄', label: `已导入文献 (${library.value.papers.length})` },
      { icon: '🔍', label: `检索结果 (${literatureResults.value.length})` },
      { icon: '⭐', label: `已标注重要 (${library.value.papers.filter(p => p.starred).length})` },
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
    title: '润色建议',
    items: suggestions.value.map((s, i) => ({
      icon: s.type === 'grammar' ? '⚠️' : s.type === 'style' ? '💡' : '📋',
      label: `第${s.line}行: ${s.text.substring(0, 15)}...`,
      badge: s.type === 'grammar' ? 'err' : 'warn'
    }))
  },
  format: {
    title: '检查项列表',
    items: [
      { icon: '⚠️', label: `引用格式 (${referenceCheck.value.issues.length}处)`, badge: referenceCheck.value.issues.length > 0 ? 'err' : null },
      { icon: '✅', label: '字体段落' },
      { icon: '⚠️', label: `引用数量 (${referenceCheck.value.citationCount})`, badge: 'warn' },
      { icon: '✅', label: '页边距行距' },
      { icon: '✅', label: '作者信息' },
    ]
  }
}))

const sidebarTitle = computed(() => sidebarData.value[currentTab.value]?.title || '')
const sidebarItems = computed(() => sidebarData.value[currentTab.value]?.items || [])
const panelTitle = computed(() => {
  const titles = { library: '📚 文献库管理', review: '🤖 综述生成助手', outline: '🧱 框架搭建助手', polish: '✨ 语言润色助手', format: '✅ 格式检查助手' }
  return titles[currentTab.value] || ''
})

// Search literature from OpenAlex
async function handleSearch() {
  if (!searchQuery.value.trim()) return
  try {
    const results = await searchLiterature(searchQuery.value, 20)
    literatureResults.value = results
  } catch (err) {
    console.error('Literature search failed:', err)
  }
}

// Select outline type
function selectOutline(type) {
  currentOutlineType.value = type
  currentOutline.value = generateOutline(type)
}

// Show literature detail
function showLiteratureDetail(paper) {
  selectedLiterature.value = paper
  alert(`标题: ${paper.title}\n\n作者: ${paper.authors}\n\n期刊: ${paper.journal} ${paper.year}\n\n引用: ${paper.citations}\n\n${paper.abstract ? '摘要: ' + paper.abstract.substring(0, 200) + '...' : '无摘要'}`)
}

// Add search result to library
function addSearchResultToLibrary(paper) {
  if (addToLibrary(paper)) {
    alert(`已添加到文献库: ${paper.title}`)
  } else {
    alert('该文献已在文献库中')
  }
}

// Handle import
function handleImport() {
  if (!importText.value.trim()) {
    alert('请粘贴文献数据')
    return
  }

  let result
  if (importFormat.value === 'ris') {
    result = importFromRIS(importText.value)
  } else if (importFormat.value === 'bibtex') {
    result = importFromBibTeX(importText.value)
  }

  if (result) {
    alert(`导入完成: 成功 ${result.imported} 篇，共 ${result.total} 篇`)
    importDialogVisible.value = false
    importText.value = ''
  }
}

// Export library
function handleExport(format) {
  let content, filename, type
  if (format === 'ris') {
    content = exportToRIS()
    filename = 'literature_export.ris'
    type = 'application/x-research-info-systems'
  } else if (format === 'bibtex') {
    content = exportToBibTeX()
    filename = 'literature_export.bib'
    type = 'application/x-bibtex'
  }

  if (content) {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }
}

// Get papers for current view
function getCurrentPapers() {
  if (selectedCollection.value === 'starred') {
    return getStarredPapers()
  }
  return getPapersByCollection(selectedCollection.value)
}

// Analyze editor content
function analyzeEditorContent(text) {
  if (!text && editor.value) {
    text = editor.value.getText()
  }
  if (!text) return

  // Update word stats
  wordStats.value = getWordStats(text)

  // Analyze text for suggestions
  suggestions.value = analyzeText(text)

  // Check references
  referenceCheck.value = checkReferences(text)
}

// Handle polish quick actions
function handlePolish(type) {
  // In a real implementation, this would call an AI API
  alert(`"${type}" 功能需要后端AI支持，当前为演示模式`)
}

function switchTab(tab) {
  currentTab.value = tab
  activeSidebarIdx.value = 0
  if (tab === 'review' && literatureResults.value.length === 0) {
    handleSearch()
  }
}

function onSidebarClick(e) {
  const item = e.target.closest('.sidebar-item')
  if (item && item.dataset.idx !== undefined) {
    activeSidebarIdx.value = parseInt(item.dataset.idx)
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
}

// --- Toolbar dropdown handlers ---

function toggleCitePicker() {
  showCitePicker.value = !showCitePicker.value
  showFigureMenu.value = false
}

function toggleFigureMenu() {
  showFigureMenu.value = !showFigureMenu.value
  showCitePicker.value = false
  showFormulaMenu.value = false
}

function toggleFormulaMenu() {
  showFormulaMenu.value = !showFormulaMenu.value
  showCitePicker.value = false
  showFigureMenu.value = false
}

function closeDropdowns() {
  showCitePicker.value = false
  showFigureMenu.value = false
  showFormulaMenu.value = false
}

function insertCitation(num) {
  if (!editor.value) return
  editor.value.chain().focus().insertContent(`<sup class="cite-ref">[${num}]</sup>`).run()
  closeDropdowns()
}

// --- Image insertion ---
function openImageDialog() {
  imageUrl.value = ''
  imagePreview.value = ''
  imageCaption.value = ''
  imageSource.value = 'url'
  imageDialogVisible.value = true
  closeDropdowns()
}

function onImageFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { imagePreview.value = reader.result }
  reader.readAsDataURL(file)
}

function confirmInsertImage() {
  if (!editor.value) return
  const src = imageSource.value === 'url' ? imageUrl.value : imagePreview.value
  if (!src) { alert('请输入图片地址或选择文件'); return }

  editor.value.chain().focus().setImage({ src }).run()

  if (imageCaption.value.trim()) {
    editor.value.chain().focus().insertContent(
      `<p class="image-caption" style="text-align:center;font-size:0.78rem;color:var(--text3);margin-top:4px;">${imageCaption.value.trim()}</p><p></p>`
    ).run()
  }
  imageDialogVisible.value = false
}

// --- Table insertion ---
function insertTable() {
  if (!editor.value) return
  editor.value.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  closeDropdowns()
}

function insertFormula(displayMode = false) {
  if (!editor.value) return
  const formula = prompt('请输入 LaTeX 公式（例如: E = mc^2）：')
  if (!formula?.trim()) return
  editor.value.chain().focus().insertContent({
    type: 'mathFormula',
    attrs: { formula: formula.trim(), displayMode },
  }).run()
  closeDropdowns()
}

onMounted(() => {
  // Auto-search on load
  handleSearch()
  // Generate default outline
  currentOutline.value = generateOutline('imrad')
  // Close toolbar dropdowns on outside click
  document.addEventListener('click', closeDropdowns)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeDropdowns)
  editor.value?.destroy()
})
</script>

<style>
:root {
  --bg: #f8f6f1;
  --card: #ffffff;
  --card-solid: #ffffff;
  --nav-bg: #ffffff;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.15);
  --accent-glow: rgba(91,141,239,0.15);
  --border: #e0dcd5;
  --section-border: #e0dcd5;
  --text2: #666666;
  --text3: #999999;
  --divider: #e8e4db;
  --radius: 16px;
  --radius-sm: 8px;
  --tag-bg: #eef4ff;
  --tag-border: rgba(91,141,239,0.3);
  --editor-bg: #ffffff;
  --highlight-suggest: rgba(245,158,11,0.12);
  --highlight-error: rgba(231,76,60,0.08);
  --highlight-border-suggest: #f59e0b;
  --highlight-border-error: #e74c3c;
  --scrollbar-thumb: rgba(91,141,239,0.25);
  --ai-card-bg: #eef4ff;
  --panel-section-radius: 0px;
}
body.dark {
  --bg: #12121a;
  --card: #1e1e2e;
  --card-solid: #1e1e2e;
  --nav-bg: #1e1e2e;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.2);
  --accent-glow: rgba(91,141,239,0.2);
  --border: #444444;
  --section-border: #444444;
  --text: #e0e0e0;
  --text2: #aaaaaa;
  --text3: #777777;
  --divider: #333333;
  --tag-bg: rgba(91,141,239,0.1);
  --tag-border: rgba(91,141,239,0.4);
  --editor-bg: #1a1a2a;
  --highlight-suggest: rgba(245,158,11,0.15);
  --highlight-error: rgba(231,76,60,0.12);
  --highlight-border-suggest: #f59e0b;
  --highlight-border-error: #e74c3c;
  --scrollbar-thumb: rgba(91,141,239,0.35);
  --ai-card-bg: rgba(91,141,239,0.05);
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
  flex-shrink: 0; height: 48px; background: var(--nav-bg);
  border: 1px solid var(--border); border-radius: var(--radius);
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
  padding: 6px 14px; border-radius: 14px; font-size: 0.78rem; font-weight: 500;
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
  color: var(--text2); font-weight: 500; font-size: 0.78rem; cursor: pointer;
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
.word-count { font-size: 0.75rem; color: var(--text3); white-space: nowrap; font-weight: 500; }

.workspace { flex: 1; min-height: 0; display: flex; gap: 8px; }

.sidebar {
  width: 220px; min-width: 180px; flex-shrink: 0;
  background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius);
  display: flex; flex-direction: column; overflow: hidden;
  transition: box-shadow 0.3s;
}
.sidebar:hover { box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.sidebar-hd {
  padding: 12px 14px; font-weight: 700; font-size: 0.78rem; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--accent); border-bottom: 1px solid var(--divider);
  display: flex; align-items: center; gap: 6px; flex-shrink: 0; background: var(--card-solid);
}
.sidebar-hd i { width: 4px; height: 14px; background: linear-gradient(180deg, var(--accent), #4a3cc0); border-radius: 2px; box-shadow: 0 0 6px var(--accent-glow); flex-shrink: 0; }
.sidebar-tab-select {
  flex: 1; padding: 6px 8px; border: 1.5px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.75rem; font-weight: 600; border-radius: 8px;
  font-family: inherit; cursor: pointer; outline: none; transition: 0.2s;
}
.sidebar-tab-select:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-light); }
.sidebar-list { list-style: none; padding: 4px 6px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 1px; }
.sidebar-item {
  padding: 9px 10px; border-radius: 0; cursor: pointer; font-size: 0.8rem; color: var(--text2);
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
  flex: 1; min-width: 0; background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius); display: flex; flex-direction: column;
  overflow: hidden; transition: box-shadow 0.3s;
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
.editor-toolbar button.active {
  background: var(--accent); color: #fff; border-color: var(--accent);
  box-shadow: 0 0 8px var(--accent-glow);
}
.editor-toolbar button:disabled {
  opacity: 0.35; cursor: not-allowed;
}
.editor-toolbar button:disabled:hover {
  background: transparent; color: var(--text2);
}
.toolbar-divider { width: 1px; height: 16px; background: var(--divider); margin: 0 4px; flex-shrink: 0; }

/* Toolbar dropdown menus */
.toolbar-dropdown-wrap { position: relative; display: flex; }
.toolbar-dropdown {
  position: absolute; top: 100%; left: 50%; transform: translateX(-50%); margin-top: 6px;
  background: var(--card-solid); border: 1.5px solid var(--border); border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15); z-index: 100; min-width: 220px;
  max-height: 280px; overflow-y: auto; padding: 4px 0;
}
.dropdown-hd {
  padding: 8px 12px; font-size: 0.75rem; font-weight: 700; color: var(--accent);
  text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--divider);
}
.dropdown-empty { padding: 12px; font-size: 0.75rem; color: var(--text3); text-align: center; }
.dropdown-item {
  padding: 7px 12px; font-size: 0.78rem; color: var(--text2); cursor: pointer;
  transition: 0.15s; display: flex; align-items: center; gap: 6px; white-space: nowrap;
}
.dropdown-item:hover { background: var(--accent-light); color: var(--accent); }
.cite-idx { font-weight: 700; color: var(--accent); font-size: 0.75rem; flex-shrink: 0; }
.cite-title { overflow: hidden; text-overflow: ellipsis; }
.editor-content {
  flex: 1; min-height: 0; overflow-y: auto; background: var(--editor-bg); transition: background 0.3s;
}
.editor-content .tiptap {
  padding: 24px 28px; font-size: 0.84rem;
  line-height: 1.95; color: var(--text); outline: none; min-height: 100%;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', serif;
  letter-spacing: 0.01em;
}
.editor-content .tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left; color: var(--text3); pointer-events: none; height: 0;
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

/* Images in editor */
.editor-content .image-resize-wrap {
  display: inline-block; vertical-align: baseline; margin: 0.2em 0.4em;
  user-select: none; cursor: default;
}
.editor-content .image-resize-box {
  border: 1px solid transparent; border-radius: 6px;
  overflow: visible;
}
.editor-content .image-resize-wrap.is-selected .image-resize-box {
  outline: 2px solid var(--accent); box-shadow: 0 0 12px var(--accent-glow);
}

/* 8 resize handles */
.editor-content .handle {
  position: absolute; width: 10px; height: 10px;
  background: var(--accent); border: 1.5px solid #fff;
  border-radius: 2px; z-index: 20; box-shadow: 0 0 4px rgba(0,0,0,0.25);
}
.editor-content .handle.nw { top: -5px; left: -5px; cursor: nw-resize; }
.editor-content .handle.ne { top: -5px; right: -5px; cursor: ne-resize; }
.editor-content .handle.sw { bottom: -5px; left: -5px; cursor: sw-resize; }
.editor-content .handle.se { bottom: -5px; right: -5px; cursor: se-resize; }
.editor-content .handle.n  { top: -5px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.editor-content .handle.s  { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.editor-content .handle.w  { top: 50%; left: -5px; transform: translateY(-50%); cursor: w-resize; }
.editor-content .handle.e  { top: 50%; right: -5px; transform: translateY(-50%); cursor: e-resize; }
.editor-content .img-delete-btn {
  position: absolute; top: -12px; right: -12px;
  width: 22px; height: 22px; border-radius: 50%;
  background: #e05555; color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 30; line-height: 1;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
  transition: transform 0.15s, background 0.15s;
}
.editor-content .img-delete-btn:hover {
  background: #c03030; transform: scale(1.15);
}

/* Tables in editor */
.editor-content table {
  border-collapse: collapse; margin: 1em 0; width: 100%;
  font-size: 0.8rem; line-height: 1.6;
}
.editor-content th,
.editor-content td {
  border: 1.5px solid var(--border); padding: 8px 12px;
  text-align: left; vertical-align: top; min-width: 60px;
}
.editor-content th {
  background: var(--accent-light); font-weight: 600; color: var(--accent);
}
.editor-content td {
  background: var(--editor-bg);
}
.editor-content .selectedCell {
  background: var(--accent-light);
}
/* Column resize handle */
.editor-content .column-resize-handle {
  background: var(--accent); width: 2px; position: absolute;
  top: 0; bottom: 0; right: -1px; cursor: col-resize;
}
.editor-content .resize-cursor { cursor: col-resize !important; }

/* Inline formula node */
.editor-content .math-inline {
  display: inline; vertical-align: middle; cursor: default;
  padding: 1px 4px; border-radius: 3px; transition: background 0.15s;
}
.editor-content .math-inline:hover { background: var(--accent-light); }
.editor-content .math-inline .math-render .katex { font-size: 1em; }

/* Block-level formula host */
.editor-content .math-block-host {
  display: block; text-align: center; margin: 1em 0; padding: 12px 16px;
  background: var(--ai-card-bg); border: 1px solid var(--divider);
  border-radius: 6px; overflow-x: auto; cursor: default; transition: background 0.15s;
}
.editor-content .math-block-host:hover { background: var(--accent-light); }
.editor-content .math-block-host .math-render .katex { font-size: 1.15em; }

.ai-panel {
  width: 270px; min-width: 220px; flex-shrink: 0;
  background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius);
  display: flex; flex-direction: column; overflow: hidden;
  transition: box-shadow 0.3s;
}
.ai-panel:hover { box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.panel-hd {
  padding: 12px 14px; font-weight: 700; font-size: 0.78rem; text-transform: uppercase;
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
  font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase;
  letter-spacing: 0.04em; margin-bottom: 6px; display: flex; align-items: center; gap: 5px;
  border-bottom: 1px solid var(--divider); padding-bottom: 4px;
}
.suggestion-item {
  background: var(--card); border: 1px solid var(--border); border-radius: 0;
  padding: 8px 10px; font-size: 0.78rem; color: var(--text2); line-height: 1.5;
  cursor: pointer; transition: 0.15s; margin-bottom: 4px;
}
.suggestion-item:last-child { margin-bottom: 0; }
.suggestion-item:hover { border-color: var(--accent); background: var(--accent-light); box-shadow: 0 2px 10px var(--accent-glow); }
.suggestion-item .sug-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; margin-right: 4px; }
.sug-tag.grammar { background: rgba(184, 74, 74, 0.15); color: #b84a4a; }
body.dark .sug-tag.grammar { background: rgba(184, 74, 74, 0.25); color: #e07070; }
.sug-tag.style { background: rgba(194, 138, 42, 0.15); color: #9e6a1a; }
body.dark .sug-tag.style { background: rgba(194, 138, 42, 0.25); color: #d4952a; }
.sug-tag.structure { background: rgba(90, 76, 216, 0.12); color: var(--accent); }
.cite-mini {
  font-size: 0.78rem; color: var(--text2); padding: 5px 8px; border-radius: 0;
  cursor: pointer; transition: 0.15s; display: flex; align-items: center; gap: 6px;
  border-bottom: 1px solid var(--divider);
}
.cite-mini:last-child { border-bottom: none; }
.cite-mini:hover { background: var(--accent-light); }
.cite-num {
  width: 20px; height: 20px; background: var(--accent-light); color: var(--accent);
  font-weight: 700; font-size: 0.72rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.ai-input-row { display: flex; gap: 5px; margin-top: 6px; }
.ai-input-row input {
  flex: 1; padding: 8px 12px; border: 1.5px solid var(--border); border-radius: 0;
  font-size: 0.78rem; background: var(--editor-bg); color: var(--text); font-family: inherit; outline: none; transition: 0.2s;
}
.ai-input-row input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-light); }
.ai-input-row button {
  padding: 8px 14px; background: var(--accent); color: #fff; border: none; border-radius: 0;
  font-weight: 600; font-size: 0.78rem; cursor: pointer; white-space: nowrap; transition: 0.2s; letter-spacing: 0.02em;
}
.ai-input-row button:hover { opacity: 0.9; box-shadow: 0 4px 12px var(--accent-glow); }
.quick-tags { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
.quick-tag {
  font-size: 0.75rem; padding: 6px 8px; background: var(--tag-bg); border: 1px solid var(--tag-border);
  border-radius: 0; cursor: pointer; color: var(--accent); transition: 0.15s;
  white-space: nowrap; font-weight: 500; text-align: center;
}
.quick-tag:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-generate {
  width: 100%; padding: 10px; background: var(--accent); color: #fff; border: none;
  border-radius: 0; font-weight: 600; font-size: 0.78rem; cursor: pointer; margin-top: 8px;
  transition: 0.2s; letter-spacing: 0.02em;
}
.btn-generate:hover { opacity: 0.9; box-shadow: 0 4px 12px var(--accent-glow); }

/* Outline options */
.outline-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}
.outline-option {
  padding: 8px 10px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
}
.outline-option:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}
.outline-option.active {
  border-color: var(--accent);
  background: var(--accent-light);
  font-weight: 600;
  color: var(--accent);
}

/* Outline sections */
.outline-sections {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.outline-section-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 10px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.section-icon {
  font-size: 0.85rem;
}
.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
}
.section-tips {
  font-size: 0.75rem;
  color: var(--text3);
  line-height: 1.4;
  padding-left: 24px;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin-top: 8px;
}
.stat-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-icon {
  font-size: 0.85rem;
}
.stat-val {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
}
.stat-lbl {
  font-size: 0.72rem;
  color: var(--text3);
}

/* Text status colors */
.text-warn {
  color: #c28a2a;
}
.text-ok {
  color: #4caf50;
}

/* Library styles */
.import-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.btn-import, .btn-export {
  width: 100%;
  padding: 8px 12px;
  border: 1.5px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 0.78rem;
  font-weight: 500;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-import:hover, .btn-export:hover {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent);
}
.btn-import {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.btn-import:hover {
  opacity: 0.9;
}

/* Library papers list */
.library-papers {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
}
.library-paper-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 10px;
}
.library-paper-item .paper-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  line-height: 1.4;
}
.library-paper-item .paper-title:hover {
  color: var(--accent);
}
.library-paper-item .paper-meta {
  font-size: 0.72rem;
  color: var(--text3);
  margin-top: 2px;
}
.paper-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.action-btn {
  cursor: pointer;
  font-size: 0.75rem;
  opacity: 0.5;
  transition: opacity 0.15s;
}
.action-btn:hover {
  opacity: 1;
}
.action-btn.starred {
  opacity: 1;
}
.empty-library {
  font-size: 0.78rem;
  color: var(--text3);
  text-align: center;
  padding: 20px;
}

/* Import dialog */
.import-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.import-dialog-content {
  background: var(--card-solid);
  border: 2px solid var(--accent);
  border-radius: var(--radius);
  padding: 20px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}
.import-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.import-dialog-header h3 {
  font-size: 0.85rem;
  color: var(--text);
}
.import-dialog-header button {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: var(--text3);
}
.import-format-select {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.import-format-select label {
  font-size: 0.78rem;
  color: var(--text2);
}
.import-format-select select {
  padding: 6px 10px;
  border: 1.5px solid var(--border);
  border-radius: 4px;
  font-size: 0.78rem;
  background: var(--card);
  color: var(--text);
}
.import-dialog textarea {
  width: 100%;
  padding: 10px;
  border: 1.5px solid var(--border);
  border-radius: 4px;
  font-size: 0.78rem;
  font-family: monospace;
  background: var(--editor-bg);
  color: var(--text);
  resize: vertical;
}
.import-dialog textarea:focus {
  outline: none;
  border-color: var(--accent);
}
.import-dialog-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  justify-content: flex-end;
}
.import-dialog-actions button {
  padding: 8px 16px;
  border: 1.5px solid var(--border);
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.import-dialog-actions button:first-child {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.import-dialog-actions button:first-child:hover {
  opacity: 0.9;
}
.import-dialog-actions button:last-child {
  background: var(--card);
  color: var(--text);
}
.import-dialog-actions button:last-child:hover {
  border-color: var(--accent);
  color: var(--accent);
}

@media (max-width: 1000px) {
  .workspace { flex-direction: column; }
  .sidebar { width: 100%; min-width: 0; max-height: 130px; }
  .ai-panel { width: 100%; min-width: 0; max-height: 220px; }
  .editor-content { padding: 16px 18px; font-size: 0.78rem; }
  .tab-btn { padding: 6px 10px; font-size: 0.75rem; }
  .top-nav { flex-wrap: wrap; height: auto; min-height: 44px; padding: 8px 12px; gap: 6px; }
}
</style>
