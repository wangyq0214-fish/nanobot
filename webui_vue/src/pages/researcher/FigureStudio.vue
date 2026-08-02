<template>
  <div class="figure-studio">
    <header class="studio-header">
      <div>
        <div class="eyebrow">研究者工具 / 科研绘图</div>
        <h1>科研图表工作台</h1>
        <p>上传原始数据，选择图表类型，AI 将字段转换为模板需要的格式并执行 Python 绘图。</p>
      </div>
      <div class="header-actions">
        <span class="status">{{ running ? '生成中' : previewUrl ? '已完成' : '待生成' }}</span>
        <button class="secondary" @click="newJob">重新开始</button>
        <button class="primary" :disabled="!canRun || running" @click="runJob">{{ running ? '正在生成...' : '生成图表' }}</button>
      </div>
    </header>

    <main class="studio-grid">
      <div class="editor-column">
        <section v-if="selectedTemplate.input === 'csv'" class="panel">
          <div class="panel-heading"><div><span>第 1 步</span><h2>上传数据</h2></div><b>{{ fileName ? '已上传' : '等待上传' }}</b></div>
          <label class="upload-zone">
            <input type="file" accept=".csv" @change="onFile" />
            <strong>{{ fileName || '选择或拖入 CSV 文件' }}</strong>
            <small>第一行应为字段名，支持中文或英文列名，最大 50 MB</small>
          </label>
          <div class="data-meta"><span>行数 <b>{{ rows || '-' }}</b></span><span>字段 <b>{{ columns.length || '-' }}</b></span><button :disabled="!fileName" @click="suggestChart">AI 自动匹配字段</button></div>
          <div v-if="dataPreview.length" class="csv-preview">
            <div class="csv-head"><b>CSV 数据内容</b><span>显示前 {{ dataPreview.length }} 行</span></div>
            <div class="table-wrap"><table><thead><tr><th v-for="column in columns" :key="column">{{ column }}</th></tr></thead><tbody><tr v-for="(row, index) in dataPreview" :key="index"><td v-for="column in columns" :key="column">{{ row[column] ?? '-' }}</td></tr></tbody></table></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-heading"><div><span>{{ selectedTemplate.input === 'csv' ? '第 2 步' : '第 1 步' }}</span><h2>选择图表类型</h2></div></div>
          <label class="field full"><span>图表类型</span><select v-model="job.template"><optgroup v-for="group in templateGroups" :key="group" :label="group"><option v-for="item in templatesByGroup(group)" :key="item.id" :value="item.id">{{ item.name }}</option></optgroup></select></label>
          <div class="template-summary"><b>{{ selectedTemplate.name }}</b><em>{{ selectedTemplate.renderer }}</em><span>{{ selectedTemplate.description }}</span></div>

          <template v-if="selectedTemplate.input === 'csv'">
            <div class="mapping-heading"><div><b>字段映射</b><span>AI 已将原始列对应到模板的语义字段，您可以手动调整。</span></div><button :disabled="!fileName" @click="suggestChart">重新匹配</button></div>
            <div class="form-grid">
              <label v-for="field in selectedTemplate.fields" :key="field.key" class="field">
                <span>{{ field.label }}{{ field.optional ? '（可选）' : '' }}</span>
                <select v-if="!field.multiple" v-model="fieldMapping[field.key]"><option value="">请选择字段</option><option v-for="column in compatibleColumns(field.type)" :key="column" :value="column">{{ column }}</option></select>
                <select v-else v-model="fieldMapping[field.key]" multiple><option v-for="column in compatibleColumns(field.type)" :key="column" :value="column">{{ column }}</option></select>
              </label>
            </div>
          </template>
          <label v-else class="field full prompt-field"><span>图形内容描述</span><textarea v-model="conceptPrompt" placeholder="说明研究主题、关键实体、作用关系、流程方向和需要强调的结论。"></textarea><small>此类模板使用文字生成图片，不需要 CSV。</small></label>

          <div v-if="selectedTemplate.params.length" class="parameter-block"><b>图表参数</b><div class="form-grid params">
            <label v-for="param in selectedTemplate.params" :key="param.key" class="field" :class="{ check: param.type === 'boolean' }">
              <template v-if="param.type === 'boolean'"><input v-model="templateParams[param.key]" type="checkbox" /><span>{{ param.label }}</span></template>
              <template v-else><span>{{ param.label }}</span><select v-if="param.type === 'select'" v-model="templateParams[param.key]"><option v-for="option in param.options" :key="option">{{ option }}</option></select><input v-else v-model.number="templateParams[param.key]" type="number" :min="Object.prototype.hasOwnProperty.call(param, 'min') ? param.min : 0" step="any" /></template>
            </label>
          </div></div>

          <div class="template-preview"><div><b>{{ selectedTemplate.name }}模板示例</b><span>示例只展示结构，生成结果使用您的数据。</span></div><img v-if="templatePreviewUrl" :src="templatePreviewUrl" :alt="`${selectedTemplate.name}模板示例`" /></div>
        </section>

        <section class="panel">
          <div class="panel-heading"><div><span>{{ selectedTemplate.input === 'csv' ? '第 3 步' : '第 2 步' }}</span><h2>标题与说明</h2></div></div>
          <label class="field full"><span>希望图表表达的结论（可选）</span><textarea v-model="job.conclusion" placeholder="例如：处理组在 48 小时的表达量显著高于对照组。"></textarea></label>
        </section>
      </div>

      <aside class="result-column">
        <section class="panel result-panel"><div class="panel-heading"><div><span>生成结果</span><h2>{{ selectedTemplate.name }}</h2></div></div>
          <div v-if="running" class="result-placeholder">AI 正在整理数据并执行绘图代码...</div>
          <div v-else-if="previewUrl" class="generated-result"><img :src="previewUrl" alt="生成的科研图表" /><a :href="previewUrl" :download="`${selectedTemplate.name}.png`">下载生成图片</a></div>
          <div v-else class="result-placeholder">生成图表后将在这里显示</div>
        </section>
        <section class="panel log-panel"><div class="panel-heading"><div><span>任务状态</span><h2>执行记录</h2></div></div><div v-for="line in logs" :key="line.time + line.text" class="log"><time>{{ line.time }}</time><b :class="line.level">{{ line.level }}</b><span>{{ line.text }}</span></div></section>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useAuthFetch } from '../../composables/useAuthFetch.js'
import { figureTemplates, templateGroups, getFigureTemplate, defaultTemplateParams } from '../../config/figureTemplates.js'

const { authGet, authPost } = useAuthFetch()
const job = ref({ template: 'volcano', conclusion: '' })
const fileName = ref('')
const rows = ref(0)
const columns = ref([])
const columnTypes = ref({})
const dataPreview = ref([])
const fieldMapping = ref({})
const templateParams = ref({})
const conceptPrompt = ref('')
const figureJobId = ref(null)
const previewUrl = ref('')
const running = ref(false)
const logs = ref([])
const selectedTemplate = computed(() => getFigureTemplate(job.value.template))
const requiredFieldsReady = computed(() => selectedTemplate.value.fields.filter(field => !field.optional).every(field => Array.isArray(fieldMapping.value[field.key]) ? fieldMapping.value[field.key].length : fieldMapping.value[field.key]))
const canRun = computed(() => selectedTemplate.value.input === 'text' ? conceptPrompt.value.trim().length >= 10 : Boolean(fileName.value && requiredFieldsReady.value))
const previewPaths = { volcano: '/nature-figure-assets/chart-atlas/atlas-04-scatter-bubble.png', roc: '/nature-figure-assets/chart-atlas/atlas-02-line-trends.png', dotplot: '/nature-figure-assets/chart-atlas/atlas-10-network-matrix.png', marginal: '/nature-figure-assets/chart-atlas/atlas-04-scatter-bubble.png', paired: '/nature-figure-assets/chart-atlas/atlas-06-distributions.png', grouped_bar: '/nature-figure-assets/chart-atlas/atlas-01-bar-charts.png', scatter: '/nature-figure-assets/chart-atlas/atlas-04-scatter-bubble.png', line: '/nature-figure-assets/chart-atlas/atlas-02-line-trends.png', heatmap: '/nature-figure-assets/chart-atlas/atlas-03-heatmaps.png', mechanism_schematic: '/nature-figure-assets/gallery/fig1-material-mechanism-rich.png', graphical_abstract: '/nature-figure-assets/gallery/fig4-single-cell-systems-rich.png' }
const templatePreviewUrl = computed(() => previewPaths[job.value.template] || '')

function templatesByGroup(group) { return figureTemplates.filter(item => item.category === group) }
function compatibleColumns(type) { return type === 'any' ? columns.value : columns.value.filter(column => !columnTypes.value[column] || columnTypes.value[column] === type) }
function resetTemplateState() { fieldMapping.value = Object.fromEntries(selectedTemplate.value.fields.map(field => [field.key, field.multiple ? [] : ''])); templateParams.value = defaultTemplateParams(selectedTemplate.value); previewUrl.value = '' }
watch(() => job.value.template, resetTemplateState, { immediate: true })
function addLog(level, text) { logs.value.unshift({ time: new Date().toLocaleTimeString(), level, text }) }
async function ensureJob() { if (figureJobId.value) return figureJobId.value; const response = await authPost('/api/researcher/figure-jobs/create', { name: `${selectedTemplate.value.name}任务` }); figureJobId.value = response.data.id; return figureJobId.value }
async function onFile(event) {
  const file = event.target.files?.[0]; if (!file) return
  try { const id = await ensureJob(); const reader = new FileReader(); reader.onload = async () => { try { const response = await authPost(`/api/researcher/figure-jobs/${id}/data`, { fileName: file.name, fileData: reader.result }); const schema = response.data.schema; fileName.value = file.name; rows.value = schema.rows; columns.value = schema.columns.map(item => item.name); columnTypes.value = Object.fromEntries(schema.columns.map(item => [item.name, item.type])); dataPreview.value = schema.preview || []; addLog('成功', `已读取 ${file.name}：${schema.rows} 行，${schema.columns.length} 个字段`); await suggestChart() } catch (error) { addLog('失败', error.message) } }; reader.readAsDataURL(file) } catch (error) { addLog('失败', error.message) }
}
async function suggestChart() {
  if (!fileName.value || selectedTemplate.value.input !== 'csv') return
  try { const id = await ensureJob(); const response = await authPost(`/api/researcher/figure-jobs/${id}/normalize`, { templateId: job.value.template }); const mapping = response.data.mapping || {}; for (const field of selectedTemplate.value.fields) fieldMapping.value[field.key] = mapping[field.key] ?? (field.multiple ? [] : ''); addLog(response.data.valid ? '成功' : '提示', response.data.valid ? 'AI 已完成模板字段匹配' : response.data.errors.join('；')) } catch (error) { addLog('失败', error.message) }
}
async function runJob() {
  try { running.value = true; previewUrl.value = ''; const id = await ensureJob(); const response = await authPost(`/api/researcher/figure-jobs/${id}/template`, { templateId: job.value.template, mapping: fieldMapping.value, params: templateParams.value, prompt: conceptPrompt.value, conclusion: job.value.conclusion }); if (!response.data.valid) throw new Error(response.data.errors.join('；')); await authPost(`/api/researcher/figure-jobs/${id}/preview`, {}); addLog('执行', selectedTemplate.value.input === 'csv' ? '已提交 Python 绘图任务' : '已提交图片生成任务'); pollJob(id) } catch (error) { running.value = false; addLog('失败', error.message) }
}
async function pollJob(id) { try { const response = await authGet(`/api/researcher/figure-jobs/${id}`); const current = response.data; if (['succeeded', 'preview_ready'].includes(current.status)) { running.value = false; previewUrl.value = current.result?.previewData || ''; addLog('成功', '图片生成完成'); return } if (current.status === 'failed') { running.value = false; addLog('失败', current.errorMessage || '绘图任务失败'); return } setTimeout(() => pollJob(id), 1000) } catch (error) { running.value = false; addLog('失败', error.message) } }
function newJob() { figureJobId.value = null; fileName.value = ''; rows.value = 0; columns.value = []; columnTypes.value = {}; dataPreview.value = []; conceptPrompt.value = ''; job.value.conclusion = ''; logs.value = []; resetTemplateState() }
</script>

<style scoped>
:global(*){box-sizing:border-box}.figure-studio{min-height:100vh;padding:30px 38px 50px;background:#f5f7f5;color:#243128;font-family:Inter,"Microsoft YaHei",sans-serif}.studio-header{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:22px}.eyebrow,.panel-heading span{color:#66806e;font-size:11px;font-weight:700}.studio-header h1{margin:7px 0 6px;font-size:27px;letter-spacing:0}.studio-header p{margin:0;color:#7a877e;font-size:13px}.header-actions{display:flex;align-items:center;gap:9px}.status{padding:7px 10px;border:1px solid #d9e2db;border-radius:999px;color:#65766a;font-size:11px}.primary,.secondary,.data-meta button,.mapping-heading button{height:38px;padding:0 14px;border:0;border-radius:6px;font:inherit;font-size:12px;font-weight:700;cursor:pointer}.primary{background:#466451;color:white}.secondary,.data-meta button,.mapping-heading button{background:#e9efea;color:#466451}.primary:disabled,button:disabled{opacity:.5;cursor:not-allowed}.studio-grid{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(340px,.8fr);gap:18px}.editor-column,.result-column{display:flex;flex-direction:column;gap:16px}.panel{padding:20px;background:white;border:1px solid #e0e7e1;border-radius:8px}.panel-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}.panel-heading h2{margin:4px 0 0;font-size:16px}.panel-heading>b{color:#6d7d72;font-size:11px}.upload-zone{min-height:94px;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px dashed #b7c9bb;border-radius:7px;background:#fafcfb;cursor:pointer}.upload-zone input{display:none}.upload-zone strong{font-size:13px}.upload-zone small{margin-top:6px;color:#929e95;font-size:11px}.data-meta{display:flex;align-items:center;gap:22px;margin-top:12px;color:#7f8c83;font-size:11px}.data-meta button{margin-left:auto;height:32px}.csv-preview{margin-top:14px;border:1px solid #e2e8e3;border-radius:6px;overflow:hidden}.csv-head{display:flex;justify-content:space-between;padding:10px 12px;background:#f7faf8;font-size:11px}.csv-head span{color:#8a978e}.table-wrap{max-height:280px;overflow:auto}table{min-width:100%;border-collapse:collapse;white-space:nowrap;font-size:11px}th,td{padding:8px 10px;border-top:1px solid #e9eeea;border-right:1px solid #e9eeea;text-align:left}th{position:sticky;top:0;background:#f1f5f2;color:#506258}.field{display:flex;flex-direction:column;gap:7px;color:#66746a;font-size:11px;font-weight:700}.field select,.field input,.field textarea{width:100%;min-height:38px;padding:8px 10px;border:1px solid #dbe3dc;border-radius:6px;background:white;color:#304037;font:inherit;font-weight:400}.field select[multiple]{min-height:92px}.field textarea{min-height:86px;resize:vertical}.field.full{grid-column:1/-1}.template-summary{display:flex;gap:10px;align-items:baseline;margin:12px 0 16px;padding:11px 12px;background:#f4f8f5;border-left:3px solid #6d8a74}.template-summary b{font-size:13px}.template-summary span{color:#76847a;font-size:11px}.mapping-heading{display:flex;align-items:center;justify-content:space-between;margin:17px 0 12px}.mapping-heading b,.mapping-heading span{display:block}.mapping-heading b,.parameter-block>b{font-size:12px}.mapping-heading span{margin-top:3px;color:#8a978e;font-size:10px}.mapping-heading button{height:31px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.parameter-block{margin-top:18px;padding-top:16px;border-top:1px solid #edf1ed}.form-grid.params{margin-top:11px}.field.check{min-height:38px;flex-direction:row;align-items:center;padding:8px 10px;border:1px solid #dbe3dc;border-radius:6px}.field.check input{width:15px;min-height:15px;accent-color:#526e5a}.prompt-field small{color:#8c988f;font-weight:400}.template-preview{margin-top:18px;padding:12px;border:1px solid #e0e7e1;border-radius:6px;background:#fafcfb}.template-preview>div{margin-bottom:10px}.template-preview b,.template-preview span{display:block}.template-preview b{font-size:12px}.template-preview span{margin-top:3px;color:#8c988f;font-size:10px}.template-preview img{display:block;width:100%;max-height:350px;object-fit:contain;background:white;border:1px solid #e8ede9}.result-panel{position:sticky;top:18px}.result-placeholder{min-height:390px;display:grid;place-items:center;border:1px dashed #c5d3c8;border-radius:6px;background:#fafcfb;color:#8b998f;font-size:12px}.generated-result{text-align:center}.generated-result img{display:block;width:100%;max-height:520px;object-fit:contain;border:1px solid #e4eae5}.generated-result a{display:inline-block;margin-top:12px;padding:9px 14px;border-radius:6px;background:#466451;color:white;font-size:12px;text-decoration:none}.log{display:grid;grid-template-columns:72px 38px 1fr;gap:7px;padding:9px 0;border-top:1px solid #edf1ed;font-size:11px}.log time{color:#939f96}.log b{color:#52765e}.log b.失败{color:#a4534d}.log b.提示{color:#a47436}.log span{color:#526058}@media(max-width:900px){.figure-studio{padding:22px 16px 40px}.studio-header{flex-direction:column}.header-actions{flex-wrap:wrap}.studio-grid{grid-template-columns:1fr}.result-panel{position:static}.form-grid{grid-template-columns:1fr}}
</style>
