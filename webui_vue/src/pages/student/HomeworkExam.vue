<template>
<div class="he-page">
  <header class="page-header">
    <div class="header-left"><h2>作业·考试</h2></div>
    <div class="he-tabs">
      <span :class="{ on: heTab === 'homework' }" @click="heTab = 'homework'">日常作业</span>
      <span :class="{ on: heTab === 'exam' }" @click="heTab = 'exam'">限时考试</span>
    </div>
  </header>

  <!-- 作业列表 -->
  <div v-if="heTab === 'homework'" class="he-list">
    <div v-for="h in homeworkList" :key="h.id" class="he-card" @click="openHomework(h)">
      <div class="he-left">
        <span class="he-icon">📝</span>
        <div>
          <h3>{{ h.title }}</h3>
          <div class="he-meta">{{ h.courseName }} · 截止 {{ h.deadline }} · {{ h.questionCount }} 题</div>
        </div>
      </div>
      <div class="he-right">
        <span class="he-status" :class="{ done: h.submitted, late: h.overdue && !h.submitted }">
          {{ h.submitted ? '已提交' : h.overdue ? '已逾期' : '待提交' }}
        </span>
        <span v-if="h.submitted && h.score !== null" class="he-score">{{ h.score }}分</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
      </div>
    </div>
    <div v-if="homeworkList.length === 0" class="empty">暂无作业</div>
  </div>

  <!-- 考试列表 -->
  <div v-else class="he-list">
    <div v-for="e in examList" :key="e.id" class="he-card" @click="openExam(e)">
      <div class="he-left">
        <span class="he-icon">📋</span>
        <div>
          <h3>{{ e.title }}</h3>
          <div class="he-meta">{{ e.courseName }} · {{ e.duration }}分钟 · {{ e.startTime }} 开始</div>
        </div>
      </div>
      <div class="he-right">
        <span class="he-status" :class="{ done: e.submitted, active: e.ongoing }">
          {{ e.submitted ? '已交卷' : e.ongoing ? '进行中' : e.ended ? '已结束' : '未开始' }}
        </span>
        <span v-if="e.submitted && e.score !== null" class="he-score">{{ e.score }}分</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
      </div>
    </div>
    <div v-if="examList.length === 0" class="empty">暂无考试</div>
  </div>
</div>
</template>

<script setup>
import { ref } from 'vue'

const heTab = ref('homework')

const homeworkList = ref([
  { id: 1, title: '水稻纹枯病田间识别作业', courseName: '作物病理学', deadline: '7月30日 23:59', questionCount: 5, submitted: false, overdue: false },
  { id: 2, title: '农药配比计算练习', courseName: '植保基础', deadline: '7月28日 23:59', questionCount: 3, submitted: true, overdue: false, score: 92 },
  { id: 3, title: '小麦锈病防治方案设计', courseName: '作物病理学', deadline: '7月20日 23:59', questionCount: 4, submitted: false, overdue: true },
])

const examList = ref([
  { id: 10, title: '植物病理学期中考试', courseName: '作物病理学', duration: 60, startTime: '7月30日 14:00', submitted: false, ongoing: false, ended: false },
  { id: 11, title: '植保基础单元测验', courseName: '植保基础', duration: 30, startTime: '7月25日 10:00', submitted: true, ongoing: false, ended: true, score: 78 },
])

function openHomework(h) { alert(`打开作业：${h.title}（演示）`) }
function openExam(e) { alert(`打开考试：${e.title}（演示）`) }
</script>

<style scoped>
.he-page { flex:1; padding:32px; overflow-y:auto; }
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.header-left h2 { font-size:1.4rem; font-weight:700; color:var(--text-primary); }
.he-tabs { display:flex; gap:2px; background:var(--bg-tag); padding:3px; border-radius:20px; }
.he-tabs span { padding:7px 18px; border-radius:18px; font-size:0.78rem; color:var(--text-muted); cursor:pointer; transition:all 0.2s; }
.he-tabs span:hover { color:var(--text-primary); }
.he-tabs span.on { background:var(--bg-card); color:#526e5a; font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,0.05); }

.he-list { display:flex; flex-direction:column; gap:10px; }
.he-card { display:flex; align-items:center; justify-content:space-between; padding:18px 22px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-md); cursor:pointer; transition:all 0.2s; }
.he-card:hover { border-color:#526e5a; }
.he-left { display:flex; align-items:center; gap:14px; }
.he-icon { font-size:1.3rem; }
.he-left h3 { font-size:0.9rem; font-weight:600; color:var(--text-primary); }
.he-meta { font-size:0.72rem; color:var(--text-muted); margin-top:3px; }
.he-right { display:flex; align-items:center; gap:12px; color:var(--text-muted); }
.he-status { font-size:0.7rem; font-weight:600; padding:3px 10px; border-radius:10px; border:1px solid var(--border-light); color:var(--text-muted); }
.he-status.done { color:#526e5a; border-color:#526e5a; }
.he-status.late { color:#e74c3c; border-color:#e74c3c; }
.he-status.active { color:#526e5a; border-color:#526e5a; background:rgba(82,110,90,0.06); }
.he-score { font-size:0.85rem; font-weight:700; color:var(--text-primary); }
.empty { text-align:center; padding:48px 0; color:var(--text-muted); font-size:0.82rem; }
</style>
