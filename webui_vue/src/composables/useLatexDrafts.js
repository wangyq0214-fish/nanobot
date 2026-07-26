import { useAuthFetch } from './useAuthFetch.js'

export function useLatexDrafts() {
  const { authGet, authMutate } = useAuthFetch()

  async function fetchLatexDrafts() {
    return authGet('/api/researcher/latex-drafts')
  }

  async function fetchLatexDraft(draftId) {
    return authGet(`/api/researcher/latex-drafts/${encodeURIComponent(draftId)}`)
  }

  async function saveLatexDraft(payload) {
    return authMutate('/api/researcher/latex-drafts/save', payload)
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
