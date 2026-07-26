/**
 * Composable for managing researcher saved AI outputs.
 *
 * Provides CRUD operations for research results saved from workspace chat.
 */

import { ref } from 'vue'
import { useAuthFetch } from './useAuthFetch.js'
import { useGateway } from './useGateway.js'

const results = ref([])
const loading = ref(false)
const currentResult = ref(null)

export function useResearchResults() {
  const { authGet, authMutate } = useAuthFetch()
  const { sendSaveResearchResult } = useGateway()

  /**
   * Fetch all research results for the current user.
   */
  async function fetchResults() {
    loading.value = true
    try {
      const data = await authGet('/api/researcher/results')
      if (data?.ok) {
        results.value = data.data || []
      }
    } catch (err) {
      console.error('Failed to fetch research results:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single research result with full content.
   * @param {number} id - Result ID
   */
  async function fetchResult(id) {
    try {
      const data = await authGet(`/api/researcher/results/${id}`)
      if (data?.ok) {
        currentResult.value = data.data
        return data.data
      }
    } catch (err) {
      console.error('Failed to fetch research result:', err)
    }
    return null
  }

  /**
   * Save an AI message as a research result via WebSocket (supports long text).
   * @param {string} content - AI message content (Markdown)
   * @param {string} chatId - Current chat session ID
   * @param {string} sessionTitle - Optional session title
   * @returns {Promise<object|null>} Created result or null
   */
  async function saveResult(contentOrPayload, chatId, sessionTitle = '') {
    try {
      const payload = typeof contentOrPayload === 'object' && contentOrPayload !== null
        ? contentOrPayload
        : { content: contentOrPayload, chat_id: chatId, session_title: sessionTitle }
      const { result } = await sendSaveResearchResult(payload)
      if (result) {
        // Prepend to list
        results.value.unshift(result)
        return result
      }
    } catch (err) {
      console.error('Failed to save research result:', err)
    }
    return null
  }

  /**
   * Delete a research result.
   * @param {number} id - Result ID
   */
  async function deleteResult(id) {
    try {
      await authMutate(`/api/researcher/results/${id}/delete`, {})
      results.value = results.value.filter(r => r.id !== id)
      if (currentResult.value?.id === id) {
        currentResult.value = null
      }
    } catch (err) {
      console.error('Failed to delete research result:', err)
    }
  }

  /**
   * Update a research result (title, tags).
   * @param {number} id - Result ID
   * @param {object} data - Fields to update
   */
  async function updateResult(id, data) {
    try {
      await authMutate(`/api/researcher/results/${id}/update`, data)
      // Update local state
      const idx = results.value.findIndex(r => r.id === id)
      if (idx >= 0) {
        Object.assign(results.value[idx], data)
      }
      if (currentResult.value?.id === id) {
        Object.assign(currentResult.value, data)
      }
    } catch (err) {
      console.error('Failed to update research result:', err)
    }
  }

  return {
    results,
    loading,
    currentResult,
    fetchResults,
    fetchResult,
    saveResult,
    deleteResult,
    updateResult,
  }
}
