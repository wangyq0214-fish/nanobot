/**
 * Unified authentication fetch composable.
 *
 * Provides consistent auth token injection for all API calls.
 * Token is sourced from useGateway().getToken() (bootstrap token).
 * Token is sent via Authorization header — role/user_id are resolved
 * server-side from the token's metadata.
 */

import { useGateway } from './useGateway.js'

export function useAuthFetch() {
  const { getToken } = useGateway()

  async function parseResponse(res) {
    const text = await res.text()
    if (!text) {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return {}
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

  /**
   * Authenticated GET request.
   */
  async function authGet(url) {
    const res = await fetch(url, {
      headers: authHeaders(),
      credentials: 'same-origin',
    })
    return parseResponse(res)
  }

  /**
   * Authenticated POST request with JSON body.
   */
  async function authPost(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(body),
      credentials: 'same-origin',
    })
    return parseResponse(res)
  }

  /**
   * Authenticated DELETE request.
   */
  async function authDelete(url) {
    const res = await fetch(url, {
      method: 'DELETE',
      headers: authHeaders(),
      credentials: 'same-origin',
    })
    return parseResponse(res)
  }

  /**
   * Authenticated request for mutations via query param data.
   * Used by handlers that read mutation data from query params.
   */
  async function authMutate(url, data) {
    const params = new URLSearchParams()
    params.set('data', JSON.stringify(data))
    const sep = url.includes('?') ? '&' : '?'
    const res = await fetch(`${url}${sep}${params}`, {
      headers: authHeaders(),
      credentials: 'same-origin',
    })
    return parseResponse(res)
  }

  return { authHeaders, authGet, authPost, authDelete, authMutate }
}
