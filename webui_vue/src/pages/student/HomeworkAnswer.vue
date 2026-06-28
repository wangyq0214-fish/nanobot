<template>
  <div class="homework-answer-page">
    <!-- 顶部导航栏 -->
    <div class="top-bar">
      <button class="back-btn" @click="goBack">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m15 18-6-6 6-6"/>
        </svg>
        <span>返回课程作业列表</span>
      </button>
      <div class="breadcrumb-info">
        <span>当前科目: {{ course?.subject || '-' }}</span>
        <span class="separator">|</span>
        <span>试卷: {{ homework?.title || '-' }}</span>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="content-wrapper">
      <!-- 左侧答题区 -->
      <div class="question-panel" ref="questionPanel">
        <div class="questions-container">
          <!-- 按题型分组显示 -->
          <div v-for="group in questionGroups" :key="group.type" class="question-group">
            <!-- 题型头部 -->
            <div class="group-header">
              <span class="group-title">{{ group.label }} ({{ group.totalPoints }}.0 分)</span>
              <span class="group-range">第 {{ group.startIndex + 1 }}-{{ group.endIndex + 1 }} 题</span>
            </div>

            <!-- 题目列表 -->
            <div v-for="qi in group.indices" :key="qi" class="question-item" :id="`question-${qi}`">
              <!-- 选择题 -->
              <div v-if="questions[qi].type === 'choice'" class="choice-question">
                <p class="question-text">
                  <span class="question-num">{{ qi + 1 }}.</span>
                  {{ questions[qi].content }}
                  <span class="question-points">({{ questions[qi].points }}分)</span>
                </p>
                <div class="options-grid">
                  <label
                    v-for="opt in questions[qi].options"
                    :key="opt.key"
                    class="option-card"
                    :class="{ selected: answers[questions[qi].id] === opt.key }"
                  >
                    <input
                      type="radio"
                      :name="`q-${questions[qi].id}`"
                      :value="opt.key"
                      v-model="answers[questions[qi].id]"
                      @change="updateProgress"
                    />
                    <span class="option-label"><b>{{ opt.key }}.</b> {{ opt.text }}</span>
                  </label>
                </div>
              </div>

              <!-- 判断题 -->
              <div v-else-if="questions[qi].type === 'true_false'" class="tf-question">
                <div class="question-header">
                  <span class="question-num">{{ qi + 1 }}.</span>
                  <p class="question-text">
                    {{ questions[qi].content }}
                    <span class="question-points">({{ questions[qi].points }}分)</span>
                  </p>
                </div>
                <div class="tf-options">
                  <button
                    class="tf-btn"
                    :class="{ selected: answers[questions[qi].id] === 'true' }"
                    @click="answers[questions[qi].id] = 'true'; updateProgress()"
                  >✓ 正确</button>
                  <button
                    class="tf-btn"
                    :class="{ selected: answers[questions[qi].id] === 'false' }"
                    @click="answers[questions[qi].id] = 'false'; updateProgress()"
                  >✕ 错误</button>
                </div>
              </div>

              <!-- 填空题/简答题/论述题 -->
              <div v-else class="text-question">
                <div class="question-header">
                  <span class="question-num">{{ qi + 1 }}.</span>
                  <p class="question-text">
                    {{ questions[qi].content }}
                    <span class="question-points">({{ questions[qi].points }}分)</span>
                  </p>
                </div>
                <div class="answer-input-box">
                  <textarea
                    v-model="answers[questions[qi].id]"
                    :rows="questions[qi].type === 'essay' ? 8 : 4"
                    :placeholder="getPlaceholder(questions[qi].type)"
                    @input="updateProgress"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧答题卡 -->
      <aside class="answer-card-panel">
        <div class="card-header">
          <span class="card-label">Answer Progress</span>
          <span class="card-title">答题卡导航中心</span>
        </div>

        <div class="card-groups">
          <div v-for="group in questionGroups" :key="group.type" class="card-group">
            <div class="group-info">
              <span>{{ group.label }}</span>
              <span class="group-score">({{ group.totalPoints }}.0 分)</span>
            </div>
            <div class="group-items">
              <div
                v-for="qi in group.indices"
                :key="qi"
                class="card-item"
                :class="{
                  answered: isAnswered(qi),
                  active: currentQuestion === qi
                }"
                @click="scrollToQuestion(qi)"
              >
                <span>{{ qi + 1 }}</span>
                <div v-if="isAnswered(qi)" class="answered-dot">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <div class="progress-text">答题进度: {{ answeredCount }} / {{ questions.length }} 题</div>
          <button
            class="submit-btn"
            @click="handleSubmit"
            :disabled="submitting"
          >
            {{ submitting ? '提交中...' : '提交试卷' }}
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useCourse } from '../../composables/useCourse.js'
import { useGateway } from '../../composables/useGateway.js'

const router = useRouter()
const route = useRoute()
const { user } = useAuth()
const {
  currentCourse: course, homeworkList,
  fetchCourseDetail, fetchHomeworkList, submitHomework,
} = useCourse()
const { connect: connectGateway, connected, getToken } = useGateway()

const courseId = route.params.courseId
const hwId = route.params.hwId

const homework = computed(() => homeworkList.value.find(h => h.hwId === hwId))
const questions = computed(() => homework.value?.questions || [])

const answers = reactive({})
const submitting = ref(false)
const currentQuestion = ref(0)
const questionPanel = ref(null)

// 计算答题进度
const answeredCount = computed(() => {
  return questions.value.filter(q => {
    const ans = answers[q.id]
    return ans !== undefined && ans !== null && ans !== ''
  }).length
})

// 按题型分组
const questionGroups = computed(() => {
  const groups = []
  const typeOrder = ['choice', 'true_false', 'fill', 'short_answer', 'essay']
  const typeLabels = {
    choice: '一、单选题',
    true_false: '二、判断题',
    fill: '三、填空题',
    short_answer: '四、简答题',
    essay: '五、论述题',
  }

  const typeMap = {}
  questions.value.forEach((q, i) => {
    if (!typeMap[q.type]) {
      typeMap[q.type] = { indices: [], totalPoints: 0 }
    }
    typeMap[q.type].indices.push(i)
    typeMap[q.type].totalPoints += q.points || 0
  })

  for (const type of typeOrder) {
    if (typeMap[type]) {
      groups.push({
        type,
        label: typeLabels[type] || type,
        indices: typeMap[type].indices,
        totalPoints: typeMap[type].totalPoints,
        startIndex: typeMap[type].indices[0],
        endIndex: typeMap[type].indices[typeMap[type].indices.length - 1],
      })
    }
  }

  return groups
})

function isAnswered(qi) {
  const q = questions.value[qi]
  if (!q) return false
  const ans = answers[q.id]
  return ans !== undefined && ans !== null && ans !== ''
}

function getPlaceholder(type) {
  const placeholders = {
    fill: '填写答案...',
    short_answer: '输入你的答案...',
    essay: '详细阐述你的观点...',
  }
  return placeholders[type] || '输入答案...'
}

function updateProgress() {
  // 触发响应式更新
}

function scrollToQuestion(qi) {
  currentQuestion.value = qi
  const el = document.getElementById(`question-${qi}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function goBack() {
  router.push(`/student/courses/${courseId}`)
}

async function handleSubmit() {
  if (submitting.value) return

  const unanswered = questions.value.filter(q => {
    const ans = answers[q.id]
    return ans === undefined || ans === null || ans === ''
  })

  if (unanswered.length > 0) {
    const confirmSubmit = confirm(`还有 ${unanswered.length} 道题未作答，确定要提交吗？`)
    if (!confirmSubmit) return
  }

  submitting.value = true
  try {
    await submitHomework(courseId, hwId, { ...answers })
    alert('作业提交成功！')
    router.push(`/student/courses/${courseId}`)
  } catch (e) {
    alert('提交失败：' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

// 监听滚动更新当前题目
function handleScroll() {
  if (!questionPanel.value) return
  const panelTop = questionPanel.value.getBoundingClientRect().top

  for (let i = questions.value.length - 1; i >= 0; i--) {
    const el = document.getElementById(`question-${i}`)
    if (el) {
      const rect = el.getBoundingClientRect()
      if (rect.top - panelTop <= 100) {
        currentQuestion.value = i
        break
      }
    }
  }
}

onMounted(async () => {
  if (!user.value) return

  try {
    if (!connected.value) {
      await connectGateway({ role: user.value.role, userId: user.value.userId })
    }
  } catch (e) {
    console.warn('[HomeworkAnswer] Gateway connect failed:', e.message)
  }

  try {
    await Promise.all([
      fetchCourseDetail(courseId),
      fetchHomeworkList(courseId),
    ])
  } catch (e) {
    console.error('[HomeworkAnswer] Failed to load data:', e)
  }

  if (questionPanel.value) {
    questionPanel.value.addEventListener('scroll', handleScroll)
  }
})

onBeforeUnmount(() => {
  if (questionPanel.value) {
    questionPanel.value.removeEventListener('scroll', handleScroll)
  }
})
</script>

<style scoped>
.homework-answer-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #232824;
}

/* 顶部导航栏 */
.top-bar {
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: #ffffff;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: #999999;
  font-size: 12px;
  cursor: pointer;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #121212;
}

.breadcrumb-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  color: #999999;
}

.separator {
  color: #e0e0e0;
}

/* 主体内容区 */
.content-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧答题区 */
.question-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  border-right: 1px solid #f5f5f5;
}

.questions-container {
  max-width: 768px;
  padding-bottom: 64px;
}

/* 题型分组 */
.question-group {
  margin-bottom: 32px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  color: #999999;
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.group-title {
  color: #121212;
  font-weight: 700;
}

.group-range {
  font-family: 'Courier New', monospace;
}

/* 题目项 */
.question-item {
  margin-bottom: 24px;
}

/* 选择题 */
.choice-question .question-text {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  line-height: 1.6;
  margin: 0 0 12px;
}

.question-num {
  font-family: 'Courier New', monospace;
  margin-right: 4px;
}

.question-points {
  color: #999999;
  font-weight: 400;
  font-family: 'Courier New', monospace;
  margin-left: 4px;
}

.options-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-card {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #ffffff;
}

.option-card:hover {
  border-color: #121212;
}

.option-card.selected {
  border-width: 2px;
  border-color: #121212;
  background: #fafbfa;
}

.option-card input[type="radio"] {
  display: none;
}

.option-label {
  font-size: 12px;
  color: #444444;
  line-height: 1.5;
  font-family: 'Noto Serif SC', serif;
}

.option-card.selected .option-label {
  color: #121212;
  font-weight: 600;
}

.option-label b {
  font-family: 'Courier New', monospace;
  margin-right: 8px;
}

/* 判断题 */
.tf-question .question-header {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 12px;
}

.tf-question .question-text {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  line-height: 1.6;
  margin: 0;
}

.tf-options {
  display: flex;
  gap: 8px;
}

.tf-btn {
  padding: 6px 20px;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  background: #ffffff;
  font-size: 12px;
  font-weight: 500;
  color: #444444;
  cursor: pointer;
  transition: all 0.2s;
}

.tf-btn:hover {
  border-color: #121212;
}

.tf-btn.selected {
  border-color: #121212;
  background: #121212;
  color: #ffffff;
}

/* 填空题/论述题 */
.text-question .question-header {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 12px;
}

.text-question .question-text {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
  line-height: 1.6;
  margin: 0;
}

.answer-input-box {
  border: 1px solid #edf0ed;
  border-radius: 12px;
  padding: 12px;
  background: #ffffff;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.001);
}

.answer-input-box:focus-within {
  border-color: #121212;
}

.answer-input-box textarea {
  width: 100%;
  background: transparent;
  border: none;
  font-size: 12px;
  color: #121212;
  placeholder-color: #cccccc;
  outline: none;
  resize: none;
  font-family: 'Noto Serif SC', serif;
  line-height: 1.6;
}

/* 右侧答题卡 */
.answer-card-panel {
  width: 288px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: #fcfdfc;
  padding: 20px;
}

.card-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.card-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: #999999;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: 'Courier New', monospace;
  margin-bottom: 4px;
}

.card-title {
  font-size: 12px;
  font-weight: 700;
  color: #121212;
}

/* 答题卡分组 */
.card-groups {
  flex: 1;
  overflow-y: auto;
}

.card-group {
  margin-bottom: 16px;
}

.group-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 9px;
  color: #999999;
  font-weight: 500;
  font-family: 'Courier New', monospace;
  margin-bottom: 8px;
}

.group-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 答题卡题目编号 */
.card-item {
  width: 36px;
  height: 36px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: #999999;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background: #ffffff;
}

.card-item:hover {
  border-color: #999999;
  color: #121212;
}

.card-item.active {
  border-width: 2px;
  border-color: #121212;
  color: #121212;
  font-weight: 700;
}

.card-item.answered {
  border-color: #e0e0e0;
  color: #999999;
}

.answered-dot {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 12px;
  height: 12px;
  background: #121212;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
}

/* 底部提交区 */
.card-footer {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  margin-top: 16px;
}

.progress-text {
  font-size: 10px;
  color: #999999;
  text-align: center;
  font-family: 'Courier New', monospace;
  margin-bottom: 8px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background: #121212;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  letter-spacing: 4px;
}

.submit-btn:hover {
  background: #333333;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 暗色主题 */
body.dark .homework-answer-page {
  background: #121212;
  color: #e5e5e5;
}

body.dark .top-bar {
  background: #1a1a1a;
  border-bottom-color: #2d2d2d;
}

body.dark .back-btn {
  color: #666666;
}

body.dark .back-btn:hover {
  color: #e5e5e5;
}

body.dark .breadcrumb-info {
  color: #666666;
}

body.dark .question-panel {
  border-right-color: #2d2d2d;
}

body.dark .group-header {
  border-bottom-color: #2d2d2d;
  color: #666666;
}

body.dark .group-title {
  color: #e5e5e5;
}

body.dark .question-text {
  color: #e5e5e5;
}

body.dark .option-card {
  border-color: #333333;
  background: #1a1a1a;
}

body.dark .option-card:hover {
  border-color: #e5e5e5;
}

body.dark .option-card.selected {
  border-color: #e5e5e5;
  background: #242424;
}

body.dark .option-label {
  color: #cccccc;
}

body.dark .option-card.selected .option-label {
  color: #e5e5e5;
}

body.dark .tf-btn {
  border-color: #333333;
  background: #1a1a1a;
  color: #cccccc;
}

body.dark .tf-btn:hover {
  border-color: #e5e5e5;
}

body.dark .tf-btn.selected {
  border-color: #e5e5e5;
  background: #e5e5e5;
  color: #121212;
}

body.dark .answer-input-box {
  border-color: #333333;
  background: #1a1a1a;
}

body.dark .answer-input-box:focus-within {
  border-color: #e5e5e5;
}

body.dark .answer-input-box textarea {
  color: #e5e5e5;
}

body.dark .answer-card-panel {
  background: #1a1a1a;
}

body.dark .card-header {
  border-bottom-color: #2d2d2d;
}

body.dark .card-label {
  color: #666666;
}

body.dark .card-title {
  color: #e5e5e5;
}

body.dark .group-info {
  color: #666666;
}

body.dark .card-item {
  border-color: #333333;
  color: #666666;
  background: #1a1a1a;
}

body.dark .card-item:hover {
  border-color: #999999;
  color: #e5e5e5;
}

body.dark .card-item.active {
  border-color: #e5e5e5;
  color: #e5e5e5;
}

body.dark .answered-dot {
  background: #e5e5e5;
  color: #121212;
}

body.dark .card-footer {
  border-top-color: #2d2d2d;
}

body.dark .progress-text {
  color: #666666;
}

body.dark .submit-btn {
  background: #e5e5e5;
  color: #121212;
}

body.dark .submit-btn:hover {
  background: #cccccc;
}

/* 绿色主题 */
body.green .homework-answer-page {
  background: #f7f8f7;
  color: #1e2720;
}

body.green .top-bar {
  background: #edf0ed;
  border-bottom-color: #dee2de;
}

body.green .back-btn {
  color: #8fa091;
}

body.green .back-btn:hover {
  color: #1e2720;
}

body.green .breadcrumb-info {
  color: #8fa091;
}

body.green .question-panel {
  border-right-color: #e2e6e2;
}

body.green .group-header {
  border-bottom-color: #e2e6e2;
  color: #8fa091;
}

body.green .group-title {
  color: #1e2720;
}

body.green .question-text {
  color: #1e2720;
}

body.green .option-card {
  border-color: #d4e0d6;
  background: #ffffff;
}

body.green .option-card:hover {
  border-color: #526e5a;
}

body.green .option-card.selected {
  border-color: #526e5a;
  background: #edf2ee;
}

body.green .option-label {
  color: #3b473d;
}

body.green .option-card.selected .option-label {
  color: #1e2720;
}

body.green .tf-btn {
  border-color: #d4e0d6;
  background: #ffffff;
  color: #3b473d;
}

body.green .tf-btn:hover {
  border-color: #526e5a;
}

body.green .tf-btn.selected {
  border-color: #526e5a;
  background: #526e5a;
  color: #ffffff;
}

body.green .answer-input-box {
  border-color: #d4e0d6;
  background: #ffffff;
}

body.green .answer-input-box:focus-within {
  border-color: #526e5a;
}

body.green .answer-input-box textarea {
  color: #1e2720;
}

body.green .answer-card-panel {
  background: #edf0ed;
}

body.green .card-header {
  border-bottom-color: #d4e0d6;
}

body.green .card-label {
  color: #8fa091;
}

body.green .card-title {
  color: #1e2720;
}

body.green .group-info {
  color: #8fa091;
}

body.green .card-item {
  border-color: #d4e0d6;
  color: #8fa091;
  background: #ffffff;
}

body.green .card-item:hover {
  border-color: #526e5a;
  color: #1e2720;
}

body.green .card-item.active {
  border-color: #526e5a;
  color: #1e2720;
}

body.green .answered-dot {
  background: #526e5a;
  color: #ffffff;
}

body.green .card-footer {
  border-top-color: #d4e0d6;
}

body.green .progress-text {
  color: #8fa091;
}

body.green .submit-btn {
  background: #526e5a;
  color: #ffffff;
}

body.green .submit-btn:hover {
  background: #415848;
}

/* 响应式 */
@media (max-width: 768px) {
  .answer-card-panel {
    display: none;
  }

  .top-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .breadcrumb-info {
    font-size: 10px;
  }
}
</style>
