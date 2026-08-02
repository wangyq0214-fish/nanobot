<template>
<div class="analytics-page">
  <section class="kpi-bar">
    <div class="kpi-item"><div class="kpi-num">{{ overview.avgScore }}</div><div class="kpi-label">全级平均分</div></div>
    <div class="kpi-item"><div class="kpi-num">{{ overview.passRate }}<small>%</small></div><div class="kpi-label">及格率</div></div>
    <div class="kpi-item"><div class="kpi-num">{{ overview.excellentRate }}<small>%</small></div><div class="kpi-label">优秀率 ≥90</div></div>
    <div class="kpi-item"><div class="kpi-num">{{ overview.weakPointCount }}</div><div class="kpi-label">薄弱知识点</div></div>
    <div class="kpi-item warn"><div class="kpi-num">{{ overview.riskCount }}</div><div class="kpi-label">挂科风险学生</div></div>
    <div class="kpi-item"><div class="kpi-num">{{ overview.totalStudents }}</div><div class="kpi-label">学籍总人数</div></div>
  </section>

  <div class="grid-main">
    <!-- LEFT -->
    <div class="col-left">
      <div class="panel">
        <div class="panel-hd"><span class="panel-title">薄弱知识点频次</span></div>
        <div class="panel-body">
          <div class="weak-list">
            <div v-for="(wp, i) in weakPoints" :key="i" class="weak-row">
              <span class="weak-idx">{{ i + 1 }}</span><span class="weak-name">{{ wp.name }}</span>
              <div class="weak-bar-wrap"><div class="weak-bar" :style="{ width: wp.pct + '%' }"></div></div>
              <span class="weak-count">{{ wp.count }}次</span>
            </div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-hd"><span class="panel-title">学生个体预警</span></div>
        <div class="panel-body">
          <div class="student-alert-list">
            <div v-for="s in riskStudents" :key="s.name" class="sa-row">
              <span class="sa-avatar">{{ s.name[0] }}</span><div class="sa-info"><div class="sa-name">{{ s.name }}</div><div class="sa-desc">{{ s.course }} · {{ s.reason }}</div></div>
              <span class="sa-score" :class="{ danger: s.score < 50 }">{{ s.score }}分</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CENTER -->
    <div class="col-center">
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">班级学情态势</span>
          <div class="legend"><span><i class="dot normal"></i>常态</span><span><i class="dot warn-dot"></i>关注</span></div>
        </div>
        <div class="panel-body">
          <div class="class-grid">
            <div v-for="cls in classStats" :key="cls.name" class="class-card" :class="{ alert: cls.avgScore < 60 }">
              <div class="class-head"><span class="class-name">{{ cls.name }}</span><span class="class-score">{{ cls.avgScore }}</span></div>
              <div class="class-tags"><span>{{ cls.studentCount }}人</span><span>{{ cls.submissionCount }}份提交</span></div>
              <div class="class-foot"><span>及格率 {{ cls.passRate }}%</span><span class="class-action">{{ cls.avgScore >= 80 ? '稳中求进' : cls.avgScore >= 60 ? '专题突破' : '限时训练' }}</span></div>
            </div>
          </div>
        </div>
      </div>
      <div class="two-col">
        <div class="panel">
          <div class="panel-hd"><span class="panel-title">常见错误聚类</span></div>
          <div class="panel-body">
            <div class="cluster-list">
              <div v-for="c in errorClusters" :key="c.name" class="cluster-item">
                <span class="cl-label">{{ c.name }}</span><span class="cl-pct">{{ c.pct }}%</span><span class="cl-desc">{{ c.desc }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-hd"><span class="panel-title">教学难点分布</span></div>
          <div class="panel-body">
            <div class="diff-list">
              <div v-for="d in difficultyMap" :key="d.name" class="diff-item">
                <span class="diff-name">{{ d.name }}</span><div class="diff-bar-wrap"><div class="diff-bar" :style="{ width: d.pct + '%' }"></div></div><span class="diff-pct">{{ d.pct }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="col-right">
      <div class="panel">
        <div class="panel-hd"><span class="panel-title">各章节全班平均分</span></div>
        <div class="panel-body">
          <div class="trend-chart">
            <svg viewBox="0 0 200 80" class="trend-svg">
              <line v-for="y in [20,40,60]" :key="'g'+y" x1="0" :y1="y" x2="200" :y2="y" stroke="#f0f0f0" stroke-width="0.5"/>
              <path :d="areaPath" fill="rgba(82,110,90,0.1)"/>
              <path :d="trendPath" fill="none" stroke="#526e5a" stroke-width="2" stroke-linecap="round"/>
              <circle v-for="(p, i) in trendPoints" :key="'c'+i" :cx="p.x" :cy="p.y" r="2.5" fill="#fff" stroke="#526e5a" stroke-width="1.5"/>
              <text v-for="(p, i) in trendPoints" :key="'t'+i" :x="p.x" :y="p.y-5" text-anchor="middle" fill="#526e5a" font-size="6" font-weight="700">{{ trendData[i].score }}</text>
            </svg>
            <div class="trend-labels"><span v-for="d in trendData" :key="d.chapter" class="tlabel">{{ d.chapter }}</span></div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-hd"><span class="panel-title">分组教学建议</span></div>
        <div class="panel-body">
          <div class="group-section">
            <div class="group-label">同质分组</div>
            <div v-for="g in homoGroups" :key="g.label" class="group-card"><span class="group-tag">{{ g.label }}</span><span class="group-desc">{{ g.desc }}</span></div>
          </div>
          <div class="group-section">
            <div class="group-label">异质分组</div>
            <div v-for="g in heteroGroups" :key="g.label" class="group-card"><span class="group-tag">{{ g.label }}</span><span class="group-desc">{{ g.desc }}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="strategy-bar" :class="{ closed: !sbOpen }">
    <div v-if="sbOpen" class="sb-items">
      <div v-for="(s, i) in strategyList" :key="i" class="sb-item">
        <span class="sb-num">{{ i + 1 }}</span>
        <div class="sb-text">
          <span class="sb-cls">{{ s.cls }}</span>
          <span class="sb-desc">{{ s.desc }}</span>
        </div>
      </div>
    </div>
    <span v-if="!sbOpen" class="sb-hint">教学策略建议</span>
    <svg class="sb-arrow" :class="{ open: sbOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" @click="sbOpen = !sbOpen"><path d="m6 9 6 6 6-6"/></svg>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'

const sbOpen = ref(true)
const overview = ref({ avgScore: 72, passRate: 78, excellentRate: 21, weakPointCount: 8, riskCount: 5, totalStudents: 128 })

const weakPoints = ref([
  { name: '真菌病害诊断与鉴别', count: 47, pct: 94 },
  { name: '农药配比计算', count: 38, pct: 76 },
  { name: '昆虫口器类型识别', count: 32, pct: 64 },
  { name: '病害循环与侵染过程', count: 28, pct: 56 },
  { name: '生物防治原理', count: 24, pct: 48 },
  { name: '田间调查方法', count: 18, pct: 36 },
])

const riskStudents = ref([
  { name: '张三', course: '作物病理学', score: 42, reason: '连续3次作业不及格' },
  { name: '李四', course: '植保基础', score: 48, reason: '最近作业未提交' },
  { name: '王五', course: '作物病理学', score: 38, reason: '知识点掌握断层' },
  { name: '赵六', course: '植保基础', score: 55, reason: '配比计算薄弱' },
])

const classStats = ref([
  { name: '24植保1班', avgScore: 78, studentCount: 32, submissionCount: 28, passRate: 88 },
  { name: '24植保2班', avgScore: 65, studentCount: 30, submissionCount: 25, passRate: 63 },
  { name: '24农学1班', avgScore: 82, studentCount: 35, submissionCount: 33, passRate: 94 },
  { name: '24农学2班', avgScore: 55, studentCount: 31, submissionCount: 22, passRate: 48 },
])

const errorClusters = ref([
  { name: '病原菌分类混淆', pct: 38, desc: '担子菌/半知菌/子囊菌' },
  { name: '农药稀释倍数算错', pct: 25, desc: 'ppm与百分比换算' },
  { name: '口器与害虫对应错', pct: 20, desc: '咀嚼式/刺吸式混淆' },
  { name: '病害循环环节遗漏', pct: 17, desc: '越冬/传播链缺失' },
])

const difficultyMap = ref([
  { name: '真菌分类', pct: 85 }, { name: '农药计算', pct: 72 },
  { name: '昆虫识别', pct: 58 }, { name: '病害循环', pct: 45 }, { name: '生物防治', pct: 35 },
])

const homoGroups = ref([
  { label: 'A组·拔高', desc: '平均分85+ → 研究型课题' },
  { label: 'B组·巩固', desc: '平均分60-85 → 专题训练' },
  { label: 'C组·补弱', desc: '平均分<60 → 基础回顾' },
])
const heteroGroups = ref([
  { label: '混合A', desc: '2强+3中+1弱 → 以强带弱' },
  { label: '混合B', desc: '1强+4中+1弱 → 课堂协作' },
])

const trendData = ref([
  { chapter: '真菌基础', score: 65 }, { chapter: '水稻病害', score: 58 },
  { chapter: '小麦病害', score: 72 }, { chapter: '昆虫分类', score: 80 },
  { chapter: '农药配比', score: 55 }, { chapter: '生物防治', score: 78 }, { chapter: '综合诊断', score: 70 },
])

const trendPoints = computed(() => {
  const w = 200, h = 80, pl = 8, pr = 8, pt = 14, pb = 14
  const xs = (w - pl - pr) / (trendData.value.length - 1)
  return trendData.value.map((d, i) => ({ x: pl + i * xs, y: pt + (h - pt - pb) * (1 - d.score / 100) }))
})
const trendPath = computed(() => {
  const pts = trendPoints.value; let d = `M${pts[0].x},${pts[0].y}`
  for (let i = 1; i < pts.length; i++) { const cx = (pts[i-1].x + pts[i].x) / 2; d += ` C${cx},${pts[i-1].y} ${cx},${pts[i].y} ${pts[i].x},${pts[i].y}` }
  return d
})
const areaPath = computed(() => trendPath.value + ` L${trendPoints.value.at(-1).x},66 L${trendPoints.value[0].x},66 Z`)

const strategyList = computed(() => [
  { cls: '24农学2班', desc: '及格率48% → 基础回顾 + 限时训练 + 一对一辅导' },
  { cls: '24植保2班', desc: '及格率63% → 真菌病害专题 + 配比强化' },
  { cls: '整体', desc: '增加图文病例题 → 对接CropGPT视觉诊断场景' },
])
</script>

<style scoped>
.analytics-page { flex:1; display:flex; flex-direction:column; gap:10px; padding:14px 16px; overflow:hidden; border:1px solid var(--border-light); border-radius:16px; background:var(--bg-page,#fafbfa); margin:8px; }
.kpi-bar { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; flex-shrink:0; }
.kpi-item { background:var(--bg-card); border:1.5px solid #526e5a; border-radius:14px; padding:16px 10px; text-align:center; }
.kpi-item.warn { }
.kpi-num { font-size:1.6rem; font-weight:700; color:var(--text-primary); line-height:1.2; letter-spacing:-0.02em; }
.kpi-item.warn .kpi-num { color:#c0392b; }
.kpi-num small { font-size:0.64rem; font-weight:500; color:var(--text-muted); }
.kpi-label { font-size:0.62rem; color:var(--text-muted); margin-top:4px; font-weight:500; }

.grid-main { flex:1; display:grid; grid-template-columns:255px 1fr 275px; gap:8px; min-height:0; overflow:hidden; }
.col-left,.col-right { display:flex; flex-direction:column; gap:8px; overflow-y:auto; }
.col-center { display:flex; flex-direction:column; gap:8px; overflow-y:auto; }
.col-left::-webkit-scrollbar,.col-right::-webkit-scrollbar,.col-center::-webkit-scrollbar { width:3px; }
.col-left::-webkit-scrollbar-thumb,.col-right::-webkit-scrollbar-thumb,.col-center::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

.panel { background:var(--bg-card); border:1.5px solid #526e5a; border-radius:14px; display:flex; flex-direction:column; overflow:hidden; }
.panel-hd { display:flex; align-items:center; justify-content:space-between; padding:11px 16px; border-bottom:1px solid var(--divider,#f0f0f0); flex-shrink:0; }
.panel-title { font-size:0.72rem; font-weight:700; color:var(--text-primary); letter-spacing:0.01em; }
.panel-body { flex:1; padding:10px 16px; overflow-y:auto; }
.legend { display:flex; gap:10px; font-size:0.6rem; color:var(--text-muted); }
.legend span { display:flex; align-items:center; gap:4px; }
.dot { width:6px; height:6px; border-radius:50%; display:inline-block; }
.dot.normal { background:#526e5a; }
.dot.warn-dot { background:#e74c3c; }

.weak-list { display:flex; flex-direction:column; gap:2px; }
.weak-row { display:flex; align-items:center; gap:6px; padding:6px 0; border-bottom:1px solid var(--divider,#f0f0f0); font-size:0.68rem; }
.weak-row:last-child { border-bottom:none; }
.weak-idx { width:16px; height:16px; border-radius:50%; background:var(--bg-tag,#f4f4f4); color:var(--text-muted); font-size:0.56rem; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.weak-name { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-primary); }
.weak-bar-wrap { width:40px; height:4px; background:var(--bg-tag,#f4f4f4); border-radius:2px; overflow:hidden; flex-shrink:0; }
.weak-bar { height:100%; background:#526e5a; border-radius:2px; }
.weak-count { font-weight:700; font-family:monospace; color:var(--text-primary); flex-shrink:0; }

.student-alert-list { display:flex; flex-direction:column; gap:6px; }
.sa-row { display:flex; align-items:center; gap:8px; padding:8px 10px; background:var(--bg-soft,#fafbfa); border-radius:8px; border:1px solid var(--border-light); }
.sa-avatar { width:24px; height:24px; border-radius:50%; background:#526e5a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:0.6rem; font-weight:700; flex-shrink:0; }
.sa-info { flex:1; min-width:0; }
.sa-name { font-size:0.7rem; font-weight:600; color:var(--text-primary); }
.sa-desc { font-size:0.58rem; color:var(--text-muted); }
.sa-score { font-size:0.78rem; font-weight:700; font-family:monospace; color:var(--text-primary); }
.sa-score.danger { color:#c0392b; }

/* Strategy bar */
.strategy-bar { display:flex; align-items:center; padding:16px 20px; border:1.5px solid #526e5a; border-radius:14px; flex-shrink:0; gap:16px; transition:padding 0.2s; }
.strategy-bar.closed { padding:10px 20px; }
.sb-hint { font-size:0.74rem; color:#526e5a; font-weight:600; flex:1; }
.sb-arrow { color:var(--text-muted); transition:transform 0.2s; flex-shrink:0; cursor:pointer; }
.sb-arrow:hover { color:#526e5a; }
.sb-arrow.open { transform:rotate(180deg); }
.sb-items { display:flex; flex:1; }
.sb-item { display:flex; gap:10px; flex:1; padding:12px 14px; border:1.5px solid #526e5a; border-radius:10px; }
.sb-num { width:22px; height:22px; border-radius:5px; background:#526e5a; color:#fff; font-size:0.66rem; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:1px; }
.sb-text { display:flex; flex-direction:column; gap:4px; }
.sb-cls { font-weight:700; color:var(--text-primary); font-size:0.8rem; }
.sb-desc { color:var(--text-muted); font-size:0.72rem; line-height:1.4; }

.class-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; }
.class-card { background:var(--bg-soft,#fafbfa); border:1.5px solid #526e5a; border-radius:10px; padding:12px; }
.class-card.alert { border-color:#e74c3c; border-width:2px; }
.class-head { display:flex; justify-content:space-between; }
.class-name { font-size:0.74rem; font-weight:700; }
.class-score { font-size:0.8rem; font-weight:700; font-family:monospace; }
.class-tags { display:flex; gap:6px; margin-top:6px; font-size:0.6rem; color:var(--text-muted); }
.class-foot { display:flex; justify-content:space-between; margin-top:8px; padding-top:6px; border-top:1px solid var(--divider,#f0f0f0); font-size:0.6rem; color:var(--text-muted); }
.class-action { font-size:0.62rem; font-weight:700; color:#526e5a; }

.two-col { display:grid; grid-template-columns:1fr 1fr; gap:10px; }

.cluster-list { display:flex; flex-direction:column; gap:6px; }
.cluster-item { display:flex; align-items:center; gap:6px; font-size:0.68rem; padding:2px 0; }
.cl-label { font-weight:600; color:var(--text-primary); flex-shrink:0; }
.cl-pct { font-weight:700; color:var(--text-primary); font-family:monospace; flex-shrink:0; }
.cl-desc { color:var(--text-muted); font-size:0.62rem; }

.diff-list { display:flex; flex-direction:column; gap:8px; }
.diff-item { display:flex; align-items:center; gap:6px; font-size:0.68rem; }
.diff-name { width:52px; flex-shrink:0; color:var(--text-primary); text-align:right; }
.diff-bar-wrap { flex:1; height:5px; background:var(--bg-tag,#f4f4f4); border-radius:3px; overflow:hidden; }
.diff-bar { height:100%; background:#526e5a; border-radius:3px; }
.diff-pct { font-weight:700; font-family:monospace; color:var(--text-primary); flex-shrink:0; }

.trend-chart { padding:4px 0; }
.trend-svg { width:100%; height:auto; display:block; }
.trend-labels { display:flex; justify-content:space-between; padding:2px 0 0; }
.tlabel { font-size:0.5rem; color:var(--text-muted); }

.group-section { margin-bottom:10px; }
.group-section:last-child { margin-bottom:0; }
.group-label { font-size:0.62rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }
.group-card { display:flex; gap:6px; padding:6px 10px; background:var(--bg-soft,#fafbfa); border:1px solid var(--border-light); border-radius:8px; margin-bottom:3px; font-size:0.66rem; }
.group-tag { font-weight:700; color:#526e5a; flex-shrink:0; }
.group-desc { color:var(--text-secondary); }
</style>
