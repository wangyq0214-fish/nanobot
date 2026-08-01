/**
 * Database-backed researcher workspace state.
 */
import { ref } from 'vue'
import { useAuthFetch } from './useAuthFetch.js'

const projects = ref([])
const attachments = ref([])
const loadingProjects = ref(false)
const uploadingAttachment = ref(false)

export function useResearchWorkspace() {
  const { authGet, authMutate, authPut } = useAuthFetch()

  async function fetchProjects() {
    loadingProjects.value = true
    try {
      const data = await authGet('/api/researcher/projects')
      if (data?.ok) projects.value = data.data || []
      return projects.value
    } finally {
      loadingProjects.value = false
    }
  }

  async function createProject(name, description = '') {
    const data = await authMutate('/api/researcher/projects/create', { name, description })
    if (data?.ok && data.data) {
      projects.value.unshift(data.data)
      return data.data
    }
    return null
  }

  async function fetchProjectLinks(projectId) {
    const data = await authGet(`/api/researcher/projects/${projectId}/links`)
    return data?.ok ? data.data || { paperIds: [], resultIds: [] } : null
  }

  async function replaceProjectLinks(projectId, links) {
    const data = await authPut(`/api/researcher/projects/${projectId}/links`, links)
    return data?.ok ? data.data : null
  }

  async function migrateProjectLinks(links) {
    const data = await authMutate('/api/researcher/projects/links/migrate', { links })
    return data?.ok ? data.data || [] : null
  }

  async function fetchAttachments(chatId = '') {
    const qs = chatId ? `?chat_id=${encodeURIComponent(chatId)}` : ''
    const data = await authGet(`/api/researcher/attachments${qs}`)
    if (data?.ok) attachments.value = data.data || []
    return attachments.value
  }

  async function uploadAttachment(file, { chatId = '', projectId = null } = {}) {
    uploadingAttachment.value = true
    try {
      const fileData = await fileToBase64(file)
      const payload = {
        fileName: file.name,
        fileType: inferType(file),
        fileData,
        chatId,
        projectId,
      }
      const data = await authMutate('/api/researcher/attachments/upload', payload)
      if (data?.ok && data.data) {
        attachments.value.unshift(data.data)
        return data.data
      }
      return null
    } finally {
      uploadingAttachment.value = false
    }
  }

  return {
    projects,
    attachments,
    loadingProjects,
    uploadingAttachment,
    fetchProjects,
    createProject,
    fetchProjectLinks,
    replaceProjectLinks,
    migrateProjectLinks,
    fetchAttachments,
    uploadAttachment,
  }
}

function inferType(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  return ext || file.type || 'txt'
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'))
    reader.readAsDataURL(file)
  })
}
