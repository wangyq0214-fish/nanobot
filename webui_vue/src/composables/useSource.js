/**
 * Source file management — fetch files from the user's workspace source directory.
 */

export function useSource() {

  async function fetchSourceFiles(role, userId, token) {
    const params = new URLSearchParams()
    if (role) params.set('role', role)
    if (userId) params.set('user_id', userId)
    // Pass token as query param too — some reverse proxies drop Authorization headers
    if (token) params.set('token', token)
    const qs = params.toString()
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(`/api/source${qs ? '?' + qs : ''}`, {
      credentials: 'same-origin',
      headers,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }

  async function fetchSourceFile(filePath, role, userId, token) {
    const params = new URLSearchParams()
    if (role) params.set('role', role)
    if (userId) params.set('user_id', userId)
    if (token) params.set('token', token)
    const qs = params.toString()
    const encodedPath = filePath.split('/').map(encodeURIComponent).join('/')
    const url = `/api/source/${encodedPath}${qs ? '?' + qs : ''}`
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(url, { credentials: 'same-origin', headers })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }

  return {
    fetchSourceFiles,
    fetchSourceFile,
  }
}
