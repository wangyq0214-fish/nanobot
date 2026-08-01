import { useAuthFetch } from './useAuthFetch.js'

export function useLatexDrafts() {
  const { authGet, authPost, authMutate } = useAuthFetch()

  async function fetchLatexDrafts() {
    return authGet('/api/researcher/latex-drafts')
  }

  async function fetchLatexDraft(draftId) {
    return authGet(`/api/researcher/latex-drafts/${encodeURIComponent(draftId)}`)
  }

  async function saveLatexDraft(payload) {
    return authPost(`${import.meta.env.VITE_LATEX_API_URL || 'http://127.0.0.1:8766'}/api/researcher/latex-drafts/save`, payload)
  }

  async function fetchLatexDraftVersions(draftId) {
    return authGet(`/api/researcher/latex-drafts/${encodeURIComponent(draftId)}/versions`)
  }

  async function createLatexCompileRecord(payload) {
    return authMutate('/api/researcher/latex-drafts/compile-records/create', payload)
  }

  return {
    fetchLatexDrafts,
    fetchLatexDraft,
    saveLatexDraft,
    fetchLatexDraftVersions,
    createLatexCompileRecord,
  }
}
