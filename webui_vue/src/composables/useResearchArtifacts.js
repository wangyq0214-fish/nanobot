import { ref } from 'vue'
import { useAuthFetch } from './useAuthFetch.js'

const artifacts = ref([])
const loading = ref(false)
const error = ref(null)
const currentArtifact = ref(null)

export const ARTIFACT_TYPES = [
  { value: 'mind_map', label: '思维导图', description: '生成可折叠的研究结构', icon: '图', available: true },
  { value: 'report', label: '报告', description: '生成章节化研究报告', icon: '报', available: true },
  { value: 'flashcards', label: '闪卡', description: '生成可翻转的学习卡片', icon: '卡', available: true },
  { value: 'quiz', label: '测验', description: '生成单选研究测验', icon: '测', available: true },
  { value: 'data_table', label: '数据表格', description: '提取可追溯的研究数据', icon: '表', available: true },
]

export function artifactTypeLabel(value) {
  return ARTIFACT_TYPES.find(item => item.value === value)?.label || value || '未知类型'
}

export function useResearchArtifacts() {
  const { authGet, authMutate } = useAuthFetch()

  async function fetchArtifacts() {
    loading.value = true
    error.value = null
    try {
      const data = await authGet('/api/researcher/artifacts')
      if (data?.ok) artifacts.value = data.data || []
      return artifacts.value
    } catch (err) {
      error.value = err?.message || '加载制品失败'
      artifacts.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchArtifact(id) {
    error.value = null
    try {
      const data = await authGet(`/api/researcher/artifacts/${id}`)
      if (data?.ok) {
        currentArtifact.value = data.data
        return currentArtifact.value
      }
    } catch (err) {
      error.value = err?.message || '加载制品详情失败'
    }
    return null
  }

  async function createArtifact(payload) {
    const data = await authMutate('/api/researcher/artifacts/create', payload)
    if (data?.ok && data.data) {
      upsertArtifact(data.data)
      currentArtifact.value = data.data
      return data.data
    }
    return null
  }

  async function regenerateArtifact(id) {
    const data = await authMutate(`/api/researcher/artifacts/${id}/generate`, {})
    if (data?.ok && data.data) {
      upsertArtifact(data.data)
      currentArtifact.value = data.data
      return data.data
    }
    return null
  }

  async function updateArtifact(id, payload) {
    const data = await authMutate(`/api/researcher/artifacts/${id}/update`, payload)
    if (data?.ok && data.data) {
      upsertArtifact(data.data)
      currentArtifact.value = data.data
      return data.data
    }
    return null
  }

  async function deleteArtifact(id) {
    const data = await authMutate(`/api/researcher/artifacts/${id}/delete`, {})
    if (data?.ok) {
      artifacts.value = artifacts.value.filter(item => item.id !== id)
      if (currentArtifact.value?.id === id) currentArtifact.value = null
      return true
    }
    return false
  }

  function upsertArtifact(value) {
    const index = artifacts.value.findIndex(item => item.id === value.id)
    if (index >= 0) artifacts.value[index] = value
    else artifacts.value.unshift(value)
  }

  return {
    artifacts,
    loading,
    error,
    currentArtifact,
    fetchArtifacts,
    fetchArtifact,
    createArtifact,
    regenerateArtifact,
    updateArtifact,
    deleteArtifact,
  }
}
