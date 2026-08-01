<template>
  <section class="create-page">
    <header class="page-header">
      <div>
        <h1>创建制品</h1>
        <p>从研究资料生成可编辑、可追溯的研究报告。</p>
      </div>
      <button class="quiet-button" @click="router.push('/researcher/artifacts')">查看制品中心</button>
    </header>

    <nav class="steps" aria-label="创建步骤">
      <button :class="{ active: step === 1 }" @click="step = 1">01 选择资料</button>
      <button :class="{ active: step === 2 }" :disabled="!selectedSources.length" @click="step = 2">02 选择类型</button>
      <button :class="{ active: step === 3 }" :disabled="!selectedType" @click="step = 3">03 配置并生成</button>
    </nav>

    <div v-if="loading" class="state">正在加载资料...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>

    <template v-else-if="step === 1">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>选择研究资料</h2>
            <p>可同时选择附件、论文、研究结果、课题和 LaTeX 文稿。</p>
          </div>
          <label class="upload-button">上传附件<input type="file" accept=".pdf,.docx,.xlsx,.csv,.txt,.md" @change="uploadFile" /></label>
        </div>
        <div class="source-filter">
          <input v-model.trim="sourceQuery" placeholder="搜索资料" />
          <select v-model="sourceFilter">
            <option value="all">全部来源</option>
            <option value="attachment">上传附件</option>
            <option value="paper">论文</option>
            <option value="result">研究结果</option>
            <option value="project">课题</option>
            <option value="latex">LaTeX 文稿</option>
          </select>
        </div>
        <div class="source-grid">
          <button v-for="source in filteredSources" :key="sourceKey(source)" class="source-card" :class="{ selected: isSelected(source) }" @click="toggleSource(source)">
            <span class="check">{{ isSelected(source) ? '✓' : '' }}</span>
            <span class="source-type">{{ sourceLabel(source.type) }}</span>
            <strong>{{ source.title }}</strong>
            <small>{{ source.preview || source.meta || '暂无摘要' }}</small>
            <em>{{ source.meta }}</em>
          </button>
        </div>
        <div v-if="!filteredSources.length" class="inline-empty">暂无可选资料，请先上传文件或保存研究结果。</div>
      </section>
      <div class="actions">
        <span>{{ selectedSources.length }} 项资料已选择</span>
        <button class="primary" :disabled="!selectedSources.length" @click="step = 2">继续选择类型</button>
      </div>
    </template>

    <template v-else-if="step === 2">
      <section class="panel">
        <div class="panel-head">
          <div><h2>选择制品类型</h2><p>选择一种结构化制品，生成后可继续编辑。</p></div>
          <button class="secondary" @click="step = 1">返回选择资料</button>
        </div>
        <div class="output-grid">
          <button v-for="item in ARTIFACT_TYPES" :key="item.value" class="output-card" :class="{ selected: selectedType === item.value, unavailable: !item.available }" :disabled="!item.available" @click="selectedType = item.value">
            <span class="output-icon">{{ item.icon }}</span>
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
            <span v-if="selectedType === item.value" class="selected-mark">已选择</span>
          </button>
        </div>
      </section>
      <div class="actions">
        <span>{{ selectedTypeLabel || '请选择一种制品类型' }}</span>
        <button class="primary" :disabled="!selectedType" @click="step = 3">继续配置</button>
      </div>
    </template>

    <template v-else>
      <section class="panel configure">
        <div class="panel-head">
          <div><h2>配置并生成{{ selectedTypeLabel }}</h2><p>{{ selectedSources.length }} 项资料 · {{ selectedTypeLabel }}</p></div>
          <button class="secondary" :disabled="generating" @click="step = 2">返回选类型</button>
        </div>
        <label>制品标题<input v-model.trim="title" maxlength="240" :placeholder="selectedTypeLabel" /></label>
        <template v-if="selectedType === 'report'"><label>报告长度<select v-model="length"><option value="short">简洁</option><option value="standard">标准</option><option value="detailed">详细</option></select></label><label>研究重点或问题<textarea v-model.trim="note" rows="4" maxlength="1000" placeholder="可选：补充需要重点分析的问题或结论"></textarea></label><label class="checkbox-label"><input v-model="includeCitations" type="checkbox" /> 在报告中保留来源引用</label></template>
        <template v-else-if="selectedType === 'mind_map'"><label>最大层级<select v-model.number="maxDepth"><option :value="2">2 层</option><option :value="3">3 层</option><option :value="4">4 层</option></select></label><label class="checkbox-label"><input v-model="includeSummaries" type="checkbox" /> 包含节点摘要</label></template>
        <template v-else-if="selectedType === 'flashcards'"><label>卡片数量<input v-model.number="cardCount" type="number" min="8" max="20" /></label><label>难度<select v-model="difficulty"><option value="mixed">混合</option><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option></select></label></template>
        <template v-else-if="selectedType === 'quiz'"><label>题目数量<input v-model.number="questionCount" type="number" min="5" max="30" /></label><label>题目类型<select v-model="questionType"><option value="single">单选题</option></select></label></template>
        <template v-else-if="selectedType === 'data_table'"><label>表格主题<input v-model.trim="tableTopic" maxlength="240" placeholder="论文对比、研究结论汇总或实验数据整理" /></label><label>最大行数<input v-model.number="maxRows" type="number" min="5" max="20" /></label><label class="checkbox-label"><input v-model="extractNumbers" type="checkbox" /> 提取来源中的数字和比较关系</label></template>
        <div class="source-summary"><span v-for="source in selectedSources" :key="sourceKey(source)">{{ source.title }}</span></div>
        <div v-if="generating" class="progress" aria-live="polite">
          <div class="progress-bar"><i :style="{ width: `${progress}%` }"></i></div>
          <span>{{ progressStage }} {{ progress }}%</span>
        </div>
        <p v-if="generateError" class="error">{{ generateError }}</p>
      </section>
      <div class="actions">
        <span>生成后会自动保存到数据库制品中心。</span>
        <button class="primary" :disabled="generating || !selectedSources.length" @click="generate">{{ generating ? '生成中...' : `生成${selectedTypeLabel}` }}</button>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchWorkspace } from '../../composables/useResearchWorkspace.js'
import { usePaperLibrary } from '../../composables/usePaperLibrary.js'
import { useResearchResults } from '../../composables/useResearchResults.js'
import { useLatexDrafts } from '../../composables/useLatexDrafts.js'
import { ARTIFACT_TYPES, useResearchArtifacts } from '../../composables/useResearchArtifacts.js'

const router = useRouter()
const { attachments, projects, fetchAttachments, fetchProjects, uploadAttachment } = useResearchWorkspace()
const { papers, fetchPapers } = usePaperLibrary()
const { results, fetchResults } = useResearchResults()
const { fetchLatexDrafts } = useLatexDrafts()
const { createArtifact, fetchArtifact } = useResearchArtifacts()

const latexDrafts = ref([])
const step = ref(1)
const loading = ref(true)
const error = ref('')
const sourceQuery = ref('')
const sourceFilter = ref('all')
const selectedSources = ref([])
const selectedType = ref('report')
const title = ref('')
const note = ref('')
const length = ref('standard')
const includeCitations = ref(true)
const maxDepth = ref(3)
const includeSummaries = ref(true)
const cardCount = ref(12)
const difficulty = ref('mixed')
const questionCount = ref(10)
const questionType = ref('single')
const tableTopic = ref('')
const maxRows = ref(10)
const extractNumbers = ref(true)
const generating = ref(false)
const progress = ref(0)
const generateError = ref('')

const sourceItems = computed(() => [
  ...attachments.value.map(item => ({ type: 'attachment', id: item.id, title: item.fileName || '未命名附件', preview: item.summary, meta: `${item.fileType || '文件'} · ${item.parseStatus || '待解析'}` })),
  ...papers.value.map(item => ({ type: 'paper', id: item.id, title: item.title || item.fileName || '未命名论文', preview: item.aiSummary || item.abstract, meta: `${item.year || '未知年份'} · 论文库` })),
  ...results.value.map(item => ({ type: 'result', id: item.id, title: item.title || '未命名研究结果', preview: item.contentPreview, meta: item.sessionTitle || '工作台保存' })),
  ...projects.value.map(item => ({ type: 'project', id: item.id, title: item.name || '未命名课题', preview: item.description, meta: item.status || 'active' })),
  ...latexDrafts.value.map(item => ({ type: 'latex', id: item.id, title: item.title || item.fileName || '未命名 LaTeX 文稿', preview: String(item.content || '').slice(0, 160), meta: `LaTeX · v${item.currentVersion || 1}` })),
])
const filteredSources = computed(() => sourceItems.value.filter(item => {
  const haystack = `${item.title} ${item.preview || ''} ${item.meta || ''}`.toLowerCase()
  return (sourceFilter.value === 'all' || item.type === sourceFilter.value) && (!sourceQuery.value || haystack.includes(sourceQuery.value.toLowerCase()))
}))
const selectedTypeLabel = computed(() => ARTIFACT_TYPES.find(item => item.value === selectedType.value)?.label || '')
const progressStage = computed(() => progress.value < 35 ? '正在准备资料...' : progress.value < 80 ? '正在生成结构...' : '正在整理引用...')

onMounted(async () => {
  try {
    const data = await Promise.all([fetchProjects(), fetchAttachments(), fetchPapers(), fetchResults(), fetchLatexDrafts()])
    latexDrafts.value = data[4]?.data || []
  } catch (err) {
    error.value = err.message || '资料加载失败'
  } finally {
    loading.value = false
  }
})

function sourceKey(source) { return `${source.type}:${source.id}` }
function sourceLabel(type) { return { attachment: '附件', paper: '论文', result: '研究结果', project: '课题', latex: 'LaTeX 文稿' }[type] || type }
function isSelected(source) { return selectedSources.value.some(item => sourceKey(item) === sourceKey(source)) }
function toggleSource(source) { selectedSources.value = isSelected(source) ? selectedSources.value.filter(item => sourceKey(item) !== sourceKey(source)) : [...selectedSources.value, source] }
async function uploadFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try { await uploadAttachment(file); await fetchAttachments() } catch (err) { error.value = err.message || '上传失败' }
}
async function generate() {
  if (!selectedSources.value.length) return
  generating.value = true
  generateError.value = ''
  progress.value = 16
  await new Promise(resolve => setTimeout(resolve, 100))
  progress.value = 42
  try {
    const artifact = await createArtifact({
      type: selectedType.value,
      title: title.value || selectedTypeLabel.value,
      sourceRefs: selectedSources.value.map(item => ({ type: item.type, id: item.id, title: item.title })),
      config: { note: note.value, length: length.value, includeCitations: includeCitations.value, maxDepth: maxDepth.value, includeSummaries: includeSummaries.value, count: selectedType.value === 'flashcards' ? cardCount.value : questionCount.value, difficulty: difficulty.value, questionType: questionType.value, topic: tableTopic.value, maxRows: maxRows.value, extractNumbers: extractNumbers.value },
    })
    if (!artifact) throw new Error('报告创建失败')
    const finalArtifact = await waitForArtifact(artifact)
    progress.value = 100
    if (finalArtifact.status === 'failed') throw new Error(finalArtifact.errorMessage || `${selectedTypeLabel.value}生成失败`)
    await new Promise(resolve => setTimeout(resolve, 120))
    router.push({ path: '/researcher/artifacts', query: { id: finalArtifact.id } })
  } catch (err) {
    generateError.value = err.message || '报告生成失败'
  } finally {
    generating.value = false
  }
}

async function waitForArtifact(initialArtifact) {
  let artifact = initialArtifact
  if (artifact.status !== 'generating') return artifact
  const maxAttempts = 90
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 2000))
    progress.value = Math.min(95, 42 + Math.round((attempt / maxAttempts) * 50))
    artifact = await fetchArtifact(initialArtifact.id) || artifact
    if (artifact.status === 'ready' || artifact.status === 'failed') return artifact
  }
  return artifact
}
</script>

<style scoped>
.create-page{height:100%;overflow:auto;padding:36px 44px;background:#fafbfa;color:#172019}.page-header,.panel-head,.actions{display:flex;align-items:center;justify-content:space-between;gap:18px}.page-header{border-bottom:1px solid #e2e8e2;padding-bottom:22px}.page-header h1{margin:0;font-size:28px}.page-header p,.panel-head p{margin:8px 0 0;color:#758078}.quiet-button,.secondary,.primary,.upload-button{border:1px solid #d5ddd5;padding:10px 15px;background:#fff;cursor:pointer}.primary{background:#263d2e;border-color:#263d2e;color:#fff}.primary:disabled,.secondary:disabled{opacity:.5;cursor:not-allowed}.steps{display:flex;gap:28px;padding:22px 0}.steps button{border:0;border-bottom:2px solid transparent;background:none;padding:7px 0;color:#9aa49d;cursor:pointer}.steps button.active{color:#263d2e;border-color:#526e5a;font-weight:700}.panel{background:#fff;border:1px solid #e1e7e1;padding:24px}.panel h2{margin:0;font-size:18px}.panel-head{align-items:flex-start}.upload-button{background:#eef5ef;color:#31583a}.upload-button input{display:none}.source-filter{display:flex;gap:12px;margin:24px 0 16px}.source-filter input,.source-filter select,.configure input,.configure select,.configure textarea{border:1px solid #dce3dc;background:#fff;padding:10px 12px;border-radius:5px;font:inherit}.source-filter input{width:300px}.source-grid,.output-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}.source-card,.output-card{position:relative;display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-height:145px;text-align:left;border:1px solid #e1e7e1;background:#fff;padding:16px;cursor:pointer}.source-card:hover,.source-card.selected,.output-card:hover,.output-card.selected{border-color:#526e5a;background:#f5faf5}.source-card strong,.output-card strong{font-size:15px}.source-card small,.output-card small{color:#758078;line-height:1.5}.source-card em{font-style:normal;color:#97a29a;font-size:11px}.source-type{color:#526e5a;font-size:12px}.check,.selected-mark{position:absolute;right:12px;top:12px;color:#31583a;font-size:12px}.check{width:18px;height:18px;border:1px solid #bfcbbf;text-align:center}.output-card{min-height:150px}.output-card.unavailable{cursor:not-allowed;opacity:.55}.output-icon{font-weight:700;font-size:20px;color:#526e5a}.inline-empty,.state{padding:56px;text-align:center;color:#758078}.actions{padding:18px 0;color:#758078;font-size:13px}.configure{max-width:720px}.configure>label{display:grid;gap:7px;margin:22px 0;font-size:13px}.checkbox-label{display:flex!important;align-items:center;gap:8px!important}.source-summary{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.source-summary span{padding:6px 9px;background:#eef5ef;color:#526e5a;font-size:12px}.progress{margin-top:22px}.progress-bar{height:8px;background:#edf1ed;overflow:hidden}.progress-bar i{display:block;height:100%;background:#526e5a;transition:width .2s}.progress span{display:block;margin-top:8px;color:#758078;font-size:12px}.error{color:#a33b30}.error.state{color:#a33b30}@media(max-width:720px){.create-page{padding:24px 18px}.page-header,.panel-head,.actions{align-items:flex-start;flex-direction:column}.source-filter{flex-direction:column}.source-filter input{width:auto}.steps{gap:16px}.actions .primary{width:100%}}
</style>
