import { ref, computed } from 'vue'

const USER_KEY = 'nanobot-webui.user'

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

  function logout() {
    clearUser()
  }

  return { user, isLoggedIn, login, logout, saveUser, clearUser }
}
