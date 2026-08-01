/**
 * Unified authentication fetch composable.
 *
 * Provides consistent auth token injection for all API calls.
 * Token is sourced from useGateway().getToken() (bootstrap token).
 * Token is sent via Authorization header — role/user_id are resolved
 * server-side from the token's metadata.
 */

import { useGateway } from './useGateway.js'
import { useAuth } from './useAuth.js'

export function useAuthFetch() {
  const { getToken, refreshTokens } = useGateway()
  const { user } = useAuth()

  async function parseResponse(res) {
    const text = await res.text()
    const contentType = res.headers.get('content-type') || ''
    if (!text) {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return {}
    }
    if (!contentType.includes('application/json')) {
      const snippet = text.trim().slice(0, 120)
      if (!res.ok) throw new Error(snippet || `HTTP ${res.status}`)
      throw new Error(`Expected JSON response, received ${contentType || 'unknown content type'}`)
    }
    try {
      const body = JSON.parse(text)
      if (!res.ok) throw new Error(body?.error || `HTTP ${res.status}`)
      return body
    } catch (err) {
      if (!res.ok) throw new Error(text || `HTTP ${res.status}`)
      throw err
    }
  }

  /**
   * Build headers with Authorization bearer token and CSRF protection.
   * Token is only sent via header (not query param) for security.
   */
  function authHeaders() {
    const token = getToken()
    const headers = {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',  // CSRF protection
    }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
  }

  async function request(url, options = {}, retry = true) {
    const res = await fetch(url, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
      credentials: 'same-origin',
    })
    if (res.status === 401 && retry && user.value?.userId) {
      try {
        await refreshTokens()
        return request(url, options, false)
      } catch {
        // Let parseResponse surface the original authentication error.
      }
    }
    return parseResponse(res)
  }

  /**
   * Authenticated GET request.
   */
  async function authGet(url) {
    return request(url)
  }

  /**
   * Authenticated POST request with JSON body.
   */
  async function authPost(url, body) {
    return request(url, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  /**
   * Authenticated DELETE request.
   */
  async function authDelete(url) {
    return request(url, {
      method: 'DELETE',
    })
  }

  async function authMutate(url, data) {
    return request(url, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async function authPut(url, data) {
    return request(url, { method: 'PUT', body: JSON.stringify(data) })
  }

  async function authPatch(url, data) {
    return request(url, { method: 'PATCH', body: JSON.stringify(data) })
  }

  async function authDownload(url) {
    const res = await fetch(url, { headers: authHeaders(), credentials: 'same-origin' })
    if (res.status === 401 && user.value?.userId) {
      await refreshTokens()
      return authDownload(url)
    }
    if (!res.ok) {
      let message = `HTTP ${res.status}`
      try { message = (await res.json()).error || message } catch {}
      throw new Error(message)
    }
    const disposition = res.headers.get('content-disposition') || ''
    const match = disposition.match(/filename="?([^";]+)"?/i)
    return { blob: await res.blob(), filename: match?.[1] || '' }
  }

  return { authHeaders, authGet, authPost, authDelete, authMutate, authPut, authPatch, authDownload }
}
