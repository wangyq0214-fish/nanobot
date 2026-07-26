<template>
  <div class="latex-page">
    <header class="topbar">
      <div class="title">
        <h1>LaTeX 学术写作</h1>
        <span>{{ fileName ? `${fileName}.tex` : '未命名文档' }}</span>
        <em v-if="savingFile">同步中...</em>
      </div>
      <div class="actions">
        <button @click="createNewFile">新建</button>
        <button @click="loadFileList(true)" :disabled="loadingFile">打开</button>
        <button @click="triggerFileInput">附件 {{ attachments.length ? `(${attachments.length})` : '' }}</button>
        <input ref="fileInput" hidden type="file" multiple accept="image/*,.bib,.sty,.cls" @change="handleFileChange" />
        <button class="primary" @click="handleCompile" :disabled="compiling || !latexCode.trim()">
          {{ compiling ? '编译中...' : '编译 PDF' }}
        </button>
        <button v-if="pdfUrl" class="success" @click="downloadPdf(`${fileName || 'output'}.pdf`)">下载</button>
      </div>
    </header>

    <main class="main">
      <section class="work">
        <div v-if="attachments.length" class="attachments">
          <span v-for="(file, idx) in attachments" :key="`${file.name}_${idx}`">
            {{ file.name }} <button @click="removeAttachment(idx)">×</button>
          </span>
        </div>
        <div class="split">
          <div class="editor">
            <MonacoEditor
              v-model:value="latexCode"
              language="latex"
              :theme="editorTheme"
              :options="editorOptions"
              @beforeMount="defineMonacoTheme"
              @mount="handleEditorMount"
              @change="onCodeChange"
            />
          </div>
          <div class="preview">
            <div class="preview-head">
              <strong>PDF 预览</strong>
              <span v-if="pdfUrl">编译成功</span>
            </div>
            <div v-if="compileError" class="error">
              <strong>{{ compileError }}</strong>
              <pre v-if="compileLog">{{ compileLog }}</pre>
            </div>
            <div v-else-if="pdfUrl" class="pdf">
              <VuePdfEmbed :source="pdfSource" :width="760" />
            </div>
            <div v-else class="empty">点击“编译 PDF”后在这里预览</div>
          </div>
        </div>
      </section>

      <aside class="chat" :style="{ width: copilotWidth + 'px' }">
        <header>
          <strong>AI 学术助手</strong>
          <i :class="{ on: connected }"></i>
        </header>
        <div ref="chatContainer" class="messages">
          <div v-for="(msg, idx) in visibleMessages" :key="msg.id || idx" :class="['msg', msg.role]">
            <template v-if="msg.role === 'aux_group'">
              <div class="bubble trace">
                <div v-for="item in msg.items" :key="item.id || item.content?.slice(0, 20)">
                  <button @click="item.collapsed = !item.collapsed">
                    {{ item.collapsed ? '展开' : '收起' }} {{ item.name || (item.reasoning ? 'reasoning' : item.role) }}
                  </button>
                  <div v-if="!item.collapsed" v-html="renderMarkdown(item.content)"></div>
                </div>
              </div>
            </template>
            <template v-else>
              <b>{{ msg.role === 'user' ? '你' : 'AI' }}</b>
              <div class="bubble" v-html="renderMarkdown(msg.content || '')"></div>
            </template>
          </div>
        </div>
        <footer>
          <textarea
            v-model="chatInput"
            rows="3"
            :disabled="!connected"
            placeholder="让 AI 直接修改当前编辑器内容..."
            @keydown.enter.exact.prevent="sendChat"
          ></textarea>
          <button class="primary" @click="sendChat" :disabled="chatLoading || !chatInput.trim() || !connected">
            {{ chatLoading ? '发送中...' : '发送' }}
          </button>
        </footer>
      </aside>
    </main>

    <div v-if="showFileBrowser" class="mask" @click.self="showFileBrowser = false">
      <div class="dialog">
        <header><strong>打开 LaTeX 文件</strong><button @click="showFileBrowser = false">×</button></header>
        <p v-if="loadingFileList">加载中...</p>
        <button v-for="file in availableFiles" :key="file.id" class="file" @click="loadFromFile(file)">
          {{ file.title || file.fileName }}
        </button>
        <p v-if="!loadingFileList && !availableFiles.length">暂无 .tex 文件</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import MonacoEditor from '@guolao/vue-monaco-editor'
import VuePdfEmbed from 'vue-pdf-embed'
import { useLatexCompiler } from '../../composables/useLatexCompiler.js'
import { useGateway } from '../../composables/useGateway.js'
import { useAuth } from '../../composables/useAuth.js'
import { useSessions } from '../../composables/useSessions.js'
import { useLatexDrafts } from '../../composables/useLatexDrafts.js'

const { compiling, compileError, compileLog, pdfUrl, compileLatex, downloadPdf, cleanup } = useLatexCompiler()
const { sendMessage, onChat, connected, getToken } = useGateway()
const { user } = useAuth()
const { fetchSessionMessages } = useSessions()
const { fetchLatexDrafts, fetchLatexDraft, fetchLatexDraftVersions, saveLatexDraft, createLatexCompileRecord } = useLatexDrafts()

const latexCode = ref('')
const fileName = ref('')
const saveFilePath = ref('')
const currentDraftId = ref(null)
const currentDraftVersion = ref(null)
const savingFile = ref(false)
const loadingFile = ref(false)
const loadingFileList = ref(false)
const availableFiles = ref([])
const showFileBrowser = ref(false)
const attachments = ref([])
const fileInput = ref(null)
const currentTheme = ref('white')
const copilotWidth = ref(320)
const chatInput = ref('')
const chatLoading = ref(false)
const chatContainer = ref(null)
const writingChatId = ref('')
const welcome = '你好，我是 AI 学术助手。这里的对话只属于学术写作助手，不会并入研者端主对话。你可以让我直接修改当前 LaTeX 编辑器内容。'
const chatMessages = ref([{ role: 'assistant', content: welcome }])

let editorInstance = null
let unsubChat = null
let subscribedChatId = null
let activeStreamId = null
let activeAiMessageId = null
let saveTimer = null
let historyLoadSeq = 0
let fileListCache = null
let fileListCacheTime = 0
const fileContentCache = new Map()

const editorTheme = computed(() => currentTheme.value === 'dark' ? 'custom-dark' : currentTheme.value === 'green' ? 'custom-green' : 'custom-light')
const editorOptions = computed(() => ({ minimap: { enabled: false }, fontSize: 14, wordWrap: 'on', lineNumbers: 'on', scrollBeyondLastLine: false, automaticLayout: true }))
const pdfSource = computed(() => pdfUrl.value ? { url: pdfUrl.value, cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/', cMapPacked: true } : null)
const visibleMessages = computed(() => {
  const grouped = []
  let active = null
  for (const msg of chatMessages.value) {
    if (msg.role === 'tool' || msg.reasoning) {
      if (!active) {
        active = { role: 'aux_group', items: [] }
        grouped.push(active)
      }
      active.items.push(msg)
    } else {
      active = null
      grouped.push(msg)
    }
  }
  return grouped
})

function renderMarkdown(text) {
  return marked.parse(text || '')
}

function defineMonacoTheme(monaco) {
  monaco.editor.defineTheme('custom-dark', { base: 'vs-dark', inherit: true, rules: [], colors: { 'editor.background': '#1e1e1e' } })
  monaco.editor.defineTheme('custom-light', { base: 'vs', inherit: true, rules: [], colors: { 'editor.background': '#ffffff' } })
  monaco.editor.defineTheme('custom-green', { base: 'vs', inherit: true, rules: [], colors: { 'editor.background': '#f7f8f7' } })
}

function handleEditorMount(editor) {
  editorInstance = editor
}

function writingChatStorageKey() {
  return `nanobot_latex_chat_id.researcher.${user.value?.userId || 'anonymous'}`
}

function ensureWritingChatId() {
  if (writingChatId.value) return writingChatId.value
  const key = writingChatStorageKey()
  let stored = ''
  try { stored = localStorage.getItem(key) || '' } catch {}
  const raw = crypto?.randomUUID?.() || `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
  writingChatId.value = stored || `latex_${raw.replace(/[^A-Za-z0-9_-]/g, '_')}`
  try { localStorage.setItem(key, writingChatId.value) } catch {}
  return writingChatId.value
}

function stopChatListener() {
  if (unsubChat) unsubChat()
  unsubChat = null
  subscribedChatId = null
  activeStreamId = null
  activeAiMessageId = null
}

function ensureChatListener(chatId = ensureWritingChatId()) {
  if (!chatId || (subscribedChatId === chatId && unsubChat)) return
  stopChatListener()
  subscribedChatId = chatId
  unsubChat = onChat(chatId, handleChatResponse)
}

async function loadHistory(chatId = ensureWritingChatId()) {
  chatMessages.value = [{ role: 'assistant', content: welcome }]
  const seq = ++historyLoadSeq
  try {
    const data = await fetchSessionMessages(`websocket:${chatId}`, 'researcher', user.value?.userId, getToken())
    if (seq !== historyLoadSeq || chatId !== writingChatId.value) return
    const history = (data?.messages || []).flatMap(mapSessionMessage).filter(Boolean)
    if (history.length) chatMessages.value = history
  } catch {}
  scrollToBottom()
  ensureChatListener(chatId)
}

function mapSessionMessage(m) {
  if (m.role === 'user') return [{ role: 'user', content: stringifyContent(m.content) }]
  if (m.role === 'assistant') {
    const content = stringifyContent(m.content).trim()
    const reasoning = stringifyContent(m.reasoning_content).trim()
    return [
      reasoning ? { role: 'assistant', content: reasoning, reasoning: true, collapsed: true } : null,
      content || !reasoning ? { role: 'assistant', content } : null,
    ].filter(Boolean)
  }
  if (m.role === 'tool') return [{ role: 'tool', name: m.name || 'tool', content: stringifyContent(m.content), collapsed: true }]
  return []
}

function stringifyContent(content) {
  if (Array.isArray(content)) return content.map(c => c.text || c.content || '').join('')
  return content || ''
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  })
}

function sanitizeLatexBaseName(value) {
  return String(value || '')
    .trim()
    .replace(/\.tex$/i, '')
    .replace(/[\\/:*?"<>|]/g, '_')
}

function timestampName() {
  const d = new Date()
  const pad = value => String(value).padStart(2, '0')
  return `document-${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
}

function uniqueLatexBaseName(baseName, existingNames) {
  const cleanBase = sanitizeLatexBaseName(baseName) || timestampName()
  let candidate = cleanBase
  let idx = 2
  while (existingNames.has(`${candidate}.tex`.toLowerCase())) {
    candidate = `${cleanBase}-${idx}`
    idx += 1
  }
  return candidate
}

async function existingLatexFileNames() {
  await loadFileList(false)
  return new Set((availableFiles.value || []).map(file => String(file.fileName || '').toLowerCase()).filter(Boolean))
}

async function createNewFile() {
  const existingNames = await existingLatexFileNames()
  const defaultName = uniqueLatexBaseName(timestampName(), existingNames)
  const name = sanitizeLatexBaseName(prompt('请输入文件名（不含扩展名）', defaultName))
  if (!name) return
  const filePath = `${name}.tex`
  if (existingNames.has(filePath.toLowerCase())) {
    alert(`已存在 ${filePath}，请用“打开”继续编辑，或换一个新文件名。`)
    return
  }
  const content = `\\documentclass[12pt,a4paper]{article}
\\usepackage{graphicx}
\\usepackage{amsmath}
\\usepackage[UTF8, heading=true]{ctex}

\\title{论文标题}
\\author{作者姓名}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
摘要内容
\\end{abstract}

\\section{引言}
正文内容

\\end{document}`
  latexCode.value = content
  saveFilePath.value = filePath
  fileName.value = name
  currentDraftId.value = null
  currentDraftVersion.value = null
  fileListCache = null
  localStorage.setItem('nanobot_latex_file_path', filePath)
  await persistCurrentDraft('manual')
  void loadFileList(false)
}

function buildDraftPayload(changeSource = 'autosave') {
  const baseName = fileName.value || saveFilePath.value?.replace(/\.tex$/i, '') || 'document'
  const texName = saveFilePath.value || `${baseName}.tex`
  return {
    draftId: currentDraftId.value,
    title: baseName,
    fileName: texName,
    content: latexCode.value,
    chatId: writingChatId.value || ensureWritingChatId(),
    status: 'draft',
    metadata: {
      source: 'latex-writing-editor',
      attachmentNames: attachments.value.map(file => file.name),
    },
    changeSource,
  }
}

async function persistCurrentDraft(changeSource = 'autosave') {
  if (!saveFilePath.value) {
    fileName.value = fileName.value || 'document'
    saveFilePath.value = `${fileName.value}.tex`
  }
  savingFile.value = true
  try {
    const data = await saveLatexDraft(buildDraftPayload(changeSource))
    const draft = data?.data
    if (draft?.id) {
      currentDraftId.value = draft.id
      currentDraftVersion.value = draft.currentVersion || currentDraftVersion.value
      fileName.value = (draft.title || draft.fileName || fileName.value).replace(/\.tex$/i, '')
      saveFilePath.value = draft.fileName || saveFilePath.value
      fileContentCache.set(String(draft.id), draft.content || latexCode.value)
      localStorage.setItem('nanobot_latex_draft_id', String(draft.id))
      localStorage.setItem('nanobot_latex_file_path', saveFilePath.value)
      fileListCache = null
    }
    return draft
  } catch (err) {
    console.warn('Failed to save LaTeX draft:', err)
    return null
  } finally {
    setTimeout(() => { savingFile.value = false }, 500)
  }
}

function autoSave() {
  if (!saveFilePath.value || !connected.value) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    void persistCurrentDraft('autosave')
  }, 1000)
}

function onCodeChange() {
  autoSave()
}

async function loadFileList(showBrowser = false) {
  try {
    const now = Date.now()
    if (fileListCache && now - fileListCacheTime < 30000) {
      availableFiles.value = fileListCache
      if (showBrowser) showFileBrowser.value = true
      return
    }
    loadingFileList.value = true
    if (showBrowser) showFileBrowser.value = true
    const data = await fetchLatexDrafts()
    const files = data.data || []
    fileListCache = files
    fileListCacheTime = now
    availableFiles.value = files
  } finally {
    loadingFileList.value = false
  }
}

async function loadFromFile(file) {
  loadingFile.value = true
  try {
    const draftId = file?.id
    let content = fileContentCache.get(String(draftId))
    let draft = file
    if (content === undefined) {
      const data = await fetchLatexDraft(draftId)
      draft = data.data || file
      content = draft.content || ''
      fileContentCache.set(String(draftId), content)
    }
    latexCode.value = content
    currentDraftId.value = draftId
    currentDraftVersion.value = draft.currentVersion || null
    saveFilePath.value = draft.fileName || `${draft.title || 'document'}.tex`
    fileName.value = (draft.title || draft.fileName || 'document').replace(/\.tex$/i, '')
    localStorage.setItem('nanobot_latex_draft_id', String(draftId))
    localStorage.setItem('nanobot_latex_file_path', saveFilePath.value)
    showFileBrowser.value = false
  } finally {
    loadingFile.value = false
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e) {
  attachments.value.push(...Array.from(e.target.files || []))
  if (fileInput.value) fileInput.value.value = ''
}

function removeAttachment(idx) {
  attachments.value.splice(idx, 1)
}

async function handleCompile() {
  const draft = await persistCurrentDraft('compile')
  const draftId = draft?.id || currentDraftId.value
  const result = await compileLatex(latexCode.value, attachments.value)
  const ok = result === true || result?.success === true
  if (result?.texCode && result.texCode !== latexCode.value) {
    latexCode.value = result.texCode
    if (editorInstance?.setValue && editorInstance.getValue?.() !== latexCode.value) editorInstance.setValue(latexCode.value)
    void persistCurrentDraft('compile-normalized')
  }
  if (draftId) {
    try {
      let versionId = null
      const versionNumber = draft?.currentVersion || currentDraftVersion.value
      try {
        const versionData = await fetchLatexDraftVersions(draftId)
        const versions = versionData?.data || []
        const currentVersion = versions.find(item => item.versionNumber === versionNumber)
        versionId = currentVersion?.id || null
      } catch {}
      await createLatexCompileRecord({
        draftId,
        versionId,
        status: ok ? 'success' : 'failed',
        engine: 'xelatex',
        log: compileLog.value || compileError.value || '',
        outputName: ok ? `${fileName.value || 'output'}.pdf` : '',
        metadata: {
          attachmentNames: attachments.value.map(file => file.name),
          source: 'latex-writing-editor',
        },
      })
    } catch (err) {
      console.warn('Failed to save LaTeX compile record:', err)
    }
  }
  return ok
}

async function sendChat() {
  const msg = chatInput.value.trim()
  if (!msg || chatLoading.value) return
  const chatId = ensureWritingChatId()
  chatMessages.value.push({ role: 'user', content: msg })
  chatInput.value = ''
  chatLoading.value = true
  const pendingId = `ai_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  activeAiMessageId = pendingId
  activeStreamId = null
  chatMessages.value.push({ id: pendingId, role: 'assistant', content: '', loading: true })
  scrollToBottom()
  ensureChatListener(chatId)
  try {
    if (!saveFilePath.value) {
      saveFilePath.value = `${fileName.value || 'document'}.tex`
      fileName.value = fileName.value || 'document'
      localStorage.setItem('nanobot_latex_file_path', saveFilePath.value)
    }
    sendMessage(msg, { _skill: 'latex-writing', latex_code: latexCode.value, file_path: saveFilePath.value, isolated_context: 'latex-writing' }, chatId)
  } catch (err) {
    const last = chatMessages.value[chatMessages.value.length - 1]
    if (last) {
      last.content = 'Send failed: ' + err.message
      last.loading = false
    }
    chatLoading.value = false
  }
}

const EDIT_BLOCK_RE = /```(?:latex-editor|editor-action)\s*([\s\S]*?)```/gi
const LATEX_CODE_BLOCK_RE = /```(?:latex|tex)\s*([\s\S]*?)```/gi

function parseEditorActions(text) {
  const actions = []
  let match
  EDIT_BLOCK_RE.lastIndex = 0
  while ((match = EDIT_BLOCK_RE.exec(text || '')) !== null) {
    try {
      const payload = JSON.parse(match[1].trim())
      if (Array.isArray(payload)) actions.push(...payload)
      else if (Array.isArray(payload.actions)) actions.push(...payload.actions)
      else if (payload.action) actions.push(payload)
    } catch (err) {
      console.warn('Invalid latex editor action block:', err)
    }
  }
  return actions
}

function extractCompleteLatexDocument(text) {
  LATEX_CODE_BLOCK_RE.lastIndex = 0
  let match
  while ((match = LATEX_CODE_BLOCK_RE.exec(text || '')) !== null) {
    const content = nl(match[1]).trim()
    if (/\\documentclass(?:\[[^\]]*\])?\{[^}]+\}/.test(content) && content.includes('\\begin{document}') && content.includes('\\end{document}')) {
      return content
    }
  }
  return ''
}

function stripEditorActions(text) {
  return (text || '').replace(EDIT_BLOCK_RE, '').trim()
}

function nl(value) {
  return String(value ?? '').replace(/\r\n/g, '\n')
}

function applyOneEditorAction(action) {
  const current = nl(latexCode.value)
  const type = action?.action
  if (type === 'get' || type === 'structure') {
    return { ok: true }
  }
  if (type === 'set') {
    latexCode.value = nl(action.content)
    return { ok: true }
  }
  if (type === 'append') {
    const content = nl(action.content)
    latexCode.value = current + (current.endsWith('\n') || !current ? '' : '\n') + content
    return { ok: true }
  }
  if (type === 'prepend') {
    const content = nl(action.content)
    latexCode.value = content + (content.endsWith('\n') || !current ? '' : '\n') + current
    return { ok: true }
  }
  if (type === 'replace') {
    const search = nl(action.search)
    if (!search || !current.includes(search)) return { ok: false, message: 'replace target not found' }
    latexCode.value = current.replace(search, nl(action.replace ?? action.content))
    return { ok: true }
  }
  if (type === 'insert_after' || type === 'insert_before') {
    const anchor = nl(action.anchor)
    const content = nl(action.content)
    const idx = current.indexOf(anchor)
    if (!anchor || idx < 0) return { ok: false, message: `${type} anchor not found` }
    const at = type === 'insert_after' ? idx + anchor.length : idx
    const before = current.slice(0, at)
    const after = current.slice(at)
    latexCode.value = before + (before.endsWith('\n') || content.startsWith('\n') ? '' : '\n') + content + (content.endsWith('\n') || after.startsWith('\n') ? '' : '\n') + after
    return { ok: true }
  }
  if (type === 'insert_line') {
    const line = Number(action.line)
    if (!Number.isInteger(line) || line < 1) return { ok: false, message: 'insert_line requires a one-based line number' }
    const lines = current.split('\n')
    const at = Math.min(line - 1, lines.length)
    lines.splice(at, 0, nl(action.content))
    latexCode.value = lines.join('\n')
    return { ok: true }
  }
  if (type === 'delete_line') {
    const line = Number(action.line)
    const lines = current.split('\n')
    if (!Number.isInteger(line) || line < 1 || line > lines.length) return { ok: false, message: 'delete_line target not found' }
    lines.splice(line - 1, 1)
    latexCode.value = lines.join('\n')
    return { ok: true }
  }
  return { ok: false, message: `unknown action: ${type}` }
}

async function applyEditorActions(actions, { visibleMessage = null } = {}) {
  if (!actions.length) return
  const results = actions.map(applyOneEditorAction)
  const applied = results.filter(r => r.ok).length
  const failed = results.filter(r => !r.ok).map(r => r.message)
  if (visibleMessage) {
    const visible = stripEditorActions(visibleMessage.content)
    visibleMessage.content = `${visible ? visible + '\n\n' : ''}Applied ${applied} editor action(s).`
    if (failed.length) visibleMessage.content += `\n\nSkipped: ${failed.join('; ')}`
  } else {
    chatMessages.value.push({
      role: failed.length ? 'tool' : 'assistant',
      name: 'latex_editor',
      content: failed.length ? `Applied ${applied} editor action(s). Skipped: ${failed.join('; ')}` : `Applied ${applied} editor action(s).`,
      collapsed: true,
    })
  }
  autoSave()
  if (editorInstance?.setValue && editorInstance.getValue?.() !== latexCode.value) editorInstance.setValue(latexCode.value)
  if (actions.some(a => a.compile === true)) await handleCompile()
  scrollToBottom()
}

async function applyEditorActionsFromMessage(message) {
  let actions = parseEditorActions(message.content)
  if (!actions.length) {
    const fullDocument = extractCompleteLatexDocument(message.content)
    if (fullDocument) actions = [{ action: 'set', content: fullDocument }]
  }
  if (!actions.length) return
  await applyEditorActions(actions, { visibleMessage: message })
}

function pushTraceMessage(ev, text) {
  const isReasoning = !!ev.reasoning
  const role = ev.role === 'tool' ? 'tool' : 'assistant'
  const name = ev.name || (isReasoning ? 'reasoning' : role)
  const last = chatMessages.value[chatMessages.value.length - 1]
  if (isReasoning && last?.reasoning && last.role === role) {
    last.content += text
    return
  }
  chatMessages.value.push({
    role,
    name,
    content: text,
    reasoning: isReasoning,
    collapsed: true,
  })
}

function handleChatResponse(ev) {
  if (ev.event === 'latex_editor_action') {
    const { event, chat_id: _chatId, ...action } = ev
    applyEditorActions([action])
    return
  }
  if (ev.event === 'delta') {
    const streamId = ev.stream_id || '__default_stream__'
    activeStreamId = streamId
    if (!activeAiMessageId) {
      activeAiMessageId = `ai_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      chatMessages.value.push({ id: activeAiMessageId, role: 'assistant', content: '', loading: true })
    }
    const msg = chatMessages.value.find(m => m.id === activeAiMessageId)
    if (msg) msg.content += ev.text || ''
    scrollToBottom()
    return
  }
  if (ev.event === 'stream_end') {
    const target = activeAiMessageId ? chatMessages.value.find(m => m.id === activeAiMessageId) : chatMessages.value[chatMessages.value.length - 1]
    if (target) {
      target.loading = false
      applyEditorActionsFromMessage(target)
    }
    chatLoading.value = false
    activeStreamId = null
    activeAiMessageId = null
    scrollToBottom()
    return
  }
  if (ev.event === 'message') {
    const text = ev.text || ev.content || ''
    if (!text) return
    if (ev.kind === 'trace') {
      pushTraceMessage(ev, text)
      scrollToBottom()
      return
    }
    const target = activeAiMessageId ? chatMessages.value.find(m => m.id === activeAiMessageId) : chatMessages.value[chatMessages.value.length - 1]
    if (target && target.role === 'assistant' && target.loading) {
      target.content = text
      target.loading = false
      applyEditorActionsFromMessage(target)
    } else {
      const message = { role: 'assistant', content: text }
      chatMessages.value.push(message)
      applyEditorActionsFromMessage(message)
    }
    chatLoading.value = false
    activeStreamId = null
    activeAiMessageId = null
    scrollToBottom()
  }
}

onMounted(async () => {
  ensureWritingChatId()
  const savedDraftId = localStorage.getItem('nanobot_latex_draft_id')
  const savedPath = localStorage.getItem('nanobot_latex_file_path')
  if (savedDraftId) {
    try {
      const data = await fetchLatexDraft(savedDraftId)
      const draft = data?.data
      if (draft) {
        await loadFromFile(draft)
      }
    } catch {
      localStorage.removeItem('nanobot_latex_draft_id')
    }
  } else if (savedPath) {
    saveFilePath.value = savedPath
    fileName.value = savedPath.split('/').pop().replace('.tex', '')
    try {
      const data = await fetchLatexDrafts()
      const draft = (data?.data || []).find(item => item.fileName === savedPath)
      if (draft) await loadFromFile(draft)
    } catch {}
  }
  const savedTheme = localStorage.getItem('nanobot-theme')
  if (['white', 'dark', 'green'].includes(savedTheme)) currentTheme.value = savedTheme
  const savedWidth = localStorage.getItem('nanobot_copilot_width')
  if (savedWidth) copilotWidth.value = parseInt(savedWidth) || 320
  loadHistory()
  loadFileList()
})

onUnmounted(() => {
  cleanup()
  stopChatListener()
})
</script>

<style scoped>
.latex-page { height: 100vh; display: flex; flex-direction: column; color: #121212; background: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.topbar { height: 50px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-bottom: 1px solid #e6e6e6; background: #f8f9f8; }
.title, .actions, .attachments, .preview-head, .chat header { display: flex; align-items: center; gap: 8px; }
h1 { margin: 0; font-size: 18px; }
.title span, .title em { padding: 4px 8px; border-radius: 6px; background: #eee; font-size: 12px; color: #666; font-style: normal; }
button { border: 1px solid #ddd; background: #f4f4f4; color: #121212; border-radius: 6px; padding: 7px 11px; cursor: pointer; font: inherit; font-size: 13px; }
button:disabled { opacity: .45; cursor: not-allowed; }
button.primary { background: #0078d4; border-color: #0078d4; color: #fff; }
button.success { background: #2ea043; border-color: #2ea043; color: #fff; }
.main { flex: 1; min-height: 0; display: flex; overflow: hidden; }
.work { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.attachments { padding: 8px 12px; border-bottom: 1px solid #e6e6e6; background: #f8f9f8; flex-wrap: wrap; }
.attachments span { padding: 3px 8px; border-radius: 6px; background: #eee; font-size: 12px; }
.attachments button { border: 0; background: transparent; padding: 0 0 0 4px; color: #d92d20; }
.split { flex: 1; min-height: 0; display: flex; }
.editor, .preview { flex: 1; min-width: 0; }
.editor { border-right: 1px solid #e6e6e6; }
.preview { display: flex; flex-direction: column; }
.preview-head { height: 36px; justify-content: space-between; padding: 0 14px; border-bottom: 1px solid #e6e6e6; background: #f8f9f8; font-size: 13px; }
.preview-head span { color: #2ea043; }
.pdf { flex: 1; overflow: auto; padding: 24px; display: flex; justify-content: center; }
.empty { flex: 1; display: flex; align-items: center; justify-content: center; color: #777; }
.error { margin: 14px; padding: 12px; border: 1px solid #d92d20; border-radius: 8px; color: #b42318; background: #fff4f4; }
.error pre { white-space: pre-wrap; max-height: 240px; overflow: auto; font-size: 11px; }
.chat { flex-shrink: 0; min-width: 280px; max-width: 560px; display: flex; flex-direction: column; border-left: 1px solid #e6e6e6; background: #f8f9f8; }
.chat header { height: 36px; justify-content: space-between; padding: 0 12px; border-bottom: 1px solid #e6e6e6; }
.chat i { width: 8px; height: 8px; border-radius: 50%; background: #d92d20; }
.chat i.on { background: #2ea043; }
.messages { flex: 1; overflow: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.msg { display: flex; align-items: flex-start; gap: 8px; }
.msg.user { flex-direction: row-reverse; }
.msg > b { width: 30px; height: 30px; border-radius: 10px; background: #eee; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
.bubble { max-width: 86%; padding: 10px 12px; border: 1px solid #e6e6e6; border-radius: 12px; background: #fff; font-size: 13px; line-height: 1.65; word-break: break-word; }
.msg.user .bubble { background: #121212; color: #fff; border-color: #121212; }
.trace { color: #666; font-size: 12px; }
.trace button { border: 0; background: transparent; padding: 0; color: #666; }
.chat footer { padding: 12px; border-top: 1px solid #e6e6e6; display: flex; flex-direction: column; gap: 8px; }
textarea { resize: none; min-height: 70px; border: 1px solid #ddd; border-radius: 6px; padding: 8px 10px; font: inherit; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { width: 420px; max-width: calc(100vw - 32px); background: #fff; border-radius: 10px; border: 1px solid #ddd; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.dialog header { display: flex; justify-content: space-between; align-items: center; }
.file { text-align: left; }
.bubble :deep(p) { margin: 0 0 8px; }
.bubble :deep(p:last-child) { margin-bottom: 0; }
.bubble :deep(pre) { overflow: auto; background: #1e1e1e; color: #eee; border-radius: 8px; padding: 10px; }
</style>
