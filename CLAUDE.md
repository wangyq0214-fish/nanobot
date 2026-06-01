# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作提供指导。

## 项目概述

**nanobot** 是一个 AI 教育平台，包含 Python 后端（WebSocket 网关 + REST API）和 Vue.js 前端。前端位于 `webui_vue/`，支持三种角色：教师、学生、研究员。

## 开发命令

### 前端 (webui_vue/)
```bash
cd webui_vue && npm install    # 安装依赖
npm run dev                    # 开发服务器 (Vite, 默认 http://localhost:5173)
npm run build                  # 生产构建
```

### 后端 (nanobot/)
```bash
pip install -e ".[dev]"        # 安装开发依赖
pytest                         # 运行所有测试
ruff check nanobot/            # 代码检查
```

## WebUI Vue 架构

### 技术栈

Vue 3 (Composition API) + Vue Router + Vite + ECharts + KaTeX

### 目录结构

```
webui_vue/src/
├── main.js                         # 入口，挂载 Vue app + router
├── App.vue                         # 根组件，<router-view>
├── router/index.js                 # 路由配置 + 权限守卫
├── composables/                    # 组合式函数（状态 + 逻辑）
│   ├── useAuth.js                  # 登录/登出、角色、localStorage 持久化
│   ├── useGateway.js               # WebSocket 连接、消息收发、AI 评分
│   ├── useCourse.js                # 课程/作业/题库 CRUD + AI 批改
│   ├── useLessonPlan.js            # 教案 CRUD
│   ├── useSessions.js              # 会话列表管理
│   ├── useSource.js                # 源文件浏览/保存
│   └── useBoardArt.js              # 黑板艺术生成
├── components/                     # 可复用 UI 组件
│   ├── TeacherNav.vue              # 教师侧边导航
│   ├── StudentNav.vue              # 学生侧边导航
│   ├── ResearcherNav.vue           # 研究员侧边导航
│   ├── CreateHomeworkDialog.vue    # 创建作业弹窗
│   ├── QuestionBankDialog.vue      # 题库管理弹窗
│   ├── MarkdownSection.vue         # Markdown 渲染（支持 KaTeX）
│   ├── SectionItem.vue             # 通用段落条目
│   └── Lesson*.vue                 # 教案各板块组件
├── pages/
│   ├── Login.vue                   # 登录页（角色选择）
│   ├── teacher/
│   │   ├── Courses.vue             # 课程列表
│   │   ├── CourseDetail.vue        # 课程详情（课时/作业/成员）
│   │   ├── HomeworkGrading.vue     # 作业批改（AI 辅助）
│   │   ├── LessonPlan.vue          # 教案编辑
│   │   ├── AnalyticsDashboard.vue  # 学情分析仪表盘
│   │   └── StudentAnalytics.vue    # 单个学生学情
│   ├── student/
│   │   ├── StudentCourses.vue      # 学生课程列表
│   │   ├── StudentCourseDetail.vue # 课程详情 + 答题
│   │   ├── LearningPath.vue        # 学习路径
│   │   ├── FormulaDerivation.vue   # 公式推导
│   │   ├── TutoringAssistant.vue   # AI 辅导助手
│   │   └── StudentDashboard.vue    # 学生仪表盘
│   └── researcher/
│       ├── ResearchHotspot.vue     # 研究热点
│       ├── WritingAssistant.vue    # 写作助手
│       └── DataLab.vue             # 数据实验室
├── layouts/
│   └── TeacherLayout.vue           # 教师页面布局（侧边栏 + router-view）
└── analytics.js / homework.js / student.js  # 独立工具模块
```

### 核心设计模式

**Composable 模式**：所有状态和业务逻辑封装在 `composables/` 中，通过 `ref()` 实现跨组件共享。每个 composable 导出一个函数，返回响应式状态和操作方法。

```javascript
// 典型用法
import { useCourse } from '../composables/useCourse.js'
const { courses, fetchCourses, createCourse } = useCourse()
```

**关键 Composable 接口**：

| Composable | 导出状态 | 主要方法 |
|-----------|---------|---------|
| `useAuth` | `user`, `isLoggedIn` | `login(u)`, `logout()`, `getToken()` |
| `useGateway` | `connected`, `connectionError` | `connect({role, userId})`, `send(content)`, `aiGradeQuestion(...)`, `aiGenerateQuestions(...)`, `onChat(cb)` |
| `useCourse` | `courses`, `currentCourse`, `members`, `lessons`, `homeworkList` | `fetchCourses()`, `createCourse(...)`, `joinCourse(...)`, `fetchHomework(...)`, `submitHomework(...)`, `aiGradeSubmission(...)` |
| `useLessonPlan` | `lessonPlan`, `sections` | `fetchPlan()`, `savePlan()`, `generateSection(...)` |
| `useSource` | `files`, `currentFile` | `fetchFiles()`, `saveFile(...)` |

**Gateway 通信模式**：
- HTTP API：`fetch('/api/...?role=&user_id=&token=')` — 用于 CRUD 操作
- WebSocket：`useGateway().send()` — 用于实时消息和 AI 交互
- AI 评分/生成通过 WS envelope 的 `ai_grade_question` / `ai_grade_submission` / `ai_generate_questions` 类型

**认证流程**：
1. `POST /api/users/register` 注册 → `POST /api/users/validate` 验证
2. `GET /webui/bootstrap` 获取 token + ws_path
3. WebSocket 连接到 `ws://host:port/ws?token=xxx`
4. 所有 HTTP 请求携带 `role`, `user_id`, `token` 查询参数

**路由守卫**（`router/index.js`）：
- 未登录 → 重定向 `/login`
- 角色不匹配 → 重定向到对应角色首页
- 进入受保护页面前自动建立 Gateway 连接

### 添加新页面的流程

1. 在 `pages/` 对应角色目录下创建 `.vue` 文件
2. 在 `router/index.js` 添加路由条目（教师页面加到 `TeacherLayout` children 中）
3. 如需新状态/逻辑，在 `composables/` 中创建或扩展现有 composable
4. 如需新 API，在后端 `nanobot/api/handlers/` 添加 handler 并在 `websocket.py` 的 router 中注册

### 代码风格

- Vue 3 Composition API（`<script setup>` 或 `setup()` 函数）
- 组件文件名 PascalCase（`TeacherNav.vue`），composable 文件名 camelCase（`useCourse.js`）
- 响应式状态用 `ref()`，复杂对象可用 `reactive()`
- 异步操作用 `async/await`，错误处理用 `try/catch`
- CSS 用 `<style scoped>` 避免全局污染

## 后端架构概览

```
WebSocket 请求 → _dispatch_http() → Router → handlers/ → StorageWrapper → 存储后端
WS envelope    → _dispatch_envelope() → ws_handlers.py → storage / ai_grade
```

### 后端 API 模块 (nanobot/api/)

| 模块 | 职责 |
|------|------|
| `router.py` | 声明式 HTTP 路由表（正则匹配 + 参数注入） |
| `auth.py` | AuthManager — token 管理、用户注册/验证、workspace 创建 |
| `utils.py` | HTTP 工具函数（JSON 响应、错误响应、路径解析） |
| `ws_handlers.py` | WS envelope 处理（消息、AI 评分、文件保存） |
| `handlers/courses.py` | 课程 CRUD |
| `handlers/lessons.py` | 课时管理 |
| `handlers/homework.py` | 作业 CRUD + 提交 |
| `handlers/grading.py` | 批改、AI 批改、发布、删除 |
| `handlers/question_bank.py` | 题库管理 |
| `ai_grade.py` | AI 评分逻辑（调用 LLM） |
| `ai_generate_questions.py` | AI 题目生成 |

### 后端代码风格

- Python 3.11+，行宽 100，`ruff` 检查
- 异步优先（`asyncio`），测试用 `asyncio_mode = "auto"`
- 优先小而专注的改动，避免过度抽象

## 分支策略

| 变更类型 | 目标分支 |
|---------|---------|
| 新功能 / 重构 | `nightly` |
| Bug 修复 / 文档 | `main` |
