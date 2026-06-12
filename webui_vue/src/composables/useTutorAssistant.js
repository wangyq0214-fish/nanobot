/**
 * Tutor Assistant composable — manages tutoring state and AI interactions.
 *
 * Provides:
 * - Real AI chat via Gateway sendMessage/onChat
 * - AI answer evaluation via ai_tutor_evaluate envelope
 * - Persistent tutor profile (knowledge points, error records, strategies)
 */

import { ref, nextTick } from 'vue'
import { useGateway } from './useGateway.js'
import { useAuth } from './useAuth.js'

// Shared reactive state (singleton across components)
const tutorProfile = ref(null)
const chatMessages = ref([])
const isLoading = ref(false)
const profileLoading = ref(false)

export function useTutorAssistant() {
  const { sendMessage, onChat, sendAiTutorEvaluate, sendAiTutorRecommend, getChatId, getToken } = useGateway()
  const { user } = useAuth()

  /**
   * Fetch the student's tutor profile from the backend.
   */
  async function fetchProfile() {
    const u = user.value
    if (!u?.userId) return

    profileLoading.value = true
    try {
      const params = new URLSearchParams({
        role: u.role,
        user_id: u.userId,
        token: getToken() || '',
      })
      const resp = await fetch(`/api/tutor/profile?${params}`)
      if (resp.ok) {
        tutorProfile.value = await resp.json()
      }
    } catch (err) {
      console.error('[tutor] Failed to fetch profile:', err.message)
    } finally {
      profileLoading.value = false
    }
  }

  /**
   * Send a question to the AI tutor via Gateway chat.
   * The response arrives asynchronously via onChat.
   */
  async function askTutor(question) {
    if (!question?.trim()) return

    const q = question.trim()
    isLoading.value = true

    // Add student message to chat
    chatMessages.value.push({
      role: 'student',
      content: q,
      timestamp: Date.now(),
    })

    try {
      // Use meta to signal tutor mode to the backend
      sendMessage(q, { _skill: 'tutor' })
    } catch (err) {
      chatMessages.value.push({
        role: 'system',
        content: `发送失败: ${err.message}`,
        timestamp: Date.now(),
      })
      isLoading.value = false
    }
  }

  /**
   * Subscribe to AI chat responses for the current chat session.
   * Call this after gateway is connected.
   */
  function subscribeToChat() {
    const chatId = getChatId()
    if (!chatId) return

    let currentAiMessage = ''

    onChat(chatId, (event) => {
      if (event.event === 'delta') {
        // Streaming text chunk
        currentAiMessage += event.text || ''
        // Update or create the AI message in chat
        const msgs = chatMessages.value
        const lastMsg = msgs[msgs.length - 1]
        if (lastMsg?.role === 'ai' && lastMsg._streaming) {
          lastMsg.content = currentAiMessage
        } else {
          msgs.push({
            role: 'ai',
            content: currentAiMessage,
            timestamp: Date.now(),
            _streaming: true,
          })
        }
      } else if (event.event === 'stream_end') {
        // Finalize the streaming message
        const msgs = chatMessages.value
        const lastMsg = msgs[msgs.length - 1]
        if (lastMsg?.role === 'ai') {
          lastMsg._streaming = false
        }
        currentAiMessage = ''
        isLoading.value = false
      } else if (event.event === 'message') {
        // Non-streaming message
        if (!currentAiMessage) {
          chatMessages.value.push({
            role: 'ai',
            content: event.text || '',
            timestamp: Date.now(),
          })
          isLoading.value = false
        }
      } else if (event.event === 'error') {
        chatMessages.value.push({
          role: 'system',
          content: `错误: ${event.detail || '未知错误'}`,
          timestamp: Date.now(),
        })
        isLoading.value = false
        currentAiMessage = ''
      }
    })
  }

  /**
   * Evaluate a student's answer using AI.
   * Returns the evaluation result and updates the tutor profile.
   */
  async function evaluateAnswer(question, answer, referenceAnswer) {
    if (!question?.trim() || !answer?.trim()) {
      throw new Error('题目和解答不能为空')
    }

    isLoading.value = true
    try {
      const result = await sendAiTutorEvaluate({
        question: question.trim(),
        studentAnswer: answer.trim(),
        referenceAnswer: referenceAnswer?.trim() || '',
      })

      // Update local profile with the result
      if (tutorProfile.value) {
        tutorProfile.value.totalSubmissions = result.totalSubmissions || (tutorProfile.value.totalSubmissions || 0) + 1

        // Update knowledge points
        for (const newKp of result.knowledgePoints || []) {
          const existing = tutorProfile.value.knowledgePoints?.find(k => k.title === newKp.title)
          if (existing) {
            existing.mastery = Math.max(0, Math.min(1, (existing.mastery || 0.5) + newKp.masteryDelta))
            existing.attempts = (existing.attempts || 0) + 1
            if (result.isCorrect) existing.correct = (existing.correct || 0) + 1
            existing.lastAttempt = new Date().toISOString()
          } else {
            if (!tutorProfile.value.knowledgePoints) tutorProfile.value.knowledgePoints = []
            tutorProfile.value.knowledgePoints.push({
              id: `kp_${tutorProfile.value.knowledgePoints.length + 1}`,
              title: newKp.title,
              formula: newKp.formula || '',
              mastery: Math.max(0, Math.min(1, 0.5 + newKp.masteryDelta)),
              attempts: 1,
              correct: result.isCorrect ? 1 : 0,
              lastAttempt: new Date().toISOString(),
            })
          }
        }

        // Add error record
        if (!result.isCorrect && result.errorType) {
          if (!tutorProfile.value.errorRecords) tutorProfile.value.errorRecords = []
          tutorProfile.value.errorRecords.push({
            id: `err_${tutorProfile.value.errorRecords.length + 1}`,
            type: result.errorType,
            title: question.slice(0, 50),
            detail: result.errorDetail || '',
            timestamp: new Date().toISOString(),
          })
        }

        // Add strategy
        if (result.strategy) {
          if (!tutorProfile.value.strategies) tutorProfile.value.strategies = []
          tutorProfile.value.strategies.push({
            id: `strat_${tutorProfile.value.strategies.length + 1}`,
            content: result.strategy,
            relatedKp: result.knowledgePoints?.[0]?.title || '',
            timestamp: new Date().toISOString(),
          })
        }
      }

      return result
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Generate AI-recommended practice questions based on the student's tutor profile.
   * @param {Object} params - { numQuestions, typeDistribution, content }
   * @returns {Promise<{questions, totalPoints}>}
   */
  async function recommendQuestions(params = {}) {
    isLoading.value = true
    try {
      const result = await sendAiTutorRecommend({
        numQuestions: params.numQuestions || 5,
        typeDistribution: params.typeDistribution || {},
        content: params.content || '',
      })
      return result
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear chat history.
   */
  function clearChat() {
    chatMessages.value = []
  }

  return {
    tutorProfile,
    chatMessages,
    isLoading,
    profileLoading,
    fetchProfile,
    askTutor,
    subscribeToChat,
    evaluateAnswer,
    recommendQuestions,
    clearChat,
  }
}
