<template>
<div class="sa-page">
  <header class="page-header">
    <div class="header-left"><h2>学情分析</h2></div>
  </header>

  <!-- KPI 卡片 -->
  <div class="sa-kpis">
    <div class="sa-kpi">
      <div class="sa-kpi-val">{{ stats.totalHours }}<small>h</small></div>
      <div class="sa-kpi-label">累计学习</div>
    </div>
    <div class="sa-kpi">
      <div class="sa-kpi-val">{{ stats.completedTasks }}</div>
      <div class="sa-kpi-label">完成任务</div>
    </div>
    <div class="sa-kpi">
      <div class="sa-kpi-val">{{ stats.avgScore }}</div>
      <div class="sa-kpi-label">平均得分</div>
    </div>
    <div class="sa-kpi warn">
      <div class="sa-kpi-val">{{ stats.weakPoints }}</div>
      <div class="sa-kpi-label">薄弱知识点</div>
    </div>
  </div>

  <div class="sa-body">
    <!-- 左：薄弱点 + 投入曲线 -->
    <div class="sa-left">
      <!-- 知识点薄弱项 -->
      <div class="sa-panel">
        <div class="sa-panel-hd">知识点薄弱项</div>
        <div class="sa-weaklist">
          <div v-for="w in weakPoints" :key="w.name" class="sa-weak-item">
            <div class="sa-weak-top">
              <span>{{ w.name }}</span>
              <span :class="{ low: w.level === 'low', mid: w.level === 'mid', high: w.level === 'high' }">{{ w.label }}</span>
            </div>
            <div class="sa-weak-bar"><i :style="{ width: w.pct + '%' }" :class="w.level"></i></div>
          </div>
        </div>
      </div>

      <!-- 学习投入曲线 -->
      <div class="sa-panel">
        <div class="sa-panel-hd">学习投入趋势</div>
        <div class="sa-chart">
          <div class="sa-bars">
            <div v-for="d in timeData" :key="d.day" class="sa-bar-col">
              <div class="sa-bar-wrap"><div class="sa-bar" :style="{ height: (d.hours / 4 * 100) + '%' }"></div></div>
              <span class="sa-bar-label">{{ d.day }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右：学习任务包 -->
    <div class="sa-right">
      <div class="sa-panel">
        <div class="sa-panel-hd">学习任务包</div>
        <p class="sa-task-intro">根据你的薄弱项自动生成，每周更新。</p>
        <div class="sa-tasks">
          <div v-for="t in taskPack" :key="t.id" class="sa-task-card">
            <div class="sa-task-type" :class="t.type">{{ t.typeLabel }}</div>
            <h3>{{ t.title }}</h3>
            <p>{{ t.desc }}</p>
            <button class="sa-task-btn" @click="startTask(t)">开始练习</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref } from 'vue'

const stats = ref({ totalHours: 48, completedTasks: 23, avgScore: 82, weakPoints: 5 })

const weakPoints = ref([
  { name: '真菌病害诊断', pct: 65, level: 'mid', label: '中等' },
  { name: '农药配比计算', pct: 40, level: 'low', label: '薄弱' },
  { name: '昆虫分类识别', pct: 78, level: 'mid', label: '中等' },
  { name: '病害循环理解', pct: 52, level: 'mid', label: '中等' },
  { name: '生物防治原理', pct: 30, level: 'high', label: '高危' },
])

const timeData = ref([
  { day: '周一', hours: 2.5 }, { day: '周二', hours: 3.2 }, { day: '周三', hours: 1.8 },
  { day: '周四', hours: 3.8 }, { day: '周五', hours: 2.1 }, { day: '周六', hours: 1.2 }, { day: '周日', hours: 2.9 },
])

const taskPack = ref([
  { id: 1, type: 'error', typeLabel: '错题', title: '生物防治原理 · 3道错题重练', desc: '包含你答错的选择题和简答题，附错误推理链回顾' },
  { id: 2, type: 'weak', typeLabel: '靶向', title: '农药配比计算 · 专项练习', desc: '针对配比计算薄弱点，含5道阶梯难度练习' },
  { id: 3, type: 'review', typeLabel: '复习', title: '真菌病害诊断 · 关键点卡片', desc: '纹枯病、稻瘟病、锈病的鉴别要点对比卡片' },
])

function startTask(t) { alert(`开始：${t.title}（演示）`) }
</script>

<style scoped>
.sa-page { flex:1; padding:32px; overflow-y:auto; }
.page-header { margin-bottom:24px; }
.page-header h2 { font-size:1.4rem; font-weight:700; color:var(--text-primary); }

/* KPI */
.sa-kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px; }
.sa-kpi { padding:20px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-md); text-align:center; }
.sa-kpi.warn { border-color:rgba(231,76,60,0.3); background:rgba(231,76,60,0.03); }
.sa-kpi-val { font-size:1.8rem; font-weight:800; color:var(--text-primary); }
.sa-kpi-val small { font-size:0.85rem; font-weight:400; color:var(--text-muted); }
.sa-kpi-label { font-size:0.72rem; color:var(--text-muted); margin-top:4px; }

/* Body */
.sa-body { display:grid; grid-template-columns:1fr 340px; gap:20px; }
.sa-left { display:flex; flex-direction:column; gap:20px; }
.sa-panel { background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-md); padding:20px; }
.sa-panel-hd { font-size:0.8rem; font-weight:700; color:var(--text-primary); margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--divider); }

/* 薄弱点 */
.sa-weaklist { display:flex; flex-direction:column; gap:14px; }
.sa-weak-item { }
.sa-weak-top { display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:6px; }
.sa-weak-top span:first-child { color:var(--text-primary); }
.sa-weak-top span:last-child { font-size:0.66rem; font-weight:700; padding:1px 8px; border-radius:6px; }
.sa-weak-top .low { color:#c0392b; background:rgba(231,76,60,0.08); }
.sa-weak-top .mid { color:#f59e0b; background:rgba(245,158,11,0.08); }
.sa-weak-top .high { color:#e74c3c; background:rgba(231,76,60,0.12); }
.sa-weak-bar { height:6px; background:var(--bg-tag); border-radius:3px; overflow:hidden; }
.sa-weak-bar i { display:block; height:100%; border-radius:3px; }
.sa-weak-bar i.low { background:#e74c3c; }
.sa-weak-bar i.mid { background:#f59e0b; }
.sa-weak-bar i.high { background:#e74c3c; }

/* 投入曲线 */
.sa-chart { }
.sa-bars { display:flex; align-items:flex-end; gap:16px; height:100px; padding-top:8px; }
.sa-bar-col { flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; height:100%; }
.sa-bar-wrap { flex:1; width:100%; display:flex; align-items:flex-end; justify-content:center; }
.sa-bar { width:60%; max-width:32px; background:#526e5a; border-radius:4px 4px 0 0; min-height:4px; transition:height 0.6s; }
.sa-bar-label { font-size:0.62rem; color:var(--text-muted); }

/* 任务包 */
.sa-task-intro { font-size:0.74rem; color:var(--text-muted); margin-bottom:14px; }
.sa-tasks { display:flex; flex-direction:column; gap:12px; }
.sa-task-card { padding:16px; border:1px solid var(--border-light); border-radius:var(--radius-md); transition:all 0.2s; }
.sa-task-card:hover { border-color:#526e5a; }
.sa-task-type { display:inline-block; font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:6px; margin-bottom:6px; }
.sa-task-type.error { border:1px solid #c0392b; color:#c0392b; }
.sa-task-type.weak { border:1px solid #f59e0b; color:#92400e; }
.sa-task-type.review { border:1px solid #526e5a; color:#526e5a; }
.sa-task-card h3 { font-size:0.82rem; font-weight:600; color:var(--text-primary); margin-bottom:4px; }
.sa-task-card p { font-size:0.72rem; color:var(--text-muted); margin-bottom:10px; line-height:1.4; }
.sa-task-btn { padding:6px 16px; border:1.5px solid #526e5a; background:transparent; color:#526e5a; border-radius:16px; font-size:0.7rem; font-weight:600; cursor:pointer; transition:all 0.2s; }
.sa-task-btn:hover { background:#526e5a; color:#fff; }

@media (max-width:768px) { .sa-kpis { grid-template-columns:repeat(2,1fr); } .sa-body { grid-template-columns:1fr; } }
</style>
