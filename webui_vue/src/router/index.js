import { createRouter, createWebHistory } from 'vue-router'
import { useGateway } from '../composables/useGateway.js'
import { useAuth } from '../composables/useAuth.js'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/Login.vue'),
  },
  // ===== Teacher pages (shared nav layout) =====
  {
    path: '/teacher',
    component: () => import('../layouts/TeacherLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/teacher/lesson-plan',
      },
      {
        path: 'lesson-plan',
        name: 'LessonPlan',
        component: () => import('../pages/teacher/LessonPlan.vue'),
      },
      {
        path: 'exam',
        name: 'ExamAssessment',
        component: () => import('../pages/teacher/HomeworkGrading.vue'),
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('../pages/teacher/AnalyticsDashboard.vue'),
      },
      {
        path: 'courses',
        name: 'TeacherCourses',
        component: () => import('../pages/teacher/Courses.vue'),
      },
      {
        path: 'courses/:courseId',
        name: 'TeacherCourseDetail',
        component: () => import('../pages/teacher/CourseDetail.vue'),
      },
      {
        path: 'courses/:courseId/analytics/:studentId',
        name: 'StudentAnalytics',
        component: () => import('../pages/teacher/StudentAnalytics.vue'),
      },
    ],
  },
  // ===== Student pages (shared sidebar layout) =====
  {
    path: '/student',
    component: () => import('../layouts/StudentLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/student/learning-path',
      },
      {
        path: 'learning-path',
        name: 'LearningPath',
        component: () => import('../pages/student/LearningPath.vue'),
      },
      {
        path: 'formula-derivation',
        name: 'FormulaDerivation',
        component: () => import('../pages/student/FormulaDerivation.vue'),
      },
      {
        path: 'tutoring-assistant',
        name: 'TutoringAssistant',
        component: () => import('../pages/student/TutoringAssistant.vue'),
      },
      {
        path: 'courses',
        name: 'StudentCourses',
        component: () => import('../pages/student/StudentCourses.vue'),
      },
      {
        path: 'courses/:courseId',
        name: 'StudentCourseDetail',
        component: () => import('../pages/student/StudentCourseDetail.vue'),
      },
      {
        path: 'courses/:courseId/homework/:hwId',
        name: 'HomeworkAnswer',
        component: () => import('../pages/student/HomeworkAnswer.vue'),
      },
      {
        path: 'my-resources',
        name: 'MyResources',
        component: () => import('../pages/student/MyResources.vue'),
      },
    ],
  },
  // ===== Researcher pages (shared nav layout) =====
  {
    path: '/researcher',
    component: () => import('../layouts/ResearcherLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/researcher/workspace',
      },
      {
        path: 'workspace',
        name: 'ResearcherWorkspace',
        component: () => import('../pages/researcher/Workspace.vue'),
      },
      {
        path: 'figure-studio',
        name: 'FigureStudio',
        component: () => import('../pages/researcher/FigureStudio.vue'),
      },
      {
        path: 'results',
        name: 'ResearchResults',
        component: () => import('../pages/researcher/ResearchResults.vue'),
      },
      {
        path: 'materials',
        name: 'ResearcherMaterials',
        component: () => import('../pages/researcher/Materials.vue'),
      },
      {
        path: 'projects',
        name: 'ResearcherProjects',
        component: () => import('../pages/researcher/CourseRadar.vue'),
      },
      {
        path: 'artifacts',
        name: 'ArtifactCenter',
        component: () => import('../pages/researcher/ArtifactCenter.vue'),
      },
      {
        path: 'create-artifact',
        name: 'CreateArtifact',
        component: () => import('../pages/researcher/CreateArtifact.vue'),
      },
      {
        path: 'agents',
        name: 'AgentMatrix',
        component: () => import('../pages/researcher/AgentMatrix.vue'),
      },
      {
        path: 'paper-search',
        name: 'PaperSearch',
        component: () => import('../pages/researcher/PaperSearch.vue'),
      },
      {
        path: 'paper-library',
        name: 'PaperLibrary',
        component: () => import('../pages/researcher/PaperLibrary.vue'),
      },
      {
        path: 'paper/:id',
        name: 'PaperWorkspace',
        component: () => import('../pages/researcher/PaperWorkspace.vue'),
      },
      {
        path: 'writing-assistant',
        name: 'WritingAssistant',
        component: () => import('../pages/researcher/WritingAssistant.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard — check login + role-based access
router.beforeEach(async (to) => {
  if (to.path === '/login') return true
  let user = null
  try {
    const raw = localStorage.getItem('nanobot-webui.user')
    if (raw) user = JSON.parse(raw)
  } catch { /* fall through */ }
  if (!user?.userId) return '/login'
  // Role-based: teacher pages only for teachers, student pages only for students, etc.
  if (to.path.startsWith('/teacher') && user.role !== 'teacher') {
    const roleHome = { student: '/student/learning-path', researcher: '/researcher/workspace' }
    return roleHome[user.role] || '/login'
  }
  if (to.path.startsWith('/student') && user.role !== 'student') {
    const roleHome = { teacher: '/teacher/lesson-plan', researcher: '/researcher/workspace' }
    return roleHome[user.role] || '/login'
  }
  if (to.path.startsWith('/researcher') && user.role !== 'researcher') {
    const roleHome = { teacher: '/teacher/lesson-plan', student: '/student/learning-path' }
    return roleHome[user.role] || '/login'
  }

  // Ensure gateway connection is established before navigating to protected pages
  const { connected, connect } = useGateway()
  if (!connected.value) {
    try {
      await connect({ role: user.role, userId: user.userId })
    } catch (e) {
      console.error('[router] Gateway connection failed:', e.message)
      // Don't block navigation, let the page handle the connection error
    }
  }

  return true
})

export default router
