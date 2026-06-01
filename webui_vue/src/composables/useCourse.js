/**
 * Course management — CRUD, join, lessons, homework, submissions.
 */

import { ref } from 'vue'
import { useGateway } from './useGateway.js'

const courses = ref([])
const currentCourse = ref(null)
const members = ref([])
const lessons = ref([])
const homeworkList = ref([])

export function useCourse() {

  // Helper: build query params with auth
  function _authParams(role, userId, token) {
    const params = new URLSearchParams()
    if (role) params.set('role', role)
    if (userId) params.set('user_id', userId)
    if (token) params.set('token', token)
    return params
  }
  function _authHeaders(token) {
    const h = {}
    if (token) h['Authorization'] = `Bearer ${token}`
    return h
  }
  async function _get(url, role, userId, token) {
    const params = _authParams(role, userId, token)
    const res = await fetch(`${url}?${params.toString()}`, {
      // Don't send cookies to reduce header size
      credentials: 'omit',
      headers: _authHeaders(token),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
  async function _mutate(url, data, role, userId, token) {
    const params = _authParams(role, userId, token)
    params.set('data', JSON.stringify(data))
    const res = await fetch(`${url}?${params.toString()}`, {
      // Don't send cookies to reduce header size
      credentials: 'omit',
      headers: _authHeaders(token),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || `HTTP ${res.status}`)
    }
    return res.json()
  }

  // --- Course CRUD ---

  async function fetchCourses(role, userId, token) {
    const data = await _get('/api/courses', role, userId, token)
    courses.value = data.courses || []
    return data.courses || []
  }

  async function createCourse(data, role, userId, token) {
    return _mutate('/api/courses/create', data, role, userId, token)
  }

  async function joinCourse(joinCode, displayName, role, userId, token) {
    return _mutate('/api/courses/join', { joinCode, displayName }, role, userId, token)
  }

  async function fetchCourseDetail(courseId, token) {
    const data = await _get(`/api/courses/${courseId}`, null, null, token)
    currentCourse.value = data.course || null
    return data.course
  }

  // --- Members ---

  async function fetchMembers(courseId, token) {
    const data = await _get(`/api/courses/${courseId}/members`, null, null, token)
    members.value = data.members || []
    return data.members || []
  }

  // --- Lessons ---

  async function fetchLessons(courseId, token) {
    const data = await _get(`/api/courses/${courseId}/lessons`, null, null, token)
    lessons.value = data.lessons || []
    return data.lessons || []
  }

  async function fetchLessonDetail(courseId, lessonId, token) {
    const data = await _get(`/api/courses/${courseId}/lessons/${lessonId}`, null, null, token)
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

  async function fetchHomeworkList(courseId, token) {
    const data = await _get(`/api/courses/${courseId}/homework`, null, null, token)
    const list = (data.homework || []).map(_normHomework)
    homeworkList.value = list
    return list
  }

  async function createHomework(courseId, data) {
    const { sendCreateHomework } = useGateway()
    return sendCreateHomework(courseId, data)
  }

  async function fetchHomeworkDetail(courseId, hwId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}`, null, null, token)
    return _normHomework(data.homework)
  }

  async function submitHomework(courseId, hwId, answers, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/submit`, { answers }, role, userId, token)
  }

  async function fetchSubmissions(courseId, hwId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}/submissions`, null, null, token)
    return (data.submissions || []).map(_normSubmission)
  }

  async function fetchSubmissionDetail(courseId, hwId, studentId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}/submissions/${studentId}`, null, null, token)
    return _normSubmission(data.submission)
  }

  async function gradeSubmission(courseId, hwId, studentId, score, feedback, role, userId, token, questions) {
    const data = { studentId, score, feedback }
    if (questions) data.questions = questions
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/grade`, data, role, userId, token)
  }

  async function aiGradeSubmission(courseId, hwId, studentId, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade`, { studentId }, role, userId, token)
  }

  async function aiGradeQuestion(courseId, hwId, questionData, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/ai-grade-question`, questionData, role, userId, token)
  }

  async function deleteHomework(courseId, hwId, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/delete`, {}, role, userId, token)
  }

  async function publishHomework(courseId, hwId, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/publish`, {}, role, userId, token)
  }

  async function aiGenerateQuestions(courseId, content, numQuestions, typeDistribution, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/ai-generate-questions`, {
      content,
      numQuestions,
      typeDistribution,
    }, role, userId, token)
  }

  // --- Question Bank ---

  async function fetchQuestionBank(courseId, token, type = null) {
    let url = `/api/courses/${courseId}/question-bank`
    if (type) url += `?type=${type}`
    const data = await _get(url, null, null, token)
    return data.questions || []
  }

  async function addToQuestionBank(courseId, question, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/question-bank/add`, question, role, userId, token)
  }

  async function batchAddToQuestionBank(courseId, questions, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/question-bank/batch-add`, { questions }, role, userId, token)
  }

  async function deleteFromQuestionBank(courseId, questionId, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/question-bank/${questionId}/delete`, {}, role, userId, token)
  }

  async function updateQuestionBank(courseId, questionId, data, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/question-bank/${questionId}/update`, data, role, userId, token)
  }

  return {
    courses, currentCourse, members, lessons, homeworkList,
    fetchCourses, createCourse, joinCourse, fetchCourseDetail,
    fetchMembers, fetchLessons, fetchLessonDetail,
    fetchHomeworkList, createHomework, fetchHomeworkDetail,
    submitHomework, fetchSubmissions, fetchSubmissionDetail, gradeSubmission, aiGradeSubmission, aiGradeQuestion, deleteHomework,
    publishHomework, aiGenerateQuestions,
    fetchQuestionBank, addToQuestionBank, batchAddToQuestionBank, deleteFromQuestionBank, updateQuestionBank,
  }
}
