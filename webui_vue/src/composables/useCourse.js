/**
 * Course management — CRUD, join, lessons, homework, submissions.
 */

import { ref } from 'vue'

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
      credentials: 'same-origin', headers: _authHeaders(token),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
  async function _mutate(url, data, role, userId, token) {
    const params = _authParams(role, userId, token)
    params.set('data', encodeURIComponent(JSON.stringify(data)))
    const res = await fetch(`${url}?${params.toString()}`, {
      credentials: 'same-origin', headers: _authHeaders(token),
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

  // --- Homework ---

  async function fetchHomeworkList(courseId, token) {
    const data = await _get(`/api/courses/${courseId}/homework`, null, null, token)
    homeworkList.value = data.homework || []
    return data.homework || []
  }

  async function createHomework(courseId, data, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/create`, data, role, userId, token)
  }

  async function fetchHomeworkDetail(courseId, hwId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}`, null, null, token)
    return data.homework
  }

  async function submitHomework(courseId, hwId, answers, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/submit`, { answers }, role, userId, token)
  }

  async function fetchSubmissions(courseId, hwId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}/submissions`, null, null, token)
    return data.submissions || []
  }

  async function fetchSubmissionDetail(courseId, hwId, studentId, token) {
    const data = await _get(`/api/courses/${courseId}/homework/${hwId}/submissions/${studentId}`, null, null, token)
    return data.submission
  }

  async function gradeSubmission(courseId, hwId, studentId, score, feedback, role, userId, token) {
    return _mutate(`/api/courses/${courseId}/homework/${hwId}/grade`, { studentId, score, feedback }, role, userId, token)
  }

  return {
    courses, currentCourse, members, lessons, homeworkList,
    fetchCourses, createCourse, joinCourse, fetchCourseDetail,
    fetchMembers, fetchLessons, fetchLessonDetail,
    fetchHomeworkList, createHomework, fetchHomeworkDetail,
    submitHomework, fetchSubmissions, fetchSubmissionDetail, gradeSubmission,
  }
}
