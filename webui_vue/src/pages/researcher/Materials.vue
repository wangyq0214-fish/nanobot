<template>
  <section class="materials-page">
    <header class="page-header">
      <div><h1>我的资料</h1><p>统一管理研究附件、论文、研究结果和课题。</p></div>
      <label class="upload-button">上传资料<input ref="fileInput" type="file" accept=".pdf,.docx,.xlsx,.csv,.txt,.md" @change="uploadFile" /></label>
    </header>

    <div class="toolbar">
      <input v-model.trim="query" placeholder="搜索资料名称或内容" />
      <select v-model="typeFilter"><option value="all">全部类型</option><option value="attachment">上传附件</option><option value="paper">论文</option><option value="result">研究结果</option><option value="project">课题</option></select>
      <span class="count">{{ filteredItems.length }} 项资料</span>
    </div>

    <div v-if="loading" class="state">正在加载资料...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <div v-else-if="!filteredItems.length" class="state empty"><strong>暂无匹配资料</strong><span>上传附件或先在工作台保存研究结果。</span></div>
    <div v-else class="resource-grid">
      <article v-for="item in filteredItems" :key="`${item.type}-${item.id}`" class="resource-card" @click="openItem(item)">
        <div class="card-top"><span class="type-mark">{{ typeLabel(item.type) }}</span><span class="date">{{ formatDate(item.date) }}</span></div>
        <h2>{{ item.title }}</h2><p>{{ item.preview || '暂无摘要' }}</p>
        <div class="card-bottom"><span>{{ item.meta }}</span><button v-if="item.type === 'attachment'" class="delete-button" title="删除附件" @click.stop="removeAttachment(item)">删除</button></div>
      </article>
    </div>

    <div v-if="selected" class="modal-mask" @click.self="selected = null">
      <article class="modal">
        <header><div><span class="type-mark">{{ typeLabel(selected.type) }}</span><h2>{{ selected.title }}</h2></div><button class="close-button" title="关闭" @click="selected = null">×</button></header>
        <dl><div><dt>来源</dt><dd>{{ selected.meta }}</dd></div><div><dt>时间</dt><dd>{{ formatDate(selected.date) }}</dd></div><div v-if="selected.projectName"><dt>课题</dt><dd>{{ selected.projectName }}</dd></div></dl>
        <div v-if="selected.type === 'result'" class="modal-detail-rendered">
          <template v-for="(part, index) in resultParts(selected)" :key="`${part.type}-${index}`">
            <div v-if="part.type === 'text' && part.content.trim()" class="result-detail-content" v-html="renderMarkdown(part.content)"></div>
            <ResearchResourceRenderer v-else-if="part.type === 'resources'" :resources="part.resources" />
          </template>
        </div>
        <pre v-else>{{ selected.detail || selected.preview || '暂无详细内容' }}</pre>
        <footer><button class="secondary" @click="selected = null">关闭</button><button v-if="selected.type === 'attachment'" class="danger" @click="removeAttachment(selected)">删除附件</button></footer>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'
import DOMPurify from 'dompurify'
import { useResearchWorkspace } from '../../composables/useResearchWorkspace.js'
import { usePaperLibrary } from '../../composables/usePaperLibrary.js'
import { useResearchResults } from '../../composables/useResearchResults.js'
import { useAuthFetch } from '../../composables/useAuthFetch.js'
import ResearchResourceRenderer from '../../components/ResearchResourceRenderer.vue'
import { researchMessageParts, stripResearchResourceBlocks } from '../../composables/useResearchResources.js'

marked.setOptions({ breaks: true, gfm: true })
marked.use(markedKatex({ throwOnError: false, output: 'html', nonStandard: true }))

const route = useRoute()
const { projects, attachments, fetchProjects, fetchAttachments, uploadAttachment } = useResearchWorkspace()
const { papers, fetchPapers } = usePaperLibrary()
const { results, fetchResults, fetchResult } = useResearchResults()
const { authMutate } = useAuthFetch()
const query = ref('')
const typeFilter = ref('all')
const loading = ref(true)
const error = ref('')
const selected = ref(null)

const projectMap = computed(() => new Map(projects.value.map(project => [String(project.id), project.name])))
const items = computed(() => [
  ...attachments.value.map(item => ({ type: 'attachment', id: item.id, title: item.fileName || '未命名附件', preview: item.summary, detail: item.summary, meta: `${item.fileType || '文件'} · ${item.parseStatus || '待解析'}`, date: item.createdAt, projectName: projectMap.value.get(String(item.projectId)) })),
  ...papers.value.map(item => ({ type: 'paper', id: item.id, title: item.title || item.fileName || '未命名论文', preview: item.aiSummary || item.abstract || '暂无摘要', detail: item.fullText || item.abstract || item.aiSummary, meta: `${item.year || '未知年份'} · ${item.authors || '作者未知'}`, date: item.updatedAt || item.createdAt })),
  ...results.value.map(item => ({ type: 'result', id: item.id, title: item.title || '未命名研究结果', preview: item.contentPreview, detail: item.content, resources: item.resources || [], meta: item.sessionTitle || '工作台保存', date: item.updatedAt || item.createdAt, projectName: item.projectName })),
  ...projects.value.map(item => ({ type: 'project', id: item.id, title: item.name || '未命名课题', preview: item.description, detail: item.description, meta: item.status || 'active', date: item.updatedAt || item.createdAt })),
])
const filteredItems = computed(() => items.value.filter(item => {
  const haystack = `${item.title} ${item.preview || ''} ${item.meta || ''}`.toLowerCase()
  return (typeFilter.value === 'all' || item.type === typeFilter.value) && (!query.value || haystack.includes(query.value.toLowerCase()))
}))

onMounted(async () => {
  try {
    await Promise.all([fetchProjects(), fetchAttachments(), fetchPapers(), fetchResults()])
    const sourceType = String(route.query.sourceType || '')
    const sourceId = String(route.query.sourceId || '')
    const source = items.value.find(item => item.type === sourceType && String(item.id) === sourceId)
    if (source) await openItem(source)
  } catch (err) {
    error.value = err.message || '资料加载失败'
  } finally {
    loading.value = false
  }
})

function typeLabel(type) { return { attachment: '附件', paper: '论文', result: '研究结果', project: '课题' }[type] || type }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('zh-CN') : '未记录' }
async function openItem(item) {
  if (item.type === 'result') {
    const full = await fetchResult(item.id)
    selected.value = { ...item, detail: full?.content || item.detail, resources: full?.resources || item.resources || [] }
  } else selected.value = item
}

function resultParts(item) {
  return researchMessageParts({
    content: item?.detail || item?.preview || '',
    resources: item?.resources || [],
  })
}

function renderMarkdown(text) {
  if (!text) return ''
  const html = marked.parse(stripResearchResourceBlocks(text))
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onclick', 'onload'],
  })
}
async function uploadFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try { await uploadAttachment(file); await fetchAttachments() } catch (err) { error.value = err.message || '上传失败' }
}
async function removeAttachment(item) {
  if (!window.confirm(`确定删除“${item.title}”吗？`)) return
  try {
    const data = await authMutate(`/api/researcher/attachments/${item.id}/delete`, {})
    if (data?.ok) {
      attachments.value = attachments.value.filter(attachment => attachment.id !== item.id)
      if (selected.value?.id === item.id && selected.value?.type === 'attachment') selected.value = null
    }
  } catch (err) { error.value = err.message || '删除失败' }
}
</script>

<style scoped>
.materials-page{height:100%;overflow:auto;padding:36px 44px;background:#fafbfa;color:#172019}.page-header,.toolbar,.card-top,.card-bottom,.modal header,.modal footer{display:flex;align-items:center;justify-content:space-between;gap:16px}.page-header{border-bottom:1px solid #e2e8e2;padding-bottom:22px}.page-header h1{margin:0;font-size:28px}.page-header p{margin:8px 0 0;color:#758078}.upload-button,.secondary,.danger{border:1px solid #d5ddd5;background:#fff;padding:10px 15px;cursor:pointer}.upload-button{background:#263d2e;color:#fff;border-color:#263d2e}.upload-button input{display:none}.toolbar{justify-content:flex-start;margin:24px 0}.toolbar input,.toolbar select{border:1px solid #dce3dc;background:#fff;padding:10px 12px;border-radius:5px}.toolbar input{width:min(360px,100%)}.count{margin-left:auto;color:#758078;font-size:13px}.resource-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}.resource-card{min-height:178px;padding:18px;border:1px solid #e1e7e1;background:#fff;cursor:pointer;transition:border-color .15s,transform .15s}.resource-card:hover{border-color:#78927e;transform:translateY(-1px)}.type-mark{display:inline-flex;padding:4px 7px;background:#edf4ee;color:#35583e;font-size:12px}.date,.card-bottom{color:#849087;font-size:12px}.resource-card h2{margin:18px 0 8px;font-size:17px}.resource-card p{color:#657069;font-size:13px;line-height:1.6;min-height:42px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.card-bottom{margin-top:16px}.delete-button{border:0;background:none;color:#a33b30;cursor:pointer}.state{padding:80px 20px;text-align:center;color:#758078}.state strong,.state span{display:block}.state span{margin-top:8px}.error{color:#a33b30}.modal-mask{position:fixed;inset:0;z-index:20;display:grid;place-items:center;background:rgba(20,30,22,.35);padding:20px}.modal{width:min(680px,100%);max-height:80vh;overflow:auto;background:#fff;padding:25px}.modal header{align-items:flex-start}.modal h2{margin:13px 0 0;font-size:22px}.close-button{border:0;background:none;font-size:26px;cursor:pointer}.modal dl{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0;padding:16px 0;border-top:1px solid #edf0ed;border-bottom:1px solid #edf0ed}.modal dt{color:#849087;font-size:12px}.modal dd{margin:5px 0 0;font-size:13px}.modal pre{white-space:pre-wrap;font:inherit;line-height:1.7;color:#334037;max-height:320px;overflow:auto}.modal-detail-rendered{max-height:440px;overflow:auto;color:#334037;line-height:1.7}.result-detail-content :deep(.katex-display){max-width:100%;box-sizing:border-box;margin:14px 0;padding:3px 2px;overflow-x:auto;overflow-y:hidden;white-space:nowrap}.result-detail-content :deep(.katex){font-size:1.1em}.modal footer{justify-content:flex-end;margin-top:24px}.danger{border-color:#d9aaa5;color:#a33b30}@media(max-width:700px){.materials-page{padding:24px 18px}.toolbar{align-items:stretch;flex-wrap:wrap}.count{width:100%;margin-left:0}.modal dl{grid-template-columns:1fr}.page-header{align-items:flex-start;flex-direction:column}}
</style>
