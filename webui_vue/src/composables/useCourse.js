/**
 * Course management — CRUD, join, lessons, homework, submissions.
 */

import { ref } from 'vue'
import { useGateway } from './useGateway.js'
import { useAuthFetch } from './useAuthFetch.js'

const courses = ref([])
const currentCourse = ref(null)
const members = ref([])
const lessons = ref([])
const homeworkList = ref([])

export function useCourse() {
  const { authGet, authMutate } = useAuthFetch()

  // --- Course CRUD ---

  async function fetchCourses() {
    const data = await authGet('/api/courses')
    courses.value = data.courses || []
    return data.courses || []
  }

  async function createCourse(data) {
    return authMutate('/api/courses/create', data)
  }

  async function joinCourse(joinCode, displayName) {
    return authMutate('/api/courses/join', { joinCode, displayName })
  }

  async function fetchCourseDetail(courseId) {
    const data = await authGet(`/api/courses/${courseId}`)
    currentCourse.value = data.course || null
    return data.course
  }

  // --- Members ---

  async function fetchMembers(courseId) {
    const data = await authGet(`/api/courses/${courseId}/members`)
    members.value = data.members || []
    return data.members || []
  }

  // --- Lessons ---

  async function fetchLessons(courseId) {
    const data = await authGet(`/api/courses/${courseId}/lessons`)
    lessons.value = data.lessons || []
    return data.lessons || []
  }

  async function fetchLessonDetail(courseId, lessonId) {
    const data = await authGet(`/api/courses/${courseId}/lessons/${lessonId}`)
    return data.lesson
  }

  // --- Normalize helpers (snake_case → camelCase) ---
  function _normHomework(hw) {
    if (!hw) return hw
    return {
      hwId: hw.hwId || hw.hw_id || '',
      courseId: hw.courseId || hw.course_id || '',
      title: hw.title || '',
      description: hw.description || '',
      totalPoints: hw.totalPoints ?? hw.total_points ?? 0,
      deadline: hw.deadline || '',
      createdBy: hw.createdBy || hw.created_by || '',
      status: hw.status || 'draft',
      questions: hw.questions || [],
      settings: hw.settings || {},
      createdAt: hw.createdAt || hw.created_at || '',
    }
  }
  function _normSubmission(s) {
    if (!s) return s
    return {
      id: s.id,
      hwId: s.hwId || s.hw_id || '',
      studentId: s.studentId || s.student_id || '',
      studentName: s.studentName || s.student_name || s.studentId || s.student_id || '',
      studentRole: s.studentRole || s.student_role || '',
      courseId: s.courseId || s.course_id || '',
      attemptNumber: s.attemptNumber ?? s.attempt_number ?? 1,
      answers: s.answers || {},
      status: s.status || 'submitted',
      score: s.score ?? 0,
      feedback: s.feedback || {},
      submittedAt: s.submittedAt || s.submitted_at || '',
      gradedAt: s.gradedAt || s.graded_at || null,
      gradedBy: s.gradedBy || s.graded_by || null,
    }
  }

  // --- Homework ---

  async function fetchHomeworkList(courseId) {
    const data = await authGet(`/api/courses/${courseId}/homework`)
    const list = (data.homework || []).map(_normHomework)
    homeworkList.value = list
    return list
  }

  async function createHomework(courseId, data) {
    const { sendCreateHomework } = useGateway()
    return sendCreateHomework(courseId, data)
  }

  async function fetchHomeworkDetail(courseId, hwId) {
    const data = await authGet(`/api/courses/${courseId}/homework/${hwId}`)
    return _normHomework(data.homework)
  }

  async function submitHomework(courseId, hwId, answers) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/submit`, { answers })
  }

  async function fetchSubmissions(courseId, hwId) {
    const data = await authGet(`/api/courses/${courseId}/homework/${hwId}/submissions`)
    return (data.submissions || []).map(_normSubmission)
  }

  async function fetchSubmissionDetail(courseId, hwId, studentId) {
    const data = await authGet(`/api/courses/${courseId}/homework/${hwId}/submissions/${studentId}`)
    return _normSubmission(data.submission)
  }

  async function gradeSubmission(courseId, hwId, studentId, score, feedback, questions) {
    const data = { studentId, score, feedback }
    if (questions) data.questions = questions
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/grade`, data)
  }

  async function aiGradeSubmission(courseId, hwId, studentId) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade`, { studentId })
  }

  async function aiGradeCropGpt(courseId, hwId, studentId) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade-cropgpt`, { studentId })
  }

  async function aiGradeGeneral(courseId, hwId, studentId) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade-general`, { studentId })
  }

  async function aiGradeQuestion(courseId, hwId, questionData) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade-question`, questionData)
  }

  async function deleteHomework(courseId, hwId) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/delete`, {})
  }

  async function publishHomework(courseId, hwId) {
    return authMutate(`/api/courses/${courseId}/homework/${hwId}/publish`, {})
  }

  async function aiGenerateQuestions(courseId, content, numQuestions, typeDistribution) {
    return authMutate(`/api/courses/${courseId}/ai-generate-questions`, {
      content,
      numQuestions,
      typeDistribution,
    })
  }

  // --- Question Bank ---

  async function fetchQuestionBank(courseId, type = null) {
    let url = `/api/courses/${courseId}/question-bank`
    if (type) url += `?type=${type}`
    const data = await authGet(url)
    return data.questions || []
  }

  async function addToQuestionBank(courseId, question) {
    return authMutate(`/api/courses/${courseId}/question-bank/add`, question)
  }

  async function batchAddToQuestionBank(courseId, questions) {
    return authMutate(`/api/courses/${courseId}/question-bank/batch-add`, { questions })
  }

  async function deleteFromQuestionBank(courseId, questionId) {
    return authMutate(`/api/courses/${courseId}/question-bank/${questionId}/delete`, {})
  }

  async function updateQuestionBank(courseId, questionId, data) {
    return authMutate(`/api/courses/${courseId}/question-bank/${questionId}/update`, data)
  }

  // --- Resources ---
  async function fetchResources(courseId, type = null) {
    let url = `/api/courses/${courseId}/resources`
    if (type) url += `?type=${type}`
    const data = await authGet(url)
    return data.resources || []
  }

  async function createResource(courseId, resourceData) {
    return authMutate(`/api/courses/${courseId}/resources/create`, resourceData)
  }

  async function deleteResource(courseId, resourceId) {
    return authMutate(`/api/courses/${courseId}/resources/${resourceId}/delete`, {})
  }

  // --- Notifications ---
  async function fetchNotifications() {
    const data = await authGet('/api/notifications')
    return data.notifications || []
  }

  async function createNotification(data) {
    return authMutate('/api/notifications/create', data)
  }

  // --- Discussions ---
  async function fetchDiscussions() {
    const data = await authGet('/api/discussions')
    return data.discussions || []
  }

  async function createDiscussion(data) {
    return authMutate('/api/discussions/create', data)
  }

  async function replyDiscussion(discussionId, text) {
    return authMutate(`/api/discussions/${discussionId}/reply`, { text })
  }

  return {
    courses, currentCourse, members, lessons, homeworkList,
    fetchCourses, createCourse, joinCourse, fetchCourseDetail,
    fetchMembers, fetchLessons, fetchLessonDetail,
    fetchHomeworkList, createHomework, fetchHomeworkDetail,
    submitHomework, fetchSubmissions, fetchSubmissionDetail, gradeSubmission, aiGradeSubmission,
    aiGradeCropGpt, aiGradeGeneral, aiGradeQuestion, deleteHomework,
    publishHomework, aiGenerateQuestions,
    fetchQuestionBank, addToQuestionBank, batchAddToQuestionBank, deleteFromQuestionBank, updateQuestionBank,
    fetchResources, createResource, deleteResource,
    fetchNotifications, createNotification,
    fetchDiscussions, createDiscussion, replyDiscussion,
  }
}
