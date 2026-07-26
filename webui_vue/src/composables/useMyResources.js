/**
 * Composable for managing student's personal resources (questions, files, notes) and categories.
 * Uses WebSocket messages for all mutations (backend websockets lib doesn't support POST).
 * Uses HTTP GET for read-only queries (GET works fine with websockets).
 */

import { ref } from 'vue'
import { useAuth } from './useAuth.js'
import { useGateway } from './useGateway.js'

export function useMyResources() {
  const { user } = useAuth()
  const {
    getToken,
    sendStudentResourceList, sendStudentResourceCreate, sendStudentResourceDelete,
    sendStudentResourceUpdate, sendStudentResourceCategorize,
    sendStudentCategoriesList, sendStudentCategoryCreate, sendStudentCategoryUpdate,
    sendStudentCategoryDelete,
  } = useGateway()

  const resources = ref([])
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)

  // ==================== Resource Operations ====================

  /**
   * Fetch all student resources via WebSocket
   * @param {string|null} type - Resource type filter: 'question', 'file', 'note'
   */
  async function fetchResources(type = null) {
    loading.value = true
    error.value = null
    try {
      const result = await sendStudentResourceList({ resourceType: type })
      resources.value = result.resources || []
      return resources.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new student resource
   */
  async function createResource(resourceData) {
    const result = await sendStudentResourceCreate({
      resourceType: resourceData.resource_type,
      title: resourceData.title,
      content: resourceData.content || '',
      sourceType: resourceData.source_type || 'manual',
      sourceId: resourceData.source_id || null,
      categoryId: resourceData.category_id || null,
      metadata: resourceData.metadata || {},
    })
    if (result.ok && result.resource) {
      resources.value.unshift(result.resource)
    }
    return result
  }

  /**
   * Favorite a question from course question bank
   */
  async function favoriteQuestion(courseId, questionId) {
    // Use HTTP GET to fetch the question details first, then create via WS
    const authQuery = `role=student&user_id=${user.value.userId}&token=${getToken()}`
    const res = await fetch(`/api/courses/${courseId}/question-bank?${authQuery}`)
    const data = await res.json()
    const questions = data.questions || []
    const question = questions.find(q => q.id === questionId || q.id === String(questionId))

    if (!question) {
      throw new Error('题目不存在')
    }

    // Check if already favorited
    const existing = resources.value.find(r =>
      r.resource_type === 'question' && r.source_id === String(questionId) && r.source_type === 'course'
    )
    if (existing) {
      return { ok: true, resource: existing, message: 'Already favorited' }
    }

    // Create via WebSocket
    return createResource({
      resource_type: 'question',
      title: (question.content || '').substring(0, 100),
      content: question.content || '',
      source_type: 'course',
      source_id: String(questionId),
      metadata: {
        course_id: courseId,
        question_type: question.questionType || question.question_type || '',
        options: question.options || [],
        answer: question.answer || '',
        explanation: question.explanation || '',
        tags: question.tags || [],
      },
    })
  }

  /**
   * Delete a student resource
   */
  async function deleteResource(resourceId) {
    const result = await sendStudentResourceDelete(resourceId)
    if (result.ok) {
      resources.value = resources.value.filter(r => r.id !== resourceId)
    }
    return result
  }

  /**
   * Update a student resource
   */
  async function updateResource(resourceId, updateData) {
    const result = await sendStudentResourceUpdate(resourceId, updateData)
    if (result.ok && result.resource) {
      const index = resources.value.findIndex(r => r.id === resourceId)
      if (index !== -1) {
        resources.value[index] = result.resource
      }
    }
    return result
  }

  /**
   * Upload a file to student resources
   * Note: File upload still uses HTTP POST via the existing upload endpoint
   */
  async function uploadFile(file) {
    const authQuery = `role=student&user_id=${user.value.userId}&token=${getToken()}`
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`/api/student/resources/upload?${authQuery}`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: formData
    })
    const data = await res.json()
    if (data.ok && data.resource) {
      resources.value.unshift(data.resource)
    }
    return data
  }

  /**
   * Get resources filtered by type
   */
  function getResourcesByType(type) {
    return resources.value.filter(r => r.resource_type === type)
  }

  /**
   * Search resources by title or content
   */
  function searchResources(keyword) {
    if (!keyword) return resources.value
    const lowerKeyword = keyword.toLowerCase()
    return resources.value.filter(r =>
      (r.title && r.title.toLowerCase().includes(lowerKeyword)) ||
      (r.content && r.content.toLowerCase().includes(lowerKeyword))
    )
  }

  // ==================== Category Operations ====================

  /**
   * Fetch all categories via WebSocket
   */
  async function fetchCategories() {
    try {
      const result = await sendStudentCategoriesList()
      categories.value = result.categories || []
      return categories.value
    } catch (err) {
      console.error('Failed to fetch categories:', err)
      throw err
    }
  }

  /**
   * Create a new category
   */
  async function createCategory(categoryData) {
    const result = await sendStudentCategoryCreate({
      name: categoryData.name,
      description: categoryData.description || '',
      color: categoryData.color || null,
    })
    if (result.ok && result.category) {
      categories.value.push(result.category)
    }
    return result
  }

  /**
   * Update a category
   */
  async function updateCategory(categoryId, updateData) {
    const result = await sendStudentCategoryUpdate(categoryId, updateData)
    if (result.ok && result.category) {
      const index = categories.value.findIndex(c => c.id === categoryId)
      if (index !== -1) {
        categories.value[index] = result.category
      }
    }
    return result
  }

  /**
   * Delete a category
   */
  async function deleteCategory(categoryId) {
    const result = await sendStudentCategoryDelete(categoryId)
    if (result.ok) {
      categories.value = categories.value.filter(c => c.id !== categoryId)
      // Update resources that were in this category
      resources.value.forEach(r => {
        if (r.category_id === categoryId) {
          r.category_id = null
        }
      })
    }
    return result
  }

  /**
   * Set category for a resource
   */
  async function categorizeResource(resourceId, categoryId) {
    const result = await sendStudentResourceCategorize(resourceId, categoryId)
    if (result.ok && result.resource) {
      const index = resources.value.findIndex(r => r.id === resourceId)
      if (index !== -1) {
        resources.value[index] = result.resource
      }
      // Refresh categories to update counts
      await fetchCategories()
    }
    return result
  }

  /**
   * Get resources filtered by category
   */
  function getResourcesByCategory(categoryId) {
    if (categoryId === null) {
      return resources.value.filter(r => r.resource_type === 'question' && !r.category_id)
    }
    return resources.value.filter(r => r.resource_type === 'question' && r.category_id === categoryId)
  }

  return {
    resources,
    categories,
    loading,
    error,
    fetchResources,
    createResource,
    favoriteQuestion,
    deleteResource,
    updateResource,
    uploadFile,
    getResourcesByType,
    searchResources,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    categorizeResource,
    getResourcesByCategory
  }
}
