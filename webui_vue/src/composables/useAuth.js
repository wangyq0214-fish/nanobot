import { ref, computed } from 'vue'

const USER_KEY = 'nanobot-webui.user'
const API_TOKEN_KEY = 'nanobot-webui.api_token'
const WS_TOKEN_KEY = 'nanobot-webui.ws_token'
const LEGACY_TOKEN_KEY = 'nanobot-webui.token'

// Shared reactive state — all pages read/write the same user
const user = ref(loadUser())

function loadUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    const p = JSON.parse(raw)
    return p?.userId ? p : null
  } catch { return null }
}

function saveUser(u) {
  localStorage.setItem(USER_KEY, JSON.stringify(u))
  user.value = u
}

function clearUser() {
  localStorage.removeItem(USER_KEY)
  user.value = null
}

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)

  function login(loginUser) {
    saveUser(loginUser)
  }

  async function logout() {
    // Call server-side logout to revoke API token
    const apiToken = sessionStorage.getItem(API_TOKEN_KEY) || sessionStorage.getItem(LEGACY_TOKEN_KEY)
    if (apiToken) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json'
          },
          credentials: 'same-origin'
        })
      } catch (e) {
        // Ignore logout API errors — still clear local state
        console.warn('Logout API failed:', e)
      }
    }

    // Clear local storage
    clearUser()
    sessionStorage.removeItem(API_TOKEN_KEY)
    sessionStorage.removeItem(WS_TOKEN_KEY)
    sessionStorage.removeItem(LEGACY_TOKEN_KEY)
    // Clear chatId for this user
    if (user.value) {
      const { role, userId } = user.value
      localStorage.removeItem(`nanobot-webui.chatId.${role}.${userId}`)
    }
  }

  return { user, isLoggedIn, login, logout, saveUser, clearUser }
}
