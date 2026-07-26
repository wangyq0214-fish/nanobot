/**
 * Global parse container for streaming question parsing.
 * Persists across page navigation.
 */

import { ref } from 'vue'

// Shared state (outside component)
const previewQuestions = ref([])
const isParsing = ref(false)
const parseError = ref(null)

export function useParseContainer() {
  function addQuestion(question) {
    previewQuestions.value.push(question)
  }

  function setParsing(value) {
    isParsing.value = value
  }

  function setError(error) {
    parseError.value = error
  }

  function clearAll() {
    previewQuestions.value = []
    isParsing.value = false
    parseError.value = null
  }

  function removeQuestion(index) {
    previewQuestions.value.splice(index, 1)
  }

  return {
    previewQuestions,
    isParsing,
    parseError,
    addQuestion,
    setParsing,
    setError,
    clearAll,
    removeQuestion,
  }
}
