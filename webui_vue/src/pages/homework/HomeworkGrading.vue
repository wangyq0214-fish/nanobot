<template>
<!-- ====== LOGIN SCREEN ====== -->
<div v-if="!user" class="login-screen">
  <div class="login-card">
    <div class="login-header">
      <div class="login-logo"><span class="dot"></span>Nanobot</div>
      <p class="login-subtitle">作业智能批改</p>
    </div>
    <div class="login-roles">
      <button v-for="r in roleOptions" :key="r.role" class="role-btn" :class="{ active: loginRole === r.role }" @click="loginRole = r.role">
        <span class="role-icon">{{ r.icon }}</span>
        <span class="role-label">{{ r.label }}</span>
      </button>
    </div>
    <input class="login-input" v-model="loginUserId" placeholder="输入用户名" @keydown.enter="handleLogin" autofocus />
    <p v-if="loginError" class="login-error">{{ loginError }}</p>
    <button class="login-submit" @click="handleLogin" :disabled="!loginRole || !loginUserId.trim() || loginLoading">
      {{ loginLoading ? '连接中...' : (authMode === 'login' ? '登录' : '注册') }}
    </button>
    <button class="login-toggle" @click="toggleAuthMode">
      {{ authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
    </button>
  </div>
</div>

<!-- ====== MAIN APP SHELL ====== -->
<div v-else class="app-shell">

<!-- ====== TOP NAV ====== -->
<nav class="top-nav">
  <div class="nav-left"><span class="nav-logo"><span class="dot"></span>Nanobot</span></div>
  <div class="nav-center">
    <span class="nav-tab" @click="goToLessonPlan">教案与活动</span>
    <span class="nav-tab active">作业批改</span>
    <span class="nav-tab" @click="goToAnalytics">学情分析</span>
  </div>
  <div class="nav-right">
    <span class="conn-status offline" title="Demo 模式"><span class="conn-dot"></span><span class="conn-label">Demo</span></span>
    <button class="nav-icon" @click="toggleTheme" title="切换主题">
      <svg v-if="!isDark" viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16 7 7 0 0 1 0-14"/></svg>
      <svg v-else viewBox="0 0 20 20"><circle cx="10" cy="10" r="4"/><path d="M10 2v2m0 12v2M2 10h2m12 0h2M4.5 4.5l1.5 1.5m8 8l1.5 1.5M4.5 15.5l1.5-1.5m8-8l1.5-1.5"/></svg>
    </button>
    <button class="nav-icon" @click="handleLogout" title="退出登录">
      <svg viewBox="0 0 20 20"><path d="M7 17H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h3M13 14l4-4-4-4M17 10H7"/></svg>
    </button>
    <div class="nav-avatar" :title="user?.userId || ''">{{ user?.userId?.[0] || '?' }}</div>
  </div>
</nav>

<!-- ====== MAIN AREA ====== -->
<div class="main-area">

<!-- ====== LEFT: SUBMISSION LIST ====== -->
<aside class="panel panel-left" :class="{ collapsed: panelCollapsed.left }">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
  <button class="panel-toggle" @click="panelCollapsed.left = !panelCollapsed.left" :title="panelCollapsed.left ? '展开' : '收起'">
    <svg viewBox="0 0 16 16" width="14" height="14"><path d="M10 4L6 8l4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>

  <div class="pl-header">
    <span class="pl-title">提交列表</span>
    <span class="pl-badge">{{ ungradedCount }} 待批</span>
  </div>
  <div class="pl-search">
    <svg viewBox="0 0 20 20" class="pl-search-icon"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
    <input v-model="searchQuery" placeholder="搜索学生或作业..." />
  </div>
  <div class="pl-filters">
    <span class="pl-chip" :class="{ on: statusFilter === 'all' }" @click="statusFilter = 'all'">全部</span>
    <span class="pl-chip" :class="{ on: statusFilter === 'pending' }" @click="statusFilter = 'pending'">待批改</span>
    <span class="pl-chip" :class="{ on: statusFilter === 'graded' }" @click="statusFilter = 'graded'">已批改</span>
  </div>
  <div class="pl-list">
    <div v-for="(sub, si) in filteredSubmissions" :key="sub.id"
      class="submission-row" :class="{ active: activeId === sub.id }"
      @click="selectSubmission(sub)" :style="{ animationDelay: si * 0.03 + 's' }">
      <div class="sr-rank">{{ si + 1 }}</div>
      <div class="sr-avatar">{{ sub.student[0] }}</div>
      <div class="sr-body">
        <div class="sr-name">{{ sub.student }}</div>
        <div class="sr-desc">{{ sub.title }}</div>
      </div>
      <div class="sr-tail">
        <span v-if="sub.status === 'graded'" class="sr-score">{{ sub.score }}</span>
        <span v-else class="sr-dot"></span>
      </div>
    </div>
    <div v-if="filteredSubmissions.length === 0" class="pl-empty">暂无匹配项</div>
  </div>
  <div class="pl-footer">
    <div class="pl-stats-row">
      <div class="pl-stat">
        <div class="pl-stat-val">{{ submissions.length }}</div>
        <div class="pl-stat-lbl">总提交</div>
      </div>
      <div class="pl-stat">
        <div class="pl-stat-val">{{ gradedCount }}</div>
        <div class="pl-stat-lbl">已批改</div>
      </div>
      <div class="pl-stat">
        <div class="pl-stat-val">{{ avgScore }}</div>
        <div class="pl-stat-lbl">平均分</div>
      </div>
    </div>
    <button class="batch-btn" :disabled="ungradedCount === 0" @click="batchGradeAll">
      一键批改 {{ ungradedCount }} 份
    </button>
  </div>
</aside>

<!-- ====== CENTER: QUESTION VIEWER ====== -->
<section class="panel panel-center">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>

  <div v-if="!activeSubmission" class="center-empty">
    <div class="empty-icon-wrap">
      <svg viewBox="0 0 20 20"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>
    </div>
    <p class="empty-title">选择左侧作业</p>
    <p class="empty-desc">开始 AI 辅助批改</p>
  </div>

  <div v-else class="center-scroll">
    <!-- Student info -->
    <div class="student-bar">
      <div class="sb-left">
        <div class="sb-avatar">{{ activeSubmission.student[0] }}</div>
        <div>
          <div class="sb-name">{{ activeSubmission.student }} <span class="sb-class">{{ activeSubmission.className }}</span></div>
          <div class="sb-meta">{{ activeSubmission.title }} · {{ activeSubmission.date }}</div>
        </div>
      </div>
      <span class="sb-status" :class="{ done: activeSubmission.status === 'graded' }">
        {{ activeSubmission.status === 'graded' ? '✓ 已批改' : '待批改' }}
      </span>
    </div>

    <!-- Question type tabs -->
    <div class="q-tabs">
      <span class="q-tab" :class="{ on: questionType === 'all' }" @click="questionType = 'all'">全部</span>
      <span class="q-tab" :class="{ on: questionType === 'subjective' }" @click="questionType = 'subjective'">主观题</span>
      <span class="q-tab" :class="{ on: questionType === 'objective' }" @click="questionType = 'objective'">客观题</span>
      <span class="q-tab-summary">{{ displayQuestions.length }} 题</span>
    </div>

    <!-- Question cards -->
    <div class="q-list">
      <div v-for="(q, qi) in displayQuestions" :key="q.id" class="q-card" :class="{ graded: q.graded, 'q-obj': q.objType, 'q-sub': !q.objType }">
        <!-- Left accent strip -->
        <div class="q-accent"></div>

        <div class="q-inner">
          <!-- Header -->
          <div class="q-top">
            <span class="q-idx">{{ qi + 1 }}</span>
            <span class="q-kind">{{ q.typeLabel }}</span>
            <span class="q-pts">{{ q.maxScore }} 分</span>
          </div>

          <!-- Stem -->
          <div class="q-stem">{{ q.stem }}</div>

          <!-- 客观题: 选择题 -->
          <div v-if="q.objType === 'choice'" class="q-opts">
            <div v-for="opt in q.options" :key="opt.key" class="q-opt"
              :class="{ correct: q.graded && opt.key === q.answerKey, wrong: q.graded && opt.key === q.studentPick && opt.key !== q.answerKey, picked: opt.key === q.studentPick }">
              <span class="q-opt-letter">{{ opt.key }}</span>
              <span class="q-opt-text">{{ opt.text }}</span>
            </div>
          </div>

          <!-- 客观题: 判断题 -->
          <div v-if="q.objType === 'tf'" class="q-tf">
            <span class="q-tf-label">学生答案</span>
            <span class="q-tf-val" :class="{ 'is-correct': q.graded && q.studentPick === q.answerKey, 'is-wrong': q.graded && q.studentPick !== q.answerKey }">{{ q.studentPick }}</span>
            <span v-if="q.graded && q.studentPick !== q.answerKey" class="q-tf-ref">正确答案：{{ q.answerKey }}</span>
          </div>

          <!-- 客观题: 填空题 -->
          <div v-if="q.objType === 'fill'" class="q-fill">
            <span class="q-fill-label">学生答案</span>
            <code class="q-fill-val" :class="{ 'is-correct': q.graded && q.studentPick === q.answerKey, 'is-wrong': q.graded && q.studentPick !== q.answerKey }">{{ q.studentPick || '(空)' }}</code>
            <span v-if="q.graded && q.studentPick !== q.answerKey" class="q-fill-ref">参考答案：{{ q.answerKey }}</span>
          </div>

          <!-- 主观题: 学生作答 -->
          <div v-if="!q.objType" class="q-answer-area">
            <div class="q-answer-box">
              <div class="q-answer-label">学生作答</div>
              <p class="q-answer-text">{{ q.studentAnswer }}</p>
            </div>
            <div v-if="q.referenceAnswer" class="q-ref-box">
              <div class="q-ref-label">参考答案</div>
              <p class="q-ref-text">{{ q.referenceAnswer }}</p>
            </div>
          </div>

          <!-- 评分结果 -->
          <div v-if="q.graded" class="q-footer">
            <span class="q-footer-score" :class="{ full: q.studentScore === q.maxScore, half: q.studentScore > 0 && q.studentScore < q.maxScore, zero: q.studentScore === 0 }">{{ q.studentScore }}/{{ q.maxScore }}</span>
            <span class="q-footer-note">{{ q.comment }}</span>
          </div>
        </div>
      </div>
      <div v-if="displayQuestions.length === 0" class="q-empty">该分类下暂无题目</div>
    </div>
  </div>
</section>

<!-- ====== RIGHT: GRADING DASHBOARD ====== -->
<aside class="panel panel-right" :class="{ collapsed: panelCollapsed.right }">
  <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
  <button class="panel-toggle right-toggle" @click="panelCollapsed.right = !panelCollapsed.right" :title="panelCollapsed.right ? '展开' : '收起'">
    <svg viewBox="0 0 16 16" width="14" height="14"><path d="M6 4l4 4-4 4" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>

  <div v-if="!activeSubmission" class="pr-empty">
    <svg viewBox="0 0 20 20" width="28" height="28"><circle cx="10" cy="10" r="7"/><path d="M10 6v5M10 13v1"/></svg>
    <p>选择作业后<br>此处展示批改仪表盘</p>
  </div>

  <div v-else class="pr-scroll">
    <!-- Pending state -->
    <template v-if="activeSubmission.status === 'pending'">
      <div class="pr-section">
        <div class="pr-sec-title">AI 批改</div>
        <p class="grade-intro">AI 助教将对客观题自动判分，主观题根据评分标准智能评阅，并生成多维分析报告。</p>
        <div class="grade-opts">
          <label class="grade-opt"><input type="checkbox" v-model="gradeOptions.detailed" checked /><span>逐题点评</span></label>
          <label class="grade-opt"><input type="checkbox" v-model="gradeOptions.rubric" checked /><span>维度分析</span></label>
          <label class="grade-opt"><input type="checkbox" v-model="gradeOptions.suggestions" checked /><span>改进建议</span></label>
        </div>
        <button class="grade-start" @click="gradeSubmission(activeSubmission)" :disabled="gradingInProgress">
          <span v-if="gradingInProgress" class="grade-spinner"></span>
          {{ gradingInProgress ? 'AI 正在批改…' : '开始 AI 批改' }}
        </button>
      </div>
    </template>

    <!-- Graded dashboard -->
    <template v-if="activeSubmission.status === 'graded'">
      <!-- Rubric radar chart -->
      <div class="pr-section">
        <div class="pr-sec-title">评分维度</div>
        <div v-if="radarData" class="radar-wrap">
          <svg viewBox="0 0 220 220" class="radar-svg">
            <!-- Concentric rings -->
            <polygon v-for="(ring, ri) in radarData.rings" :key="'r'+ri"
              :points="ring" :class="'radar-ring rl-' + (ri+1)"
            />
            <!-- Axis lines -->
            <line v-for="(ax, ai) in radarData.axes" :key="'a'+ai"
              x1="110" y1="110" :x2="ax.x2" :y2="ax.y2" class="radar-axis"
            />
            <!-- Data polygon -->
            <polygon :points="radarData.dataPts" class="radar-data"/>
            <!-- Data dots -->
            <circle v-for="(dot, di) in radarData.dots" :key="'d'+di"
              :cx="dot.x" :cy="dot.y" r="3.5" class="radar-dot"
            />
            <!-- Labels -->
            <text v-for="(ax, ai) in radarData.axes" :key="'l'+ai"
              :x="ax.lx" :y="ax.ly" class="radar-label"
              :class="{ 'radar-label-top': ax.ly < 70, 'radar-label-bot': ax.ly > 150 }"
              text-anchor="middle" dominant-baseline="central"
            >{{ radarData.dims[ai].name }}</text>
          </svg>
          <!-- Score legend -->
          <div class="radar-legend">
            <span v-for="(d, di) in radarData.dims" :key="di" class="radar-legend-item">
              <i class="radar-legend-dot"></i>{{ d.name }} {{ d.score }}/{{ d.max }}
            </span>
          </div>
        </div>
      </div>

      <!-- Score distribution histogram -->
      <div class="pr-section">
        <div class="pr-sec-title">班级分布</div>
        <div class="histogram">
          <div v-for="bar in scoreDist" :key="bar.range" class="hist-col">
            <div class="hist-count">{{ bar.count }}人</div>
            <div class="hist-bar-wrap">
              <div class="hist-bar-spacer" :style="{ flex: (100 - bar.pct) + ' 0 0' }"></div>
              <div class="hist-bar" :style="{ flex: bar.pct + ' 0 0' }" :class="{ highlight: bar.isCurrent }"></div>
            </div>
            <div class="hist-label">{{ bar.range }}</div>
          </div>
        </div>
        <div class="hist-legend">
          <span class="hist-avg">班级均分 {{ classAvg }} · 最高 {{ classMax }} · 最低 {{ classMin }}</span>
        </div>
      </div>

      <!-- Notebook review -->
      <div class="pr-section">
        <div class="pr-sec-title">综合评语</div>
        <div class="notebook">
          <div class="notebook-score-row">
            <span class="notebook-score">{{ activeSubmission.score }}</span>
            <span class="notebook-score-label">分 · {{ scoreWord }}</span>
          </div>
          <p class="notebook-text">{{ activeSubmission.feedback }}</p>
        </div>
      </div>

      <!-- Strengths -->
      <div class="pr-section" v-if="activeSubmission.strengths?.length">
        <div class="pr-sec-title">优势亮点</div>
        <div class="notebook">
          <div v-for="(s, si) in activeSubmission.strengths" :key="si" class="notebook-li">{{ s }}</div>
        </div>
      </div>

      <!-- Improvements -->
      <div class="pr-section" v-if="activeSubmission.improvements?.length">
        <div class="pr-sec-title">改进建议</div>
        <div class="notebook">
          <div v-for="(imp, ii) in activeSubmission.improvements" :key="ii" class="notebook-imp">
            <div>
              <div class="notebook-imp-t">{{ imp.title }}</div>
              <div class="notebook-imp-d">{{ imp.detail }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export -->
      <div class="pr-section">
        <div class="export-row">
          <button class="exp-btn" @click="exportReport('pdf')">
            <svg viewBox="0 0 20 20" width="13" height="13"><path d="M5 3v14l5-3 5 3V3a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1z"/></svg>导出 PDF
          </button>
          <button class="exp-btn" @click="exportReport('excel')">
            <svg viewBox="0 0 20 20" width="13" height="13"><rect x="3" y="2" width="14" height="16" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/></svg>导出 Excel
          </button>
        </div>
      </div>
    </template>
  </div>
</aside>

</div><!-- end main-area -->
</div><!-- end app-shell -->
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

// ====== User ======
const USER_KEY = 'nanobot-webui.user'
const roleOptions = [
  { role: 'teacher', icon: '👨‍🏫', label: '教师' },
  { role: 'student', icon: '📚', label: '学生' },
  { role: 'researcher', icon: '🔬', label: '研究员' },
]
const user = ref(null)
const authMode = ref('login')
const loginRole = ref('teacher')
const loginUserId = ref('')
const loginError = ref('')
const loginLoading = ref(false)
function loadUser() { try { const r = localStorage.getItem(USER_KEY); if (!r) return null; const p = JSON.parse(r); return p?.role && p?.userId ? p : null } catch { return null } }
function saveUser(u) { localStorage.setItem(USER_KEY, JSON.stringify(u)) }
function clearUser() { localStorage.removeItem(USER_KEY) }
async function handleLogin() { const t = loginUserId.value.trim(); if (!loginRole.value || !t) return; loginError.value = ''; loginLoading.value = true; const u = { role: loginRole.value, userId: t }; saveUser(u); user.value = u; loginLoading.value = false }
function toggleAuthMode() { authMode.value = authMode.value === 'login' ? 'register' : 'login'; loginError.value = '' }
function handleLogout() { clearUser(); user.value = null; loginUserId.value = ''; loginRole.value = 'teacher'; authMode.value = 'login' }

// ====== Theme ======
const isDark = ref(false)
function toggleTheme() { isDark.value = !isDark.value; document.body.classList.toggle('dark', isDark.value) }
function goToLessonPlan() { window.location.href = '/' }
function goToAnalytics() { window.location.href = '/analytics.html' }

// ====== Helpers ======
let _qid = 0
function Q(objType, stem, maxScore, extra = {}) {
  return { id: ++_qid, label: '', objType, stem, maxScore, typeLabel: objType === 'choice' ? '选择题' : objType === 'tf' ? '判断题' : objType === 'fill' ? '填空题' : objType === 'short' ? '简答题' : '分析题', studentPick: '', studentAnswer: '', referenceAnswer: '', answerKey: '', options: null, graded: false, studentScore: 0, comment: '', ...extra }
}

// ====== Mock data ======
const MOCK = [
  { id: 's1', student: '陈小明', title: '《背影》课后练习', className: '八年级（3）班', date: '12.18', status: 'graded', score: 91,
    questions: [
      Q('choice', '《背影》的作者是谁？', 3, { options: [{ key:'A',text:'鲁迅' },{ key:'B',text:'朱自清' },{ key:'C',text:'老舍' },{ key:'D',text:'茅盾' }], answerKey:'B', studentPick:'B', graded:true, studentScore:3, comment:'正确' }),
      Q('tf', '"背影"在文中指父亲爬月台买橘子时留下的背影。', 4, { answerKey:'对', studentPick:'对', graded:true, studentScore:4, comment:'正确' }),
      Q('fill', '文中父亲为儿子买的食物是______。', 3, { answerKey:'橘子', studentPick:'橘子', graded:true, studentScore:3, comment:'正确' }),
      Q('short', '请概括《背影》一文的主要内容。', 10, { studentAnswer:'本文通过描写父亲在车站送别儿子时的背影，表现了父亲对儿子深沉的爱。作者通过对父亲爬过月台买橘子的细节描写，刻画了父亲朴实、真挚的父爱形象，读来令人动容。', referenceAnswer:'通过描写父亲在车站为儿子买橘子、爬过月台时留下的背影，表现了父亲对儿子深沉的爱以及儿子对父爱的感悟。', graded:true, studentScore:9, comment:'概括准确，能抓住核心情节与主题。' }),
      Q(null, '分析文中"背影"这个意象的多重作用。', 16, { studentAnswer:'背影是贯穿全文的行文线索，串联起离别前、离别时、离别后的完整叙事。同时，背影是父爱的视觉象征——父亲肥胖的身子、蹒跚的步伐，让无形的爱变得可见可感。最后，背影起到了情感凝结的作用，将作者复杂的情感浓缩在一个画面中，成为全文的情感爆发点。', referenceAnswer:'1. 线索作用——贯穿全文，串联叙事；2. 象征作用——象征父爱的深沉与无言；3. 情感凝结——将无形的爱意凝练为有形的画面，增强感染力。', graded:true, studentScore:14, comment:'分析透彻，三个维度都有深入展开，语言表达流畅。' }),
    ],
    rubric:[{ name:'基础知识', score:18, max:20 },{ name:'内容理解', score:18, max:20 },{ name:'分析深度', score:19, max:20 },{ name:'语言表达', score:17, max:20 },{ name:'文学鉴赏', score:14, max:15 },{ name:'创新思维', score:8, max:10 }],
    feedback:'整体完成质量优秀。客观题全对，基础知识扎实。主观题文本理解深入，能准确把握情感脉络并展开有层次的分析。"背影"意象分析尤为出色，三个维度层层递进，语言流畅有感染力。继续保持。',
    strengths:['客观题全对，基础扎实', '文本理解深入，能抓住核心情感', '分析层次分明，语言表达流畅'],
    improvements:[{ title:'①深化论证', detail:'在现有基础上可引入"以背写爱"的独特视角——作者为何选择"背影"而非正面描写，这一选择有何深意。' },{ title:'②术语积累', detail:'适当运用"细节描写""情感线索""以小见大""留白"等专业术语可进一步提升答案的学术性。' }],
  },
  { id: 's2', student: '李雨桐', title: '《背影》课后练习', className: '八年级（3）班', date: '12.18', status: 'graded', score: 68,
    questions: [
      Q('choice', '《背影》的作者是谁？', 3, { options: [{ key:'A',text:'鲁迅' },{ key:'B',text:'朱自清' },{ key:'C',text:'老舍' },{ key:'D',text:'茅盾' }], answerKey:'B', studentPick:'B', graded:true, studentScore:3, comment:'正确' }),
      Q('tf', '"背影"在文中指父亲爬月台买橘子时留下的背影。', 4, { answerKey:'对', studentPick:'错', graded:true, studentScore:0, comment:'判断有误，这是文中最核心的"背影"场景。' }),
      Q('fill', '文中父亲为儿子买的食物是______。', 3, { answerKey:'橘子', studentPick:'水果', graded:true, studentScore:0, comment:'表述不准确，应为"橘子"。' }),
      Q('short', '请概括《背影》一文的主要内容。', 10, { studentAnswer:'写父亲送作者去车站，给作者买橘子，作者看到父亲的背影很感动。', referenceAnswer:'通过描写父亲在车站为儿子买橘子、爬过月台时留下的背影，表现了父亲对儿子深沉的爱以及儿子对父爱的感悟。', graded:true, studentScore:5, comment:'基本内容正确，但过于简略，未提炼主题。' }),
      Q(null, '分析文中"背影"这个意象的多重作用。', 16, { studentAnswer:'背影代表了父亲的爱，是文章的中心。作者用背影来表达情感，让读者感动。', referenceAnswer:'1. 线索——贯穿全文；2. 象征——父爱的深沉与无言；3. 情感凝结——将无形的爱意凝练为有形的画面。', graded:true, studentScore:6, comment:'方向正确但分析过于笼统，未展开论述。' }),
    ],
    rubric:[{ name:'基础知识', score:12, max:20 },{ name:'内容理解', score:11, max:20 },{ name:'分析深度', score:8, max:20 },{ name:'语言表达', score:9, max:20 },{ name:'文学鉴赏', score:6, max:15 },{ name:'创新思维', score:3, max:10 }],
    feedback:'对课文有基本了解，但客观题存在审题不细的问题，判断题和填空题均有失分。主观题作答普遍偏简略，缺乏深入分析和展开。需重点提升答题深度和语言组织能力。',
    strengths:['选择题正确', '对课文基本内容有了解'],
    improvements:[{ title:'夯实客观题', detail:'判断题需仔细审题，填空题注意用词准确性，不能以笼统概念代替具体内容。' },{ title:'提升答题深度', detail:'10分以上简答题每个得分点需展开1-2句分析，结合原文语句作为论据。' },{ title:'构建答题框架', detail:'建议采用"观点提出→文本例证→分析阐述→小结回应"的四步答题结构。' }],
  },
  { id: 's3', student: '王浩然', title: '《背影》课后练习', className: '八年级（3）班', date: '12.19', status: 'pending', score: 0,
    questions: [
      Q('choice', '《背影》的作者是谁？', 3, { options: [{ key:'A',text:'鲁迅' },{ key:'B',text:'朱自清' },{ key:'C',text:'老舍' },{ key:'D',text:'茅盾' }], answerKey:'B', studentPick:'B' }),
      Q('tf', '"背影"在文中指父亲爬月台买橘子时留下的背影。', 4, { answerKey:'对', studentPick:'对' }),
      Q('fill', '文中父亲为儿子买的食物是______。', 3, { answerKey:'橘子', studentPick:'橘子' }),
      Q('short', '请概括《背影》一文的主要内容。', 10, { studentAnswer:'这篇课文写的是朱自清回忆父亲在浦口火车站送他的情景。父亲身体很胖却坚持穿过铁路去对面月台给儿子买橘子，作者看到父亲的背影非常感动。多年后收到父亲的信，又想起那个背影。', referenceAnswer:'通过描写父亲在车站为儿子买橘子、爬过月台时留下的背影，表现了父亲对儿子深沉的爱以及儿子对父爱的感悟。' }),
      Q(null, '分析文中"背影"这个意象的多重作用。', 16, { studentAnswer:'背影在文中多次出现，起到了贯穿全文的作用。父亲爬月台的背影是最重要的画面，是父亲形象的缩影。作者用背影而非正面写父亲，因为背影更能引起读者想象和共鸣。', referenceAnswer:'1. 线索——贯穿全文；2. 象征——父爱的深沉与无言；3. 情感凝结——将无形的爱意凝练为有形的画面。' }),
    ],
    rubric:[], feedback:'', strengths:[], improvements:[],
  },
  { id: 's4', student: '张思睿', title: '《背影》课后练习', className: '八年级（3）班', date: '12.19', status: 'graded', score: 84,
    questions: [
      Q('choice', '《背影》的作者是谁？', 3, { options: [{ key:'A',text:'鲁迅' },{ key:'B',text:'朱自清' },{ key:'C',text:'老舍' },{ key:'D',text:'茅盾' }], answerKey:'B', studentPick:'B', graded:true, studentScore:3, comment:'正确' }),
      Q('tf', '"背影"在文中指父亲爬月台买橘子时留下的背影。', 4, { answerKey:'对', studentPick:'对', graded:true, studentScore:4, comment:'正确' }),
      Q('fill', '文中父亲为儿子买的食物是______。', 3, { answerKey:'橘子', studentPick:'橘子', graded:true, studentScore:3, comment:'正确' }),
      Q('short', '请概括《背影》一文的主要内容。', 10, { studentAnswer:'本文记述了作者在浦口火车站与父亲分别的情景，重点描写父亲穿过铁路爬上月台为儿子买橘子的过程。通过"背影"细节表现父亲深沉内敛的爱和儿子的领悟。', referenceAnswer:'通过描写父亲在车站为儿子买橘子、爬过月台时留下的背影，表现了父亲对儿子深沉的爱以及儿子对父爱的感悟。', graded:true, studentScore:8, comment:'概括完整，层次清晰。' }),
      Q(null, '分析文中"背影"这个意象的多重作用。', 16, { studentAnswer:'背影是全文的叙事线索，串联起整个故事。背影是父爱的象征——父亲的体态和动作都是爱的具体展现。背影还起到情感凝结作用，将复杂情感浓缩在一个画面中，使文章具有强烈感染力。', referenceAnswer:'1. 线索——贯穿全文；2. 象征——父爱的深沉与无言；3. 情感凝结——将无形的爱意凝练为有形的画面。', graded:true, studentScore:12, comment:'分析全面，三个层面均涉及，有文本支撑。' }),
    ],
    rubric:[{ name:'基础知识', score:18, max:20 },{ name:'内容理解', score:17, max:20 },{ name:'分析深度', score:15, max:20 },{ name:'语言表达', score:14, max:20 },{ name:'文学鉴赏', score:12, max:15 },{ name:'创新思维', score:7, max:10 }],
    feedback:'表现出色，客观题全对，主观题层次分明、有据可依。"背影"意象分析能将形式与内容结合讨论。语言流畅清晰，继续保持。',
    strengths:['客观题全对', '答题结构清晰，层次分明', '能结合文本进行分析论证'],
    improvements:[{ title:'术语规范', detail:'可多使用"细节描写""情感线索""以小见大"等专业术语。' },{ title:'深度拓展', detail:'探讨"以背写爱"这一独特写作视角——为何选择背影。' }],
  },
  { id: 's5', student: '赵小雅', title: '《背影》课后练习', className: '八年级（3）班', date: '12.20', status: 'pending', score: 0,
    questions: [
      Q('choice', '《背影》的作者是谁？', 3, { options: [{ key:'A',text:'鲁迅' },{ key:'B',text:'朱自清' },{ key:'C',text:'老舍' },{ key:'D',text:'茅盾' }], answerKey:'B', studentPick:'A' }),
      Q('tf', '"背影"在文中指父亲爬月台买橘子时留下的背影。', 4, { answerKey:'对', studentPick:'错' }),
      Q('fill', '文中父亲为儿子买的食物是______。', 3, { answerKey:'橘子', studentPick:'苹果' }),
      Q('short', '请概括《背影》一文的主要内容。', 10, { studentAnswer:'这篇课文主要写了作者的父亲。父亲很爱他，在车站给他买橘子。作者看到父亲的背影感觉很心酸。后来作者也明白了父亲的爱。', referenceAnswer:'通过描写父亲在车站为儿子买橘子、爬过月台时留下的背影，表现了父亲对儿子深沉的爱以及儿子对父爱的感悟。' }),
    ],
    rubric:[], feedback:'', strengths:[], improvements:[],
  },
]

const submissions = ref(JSON.parse(JSON.stringify(MOCK)))
const activeId = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const questionType = ref('all')
const gradingInProgress = ref(false)
const gradeOptions = reactive({ detailed: true, rubric: true, suggestions: true })

const activeSubmission = computed(() => submissions.value.find(s => s.id === activeId.value) || null)
const displayQuestions = computed(() => {
  if (!activeSubmission.value) return []
  let qs = activeSubmission.value.questions
  if (questionType.value === 'subjective') qs = qs.filter(q => !q.objType)
  if (questionType.value === 'objective') qs = qs.filter(q => q.objType)
  return qs
})
const filteredSubmissions = computed(() => {
  let list = submissions.value
  if (statusFilter.value === 'pending') list = list.filter(s => s.status === 'pending')
  if (statusFilter.value === 'graded') list = list.filter(s => s.status === 'graded')
  if (searchQuery.value.trim()) { const q = searchQuery.value.trim().toLowerCase(); list = list.filter(s => s.student.toLowerCase().includes(q) || s.title.toLowerCase().includes(q)) }
  return list
})
const ungradedCount = computed(() => submissions.value.filter(s => s.status === 'pending').length)
const gradedCount = computed(() => submissions.value.filter(s => s.status === 'graded').length)
const avgScore = computed(() => { const g = submissions.value.filter(s => s.status === 'graded'); return g.length ? Math.round(g.reduce((a,b) => a + b.score, 0) / g.length) : '--' })
const scoreWord = computed(() => { const s = activeSubmission.value?.score || 0; if (s >= 90) return '优秀'; if (s >= 80) return '良好'; if (s >= 70) return '中等'; if (s >= 60) return '及格'; return '待提升' })
const scoreLevel = computed(() => { const s = activeSubmission.value?.score || 0; if (s >= 90) return 'lv-a'; if (s >= 80) return 'lv-b'; if (s >= 70) return 'lv-c'; if (s >= 60) return 'lv-d'; return 'lv-f' })

// Histogram data
const classAvg = 82; const classMax = 96; const classMin = 58
const scoreDist = computed(() => {
  const ranges = ['0-59','60-69','70-79','80-89','90-100']
  const counts = [1, 3, 7, 16, 9] // mock distribution for 36 students
  const maxCount = Math.max(...counts)
  const curScore = activeSubmission.value?.score || 0
  return ranges.map((r, i) => {
    const [lo, hi] = r.split('-').map(Number)
    return { range: r, count: counts[i], pct: Math.round((counts[i] / maxCount) * 100), isCurrent: curScore >= lo && curScore <= hi }
  })
})

// ====== Radar chart ======
const radarData = computed(() => {
  const rubric = activeSubmission.value?.rubric
  if (!rubric?.length) return null
  const n = rubric.length
  const cx = 110, cy = 110, maxR = 70
  const levels = [0.25, 0.5, 0.75, 1.0]
  const rings = levels.map(lvl => {
    const pts = []
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + (2 * Math.PI * i) / n
      pts.push({ x: +(cx + maxR * lvl * Math.cos(a)).toFixed(1), y: +(cy + maxR * lvl * Math.sin(a)).toFixed(1) })
    }
    return pts.map(p => p.x + ',' + p.y).join(' ')
  })
  const axes = rubric.map((_, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n
    return {
      x2: +(cx + maxR * Math.cos(a)).toFixed(1),
      y2: +(cy + maxR * Math.sin(a)).toFixed(1),
      lx: +(cx + (maxR + 22) * Math.cos(a)).toFixed(1),
      ly: +(cy + (maxR + 22) * Math.sin(a)).toFixed(1),
    }
  })
  const dataPts = rubric.map((d, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n
    const r = (d.score / d.max) * maxR
    return (+(cx + r * Math.cos(a)).toFixed(1)) + ',' + (+(cy + r * Math.sin(a)).toFixed(1))
  }).join(' ')
  const dots = rubric.map((d, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n
    const r = (d.score / d.max) * maxR
    return { x: +(cx + r * Math.cos(a)).toFixed(1), y: +(cy + r * Math.sin(a)).toFixed(1), score: d.score, max: d.max }
  })
  return { rings, axes, dataPts, dots, dims: rubric }
})

// ====== Panel collapse ======
const panelCollapsed = reactive({ left: false, right: false })

// ====== Actions ======
function selectSubmission(sub) { activeId.value = sub.id; questionType.value = 'all' }
function autoGradeObj(q) {
  if (q.objType === 'choice' || q.objType === 'tf') return q.studentPick === q.answerKey ? q.maxScore : 0
  if (q.objType === 'fill') { const a = (q.studentPick||'').trim(), b = (q.answerKey||'').trim(); if (!a) return 0; if (a === b) return q.maxScore; if (b.includes(a)||a.includes(b)) return Math.ceil(q.maxScore*0.5); return 0 }
  return 0
}
function autoGradeSub(q) { const l = (q.studentAnswer||'').length; if (l > 150) return { score: Math.round(q.maxScore*0.9), comment:'回答详细，条理清晰。' }; if (l > 80) return { score: Math.round(q.maxScore*0.72), comment:'回答基本完整，可进一步展开。' }; if (l > 30) return { score: Math.round(q.maxScore*0.5), comment:'回答偏简略，建议展开论述。' }; return { score: Math.round(q.maxScore*0.3), comment:'回答过于简略，需充分展开。' } }

function gradeSubmission(sub) {
  gradingInProgress.value = true
  setTimeout(() => {
    const idx = submissions.value.findIndex(s => s.id === sub.id)
    if (idx === -1) { gradingInProgress.value = false; return }
    const g = JSON.parse(JSON.stringify(sub)); g.status = 'graded'
    g.questions.forEach(q => { q.graded = true; if (q.objType) { q.studentScore = autoGradeObj(q); q.comment = q.studentScore === q.maxScore ? '正确' : q.studentScore > 0 ? '部分正确' : '错误' } else { const r = autoGradeSub(q); q.studentScore = r.score; q.comment = r.comment } })
    const tm = g.questions.reduce((a,q)=>a+q.maxScore,0); const ts = g.questions.reduce((a,q)=>a+q.studentScore,0); g.score = Math.round((ts/tm)*100)
    g.rubric = [
      { name:'基础知识', score:Math.round(g.questions.filter(q=>q.objType).reduce((a,q)=>a+q.studentScore,0)/Math.max(1,g.questions.filter(q=>q.objType).reduce((a,q)=>a+q.maxScore,0))*20)||Math.round(14+Math.random()*6), max:20 },
      { name:'内容理解', score:Math.round(12+Math.random()*8), max:20 },{ name:'分析深度', score:Math.round(10+Math.random()*10), max:20 },{ name:'语言表达', score:Math.round(10+Math.random()*10), max:20 },
      { name:'文学鉴赏', score:Math.round(6+Math.random()*9), max:15 },{ name:'创新思维', score:Math.round(4+Math.random()*6), max:10 },
    ]
    g.feedback = `本次作业完成质量${g.score>=85?'优秀':g.score>=70?'良好':'一般'}。客观题${g.questions.filter(q=>q.objType&&q.studentScore===q.maxScore).length}/${g.questions.filter(q=>q.objType).length}道全对，主观题${g.score>=80?'分析到位、表述清晰':g.score>=70?'基本理解正确但深度有待加强':'需要提升分析深度和语言组织'}。`
    g.strengths = g.score>=80 ? ['客观题正确率高','对文本有较深理解','作答思路清晰'] : ['能完成全部题目','对课文有基本了解']
    g.improvements = g.score>=80 ? [{ title:'精益求精', detail:'尝试从更多维度展开，如社会背景、作者生平，使论述更加立体。' },{ title:'术语规范', detail:'多使用"细节描写""情感线索""以小见大"等专业术语。' }] : [{ title:'夯实基础', detail:'客观题需加强记忆和理解，避免粗心失分。' },{ title:'提升分析深度', detail:'主观题每道至少展开3-4句，采用"观点+原文+分析"的结构。' }]
    submissions.value.splice(idx,1,g); gradingInProgress.value = false
  }, 1600)
}

function batchGradeAll() {
  const pending = submissions.value.filter(s => s.status === 'pending'); if (!pending.length) return
  gradingInProgress.value = true; let i = 0
  const go = () => { if (i >= pending.length) { gradingInProgress.value = false; return }; const idx = submissions.value.findIndex(s => s.id === pending[i].id); if (idx !== -1) { const g = JSON.parse(JSON.stringify(submissions.value[idx])); g.status = 'graded'; g.questions.forEach(q => { q.graded = true; if (q.objType) { q.studentScore = autoGradeObj(q); q.comment = q.studentScore === q.maxScore ? '正确' : q.studentScore > 0 ? '部分正确' : '错误' } else { const r = autoGradeSub(q); q.studentScore = r.score; q.comment = r.comment } }); const tm = g.questions.reduce((a,q)=>a+q.maxScore,0); g.score = Math.round((g.questions.reduce((a,q)=>a+q.studentScore,0)/tm)*100); g.rubric = [{ name:'基础知识', score:Math.round(10+Math.random()*10), max:20 },{ name:'内容理解', score:Math.round(10+Math.random()*10), max:20 },{ name:'分析深度', score:Math.round(8+Math.random()*12), max:20 },{ name:'语言表达', score:Math.round(8+Math.random()*12), max:20 },{ name:'文学鉴赏', score:Math.round(5+Math.random()*10), max:15 },{ name:'创新思维', score:Math.round(3+Math.random()*7), max:10 }]; g.feedback = '已完成批改。'; g.strengths = ['完成了全部题目']; g.improvements = [{ title:'继续努力', detail:'加强日常练习和阅读积累。' }]; submissions.value.splice(idx,1,g) }; i++; setTimeout(go,250) }; go()
}

function exportReport(f) { alert(`导出 ${f.toUpperCase()}（Demo 模式暂不可用）`) }

onMounted(() => { const saved = loadUser(); if (saved) user.value = saved; else { user.value = { role:'teacher', userId:'demo' }; saveUser(user.value) }; activeId.value = 's1' })
</script>

<style>
/* ====== Theme ====== */
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255,255,255,0.55);
  --bg-card-hover: rgba(255,255,255,0.86);
  --bg-nav: rgba(255,255,255,0.82);
  --bg-input: rgba(255,255,255,0.50);
  --bg-tag: rgba(107,93,240,0.05);
  --bg-soft: rgba(107,93,240,0.03);
  --accent: #6B5DF0;
  --accent-light: rgba(107,93,240,0.20);
  --accent-soft: rgba(107,93,240,0.07);
  --accent-glow: rgba(107,93,240,0.16);
  --accent-bright: rgba(107,93,240,0.32);
  --accent-deep: #5A4AD0;
  --accent-dim: rgba(107,93,240,0.04);
  --border-light: rgba(0,0,0,0.08);
  --border-medium: rgba(0,0,0,0.14);
  --border-active: #6B5DF0;
  --border-active-glow: rgba(107,93,240,0.38);
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0,0,0,0.06);
  --panel-radius: 16px;
  --trans: 0.35s cubic-bezier(0.22,0.08,0.22,1);
}
body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18,19,34,0.50);
  --bg-card-hover: rgba(24,25,44,0.72);
  --bg-nav: rgba(10,11,22,0.88);
  --bg-input: rgba(18,16,36,0.50);
  --bg-tag: rgba(123,92,255,0.06);
  --bg-soft: rgba(139,112,255,0.04);
  --accent: #8B70FF;
  --accent-light: rgba(139,112,255,0.24);
  --accent-soft: rgba(139,112,255,0.09);
  --accent-glow: rgba(139,112,255,0.22);
  --accent-bright: rgba(139,112,255,0.40);
  --accent-deep: #6B50E0;
  --accent-dim: rgba(139,112,255,0.05);
  --border-light: rgba(255,255,255,0.08);
  --border-medium: rgba(255,255,255,0.16);
  --border-active: #8B70FF;
  --border-active-glow: rgba(139,112,255,0.48);
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.07);
}

* { margin:0; padding:0; box-sizing:border-box; }
html { font-size: 15px; }
body {
  font-family: 'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  color: var(--text-primary); background: var(--bg-root);
  -webkit-font-smoothing: antialiased; min-height: 100vh;
  transition: background 0.4s, color 0.4s; overflow: hidden;
}

/* ====== Login ====== */
.login-screen { display:flex; align-items:center; justify-content:center; height:100vh; background:var(--bg-root); }
.login-card { width:380px; background:var(--bg-card); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); border:1.5px solid var(--border-medium); border-radius:20px; padding:36px 28px; box-shadow:0 8px 32px rgba(0,0,0,0.06); }
.login-header { text-align:center; margin-bottom:24px; }
.login-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.6rem; font-weight:700; color:var(--accent); display:flex; align-items:center; justify-content:center; gap:6px; }
.login-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.login-subtitle { font-size:0.82rem; color:var(--text-muted); margin-top:4px; }
.login-roles { display:flex; gap:8px; margin-bottom:16px; justify-content:center; }
.role-btn { flex:1; padding:10px 8px; border-radius:12px; border:1.5px solid var(--border-light); background:transparent; cursor:pointer; transition:all 0.25s; text-align:center; }
.role-btn:hover { border-color:var(--border-medium); }
.role-btn.active { border-color:var(--accent); background:var(--accent-soft); box-shadow:0 0 12px var(--accent-soft); }
.role-icon { font-size:1.2rem; display:block; margin-bottom:2px; }
.role-label { font-size:0.72rem; color:var(--text-secondary); }
.login-input { width:100%; padding:12px; border-radius:12px; border:1.5px solid var(--border-light); background:var(--bg-input); font-size:0.88rem; color:var(--text-primary); outline:none; transition:all 0.25s; text-align:center; }
.login-input:focus { border-color:var(--border-active); box-shadow:0 0 20px var(--accent-glow); }
.login-error { color:#E07B30; font-size:0.76rem; text-align:center; margin-top:8px; }
.login-submit { width:100%; padding:11px; border-radius:12px; background:var(--accent); color:#fff; border:none; font-weight:600; font-size:0.88rem; cursor:pointer; margin-top:12px; transition:all 0.25s; }
.login-submit:hover:not(:disabled) { box-shadow:0 0 20px var(--accent-glow); }
.login-submit:disabled { opacity:0.45; cursor:not-allowed; }
.login-toggle { width:100%; padding:8px; border-radius:12px; background:transparent; border:none; color:var(--text-muted); font-size:0.74rem; cursor:pointer; margin-top:6px; }
.login-toggle:hover { color:var(--accent); }

/* ====== Layout ====== */
.app-shell { display:flex; flex-direction:column; height:100vh; width:100%; overflow:hidden; padding:6px 10px; gap:6px; min-width:1100px; }

/* ====== TOP NAV ====== */
.top-nav {
  flex-shrink:0; height:50px; display:flex; align-items:center; justify-content:space-between;
  background:var(--bg-nav); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  border:1.8px solid var(--border-medium); border-radius:var(--panel-radius);
  padding:0 24px; position:relative;
  box-shadow:0 0 16px var(--accent-soft);
}
.top-nav::before { content:''; position:absolute; pointer-events:none; top:-1px; left:28px; right:28px; height:1.5px; border-radius:1px; background:linear-gradient(90deg,transparent,var(--accent-light),transparent); opacity:0.55; }
.nav-left { display:flex; align-items:center; gap:20px; }
.nav-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.4rem; font-weight:700; color:var(--accent); letter-spacing:-0.01em; display:flex; align-items:center; gap:7px; }
.nav-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); animation:dotPulse 2s ease-in-out infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.6);opacity:0.6} }
.nav-center { display:flex; align-items:center; gap:3px; }
.nav-tab { padding:6px 14px; border-radius:13px; font-size:0.82rem; font-weight:500; color:var(--text-secondary); cursor:pointer; transition:all 0.25s; border:1.5px solid transparent; white-space:nowrap; }
.nav-tab:hover { color:var(--text-primary); background:var(--bg-tag); }
.nav-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 14px var(--accent-glow); }
.nav-right { display:flex; align-items:center; gap:8px; }
.nav-icon { width:32px; height:32px; border-radius:50%; border:1.5px solid var(--border-medium); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--text-secondary); transition:all 0.25s; flex-shrink:0; }
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.nav-icon:hover { color:var(--accent); border-color:var(--border-active); box-shadow:0 0 16px var(--accent-glow); }
.nav-avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,#7B5CFF,#A78BFA); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:0.74rem; cursor:pointer; border:2px solid transparent; box-shadow:0 0 16px var(--accent-glow); transition:all 0.25s; }
.nav-avatar:hover { transform:scale(1.06); }
.conn-status { display:flex; align-items:center; gap:5px; padding:4px 10px; border-radius:12px; font-size:0.72rem; color:var(--text-muted); border:1px solid var(--border-light); background:var(--bg-card); cursor:default; }
.conn-dot { width:7px; height:7px; border-radius:50%; background:var(--text-muted); flex-shrink:0; }
.conn-label { font-weight:500; }

/* ====== MAIN AREA ====== */
.main-area { flex:1; min-height:0; display:flex; gap:8px; }

/* ====== UNIVERSAL PANEL WITH PURPLE GLOW STRIPS ====== */
.panel {
  background:var(--bg-card); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border:1.8px solid var(--border-active); border-radius:var(--panel-radius);
  position:relative; overflow:hidden; display:flex; flex-direction:column;
  box-shadow:0 0 20px var(--accent-glow),0 0 44px var(--accent-soft);
}
.panel-strip { position:absolute; pointer-events:none; z-index:1; }
.panel-strip.top, .panel-strip.bottom { left:-100%; width:100%; height:1.5px; background:linear-gradient(90deg,transparent,#C4B0FF,#7B5CFF,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
.panel-strip.right, .panel-strip.left { top:-100%; width:1.5px; height:100%; background:linear-gradient(180deg,transparent,#C4B0FF,#A78BFA,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
.panel-strip.top    { top:0;    animation:scanH 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); }
.panel-strip.right  { right:0;  animation:scanV 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:0.8s; }
.panel-strip.bottom { bottom:0; animation:scanHRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:1.6s; }
.panel-strip.left   { left:0;   animation:scanVRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:2.4s; }
@keyframes scanH    { 0%{left:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:100%;opacity:0} }
@keyframes scanHRev { 0%{left:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:-100%;opacity:0} }
@keyframes scanV    { 0%{top:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:100%;opacity:0} }
@keyframes scanVRev { 0%{top:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:-100%;opacity:0} }

/* Panel sizing */
.panel-left { width:278px; min-width:250px; flex-shrink:0; }
.panel-center { flex:1; min-width:0; }
.panel-right { width:330px; min-width:290px; flex-shrink:0; }

/* ====== LEFT PANEL ====== */
.pl-header { flex-shrink:0; display:flex; align-items:center; justify-content:space-between; padding:14px 14px 0; position:relative; z-index:2; }
.pl-title { font-size:0.84rem; font-weight:700; color:var(--text-primary); }
.pl-badge { font-size:0.66rem; color:var(--accent); background:var(--accent-soft); padding:2px 10px; border-radius:8px; font-weight:600; }
.pl-search { display:flex; align-items:center; gap:6px; margin:10px 14px; padding:7px 10px; background:var(--bg-input); border:1.8px solid var(--border-light); border-radius:10px; transition:all 0.25s; position:relative; z-index:2; }
.pl-search:focus-within { border-color:var(--border-active); box-shadow:0 0 12px var(--accent-soft); }
.pl-search-icon { width:13px; height:13px; stroke:var(--text-muted); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0; }
.pl-search input { border:none; outline:none; background:transparent; font-family:inherit; font-size:0.72rem; color:var(--text-primary); width:100%; }
.pl-search input::placeholder { color:var(--text-muted); }
.pl-filters { display:flex; gap:5px; padding:0 14px 10px; position:relative; z-index:2; }
.pl-chip { padding:4px 12px; border-radius:16px; font-size:0.66rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.2s; border:1.5px solid transparent; }
.pl-chip:hover { color:var(--text-secondary); background:var(--bg-tag); }
.pl-chip.on { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); }

.pl-list { flex:1; overflow-y:auto; padding:0 10px; position:relative; z-index:2; }
.pl-list::-webkit-scrollbar { width:3px; }
.pl-list::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
.submission-row {
  display:flex; align-items:center; gap:8px; padding:9px 10px; border-radius:10px;
  cursor:pointer; transition:all 0.2s; border:1.5px solid transparent; position:relative; overflow:hidden;
  animation: fadeIn 0.35s ease both;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
.submission-row:hover { background:var(--bg-card-hover); }
.submission-row.active { border-color:var(--accent-light); background:var(--accent-soft); box-shadow:0 0 12px var(--accent-soft); }
.submission-row.active::after { content:''; position:absolute; inset:0; pointer-events:none; background:linear-gradient(90deg,transparent,rgba(180,160,240,0.10),transparent); background-size:200% 100%; animation:shimmerSweep 2s ease-in-out infinite; }
@keyframes shimmerSweep { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.sr-rank { font-size:0.64rem; color:var(--text-muted); width:16px; text-align:center; flex-shrink:0; }
.sr-avatar { width:30px; height:30px; border-radius:8px; background:var(--accent-soft); display:flex; align-items:center; justify-content:center; flex-shrink:0; color:var(--accent); font-weight:700; font-size:0.68rem; }
.sr-body { flex:1; min-width:0; }
.sr-name { font-size:0.76rem; font-weight:600; color:var(--text-primary); }
.sr-desc { font-size:0.64rem; color:var(--text-muted); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-tail { flex-shrink:0; }
.sr-score { font-size:0.82rem; font-weight:700; color:var(--accent); }
.sr-dot { display:block; width:6px; height:6px; border-radius:50%; background:var(--text-muted); opacity:0.45; }
.pl-empty { text-align:center; padding:32px 0; color:var(--text-muted); font-size:0.72rem; }

.pl-footer { flex-shrink:0; padding:10px 14px 14px; position:relative; z-index:2; }
.pl-stats-row { display:flex; gap:8px; margin-bottom:10px; }
.pl-stat {
  flex:1; text-align:center; padding:12px 6px; border-radius:14px;
  background:rgba(245,242,255,0.65);
  backdrop-filter:blur(20px) saturate(1.2);
  -webkit-backdrop-filter:blur(20px) saturate(1.2);
  border:1px solid rgba(180,160,240,0.30);
  box-shadow:0 2px 16px rgba(139,112,255,0.08), 0 0 0 1px rgba(200,180,255,0.15);
  transition:all 0.25s;
}
body.dark .pl-stat {
  background:rgba(160,140,220,0.08);
  border:1px solid rgba(160,140,220,0.15);
  box-shadow:0 2px 16px rgba(0,0,0,0.2), 0 0 0 1px rgba(160,140,220,0.06);
}
.pl-stat:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(139,112,255,0.14), 0 0 0 1px rgba(180,150,240,0.25); }
.pl-stat-val { font-size:1.05rem; font-weight:700; color:var(--accent); letter-spacing:-0.02em; }
.pl-stat-lbl { font-size:0.62rem; color:var(--text-muted); margin-top:2px; font-weight:500; }
.batch-btn {
  width:100%; padding:11px; border-radius:14px;
  border:1px solid rgba(180,160,240,0.28);
  background:rgba(245,242,255,0.60);
  backdrop-filter:blur(20px) saturate(1.2);
  -webkit-backdrop-filter:blur(20px) saturate(1.2);
  color:var(--accent); font-size:0.76rem; font-weight:600;
  cursor:pointer; transition:all 0.25s; font-family:inherit;
  box-shadow:0 2px 16px rgba(139,112,255,0.08), 0 0 0 1px rgba(200,180,255,0.12);
}
body.dark .batch-btn {
  background:rgba(160,140,220,0.07);
  border:1px solid rgba(160,140,220,0.14);
  box-shadow:0 2px 16px rgba(0,0,0,0.2), 0 0 0 1px rgba(160,140,220,0.05);
}
.batch-btn:hover:not(:disabled) {
  background:rgba(250,248,255,0.75);
  border-color:rgba(160,130,230,0.40);
  box-shadow:0 6px 24px rgba(139,112,255,0.16), 0 0 0 1px rgba(180,150,240,0.28);
  transform:translateY(-1px);
}
.batch-btn:disabled { opacity:0.25; cursor:not-allowed; box-shadow:none; }

/* ====== CENTER PANEL ====== */
.center-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:10px; position:relative; z-index:3; }
.empty-icon-wrap { width:52px; height:52px; border-radius:14px; background:var(--bg-tag); display:flex; align-items:center; justify-content:center; }
.empty-icon-wrap svg { width:24px; height:24px; stroke:var(--text-muted); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }
.empty-title { font-size:0.84rem; font-weight:600; color:var(--text-secondary); }
.empty-desc { font-size:0.72rem; color:var(--text-muted); }

.center-scroll { flex:1; overflow-y:auto; padding:20px 24px 24px; position:relative; z-index:3; }
.center-scroll::-webkit-scrollbar { width:4px; }
.center-scroll::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

/* Student bar */
.student-bar { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--divider); }
.sb-left { display:flex; align-items:center; gap:10px; }
.sb-avatar {
  width:38px; height:38px; border-radius:50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-weight:700; font-size:0.82rem; flex-shrink:0;
  box-shadow: 0 2px 8px rgba(107,93,240,0.25);
}
.sb-name { font-size:0.88rem; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:8px; letter-spacing:0.02em; }
.sb-class { font-size:0.64rem; font-weight:500; color:var(--text-muted); background:var(--bg-tag); padding:3px 10px; border-radius:10px; }
.sb-meta { font-size:0.72rem; color:var(--text-muted); margin-top:2px; font-weight:500; }
.sb-status { font-size:0.68rem; font-weight:600; padding:4px 12px; border-radius:8px; border:1px solid var(--border-light); color:var(--text-muted); }
.sb-status.done { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); }

/* Question tabs */
.q-tabs { display:flex; align-items:center; gap:4px; margin-bottom:14px; }
.q-tab { padding:6px 15px; border-radius:18px; font-size:0.73rem; font-weight:500; color:var(--text-muted); cursor:pointer; transition:all 0.2s; border:1.5px solid transparent; background:transparent; }
.q-tab:hover { color:var(--text-secondary); background:var(--bg-tag); }
.q-tab.on { color:var(--accent); background:var(--accent-soft); border-color:var(--accent-light); box-shadow:0 0 8px var(--accent-soft); }
.q-tab-summary { margin-left:auto; font-size:0.66rem; color:var(--text-muted); }

/* Question cards */
.q-list { display:flex; flex-direction:column; gap:14px; }
.q-card {
  position:relative; border-radius:10px;
  background:var(--bg-card);
  border:2px solid var(--accent);
  transition:all 0.2s;
}
.q-card::before {
  content:''; position:absolute; z-index:2; pointer-events:none;
  top:5px; left:5px; width:20px; height:20px;
  border-top:2px solid var(--accent);
  border-left:2px solid var(--accent);
  border-radius:2px 0 0 0;
  opacity:0; transition:opacity 0.25s;
}
.q-card::after {
  content:''; position:absolute; z-index:2; pointer-events:none;
  top:5px; right:5px; width:20px; height:20px;
  border-top:2px solid var(--accent);
  border-right:2px solid var(--accent);
  border-radius:0 2px 0 0;
  opacity:0; transition:opacity 0.25s;
}
.q-inner::before {
  content:''; position:absolute; z-index:2; pointer-events:none;
  bottom:5px; left:5px; width:20px; height:20px;
  border-bottom:2px solid var(--accent);
  border-left:2px solid var(--accent);
  border-radius:0 0 0 2px;
  opacity:0; transition:opacity 0.25s;
}
.q-inner::after {
  content:''; position:absolute; z-index:2; pointer-events:none;
  bottom:5px; right:5px; width:20px; height:20px;
  border-bottom:2px solid var(--accent);
  border-right:2px solid var(--accent);
  border-radius:0 0 2px 0;
  opacity:0; transition:opacity 0.25s;
}
.q-card:hover { border-color:transparent; }
.q-card:hover::before, .q-card:hover::after,
.q-card:hover .q-inner::before, .q-card:hover .q-inner::after { opacity:1; }
.q-card .q-accent { display:none; }

.q-inner { padding:16px 16px 16px 20px; position:relative; z-index:1; }

.q-top { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.q-idx {
  width:20px; height:20px; border-radius:5px; background:var(--accent-soft);
  color:var(--accent); font-size:0.66rem; font-weight:700;
  display:flex; align-items:center; justify-content:center;
}
.q-kind { font-size:0.66rem; color:var(--text-muted); }
.q-pts { font-size:0.66rem; color:var(--text-muted); margin-left:auto; font-weight:500; }

.q-stem { font-size:0.84rem; color:var(--text-primary); line-height:1.7; margin-bottom:8px; }

/* Options */
.q-opts { display:flex;flex-direction:column;gap:4px;margin-bottom:8px; }
.q-opt { display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;border:1.5px solid var(--border-light);font-size:0.78rem;transition:all 0.15s; }
.q-opt.picked { border-color:var(--accent-light); background:var(--accent-dim); }
.q-opt.correct { border-color:var(--accent); background:var(--accent-soft); }
.q-opt.wrong { border-color:rgba(224,123,48,0.22); background:rgba(224,123,48,0.03); }
.q-opt-letter { width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border-medium);display:flex;align-items:center;justify-content:center;font-size:0.70rem;font-weight:600;color:var(--text-secondary);flex-shrink:0; }
.q-opt.picked .q-opt-letter { border-color:var(--accent);color:var(--accent);background:var(--accent-soft); }
.q-opt.correct .q-opt-letter { border-color:var(--accent);color:#fff;background:var(--accent); }
.q-opt.wrong .q-opt-letter { border-color:#E07B30;color:#E07B30;background:rgba(224,123,48,0.06); }
.q-opt-text { flex:1;color:var(--text-secondary); }

/* TF / Fill */
.q-tf, .q-fill { display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap; }
.q-tf-label, .q-fill-label { font-size:0.62rem;font-weight:700;letter-spacing:0.05em;color:var(--text-muted);text-transform:uppercase; }
.q-tf-val, .q-fill-val { font-size:0.80rem;font-weight:600;padding:4px 12px;border-radius:6px;background:var(--bg-tag); }
.q-tf-val.is-correct, .q-fill-val.is-correct { color:var(--accent); }
.q-tf-val.is-wrong, .q-fill-val.is-wrong { color:#E07B30; }
.q-fill-val { font-family:'JetBrains Mono',monospace; }
.q-tf-ref, .q-fill-ref { font-size:0.70rem;color:var(--accent-deep); }

/* Subjective answer */
.q-answer-area { margin-bottom:8px; display:flex; flex-direction:column; gap:8px; }
.q-answer-box {
  padding:12px 14px; border-radius:10px;
  border:1.5px solid var(--accent); background:var(--bg-card);
}
.q-answer-label {
  font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--accent);
  margin-bottom:6px; display:inline-block;
  border-bottom:1px solid var(--accent-soft); padding-bottom:3px;
}
.q-answer-text { font-size:0.82rem; color:var(--text-primary); line-height:1.8; margin:0; }
.q-ref-box {
  padding:12px 14px; border-radius:10px;
  border:1.5px solid var(--accent); background:var(--accent-dim);
}
.q-ref-label {
  font-size:0.62rem; font-weight:700; letter-spacing:0.06em; color:var(--accent-deep);
  margin-bottom:6px; display:inline-block;
  border-bottom:1px solid var(--accent-light); padding-bottom:3px;
}
.q-ref-text { font-size:0.82rem; color:var(--accent-deep); line-height:1.8; margin:0; }

/* Footer */
.q-footer { display:flex;align-items:center;gap:8px;padding-top:10px;border-top:1px solid var(--divider);margin-top:4px; }
.q-footer-score { font-size:0.70rem;font-weight:700;padding:2px 8px;border-radius:5px;flex-shrink:0; }
.q-footer-score.full { color:var(--accent);background:var(--accent-soft); }
.q-footer-score.half { color:var(--accent-deep);background:var(--accent-dim); }
.q-footer-score.zero { color:#E07B30;background:rgba(224,123,48,0.05); }
.q-footer-note { font-size:0.68rem;color:var(--text-muted); }
.q-empty { text-align:center;padding:32px 0;color:var(--text-muted);font-size:0.74rem; }

/* ====== RIGHT PANEL ====== */
.pr-empty { display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:10px;color:var(--text-muted);position:relative;z-index:3; }
.pr-empty svg { stroke:var(--text-muted);fill:none;stroke-width:1.5; }
.pr-empty p { font-size:0.72rem;text-align:center;line-height:1.6; }

.pr-scroll { flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:16px;position:relative;z-index:3; }
.pr-scroll::-webkit-scrollbar { width:3px; }
.pr-scroll::-webkit-scrollbar-thumb { background:var(--border-light);border-radius:2px; }

.pr-section { }
.pr-sec-title {
  font-size:0.66rem; font-weight:700; letter-spacing:0.05em;
  color:var(--text-muted); margin-bottom:10px; text-transform:uppercase;
  display:flex; align-items:center; gap:10px;
}
.pr-sec-title::after {
  content:''; flex:1; height:1px;
  background: var(--divider);
}

/* Score hero */

/* Dimensions */
.dim-row { display:flex; align-items:center; gap:10px; margin-bottom:9px; }
.dim-name { font-size:0.70rem; color:var(--text-secondary); width:56px; flex-shrink:0; }
.dim-bar { flex:1; height:6px; background:var(--border-light); border-radius:4px; overflow:hidden; }
.dim-bar i { display:block; height:100%; background: linear-gradient(90deg, var(--accent-deep), var(--accent)); border-radius:4px; transition: width 0.8s var(--trans); box-shadow: 0 0 8px var(--accent-soft); }
.dim-val { font-size:0.70rem; font-weight:600; color:var(--text-primary); width:44px; text-align:right; flex-shrink:0; }
.dim-val small { font-size:0.60rem; color:var(--text-muted); font-weight:400; }

/* Histogram */
.histogram {
	  display:flex; align-items:flex-end; gap:14px; height:148px; padding:0 8px;
	  position:relative;
	  background:
	    repeating-linear-gradient(to bottom, transparent, transparent 23%, var(--divider) 23%, var(--divider) 25%, transparent 25%, transparent 48%, var(--divider) 48%, var(--divider) 50%, transparent 50%, transparent 73%, var(--divider) 73%, var(--divider) 75%, transparent 75%);
	}
.hist-col { flex:1; display:flex; flex-direction:column; align-items:center; gap:5px; z-index:1; min-width:0; }
.hist-bar-wrap { flex:1; width:100%; display:flex; flex-direction:column; align-items:center; }
.hist-bar-spacer { min-height:0; width:100%; }
.hist-bar {
	  width:64%; max-width:48px; min-height:6px;
	  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-light) 90%);
	  border-radius:6px 6px 3px 3px;
	  transition: all 0.6s var(--trans);
	  box-shadow: 0 -1px 8px var(--accent-soft);
	}
.hist-bar.highlight {
	  background: linear-gradient(180deg, var(--accent) 0%, var(--accent) 100%);
	  box-shadow: 0 0 16px var(--accent-glow), 0 -2px 10px var(--accent);
	}
.hist-label { font-size:0.62rem; color:var(--text-muted); font-weight:500; white-space:nowrap; }
.hist-count { font-size:0.64rem; font-weight:700; color:var(--text-secondary); white-space:nowrap; }
.hist-legend { text-align:center; margin-top:8px; }
.hist-avg { font-size:0.66rem; color:var(--text-muted); }

/* Feedback */
.feedback-card { padding:12px 14px;border-radius:10px;background:var(--bg-tag);border:1px solid var(--border-light); }
.feedback-card p { font-size:0.76rem;color:var(--text-secondary);line-height:1.8; }

/* Strengths */
.plus-item { font-size:0.74rem;color:var(--text-secondary);padding:8px 12px;background:var(--bg-soft);border-radius:8px;line-height:1.6; }
.plus-item::before { content:'+ ';color:var(--accent);font-weight:700;font-size:0.9rem; }

/* Improvements */
.imp-item { display:flex;gap:10px;padding:12px 14px;border-radius:10px;background:var(--bg-tag);border:1px solid var(--border-light); }
.imp-n { width:20px;height:20px;border-radius:50%;background:var(--accent-soft);color:var(--accent);font-size:0.66rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0; }
.imp-t { font-size:0.74rem;font-weight:600;color:var(--text-primary);margin-bottom:3px; }
.imp-d { font-size:0.70rem;color:var(--text-muted);line-height:1.6; }

/* Grade action */
.grade-intro { font-size:0.76rem;color:var(--text-secondary);line-height:1.75;margin-bottom:14px; }
.grade-opts { display:flex;flex-direction:column;gap:5px;margin-bottom:14px; }
.grade-opt { display:flex;align-items:center;gap:7px;font-size:0.72rem;color:var(--text-secondary);cursor:pointer; }
.grade-opt input[type="checkbox"] { accent-color:var(--accent); }
.grade-start {
  width:100%;padding:10px;border-radius:10px;background:var(--accent);color:#fff;
  border:none;font-weight:600;font-size:0.80rem;cursor:pointer;transition:all 0.25s;
  display:flex;align-items:center;justify-content:center;gap:8px;font-family:inherit;
}
.grade-start:hover:not(:disabled) { box-shadow:0 0 20px var(--accent-glow);transform:translateY(-1px); }
.grade-start:disabled { opacity:0.55;cursor:not-allowed; }
.grade-spinner { width:15px;height:15px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.6s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

/* Export */
.export-row { display:flex;gap:8px; }
.exp-btn {
  flex:1;padding:9px;border-radius:9px;border:1px solid var(--border-medium);
  background:var(--bg-card);color:var(--text-secondary);font-size:0.73rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:6px;transition:all 0.25s;font-family:inherit;
}
.exp-btn svg { stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round; }

/* ====== RADAR CHART ====== */
.radar-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; }
.radar-svg { width:100%; max-width:210px; }
.radar-ring { fill:none; stroke:var(--border-light); stroke-width:1; }
.radar-ring.rl-2 { stroke:var(--divider); }
.radar-ring.rl-4 { stroke:var(--border-medium); stroke-width:1.2; }
.radar-axis { stroke:var(--border-light); stroke-width:0.8; }
.radar-data { fill:var(--accent-soft); stroke:var(--accent); stroke-width:1.6; stroke-linejoin:round; }
.radar-dot { fill:var(--accent); stroke:#fff; stroke-width:1.5; }
body.dark .radar-dot { stroke:var(--bg-root); }
.radar-label { font-size:0.66rem; fill:var(--text-secondary); font-weight:600; }
.radar-label-top { dominant-baseline:auto; }
.radar-label-bot { dominant-baseline:hanging; }
.radar-legend { display:flex; flex-wrap:wrap; gap:4px 10px; justify-content:center; }
.radar-legend-item { font-size:0.70rem; color:var(--text-muted); display:flex; align-items:center; gap:4px; }
.radar-legend-dot { width:6px; height:6px; border-radius:50%; background:var(--accent); display:inline-block; flex-shrink:0; }

/* ====== NOTEBOOK ====== */
.notebook {
  position:relative;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 18px 16px 20px 30px;
  font-family: "STSong", "SimSun", "Noto Serif SC", "Songti SC", serif;
}
.notebook :where(.notebook-text, .notebook-li, .notebook-imp-t, .notebook-imp-d) {
  background-image:
    repeating-linear-gradient(to bottom, transparent, transparent 26px, rgba(0,0,0,0.28) 26px, rgba(0,0,0,0.28) 28px);
  background-size: 100% 28px;
  width: fit-content;
  max-width: 100%;
}
.notebook::before {
  content: ""; position: absolute; left: 8px; top: 20px; bottom: 20px; width: 5px;
  background: repeating-linear-gradient(
    to bottom,
    var(--accent-light),
    var(--accent-light) 14px,
    transparent 14px,
    transparent 36px
  );
  border-radius: 3px;
}
body.dark .notebook :where(.notebook-text, .notebook-li, .notebook-imp-t, .notebook-imp-d) {
  background-image:
    repeating-linear-gradient(to bottom, transparent, transparent 26px, rgba(255,255,255,0.10) 26px, rgba(255,255,255,0.10) 28px);
}
.notebook-score-row {
  display: flex; align-items: baseline; gap: 6px; margin-bottom: 4px;
}
.notebook-score {
  font-size: 1.5rem; font-weight: 700; color: var(--accent);
  font-family: "STSong", "SimSun", "Noto Serif SC", "Songti SC", serif; line-height: 1;
}
.notebook-score-label {
  font-size: 0.78rem; color: var(--text-muted);
  font-family: "STSong", "SimSun", "Noto Serif SC", "Songti SC", serif;
}
.notebook-text {
  font-size: 0.82rem; color: var(--text-secondary); line-height: 28px; margin: 0;
  font-weight: 600; letter-spacing: 0.01em;
}
.notebook-li {
  font-size: 0.78rem; color: var(--text-secondary); line-height: 28px;
  padding-left: 4px; position: relative; font-weight: 600;
}
.notebook-li::before {
  content: "+"; color: var(--accent); font-weight: 700; margin-right: 8px;
}
.notebook-imp { display: flex; gap: 10px; }
.notebook-imp:not(:last-child) { margin-bottom: 8px; }
.notebook-imp-n {
  font-size: 0.82rem; font-weight: 700; color: var(--text-primary);
  line-height: 28px; flex-shrink: 0;
}
.notebook-imp-t {
  font-size: 0.82rem; font-weight: 700; color: var(--text-primary);
  letter-spacing: 0.01em; line-height: 28px;
}
.notebook-imp-d {
  font-size: 0.78rem; color: var(--text-secondary); line-height: 28px; margin-top: 2px; font-weight: 600;
}

/* ====== PANEL COLLAPSE ====== */
.panel-toggle {
  position:absolute; top:50%; transform:translateY(-50%); z-index:10;
  width:22px; height:44px; border-radius:6px; border:1px solid var(--border-medium);
  background:var(--bg-card); color:var(--text-muted); cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.25s; padding:0;
}
.panel-left .panel-toggle { right:2px; }
.panel-right .panel-toggle { left:2px; }
.panel-toggle:hover { color:var(--accent); border-color:var(--accent-light); box-shadow:0 0 10px var(--accent-soft); }
.panel-toggle svg { transition:transform 0.3s; }
.panel.collapsed .panel-toggle { transform:translateY(-50%); }

.panel.collapsed {
  width:38px !important; min-width:38px !important; flex-shrink:0;
  transition:width 0.35s var(--trans), min-width 0.35s var(--trans);
}
.panel.collapsed > *:not(.panel-strip):not(.panel-toggle) { display:none; }
.panel.collapsed .panel-toggle svg { transform:rotate(180deg); }
.exp-btn:hover { border-color:var(--border-active);color:var(--accent);box-shadow:0 0 12px var(--accent-soft); }
</style>
