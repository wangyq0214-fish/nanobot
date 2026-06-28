/**
 * Multi-source paper search — searches across Semantic Scholar, arXiv, CrossRef, OpenAlex.
 */

import { ref } from 'vue'
import { useAuthFetch } from './useAuthFetch.js'

export function usePaperSearch() {
  const loading = ref(false)
  const error = ref(null)
  const results = ref([])
  const total = ref(0)
  const importing = ref(false)

  const { authMutate } = useAuthFetch()

  /**
   * Search papers from a specific source.
   * @param {string} query - Search query
   * @param {string} source - Data source: semantic_scholar, arxiv, crossref, openalex
   * @param {object} options - Additional options
   * @param {number} options.limit - Results per page (default 20)
   * @param {number} options.offset - Pagination offset
   * @param {number} options.yearFrom - Start year filter
   * @param {number} options.yearTo - End year filter
   * @param {string} options.author - Author filter
   */
  async function searchPapers(query, source = 'openalex', options = {}) {
    if (!query || !query.trim()) {
      error.value = '请输入搜索关键词'
      return []
    }

    loading.value = true
    error.value = null

    try {
      const data = {
        query: query.trim(),
        source,
        limit: options.limit || 20,
        offset: options.offset || 0,
        yearFrom: options.yearFrom || null,
        yearTo: options.yearTo || null,
        author: options.author || '',
      }

      const json = await authMutate('/api/researcher/search', data)
      const items = json.results || []

      if (options.append) {
        // Deduplicate when appending
        const existingIds = new Set(results.value.map(r => r.id))
        const newItems = items.filter(item => !existingIds.has(item.id))
        results.value = [...results.value, ...newItems]
      } else {
        results.value = items
      }

      total.value = json.total || 0
      return items
    } catch (e) {
      error.value = e.message
      console.error('[usePaperSearch] search error:', e)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Import a paper from URL into the local library.
   */
  async function importPaper(paper) {
    importing.value = true
    error.value = null

    try {
      const data = {
        pdfUrl: paper.pdfUrl || paper.pdf_url,
        title: paper.title,
        source: paper.source,
        sourceId: paper.id,
        authors: Array.isArray(paper.authors) ? paper.authors.join(', ') : (paper.authors || ''),
        abstract: paper.abstract || '',
        year: paper.year || 0,
        doi: paper.doi || '',
        citations: paper.citations || 0,
        venue: paper.venue || '',
      }

      const json = await authMutate('/api/researcher/search/import', data)
      return json
    } catch (e) {
      error.value = e.message
      console.error('[usePaperSearch] import error:', e)
      throw e
    } finally {
      importing.value = false
    }
  }

  function clearResults() {
    results.value = []
    total.value = 0
    error.value = null
  }

  return {
    loading,
    error,
    results,
    total,
    importing,
    searchPapers,
    importPaper,
    clearResults,
  }
}
