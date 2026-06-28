<template>
  <div class="main-area">
      <div class="analytics-page">
        <button class="back-btn" @click="$router.push(`/teacher/courses/${courseId}`)">← 返回课程</button>

        <!-- Student Info -->
        <div class="student-card">
          <div class="avatar">{{ studentName[0] }}</div>
          <div class="info">
            <h2>{{ studentName }}</h2>
            <p class="meta">{{ courseName }} · 综合 {{ mockData.totalScore }}分</p>
          </div>
        </div>

        <!-- 2x2 网格容器 -->
        <div class="grid-container">
          <!-- Radar Chart -->
          <div class="chart-section panel">
            <div class="panel-hd">
              <i class="panel-accent-bar"></i>
              <span class="panel-title">能力雷达图</span>
            </div>
            <div class="panel-body">
              <div ref="radarEl" class="chart-container"></div>
            </div>
          </div>

          <!-- Weak Points -->
          <div class="section panel">
            <div class="panel-hd">
              <i class="panel-accent-bar"></i>
              <span class="panel-title">薄弱知识点</span>
            </div>
            <div class="panel-body">
              <table class="data-table">
                <thead><tr><th>知识点</th><th>掌握度</th><th>状态</th></tr></thead>
                <tbody>
                  <tr v-for="wp in mockData.weakPoints" :key="wp.name">
                    <td>{{ wp.name }}</td>
                    <td>
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: wp.pct + '%', background: wp.pct < 50 ? '#ef4444' : wp.pct < 70 ? '#f59e0b' : '#0d9488' }"></div>
                      </div>
                      <span class="pct-label">{{ wp.pct }}%</span>
                    </td>
                    <td><span class="status-badge" :class="wp.pct < 50 ? 'danger' : wp.pct < 70 ? 'warning' : 'good'">
                      {{ wp.pct < 50 ? '需加强' : wp.pct < 70 ? '待巩固' : '已掌握' }}
                    </span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Homework History -->
          <div class="section panel">
            <div class="panel-hd">
              <i class="panel-accent-bar"></i>
              <span class="panel-title">作业记录</span>
            </div>
            <div class="panel-body">
              <table class="data-table">
                <thead><tr><th>作业</th><th>提交时间</th><th>得分</th><th>状态</th></tr></thead>
                <tbody>
                  <tr v-for="hw in mockData.homeworkHistory" :key="hw.title">
                    <td>{{ hw.title }}</td>
                    <td>{{ hw.submittedAt }}</td>
                    <td>{{ hw.score }}/{{ hw.total }}</td>
                    <td><span class="status-badge" :class="hw.score / hw.total >= 0.7 ? 'good' : 'warning'">
                      {{ hw.score / hw.total >= 0.7 ? '良好' : '待提升' }}
                    </span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Learning Path -->
          <div class="section panel">
            <div class="panel-hd">
              <i class="panel-accent-bar"></i>
              <span class="panel-title">学习路径进度</span>
            </div>
            <div class="panel-body">
              <div class="path-list">
                <div v-for="p in mockData.learningPath" :key="p.name" class="path-item">
                  <div class="path-indicator" :class="p.status"></div>
                  <div class="path-info">
                    <span class="path-name">{{ p.name }}</span>
                    <span class="path-desc">{{ p.desc }}</span>
                  </div>
                  <span class="path-pct">{{ p.pct }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup>
// 脚本与原来完全一致，无需任何修改
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import echarts from '../../utils/echarts.js'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'

const router = useRouter()
const route = useRoute()
const { user, logout: authLogout } = useAuth()
const { currentCourse: course, fetchCourseDetail } = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

const courseId = route.params.courseId
const studentId = route.params.studentId
const studentName = ref(studentId)
const courseName = ref('')
const radarEl = ref(null)
let chartInstance = null

const mockData = {
  totalScore: 78.5,
  weakPoints: [
    { name: '光合作用光反应', pct: 35 },
    { name: '土壤团粒结构', pct: 48 },
    { name: '植物激素调控', pct: 52 },
    { name: '作物产量估算', pct: 65 },
    { name: '叶面积指数(LAI)', pct: 72 },
    { name: '蒸腾作用', pct: 80 },
  ],
  homeworkHistory: [
    { title: '光合作用与产量形成', submittedAt: '2026-05-20', score: 42, total: 50 },
    { title: '土壤肥料学基础', submittedAt: '2026-05-18', score: 35, total: 50 },
    { title: '植物生理学综合', submittedAt: '2026-05-15', score: 28, total: 40 },
    { title: '作物栽培技术', submittedAt: '2026-05-10', score: 44, total: 50 },
  ],
  learningPath: [
    { name: '植物生理基础', desc: '光合作用、呼吸作用、蒸腾作用', status: 'done', pct: 85 },
    { name: '土壤与肥料', desc: '土壤结构、肥料分类、施肥技术', status: 'current', pct: 60 },
    { name: '作物栽培技术', desc: '播种、田间管理、收获', status: 'current', pct: 45 },
    { name: '病虫害防治', desc: '识别、预防、综合治理', status: 'future', pct: 20 },
    { name: '智慧农业技术', desc: '传感器、遥感、精准管理', status: 'future', pct: 10 },
  ],
}

function onLogout() { authLogout(); router.push('/login') }

async function loadCourse() {
  try {
    const c = await fetchCourseDetail(courseId, getToken())
    if (c) courseName.value = c.courseName
  } catch { /* ignore */ }
}

function initRadar() {
  if (!radarEl.value) return
  chartInstance = echarts.init(radarEl.value)
  chartInstance.setOption({
    radar: {
      indicator: [
        { name: '植物生理', max: 100 },
        { name: '土壤肥料', max: 100 },
        { name: '作物栽培', max: 100 },
        { name: '病虫害防治', max: 100 },
        { name: '数据分析', max: 100 },
        { name: '综合规划', max: 100 },
      ],
      shape: 'polygon',
      splitNumber: 4,
    },
    series: [{
      type: 'radar',
      data: [{
        value: [65, 52, 78, 45, 40, 58],
        name: studentId,
        areaStyle: { opacity: 0.15 },
        lineStyle: { width: 2 },
        itemStyle: { color: '#5b8def' },
      }],
    }],
  })
}

onMounted(async () => {
  if (!user.value) return
  await loadCourse()
  await nextTick()
  initRadar()
})
</script>

<style scoped>
/* ========== 主题变量 ========== */
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255, 255, 255, 0.55);
  --accent: #6b5df0;
  --accent-deep: #5a4ad0;
  --accent-soft: rgba(107, 93, 240, 0.09);
  --accent-glow: rgba(107, 93, 240, 0.22);
  --border-light: rgba(0, 0, 0, 0.08);
  --border-medium: rgba(0, 0, 0, 0.14);
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0, 0, 0, 0.06);
  --danger: #ef4444;
  --warning: #f59e0b;
  --success: #0d9488;
}

body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18, 19, 34, 0.50);
  --accent: #8b70ff;
  --accent-deep: #6b50e0;
  --accent-soft: rgba(139, 112, 255, 0.12);
  --accent-glow: rgba(139, 112, 255, 0.30);
  --border-light: rgba(255, 255, 255, 0.08);
  --border-medium: rgba(255, 255, 255, 0.16);
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255, 255, 255, 0.07);
}
body.green {
  --bg-root: #f7f8f7;
  --bg-card: rgba(255, 255, 255, 0.85);
  --accent: #526e5a;
  --accent-deep: #415848;
  --accent-soft: rgba(82, 110, 90, 0.09);
  --accent-glow: rgba(82, 110, 90, 0.22);
  --border-light: rgba(0, 0, 0, 0.06);
  --border-medium: rgba(0, 0, 0, 0.1);
  --text-primary: #1e2720;
  --text-secondary: #556056;
  --text-muted: #8fa091;
  --divider: rgba(0, 0, 0, 0.05);
  --danger: #ef4444;
  --warning: #f59e0b;
  --success: #0d9488;
}

/* ========== 布局 ========== */
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-root);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  transition: background 0.4s, color 0.4s;
}

.main-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-light) transparent;
}

.main-area::-webkit-scrollbar {
  width: 4px;
}
.main-area::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 2px;
}

.analytics-page {
  width: 100%;
}

/* ========== 返回按钮 ========== */
.back-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 0.85rem;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 4px 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}
.back-btn:hover {
  color: var(--accent-deep);
}

/* ========== 学生卡片 ========== */
.student-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1.8px solid var(--accent);
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: 0 0 16px var(--accent-soft);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.student-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 28px var(--accent-glow);
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  box-shadow: 0 0 12px var(--accent-glow);
}

.info h2 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.info .meta {
  margin: 4px 0 0;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

/* ========== 2x2 网格容器 ========== */
.grid-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* ========== 通用面板样式 ========== */
.panel {
  background: var(--bg-card);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1.8px solid var(--accent);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 0 16px var(--accent-soft);
  transition: border-color 0.3s, box-shadow 0.3s;
  /* 移除 margin-bottom，网格 gap 已控制间距 */
  margin-bottom: 0;
}
.panel:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 28px var(--accent-glow);
}

.panel-hd {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--divider);
}

.panel-accent-bar {
  display: inline-block;
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, var(--accent), var(--accent-deep));
  border-radius: 2px;
  box-shadow: 0 0 8px var(--accent-glow);
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.4px;
}

.panel-body {
  padding: 16px 20px;
}

/* ========== 图表容器 ========== */
.chart-container {
  width: 100%;
  height: 280px; /* 适当缩小，适应网格 */
}

/* ========== 表格 ========== */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--divider);
  font-size: 0.82rem;
  color: var(--text-primary);
}

.data-table th {
  font-weight: 600;
  color: var(--text-secondary);
}

/* ========== 进度条 ========== */
.progress-bar {
  display: inline-block;
  width: 80px;
  height: 6px;
  background: var(--divider);
  border-radius: 3px;
  vertical-align: middle;
  margin-right: 8px;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.pct-label {
  font-size: 0.78rem;
  color: var(--text-muted);
}

/* ========== 状态徽章 ========== */
.status-badge {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.status-badge.danger {
  background: rgba(239, 68, 68, 0.08);
  color: var(--danger);
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.status-badge.warning {
  background: rgba(245, 158, 11, 0.08);
  color: var(--warning);
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.status-badge.good {
  background: rgba(13, 148, 136, 0.08);
  color: var(--success);
  border: 1px solid rgba(13, 148, 136, 0.25);
}

/* ========== 学习路径 ========== */
.path-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.path-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--divider);
}
.path-item:last-child {
  border-bottom: none;
}

.path-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.path-indicator.done {
  background: var(--success);
  box-shadow: 0 0 6px rgba(13, 148, 136, 0.4);
}

.path-indicator.current {
  background: var(--warning);
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.path-indicator.future {
  background: var(--text-muted);
  opacity: 0.4;
}

.path-info {
  flex: 1;
}

.path-name {
  font-weight: 600;
  font-size: 0.88rem;
  display: block;
  color: var(--text-primary);
}

.path-desc {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.path-pct {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--accent);
}
</style>