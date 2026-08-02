<template>
<!-- ====== 互动消息 · 双栏布局 ====== -->
<div v-if="activeTab === 'feed'" class="feed-layout">
  <div class="feed-topbar">
    <h1 class="ft-title">互动消息</h1>
  </div>

  <div class="feed-cols">
    <!-- 左栏：讨论 -->
    <div class="feed-col">
      <div class="col-head">
        <div class="col-head-left">
          <span class="col-title">课程讨论</span>
          <span class="col-count">{{ discussions.length }}</span>
        </div>
        <button class="col-compose-btn" @click="composeType = 'discussion'; composeOpen = true">+ 发起</button>
      </div>
      <div class="col-list">
        <div v-for="(d, di) in discussions" :key="d.key" class="discuss-card" :class="{ pinned: d.pinned }" :style="{ animationDelay: di * 0.06 + 's' }" @click="openThread(d)">
          <div class="dc-top">
            <span v-if="d.pinned" class="dc-pin">📌 置顶</span>
            <h3 class="dc-title">{{ d.title }}</h3>
          </div>
          <p class="dc-body">{{ d.content.slice(0, 90) }}{{ d.content.length > 90 ? '...' : '' }}</p>
          <div class="dc-foot">
            <span class="dc-author">{{ d.author }}</span>
            <span class="dc-replies">{{ d.replies || 0 }} 回复</span>
            <span class="dc-time">{{ d.time }}</span>
          </div>
          <div v-if="(d.replyList || []).length" class="dc-last-reply">
            <span class="dlr-name">{{ d.replyList[d.replyList.length - 1].author }}</span>
            <span class="dlr-text">：{{ d.replyList[d.replyList.length - 1].text.slice(0, 50) }}{{ d.replyList[d.replyList.length - 1].text.length > 50 ? '...' : '' }}</span>
          </div>
        </div>
        <div v-if="discussions.length === 0" class="col-empty">暂无讨论</div>
      </div>
    </div>

    <!-- 右栏：通知 -->
    <div class="feed-col">
      <div class="col-head">
        <div class="col-head-left">
          <span class="col-title">班级通知</span>
          <span class="col-count">{{ sentNotifications.length }}</span>
        </div>
        <button class="col-compose-btn" @click="composeType = 'notification'; composeOpen = true">+ 群发</button>
      </div>
      <div class="col-list">
        <div v-for="(n, ni) in sentNotifications" :key="n.key" class="noti-card" :style="{ animationDelay: ni * 0.06 + 's' }">
          <div class="nc-stripe"></div>
          <div class="nc-content">
            <div class="nc-head">
              <span class="nc-badge">{{ n.typeLabel }}</span>
              <span class="nc-time">{{ n.time }}</span>
            </div>
            <h3 class="nc-title">{{ n.title }}</h3>
            <div class="nc-meta">{{ n.courseName || '全课程' }}</div>
          </div>
        </div>
        <div v-if="sentNotifications.length === 0" class="col-empty">暂无通知</div>
      </div>
    </div>
  </div>

  <!-- 线程浮层 -->
  <Transition name="fade">
    <div v-if="threadOpen" class="thread-overlay" @click.self="threadOpen = null">
      <div class="thread-sheet">
        <div class="ts-head">
          <button @click="threadOpen = null">← 返回列表</button>
          <span v-if="threadOpen.pinned" class="ts-pin">📌 置顶</span>
        </div>
        <div class="ts-scroll">
          <h2 class="ts-title">{{ threadOpen.title }}</h2>
          <div class="ts-meta">{{ threadOpen.author }} · {{ threadOpen.time }}</div>
          <p class="ts-body">{{ threadOpen.content }}</p>
          <div class="ts-divider">{{ threadOpen.replies || 0 }} 条回复</div>
          <div v-for="r in (threadOpen.replyList || [])" :key="r.id" class="reply-row">
            <span class="rr-avatar">{{ r.author[0] }}</span>
            <div class="rr-body">
              <div class="rr-name">{{ r.author }} <span class="rr-time">{{ r.time }}</span></div>
              <div class="rr-text">{{ r.text }}</div>
            </div>
          </div>
        </div>
        <div class="ts-input-bar">
          <input v-model="replyText" placeholder="输入回复..." @keyup.enter="addReply" />
          <button @click="addReply" :disabled="!replyText.trim()">发送</button>
        </div>
      </div>
    </div>
  </Transition>

  <!-- 撰写浮层 -->
  <Transition name="fade">
    <div v-if="composeOpen" class="compose-overlay" @click.self="composeOpen = false">
      <div class="compose-sheet">
        <div class="cs-head">
          <button @click="composeOpen = false">取消</button>
          <h2>{{ composeType === 'discussion' ? '发起讨论' : '群发通知' }}</h2>
          <button class="cs-submit" @click="publishCompose">{{ composeType === 'discussion' ? '发布' : '发送' }}</button>
        </div>
        <div class="cs-body">
          <template v-if="composeType === 'discussion'">
            <input v-model="newTopic.title" class="cs-title-input" placeholder="话题标题..." />
            <textarea v-model="newTopic.content" class="cs-textarea" rows="6" placeholder="说点什么来开启讨论吧...&#10;&#10;可以是课程问题、植保案例讨论、实习经验分享..."></textarea>
            <div class="cs-options">
              <label class="cs-check"><input type="checkbox" v-model="newTopic.pinned" /><span>置顶话题</span></label>
            </div>
          </template>
          <template v-else>
            <div class="cs-row">
              <div class="cs-field">
                <label>目标范围</label>
                <select v-model="notifyForm.courseId"><option value="">全部课程</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select>
              </div>
              <div class="cs-field">
                <label>通知类型</label>
                <select v-model="notifyForm.type"><option value="general">一般通知</option><option value="deadline">作业截止</option><option value="exam">考试通知</option><option value="schedule">调课通知</option></select>
              </div>
            </div>
            <input v-model="notifyForm.title" class="cs-title-input" placeholder="通知标题..." />
            <textarea v-model="notifyForm.content" class="cs-textarea" rows="6" placeholder="通知正文...&#10;&#10;将发送给目标课程的所有学生。"></textarea>
          </template>
        </div>
      </div>
    </div>
  </Transition>
</div>

<!-- ====== 课程资料 ====== -->
<div v-else class="resource-layout">
  <div class="res-topbar">
    <div class="ft-left">
      <h1 class="ft-title">课程资料</h1>
    </div>
    <div class="ft-right">
      <div class="ft-search">
        <svg viewBox="0 0 20 20" width="14" height="14"><circle cx="9" cy="9" r="5"/><path d="M13 13l4 4"/></svg>
        <input v-model="resourceSearch" placeholder="搜索文件名..." />
      </div>
      <button class="res-upload-btn" @click="showUpload = true">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
        上传文件
      </button>
    </div>
  </div>

  <!-- 类型筛选 + 拖拽条 -->
  <div class="res-bar">
    <div class="res-filters">
      <span :class="{ on: resourceTypeFilter === 'all' }" @click="resourceTypeFilter = 'all'">全部</span>
      <span :class="{ on: resourceTypeFilter === 'pdf' }" @click="resourceTypeFilter = 'pdf'">PDF 文档</span>
      <span :class="{ on: resourceTypeFilter === 'video' }" @click="resourceTypeFilter = 'video'">视频</span>
      <span :class="{ on: resourceTypeFilter === 'image' }" @click="resourceTypeFilter = 'image'">图片</span>
      <span :class="{ on: resourceTypeFilter === 'other' }" @click="resourceTypeFilter = 'other'">其他</span>
    </div>
    <div class="res-dropstrip" @dragover.prevent @dragenter.prevent="isDragOver = true" @dragleave.prevent="isDragOver = false" @drop.prevent="onFileDrop" :class="{ hovering: isDragOver }">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
      <span>拖拽文件到此处上传 · PDF、PPT、视频、图片</span>
    </div>
  </div>

  <!-- 文件列表 -->
  <div class="res-table-wrap">
    <div class="res-table">
      <div class="rt-row rt-head">
        <span class="rt-cell rt-name">文件名</span>
        <span class="rt-cell rt-course">所属课程</span>
        <span class="rt-cell rt-size">大小</span>
        <span class="rt-cell rt-date">上传时间</span>
        <span class="rt-cell rt-act"></span>
      </div>
      <div v-for="r in filteredResources" :key="r.id" class="rt-row">
        <span class="rt-cell rt-name">
          <span class="rt-icon" :class="r.type">
            <svg v-if="r.type === 'pdf'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <svg v-else-if="r.type === 'video'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <svg v-else-if="r.type === 'image'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
          </span>
          <span class="rt-fname">{{ r.name }}</span>
        </span>
        <span class="rt-cell rt-course">{{ r.courseName || '未分类' }}</span>
        <span class="rt-cell rt-size">{{ r.size }}</span>
        <span class="rt-cell rt-date">{{ r.date || '刚刚' }}</span>
        <span class="rt-cell rt-act">
          <button title="下载"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg></button>
          <button title="删除" @click="handleDeleteResource(r)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
        </span>
      </div>
      <div v-if="filteredResources.length === 0" class="rt-empty">暂无资料，拖拽文件或点击"上传文件"开始</div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showUpload" class="modal-overlay" @click.self="showUpload = false">
      <div class="modal-panel">
        <div class="modal-header"><h3>上传资料</h3><button class="modal-close" @click="showUpload = false"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>
        <div class="modal-body">
          <div class="upload-area"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg><p>选择要上传的文件</p></div>
          <div class="mf-field"><label>所属课程</label><select v-model="uploadForm.courseId" @change="onResourceCourseChange"><option value="">选择课程...</option><option v-for="c in courses" :key="c.courseId" :value="c.courseId">{{ c.courseName }}</option></select></div>
        </div>
        <div class="modal-footer"><button class="btn-cancel" @click="showUpload = false">取消</button><button class="btn-primary" @click="uploadResource" :disabled="uploading">{{ uploading ? '上传中...' : '确认上传' }}</button></div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourse } from '../../composables/useCourse.js'

const route = useRoute()
const {
  courses, fetchCourses, fetchResources, createResource, deleteResource,
  fetchNotifications, createNotification,
  fetchDiscussions, createDiscussion, replyDiscussion,
} = useCourse()

const activeTab = ref(route.query.tab || 'feed')
watch(() => route.query.tab, (val) => { if (val) activeTab.value = val })

const loading = ref(false)

// ====== 互动消息 ======
const composeType = ref('discussion')
const composeOpen = ref(false)
const threadOpen = ref(null)
const replyText = ref('')
const replying = ref(false)
const composing = ref(false)
const newTopic = ref({ title: '', content: '', pinned: false })
const notifyForm = ref({ courseId: '', type: 'general', title: '', content: '' })

const discussions = ref([])
const sentNotifications = ref([])

const typeLabels = { general: '通知', deadline: '截止', exam: '考试', schedule: '调课' }

async function loadDiscussions() {
  try {
    const list = await fetchDiscussions()
    discussions.value = list.map(d => ({
      id: d.id, kind: 'discussion', key: d.key || `d${d.id}`,
      title: d.title, author: d.author || '教师', replies: d.replies || 0,
      time: fmtTime(d.createdAt), pinned: d.pinned || false,
      content: d.content || '', replyList: d.replyList || [],
    }))
  } catch (e) { console.warn('load discussions failed:', e) }
}

async function loadNotifications() {
  try {
    const list = await fetchNotifications()
    sentNotifications.value = list
      .filter(n => n.type !== 'discussion')
      .map(n => ({
        id: n.id, kind: 'notification', key: `n${n.id}`,
        title: n.title, type: n.type, typeLabel: typeLabels[n.type] || n.type,
        courseName: n.relatedId ? (courses.value.find(c => c.courseId === n.relatedId)?.courseName || '全课程') : '全课程',
        time: fmtTime(n.createdAt),
      }))
  } catch (e) { console.warn('load notifications failed:', e) }
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso), now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function openThread(d) { threadOpen.value = d }

async function addReply() {
  if (!replyText.value.trim() || !threadOpen.value) return
  replying.value = true
  try {
    await replyDiscussion(threadOpen.value.id, replyText.value)
    threadOpen.value.replyList.push({ author: '教师', text: replyText.value, time: '刚刚' })
    threadOpen.value.replies++
    replyText.value = ''
  } catch (e) { console.error('reply failed:', e) }
  finally { replying.value = false }
}

async function publishCompose() {
  composing.value = true
  try {
    if (composeType.value === 'discussion') {
      await createDiscussion({
        title: newTopic.value.title || '无标题',
        content: newTopic.value.content,
        pinned: newTopic.value.pinned,
      })
      newTopic.value = { title: '', content: '', pinned: false }
      await loadDiscussions()
    } else {
      await createNotification({
        title: notifyForm.value.title || '无标题',
        type: notifyForm.value.type,
        content: notifyForm.value.content,
        courseId: notifyForm.value.courseId,
      })
      notifyForm.value = { courseId: '', type: 'general', title: '', content: '' }
      await loadNotifications()
    }
  } catch (e) { console.error('publish failed:', e) }
  finally { composing.value = false; composeOpen.value = false }
}

// ====== 资料 ======
const resourceSearch = ref('')
const resourceTypeFilter = ref('all')
const showUpload = ref(false)
const isDragOver = ref(false)
const uploadForm = ref({ courseId: '' })
const uploading = ref(false)
const resources = ref([])
const selectedResourceCourse = ref('')

async function loadResources(courseId) {
  if (!courseId) { resources.value = []; return }
  try {
    const list = await fetchResources(courseId, resourceTypeFilter.value !== 'all' ? resourceTypeFilter.value : null)
    resources.value = list.map(r => ({
      id: r.id,
      name: r.title,
      type: r.resource_type || r.type || 'other',
      size: formatSize(r.file_size || r.fileSize || 0),
      courseName: courses.value.find(c => c.courseId === r.course_id || c.courseId === r.courseId)?.courseName || '',
      date: fmtTime(r.created_at || r.createdAt),
    }))
  } catch (e) { console.warn('load resources failed:', e) }
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const filteredResources = computed(() => {
  let list = resources.value
  if (resourceTypeFilter.value !== 'all') list = list.filter(r => r.type === resourceTypeFilter.value)
  if (resourceSearch.value) list = list.filter(r => r.name.toLowerCase().includes(resourceSearch.value.toLowerCase()))
  return list
})

async function onFileDrop() {
  isDragOver.value = false
  if (!uploadForm.value.courseId) return
  await createResource(uploadForm.value.courseId, { title: '拖拽上传文件', type: 'other' })
  await loadResources(uploadForm.value.courseId)
}

async function uploadResource() {
  if (!uploadForm.value.courseId) return
  uploading.value = true
  try {
    await createResource(uploadForm.value.courseId, { title: '新上传文件', type: 'other' })
    await loadResources(uploadForm.value.courseId)
  } catch (e) { console.error('upload failed:', e) }
  finally { uploading.value = false; showUpload.value = false }
}

async function handleDeleteResource(resource) {
  if (!confirm(`确定删除 "${resource.name}"？`)) return
  // 需要知道 resource 属于哪个 course，从列表推断
  const courseId = uploadForm.value.courseId || selectedResourceCourse.value
  if (!courseId) return
  try {
    await deleteResource(courseId, resource.id)
    resources.value = resources.value.filter(r => r.id !== resource.id)
  } catch (e) { console.error('delete failed:', e) }
}

// 课程切换时重新加载资料
async function onResourceCourseChange() {
  selectedResourceCourse.value = uploadForm.value.courseId
  await loadResources(uploadForm.value.courseId)
}

onMounted(async () => {
  loading.value = true
  await fetchCourses()
  await Promise.all([loadDiscussions(), loadNotifications()])
  loading.value = false
})
</script>

<style scoped>
* { margin:0; padding:0; box-sizing:border-box; }
:root { --bg-soft: #fafbfa; --bg-tag: #f0f0f0; --bg-card: #fff; --accent: #121212; --border-light: #e0e0e0; --text-primary: #121212; --text-secondary: #4a534c; --text-muted: #999; --divider: #f0f0f0; --radius-lg: 16px; --radius-md: 12px; }

/* ====== 互动消息 · 双栏 ====== */
.feed-layout { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.feed-topbar { padding:24px 32px 16px; flex-shrink:0; }
.ft-title { font-size:1.5rem; font-weight:700; color:var(--text-primary); letter-spacing:-0.02em; }

.feed-cols { flex:1; display:grid; grid-template-columns:1fr 1fr; gap:20px; padding:0 32px 24px; overflow:hidden; }
.feed-col { display:flex; flex-direction:column; overflow:hidden; background:var(--bg-card); border:1px solid var(--border-light); border-radius:var(--radius-lg); }

/* 列头 */
.col-head { display:flex; align-items:center; justify-content:space-between; padding:16px 20px; border-bottom:1px solid var(--divider); flex-shrink:0; }
.col-head-left { display:flex; align-items:center; gap:8px; }
.col-title { font-size:0.9rem; font-weight:700; color:var(--text-primary); }
.col-count { font-size:0.68rem; color:var(--text-muted); background:var(--bg-tag); padding:1px 8px; border-radius:10px; font-weight:600; }
.col-compose-btn { padding:6px 16px; border-radius:18px; border:1.5px solid #526e5a; background:transparent; color:#526e5a; font-size:0.74rem; font-weight:600; cursor:pointer; transition:all 0.2s; font-family:inherit; }
.col-compose-btn:hover { background:#526e5a; color:#fff; }

.col-list { flex:1; overflow-y:auto; padding:12px 16px; display:flex; flex-direction:column; gap:8px; }
.col-list::-webkit-scrollbar { width:3px; }
.col-list::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
.col-empty { text-align:center; padding:40px 0; color:var(--text-muted); font-size:0.78rem; }

/* 讨论卡片 */
.discuss-card { padding:16px; border:1px solid var(--border-light); border-radius:var(--radius-md); cursor:pointer; transition:all 0.2s; animation:fadeUp 0.4s ease both; }
@keyframes fadeUp { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:translateY(0)} }
.discuss-card:hover { border-color:#526e5a; }
.discuss-card.pinned { border-left:3px solid #526e5a; }
.dc-top { margin-bottom:6px; }
.dc-pin { font-size:0.62rem; font-weight:700; color:#526e5a; }
.dc-title { font-size:0.88rem; font-weight:600; color:var(--text-primary); line-height:1.4; display:inline; }
.dc-body { font-size:0.76rem; color:var(--text-secondary); line-height:1.5; margin-bottom:10px; }
.dc-foot { display:flex; gap:8px; font-size:0.68rem; color:var(--text-muted); }
.dc-author { font-weight:600; color:var(--text-secondary); }
.dc-replies { }
.dc-time { margin-left:auto; }
.dc-last-reply { margin-top:10px; padding:8px 10px; background:var(--bg-soft); border-radius:8px; font-size:0.7rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-muted); }
.dlr-name { font-weight:600; color:var(--text-secondary); }

/* 通知卡片 */
.noti-card { display:flex; border:1px solid var(--border-light); border-radius:var(--radius-md); overflow:hidden; transition:all 0.2s; cursor:default; animation:fadeUp 0.4s ease both; }
.noti-card:hover { border-color:#526e5a; }
.nc-stripe { width:4px; flex-shrink:0; background:#526e5a; }
.nc-content { flex:1; padding:14px 16px; }
.nc-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.nc-badge { font-size:0.6rem; font-weight:700; padding:2px 8px; border-radius:6px; border:1px solid #526e5a; color:#526e5a; }
.nc-time { font-size:0.66rem; color:var(--text-muted); }
.nc-title { font-size:0.82rem; font-weight:600; color:var(--text-primary); line-height:1.4; }
.nc-meta { font-size:0.68rem; color:var(--text-muted); margin-top:4px; }
.feed-empty { text-align:center; padding:64px 0; color:var(--text-muted); font-size:0.82rem; }

/* 线程浮层 */
.thread-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); z-index:100; display:flex; justify-content:flex-end; }
.thread-sheet { width:440px; height:100%; background:var(--bg-card); display:flex; flex-direction:column; box-shadow:-12px 0 48px rgba(0,0,0,0.08); }
.ts-head { padding:16px 20px; border-bottom:1px solid var(--divider); display:flex; gap:10px; align-items:center; flex-shrink:0; }
.ts-head button { background:none; border:none; color:var(--accent); font-weight:600; cursor:pointer; font-size:0.8rem; }
.ts-pin { font-size:0.7rem; color:var(--text-secondary); }
.ts-scroll { flex:1; overflow-y:auto; padding:20px; }
.ts-title { font-size:1.1rem; font-weight:700; margin-bottom:6px; color:var(--text-primary); }
.ts-meta { font-size:0.72rem; color:var(--text-muted); margin-bottom:16px; }
.ts-body { font-size:0.84rem; line-height:1.8; color:var(--text-primary); }
.ts-divider { font-size:0.7rem; color:var(--text-muted); font-weight:600; padding:20px 0 12px; margin-top:16px; border-top:1px solid var(--divider); }
.reply-row { display:flex; gap:10px; padding:10px 0; border-bottom:1px solid var(--divider); }
.rr-avatar { width:28px; height:28px; border-radius:50%; background:var(--accent); color:#fff; display:flex; align-items:center; justify-content:center; font-size:0.68rem; font-weight:700; flex-shrink:0; }
.rr-body { flex:1; }
.rr-name { font-size:0.74rem; font-weight:600; color:var(--text-primary); }
.rr-time { font-weight:400; font-size:0.66rem; color:var(--text-muted); margin-left:8px; }
.rr-text { font-size:0.78rem; color:var(--text-secondary); margin-top:4px; line-height:1.5; }
.ts-input-bar { display:flex; gap:8px; padding:14px 20px; border-top:1px solid var(--border-light); flex-shrink:0; }
.ts-input-bar input { flex:1; padding:10px 14px; border:1px solid var(--border-light); border-radius:20px; font-size:0.78rem; outline:none; color:var(--text-primary); }
.ts-input-bar input:focus { border-color:var(--accent); }
.ts-input-bar button { padding:10px 18px; background:var(--accent); color:#fff; border:none; border-radius:20px; font-weight:600; cursor:pointer; font-size:0.76rem; }
.ts-input-bar button:disabled { opacity:0.4; cursor:default; }

/* 撰写浮层 */
.compose-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); z-index:200; display:flex; align-items:center; justify-content:center; }
.compose-sheet { background:var(--bg-card); border-radius:var(--radius-lg); width:560px; max-height:85vh; display:flex; flex-direction:column; box-shadow:0 24px 80px rgba(0,0,0,0.18); border:1px solid var(--border-light); }
.cs-head { display:flex; align-items:center; justify-content:space-between; padding:16px 24px; border-bottom:1px solid var(--divider); flex-shrink:0; }
.cs-head button { background:none; border:none; cursor:pointer; font-size:0.8rem; }
.cs-head button:first-child { color:var(--text-muted); }
.cs-head h2 { font-size:0.95rem; font-weight:700; color:var(--text-primary); }
.cs-submit { color:var(--accent) !important; font-weight:700 !important; background:var(--bg-tag) !important; padding:7px 18px !important; border-radius:18px !important; transition:all 0.2s; }
.cs-submit:hover { background:var(--accent) !important; color:#fff !important; }
.cs-body { flex:1; overflow-y:auto; padding:24px; display:flex; flex-direction:column; gap:16px; }
.cs-title-input { width:100%; padding:12px 0; border:none; border-bottom:2px solid var(--border-light); font-size:1.3rem; font-weight:700; color:var(--text-primary); outline:none; background:transparent; transition:border-color 0.2s; }
.cs-title-input:focus { border-bottom-color:var(--accent); }
.cs-title-input::placeholder { color:#ccc; font-weight:400; font-size:1rem; }
.cs-textarea { width:100%; border:none; outline:none; font-size:0.88rem; color:var(--text-primary); line-height:1.8; resize:none; background:transparent; }
.cs-textarea::placeholder { color:#ccc; }
.cs-options { padding-top:4px; border-top:1px solid var(--divider); }
.cs-check { display:flex; align-items:center; gap:6px; font-size:0.8rem; color:var(--text-secondary); cursor:pointer; }
.cs-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.cs-field { display:flex; flex-direction:column; gap:6px; }
.cs-field label { font-size:0.68rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
.cs-field select { padding:10px 12px; border:1px solid var(--border-light); border-radius:10px; font-size:0.8rem; color:var(--text-primary); background:var(--bg-card); outline:none; cursor:pointer; }
.cs-field select:focus { border-color:var(--accent); }
.fade-enter-active, .fade-leave-active { transition:opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity:0; }

/* ====== 课程资料 ====== */
.resource-layout { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.res-topbar { display:flex; align-items:center; justify-content:space-between; padding:24px 32px 16px; flex-shrink:0; }
.ft-left { display:flex; align-items:baseline; gap:10px; }
.ft-count { font-size:0.76rem; color:var(--text-muted); }
.ft-right { display:flex; align-items:center; gap:10px; }
.ft-search { display:flex; align-items:center; gap:6px; padding:8px 14px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:20px; }
.ft-search input { border:none; outline:none; background:transparent; font-size:0.76rem; width:160px; color:var(--text-primary); }
.res-upload-btn { display:flex; align-items:center; gap:6px; padding:8px 18px; border:1.5px solid #526e5a; background:transparent; color:#526e5a; border-radius:20px; font-size:0.76rem; font-weight:600; cursor:pointer; transition:all 0.2s; font-family:inherit; }
.res-upload-btn:hover { background:#526e5a; color:#fff; }

.res-bar { display:flex; align-items:center; gap:16px; padding:0 32px 16px; flex-shrink:0; }
.res-filters { display:flex; gap:2px; background:var(--bg-tag); padding:3px; border-radius:20px; }
.res-filters span { padding:6px 14px; border-radius:18px; font-size:0.72rem; color:var(--text-muted); cursor:pointer; transition:all 0.2s; white-space:nowrap; }
.res-filters span:hover { color:var(--text-primary); }
.res-filters span.on { background:var(--bg-card); color:#526e5a; font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,0.05); }
.res-dropstrip { flex:1; display:flex; align-items:center; justify-content:center; gap:8px; padding:10px 16px; border:1px dashed var(--border-light); border-radius:8px; color:var(--text-muted); font-size:0.72rem; transition:all 0.2s; cursor:default; }
.res-dropstrip svg { flex-shrink:0; }
.res-dropstrip:hover { border-color:#526e5a; color:#526e5a; }
.res-dropstrip.hovering { border-color:#526e5a; background:rgba(82,110,90,0.04); color:#526e5a; }

/* 文件表格 */
.res-table-wrap { flex:1; overflow-y:auto; padding:0 32px 24px; }
.res-table { border:1px solid var(--border-light); border-radius:var(--radius-md); overflow:hidden; }
.rt-row { display:grid; grid-template-columns:1fr 160px 100px 110px 80px; align-items:center; padding:0 16px; transition:background 0.15s; }
.rt-row:not(.rt-head) { border-top:1px solid var(--divider); min-height:48px; }
.rt-row:not(.rt-head):hover { background:var(--bg-soft); }
.rt-head { height:38px; }
.rt-head .rt-cell { font-size:0.66rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
.rt-cell { font-size:0.78rem; color:var(--text-primary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rt-name { display:flex; align-items:center; gap:10px; }
.rt-icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; border:1px solid var(--border-light); color:var(--text-secondary); }
.rt-icon.pdf { color:#526e5a; border-color:#526e5a; }
.rt-icon.video { color:#526e5a; border-color:#526e5a; }
.rt-icon.image { color:#526e5a; border-color:#526e5a; }
.rt-icon.other { color:#526e5a; border-color:#526e5a; }
.rt-fname { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rt-course { color:var(--text-secondary); }
.rt-size { color:var(--text-muted); font-size:0.74rem; }
.rt-date { color:var(--text-muted); font-size:0.74rem; }
.rt-act { display:flex; gap:6px; justify-content:flex-end; }
.rt-act button { width:30px; height:30px; border-radius:6px; border:1px solid var(--border-light); background:transparent; color:var(--text-muted); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.15s; }
.rt-act button:hover { border-color:#526e5a; color:#526e5a; }
.rt-empty { grid-column:1/-1; text-align:center; padding:48px 0; color:var(--text-muted); font-size:0.78rem; border-top:1px solid var(--divider); }

/* ====== 共享 ====== */
.mf-field { display:flex; flex-direction:column; gap:6px; }
.mf-field label { font-size:0.68rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
.mf-field input, .mf-field select, .mf-field textarea { padding:9px 12px; border:1px solid var(--border-light); border-radius:10px; font-size:0.8rem; color:var(--text-primary); background:var(--bg-card); outline:none; resize:vertical; }
.mf-field input:focus, .mf-field select:focus, .mf-field textarea:focus { border-color:var(--accent); }
.btn-cancel { padding:9px 20px; border-radius:24px; border:1px solid var(--border-light); background:var(--bg-card); color:var(--text-secondary); font-size:0.78rem; cursor:pointer; }
.btn-primary { padding:9px 20px; border-radius:24px; background:var(--accent); color:#fff; border:none; font-size:0.78rem; font-weight:600; cursor:pointer; }
.btn-primary:hover { opacity:0.85; }
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-panel { background:var(--bg-card); border-radius:var(--radius-lg); padding:24px; width:480px; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.2); border:1px solid var(--border-light); }
.modal-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.modal-header h3 { font-size:0.95rem; font-weight:700; color:var(--text-primary); }
.modal-close { background:none; border:none; color:var(--text-muted); cursor:pointer; padding:4px; border-radius:6px; }
.modal-body { display:flex; flex-direction:column; gap:14px; }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; padding-top:16px; border-top:1px solid var(--border-light); }
.upload-area { border:2px dashed var(--border-light); border-radius:12px; padding:28px; text-align:center; color:var(--text-muted); }
.upload-area p { margin-top:8px; font-size:0.8rem; }
</style>
