<template>
  <section class="artifact-page" :class="{ 'detail-open': selected }">
    <header class="page-header">
      <div><h1>制品中心</h1><p>管理从研究资料生成的可编辑、可追溯报告。</p></div>
      <button class="primary" @click="router.push('/researcher/create-artifact')">创建制品</button>
    </header>

    <div class="toolbar">
      <input v-model.trim="query" placeholder="搜索制品" />
      <select v-model="typeFilter"><option value="all">全部类型</option><option v-for="item in ARTIFACT_TYPES" :key="item.value" :value="item.value">{{ item.label }}</option></select>
      <select v-model="statusFilter"><option value="all">全部状态</option><option value="ready">已完成</option><option value="generating">生成中</option><option value="failed">生成失败</option></select>
      <span>{{ filteredArtifacts.length }} 个制品</span>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="state">正在加载制品...</div>
    <div v-else-if="!filteredArtifacts.length" class="state empty"><strong>暂无匹配制品</strong><span>从研究资料创建一份报告。</span><button class="primary" @click="router.push('/researcher/create-artifact')">开始创建</button></div>
    <div v-else class="artifact-grid">
      <article v-for="item in filteredArtifacts" :key="item.id" class="artifact-card" @click="openArtifact(item)">
        <div class="card-top"><span class="type-mark">{{ artifactTypeLabel(item.type) }}</span><span :class="['status', item.status]">{{ statusLabel(item.status) }}</span></div>
        <h2>{{ item.title }}</h2>
        <p>{{ sourceSummary(item) }}</p>
        <div class="card-bottom"><span>{{ formatDate(item.updatedAt || item.createdAt) }}</span><button class="delete-button" title="删除制品" @click.stop="removeArtifact(item)">删除</button></div>
      </article>
    </div>

    <div v-if="selected" class="modal-mask" @click.self="closeDetail">
      <article class="detail-modal" :class="{ 'mind-map-detail': selected.type === 'mind_map' }">
        <header class="modal-header">
          <div><span class="type-mark">{{ artifactTypeLabel(selected.type) }}</span><h2>{{ selected.title }}</h2><p>{{ statusLabel(selected.status) }} · {{ formatDate(selected.updatedAt || selected.createdAt) }}</p></div>
          <button class="close-button" title="关闭" @click="closeDetail">×</button>
        </header>
        <p v-if="selected.errorMessage" class="error">{{ selected.errorMessage }}</p>

        <div v-if="selected.status === 'ready'" class="preview">
          <template v-if="!editing">
            <div v-if="selected.type === 'report'" class="report-summary"><strong>摘要</strong><p>{{ selected.content?.summary }}</p></div>
            <section v-for="section in selected.content?.sections || []" :key="section.id" class="report-section">
              <h3>{{ section.title }}</h3>
              <p v-for="paragraph in section.paragraphs || []" :key="paragraph.id">{{ paragraph.text }}</p>
              <div class="citations"><button v-for="ref in section.sourceRefs || []" :key="`${ref.type}:${ref.id}`" @click="openSource(ref)">{{ ref.title || `${ref.type}:${ref.id}` }}</button></div>
            </section>
            <section v-if="selected.type !== 'mind_map' && selected.content?.references?.length" class="report-section references"><h3>参考来源</h3><button v-for="ref in selected.content.references" :key="`${ref.type}:${ref.id}`" @click="openSource(ref)">{{ ref.title }} · {{ ref.type }}:{{ ref.id }}</button></section>
            <div v-if="selected.type === 'mind_map'" class="mind-map diagram-shell">
              <svg class="mind-lines" :width="mindMapLayout.width" :height="mindMapLayout.height" :viewBox="`0 0 ${mindMapLayout.width} ${mindMapLayout.height}`" aria-hidden="true">
                <path v-for="line in mindMapLayout.lines" :key="line.id" :d="line.path" />
              </svg>
              <div class="mind-canvas" :style="{ width: `${mindMapLayout.width}px`, height: `${mindMapLayout.height}px` }">
                <article v-for="node in mindMapLayout.nodes" :key="node.id" class="mind-card" :class="[`depth-${node.depth}`, { expandable: node.children?.length }]" :style="{ left: `${node.x}px`, top: `${node.y}px` }">
                  <span class="mind-depth">{{ node.depth === 0 ? '主题' : node.depth === 1 ? '分支' : '证据' }}</span>
                  <template v-if="editing && mindEditingNodeId === node.id">
                    <input v-model.trim="node.source.label" class="mind-inline-input" maxlength="240" @click.stop />
                    <textarea v-model.trim="node.source.summary" class="mind-inline-textarea" rows="3" maxlength="2000" placeholder="节点内容" @click.stop></textarea>
                  </template>
                  <template v-else><strong>{{ node.label }}</strong><p v-if="node.summary">{{ node.summary }}</p></template>
                  <div class="mind-node-actions"><button v-if="node.children?.length" type="button" @click.stop="toggleMindNode(node.id)">{{ collapsedMindNodes[node.id] ? '展开' : '收起' }}</button><button v-if="editing && mindEditingNodeId !== node.id" type="button" @click.stop="startMindNodeEdit(node.id)">修改</button><button v-if="editing && mindEditingNodeId === node.id" type="button" @click.stop="mindEditingNodeId = ''">完成</button><button v-if="editing && node.depth > 0" type="button" class="danger-action" @click.stop="removeMindNode(node.id)">删除</button></div>
                </article>
              </div>
            </div>
            <section v-if="selected.type === 'flashcards'" class="flashcard-study">
              <div v-if="activeFlashcard" class="flashcard-stage">
                <button class="flashcard-nav" type="button" :disabled="flashcardIndex === 0" @click="previousFlashcard">Previous</button>
                <article class="flip-card" :class="{ flipped: flashcardFlipped }" tabindex="0" role="button" :aria-label="flashcardFlipped ? 'Show question' : 'Show answer'" @click="flipFlashcard" @keydown.enter.prevent="flipFlashcard" @keydown.space.prevent="flipFlashcard">
                  <div class="flip-card-inner">
                    <div class="flip-card-face flip-card-front"><span class="flashcard-side-label">Question</span><strong>{{ activeFlashcard.question }}</strong><small>Click to reveal answer</small></div>
                    <div class="flip-card-face flip-card-back"><span class="flashcard-side-label">Answer</span><p>{{ activeFlashcard.answer }}</p><small v-if="activeFlashcard.explanation">{{ activeFlashcard.explanation }}</small></div>
                  </div>
                </article>
                <button class="flashcard-nav" type="button" :disabled="flashcardIndex === flashcardList.length - 1" @click="nextFlashcard">Next</button>
              </div>
              <div class="flashcard-progress"><span>{{ flashcardIndex + 1 }} / {{ flashcardList.length }}</span><button class="secondary" type="button" @click="flipFlashcard">{{ flashcardFlipped ? 'Show question' : 'Show answer' }}</button></div>
            </section>
            <div v-if="selected.type === 'quiz'" class="quiz"><article v-for="question in selected.content.questions || []" :key="question.id" class="quiz-question"><strong>{{ question.question }}</strong><label v-for="option in question.options" :key="option.id"><input type="radio" :name="question.id" :value="option.id" v-model="answers[question.id]" /> {{ option.id }}. {{ option.text }}</label><small v-if="submitted">答案：{{ question.answer.join(', ') }} · {{ question.explanation }}</small></article><button v-if="selected.content.questions?.length" class="secondary" @click="submitted = true">提交答案</button></div>
            <section v-if="selected.type === 'quiz'" class="quiz-study">
              <div v-if="activeQuizQuestion" class="quiz-stage">
                <article class="quiz-question active-quiz-question">
                  <div class="quiz-progress">Question {{ quizIndex + 1 }} / {{ quizList.length }}</div>
                  <strong>{{ activeQuizQuestion.question }}</strong>
                  <label v-for="option in activeQuizQuestion.options" :key="option.id" :class="{ selected: answers[activeQuizQuestion.id] === option.id, correct: quizAnswered && activeQuizQuestion.answer.includes(option.id), incorrect: quizAnswered && answers[activeQuizQuestion.id] === option.id && !activeQuizQuestion.answer.includes(option.id) }"><input type="radio" :name="activeQuizQuestion.id" :value="option.id" v-model="answers[activeQuizQuestion.id]" @change="answerQuizQuestion" /> {{ option.id }}. {{ option.text }}</label>
                  <div v-if="quizAnswered" class="quiz-result" :class="{ correct: quizIsCorrect }"><strong>{{ quizIsCorrect ? 'Correct' : 'Incorrect' }}</strong><span>Answer: {{ activeQuizQuestion.answer.join(', ') }}</span><p>{{ activeQuizQuestion.explanation }}</p></div>
                </article>
                <div class="quiz-actions"><button class="secondary" type="button" :disabled="quizIndex === 0" @click="previousQuizQuestion">Previous</button><button class="primary" type="button" :disabled="!quizAnswered || quizIndex === quizList.length - 1" @click="nextQuizQuestion">Next</button></div>
              </div>
            </section>
            <section v-if="selected.type === 'data_table'" class="data-table-preview">
              <div class="data-table-meta"><strong>Structured data table</strong><span>{{ dataTableColumns.length }} fields · {{ dataTableRows.length }} rows</span></div>
              <div v-if="dataTableColumns.length && dataTableRows.length" class="table-wrap">
                <table>
                  <caption class="sr-only">{{ selected.title }}</caption>
                  <thead><tr><th class="row-number" scope="col">#</th><th v-for="column in dataTableColumns" :key="column.key" scope="col"><span>{{ column.label }}</span><small>{{ column.type || 'text' }}</small></th></tr></thead>
                  <tbody><tr v-for="(row, index) in dataTableRows" :key="index"><td class="row-number">{{ index + 1 }}</td><td v-for="column in dataTableColumns" :key="column.key" :class="{ 'is-empty': !displayTableValue(row[column.key]) }"><span>{{ displayTableValue(row[column.key]) || 'Not stated' }}</span></td></tr></tbody>
                </table>
              </div>
              <div v-else class="table-empty">No structured rows are available.</div>
              <details v-if="selected.content?.rawMarkdown" class="raw-generation">
                <summary>Model raw output</summary>
                <pre>{{ selected.content.rawMarkdown }}</pre>
              </details>
            </section>
          </template>
          <form v-else class="report-editor" @submit.prevent="saveEdit">
            <label>制品标题<input v-model.trim="draft.title" maxlength="240" /></label>
            <label v-if="draft.kind === 'report'">摘要<textarea v-model="draft.summary" rows="5"></textarea></label>
            <section v-if="draft.kind === 'report'" v-for="section in draft.sections || []" :key="section.id" class="edit-section"><label>{{ section.title }}<textarea v-for="paragraph in section.paragraphs || []" :key="paragraph.id" v-model="paragraph.text" rows="5"></textarea></label></section>
            <section v-if="draft.kind === 'flashcards'" v-for="card in draft.cards || []" :key="card.id" class="edit-section"><label>问题<textarea v-model="card.question" rows="2"></textarea></label><label>答案<textarea v-model="card.answer" rows="3"></textarea></label></section>
            <section v-if="draft.kind === 'quiz'" v-for="question in draft.questions || []" :key="question.id" class="edit-section"><label>题目<textarea v-model="question.question" rows="2"></textarea></label><label>解析<textarea v-model="question.explanation" rows="2"></textarea></label></section>
            <section v-if="draft.kind === 'data_table'" class="edit-section data-table-editor">
              <div class="data-table-meta"><strong>Edit structured table</strong><span>{{ (draft.columns || []).length }} fields · {{ (draft.rows || []).length }} rows</span></div>
              <div class="table-wrap"><table><thead><tr><th class="row-number">#</th><th v-for="column in draft.columns || []" :key="column.key">{{ column.label }}</th></tr></thead><tbody><tr v-for="(row, index) in draft.rows || []" :key="index"><td class="row-number">{{ index + 1 }}</td><td v-for="column in draft.columns || []" :key="column.key"><textarea v-model="row[column.key]" rows="3" :aria-label="`${column.label} row ${index + 1}`"></textarea></td></tr></tbody></table></div>
            </section>
            <section v-if="draft.kind === 'mind_map'" class="edit-section mind-editor">
              <h3>新增自定义分支</h3>
              <label>父节点<select v-model="newBranchParent"><option value="root">{{ draft.root?.label || '主题' }}</option><option v-for="node in editableMindNodes" :key="node.id" :value="node.id">{{ '　'.repeat(node.depth) }}{{ node.label }}</option></select></label>
              <label>分支标签<input v-model.trim="newBranchLabel" maxlength="240" placeholder="例如：研究限制" /></label>
              <label>分支内容<textarea v-model.trim="newBranchSummary" rows="3" maxlength="2000" placeholder="填写该分支的说明、论据或个人笔记"></textarea></label>
              <button class="secondary" type="button" @click="addMindBranch">添加到思维导图</button>
            </section>
            <div v-if="draft.kind === 'mind_map'" class="mind-map diagram-shell edit-diagram">
              <svg class="mind-lines" :width="mindMapLayout.width" :height="mindMapLayout.height" :viewBox="`0 0 ${mindMapLayout.width} ${mindMapLayout.height}`" aria-hidden="true"><path v-for="line in mindMapLayout.lines" :key="line.id" :d="line.path" /></svg>
              <div class="mind-canvas" :style="{ width: `${mindMapLayout.width}px`, height: `${mindMapLayout.height}px` }">
                <article v-for="node in mindMapLayout.nodes" :key="node.id" class="mind-card" :class="`depth-${node.depth}`" :style="{ left: `${node.x}px`, top: `${node.y}px` }">
                  <span class="mind-depth">{{ node.depth === 0 ? '主题' : node.depth === 1 ? '分支' : '证据' }}</span>
                  <input v-model.trim="node.source.label" class="mind-inline-input" maxlength="240" />
                  <textarea v-model.trim="node.source.summary" class="mind-inline-textarea" rows="3" maxlength="2000" placeholder="节点内容"></textarea>
                  <div class="mind-node-actions"><button v-if="node.depth > 0" type="button" class="danger-action" @click.stop="removeMindNode(node.id)">删除此节点</button></div>
                </article>
              </div>
            </div>
            <div class="editor-actions"><button class="secondary" type="button" :disabled="saving" @click="cancelEdit">取消</button><button class="primary" type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存修改' }}</button></div>
          </form>
        </div>
        <div v-else class="preview pending"><strong>{{ statusLabel(selected.status) }}</strong><span>{{ selected.errorMessage || (selected.status === 'generating' ? '制品正在生成，请稍后刷新。' : '暂无预览内容。') }}</span></div>

        <footer class="modal-footer">
          <button v-if="selected.status === 'ready' && !editing" class="secondary" @click="beginEdit">编辑</button>
          <button v-if="selected.status === 'ready'" class="secondary" @click="downloadArtifact('markdown')">Markdown</button>
          <button v-if="selected.status === 'ready'" class="secondary" @click="downloadArtifact('json')">JSON</button>
          <button v-if="selected.status === 'ready' && selected.type === 'data_table'" class="secondary" @click="downloadArtifact('csv')">CSV</button>
          <button class="secondary" :disabled="regenerating" @click="regenerate">{{ regenerating ? '生成中...' : '重新生成' }}</button>
          <button class="primary" @click="closeDetail">关闭</button>
        </footer>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ARTIFACT_TYPES, artifactTypeLabel, useResearchArtifacts } from '../../composables/useResearchArtifacts.js'
import { useAuthFetch } from '../../composables/useAuthFetch.js'

const route = useRoute()
const router = useRouter()
const { artifacts, loading, error, fetchArtifacts, fetchArtifact, updateArtifact, deleteArtifact, regenerateArtifact } = useResearchArtifacts()
const { authDownload } = useAuthFetch()
const query = ref('')
const typeFilter = ref(route.query.type || 'all')
const statusFilter = ref('all')
const selected = ref(null)
const draft = ref(null)
const editing = ref(false)
const saving = ref(false)
const regenerating = ref(false)
const answers = ref({})
const submitted = ref(false)
const newBranchParent = ref('root')
const newBranchLabel = ref('')
const newBranchSummary = ref('')
const mindEditingNodeId = ref('')
const flashcardIndex = ref(0)
const flashcardFlipped = ref(false)
const quizIndex = ref(0)

const mindMapLayout = computed(() => layoutMindMap(editing.value ? draft.value?.root : selected.value?.content?.root))
const flashcardList = computed(() => selected.value?.content?.cards || [])
const activeFlashcard = computed(() => flashcardList.value[flashcardIndex.value] || null)
const quizList = computed(() => selected.value?.content?.questions || [])
const activeQuizQuestion = computed(() => quizList.value[quizIndex.value] || null)
const quizAnswered = computed(() => Boolean(activeQuizQuestion.value && answers.value[activeQuizQuestion.value.id]))
const quizIsCorrect = computed(() => quizAnswered.value && activeQuizQuestion.value.answer.includes(answers.value[activeQuizQuestion.value.id]))
const dataTableModel = computed(() => normalizeDataTable(selected.value?.content || {}))
const dataTableColumns = computed(() => dataTableModel.value.columns)
const dataTableRows = computed(() => dataTableModel.value.rows)
const collapsedMindNodes = ref({})
const editableMindNodes = computed(() => {
  const result = []
  function visit(node, depth = 1) { if (!node) return; result.push({ id: node.id, label: node.label, depth }); (node.children || []).forEach(child => visit(child, depth + 1)) }
  ;(draft.value?.root?.children || []).forEach(child => visit(child))
  return result
})

function layoutMindMap(root) {
  if (!root) return { width: 720, height: 260, nodes: [], lines: [] }
  const nodes = []
  const lines = []
  const columns = {}
  function collect(node, depth = 0, parent = null) {
    const item = { id: node.id || `node-${nodes.length}`, label: node.label || '', summary: node.summary || '', source: node, depth, parent, children: node.children || [] }
    nodes.push(item)
    columns[depth] = (columns[depth] || 0) + 1
    if (!collapsedMindNodes.value[item.id]) item.children.forEach(child => collect(child, depth + 1, item))
  }
  collect(root)
  const maxDepth = Math.max(...nodes.map(node => node.depth), 0)
  const colWidth = 250
  const rowHeight = editing.value ? 320 : 210
  const positions = {}
  for (let depth = 0; depth <= maxDepth; depth += 1) {
    const columnNodes = nodes.filter(node => node.depth === depth)
    columnNodes.forEach((node, index) => {
      node.x = 24 + depth * colWidth
      node.y = 24 + index * rowHeight
      positions[node.id] = node
    })
  }
  nodes.forEach(node => {
    if (!node.parent) return
    const parent = positions[node.parent.id]
    lines.push({ id: `${node.parent.id}-${node.id}`, path: `M ${parent.x + 210} ${parent.y + 43} C ${parent.x + 235} ${parent.y + 43}, ${node.x - 25} ${node.y + 43}, ${node.x} ${node.y + 43}` })
  })
  return { width: Math.max(720, (maxDepth + 1) * colWidth + 24), height: Math.max(260, Math.max(...nodes.map(node => node.y), 0) + 115), nodes, lines }
}

function toggleMindNode(id) {
  collapsedMindNodes.value = { ...collapsedMindNodes.value, [id]: !collapsedMindNodes.value[id] }
}

function startMindNodeEdit(id) {
  if (!editing.value) beginEdit()
  mindEditingNodeId.value = id
}

function removeMindNode(id) {
  if (!draft.value?.root || id === draft.value.root.id) return
  function removeFrom(node) {
    const before = node.children || []
    const after = before.filter(child => child.id !== id)
    if (after.length !== before.length) { node.children = after; return true }
    return before.some(removeFrom)
  }
  removeFrom(draft.value.root)
  if (mindEditingNodeId.value === id) mindEditingNodeId.value = ''
}

function addMindBranch() {
  if (!draft.value?.root || !newBranchLabel.value) return
  const branch = { id: `custom-${Date.now()}`, label: newBranchLabel.value, summary: newBranchSummary.value, sourceRefs: [], children: [] }
  function append(node) { if (node.id === newBranchParent.value) { node.children = [...(node.children || []), branch]; return true } return (node.children || []).some(append) }
  append(draft.value.root)
  newBranchLabel.value = ''
  newBranchSummary.value = ''
  newBranchParent.value = 'root'
}

function resetFlashcards() {
  flashcardIndex.value = 0
  flashcardFlipped.value = false
}

function flipFlashcard() {
  if (activeFlashcard.value) flashcardFlipped.value = !flashcardFlipped.value
}

function previousFlashcard() {
  if (flashcardIndex.value <= 0) return
  flashcardIndex.value -= 1
  flashcardFlipped.value = false
}

function nextFlashcard() {
  if (flashcardIndex.value >= flashcardList.value.length - 1) return
  flashcardIndex.value += 1
  flashcardFlipped.value = false
}

function resetQuiz() {
  quizIndex.value = 0
  answers.value = {}
  submitted.value = false
}

function answerQuizQuestion() {
  submitted.value = true
}

function previousQuizQuestion() {
  if (quizIndex.value <= 0) return
  quizIndex.value -= 1
}

function nextQuizQuestion() {
  if (!quizAnswered.value || quizIndex.value >= quizList.value.length - 1) return
  quizIndex.value += 1
}

function normalizeDataTable(content) {
  const columns = Array.isArray(content?.columns) ? content.columns.filter(column => column && column.key) : []
  const rows = Array.isArray(content?.rows) ? content.rows.filter(row => row && typeof row === 'object') : []
  if (columns.length && rows.length) return { columns, rows }
  const markdown = String(content?.markdown || '')
  const lines = markdown.split(/\r?\n/).map(line => line.trim()).filter(line => line.startsWith('|') && line.endsWith('|'))
  if (lines.length < 3) return { columns, rows }
  const cells = line => line.slice(1, -1).split('|').map(value => value.trim())
  const header = cells(lines[0])
  const separator = cells(lines[1])
  if (!header.length || !separator.every(value => /^:?-{3,}:?$/.test(value))) return { columns, rows }
  const parsedColumns = header.map((label, index) => ({ key: `column_${index + 1}`, label: label || `Column ${index + 1}`, type: 'text' }))
  const parsedRows = lines.slice(2).map(line => {
    const values = cells(line)
    return Object.fromEntries(parsedColumns.map((column, index) => [column.key, values[index] || '']))
  }).filter(row => Object.values(row).some(Boolean))
  return { columns: parsedColumns, rows: parsedRows }
}

function displayTableValue(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value).trim()
}

const filteredArtifacts = computed(() => artifacts.value.filter(item => {
  const haystack = `${item.title || ''} ${artifactTypeLabel(item.type)}`.toLowerCase()
  return (typeFilter.value === 'all' || item.type === typeFilter.value) && (statusFilter.value === 'all' || item.status === statusFilter.value) && (!query.value || haystack.includes(query.value.toLowerCase()))
}))

onMounted(async () => {
  await fetchArtifacts()
  if (route.query.id) {
    const item = await fetchArtifact(route.query.id)
    if (item) { selected.value = item; resetFlashcards(); resetQuiz() }
  }
})

function statusLabel(status) { return { ready: '已完成', generating: '生成中', failed: '生成失败', draft: '草稿' }[status] || status || '未知状态' }
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN') : '未记录' }
function sourceSummary(item) { return item.sourceRefs?.length ? `${item.sourceRefs.length} 项来源资料` : '暂无来源资料' }
async function openArtifact(item) { selected.value = await fetchArtifact(item.id) || item; editing.value = false; resetFlashcards(); resetQuiz() }
function closeDetail() { selected.value = null; editing.value = false; draft.value = null; resetFlashcards(); resetQuiz() }
async function removeArtifact(item) {
  if (!window.confirm(`确定删除“${item.title}”吗？`)) return
  await deleteArtifact(item.id)
  if (selected.value?.id === item.id) closeDetail()
}
async function regenerate() {
  if (!selected.value) return
  regenerating.value = true
  try { selected.value = await regenerateArtifact(selected.value.id) || selected.value; editing.value = false; resetFlashcards(); resetQuiz() } finally { regenerating.value = false }
}
function beginEdit() { draft.value = JSON.parse(JSON.stringify(selected.value.content || {})); if (draft.value.kind === 'data_table') { const table = normalizeDataTable(draft.value); draft.value.columns = table.columns; draft.value.rows = table.rows } mindEditingNodeId.value = ''; editing.value = true }
function cancelEdit() { editing.value = false; mindEditingNodeId.value = ''; draft.value = null }
async function saveEdit() {
  if (!selected.value || !draft.value) return
  saving.value = true
  try {
    const result = await updateArtifact(selected.value.id, { title: draft.value.title, content: draft.value })
    if (!result) throw new Error('保存报告失败')
    selected.value = result
    editing.value = false
    draft.value = null
  } catch (err) { window.alert(err.message || '保存报告失败') } finally { saving.value = false }
}
function openSource(ref) {
  const path = ref.type === 'latex' ? '/researcher/writing-assistant' : '/researcher/materials'
  router.push({ path, query: { sourceType: ref.type, sourceId: ref.id } })
}
function markdownContent(item) { return item.content?.markdown || buildMarkdown(item.content || {}, item.title) }
function buildMarkdown(content, title) {
  if (content.kind !== 'report') {
    const lines = [`# ${content.title || title}`, '']
    if (content.kind === 'mind_map') walkMarkdown(content.root, lines, 0)
    if (content.kind === 'flashcards') (content.cards || []).forEach((card, i) => lines.push(`## ${i + 1}. ${card.question}`, '', card.answer, '', card.explanation, ''))
    if (content.kind === 'quiz') (content.questions || []).forEach((question, i) => lines.push(`## ${i + 1}. ${question.question}`, '', ...(question.options || []).map(option => `- ${option.id}: ${option.text}`), `答案：${(question.answer || []).join(', ')}`, question.explanation, ''))
    if (content.kind === 'data_table') { const table = normalizeDataTable(content); lines.push('| ' + table.columns.map(column => column.label).join(' | ') + ' |', '| ' + table.columns.map(() => '---').join(' | ') + ' |'); table.rows.forEach(row => lines.push('| ' + table.columns.map(column => row[column.key] || '').join(' | ') + ' |')) }
    return lines.join('\n')
  }
  const lines = [`# ${content.title || title}`, '', '## 摘要', '', content.summary || '', '']
  for (const section of content.sections || []) { lines.push(`## ${section.title}`, ''); for (const paragraph of section.paragraphs || []) lines.push(paragraph.text || '', '') }
  if (content.references?.length) { lines.push('## 参考来源', ''); for (const ref of content.references) lines.push(`- ${ref.title || `${ref.type}:${ref.id}`} (${ref.type}:${ref.id})`); lines.push('') }
  return lines.join('\n')
}
function walkMarkdown(node, lines, depth) { if (!node) return; lines.push(`${'  '.repeat(depth)}- ${node.label || ''}`); if (node.summary) lines.push(`${'  '.repeat(depth + 1)}${node.summary}`); (node.children || []).forEach(child => walkMarkdown(child, lines, depth + 1)) }
function downloadFile(name, content, type) { const url = URL.createObjectURL(new Blob([content], { type })); const link = document.createElement('a'); link.href = url; link.download = name; link.click(); URL.revokeObjectURL(url) }
async function downloadArtifact(format) { if (!selected.value) return; const file = await authDownload(`/api/researcher/artifacts/${selected.value.id}/export?format=${format}`); const url = URL.createObjectURL(file.blob); const link = document.createElement('a'); link.href = url; link.download = file.filename || `${selected.value.title || 'artifact'}.${format === 'markdown' ? 'md' : format}`; link.click(); URL.revokeObjectURL(url) }
function csvContent(content) { const table = normalizeDataTable(content); const quote = value => `"${String(value ?? '').replaceAll('"', '""')}"`; return [table.columns.map(column => quote(column.label)).join(','), ...table.rows.map(row => table.columns.map(column => quote(row[column.key])).join(','))].join('\n') }
</script>

<style scoped>
.artifact-page{height:100%;overflow:auto;padding:36px 44px;background:#fafbfa;color:#172019}.page-header,.toolbar,.card-top,.card-bottom,.modal-header,.modal-footer{display:flex;align-items:center;justify-content:space-between;gap:16px}.page-header{border-bottom:1px solid #e2e8e2;padding-bottom:22px}.page-header h1{margin:0;font-size:28px}.page-header p{margin:8px 0 0;color:#758078}.primary,.secondary{border:1px solid #d5ddd5;padding:10px 15px;background:#fff;cursor:pointer}.primary{background:#263d2e;border-color:#263d2e;color:#fff}.primary:disabled,.secondary:disabled{opacity:.5;cursor:not-allowed}.toolbar{justify-content:flex-start;margin:24px 0}.toolbar input,.toolbar select,.report-editor input,.report-editor textarea{border:1px solid #dce3dc;background:#fff;padding:10px 12px;border-radius:5px;font:inherit}.toolbar input{width:300px}.toolbar>span{margin-left:auto;color:#758078;font-size:13px}.artifact-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}.artifact-card{min-height:175px;padding:18px;border:1px solid #e1e7e1;background:#fff;cursor:pointer}.artifact-card:hover{border-color:#78927e}.type-mark{display:inline-flex;padding:4px 7px;background:#edf4ee;color:#35583e;font-size:12px}.status{font-size:12px;color:#758078}.status.ready{color:#2f6b3c}.status.failed{color:#a33b30}.artifact-card h2{margin:19px 0 8px;font-size:17px}.artifact-card p{color:#758078;font-size:13px}.card-bottom{margin-top:30px;color:#849087;font-size:12px}.delete-button{border:0;background:none;color:#a33b30;cursor:pointer}.state{padding:90px 20px;text-align:center;color:#758078}.state strong,.state span{display:block}.state span{margin:10px 0 20px}.error-banner{margin:0 0 16px;padding:12px 14px;border:1px solid #f0cbc6;background:#fff6f4;color:#a33b30}.modal-mask{position:fixed;inset:0;z-index:20;display:grid;place-items:center;background:rgba(20,30,22,.35);padding:20px}.detail-modal{width:min(840px,100%);max-height:88vh;overflow:auto;background:#fff;padding:26px}.modal-header{align-items:flex-start}.detail-modal h2{margin:13px 0 5px;font-size:22px}.modal-header p{margin:0;color:#758078;font-size:12px}.close-button{border:0;background:none;font-size:26px;cursor:pointer}.preview{margin:24px 0;padding:20px;border:1px solid #edf0ed;line-height:1.8}.report-summary{padding-bottom:16px;border-bottom:1px solid #edf0ed}.report-summary p{margin-bottom:0}.report-section{padding:18px 0;border-bottom:1px solid #edf0ed}.report-section h3{margin:0 0 12px;font-size:18px}.report-section p{margin:0 0 12px;white-space:pre-wrap}.citations{display:flex;flex-wrap:wrap;gap:7px}.citations button,.citations span,.references button{border:0;padding:5px 8px;background:#eef5ef;color:#35583e;font-size:12px;cursor:pointer}.references button{display:block;margin:7px 0}.mind-map{overflow:auto;padding:14px 4px}.mind-node{position:relative;margin:0 0 0 28px;padding:8px 0 8px 22px;border-left:1px solid #cbd8cc}.mind-node:first-child{margin-left:0;border-left:0}.mind-node-card{position:relative;min-width:220px;padding:12px 14px;border:1px solid #dbe5dc;background:#fff}.mind-node-card:before{content:'';position:absolute;left:-23px;top:25px;width:22px;border-top:1px solid #cbd8cc}.mind-node:first-child>.mind-node-card:before{display:none}.mind-node-card strong{display:block;color:#263d2e}.mind-node-card p{margin:5px 0 0;color:#758078;font-size:12px}.mind-toggle{float:right;border:0;background:#edf4ee;color:#35583e;cursor:pointer}.mind-children{display:flex;gap:4px;align-items:flex-start}.flashcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.flashcard{padding:16px;border:1px solid #dbe5dc;background:#fff}.flashcard p{font-weight:600}.flashcard small{color:#758078}.quiz-question{display:grid;gap:9px;padding:16px 0;border-bottom:1px solid #edf0ed}.quiz-question label{font-size:14px}.quiz-question small{color:#526e5a}.table-wrap{overflow:auto}.table-wrap table{width:100%;border-collapse:collapse}.table-wrap th,.table-wrap td{padding:10px;border:1px solid #dbe5dc;text-align:left;vertical-align:top;min-width:140px}.report-editor{display:grid;gap:18px}.report-editor>label,.edit-section label{display:grid;gap:7px;font-size:13px}.report-editor textarea{resize:vertical;min-height:100px}.edit-section{display:grid;gap:10px;padding-top:17px;border-top:1px solid #edf0ed}.edit-section textarea{min-height:90px}.editor-actions{display:flex;justify-content:flex-end;gap:10px}.pending{display:grid;gap:8px;text-align:center}.error{color:#a33b30}.modal-footer{justify-content:flex-end;margin-top:20px;flex-wrap:wrap}@media(max-width:720px){.artifact-page{padding:24px 18px}.page-header,.toolbar{align-items:flex-start;flex-direction:column}.toolbar>span{margin-left:0}.toolbar input{width:100%}.detail-modal{padding:20px}.modal-footer{justify-content:flex-start}.mind-children{display:block}}
.diagram-shell{position:relative;min-height:260px;background:#f7faf7;border:1px solid #e1e9e1}.mind-canvas{position:relative}.mind-lines{position:absolute;inset:0;z-index:0;overflow:visible}.mind-lines path{fill:none;stroke:#9bb2a0;stroke-width:2}.mind-card{position:absolute;z-index:1;width:210px;min-height:86px;padding:12px 14px;border:1px solid #cbdccc;border-radius:8px;background:#fff;box-shadow:0 4px 12px rgba(38,61,46,.08)}.mind-card.depth-0{background:#263d2e;border-color:#263d2e;color:#fff}.mind-card.depth-1{border-left:4px solid #789b80}.mind-card.depth-2{border-left:4px solid #c4d7c6}.mind-card strong{display:block;line-height:1.4}.mind-card p{margin:6px 0 0;color:#66766b;font-size:12px;line-height:1.45}.mind-card.depth-0 p{color:#d9e8db}.mind-depth{display:block;margin-bottom:6px;color:#6a8b70;font-size:10px}.mind-card.depth-0 .mind-depth{color:#b9d6bc}@media(max-width:720px){.mind-card{width:190px}}
.artifact-page{display:grid;grid-template-columns:minmax(210px,.52fr) minmax(560px,1.9fr);grid-template-rows:auto auto 1fr;column-gap:20px;align-items:start}.artifact-page>.page-header{grid-column:1 / -1}.artifact-page>.toolbar{grid-column:1 / -1}.artifact-page>.error-banner{grid-column:1 / -1}.artifact-page>.state{grid-column:1 / -1}.artifact-grid{grid-column:1;grid-row:3;grid-template-columns:1fr;max-height:calc(100vh - 230px);overflow:auto;padding-right:4px}.artifact-page>.modal-mask{grid-column:2;grid-row:3;position:static;display:block;padding:0;background:none;z-index:auto}.artifact-page>.modal-mask>.detail-modal{width:100%;max-height:calc(100vh - 230px);overflow:auto;padding:26px;box-shadow:0 8px 24px rgba(38,61,46,.08);border:1px solid #e1e7e1}.artifact-page>.modal-mask .close-button{display:none}.artifact-page>.modal-mask .modal-footer{position:sticky;bottom:-26px;padding:14px 0 0;background:#fff}.artifact-card{min-height:122px;padding:14px}.artifact-card h2{margin:10px 0 6px;font-size:15px}.artifact-card p{font-size:12px}.artifact-card .card-bottom{margin-top:14px}.diagram-shell{max-height:calc(100vh - 360px)}@media(max-width:1050px){.artifact-page{grid-template-columns:minmax(190px,.48fr) minmax(470px,1.7fr);column-gap:14px}.artifact-page>.modal-mask>.detail-modal{padding:20px}}@media(max-width:800px){.artifact-page{display:block}.artifact-grid{max-height:none;margin-bottom:18px}.artifact-page>.modal-mask{position:static}.artifact-page>.modal-mask>.detail-modal{max-height:none;box-shadow:none;padding:20px}.artifact-page>.modal-mask .close-button{display:block}.artifact-page>.modal-mask .modal-footer{position:static;padding:0;background:transparent}.diagram-shell{max-height:none}}
.artifact-page.detail-open{display:block}.artifact-page.detail-open>.toolbar{display:none}.artifact-page.detail-open>.artifact-grid{display:none}.artifact-page.detail-open>.modal-mask{display:block;margin-top:24px}.artifact-page.detail-open>.modal-mask>.detail-modal{max-height:calc(100vh - 190px)}.artifact-page.detail-open>.modal-mask .close-button{display:block}.mind-map-detail .preview{margin-top:10px;padding:8px}.mind-map-detail .modal-header{margin-bottom:4px}.mind-map-detail .modal-header h2{margin:6px 0 2px}.mind-map-detail .diagram-shell{min-height:calc(100vh - 330px);max-height:none}.mind-lines{display:block;position:absolute;left:0;top:0;width:auto;height:auto;pointer-events:none}.mind-card.expandable{cursor:pointer}.mind-card.expandable:hover{border-color:#526e5a;box-shadow:0 6px 16px rgba(38,61,46,.14)}.mind-expand{display:block;margin-top:8px;color:#526e5a;font-size:11px}.mind-card.depth-0 .mind-expand{color:#c9e1cc}
.flashcards{grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;padding:8px 4px}.flashcard{min-height:190px;padding:22px;border-radius:8px;line-height:1.7}.flashcard strong{display:block;margin-bottom:14px;font-size:16px;line-height:1.5}.flashcard p{margin:0 0 14px;font-size:15px;line-height:1.7}.flashcard small{display:block;line-height:1.6}.mind-editor{background:#f7faf7;padding:16px;border:1px solid #dbe7dc}.mind-editor h3{margin:0;font-size:16px}.mind-editor select,.mind-editor input,.mind-editor textarea{width:100%;box-sizing:border-box}@media(max-width:720px){.flashcards{grid-template-columns:1fr;gap:14px}.flashcard{min-height:0}}
.mind-inline-input,.mind-inline-textarea{display:block;width:100%;box-sizing:border-box;border:1px solid #c5d5c7;background:#fff;padding:6px 8px;font:inherit}.mind-inline-input{font-weight:700;margin-bottom:8px}.mind-inline-textarea{font-size:12px;line-height:1.45;resize:vertical;max-height:110px;overflow:auto}.mind-card.depth-0 .mind-inline-input,.mind-card.depth-0 .mind-inline-textarea{color:#172019}.mind-node-actions{display:flex;gap:6px;margin-top:10px}.mind-node-actions button{border:1px solid #cbdccc;background:#f5faf5;color:#35583e;padding:3px 7px;font-size:11px;cursor:pointer}.mind-node-actions .danger-action{border-color:#e7c5c0;background:#fff6f4;color:#a33b30}.mind-card.depth-0 .mind-node-actions button{border-color:#789b80}.edit-diagram .mind-card{min-height:180px;max-height:270px;overflow:hidden}
.table-wrap{overflow:auto;border:1px solid #dbe5dc;background:#fff}.table-wrap table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}.table-wrap th,.table-wrap td{padding:11px 12px;border-right:1px solid #dbe5dc;border-bottom:1px solid #dbe5dc;text-align:left;vertical-align:top;min-width:160px;line-height:1.55;overflow-wrap:anywhere}.table-wrap th{position:sticky;top:0;z-index:1;background:#eef5ef;color:#263d2e;font-size:12px}.table-wrap th span,.table-wrap th small{display:block}.table-wrap th small{margin-top:4px;color:#78907d;font-size:10px;font-weight:400}.table-wrap tr:last-child td{border-bottom:0}.table-wrap th:last-child,.table-wrap td:last-child{border-right:0}.table-wrap .row-number{width:42px;min-width:42px;text-align:center;color:#849087;background:#f8fbf8;font-size:12px}.table-wrap td.is-empty{color:#9aa59d;font-style:italic}.data-table-preview{margin-top:24px}.data-table-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 10px;color:#526e5a;font-size:13px}.data-table-meta span{color:#849087;font-size:12px}.table-empty{padding:28px;text-align:center;color:#849087;border:1px dashed #cbd8cc;background:#f8fbf8}.data-table-editor .table-wrap{max-height:52vh}.data-table-editor .table-wrap textarea{width:100%;min-width:140px;box-sizing:border-box;resize:vertical;border:1px solid #dce3dc;background:#fff;padding:8px;font:inherit;line-height:1.45}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.raw-generation{margin-top:16px;border-top:1px solid #edf0ed;padding-top:12px}.raw-generation summary{cursor:pointer;color:#526e5a;font-size:12px}.raw-generation pre{margin:10px 0 0;padding:12px;max-height:320px;overflow:auto;background:#f7faf7;border:1px solid #dbe5dc;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}
.flashcard-study{max-width:760px;margin:24px auto 8px}.flashcard-stage{display:grid;grid-template-columns:82px minmax(0,1fr) 82px;align-items:center;gap:18px}.flashcard-nav{border:1px solid #d5ddd5;background:#fff;color:#35583e;padding:10px 8px;cursor:pointer}.flashcard-nav:disabled{opacity:.4;cursor:not-allowed}.flip-card{height:360px;perspective:1200px;cursor:pointer;outline:none}.flip-card:focus-visible{box-shadow:0 0 0 3px rgba(82,110,90,.24)}.flip-card-inner{position:relative;width:100%;height:100%;transition:transform .48s ease;transform-style:preserve-3d}.flip-card.flipped .flip-card-inner{transform:rotateY(180deg)}.flip-card-face{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:38px 44px;border:1px solid #cbdccc;border-radius:8px;background:#fff;box-shadow:0 10px 28px rgba(38,61,46,.1);backface-visibility:hidden;text-align:center}.flip-card-front{background:#263d2e;color:#fff}.flip-card-back{transform:rotateY(180deg);background:#f7faf7;color:#172019}.flashcard-side-label{margin-bottom:20px;color:#b9d6bc;font-size:12px;letter-spacing:.08em;text-transform:uppercase}.flip-card-back .flashcard-side-label{color:#526e5a}.flip-card-face strong{max-width:580px;font-size:24px;line-height:1.5}.flip-card-face p{max-width:600px;margin:0 0 18px;font-size:19px;line-height:1.7;white-space:pre-wrap}.flip-card-face small{max-width:600px;margin-top:22px;color:#d9e8db;line-height:1.6}.flip-card-back small{color:#66766b}.flashcard-progress{display:flex;align-items:center;justify-content:center;gap:18px;margin-top:18px;color:#758078;font-size:13px}.flashcard-progress .secondary{padding:7px 11px}@media(max-width:720px){.flashcard-stage{grid-template-columns:1fr;gap:10px}.flashcard-nav{width:100%}.flashcard-nav:first-child{order:2}.flip-card{height:330px}.flip-card-face{padding:28px 24px}.flip-card-face strong{font-size:20px}.flip-card-face p{font-size:16px}.flashcard-nav:last-child{order:3}.flashcard-progress{flex-wrap:wrap}}
.quiz{display:none}.quiz-study{max-width:760px;margin:24px auto 8px}.active-quiz-question{margin:0;padding:28px;border:1px solid #dbe5dc;background:#fff}.quiz-progress{margin-bottom:18px;color:#78907d;font-size:12px}.active-quiz-question>strong{display:block;margin-bottom:20px;font-size:20px;line-height:1.55}.active-quiz-question label{display:block;margin:10px 0;padding:13px 15px;border:1px solid #dbe5dc;background:#fff;cursor:pointer;line-height:1.5}.active-quiz-question label.selected{border-color:#789b80;background:#f5faf5}.active-quiz-question label.correct{border-color:#6eaa79;background:#edf8ef}.active-quiz-question label.incorrect{border-color:#d99a91;background:#fff4f2}.active-quiz-question label input{margin-right:8px}.quiz-result{margin-top:18px;padding:14px;border-left:4px solid #c98276;background:#fff4f2}.quiz-result.correct{border-left-color:#6eaa79;background:#edf8ef}.quiz-result strong,.quiz-result span{display:block}.quiz-result span{margin-top:5px;color:#526e5a;font-size:13px}.quiz-result p{margin:8px 0 0;white-space:pre-wrap;line-height:1.55}.quiz-actions{display:flex;justify-content:space-between;gap:12px;margin-top:16px}
</style>
