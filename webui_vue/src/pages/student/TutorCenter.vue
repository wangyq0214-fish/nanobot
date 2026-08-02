<template>
<div class="tc-page">
  <header class="page-header">
    <div class="header-left"><h2>辅导助手</h2></div>
    <div class="tc-modes">
      <span :class="{ on: mode === 'free' }" @click="mode = 'free'">自由提问</span>
      <span :class="{ on: mode === 'scenario' }" @click="mode = 'scenario'">场景练习</span>
    </div>
  </header>

  <!-- 自由提问 · 苏格拉底式引导 -->
  <div v-if="mode === 'free'" class="free-mode">
    <div class="fm-chat">
      <div v-for="(msg, i) in chatMessages" :key="i" class="fm-msg" :class="msg.role">
        <div class="fm-avatar">{{ msg.role === 'ai' ? '🌾' : '我' }}</div>
        <div class="fm-bubble">
          <div class="fm-text" v-html="msg.text"></div>
          <div class="fm-time">{{ msg.time }}</div>
        </div>
        <!-- 上传的图片 -->
        <div v-if="msg.image" class="fm-image">
          <div class="fm-img-placeholder">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
            <span>{{ msg.image }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="fm-input-bar">
      <button class="fm-upload-btn" title="上传图片">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
      </button>
      <input v-model="freeInput" placeholder="描述你的问题或上传病害图片..." @keyup.enter="sendFree" />
      <button class="fm-send" @click="sendFree" :disabled="!freeInput.trim()">发送</button>
    </div>
  </div>

  <!-- 场景练习 · 复杂综合案例 -->
  <div v-else class="scenario-mode">
    <div class="sm-top">
      <div class="sm-case-card" v-if="activeScenario">
        <div class="sm-case-head">
          <span class="sm-badge">当前案例</span>
          <span class="sm-diff">{{ activeScenario.difficulty }}</span>
        </div>
        <h3 class="sm-case-title">{{ activeScenario.title }}</h3>
        <p class="sm-case-desc">{{ activeScenario.description }}</p>
      </div>
      <div class="sm-case-card" v-else>
        <div class="sm-placeholder">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <p>选择一个案例开始练习</p>
        </div>
      </div>
    </div>
    <div class="sm-bottom">
      <div class="sm-scenarios">
        <h3 class="sm-title">可选案例</h3>
        <div class="sm-grid">
          <div v-for="s in scenarios" :key="s.id" class="sm-item" :class="{ active: activeScenario?.id === s.id }" @click="activeScenario = s">
            <h4>{{ s.title }}</h4>
            <div class="sm-item-foot">
              <span>{{ s.courseName }}</span>
              <span>{{ s.difficulty }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- 交互区域 -->
      <div class="sm-chat" v-if="activeScenario">
        <div class="sm-chat-title">向系统提问收集信息</div>
        <div class="sm-messages">
          <div v-for="(q, qi) in activeScenario.questions" :key="qi" class="sm-qa">
            <div class="sm-q">🧑‍🎓 {{ q.ask }}</div>
            <div class="sm-a">🔬 {{ q.answer }}</div>
          </div>
        </div>
        <div class="sm-input-row">
          <input v-model="scenarioInput" placeholder="提问收集信息（如：土壤情况？叶片背面特征？）..." @keyup.enter="askScenario" />
          <button @click="askScenario" :disabled="!scenarioInput.trim()">提问</button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref } from 'vue'

const mode = ref('free')

// 自由提问
const freeInput = ref('')
const chatMessages = ref([
  { role: 'ai', text: '你好！我是你的植保学习助手 🌾<br>遇到任何病虫害诊断问题，可以描述症状或直接上传图片。<br><br>我不会直接告诉你答案——让我们一起通过 <b>观察 → 假设 → 验证 → 结论</b> 的步骤，逐步推导出诊断结果。', time: '刚刚' },
  { role: 'user', text: '我拍了一张水稻叶片的照片，叶子上有褐色的斑点，不知道是什么病。', time: '1分钟前', image: '水稻病叶.jpg' },
  { role: 'ai', text: '好的，让我们一步步来分析。<br><br><b>🔍 第一步：观察</b><br>你注意看一下这些褐色斑点：<br>1. 斑点是什么形状的？圆形还是不规则？<br>2. 斑点边缘有没有黄色晕圈？<br>3. 斑点是从叶尖开始还是叶基部开始？<br><br>请描述你观察到的特征。', time: '刚刚' },
])

function sendFree() {
  if (!freeInput.value.trim()) return
  chatMessages.value.push({ role: 'user', text: freeInput.value, time: '刚刚' })
  freeInput.value = ''
  setTimeout(() => {
    chatMessages.value.push({ role: 'ai', text: '很好的观察！<br><br><b>🤔 第二步：假设</b><br>根据你描述的特征（不规则形状、有黄色晕圈、从叶基部开始），这有几个可能：<br>1. 稻瘟病<br>2. 胡麻斑病<br>3. 纹枯病<br><br>你回忆一下课本上这几种病的区别点是什么？你觉得最可能是哪一种？', time: '刚刚' })
  }, 600)
}

// 场景练习
const activeScenario = ref(null)
const scenarioInput = ref('')
const scenarios = ref([
  { id: 1, title: '某地块水稻异常症状诊断', courseName: '作物病理学', difficulty: '中等', description: '某农户反映自家稻田出现异常：部分植株叶片发黄、矮化，田间呈团块状分布。请通过提问收集信息，给出诊断和处理方案。', questions: [
    { ask: '土壤情况如何？最近有施过什么肥吗？', answer: '土壤偏酸性(pH 5.2)，上个月施过尿素20kg/亩。田间低洼处积水较多。' },
  ]},
  { id: 2, title: '果园柑橘叶片异常脱落', courseName: '植物保护', difficulty: '困难', description: '某柑橘园出现大面积叶片黄化脱落，果实表面有褐色病斑。需判断是病害、虫害还是营养问题。', questions: [] },
  { id: 3, title: '小麦抽穗期穗部发黑', courseName: '作物病理学', difficulty: '中等', description: '小麦正处于抽穗期，部分麦穗出现黑色粉状物质，疑似黑穗病。需确认诊断并提出防治建议。', questions: [] },
])

function askScenario() {
  if (!scenarioInput.value.trim() || !activeScenario.value) return
  const a = activeScenario.value
  a.questions.push({ ask: scenarioInput.value, answer: '根据田间调查记录，该区域近期气温28-32℃，相对湿度85%，连续降雨3天。（演示数据）' })
  scenarioInput.value = ''
}
</script>

<style scoped>
.tc-page { flex:1; padding:32px; overflow-y:auto; display:flex; flex-direction:column; }
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; flex-shrink:0; }
.header-left h2 { font-size:1.4rem; font-weight:700; color:var(--text-primary); }
.tc-modes { display:flex; gap:2px; background:var(--bg-tag); padding:3px; border-radius:20px; }
.tc-modes span { padding:7px 18px; border-radius:18px; font-size:0.78rem; color:var(--text-muted); cursor:pointer; transition:all 0.2s; }
.tc-modes span:hover { color:var(--text-primary); }
.tc-modes span.on { background:var(--bg-card); color:#526e5a; font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,0.05); }

/* 自由提问 */
.free-mode { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.fm-chat { flex:1; overflow-y:auto; padding-right:8px; display:flex; flex-direction:column; gap:16px; }
.fm-msg { display:flex; gap:10px; }
.fm-msg.user { flex-direction:row-reverse; }
.fm-avatar { width:32px; height:32px; border-radius:50%; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; font-size:0.85rem; flex-shrink:0; }
.fm-msg.user .fm-avatar { background:#526e5a; color:#fff; font-size:0.7rem; }
.fm-bubble { max-width:70%; padding:12px 16px; border-radius:14px; background:var(--bg-card); border:1px solid var(--border-light); }
.fm-msg.user .fm-bubble { background:rgba(82,110,90,0.08); border-color:rgba(82,110,90,0.2); }
.fm-text { font-size:0.84rem; color:var(--text-primary); line-height:1.7; }
.fm-time { font-size:0.64rem; color:var(--text-muted); margin-top:4px; }
.fm-image { }
.fm-img-placeholder { padding:12px 16px; background:var(--bg-tag); border:1px dashed var(--border-light); border-radius:10px; display:flex; align-items:center; gap:8px; font-size:0.76rem; color:var(--text-muted); }
.fm-input-bar { display:flex; gap:8px; padding-top:16px; border-top:1px solid var(--divider); margin-top:16px; flex-shrink:0; }
.fm-input-bar input { flex:1; padding:10px 14px; border:1px solid var(--border-light); border-radius:20px; font-size:0.8rem; outline:none; color:var(--text-primary); background:var(--bg-card); }
.fm-input-bar input:focus { border-color:#526e5a; }
.fm-upload-btn { width:40px; height:40px; border-radius:50%; border:1px solid var(--border-light); background:var(--bg-card); color:var(--text-muted); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }
.fm-upload-btn:hover { border-color:#526e5a; color:#526e5a; }
.fm-send { padding:10px 20px; border-radius:20px; background:#526e5a; color:#fff; border:none; font-weight:600; cursor:pointer; font-size:0.78rem; }
.fm-send:disabled { opacity:0.4; cursor:default; }

/* 场景练习 */
.scenario-mode { flex:1; display:flex; flex-direction:column; gap:20px; overflow:hidden; }
.sm-case-card { padding:20px 24px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-md); }
.sm-case-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.sm-badge { font-size:0.66rem; font-weight:700; color:#526e5a; border:1px solid #526e5a; padding:2px 8px; border-radius:6px; }
.sm-diff { font-size:0.68rem; color:var(--text-muted); }
.sm-case-title { font-size:1rem; font-weight:700; color:var(--text-primary); }
.sm-case-desc { font-size:0.8rem; color:var(--text-secondary); line-height:1.6; margin-top:6px; }
.sm-placeholder { text-align:center; padding:32px; color:var(--text-muted); }
.sm-placeholder p { margin-top:10px; font-size:0.82rem; }
.sm-bottom { flex:1; display:flex; gap:20px; overflow:hidden; }
.sm-scenarios { width:280px; flex-shrink:0; }
.sm-title { font-size:0.78rem; font-weight:700; color:var(--text-primary); margin-bottom:12px; }
.sm-grid { display:flex; flex-direction:column; gap:8px; }
.sm-item { padding:14px 16px; border:1px solid var(--border-light); border-radius:var(--radius-md); cursor:pointer; transition:all 0.2s; }
.sm-item:hover { border-color:#526e5a; }
.sm-item.active { border-color:#526e5a; background:rgba(82,110,90,0.04); }
.sm-item h4 { font-size:0.8rem; font-weight:600; color:var(--text-primary); }
.sm-item-foot { display:flex; justify-content:space-between; font-size:0.66rem; color:var(--text-muted); margin-top:4px; }
.sm-chat { flex:1; display:flex; flex-direction:column; border:1px solid var(--border-light); border-radius:var(--radius-md); overflow:hidden; }
.sm-chat-title { padding:12px 16px; background:var(--bg-tag); font-size:0.72rem; font-weight:600; color:var(--text-secondary); border-bottom:1px solid var(--border-light); }
.sm-messages { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px; }
.sm-qa { }
.sm-q { font-size:0.78rem; color:#526e5a; font-weight:600; margin-bottom:4px; }
.sm-a { font-size:0.78rem; color:var(--text-secondary); padding:8px 12px; background:var(--bg-tag); border-radius:8px; line-height:1.5; }
.sm-input-row { display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--border-light); }
.sm-input-row input { flex:1; padding:9px 14px; border:1px solid var(--border-light); border-radius:16px; font-size:0.78rem; outline:none; color:var(--text-primary); }
.sm-input-row input:focus { border-color:#526e5a; }
.sm-input-row button { padding:9px 18px; background:#526e5a; color:#fff; border:none; border-radius:16px; font-weight:600; cursor:pointer; font-size:0.76rem; }
.sm-input-row button:disabled { opacity:0.4; cursor:default; }
</style>
