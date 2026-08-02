<template>
<div class="assign-layout">
  <div class="assign-topbar">
    <h1 class="at-title">布置任务</h1>
    <div class="at-tabs">
      <span :class="{ on: activeTab === 'questionBank' }" @click="activeTab = 'questionBank'">创建题库</span>
      <span :class="{ on: activeTab === 'homework' }" @click="activeTab = 'homework'">布置作业</span>
      <span :class="{ on: activeTab === 'exam' }" @click="activeTab = 'exam'">布置考试</span>
    </div>
  </div>

  <!-- ===== 题库 ===== -->
  <div v-if="activeTab === 'questionBank'" class="assign-body">
    <aside class="panel panel-left">
      <div class="pl-head">
        <span class="pl-title">题库</span>
        <div style="display:flex;align-items:center;gap:8px">
          <select v-model="qbCourseFilter" style="padding:4px 8px;border:1px solid var(--border-light);border-radius:8px;font-size:0.68rem;color:var(--text-primary);background:var(--bg-card);outline:none;max-width:120px">
            <option value="">全部课程</option>
            <option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option>
          </select>
          <span class="pl-count">{{ filteredQuestions.length }} 题</span>
        </div>
      </div>
      <div class="pl-search">
        <svg viewBox="0 0 20 20" width="14" height="14"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
        <input v-model="qbSearch" placeholder="搜索题目..." />
      </div>
      <div class="pl-filters">
        <span class="pl-chip" :class="{ on: qbTypeFilter === 'all' }" @click="qbTypeFilter = 'all'">全部</span>
        <span class="pl-chip" :class="{ on: qbTypeFilter === 'choice' }" @click="qbTypeFilter = 'choice'">选择题</span>
        <span class="pl-chip" :class="{ on: qbTypeFilter === 'essay' }" @click="qbTypeFilter = 'essay'">简答题</span>
        <span class="pl-chip" :class="{ on: qbTypeFilter === 'image' }" @click="qbTypeFilter = 'image'">图文题</span>
      </div>
      <div class="pl-list">
        <div v-for="(q, qi) in filteredQuestions" :key="q.id" class="pl-item" :class="{ active: editingQId === q.id }" @click="editingQId = q.id">
          <span class="pl-item-type" :class="q.questionType">{{ TYPE_MAP[q.questionType] || q.questionType }}</span>
          <span class="pl-item-stem">{{ (q.content||'').slice(0, 40) }}{{ (q.content||'').length > 40 ? '...' : '' }}</span>
        </div>
        <div v-if="filteredQuestions.length === 0" class="pl-empty">暂无题目</div>
      </div>
      <div class="pl-foot">
        <div class="pl-foot-actions">
          <button class="pl-add-btn" @click="editingQId = -1">+ 新建题目</button>
          <button class="pl-import-btn" @click="showBatchImport = true">批量导入</button>
          <button class="pl-ai-btn" @click="showAiGen = true">AI 生成</button>
        </div>
      </div>
    </aside>

    <section class="panel panel-center">
      <div v-if="!editingQId && editingQId !== -1" class="center-empty">
        <div class="empty-icon-wrap"><svg viewBox="0 0 20 20"><ellipse cx="10" cy="5" rx="7" ry="3"/><path d="M3 5v10a7 3 0 0 0 14 0V5"/></svg></div>
        <p class="empty-title">选择左侧题目查看</p>
        <p class="empty-desc">或点击"新建题目"开始创建</p>
      </div>
      <div v-else class="center-scroll">
        <div class="student-bar">
          <div class="sb-left"><div class="sb-avatar">{{ editingQId === -1 ? '+' : '✎' }}</div><div><div class="sb-name">{{ editingQId === -1 ? '新建题目' : '编辑题目' }}</div></div></div>
          <button v-if="editingQId !== -1" class="sb-act" @click="editingQId = null">取消</button>
        </div>
        <!-- 新建/编辑表单 -->
        <template v-if="editingQId === -1">
          <div class="form-card"><div class="form-inner">
            <div class="ff-row"><div class="ff"><label>题型</label><select v-model="newQ.type"><option value="choice">选择题</option><option value="essay">简答题</option><option value="image">图文题</option></select></div><div class="ff"><label>分值</label><input type="number" v-model.number="newQ.points" min="1" max="100" /></div></div>
            <div class="ff"><label>所属课程（可选）</label><select v-model="newQ.courseId"><option value="">全局题库</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div>
            <div class="ff"><label>题目内容</label><textarea v-model="newQ.stem" rows="3" placeholder="请输入题目内容..."></textarea></div>

            <!-- 选择题专属：选项 -->
            <template v-if="newQ.type==='choice'">
              <div class="ff"><label>选项设置</label></div>
              <div v-for="(opt, oi) in newQ.optionsList" :key="oi" class="ff-row" style="align-items:center">
                <span style="font-weight:700;width:20px">{{ opt.key }}.</span>
                <input v-model="opt.text" :placeholder="'选项'+opt.key" style="flex:1" />
                <button class="btn-sm-del" @click="newQ.optionsList.splice(oi,1)" v-if="newQ.optionsList.length>2">×</button>
              </div>
              <button class="btn-add-opt" @click="newQ.optionsList.push({key: String.fromCharCode(65+newQ.optionsList.length), text:''})" v-if="newQ.optionsList.length<6">+ 添加选项</button>
              <div class="ff" style="margin-top:8px"><label>正确答案</label>
                <select v-model="newQ.answer"><option v-for="o in newQ.optionsList" :key="o.key" :value="o.key">{{o.key}}. {{o.text||'选项'+o.key}}</option></select>
              </div>
            </template>

            <!-- 简答题专属：参考答案 -->
            <div class="ff" v-if="newQ.type==='essay'"><label>参考答案</label><textarea v-model="newQ.answer" rows="2" placeholder="输入参考答案..."></textarea></div>

            <!-- 图文题专属：图片提示 -->
            <div class="ff" v-if="newQ.type==='image'"><label>参考答案或判断要点</label><input v-model="newQ.answer" placeholder="如：水稻纹枯病(云纹状病斑)" /></div>

            <div class="ff"><label>标签（逗号分隔）</label><input v-model="newQ.tags" placeholder="如：水稻,纹枯病,真菌" /></div>
            <div class="ff-actions"><button class="btn-cancel" @click="editingQId = null">取消</button><button class="btn-primary" @click="createQ">保存题目</button></div>
          </div></div>
        </template>
        <template v-else>
          <div class="form-card"><div class="form-inner">
            <div class="ff-qstem">{{ activeQ?.content }}</div>
            <div class="ff-qmeta"><span class="ff-qtype">{{ TYPE_MAP[activeQ?.questionType] || activeQ?.questionType }}</span><span v-for="t in (activeQ?.tags||[])" :key="t" class="ff-qtags">{{ t }}</span><span>{{ activeQ?.points }}分</span></div>
            <div v-if="activeQ?.options?.length" style="margin-top:10px"><div class="ff" v-for="o in activeQ.options" :key="o.key"><span style="font-weight:700">{{o.key}}.</span> {{o.text}}</div></div>
            <div v-if="activeQ?.answer" style="margin-top:10px"><span style="font-size:0.66rem;font-weight:700;color:var(--text-muted)">答案：</span><span style="font-size:0.8rem;color:#526e5a">{{ activeQ.answer }}</span></div>
          </div></div>
        </template>
      </div>
    </section>
  </div>

  <!-- ===== 布置作业 ===== -->
  <div v-if="activeTab === 'homework'" class="assign-body">
    <aside class="panel panel-left">
      <div class="pl-head"><span class="pl-title">从题库选题</span><span class="pl-count">{{ hwForm.selectedIds.length }} 已选</span></div>
      <div class="pl-search">
        <svg viewBox="0 0 20 20" width="14" height="14"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
        <input v-model="hwPickerSearch" placeholder="搜索题目..." />
      </div>
      <div class="pl-list">
        <div v-for="q in hwFilteredPicker" :key="q.id" class="pl-item" :class="{ selected: hwForm.selectedIds.includes(q.id) }" @click="toggleQ(q.id)">
          <span class="pl-check">{{ hwForm.selectedIds.includes(q.id) ? '✓' : '' }}</span>
          <span class="pl-item-type" :class="q.questionType">{{ TYPE_MAP[q.questionType] || q.questionType }}</span>
          <span class="pl-item-stem">{{ (q.content||'').slice(0, 30) }}{{ (q.content||'').length > 30 ? '...' : '' }}</span>
        </div>
      </div>
    </aside>

    <section class="panel panel-center">
      <div class="center-scroll">
        <div class="student-bar"><div class="sb-left"><div class="sb-avatar">📝</div><div><div class="sb-name">布置新作业</div></div></div></div>
        <div class="form-card"><div class="form-inner">
          <div class="ff"><label>作业标题</label><input v-model="hwForm.title" placeholder="如：水稻纹枯病田间识别与防治方案" /></div>
          <div class="ff-row"><div class="ff"><label>目标课程</label><select v-model="hwForm.courseId"><option value="">选择课程...</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div><div class="ff"><label>截止日期</label><input type="datetime-local" v-model="hwForm.deadline" /></div></div>
          <div class="ff"><label>作业说明</label><textarea v-model="hwForm.description" rows="2" placeholder="描述作业要求、评分标准..."></textarea></div>
          <div class="ff-summary">已选 <b>{{ hwForm.selectedIds.length }}</b> 道题</div>
          <div class="ff-actions"><button class="btn-cancel" @click="saveHomeworkDraft">保存草稿</button><button class="btn-primary" @click="publishHomework">发布作业</button></div>
        </div></div>
      </div>
    </section>
  </div>

  <!-- ===== 布置考试 ===== -->
  <div v-if="activeTab === 'exam'" class="assign-body">
    <aside class="panel panel-left">
      <div class="pl-head"><span class="pl-title">从题库选题</span><span class="pl-count">{{ examForm.selectedIds.length }} 已选</span></div>
      <div class="pl-search">
        <svg viewBox="0 0 20 20" width="14" height="14"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
        <input v-model="examPickerSearch" placeholder="搜索题目..." />
      </div>
      <div class="pl-list">
        <div v-for="q in examFilteredPicker" :key="q.id" class="pl-item" :class="{ selected: examForm.selectedIds.includes(q.id) }" @click="toggleExamQ(q.id)">
          <span class="pl-check">{{ examForm.selectedIds.includes(q.id) ? '✓' : '' }}</span>
          <span class="pl-item-type" :class="q.questionType">{{ TYPE_MAP[q.questionType] || q.questionType }}</span>
          <span class="pl-item-stem">{{ (q.content||'').slice(0, 30) }}{{ (q.content||'').length > 30 ? '...' : '' }}</span>
        </div>
      </div>
    </aside>

    <section class="panel panel-center">
      <div class="center-scroll">
        <div class="student-bar"><div class="sb-left"><div class="sb-avatar">📋</div><div><div class="sb-name">创建考试</div></div></div></div>
        <div class="form-card"><div class="form-inner">
          <div class="ff"><label>考试名称</label><input v-model="examForm.title" placeholder="如：植物病理学期中考试" /></div>
          <div class="ff-row"><div class="ff"><label>目标课程</label><select v-model="examForm.courseId"><option value="">选择课程...</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div><div class="ff"><label>时长（分钟）</label><input type="number" v-model="examForm.duration" min="10" max="180" /></div></div>
          <div class="ff-row"><div class="ff"><label>开始时间</label><input type="datetime-local" v-model="examForm.startTime" /></div><div class="ff"><label>结束时间</label><input type="datetime-local" v-model="examForm.endTime" /></div></div>
          <div class="ff"><label>防作弊设置</label><div class="ff-checks"><label><input type="checkbox" v-model="examForm.antiCheat.shuffleQuestions" /><span>题目乱序</span></label><label><input type="checkbox" v-model="examForm.antiCheat.shuffleOptions" /><span>选项乱序</span></label><label><input type="checkbox" v-model="examForm.antiCheat.noCopy" /><span>禁止复制</span></label></div></div>
          <div class="ff-summary">已选 <b>{{ examForm.selectedIds.length }}</b> 道题</div>
          <div class="ff-actions"><button class="btn-cancel" @click="saveExamDraft">保存草稿</button><button class="btn-primary" @click="publishExam">发布考试</button></div>
        </div></div>
      </div>
    </section>
  </div>
  <!-- 批量导入弹窗 -->
  <Teleport to="body">
    <div v-if="showBatchImport" class="modal-overlay" @click.self="showBatchImport = false">
      <div class="modal-panel">
        <div class="modal-header"><h3>批量导入题目</h3><button class="modal-close" @click="showBatchImport = false"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>
        <div class="modal-body">
          <div class="ff"><label>题型</label><select v-model="batchImportType"><option value="choice">选择题</option><option value="essay">简答题</option></select></div>
          <div class="ff"><label>分值</label><input type="number" v-model.number="batchImportPoints" min="1" max="100" /></div>
          <div class="ff"><label>标签</label><input v-model="batchImportTags" placeholder="逗号分隔" /></div>
          <div class="ff"><label>粘贴题目 或 上传文件</label>
            <textarea v-model="batchImportText" rows="6" class="grade-textarea" placeholder="每行一题，用 | 分隔字段&#10;选择题：题目|A|选项A|B|选项B|C|选项C|D|选项D|正确答案&#10;简答题：题目|参考答案"></textarea>
            <div style="display:flex;gap:8px;align-items:center;margin-top:4px">
              <span v-if="batchImportType==='choice'" style="font-size:0.64rem;color:var(--text-muted)">格式：题目|A|选项A|B|选项B|...|正确答案</span>
              <span v-else style="font-size:0.64rem;color:var(--text-muted)">格式：题目|参考答案</span>
              <span style="flex:1"></span>
              <label class="file-upload-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                上传文件
                <input type="file" hidden accept=".txt,.csv,.json" @change="handleFileImport" />
              </label>
            </div>
            <p v-if="batchImportFileName" style="font-size:0.64rem;color:#526e5a">{{ batchImportFileName }}</p>
          </div>
          <p v-if="batchImportPreview.length" class="ff-summary">预览：{{ batchImportPreview.length }} 题</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showBatchImport = false">取消</button>
          <button class="btn-primary" @click="doBatchImport" :disabled="!batchImportText.trim()">导入</button>
        </div>
      </div>
    </div>

    <!-- AI 生成弹窗 -->
    <div v-if="showAiGen" class="modal-overlay" @click.self="showAiGen = false">
      <div class="modal-panel">
        <div class="modal-header"><h3>AI 生成题目</h3><button class="modal-close" @click="showAiGen = false"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>
        <div class="modal-body">
          <div class="ff"><label>知识点/主题</label><input v-model="aiGenTopic" placeholder="如：水稻纹枯病、农药配比、昆虫分类..." /></div>
          <div class="ff-row"><div class="ff"><label>题目数量</label><input type="number" v-model.number="aiGenCount" min="1" max="10" /></div><div class="ff"><label>题型</label><select v-model="aiGenType"><option value="mixed">混合</option><option value="choice">选择题</option><option value="essay">简答题</option></select></div></div>
          <div class="ff"><label>难度</label><select v-model="aiGenDifficulty"><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option></select></div>
          <p v-if="aiGenResult" class="ff-summary" style="color:#526e5a">{{ aiGenResult }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAiGen = false">取消</button>
          <button class="btn-primary" @click="doAiGenerate" :disabled="aiGenLoading || !aiGenTopic.trim()">
            {{ aiGenLoading ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../../composables/useCourse.js'
import { useAuth } from '../../composables/useAuth.js'
import { useAuthFetch } from '../../composables/useAuthFetch.js'

const route = useRoute()
const { courses, fetchCourses } = useCourse()
const { user } = useAuth()
const { authGet, authMutate } = useAuthFetch()
const activeTab = ref(route.query.tab || 'questionBank')
watch(() => route.query.tab, (val) => { if (val) activeTab.value = val })

// ===== 题库（全局） =====
const qbSearch = ref('')
const qbTypeFilter = ref('all')
const qbCourseFilter = ref('')
const editingQId = ref(null)
const allQuestions = ref([])
const newQ = ref({ type: 'choice', stem: '', answer: '', optionsList: [{key:'A',text:''},{key:'B',text:''}], tags: '', points: 10, courseId: '' })

const TYPE_MAP = { choice: '选择题', essay: '简答题', image: '图文题', short_answer: '简答题' }
const REV_MAP = { '选择题': 'choice', '简答题': 'essay', '图文题': 'image' }

async function fetchAllQuestions() {
  try {
    const u = user.value; if (!u) return
    const qs = []
    // Fetch question bank for each course the teacher owns
    for (const c of courses.value) {
      if (c.teacherId === u.userId) {
        const d = await authGet(`/api/courses/${c.courseId}/question-bank`)
        if (d.questions) qs.push(...d.questions)
      }
    }
    allQuestions.value = qs
  } catch(e) { console.warn('fetch questions:', e) }
}

const filteredQuestions = computed(() => {
  let qs = allQuestions.value
  if (qbCourseFilter.value) qs = qs.filter(q => q.courseId === qbCourseFilter.value)
  if (qbTypeFilter.value !== 'all') qs = qs.filter(q => q.questionType === qbTypeFilter.value)
  if (qbSearch.value) qs = qs.filter(q => (q.content||'').includes(qbSearch.value) || (q.tags||[]).some(t => (t||'').includes(qbSearch.value)))
  return qs
})
const activeQ = computed(() => allQuestions.value.find(q => q.id === editingQId.value))

async function createQ() {
  try {
    const courseId = newQ.value.courseId || (courses.value.length > 0 ? courses.value[0].courseId : '')
    if (!courseId) { alert('请先选择所属课程'); return }
    const opts = newQ.value.type === 'choice' ? newQ.value.optionsList.filter(o => o.text.trim()) : []
    const tags = newQ.value.tags.split(',').map(s => s.trim()).filter(Boolean)
    const d = await authMutate(`/api/courses/${courseId}/question-bank/add`, {
      type: newQ.value.type, content: newQ.value.stem, answer: newQ.value.answer,
      options: opts, tags, points: newQ.value.points, courseId: courseId
    })
    if (d.ok) { await fetchAllQuestions(); editingQId.value = null; newQ.value = { type: 'choice', stem: '', answer: '', optionsList: [{key:'A',text:''},{key:'B',text:''}], tags: '', points: 10, courseId: '' } }
  } catch(e) { alert('创建失败: ' + e.message) }
}

// ===== 作业 & 考试共用题库 =====
const hwPickerSearch = ref('')
const hwForm = ref({ title: '', courseId: '', deadline: '', description: '', selectedIds: [] })
const hwFilteredPicker = computed(() => {
  let qs = allQuestions.value
  if (hwForm.value.courseId) qs = qs.filter(q => !q.courseId || q.courseId === hwForm.value.courseId)
  if (hwPickerSearch.value) qs = qs.filter(q => (q.content||'').includes(hwPickerSearch.value) || (q.tags||[]).some(t => (t||'').includes(hwPickerSearch.value)))
  return qs
})
function toggleQ(id) {
  const i = hwForm.value.selectedIds.indexOf(id)
  i >= 0 ? hwForm.value.selectedIds.splice(i, 1) : hwForm.value.selectedIds.push(id)
}
function saveHomeworkDraft() { alert('已保存草稿') }
function publishHomework() { alert('已发布作业') }

const examPickerSearch = ref('')
const examForm = ref({ title: '', courseId: '', duration: 60, startTime: '', endTime: '', antiCheat: { shuffleQuestions: true, shuffleOptions: true, noCopy: true }, selectedIds: [] })
const examFilteredPicker = computed(() => {
  let qs = allQuestions.value
  if (examForm.value.courseId) qs = qs.filter(q => !q.courseId || q.courseId === examForm.value.courseId)
  if (examPickerSearch.value) qs = qs.filter(q => (q.content||'').includes(examPickerSearch.value) || (q.tags||[]).some(t => (t||'').includes(examPickerSearch.value)))
  return qs
})
function toggleExamQ(id) { const i = examForm.value.selectedIds.indexOf(id); i >= 0 ? examForm.value.selectedIds.splice(i, 1) : examForm.value.selectedIds.push(id) }
function saveExamDraft() { alert('已保存草稿') }
function publishExam() { alert('已发布考试') }

// ===== 批量导入 =====
const showBatchImport = ref(false)
const batchImportType = ref('choice')
const batchImportPoints = ref(10)
const batchImportTags = ref('')
const batchImportText = ref('')
const batchImportFileName = ref('')

function handleFileImport(e) {
  const file = e.target.files[0]
  if (!file) return
  batchImportFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => {
    let text = ev.target.result
    // Parse JSON if it's a JSON file
    if (file.name.endsWith('.json')) {
      try {
        const arr = JSON.parse(text)
        if (Array.isArray(arr)) {
          text = arr.map(q => {
            if (q.options?.length) {
              const opts = q.options.map(o => `${o.key}|${o.text}`).join('|')
              return `${q.content}|${opts}|${q.answer}`
            }
            return `${q.content}|${q.answer||''}`
          }).join('\n')
        }
      } catch {}
    }
    batchImportText.value = text
  }
  reader.readAsText(file, 'UTF-8')
}

const batchImportPreview = computed(() => {
  if (!batchImportText.value.trim()) return []
  return batchImportText.value.trim().split('\n').filter(l => l.includes('|'))
})

async function doBatchImport() {
  const lines = batchImportText.value.trim().split('\n').filter(l => l.includes('|'))
  const tags = batchImportTags.value.split(',').map(s => s.trim()).filter(Boolean)
  const questions = []
  for (const line of lines) {
    const parts = line.split('|').map(s => s.trim())
    if (batchImportType.value === 'choice' && parts.length >= 6) {
      const stem = parts[0]; const answer = parts[parts.length - 1]
      const options = []
      for (let i = 1; i < parts.length - 1; i += 2) {
        if (parts[i] && parts[i+1]) options.push({ key: parts[i], text: parts[i+1] })
      }
      questions.push({ type: 'choice', content: stem, answer, options, points: batchImportPoints.value, tags })
    } else if (batchImportType.value === 'essay' && parts.length >= 2) {
      questions.push({ type: 'essay', content: parts[0], answer: parts[1] || '', points: batchImportPoints.value, tags, options: [] })
    }
  }
  if (!questions.length) { alert('未识别到有效题目，请检查格式'); return }
  const courseId = courses.value.length > 0 ? courses.value[0].courseId : ''
  if (!courseId) { alert('请先创建课程'); return }
  try {
    const d = await authMutate(`/api/courses/${courseId}/question-bank/batch-add`, { questions })
    if (d.ok || d.questions) {
      await fetchAllQuestions()
      showBatchImport.value = false
      batchImportText.value = ''
      alert(`成功导入 ${questions.length} 题`)
    }
  } catch(e) { alert('导入失败: ' + e.message) }
}

// ===== AI 生成 =====
const showAiGen = ref(false)
const aiGenTopic = ref('')
const aiGenCount = ref(3)
const aiGenType = ref('mixed')
const aiGenDifficulty = ref('medium')
const aiGenLoading = ref(false)
const aiGenResult = ref('')

async function doAiGenerate() {
  aiGenLoading.value = true; aiGenResult.value = ''
  try {
    const courseId = courses.value.length > 0 ? courses.value[0].courseId : ''
    if (!courseId) { aiGenResult.value = '请先创建课程'; return }
    const d = await authMutate(`/api/courses/${courseId}/ai-generate-questions`, {
      content: aiGenTopic.value, num_questions: aiGenCount.value, type: aiGenType.value, difficulty: aiGenDifficulty.value
    })
    if (d.questions?.length) {
      for (const q of d.questions) {
        await authMutate(`/api/courses/${courseId}/question-bank/add`, {
          type: q.type||'essay', content: q.content, answer: q.answer||'',
          options: q.options||[], tags: q.tags||[], points: q.points||10
        })
      }
      await fetchAllQuestions()
      aiGenResult.value = `已生成并保存 ${d.questions.length} 题`
      showAiGen.value = false
    } else {
      aiGenResult.value = 'AI 暂未返回题目，请重试'
    }
  } catch(e) { aiGenResult.value = '生成失败: ' + e.message }
  finally { aiGenLoading.value = false }
}

onMounted(async () => { await fetchCourses(); await fetchAllQuestions() })
</script>

<style scoped>
* { margin:0; padding:0; box-sizing:border-box; }

.assign-layout { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.assign-topbar { display:flex; align-items:center; justify-content:space-between; padding:24px 32px 16px; flex-shrink:0; }
.at-title { font-size:1.5rem; font-weight:700; color:var(--text-primary); }
.at-tabs { display:flex; gap:2px; background:var(--bg-tag); padding:3px; border-radius:20px; }
.at-tabs span { padding:7px 16px; border-radius:18px; font-size:0.76rem; color:var(--text-muted); cursor:pointer; transition:all 0.2s; }
.at-tabs span:hover { color:var(--text-primary); }
.at-tabs span.on { background:var(--bg-card); color:#526e5a; font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,0.05); }

.assign-body { flex:1; display:flex; gap:8px; padding:0 8px 8px; overflow:hidden; }

/* Panel */
.panel { background:var(--bg-card); border:1px solid var(--border-light); border-radius:16px; display:flex; flex-direction:column; overflow:hidden; }
.panel-left { width:280px; flex-shrink:0; background:var(--bg-card); }
.panel-center { flex:1; min-width:0; }

.pl-head { display:flex; align-items:center; justify-content:space-between; padding:14px 16px 8px; flex-shrink:0; }
.pl-title { font-size:0.82rem; font-weight:700; color:var(--text-primary); }
.pl-count { font-size:0.64rem; color:var(--text-muted); background:var(--bg-tag); padding:1px 8px; border-radius:8px; }
.pl-search { display:flex; align-items:center; gap:6px; margin:8px 12px; padding:7px 10px; border:1px solid var(--border-light); border-radius:10px; color:var(--text-muted); }
.pl-search input { border:none; outline:none; background:transparent; font-size:0.72rem; color:var(--text-primary); width:100%; }
.pl-filters { display:flex; gap:4px; padding:0 12px 8px; flex-shrink:0; }
.pl-chip { padding:3px 10px; border-radius:12px; font-size:0.64rem; color:var(--text-muted); cursor:pointer; border:1px solid transparent; transition:all 0.15s; }
.pl-chip:hover { color:var(--text-primary); }
.pl-chip.on { background:var(--bg-tag); color:var(--text-primary); border-color:var(--border-light); }
.pl-list { flex:1; overflow-y:auto; padding:0 8px; }
.pl-list::-webkit-scrollbar { width:3px; }
.pl-list::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
.pl-item { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:8px; cursor:pointer; transition:all 0.15s; font-size:0.74rem; border:1px solid transparent; margin-bottom:2px; }
.pl-item:hover { background:var(--bg-card-hover); }
.pl-item.active { border-color:var(--border-light); background:var(--bg-card-hover); }
.pl-item.selected { background:rgba(82,110,90,0.04); border-color:rgba(82,110,90,0.15); }
.pl-check { width:18px; height:18px; border-radius:4px; border:1.5px solid var(--border-light); display:flex; align-items:center; justify-content:center; font-size:0.6rem; color:#526e5a; flex-shrink:0; }
.pl-item.selected .pl-check { border-color:#526e5a; background:rgba(82,110,90,0.1); }
.pl-item-type { font-size:0.56rem; font-weight:700; padding:1px 6px; border-radius:4px; flex-shrink:0; border:1px solid var(--border-light); color:var(--text-muted); }
.pl-item-type.image { color:#9d174d; border-color:rgba(157,23,77,0.2); }
.pl-item-type.choice { color:#0369a1; border-color:rgba(3,105,161,0.2); }
.pl-item-stem { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-primary); }
.pl-empty { text-align:center; padding:32px 0; color:var(--text-muted); font-size:0.72rem; }
.pl-foot { padding:10px 12px; flex-shrink:0; border-top:1px solid var(--divider); }
.pl-foot-actions { display:flex; flex-direction:column; gap:6px; }
.pl-add-btn { width:100%; padding:8px; border:1.5px dashed var(--border-light); border-radius:10px; background:transparent; color:var(--text-muted); font-size:0.74rem; cursor:pointer; transition:all 0.2s; }
.pl-add-btn:hover { border-color:#526e5a; color:#526e5a; }
.pl-import-btn { width:100%; padding:8px; border:1.5px solid var(--border-light); border-radius:10px; background:var(--bg-card); color:var(--text-muted); font-size:0.72rem; cursor:pointer; transition:all 0.2s; }
.pl-import-btn:hover { border-color:#526e5a; color:#526e5a; }
.pl-ai-btn { width:100%; padding:8px; border:1.5px solid rgba(82,110,90,0.3); border-radius:10px; background:rgba(82,110,90,0.04); color:#526e5a; font-size:0.72rem; cursor:pointer; transition:all 0.2s; }
.pl-ai-btn:hover { background:rgba(82,110,90,0.08); }

/* Center */
.center-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:8px; color:var(--text-muted); }
.empty-icon-wrap { width:48px; height:48px; border-radius:12px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; }
.empty-icon-wrap svg { width:22px; height:22px; stroke:var(--text-muted); fill:none; stroke-width:1.5; }
.empty-title { font-size:0.82rem; font-weight:600; color:var(--text-secondary); }
.empty-desc { font-size:0.7rem; color:var(--text-muted); }
.center-scroll { flex:1; overflow-y:auto; padding:20px 24px; }
.center-scroll::-webkit-scrollbar { width:4px; }
.center-scroll::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

.student-bar { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--divider); }
.sb-left { display:flex; align-items:center; gap:10px; }
.sb-avatar { width:28px; height:28px; border-radius:6px; background:var(--accent,#121212); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.72rem; }
.sb-name { font-size:0.82rem; font-weight:600; color:var(--text-primary); }
.sb-act { background:none; border:none; color:var(--text-muted); font-size:0.74rem; cursor:pointer; }

/* Form */
.form-card { border:1px solid var(--border-light); border-radius:12px; }
.form-inner { padding:20px; display:flex; flex-direction:column; gap:14px; }
.ff { display:flex; flex-direction:column; gap:6px; }
.ff label { font-size:0.66rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
.ff input, .ff select, .ff textarea { padding:9px 12px; border:1px solid var(--border-light); border-radius:10px; font-size:0.8rem; color:var(--text-primary); background:var(--bg-input,#fff); outline:none; resize:vertical; }
.ff input:focus, .ff select:focus, .ff textarea:focus { border-color:#526e5a; }
.ff-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.ff-checks { display:flex; gap:16px; }
.ff-checks label { display:flex; align-items:center; gap:6px; font-size:0.78rem; color:var(--text-primary); cursor:pointer; }
.ff-summary { font-size:0.74rem; color:var(--text-muted); padding:8px 0; }
.ff-actions { display:flex; justify-content:flex-end; gap:10px; padding-top:8px; border-top:1px solid var(--divider); }
.ff-qstem { font-size:0.9rem; color:var(--text-primary); line-height:1.7; }
.ff-qmeta { display:flex; gap:8px; align-items:center; }
.ff-qtype { font-size:0.6rem; font-weight:700; padding:2px 8px; border-radius:4px; border:1px solid var(--border-light); }
.ff-qtags { font-size:0.62rem; color:var(--text-muted); background:var(--bg-tag); padding:1px 8px; border-radius:8px; }

.btn-primary { padding:9px 20px; background:#526e5a; color:#fff; border:none; border-radius:20px; font-size:0.78rem; font-weight:600; cursor:pointer; transition:all 0.2s; }
.btn-primary:hover { opacity:0.85; }
.btn-cancel { padding:9px 20px; border:1px solid var(--border-light); background:var(--bg-card); color:var(--text-secondary); border-radius:20px; font-size:0.78rem; cursor:pointer; transition:all 0.2s; }
.btn-cancel:hover { border-color:var(--border-light); background:var(--bg-tag); }
.btn-sm-del { width:28px; height:28px; border-radius:50%; border:1px solid var(--border-light); background:var(--bg-card); color:var(--text-muted); cursor:pointer; font-size:1rem; display:flex; align-items:center; justify-content:center; }
.btn-sm-del:hover { border-color:#e74c3c; color:#e74c3c; }
.btn-add-opt { padding:6px 14px; border:1.5px dashed #526e5a; background:transparent; color:#526e5a; border-radius:18px; font-size:0.72rem; cursor:pointer; margin-top:4px; width:fit-content; }
.btn-add-opt:hover { background:rgba(82,110,90,0.04); }

/* Modals */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-panel { background:var(--bg-card); border-radius:16px; padding:24px; width:520px; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.2); border:1px solid var(--border-light); }
.modal-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.modal-header h3 { font-size:0.95rem; font-weight:700; color:var(--text-primary); }
.modal-close { background:none; border:none; color:var(--text-muted); cursor:pointer; padding:4px; border-radius:6px; }
.modal-close:hover { background:var(--bg-tag); color:var(--text-primary); }
.modal-body { display:flex; flex-direction:column; gap:14px; }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; padding-top:16px; border-top:1px solid var(--border-light); }
.grade-textarea { width:100%; padding:10px; border:1px solid var(--border-light); border-radius:10px; font-size:0.78rem; resize:vertical; outline:none; background:var(--bg-input,#fff); color:var(--text-primary); }
.grade-textarea:focus { border-color:#526e5a; }
.file-upload-btn { display:flex; align-items:center; gap:6px; padding:5px 12px; border:1.5px dashed #526e5a; border-radius:16px; font-size:0.68rem; color:#526e5a; cursor:pointer; transition:all 0.2s; }
.file-upload-btn:hover { background:rgba(82,110,90,0.04); }
</style>
