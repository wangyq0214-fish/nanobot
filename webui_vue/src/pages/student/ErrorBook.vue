<template>
<div class="eb-page">
  <header class="page-header">
    <div class="header-left">
      <h2>错题集</h2>
      <span class="header-summary">{{ errors.length }} 道错题 · 来自 {{ courseSet.length }} 门课程</span>
    </div>
    <div class="eb-filters">
      <select v-model="filterCourse">
        <option value="">全部课程</option>
        <option v-for="c in courseSet" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>
  </header>

  <div class="eb-list">
    <div v-for="(e, ei) in filteredErrors" :key="e.id" class="eb-card">
      <div class="eb-card-head" @click="e.expanded = !e.expanded">
        <div class="eb-left">
          <span class="eb-num">{{ ei + 1 }}</span>
          <div>
            <h3>{{ e.stem }}</h3>
            <div class="eb-meta">{{ e.courseName }} · {{ e.type }} · 答错于 {{ e.time }}</div>
          </div>
        </div>
        <div class="eb-right">
          <span class="eb-chips">
            <span v-for="kp in e.knowledgePoints" :key="kp" class="eb-chip">{{ kp }}</span>
          </span>
          <svg class="eb-arrow" :class="{ open: e.expanded }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
      <div v-show="e.expanded" class="eb-card-body">
        <!-- 错误推理链 -->
        <div class="eb-section">
          <div class="eb-sec-title">❌ 你的推理路径</div>
          <div class="eb-reasoning">
            <div v-for="(step, si) in e.errorChain" :key="si" class="eb-step">
              <span class="eb-step-num">{{ si + 1 }}</span>
              <span class="eb-step-text">{{ step }}</span>
            </div>
          </div>
        </div>
        <!-- 正确答案 -->
        <div class="eb-section">
          <div class="eb-sec-title">✅ 正确答案</div>
          <div class="eb-correct">{{ e.correctAnswer }}</div>
        </div>
        <!-- 错误原因 -->
        <div class="eb-section">
          <div class="eb-sec-title">🔍 错误原因</div>
          <p class="eb-reason">{{ e.errorReason }}</p>
        </div>
        <!-- 靶向练习 -->
        <div class="eb-section">
          <button class="eb-practice-btn" @click="doPractice(e)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            靶向强化练习
          </button>
        </div>
      </div>
    </div>
    <div v-if="filteredErrors.length === 0" class="empty">暂无错题</div>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'

const filterCourse = ref('')

const errors = ref([
  { id: 1, stem: '水稻纹枯病的病原菌属于哪一类？', courseName: '作物病理学', type: '单选题', time: '7月28日', knowledgePoints: ['纹枯病', '病原菌分类'], errorChain: ['观察病斑形状 → 判断为真菌性病害', '回忆病原菌分类 → 记得是担子菌'], correctAnswer: '半知菌亚门 · 立枯丝核菌（Rhizoctonia solani）', errorReason: '将立枯丝核菌误归为担子菌亚门，实际上其有性阶段为担子菌，但无性阶段分类为半知菌。需注意真菌不同发育阶段的分类归属差异。', expanded: false },
  { id: 2, stem: '下图所示的昆虫属于哪个目？', courseName: '植保基础', type: '图文题', time: '7月26日', knowledgePoints: ['昆虫分类', '形态识别'], errorChain: ['观察触角类型 → 判断为鳞翅目', '观察口器 → 确认是虹吸式口器', '观察翅脉 → 误判为膜翅目'], correctAnswer: '鳞翅目（Lepidoptera）', errorReason: '翅脉判断环节出错，将鳞翅目特有的鳞片覆盖误认为膜翅目的透明膜质翅。建议对比观察两种翅的显微结构。', expanded: false },
  { id: 3, stem: '简述生物防治相对于化学防治的优势和局限性。', courseName: '植保基础', type: '简答题', time: '7月24日', knowledgePoints: ['生物防治', '化学防治'], errorChain: ['列举了生物防治的3个优势', '局限性只写了1点，遗漏了持效性不稳定'], correctAnswer: '优势：环境友好、可持续、不易产生抗性、对非靶标生物安全。局限性：见效慢、持效性受环境影响大、防治谱较窄、产品质量控制难。', errorReason: '对生物防治局限性的理解不够全面，特别是忽略了环境因素对生物制剂持效性的影响。', expanded: false },
])

const courseSet = computed(() => [...new Set(errors.value.map(e => e.courseName))])
const filteredErrors = computed(() => filterCourse.value ? errors.value.filter(e => e.courseName === filterCourse.value) : errors.value)

function doPractice(e) { alert(`开始针对"${e.knowledgePoints.join('、')}"的靶向练习（演示）`) }
</script>

<style scoped>
.eb-page { flex:1; padding:32px; overflow-y:auto; }
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; flex-shrink:0; }
.header-left h2 { font-size:1.4rem; font-weight:700; color:var(--text-primary); }
.header-summary { font-size:0.76rem; color:var(--text-muted); margin-top:2px; display:block; }
.eb-filters select { padding:8px 14px; border:1px solid var(--border-light); border-radius:20px; font-size:0.76rem; color:var(--text-primary); background:var(--bg-card); outline:none; cursor:pointer; }
.eb-filters select:focus { border-color:#526e5a; }

.eb-list { display:flex; flex-direction:column; gap:10px; }
.eb-card { background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-md); overflow:hidden; }
.eb-card-head { display:flex; align-items:center; justify-content:space-between; padding:16px 20px; cursor:pointer; transition:background 0.15s; }
.eb-card-head:hover { background:var(--bg-card-hover); }
.eb-left { display:flex; align-items:flex-start; gap:14px; flex:1; min-width:0; }
.eb-num { width:26px; height:26px; border-radius:50%; border:1.5px solid #526e5a; color:#526e5a; display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:700; flex-shrink:0; }
.eb-left h3 { font-size:0.88rem; font-weight:600; color:var(--text-primary); }
.eb-meta { font-size:0.68rem; color:var(--text-muted); margin-top:2px; }
.eb-right { display:flex; align-items:center; gap:10px; flex-shrink:0; }
.eb-chips { display:flex; gap:4px; flex-wrap:wrap; }
.eb-chip { font-size:0.62rem; padding:2px 8px; border-radius:8px; border:1px solid var(--border-light); color:var(--text-muted); white-space:nowrap; }
.eb-arrow { transition:transform 0.2s; color:var(--text-muted); flex-shrink:0; }
.eb-arrow.open { transform:rotate(180deg); color:#526e5a; }

.eb-card-body { padding:0 20px 20px; border-top:1px solid var(--divider); display:flex; flex-direction:column; gap:16px; padding-top:16px; }
.eb-section { }
.eb-sec-title { font-size:0.72rem; font-weight:700; color:var(--text-secondary); margin-bottom:8px; }
.eb-reasoning { display:flex; flex-direction:column; gap:6px; }
.eb-step { display:flex; gap:10px; font-size:0.78rem; color:var(--text-primary); align-items:baseline; }
.eb-step-num { width:20px; height:20px; border-radius:50%; background:rgba(231,76,60,0.1); color:#c0392b; display:flex; align-items:center; justify-content:center; font-size:0.62rem; font-weight:700; flex-shrink:0; }
.eb-step-text { line-height:1.5; }
.eb-correct { font-size:0.82rem; color:#526e5a; padding:12px 16px; background:rgba(82,110,90,0.06); border-radius:10px; line-height:1.6; }
.eb-reason { font-size:0.78rem; color:var(--text-secondary); line-height:1.7; }
.eb-practice-btn { display:flex; align-items:center; gap:8px; padding:10px 20px; border:1.5px solid #526e5a; background:transparent; color:#526e5a; border-radius:20px; font-size:0.78rem; font-weight:600; cursor:pointer; transition:all 0.2s; }
.eb-practice-btn:hover { background:#526e5a; color:#fff; }

.empty { text-align:center; padding:64px 0; color:var(--text-muted); font-size:0.82rem; }
</style>
