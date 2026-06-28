<template>
<div class="analytics-page">
  <!-- Top KPI bar -->
  <section class="kpi-bar">
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.overview?.avgScore ?? '--' }}</div>
      <div class="kpi-label">年级平均分</div>
    </div>
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.overview?.passRate ?? '--' }}<small>%</small></div>
      <div class="kpi-label">及格率</div>
    </div>
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.overview?.excellentRate ?? '--' }}<small>%</small></div>
      <div class="kpi-label">优秀率 (≥90)</div>
    </div>
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.overview?.weakPointCount ?? '--' }}</div>
      <div class="kpi-label">薄弱知识点总数</div>
    </div>
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.overview?.totalStudents ?? '--' }}</div>
      <div class="kpi-label">学籍总人数</div>
    </div>
    <div class="kpi-item">
      <div class="kpi-num">{{ analytics.classStats?.length ?? '--' }}</div>
      <div class="kpi-label">教学班级数</div>
    </div>
  </section>

  <!-- Main content grid -->
  <div class="grid-main">
    <!-- LEFT: Weak points & alerts -->
    <div class="col-left">
      <!-- Weak points frequency -->
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">高频薄弱知识点频次</span>
        </div>
        <div class="panel-body">
          <div v-if="analytics.weakPoints?.length" class="weak-list">
            <div v-for="(wp, i) in analytics.weakPoints" :key="i" class="weak-row">
              <span class="weak-name">{{ wp.name }}</span>
              <span class="weak-count">{{ wp.count }}次</span>
            </div>
          </div>
          <div v-else class="empty-hint">暂无数据</div>
        </div>
      </div>

      <!-- Class alerts -->
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">班级学情动态与预警</span>
        </div>
        <div class="panel-body">
          <div v-if="alertClasses.length" class="alert-list">
            <div v-for="cls in alertClasses" :key="cls.name" class="alert-row" :class="cls.level">
              <div class="alert-info">
                <span class="alert-name">{{ cls.name }}</span>
                <span class="alert-desc">均分{{ cls.avgScore }} / {{ cls.weakness }}</span>
              </div>
              <span class="alert-tag">{{ cls.tag }}</span>
            </div>
          </div>
          <div v-else class="empty-hint">暂无预警</div>
        </div>
      </div>
    </div>

    <!-- CENTER: Class grid -->
    <div class="col-center">
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">班级学情态势 & 薄弱干预节点</span>
          <div class="legend">
            <span><i class="dot dot-normal"></i>常态</span>
            <span><i class="dot dot-alert"></i>关注</span>
          </div>
        </div>
        <div class="panel-body">
          <div v-if="analytics.classStats?.length" class="class-grid">
            <div v-for="cls in analytics.classStats" :key="cls.name"
              class="class-card" :class="{ alert: cls.avgScore < 60 }">
              <div class="class-head">
                <span class="class-name">{{ cls.name }}</span>
                <span class="class-score">{{ cls.avgScore }}</span>
              </div>
              <div class="class-tags">
                <span class="class-tag">{{ cls.studentCount }}人</span>
                <span class="class-tag">{{ cls.submissionCount }}份提交</span>
              </div>
              <div class="class-foot">
                <span class="class-pass">及格率 {{ cls.passRate }}%</span>
                <span class="class-action">{{ cls.avgScore >= 80 ? '稳中求进' : cls.avgScore >= 60 ? '专题突破' : '限时训练' }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无班级数据</div>
        </div>
      </div>
    </div>

    <!-- RIGHT: Strategy -->
    <div class="col-right">
      <!-- Score trend chart placeholder -->
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">学科成绩变化曲线</span>
        </div>
        <div class="panel-body">
          <div class="chart-placeholder">
            <svg viewBox="0 0 100 40" class="trend-svg">
              <path d="M0,35 Q25,20 50,28 T100,10" fill="none" stroke="var(--accent)" stroke-width="1.2"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Teaching strategy -->
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">差异化教学优化策略</span>
        </div>
        <div class="panel-body">
          <div v-if="strategyList.length" class="strategy-list">
            <div v-for="(s, i) in strategyList" :key="i" class="strategy-card">
              <div class="strategy-num">{{ i + 1 }}</div>
              <div class="strategy-info">
                <div class="strategy-cls">{{ s.cls }}</div>
                <div class="strategy-desc">{{ s.desc }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无策略建议</div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../../composables/useAuth.js'
import { useGateway } from '../../composables/useGateway.js'

const { user } = useAuth()
const { getToken } = useGateway()

const analytics = ref({
  overview: null,
  classStats: [],
  weakPoints: [],
})

// Fetch analytics data
async function fetchAnalytics() {
  try {
    const token = getToken()
    const res = await fetch(`/api/analytics/summary?token=${token}`)
    const data = await res.json()
    if (data.ok) {
      analytics.value = data.analytics
    }
  } catch (e) {
    console.error('Failed to fetch analytics:', e)
  }
}

// Compute alert classes (avgScore < 60)
const alertClasses = computed(() => {
  const classes = analytics.value.classStats || []
  return classes
    .filter(c => c.avgScore < 60)
    .map(c => ({
      name: c.name,
      avgScore: c.avgScore,
      weakness: '成绩薄弱',
      tag: '预警',
      level: 'alert',
    }))
    .concat(
      classes
        .filter(c => c.avgScore >= 60 && c.avgScore < 70)
        .map(c => ({
          name: c.name,
          avgScore: c.avgScore,
          weakness: '待提升',
          tag: '关注',
          level: 'warn',
        }))
    )
})

// Generate strategy list based on data
const strategyList = computed(() => {
  const classes = analytics.value.classStats || []
  const strategies = []

  classes.forEach(c => {
    if (c.avgScore < 60) {
      strategies.push({
        cls: c.name,
        desc: `成绩薄弱 → 微专题 + 错题诊所 + 限时训练`,
      })
    } else if (c.avgScore < 70) {
      strategies.push({
        cls: c.name,
        desc: `基础待巩固 → 分层教学 + 专项练习`,
      })
    }
  })

  if (strategies.length === 0) {
    strategies.push({
      cls: '整体',
      desc: '各班表现良好，继续保持稳中求进策略',
    })
  }

  return strategies.slice(0, 4)
})

onMounted(() => {
  fetchAnalytics()
})
</script>

<style scoped>
.analytics-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
  padding: 16px;
  overflow: hidden;
}

/* KPI bar */
.kpi-bar {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  flex-shrink: 0;
}

.kpi-item {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 12px 8px;
  text-align: center;
}

.kpi-num {
  font-family: 'Noto Serif SC', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.kpi-num small {
  font-size: 0.68rem;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-label {
  font-size: 0.62rem;
  color: var(--text-muted);
  margin-top: 4px;
  font-weight: 500;
}

/* Main grid */
.grid-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 250px 1fr 250px;
  gap: 12px;
  overflow: hidden;
}

.col-left,
.col-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.col-center {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

/* Panel */
.panel {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--divider);
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-primary);
}

.panel-body {
  flex: 1;
  padding: 10px 14px;
  overflow-y: auto;
  min-height: 0;
}

/* Legend */
.legend {
  display: flex;
  gap: 10px;
  font-size: 0.6rem;
  color: var(--text-muted);
}

.legend span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-normal {
  background: var(--border-light);
}

.dot-alert {
  background: var(--accent);
}

/* Weak points */
.weak-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.weak-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--divider);
  font-size: 0.7rem;
}

.weak-name {
  color: var(--text-secondary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weak-count {
  color: var(--text-primary);
  font-weight: 700;
  font-family: monospace;
  flex-shrink: 0;
  margin-left: 8px;
}

/* Alert list */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
}

.alert-row.alert {
  background: var(--bg-soft);
  border-color: var(--border-light);
}

.alert-row.warn {
  background: var(--bg-soft);
  border-color: var(--border-light);
}

.alert-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert-name {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-primary);
}

.alert-desc {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: monospace;
}

.alert-tag {
  font-size: 0.6rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-tag);
  color: var(--text-secondary);
}

/* Class grid */
.class-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.class-card {
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100px;
  transition: border-color 0.2s;
}

.class-card:hover {
  border-color: var(--accent);
}

.class-card.alert {
  border-width: 2px;
  border-color: var(--accent);
}

.class-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.class-name {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-primary);
}

.class-score {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: monospace;
}

.class-tags {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

.class-tag {
  font-size: 0.56rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-muted);
}

.class-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--divider);
}

.class-pass {
  font-size: 0.62rem;
  color: var(--text-muted);
}

.class-action {
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* Chart placeholder */
.chart-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
}

.trend-svg {
  width: 100%;
  height: 60px;
}

/* Strategy list */
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-card {
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.strategy-num {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: var(--accent);
  color: var(--bg-root);
  font-size: 0.66rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: monospace;
}

.strategy-info {
  flex: 1;
  min-width: 0;
}

.strategy-cls {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.strategy-desc {
  font-size: 0.64rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Empty hint */
.empty-hint {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 0.72rem;
}

/* Scrollbar */
.col-left::-webkit-scrollbar,
.col-right::-webkit-scrollbar,
.panel-body::-webkit-scrollbar {
  width: 3px;
}

.col-left::-webkit-scrollbar-thumb,
.col-right::-webkit-scrollbar-thumb,
.panel-body::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 2px;
}
</style>
