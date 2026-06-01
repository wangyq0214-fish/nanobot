<template>
  <div class="app-shell">
    <TeacherNav active-tab="courses" @logout="onLogout" />
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

        <!-- Radar Chart -->
        <div class="chart-section">
          <h3>能力雷达图</h3>
          <div ref="radarEl" class="chart-container"></div>
        </div>

        <!-- Weak Points -->
        <div class="section">
          <h3>薄弱知识点</h3>
          <table class="data-table">
            <thead><tr><th>知识点</th><th>掌握度</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="wp in mockData.weakPoints" :key="wp.name">
                <td>{{ wp.name }}</td>
                <td>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: wp.pct + '%', background: wp.pct < 50 ? '#e74c3c' : wp.pct < 70 ? '#f39c12' : '#2ecc71' }"></div>
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

        <!-- Homework History -->
        <div class="section">
          <h3>作业记录</h3>
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

        <!-- Learning Path -->
        <div class="section">
          <h3>学习路径进度</h3>
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
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import echarts from '../../utils/echarts.js'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'
import TeacherNav from '../../components/TeacherNav.vue'

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

// Mock data
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
.app-shell { display: flex; flex-direction: column; height: 100vh; background: var(--bg, #f8f6f1); }
.main-area { flex: 1; overflow-y: auto; padding: 24px 32px; }
.analytics-page { width: 100%; }

/* Login */
.login-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; }
.login-card { background: #fff; border-radius: 16px; padding: 40px; width: 360px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.login-header { text-align: center; margin-bottom: 24px; }
.login-logo { font-size: 1.5rem; font-weight: 700; }
.login-logo .dot { display: inline-block; width: 8px; height: 8px; background: #5b8def; border-radius: 50%; margin-right: 6px; }
.login-subtitle { color: #888; font-size: 0.85rem; margin-top: 4px; }
.login-input { width: 100%; padding: 10px 14px; border: 1.5px solid #e0dcd5; border-radius: 8px; font-size: 0.9rem; outline: none; box-sizing: border-box; }
.login-error { color: #e74c3c; font-size: 0.8rem; margin-top: 8px; }
.login-submit { width: 100%; padding: 10px; background: #5b8def; color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-top: 12px; }
.login-submit:disabled { opacity: 0.5; }

.back-btn { background: none; border: none; color: #5b8def; font-size: 0.85rem; cursor: pointer; margin-bottom: 16px; padding: 0; }

/* Student Card */
.student-card { display: flex; align-items: center; gap: 16px; background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; border: 1px solid #e8e4db; }
.avatar { width: 48px; height: 48px; border-radius: 50%; background: #5b8def; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 700; }
.info h2 { margin: 0; font-size: 1.2rem; }
.info .meta { margin: 4px 0 0; font-size: 0.82rem; color: #888; }

/* Chart */
.chart-section { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 24px; border: 1px solid #e8e4db; }
.chart-section h3 { margin: 0 0 12px; font-size: 1rem; }
.chart-container { width: 100%; height: 320px; }

/* Sections */
.section { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #e8e4db; }
.section h3 { margin: 0 0 14px; font-size: 1rem; }

/* Data table */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0ede8; font-size: 0.82rem; }
.data-table th { font-weight: 600; color: #555; }

/* Progress bar */
.progress-bar { display: inline-block; width: 80px; height: 6px; background: #e8e4db; border-radius: 3px; vertical-align: middle; margin-right: 8px; }
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.pct-label { font-size: 0.78rem; color: #666; }

/* Status badges */
.status-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.status-badge.danger { background: #fde8e8; color: #e74c3c; }
.status-badge.warning { background: #fff3e0; color: #e67e22; }
.status-badge.good { background: #e8f5e9; color: #2e7d32; }

/* Learning path */
.path-list { display: flex; flex-direction: column; gap: 12px; }
.path-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f0ede8; }
.path-item:last-child { border-bottom: none; }
.path-indicator { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.path-indicator.done { background: #2ecc71; }
.path-indicator.current { background: #f39c12; }
.path-indicator.future { background: #ddd; }
.path-info { flex: 1; }
.path-name { font-weight: 600; font-size: 0.88rem; display: block; }
.path-desc { font-size: 0.78rem; color: #888; }
.path-pct { font-size: 0.82rem; font-weight: 600; color: #555; }

/* Dark */
:global(body.dark) .app-shell { background: #12121a; }
:global(body.dark) .login-card, :global(body.dark) .student-card,
:global(body.dark) .chart-section, :global(body.dark) .section { background: #1e1e2e; border-color: #333; }
:global(body.dark) .info h2, :global(body.dark) .chart-section h3, :global(body.dark) .section h3 { color: #e0e0e0; }
:global(body.dark) .login-input { background: #2a2a3a; border-color: #444; color: #e0e0e0; }
:global(body.dark) .data-table th { color: #ccc; }
</style>
