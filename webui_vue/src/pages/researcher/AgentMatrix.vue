<template>
<div class="agent-matrix-page">
  <!-- 页面标题 -->
  <div class="page-header">
    <h1 class="page-title">学术智能体矩阵</h1>
    <p class="page-subtitle">基于当前 Nanobot 多智能体配置，展示研究员可用的真实智能体并支持即时切换。</p>
  </div>

  <!-- 搜索和筛选 -->
  <div class="filter-section">
    <div class="search-box">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
      <input
        type="text"
        v-model="searchText"
        placeholder="搜索智能体名称、职责、研究领域或能力标签..."
      />
    </div>

    <div class="layer-tabs">
      <button
        v-for="tab in layerTabs"
        :key="tab.key"
        class="layer-tab"
        :class="{ active: currentLayer === tab.key }"
        @click="currentLayer = tab.key"
      >
        {{ tab.label }}
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <button class="agent-create-btn" @click="openCreateDialog">
      新增智能体
    </button>
  </div>

  <div v-if="loading || error" class="matrix-state" :class="{ error: !!error }">
    {{ error || '正在加载智能体...' }}
  </div>

  <!-- 智能体卡片网格 -->
  <div class="agents-grid">
    <div
      v-for="agent in filteredAgents"
      :key="agent.id"
      class="agent-card"
      :class="[agent.layerClass, { active: agent.active, switching: switchingAgent === agent.name }]"
      @click="switchAgent(agent)"
    >
      <!-- 等级角标 -->
      <span class="agent-level" :class="agent.levelClass">{{ agent.level }}</span>
      <button class="agent-edit-btn" @click.stop="openEditDialog(agent)">编辑</button>

      <!-- 头像 -->
      <div class="agent-avatar" :style="{ background: agent.avatarBg }">
        <span class="avatar-text">{{ agent.initials }}</span>
      </div>

      <!-- 信息 -->
      <h3 class="agent-name">{{ agent.displayName }}</h3>
      <p class="agent-role">{{ agent.role }}</p>
      <p class="agent-desc">{{ agent.description }}</p>

      <!-- 状态指示 -->
      <div class="agent-status">
        <span class="status-dot" :class="{ online: agent.active }"></span>
        <span class="status-text">{{ switchingAgent === agent.name ? '切换中' : (agent.active ? '当前智能体' : '可切换') }}</span>
      </div>
    </div>
  </div>

  <div v-if="editorOpen" class="agent-modal-backdrop" @click.self="closeEditor">
    <div class="agent-modal">
      <div class="agent-modal-header">
        <h2>{{ editingExisting ? '修改智能体' : '新增智能体' }}</h2>
        <button class="agent-modal-close" @click="closeEditor">×</button>
      </div>
      <label class="agent-field">
        <span>标识</span>
        <input v-model="agentForm.name" :disabled="editingExisting" placeholder="researcher_custom_agent" />
      </label>
      <label class="agent-field">
        <span>名称</span>
        <input v-model="agentForm.displayName" placeholder="自定义科研智能体" />
      </label>
      <label class="agent-field">
        <span>职责</span>
        <input v-model="agentForm.role" placeholder="论文审稿 / 方法复核 / 数据分析" />
      </label>
      <label class="agent-field">
        <span>描述</span>
        <textarea v-model="agentForm.description" rows="3" placeholder="说明这个智能体适合处理什么任务"></textarea>
      </label>
      <label class="agent-field">
        <span>系统提示词</span>
        <textarea v-model="agentForm.systemPromptOverride" rows="8" placeholder="写入该智能体的 system prompt"></textarea>
      </label>
      <div class="agent-modal-actions">
        <button class="agent-cancel-btn" @click="closeEditor">取消</button>
        <button class="agent-save-btn" @click="saveAgent" :disabled="savingAgent">
          {{ savingAgent ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthFetch } from '../../composables/useAuthFetch.js'

const { authGet, authMutate } = useAuthFetch()

const searchText = ref('')
const currentLayer = ref('all')
const agents = ref([])
const currentAgentName = ref('')
const loading = ref(false)
const error = ref('')
const switchingAgent = ref('')
const editorOpen = ref(false)
const editingExisting = ref(false)
const savingAgent = ref(false)
const agentForm = ref({
  name: '',
  displayName: '',
  role: '',
  description: '',
  systemPromptOverride: '',
  temperature: '',
})

const layerTabs = computed(() => {
  const counts = agents.value.reduce((acc, agent) => {
    acc[agent.layer] = (acc[agent.layer] || 0) + 1
    return acc
  }, {})

  return [
    { key: 'all', label: '全部', count: agents.value.length },
    { key: 'L3', label: '当前', count: counts.L3 || 0 },
    { key: 'L2', label: '可用', count: counts.L2 || 0 },
    { key: 'L1', label: '系统', count: counts.L1 || 0 },
  ]
})

const filteredAgents = computed(() => {
  let result = agents.value

  if (currentLayer.value !== 'all') {
    result = result.filter(a => a.layer === currentLayer.value)
  }

  const q = searchText.value.trim().toLowerCase()
  if (q) {
    result = result.filter(a =>
      a.name.toLowerCase().includes(q) ||
      a.displayName.toLowerCase().includes(q) ||
      a.role.toLowerCase().includes(q) ||
      a.description.toLowerCase().includes(q)
    )
  }

  return result
})

function initialsOf(name) {
  const source = String(name || '').trim()
  if (!source) return 'AI'
  const ascii = source
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
  if (ascii) return ascii
  return source.slice(0, 2)
}

function decorateAgent(raw, index) {
  const name = raw.name || `agent_${index}`
  const displayName = raw.display_name || raw.displayName || name
  const active = name === currentAgentName.value
  const layer = active ? 'L3' : 'L2'

  return {
    id: name,
    name,
    displayName,
    role: raw.role || '智能体',
    description: raw.description || '暂无描述',
    level: active ? 'ACTIVE' : 'AGENT',
    layer,
    levelClass: active ? 'level-l3' : 'level-l2',
    layerClass: active ? '' : 'opacity-card',
    avatarBg: active
      ? 'linear-gradient(135deg, #f59e0b, #d97706)'
      : 'linear-gradient(135deg, #526e5a, #3d5040)',
    initials: initialsOf(displayName || name),
    online: active,
    active,
    temperature: raw.temperature,
    systemPromptOverride: raw.system_prompt_override || raw.systemPromptOverride || '',
  }
}

function applyAgents(rawAgents) {
  agents.value = (rawAgents || []).map(decorateAgent)
}

async function loadAgents() {
  loading.value = true
  error.value = ''
  try {
    const current = await authGet('/api/agents/current')
    currentAgentName.value = current?.agent?.name || ''

    const body = await authGet('/api/agents')
    if (body?.has_multi_agent === false) {
      error.value = '多智能体系统未配置'
      agents.value = []
      return
    }
    applyAgents(body?.agents || [])
  } catch (err) {
    error.value = err?.message || '智能体加载失败'
    agents.value = []
  } finally {
    loading.value = false
  }
}

async function switchAgent(agent) {
  if (!agent || agent.active || switchingAgent.value) return
  switchingAgent.value = agent.name
  error.value = ''
  try {
    const body = await authGet(`/api/agents/${encodeURIComponent(agent.name)}/switch`)
    if (!body?.success) throw new Error(body?.error || '切换失败')
    currentAgentName.value = agent.name
    applyAgents(agents.value.map(a => ({
      name: a.name,
      display_name: a.displayName,
      role: a.role,
      description: a.description,
      temperature: a.temperature,
    })))
  } catch (err) {
    error.value = err?.message || '切换失败'
  } finally {
    switchingAgent.value = ''
  }
}

function openCreateDialog() {
  editingExisting.value = false
  agentForm.value = {
    name: '',
    displayName: '',
    role: '',
    description: '',
    systemPromptOverride: '',
    temperature: '',
  }
  editorOpen.value = true
}

function openEditDialog(agent) {
  editingExisting.value = true
  agentForm.value = {
    name: agent.name,
    displayName: agent.displayName,
    role: agent.role,
    description: agent.description,
    systemPromptOverride: agent.systemPromptOverride || '',
    temperature: agent.temperature ?? '',
  }
  editorOpen.value = true
}

function closeEditor() {
  if (savingAgent.value) return
  editorOpen.value = false
}

async function saveAgent() {
  if (savingAgent.value) return
  error.value = ''
  const payload = {
    name: agentForm.value.name.trim(),
    displayName: agentForm.value.displayName.trim(),
    role: agentForm.value.role.trim(),
    description: agentForm.value.description.trim(),
    systemPromptOverride: agentForm.value.systemPromptOverride.trim(),
    temperature: agentForm.value.temperature,
  }
  if (!payload.name || !payload.displayName || !payload.systemPromptOverride) {
    error.value = '请填写标识、名称和系统提示词'
    return
  }

  savingAgent.value = true
  try {
    const body = await authMutate('/api/agents/upsert', payload)
    if (!body?.success) throw new Error(body?.error || '保存失败')
    const savedName = body.agent?.name || payload.name
    editorOpen.value = false
    await loadAgents()
    const saved = agents.value.find(a => a.name === savedName)
    if (saved) await switchAgent(saved)
  } catch (err) {
    error.value = err?.message || '保存失败'
  } finally {
    savingAgent.value = false
  }
}

onMounted(loadAgents)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap');

.agent-matrix-page {
  padding: 32px 40px;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-family: 'Noto Serif SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 400;
  color: #121212;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 12px;
  color: #666666;
  margin: 0;
  letter-spacing: 0.5px;
}

/* 搜索和筛选 */
.filter-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
}

.search-box {
  flex: 1;
  max-width: 400px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  border: 1px solid #dee3de;
  border-radius: 12px;
  padding: 10px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01);
  transition: all 0.2s ease;
}

.search-box:focus-within {
  border-color: #121212;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.search-box svg {
  color: #999999;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: #121212;
  background: transparent;
  font-family: inherit;
  letter-spacing: 0.5px;
}

.search-box input::placeholder {
  color: #999999;
}

.layer-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f0f0f0;
  padding: 4px;
  border-radius: 12px;
}

.layer-tab {
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 12px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.layer-tab:hover {
  background: rgba(255, 255, 255, 0.5);
}

.layer-tab.active {
  background: white;
  color: #121212;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.tab-count {
  font-size: 10px;
  opacity: 0.6;
}

.agent-create-btn {
  border: none;
  border-radius: 10px;
  background: #121212;
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 9px 14px;
  cursor: pointer;
  white-space: nowrap;
}

.agent-create-btn:hover {
  background: #333333;
}

/* 智能体卡片网格 */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.matrix-state {
  margin-bottom: 16px;
  padding: 10px 14px;
  border: 1px solid #dbe5dc;
  border-radius: 10px;
  background: #f7faf7;
  color: #121212;
  font-size: 12px;
}

.matrix-state.error {
  border-color: #fecaca;
  background: #fff7f7;
  color: #b91c1c;
}

.agent-card {
  background: white;
  border: 1px solid #e8ebe8;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  transition: all 0.2s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.01);
  cursor: pointer;
}

.agent-card:hover {
  border-color: #121212;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.agent-card.active {
  border-color: #f59e0b;
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.12);
}

.agent-card.switching {
  pointer-events: none;
  opacity: 0.7;
}

.agent-edit-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 7px;
  background: #fff;
  color: #121212;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
}

.agent-card:hover .agent-edit-btn {
  opacity: 1;
}

.agent-edit-btn:hover {
  border-color: #121212;
  background: #f5faf5;
}

.agent-card.opacity-card {
  opacity: 0.85;
}

.agent-card.opacity-card:hover {
  opacity: 1;
}

/* 绛夌骇瑙掓爣 */
.agent-level {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid;
}

.level-l3 {
  color: #d97706;
  background: #fffbeb;
  border-color: #fde68a;
}

.level-l2 {
  color: #121212;
  background: #ecfdf5;
  border-color: #e0e0e0;
}

.level-l1 {
  color: #6b7280;
  background: #f3f4f6;
  border-color: #e5e7eb;
}

/* 澶村儚 */
.agent-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid #edf0ed;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  margin-top: 8px;
}

.avatar-text {
  font-size: 18px;
  font-weight: 700;
  color: white;
}

/* 淇℃伅 */
.agent-name {
  font-size: 13px;
  font-weight: 700;
  color: #121212;
  margin: 0 0 4px;
  transition: color 0.2s ease;
}

.agent-card:hover .agent-name {
  color: #121212;
}

.agent-role {
  font-size: 11px;
  color: #121212;
  font-weight: 500;
  margin: 0 0 10px;
}

.agent-desc {
  font-size: 11px;
  color: #666666;
  line-height: 1.6;
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 状态指示 */
.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #f0f3f0;
  width: 100%;
  justify-content: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d1d5db;
}

.status-dot.online {
  background: #34d399;
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.2);
}

.status-text {
  font-size: 10px;
  color: #999;
}

.agent-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.agent-modal {
  width: min(680px, 100%);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e3e8e3;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
  padding: 20px;
}

.agent-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.agent-modal-header h2 {
  margin: 0;
  font-size: 18px;
  color: #121212;
}

.agent-modal-close {
  border: none;
  background: transparent;
  color: #666666;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.agent-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.agent-field span {
  font-size: 12px;
  font-weight: 600;
  color: #333333;
}

.agent-field input,
.agent-field textarea {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 10px 12px;
  font: inherit;
  font-size: 13px;
  color: #121212;
  outline: none;
  resize: vertical;
}

.agent-field input:focus,
.agent-field textarea:focus {
  border-color: #121212;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08);
}

.agent-field input:disabled {
  background: #f3f5f3;
  color: #666666;
}

.agent-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.agent-cancel-btn,
.agent-save-btn {
  border: none;
  border-radius: 10px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.agent-cancel-btn {
  background: #f0f0f0;
  color: #666666;
}

.agent-save-btn {
  background: #121212;
  color: #fff;
}

.agent-save-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* 鍝嶅簲寮?*/
@media (max-width: 1200px) {
  .agents-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .agent-matrix-page {
    padding: 20px 16px;
  }

  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: 100%;
  }

  .layer-tabs {
    overflow-x: auto;
  }

  .agents-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .agents-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== Green Theme ===== */
body.green .agent-matrix-page {
  background: #f7f8f7;
}

body.green .page-title {
  color: #1e2720;
}

body.green .page-subtitle {
  color: #717c72;
}

body.green .search-box {
  background: white;
  border-color: #dee3de;
}

body.green .search-box:focus-within {
  border-color: #bad2be;
  box-shadow: 0 4px 12px rgba(82, 110, 90, 0.04);
}

body.green .search-box svg {
  color: #9da79e;
}

body.green .search-box input {
  color: #1e2720;
}

body.green .search-box input::placeholder {
  color: #9da79e;
}

body.green .layer-tabs {
  background: #edf0ed;
}

body.green .layer-tab {
  color: #556056;
}

body.green .layer-tab:hover {
  background: rgba(255, 255, 255, 0.5);
}

body.green .layer-tab.active {
  background: white;
  color: #1e2720;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

body.green .agent-create-btn {
  background: #526e5a;
}

body.green .agent-create-btn:hover {
  background: #415848;
}

body.green .matrix-state {
  background: #eef3ee;
  border-color: #d6ded6;
  color: #1e2720;
}

body.green .matrix-state.error {
  border-color: #fecaca;
  background: #fff7f7;
  color: #b91c1c;
}

body.green .agent-card {
  background: white;
  border-color: #e8ebe8;
  box-shadow: 0 2px 12px rgba(30, 39, 32, 0.01);
}

body.green .agent-card:hover {
  border-color: #bad2be;
  box-shadow: 0 8px 24px rgba(82, 110, 90, 0.06);
}

body.green .agent-card.active {
  border-color: #526e5a;
  box-shadow: 0 8px 24px rgba(82, 110, 90, 0.12);
}

body.green .agent-edit-btn {
  border-color: #e2e7e2;
  background: #fff;
  color: #1e2720;
}

body.green .agent-edit-btn:hover {
  border-color: #526e5a;
  background: #f5faf5;
}

body.green .level-l3 {
  color: #526e5a;
  background: #eef3ee;
  border-color: #bad2be;
}

body.green .level-l2 {
  color: #1e2720;
  background: #eef3ee;
  border-color: #d6ded6;
}

body.green .agent-avatar {
  border-color: #d6ded6;
}

body.green .agent-name {
  color: #1e2720;
}

body.green .agent-card:hover .agent-name {
  color: #526e5a;
}

body.green .agent-role {
  color: #1e2720;
}

body.green .agent-desc {
  color: #556056;
}

body.green .agent-status {
  border-top-color: #edf0ed;
}

body.green .status-dot {
  background: #cbd2cb;
}

body.green .status-dot.online {
  background: #34d399;
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.2);
}

body.green .status-text {
  color: #717c72;
}

body.green .agent-modal-backdrop {
  background: rgba(0, 0, 0, 0.32);
}

body.green .agent-modal {
  background: #fff;
  border-color: #d6ded6;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
}

body.green .agent-modal-header h2 {
  color: #1e2720;
}

body.green .agent-modal-close {
  color: #556056;
}

body.green .agent-field span {
  color: #2c332e;
}

body.green .agent-field input,
body.green .agent-field textarea {
  border-color: #d6ded6;
  color: #1e2720;
}

body.green .agent-field input:focus,
body.green .agent-field textarea:focus {
  border-color: #526e5a;
  box-shadow: 0 0 0 3px rgba(82, 110, 90, 0.08);
}

body.green .agent-field input:disabled {
  background: #f3f5f3;
  color: #717c72;
}

body.green .agent-cancel-btn {
  background: #edf0ed;
  color: #556056;
}

body.green .agent-save-btn {
  background: #526e5a;
  color: #fff;
}

/* ===== Dark Theme ===== */
body.dark .agent-matrix-page {
  background: #121212;
}

body.dark .page-title {
  color: #ffffff;
}

body.dark .page-subtitle {
  color: #999999;
}

body.dark .search-box {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

body.dark .search-box:focus-within {
  border-color: #444444;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

body.dark .search-box svg {
  color: #666666;
}

body.dark .search-box input {
  color: #e5e5e5;
}

body.dark .search-box input::placeholder {
  color: #666666;
}

body.dark .layer-tabs {
  background: #1a1a1a;
}

body.dark .layer-tab {
  color: #999999;
}

body.dark .layer-tab:hover {
  background: rgba(255,255,255,0.05);
}

body.dark .layer-tab.active {
  background: #242424;
  color: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

body.dark .agent-create-btn {
  background: #ffffff;
  color: #121212;
}

body.dark .agent-create-btn:hover {
  background: #e5e5e5;
}

body.dark .matrix-state {
  background: #1a2420;
  border-color: #2d3d30;
  color: #b3b3b3;
}

body.dark .matrix-state.error {
  background: #2a1515;
  border-color: #5c2020;
  color: #ef4444;
}

body.dark .agent-card {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

body.dark .agent-card:hover {
  border-color: #444444;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

body.dark .agent-card.active {
  border-color: #f59e0b;
  box-shadow: 0 8px 24px rgba(245,158,11,0.2);
}

body.dark .agent-edit-btn {
  background: #1a1a1a;
  border-color: #333333;
  color: #b3b3b3;
}

body.dark .agent-card:hover .agent-edit-btn {
  opacity: 1;
}

body.dark .agent-edit-btn:hover {
  background: #2d2d2d;
  border-color: #444444;
}

body.dark .level-l3 {
  color: #f59e0b;
  background: #2a2515;
  border-color: #3d3520;
}

body.dark .level-l2 {
  color: #b3b3b3;
  background: #1a2420;
  border-color: #2d3d30;
}

body.dark .level-l1 {
  color: #999999;
  background: #1a1a1a;
  border-color: #333333;
}

body.dark .agent-avatar {
  border-color: #333333;
}

body.dark .agent-name {
  color: #ffffff;
}

body.dark .agent-card:hover .agent-name {
  color: #b3b3b3;
}

body.dark .agent-role {
  color: #b3b3b3;
}

body.dark .agent-desc {
  color: #999999;
}

body.dark .agent-status {
  border-top-color: #2d2d2d;
}

body.dark .status-dot {
  background: #333333;
}

body.dark .status-dot.online {
  background: #34d399;
  box-shadow: 0 0 0 2px rgba(52,211,153,0.3);
}

body.dark .status-text {
  color: #666666;
}

body.dark .agent-modal-backdrop {
  background: rgba(0,0,0,0.6);
}

body.dark .agent-modal {
  background: #242424;
  border-color: #2d2d2d;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

body.dark .agent-modal-header h2 {
  color: #ffffff;
}

body.dark .agent-modal-close {
  color: #999999;
}

body.dark .agent-field span {
  color: #e5e5e5;
}

body.dark .agent-field input,
body.dark .agent-field textarea {
  background: #1a1a1a;
  border-color: #333333;
  color: #e5e5e5;
}

body.dark .agent-field input:focus,
body.dark .agent-field textarea:focus {
  background: #242424;
  border-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(255,255,255,0.1);
}

body.dark .agent-field input:disabled {
  background: #1a1a1a;
  color: #666666;
}

body.dark .agent-cancel-btn {
  background: #1a1a1a;
  color: #b3b3b3;
}

body.dark .agent-save-btn {
  background: #ffffff;
  color: #121212;
}
</style>
