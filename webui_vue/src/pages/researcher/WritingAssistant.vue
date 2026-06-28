<template>
<div class="writing-app">
  <!-- Top header bar -->
  <header class="top-header">
    <div class="header-left">
      <span class="draft-label">当前草稿：学术论文协同起草流</span>
      <span class="header-divider">|</span>
      <span class="kb-tag"><span class="kb-icon">📦</span> 已绑定"结构化知识库"动态论据层</span>
    </div>
    <div class="header-right">
      字数统计: <span class="word-count-num">{{ wordStats.words.toLocaleString() }}</span>
    </div>
  </header>

  <div class="main-content">
    <!-- Left: Knowledge Base Panel -->
    <section class="kb-panel">
      <div class="kb-panel-title"><span class="kb-title-icon">📦</span> 知识库文献导入</div>

      <button class="btn-import-kb" @click="importDialogVisible = true">
        <span class="btn-icon">＋</span> 从结构化知识库导入
      </button>

      <div class="kb-doc-list">
        <div class="kb-doc-header">已挂载论据源 ({{ library.papers.length }})</div>

        <div
          v-for="(paper, idx) in library.papers.slice(0, 10)"
          :key="paper.id"
          class="kb-doc-card"
          :class="{ active: selectedDocIdx === idx }"
          @click="selectedDocIdx = idx"
        >
          <div class="doc-card-title">{{ paper.title }}</div>
          <div class="doc-card-meta">
            <span>来自: {{ paper.collection || '未分类沉淀' }}</span>
            <span>{{ paper.citations || 0 }} 论据</span>
          </div>
          <span class="doc-card-remove" @click.stop="removeFromLibrary(paper.id)">✕</span>
        </div>

        <div v-if="library.papers.length === 0" class="kb-empty">
          暂无论据源，请从知识库导入文献
        </div>
      </div>
    </section>

    <!-- Center: Editor -->
    <section class="editor-section">
      <div class="editor-toolbar">
        <button title="加粗" :class="{ active: editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()"><b>B</b></button>
        <button title="斜体" :class="{ active: editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()"><i>I</i></button>
        <button title="下划线" :class="{ active: editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()"><u>U</u></button>
        <span class="tb-divider"></span>
        <button title="标题2" :class="{ active: editor?.isActive('heading', { level: 2 }) }" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()">H2</button>
        <button title="标题3" :class="{ active: editor?.isActive('heading', { level: 3 }) }" @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()">H3</button>
        <span class="tb-divider"></span>
        <button title="插入公式" @click="insertFormula(false)">∑</button>
        <button title="插入链接" @click="insertLink">🔗</button>
        <span class="tb-divider"></span>
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
            <div class="dropdown-item" @click="insertTable">📋 插入表格</div>
          </div>
        </div>
        <span class="tb-divider"></span>
        <button title="撤销" :disabled="!editor?.can().undo()" @click="editor?.chain().focus().undo().run()">↩</button>
        <button title="重做" :disabled="!editor?.can().redo()" @click="editor?.chain().focus().redo().run()">↪</button>
      </div>

      <div class="editor-canvas">
        <div class="paper-page">
          <EditorContent class="editor-content" :editor="editor" />
        </div>
      </div>
    </section>

    <!-- Right: AI Copilot Chat -->
    <section class="copilot-panel">
      <div class="copilot-header">
        <div class="copilot-title-row">
          <span class="copilot-icon">💬</span>
          <span class="copilot-title">学术研讨 Copilot</span>
        </div>
        <span class="copilot-status">
          <span class="status-dot"></span> 验证在线
        </span>
      </div>

      <div class="copilot-messages" ref="messagesRef">
        <div
          v-for="(msg, idx) in chatMessages"
          :key="idx"
          class="chat-msg"
          :class="msg.role"
        >
          <div class="msg-avatar" :class="msg.role">{{ msg.role === 'ai' ? 'AI' : '您' }}</div>
          <div class="msg-bubble" :class="msg.role">{{ msg.content }}</div>
        </div>
        <div v-if="chatMessages.length === 0" class="chat-welcome">
          <div class="chat-msg ai">
            <div class="msg-avatar ai">AI</div>
            <div class="msg-bubble ai">
              首席研究员您好。检测到您已成功从 <b>结构化知识库</b> 中挂载了数据。您可以直接让我辅助核验论据、润色段落或生成综述。
            </div>
          </div>
        </div>
      </div>

      <div class="copilot-input-area">
        <div class="copilot-input-box">
          <textarea
            v-model="chatInput"
            placeholder="基于导入数据提问，或通过 / 触发指令..."
            @keydown.enter.exact.prevent="sendChatMessage"
          ></textarea>
          <div class="copilot-input-actions">
            <div class="input-tools">
              <button title="锚定特定文献段落">#</button>
              <button title="引用知识库指标">📦</button>
            </div>
            <button class="btn-send" @click="sendChatMessage" :disabled="!chatInput.trim() || chatSending">
              {{ chatSending ? '...' : '↵' }}
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>

  <!-- Import Dialog -->
  <div v-if="importDialogVisible" class="modal-overlay" @click.self="importDialogVisible = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>导入文献</h3>
        <button @click="importDialogVisible = false">✕</button>
      </div>
      <div class="modal-body">
        <div class="format-select">
          <label>选择格式：</label>
          <select v-model="importFormat">
            <option value="ris">RIS</option>
            <option value="bibtex">BibTeX</option>
          </select>
        </div>
        <textarea v-model="importText" placeholder="粘贴文献数据..." rows="10"></textarea>
      </div>
      <div class="modal-actions">
        <button class="btn-primary" @click="handleImport">导入</button>
        <button class="btn-secondary" @click="importDialogVisible = false">取消</button>
      </div>
    </div>
  </div>

  <!-- Image Insert Dialog -->
  <div v-if="imageDialogVisible" class="modal-overlay" @click.self="imageDialogVisible = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>插入图片</h3>
        <button @click="imageDialogVisible = false">✕</button>
      </div>
      <div class="modal-body">
        <div class="format-select">
          <label>图片来源：</label>
          <select v-model="imageSource">
            <option value="url">URL 链接</option>
            <option value="upload">本地上传</option>
          </select>
        </div>
        <div v-if="imageSource === 'url'">
          <input v-model="imageUrl" type="text" placeholder="输入图片 URL（https://...）" class="input-field" />
          <div v-if="imageUrl" class="image-preview">
            <img :src="imageUrl" alt="preview" @error="(e) => e.target.style.display='none'" />
          </div>
        </div>
        <div v-else>
          <input type="file" accept="image/*" @change="onImageFileChange" ref="imageFileInput" />
          <div v-if="imagePreview" class="image-preview">
            <img :src="imagePreview" alt="preview" />
          </div>
        </div>
        <input v-model="imageCaption" type="text" placeholder="图注说明（可选，如：图1 实验结果对比）" class="input-field" style="margin-top:10px;" />
      </div>
      <div class="modal-actions">
        <button class="btn-primary" @click="confirmInsertImage">插入</button>
        <button class="btn-secondary" @click="imageDialogVisible = false">取消</button>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import { ImageResize } from '../../tiptap/ImageResize.js'
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'
import { MathFormula } from '../../tiptap/MathFormula.js'
import { useAuth } from '../../composables/useAuth.js'
import { useWritingAssistant } from '../../composables/useWritingAssistant.js'
import { useGateway } from '../../composables/useGateway.js'

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

// Editor state
const wordStats = ref({ characters: 0, words: 0, paragraphs: 0, sentences: 0 })
const selectedDocIdx = ref(0)

// Chat state
const chatMessages = ref([])
const chatInput = ref('')
const chatSending = ref(false)
const messagesRef = ref(null)

// Dialog states
const importDialogVisible = ref(false)
const importFormat = ref('ris')
const importText = ref('')
const imageDialogVisible = ref(false)
const imageSource = ref('url')
const imageUrl = ref('')
const imagePreview = ref('')
const imageCaption = ref('')
const imageFileInput = ref(null)

// Toolbar dropdown states
const showCitePicker = ref(false)
const showFigureMenu = ref(false)

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

// Analyze editor content
function analyzeEditorContent(text) {
  if (!text && editor.value) {
    text = editor.value.getText()
  }
  if (!text) return
  wordStats.value = getWordStats(text)
}

// Chat functions
async function sendChatMessage() {
  if (!chatInput.value.trim() || chatSending.value) return
  const userMsg = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', content: userMsg })
  chatInput.value = ''
  chatSending.value = true

  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }

  try {
    const { send } = useGateway()
    const context = editor.value ? editor.value.getText().substring(0, 500) : ''
    const kbContext = library.value.papers.slice(0, 3).map(p => p.title).join('; ')
    const prompt = kbContext
      ? `[知识库文献: ${kbContext}]\n[当前文稿摘要: ${context}]\n\n用户提问: ${userMsg}`
      : `[当前文稿摘要: ${context}]\n\n用户提问: ${userMsg}`

    send({
      type: 'chat',
      content: prompt,
      callback: (response) => {
        chatMessages.value.push({ role: 'ai', content: response.content || response.text || '处理完成' })
        chatSending.value = false
        nextTick(() => {
          if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
        })
      }
    })
  } catch (err) {
    chatMessages.value.push({ role: 'ai', content: '抱歉，处理请求时出现错误：' + (err.message || '未知错误') })
    chatSending.value = false
  }
}

// Import functions
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

// Toolbar functions
function toggleCitePicker() {
  showCitePicker.value = !showCitePicker.value
  showFigureMenu.value = false
}

function toggleFigureMenu() {
  showFigureMenu.value = !showFigureMenu.value
  showCitePicker.value = false
}

function closeDropdowns() {
  showCitePicker.value = false
  showFigureMenu.value = false
}

function insertCitation(num) {
  if (!editor.value) return
  editor.value.chain().focus().insertContent(`<sup class="cite-ref">[${num}]</sup>`).run()
  closeDropdowns()
}

function insertFormula() {
  if (!editor.value) return
  const formula = prompt('请输入 LaTeX 公式（例如: E = mc^2）：')
  if (!formula?.trim()) return
  editor.value.chain().focus().insertContent({
    type: 'mathFormula',
    attrs: { formula: formula.trim(), displayMode: false },
  }).run()
  closeDropdowns()
}

function insertLink() {
  if (!editor.value) return
  const url = prompt('请输入链接地址：')
  if (!url?.trim()) return
  editor.value.chain().focus().setMark('link', { href: url.trim() }).run()
}

function insertTable() {
  if (!editor.value) return
  editor.value.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  closeDropdowns()
}

// Image functions
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
      `<p class="image-caption" style="text-align:center;font-size:0.78rem;color:#6b7280;margin-top:4px;">${imageCaption.value.trim()}</p><p></p>`
    ).run()
  }
  imageDialogVisible.value = false
}

onMounted(() => {
  analyzeEditorContent(initialContent)
  document.addEventListener('click', closeDropdowns)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeDropdowns)
  editor.value?.destroy()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap');

.writing-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8f8f8;
  color: #121212;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  overflow: hidden;
}

/* ===== Top Header ===== */
.top-header {
  height: 44px;
  background: #fff;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  font-size: 0.72rem;
  color: #9ca3af;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.draft-label {
  color: #121212;
  font-weight: 500;
}
.header-divider {
  color: #d1d5db;
}
.kb-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}
.kb-icon {
  font-size: 0.75rem;
  color: #666666;
}
.header-right {
  font-family: 'Courier New', monospace;
  font-size: 0.68rem;
}
.word-count-num {
  color: #121212;
  font-weight: 700;
}

/* ===== Main Content ===== */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: #ffffff;
}

/* ===== Left: Knowledge Base Panel ===== */
.kb-panel {
  width: 256px;
  background: #fff;
  border-right: 1px solid #eaeaea;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
  flex-shrink: 0;
  overflow: hidden;
}
.kb-panel-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #121212;
  display: flex;
  align-items: center;
  gap: 6px;
}
.kb-title-icon {
  font-size: 0.85rem;
  color: #121212;
}
.btn-import-kb {
  width: 100%;
  background: #fff;
  border: 1px solid #e0e0e0;
  color: #121212;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.btn-import-kb:hover {
  background: #f4f4f4;
}
.btn-icon {
  font-size: 0.85rem;
  color: #666666;
}
.kb-doc-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kb-doc-header {
  font-size: 0.6rem;
  color: #9ca3af;
  letter-spacing: 0.08em;
  font-weight: 600;
  text-transform: uppercase;
}
.kb-doc-card {
  padding: 10px;
  background: #f8f8f8;
  border: 1px solid #eaeaea;
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
}
.kb-doc-card:hover {
  background: #fff;
  border-color: #121212;
}
.kb-doc-card.active {
  background: #f4f4f4;
  border: 2px solid rgba(0,0,0,0.15);
}
.doc-card-title {
  font-size: 0.68rem;
  font-weight: 600;
  color: #121212;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-card-meta {
  font-size: 0.58rem;
  color: #9ca3af;
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
  font-family: 'Courier New', monospace;
}
.kb-doc-card.active .doc-card-meta {
  color: #121212;
}
.doc-card-remove {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 0.65rem;
  color: #9ca3af;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.kb-doc-card:hover .doc-card-remove {
  opacity: 1;
}
.doc-card-remove:hover {
  color: #ef4444;
}
.kb-empty {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: center;
  padding: 24px 8px;
}

/* ===== Center: Editor ===== */
.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fafafa;
  border-right: 1px solid #eaeaea;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.02);
}
.editor-toolbar {
  height: 40px;
  background: #fff;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 4px;
  flex-shrink: 0;
}
.editor-toolbar button {
  width: 28px;
  height: 28px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 0.78rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: inherit;
  transition: all 0.15s;
}
.editor-toolbar button:hover {
  color: #121212;
  background: #f4f4f4;
}
.editor-toolbar button.active {
  color: #121212;
  background: #f4f4f4;
  border-color: #eaeaea;
  font-weight: 700;
}
.editor-toolbar button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.editor-toolbar button:disabled:hover {
  background: transparent;
  color: #9ca3af;
}
.tb-divider {
  width: 1px;
  height: 16px;
  background: #e5e7eb;
  margin: 0 4px;
  flex-shrink: 0;
}

/* Toolbar dropdown */
.toolbar-dropdown-wrap {
  position: relative;
  display: flex;
}
.toolbar-dropdown {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 6px;
  background: #fff;
  border: 1.5px solid #eaeaea;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 100;
  min-width: 220px;
  max-height: 280px;
  overflow-y: auto;
  padding: 4px 0;
}
.dropdown-hd {
  padding: 8px 12px;
  font-size: 0.72rem;
  font-weight: 700;
  color: #121212;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #eaeaea;
}
.dropdown-empty {
  padding: 12px;
  font-size: 0.72rem;
  color: #9ca3af;
  text-align: center;
}
.dropdown-item {
  padding: 7px 12px;
  font-size: 0.75rem;
  color: #121212;
  cursor: pointer;
  transition: 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dropdown-item:hover {
  background: #f4f4f4;
  color: #121212;
}
.cite-idx {
  font-weight: 700;
  color: #121212;
  font-size: 0.72rem;
  flex-shrink: 0;
}

/* Editor canvas */
.editor-canvas {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  display: flex;
  justify-content: center;
}
.paper-page {
  width: 100%;
  max-width: 760px;
  background: #fff;
  min-height: 800px;
  box-shadow: 0 4px 25px rgba(30,39,32,0.06);
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 40px;
}

/* Editor content styles */
.editor-content :deep(.tiptap) {
  outline: none;
  min-height: 100%;
  font-family: 'Noto Serif SC', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 0.82rem;
  line-height: 1.95;
  color: #121212;
  letter-spacing: 0.01em;
  text-align: justify;
}
.editor-content :deep(h2) {
  font-size: 1.15rem;
  font-weight: 700;
  font-family: 'Noto Serif SC', serif;
  color: #121212;
  text-align: center;
  letter-spacing: 0.04em;
  margin-bottom: 2em;
  padding-bottom: 1em;
  border-bottom: 1px solid #f3f4f6;
}
.editor-content :deep(h3) {
  font-size: 0.85rem;
  font-weight: 700;
  color: #121212;
  margin: 1.2em 0 0.5em;
}
.editor-content :deep(p) {
  margin: 0.5em 0;
  color: #333333;
  line-height: 1.85;
}
.editor-content :deep(.cite-ref) {
  color: #121212;
  font-weight: 600;
  font-size: 0.72rem;
  cursor: pointer;
}
.editor-content :deep(.image-resize-wrap) {
  display: inline-block;
  vertical-align: baseline;
  margin: 0.2em 0.4em;
  user-select: none;
}
.editor-content :deep(.image-resize-box) {
  border: 1px solid transparent;
  border-radius: 6px;
}
.editor-content :deep(.image-resize-wrap.is-selected .image-resize-box) {
  outline: 2px solid #121212;
}
.editor-content :deep(.handle) {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #121212;
  border: 1.5px solid #fff;
  border-radius: 2px;
  z-index: 20;
  box-shadow: 0 0 4px rgba(0,0,0,0.25);
}
.editor-content :deep(.handle.se) { bottom: -5px; right: -5px; cursor: se-resize; }
.editor-content :deep(.handle.sw) { bottom: -5px; left: -5px; cursor: sw-resize; }
.editor-content :deep(.handle.ne) { top: -5px; right: -5px; cursor: ne-resize; }
.editor-content :deep(.handle.nw) { top: -5px; left: -5px; cursor: nw-resize; }
.editor-content :deep(.handle.n) { top: -5px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.editor-content :deep(.handle.s) { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.editor-content :deep(.handle.w) { top: 50%; left: -5px; transform: translateY(-50%); cursor: w-resize; }
.editor-content :deep(.handle.e) { top: 50%; right: -5px; transform: translateY(-50%); cursor: e-resize; }
.editor-content :deep(.img-delete-btn) {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e05555;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 30;
  line-height: 1;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.editor-content :deep(.img-delete-btn:hover) {
  background: #c03030;
  transform: scale(1.15);
}
.editor-content :deep(table) {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
  font-size: 0.78rem;
}
.editor-content :deep(th),
.editor-content :deep(td) {
  border: 1.5px solid #eaeaea;
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
  min-width: 60px;
}
.editor-content :deep(th) {
  background: #f4f4f4;
  font-weight: 600;
  color: #121212;
}
.editor-content :deep(.selectedCell) {
  background: rgba(0,0,0,0.06);
}
.editor-content :deep(.column-resize-handle) {
  background: #121212;
  width: 2px;
  position: absolute;
  top: 0;
  bottom: 0;
  right: -1px;
  cursor: col-resize;
}
.editor-content :deep(.math-inline) {
  display: inline;
  vertical-align: middle;
  padding: 1px 4px;
  border-radius: 3px;
}
.editor-content :deep(.math-inline:hover) {
  background: rgba(0,0,0,0.06);
}
.editor-content :deep(.math-block-host) {
  display: block;
  text-align: center;
  margin: 1em 0;
  padding: 12px 16px;
  background: #f4f4f4;
  border: 1px solid #eaeaea;
  border-radius: 6px;
  overflow-x: auto;
}

/* ===== Right: Copilot Panel ===== */
.copilot-panel {
  width: 288px;
  background: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}
.copilot-header {
  padding: 12px 14px;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
  flex-shrink: 0;
}
.copilot-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.copilot-icon {
  width: 20px;
  height: 20px;
  background: #f0f0f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  color: #121212;
}
.copilot-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #121212;
  letter-spacing: 0.02em;
}
.copilot-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.58rem;
  color: #059669;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #d1fae5;
}
.status-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #10b981;
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Chat messages */
.copilot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #ffffff;
}
.chat-msg {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 94%;
}
.chat-msg.user {
  margin-left: auto;
  flex-direction: row-reverse;
}
.msg-avatar {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.58rem;
  font-weight: 700;
  flex-shrink: 0;
}
.msg-avatar.ai {
  background: #121212;
  color: #fff;
}
.msg-avatar.user {
  background: #e8e8e8;
  color: #121212;
}
.msg-bubble {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  line-height: 1.65;
  font-family: 'Noto Serif SC', serif;
}
.msg-bubble.ai {
  background: #f8f8f8;
  border: 1px solid #eaeaea;
  color: #121212;
}
.msg-bubble.user {
  background: #121212;
  color: #fff;
}

/* Copilot input */
.copilot-input-area {
  padding: 10px;
  background: #fff;
  border-top: 1px solid #eaeaea;
  flex-shrink: 0;
}
.copilot-input-box {
  background: #f8f8f8;
  border: 1px solid #eaeaea;
  border-radius: 12px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s;
}
.copilot-input-box:focus-within {
  border-color: #121212;
  background: #fff;
}
.copilot-input-box textarea {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.75rem;
  color: #121212;
  font-family: inherit;
  line-height: 1.5;
  height: 48px;
}
.copilot-input-box textarea::placeholder {
  color: #999999;
}
.copilot-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.input-tools {
  display: flex;
  gap: 6px;
}
.input-tools button {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 2px;
  transition: color 0.15s;
}
.input-tools button:hover {
  color: #121212;
}
.btn-send {
  width: 28px;
  height: 28px;
  background: #121212;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
.btn-send:hover {
  background: #333333;
}
.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Modal Dialogs ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 480px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.modal-header h3 {
  font-size: 0.9rem;
  color: #121212;
  font-weight: 700;
}
.modal-header button {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
}
.modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.format-select {
  display: flex;
  align-items: center;
  gap: 8px;
}
.format-select label {
  font-size: 0.78rem;
  color: #6b7280;
}
.format-select select {
  padding: 6px 10px;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  font-size: 0.78rem;
  background: #fff;
  color: #121212;
}
.modal-body textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  font-size: 0.78rem;
  font-family: monospace;
  background: #f8f8f8;
  color: #121212;
  resize: vertical;
}
.modal-body textarea:focus {
  outline: none;
  border-color: #121212;
}
.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  font-size: 0.78rem;
  background: #f8f8f8;
  color: #121212;
  font-family: inherit;
  outline: none;
}
.input-field:focus {
  border-color: #121212;
}
.image-preview {
  margin-top: 10px;
  text-align: center;
}
.image-preview img {
  max-width: 100%;
  max-height: 160px;
  border-radius: 8px;
  border: 1px solid #eaeaea;
}
.modal-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  justify-content: flex-end;
}
.btn-primary {
  padding: 8px 20px;
  background: #121212;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-primary:hover {
  background: #333333;
}
.btn-secondary {
  padding: 8px 20px;
  background: #fff;
  color: #121212;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-secondary:hover {
  border-color: #121212;
  color: #121212;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.12);
  border-radius: 8px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.2);
}

/* ===== Green Theme ===== */
body.green .writing-app {
  background: #f7f8f7;
  color: #2c332e;
}

body.green .top-header {
  border-bottom-color: #edf0ed;
}

body.green .draft-label {
  color: #526e5a;
}

body.green .kb-icon {
  color: #6b8e76;
}

body.green .word-count-num {
  color: #526e5a;
}

body.green .main-content {
  background: linear-gradient(to bottom, #f5f7f5, #fafbfa);
}

body.green .kb-panel {
  border-right-color: #edf0ed;
}

body.green .kb-panel-title {
  color: #1e2720;
}

body.green .kb-title-icon {
  color: #526e5a;
}

body.green .btn-import-kb {
  border-color: #bad2be;
  color: #526e5a;
}

body.green .kb-doc-header {
  color: #9ca3af;
}

body.green .kb-doc-card {
  background: #f8f9f8;
  border-color: #edf1ed;
}

body.green .kb-doc-card:hover {
  background: #fff;
  border-color: #bad2be;
}

body.green .kb-doc-card.active {
  background: #f2f6f3;
  border-color: rgba(82,110,90,0.3);
}

body.green .doc-card-title {
  color: #1e2720;
}

body.green .editor-section {
  background: #fbfdfb;
  border-right-color: #dee3de;
}

body.green .editor-toolbar {
  border-bottom-color: #dee3de;
}

body.green .editor-toolbar button {
  color: #9ca3af;
}

body.green .editor-toolbar button:hover {
  color: #526e5a;
  background: #f2f4f2;
}

body.green .editor-toolbar button.active {
  color: #526e5a;
  background: #f2f6f3;
  border-color: #dee3de;
}

body.green .tb-divider {
  background: #e5e7eb;
}

body.green .toolbar-dropdown {
  border-color: #edf0ed;
}

body.green .dropdown-hd {
  color: #526e5a;
  border-bottom-color: #edf0ed;
}

body.green .dropdown-item {
  color: #2c332e;
}

body.green .dropdown-item:hover {
  background: #f2f6f3;
  color: #526e5a;
}

body.green .cite-idx {
  color: #526e5a;
}

body.green .paper-page {
  border-color: #dee3de;
}

body.green .editor-content :deep(h2) {
  color: #1e2720;
  border-bottom-color: #f3f4f6;
}

body.green .editor-content :deep(h3) {
  color: #1e2720;
}

body.green .editor-content :deep(p) {
  color: #3b473d;
}

body.green .editor-content :deep(.cite-ref) {
  color: #526e5a;
}

body.green .editor-content :deep(.image-resize-wrap.is-selected .image-resize-box) {
  outline-color: #526e5a;
}

body.green .editor-content :deep(.handle) {
  background: #526e5a;
}

body.green .editor-content :deep(th) {
  background: #f2f6f3;
  color: #526e5a;
}

body.green .editor-content :deep(.selectedCell) {
  background: rgba(82,110,90,0.08);
}

body.green .editor-content :deep(.column-resize-handle) {
  background: #526e5a;
}

body.green .editor-content :deep(.math-inline:hover) {
  background: rgba(82,110,90,0.08);
}

body.green .editor-content :deep(.math-block-host) {
  background: #f2f6f3;
  border-color: #edf0ed;
}

body.green .copilot-panel {
  border-left-color: #edf0ed;
}

body.green .copilot-header {
  background: #fbfdfb;
  border-bottom-color: #edf0ed;
}

body.green .copilot-icon {
  background: #eef3ee;
  color: #526e5a;
}

body.green .copilot-title {
  color: #1e2720;
}

body.green .copilot-status {
  color: #059669;
  background: #ecfdf5;
  border-color: #d1fae5;
}

body.green .copilot-messages {
  background: linear-gradient(to bottom, #fbfdfb, #fff);
}

body.green .msg-avatar.ai {
  background: #526e5a;
  color: #fff;
}

body.green .msg-avatar.user {
  background: #dbe1db;
  color: #1e2720;
}

body.green .msg-bubble.ai {
  background: #f4f6f4;
  border-color: #edf1ed;
  color: #2c332e;
}

body.green .msg-bubble.user {
  background: #526e5a;
  color: #fff;
}

body.green .copilot-input-area {
  border-top-color: #edf0ed;
}

body.green .copilot-input-box {
  background: #f8f9f8;
  border-color: #dee3de;
}

body.green .copilot-input-box:focus-within {
  border-color: #bad2be;
  background: #fff;
}

body.green .copilot-input-box textarea {
  color: #1e2720;
}

body.green .copilot-input-box textarea::placeholder {
  color: #9da79e;
}

body.green .input-tools button {
  color: #9ca3af;
}

body.green .input-tools button:hover {
  color: #526e5a;
}

body.green .btn-send {
  background: #526e5a;
  box-shadow: 0 1px 3px rgba(82,110,90,0.2);
}

body.green .btn-send:hover {
  background: #415848;
}

body.green .modal-content {
  border-color: #dee3de;
}

body.green .modal-header h3 {
  color: #1e2720;
}

body.green .format-select label {
  color: #6b7280;
}

body.green .format-select select {
  border-color: #dee3de;
  color: #2c332e;
}

body.green .modal-body textarea {
  border-color: #dee3de;
  background: #f8f9f8;
  color: #2c332e;
}

body.green .modal-body textarea:focus {
  border-color: #526e5a;
}

body.green .input-field {
  border-color: #dee3de;
  background: #f8f9f8;
  color: #2c332e;
}

body.green .input-field:focus {
  border-color: #526e5a;
}

body.green .image-preview img {
  border-color: #dee3de;
}

body.green .btn-primary {
  background: #526e5a;
}

body.green .btn-primary:hover {
  background: #415848;
}

body.green .btn-secondary {
  color: #2c332e;
  border-color: #dee3de;
}

body.green .btn-secondary:hover {
  border-color: #526e5a;
  color: #526e5a;
}

/* ===== Dark Theme ===== */
body.dark .writing-app {
  background: #121212;
  color: #e5e5e5;
}

body.dark .top-header {
  background: #1a1a1a;
  border-bottom-color: #2d2d2d;
  color: #999999;
}

body.dark .draft-label {
  color: #b3b3b3;
}

body.dark .header-divider {
  color: #333333;
}

body.dark .word-count-num {
  color: #ffffff;
}

body.dark .main-content {
  background: linear-gradient(to bottom, #141414, #121212);
}

body.dark .kb-panel {
  background: #1a1a1a;
  border-right-color: #2d2d2d;
}

body.dark .kb-panel-title {
  color: #e5e5e5;
}

body.dark .kb-title-icon {
  color: #ffffff;
}

body.dark .btn-import-kb {
  background: #242424;
  border-color: #333333;
  color: #b3b3b3;
}

body.dark .btn-import-kb:hover {
  background: #2d2d2d;
}

body.dark .btn-icon {
  color: #ffffff;
}

body.dark .kb-doc-header {
  color: #666666;
}

body.dark .kb-doc-card {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .kb-doc-card:hover {
  background: #2d2d2d;
  border-color: #444444;
}

body.dark .kb-doc-card.active {
  background: #1a1a1a;
  border-color: rgba(255,255,255,0.3);
}

body.dark .doc-card-title {
  color: #e5e5e5;
}

body.dark .doc-card-meta {
  color: #666666;
}

body.dark .kb-doc-card.active .doc-card-meta {
  color: #b3b3b3;
}

body.dark .kb-empty {
  color: #666666;
}

body.dark .editor-section {
  background: #141414;
  border-right-color: #2d2d2d;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
}

body.dark .editor-toolbar {
  background: #1a1a1a;
  border-bottom-color: #2d2d2d;
}

body.dark .editor-toolbar button {
  color: #999999;
}

body.dark .editor-toolbar button:hover {
  color: #ffffff;
  background: #2d2d2d;
}

body.dark .editor-toolbar button.active {
  color: #ffffff;
  background: #333333;
  border-color: #444444;
}

body.dark .tb-divider {
  background: #333333;
}

body.dark .toolbar-dropdown {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .dropdown-hd {
  color: #b3b3b3;
  border-bottom-color: #2d2d2d;
}

body.dark .dropdown-empty {
  color: #666666;
}

body.dark .dropdown-item {
  color: #e5e5e5;
}

body.dark .dropdown-item:hover {
  background: #2d2d2d;
  color: #ffffff;
}

body.dark .cite-idx {
  color: #ffffff;
}

body.dark .paper-page {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 4px 25px rgba(0,0,0,0.3);
}

body.dark .editor-content :deep(.tiptap) {
  color: #e5e5e5;
}

body.dark .editor-content :deep(h2) {
  color: #ffffff;
  border-bottom-color: #333333;
}

body.dark .editor-content :deep(h3) {
  color: #ffffff;
}

body.dark .editor-content :deep(p) {
  color: #b3b3b3;
}

body.dark .editor-content :deep(.cite-ref) {
  color: #ffffff;
}

body.dark .editor-content :deep(.image-resize-wrap.is-selected .image-resize-box) {
  outline-color: #ffffff;
}

body.dark .editor-content :deep(.handle) {
  background: #ffffff;
  border-color: #242424;
}

body.dark .editor-content :deep(th),
body.dark .editor-content :deep(td) {
  border-color: #333333;
}

body.dark .editor-content :deep(th) {
  background: #1a1a1a;
  color: #b3b3b3;
}

body.dark .editor-content :deep(.selectedCell) {
  background: rgba(255,255,255,0.08);
}

body.dark .editor-content :deep(.column-resize-handle) {
  background: #ffffff;
}

body.dark .editor-content :deep(.math-inline:hover) {
  background: rgba(255,255,255,0.08);
}

body.dark .editor-content :deep(.math-block-host) {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

body.dark .copilot-panel {
  background: #1a1a1a;
}

body.dark .copilot-header {
  background: #141414;
  border-bottom-color: #2d2d2d;
}

body.dark .copilot-icon {
  background: #2d2d2d;
  color: #ffffff;
}

body.dark .copilot-title {
  color: #ffffff;
}

body.dark .copilot-status {
  color: #10b981;
  background: #0a2520;
  border-color: #0d3b2e;
}

body.dark .status-dot {
  background: #10b981;
}

body.dark .copilot-messages {
  background: linear-gradient(to bottom, #141414, #1a1a1a);
}

body.dark .msg-avatar.ai {
  background: #ffffff;
  color: #121212;
}

body.dark .msg-avatar.user {
  background: #333333;
  color: #e5e5e5;
}

body.dark .msg-bubble.ai {
  background: #242424;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .msg-bubble.user {
  background: #333333;
  color: #ffffff;
}

body.dark .copilot-input-area {
  background: #1a1a1a;
  border-top-color: #2d2d2d;
}

body.dark .copilot-input-box {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .copilot-input-box:focus-within {
  border-color: #444444;
  background: #1a1a1a;
}

body.dark .copilot-input-box textarea {
  color: #e5e5e5;
}

body.dark .copilot-input-box textarea::placeholder {
  color: #666666;
}

body.dark .input-tools button {
  color: #999999;
}

body.dark .input-tools button:hover {
  color: #ffffff;
}

body.dark .btn-send {
  background: #ffffff;
  color: #121212;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

body.dark .btn-send:hover {
  background: #e5e5e5;
}

body.dark .modal-overlay {
  background: rgba(0,0,0,0.6);
}

body.dark .modal-content {
  background: #242424;
  border-color: #2d2d2d;
}

body.dark .modal-header h3 {
  color: #ffffff;
}

body.dark .modal-header button {
  color: #999999;
}

body.dark .format-select label {
  color: #999999;
}

body.dark .format-select select {
  background: #1a1a1a;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .modal-body textarea {
  background: #1a1a1a;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .modal-body textarea:focus {
  border-color: #ffffff;
}

body.dark .input-field {
  background: #1a1a1a;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

body.dark .input-field:focus {
  border-color: #ffffff;
}

body.dark .image-preview img {
  border-color: #2d2d2d;
}

body.dark .btn-primary {
  background: #ffffff;
  color: #121212;
}

body.dark .btn-primary:hover {
  background: #e5e5e5;
}

body.dark .btn-secondary {
  background: #242424;
  color: #e5e5e5;
  border-color: #2d2d2d;
}

body.dark .btn-secondary:hover {
  border-color: #ffffff;
  color: #ffffff;
}

body.dark ::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
}

body.dark ::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.2);
}
</style>
