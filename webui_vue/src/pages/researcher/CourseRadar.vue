<template>
  <div class="topic-page">
    <header class="page-header">
      <div><h1>前沿课程选题</h1><p>把值得持续研究的方向整理成课题，并集中管理相关论文和 AI 报告。</p></div>
      <button class="primary" @click="showCreate = true">新建课题</button>
    </header>

    <div class="toolbar"><input v-model="query" placeholder="搜索课题名称或说明" /><span>{{ projects.length }} 个课题</span></div>
    <main class="workspace">
      <section class="project-list">
        <button v-for="project in filteredProjects" :key="project.id" class="project-row" :class="{ selected: selected?.id === project.id }" @click="selectProject(project)">
          <strong>{{ project.name }}</strong><span>{{ project.description || '暂无说明' }}</span><small>{{ formatDate(project.updatedAt || project.createdAt) }}</small>
        </button>
        <div v-if="!loading && filteredProjects.length === 0" class="empty">暂无课题，先新建一个课题。</div>
        <div v-if="loading" class="empty">正在加载课题...</div>
      </section>

      <section v-if="selected" class="detail">
        <div class="detail-head"><div><span class="eyebrow">研究课题</span><h2>{{ selected.name }}</h2><p>{{ selected.description || '暂无说明' }}</p></div><button class="icon-btn" title="关闭" @click="selected = null">×</button></div>
        <div class="tabs"><button :class="{ active: tab === 'papers' }" @click="tab = 'papers'">关联论文（{{ linkedPaperIds.length }}）</button><button :class="{ active: tab === 'results' }" @click="tab = 'results'">AI 报告（{{ linkedResultIds.length }}）</button></div>

        <div v-if="tab === 'papers'" class="resource-list"><label v-for="paper in papers" :key="paper.id" class="resource-row"><input type="checkbox" :checked="linkedPaperIds.includes(paper.id)" @change="togglePaper(paper.id)" /><span><strong>{{ paper.title || paper.fileName || '未命名论文' }}</strong><small>{{ paper.authors || '' }} {{ paper.year ? `· ${paper.year}` : '' }}</small></span></label><div v-if="!papers.length" class="empty">论文库暂无内容，请先导入论文。</div></div>
        <div v-else class="resource-list"><label v-for="result in results" :key="result.id" class="resource-row"><input type="checkbox" :checked="linkedResultIds.includes(result.id)" @change="toggleResult(result.id)" /><span><strong>{{ result.title || result.sessionTitle || '未命名研究报告' }}</strong><small>{{ result.contentPreview || 'AI 研究成果' }}</small></span></label><div v-if="!results.length" class="empty">暂无 AI 研究报告，请先在工作台保存研究成果。</div></div>
      </section>
      <section v-else class="placeholder"><h2>选择一个课题</h2><p>查看并关联论文、AI 报告。</p></section>
    </main>

    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false"><form class="modal" @submit.prevent="createProject"><h2>新建课题</h2><label>课题名称<input v-model.trim="form.name" required maxlength="120" /></label><label>课题说明<textarea v-model.trim="form.description" rows="4" maxlength="500"></textarea></label><p v-if="createError" class="error">{{ createError }}</p><div class="modal-actions"><button type="button" @click="showCreate = false">取消</button><button class="primary" type="submit" :disabled="creating">{{ creating ? '创建中...' : '创建课题' }}</button></div></form></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useResearchWorkspace } from '../../composables/useResearchWorkspace.js'
import { usePaperLibrary } from '../../composables/usePaperLibrary.js'
import { useResearchResults } from '../../composables/useResearchResults.js'

const { projects, loadingProjects, fetchProjects, createProject: apiCreateProject, fetchProjectLinks, replaceProjectLinks, migrateProjectLinks } = useResearchWorkspace()
const { papers, fetchPapers } = usePaperLibrary()
const { results, fetchResults } = useResearchResults()
const selected = ref(null); const query = ref(''); const tab = ref('papers'); const showCreate = ref(false); const creating = ref(false); const createError = ref(''); const form = ref({ name: '', description: '' })
const links = ref({})
const loading = computed(() => loadingProjects.value)
const filteredProjects = computed(() => projects.value.filter(p => `${p.name} ${p.description || ''}`.toLowerCase().includes(query.value.toLowerCase())))
const currentLinks = computed(() => links.value[selected.value?.id] || { paperIds: [], resultIds: [] })
const linkedPaperIds = computed(() => currentLinks.value.paperIds || [])
const linkedResultIds = computed(() => currentLinks.value.resultIds || [])
onMounted(async () => {
  await Promise.all([fetchProjects(), fetchPapers(), fetchResults()])
  const legacy = localStorage.getItem('researcher:topic-links')
  if (legacy) {
    try { await migrateProjectLinks(JSON.parse(legacy)); localStorage.removeItem('researcher:topic-links') } catch (error) { console.warn('project link migration failed', error) }
  }
})
async function selectProject(project) {
  selected.value = project; tab.value = 'papers'
  const data = await fetchProjectLinks(project.id)
  if (data) links.value = { ...links.value, [project.id]: data }
}
async function updateLinks(type, id) {
  if (!selected.value) return
  const current = links.value[selected.value.id] || { paperIds: [], resultIds: [] }
  const key = type === 'papers' ? 'paperIds' : 'resultIds'
  const next = { ...current, [key]: current[key].includes(id) ? current[key].filter(item => item !== id) : [...current[key], id] }
  const saved = await replaceProjectLinks(selected.value.id, next)
  if (saved) links.value = { ...links.value, [selected.value.id]: saved }
}
function togglePaper(id) { updateLinks('papers', id) }
function toggleResult(id) { updateLinks('results', id) }
async function createProject() { if (!form.value.name) return; creating.value = true; createError.value = ''; try { const project = await apiCreateProject(form.value.name, form.value.description); if (!project) throw new Error('创建失败'); showCreate.value = false; form.value = { name: '', description: '' }; selectProject(project) } catch (error) { createError.value = error.message || '创建失败，请重试' } finally { creating.value = false } }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('zh-CN') : '' }
</script>

<style scoped>
.topic-page{height:100%;overflow:auto;padding:32px 40px;background:#fff;color:#171717}.page-header,.toolbar,.detail-head{display:flex;align-items:center;justify-content:space-between;gap:16px}h1{margin:0;font-size:24px}h2{margin:6px 0;font-size:20px}.page-header p,.detail-head p{margin:7px 0;color:#777;font-size:13px}.primary{border:1px solid #526e5a;background:#526e5a;color:#fff;padding:9px 14px;cursor:pointer}.toolbar{margin:28px 0 14px}.toolbar input{width:320px;border:1px solid #ddd;padding:10px 12px}.toolbar span{color:#888;font-size:12px}.workspace{display:grid;grid-template-columns:minmax(360px,1fr) minmax(420px,1.2fr);gap:16px;align-items:start}.project-list,.detail,.placeholder{border:1px solid #e5e5e5;background:#fff}.project-row{display:grid;gap:6px;width:100%;padding:16px;text-align:left;border:0;border-bottom:1px solid #eee;background:#fff;cursor:pointer}.project-row:hover,.project-row.selected{background:#f6f8f6}.project-row span,.project-row small{color:#777;font-size:12px}.empty,.placeholder{padding:36px;color:#888;text-align:center}.detail{padding:20px}.eyebrow{color:#526e5a;font-size:12px}.icon-btn{border:0;background:none;font-size:24px;cursor:pointer}.tabs{display:flex;gap:18px;margin:24px 0 10px;border-bottom:1px solid #eee}.tabs button{border:0;background:none;padding:10px 0;color:#777;cursor:pointer}.tabs button.active{color:#171717;border-bottom:2px solid #526e5a}.resource-row{display:flex;gap:10px;padding:14px 4px;border-bottom:1px solid #eee;cursor:pointer}.resource-row input{margin-top:3px}.resource-row span{display:grid;gap:5px;min-width:0}.resource-row small{color:#777;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.modal-mask{position:fixed;inset:0;display:grid;place-items:center;background:rgba(0,0,0,.3);z-index:10}.modal{width:min(440px,calc(100vw - 32px));padding:24px;background:#fff}.modal label{display:grid;gap:7px;margin:16px 0;font-size:13px}.modal input,.modal textarea{border:1px solid #ddd;padding:9px;font:inherit}.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:20px}.modal-actions button{border:1px solid #ddd;background:#fff;padding:9px 14px;cursor:pointer}.modal-actions .primary{border-color:#526e5a}.error{color:#b42318;font-size:13px}@media(max-width:900px){.topic-page{padding:24px 20px}.workspace{grid-template-columns:1fr}.toolbar input{width:100%}.toolbar{align-items:stretch;flex-direction:column}}
</style>
