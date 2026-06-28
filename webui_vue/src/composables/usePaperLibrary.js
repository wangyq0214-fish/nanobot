/**
 * Paper library management — CRUD for local papers, upload, favorites, tags.
 */

import { ref } from 'vue'
import { useGateway } from './useGateway.js'
import { useAuthFetch } from './useAuthFetch.js'

export function usePaperLibrary() {
  const loading = ref(false)
  const error = ref(null)
  const papers = ref([])
  const currentPaper = ref(null)
  const uploading = ref(false)
  const uploadProgress = ref(0)

  const { authGet, authMutate } = useAuthFetch()

  /**
   * Fetch all papers for the current user.
   */
  async function fetchPapers() {
    loading.value = true
    error.value = null
    try {
      const data = await authGet('/api/researcher/papers')
      papers.value = data.papers || []
      return papers.value
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] fetchPapers error:', e)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Upload a PDF file via WebSocket (avoids HTTP 431 from large base64 in URL).
   * @param {File} file - The PDF file to upload
   * @param {string} title - Optional title override
   */
  async function uploadPaper(file, title = '') {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      error.value = '请上传 PDF 文件'
      return null
    }

    uploading.value = true
    uploadProgress.value = 0
    error.value = null

    try {
      // Read file as base64
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result
          // Remove data:application/pdf;base64, prefix
          const base64Data = result.split(',')[1]
          resolve(base64Data)
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })

      uploadProgress.value = 30

      // Send via chunked WebSocket to avoid HTTP 431 and large frame issues
      const { sendUploadPaper } = useGateway()
      const result = await sendUploadPaper(base64, file.name, title || '')

      uploadProgress.value = 100

      // Add to local list
      if (result.paper) {
        papers.value = [result.paper, ...papers.value]
      }

      return result
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] uploadPaper error:', e)
      return null
    } finally {
      uploading.value = false
      setTimeout(() => { uploadProgress.value = 0 }, 1000)
    }
  }

  /**
   * Get paper detail by ID.
   */
  async function getPaperDetail(paperId) {
    loading.value = true
    error.value = null
    try {
      const data = await authGet(`/api/researcher/papers/${paperId}`)
      currentPaper.value = data.paper || null
      return currentPaper.value
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] getPaperDetail error:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a paper.
   */
  async function deletePaper(paperId) {
    error.value = null
    try {
      await authGet(`/api/researcher/papers/${paperId}/delete`)
      papers.value = papers.value.filter(p => p.id !== paperId)
      return true
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] deletePaper error:', e)
      return false
    }
  }

  /**
   * Toggle favorite status.
   */
  async function toggleFavorite(paperId) {
    error.value = null
    try {
      const data = await authGet(`/api/researcher/papers/${paperId}/favorite`)
      // Update local state
      const paper = papers.value.find(p => p.id === paperId)
      if (paper) {
        paper.isFavorite = data.isFavorite
      }
      return data.isFavorite
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] toggleFavorite error:', e)
      return null
    }
  }

  /**
   * Update paper tags.
   */
  async function updateTags(paperId, tags) {
    error.value = null
    try {
      const result = await authMutate(`/api/researcher/papers/${paperId}/tags`, { tags })
      // Update local state
      const paper = papers.value.find(p => p.id === paperId)
      if (paper) {
        paper.tags = result.tags
      }
      return result.tags
    } catch (e) {
      error.value = e.message
      console.error('[usePaperLibrary] updateTags error:', e)
      return null
    }
  }

  return {
    loading,
    error,
    papers,
    currentPaper,
    uploading,
    uploadProgress,
    fetchPapers,
    uploadPaper,
    getPaperDetail,
    deletePaper,
    toggleFavorite,
    updateTags,
  }
}
