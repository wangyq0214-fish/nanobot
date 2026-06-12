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
  // ===== Student pages (standalone) =====
  {
    path: '/student/learning-path',
    name: 'LearningPath',
    component: () => import('../pages/student/LearningPath.vue'),
  },
  {
    path: '/student/formula-derivation',
    name: 'FormulaDerivation',
    component: () => import('../pages/student/FormulaDerivation.vue'),
  },
  {
    path: '/student/tutoring-assistant',
    name: 'TutoringAssistant',
    component: () => import('../pages/student/TutoringAssistant.vue'),
  },
  {
    path: '/student/courses',
    name: 'StudentCourses',
    component: () => import('../pages/student/StudentCourses.vue'),
  },
  {
    path: '/student/courses/:courseId',
    name: 'StudentCourseDetail',
    component: () => import('../pages/student/StudentCourseDetail.vue'),
  },
  // ===== Researcher pages =====
  {
    path: '/researcher/hotspot',
    name: 'ResearchHotspot',
    component: () => import('../pages/researcher/ResearchHotspot.vue'),
  },
  {
    path: '/researcher/paper-search',
    name: 'PaperSearch',
    component: () => import('../pages/researcher/PaperSearch.vue'),
  },
  {
    path: '/researcher/paper-library',
    name: 'PaperLibrary',
    component: () => import('../pages/researcher/PaperLibrary.vue'),
  },
  {
    path: '/researcher/writing-assistant',
    name: 'WritingAssistant',
    component: () => import('../pages/researcher/WritingAssistant.vue'),
  },
  {
    path: '/researcher/datalab',
    name: 'DataLab',
    component: () => import('../pages/researcher/DataLab.vue'),
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
    const roleHome = { student: '/student/learning-path', researcher: '/researcher/hotspot' }
    return roleHome[user.role] || '/login'
  }
  if (to.path.startsWith('/student') && user.role !== 'student') {
    const roleHome = { teacher: '/teacher/lesson-plan', researcher: '/researcher/hotspot' }
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
