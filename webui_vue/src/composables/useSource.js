/**
 * Source file management — fetch files from the user's workspace source directory.
 */

import { useAuthFetch } from './useAuthFetch.js'

export function useSource() {
  const { authGet } = useAuthFetch()

  async function fetchSourceFiles() {
    return authGet('/api/source')
  }

  async function fetchSourceFile(filePath) {
    const encodedPath = filePath.split('/').map(encodeURIComponent).join('/')
    return authGet(`/api/source/${encodedPath}`)
  }

  return {
    fetchSourceFiles,
    fetchSourceFile,
  }
}
