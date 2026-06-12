import { ref, computed } from 'vue'
import { useGateway } from './useGateway.js'

/**
 * Derivation chain composable — manages AI-generated derivation steps
 * and real-time chat for Q&A about the derivation.
 *
 * Generates both formula and concept modes in parallel on each request.
 * Follows the same singleton-ref pattern as useTutorAssistant.
 */

// Shared reactive state (module-level singleton)
const formulaSteps = ref([])
const conceptSteps = ref([])
const isGenerating = ref(false)
const chatMessages = ref([])
const currentTopic = ref('')

let chatUnsubscribe = null

export function useDerivation() {
  const gateway = useGateway()

  /**
   * Get steps for the given mode.
   * @param {string} mode - 'formula' | 'concept'
   */
  function getSteps(mode) {
    return mode === 'concept' ? conceptSteps.value : formulaSteps.value
  }

  /**
   * Generate derivation chains for both formula and concept modes in parallel.
   * @param {string} topic - The topic to derive
   */
  async function generateDerivation(topic) {
    if (!topic?.trim()) throw new Error('请输入主题')
    if (isGenerating.value) return

    isGenerating.value = true
    currentTopic.value = topic.trim()
    formulaSteps.value = []
    conceptSteps.value = []

    const fallbackStep = (mode, err) => [{
      id: 0,
      name: `📖 ${topic.trim()}`,
      shortDesc: '生成失败',
      trace: 'AI 服务不可用',
      extra: err?.message || '',
      sections: [{
        kind: 'text',
        value: `推导链生成失败：${err?.message || '未知错误'}。请稍后重试。`,
      }, {
        kind: 'insight',
        value: '如果问题持续存在，请检查网络连接或联系管理员。',
      }],
    }]

    try {
      const [formulaResult, conceptResult] = await Promise.allSettled([
        gateway.sendAiGenerateDerivation({ topic: topic.trim(), mode: 'formula' }),
        gateway.sendAiGenerateDerivation({ topic: topic.trim(), mode: 'concept' }),
      ])

      formulaSteps.value = formulaResult.status === 'fulfilled'
        ? (formulaResult.value.steps || [])
        : fallbackStep('formula', formulaResult.reason)

      conceptSteps.value = conceptResult.status === 'fulfilled'
        ? (conceptResult.value.steps || [])
        : fallbackStep('concept', conceptResult.reason)

      return { formula: formulaSteps.value, concept: conceptSteps.value }
    } catch (err) {
      formulaSteps.value = fallbackStep('formula', err)
      conceptSteps.value = fallbackStep('concept', err)
      throw err
    } finally {
      isGenerating.value = false
    }
  }

  /**
   * Send a question about the current derivation via streaming chat.
   * @param {string} question - The user's question
   * @param {string} mode - Current mode for context
   */
  function askQuestion(question, mode = 'formula') {
    if (!question?.trim()) return

    const topic = currentTopic.value || '未知主题'
    const steps = getSteps(mode)
    const stepsSummary = steps
      .map((s, i) => `${i + 1}. ${s.name} — ${s.shortDesc}`)
      .join('\n')

    const contextualQuestion = [
      `当前推导主题：「${topic}」`,
      stepsSummary ? `推导步骤：\n${stepsSummary}` : '',
      `学生提问：${question.trim()}`,
    ].filter(Boolean).join('\n')

    chatMessages.value.push({ text: question.trim(), isUser: true })
    gateway.sendMessage(contextualQuestion, { _skill: 'derivation' })
  }

  /**
   * Subscribe to streaming chat responses for the current chat session.
   * @param {string} chatId - The chat ID to subscribe to
   * @returns {Function} Unsubscribe function
   */
  function subscribeToChat(chatId) {
    if (chatUnsubscribe) {
      chatUnsubscribe()
    }

    let aiBuffer = ''
    let aiMessageIndex = -1

    chatUnsubscribe = gateway.onChat(chatId, (ev) => {
      if (ev.event === 'delta') {
        aiBuffer += ev.text || ''
        if (aiMessageIndex === -1) {
          aiMessageIndex = chatMessages.value.length
          chatMessages.value.push({ text: aiBuffer, isUser: false, streaming: true })
        } else {
          chatMessages.value[aiMessageIndex] = { text: aiBuffer, isUser: false, streaming: true }
        }
      } else if (ev.event === 'stream_end') {
        if (aiMessageIndex !== -1) {
          chatMessages.value[aiMessageIndex] = { text: aiBuffer, isUser: false, streaming: false }
        }
        aiBuffer = ''
        aiMessageIndex = -1
        if (chatMessages.value.length > 20) {
          chatMessages.value = chatMessages.value.slice(-20)
        }
      } else if (ev.event === 'message') {
        chatMessages.value.push({ text: ev.text || '', isUser: false })
        if (chatMessages.value.length > 20) {
          chatMessages.value = chatMessages.value.slice(-20)
        }
      } else if (ev.event === 'error') {
        chatMessages.value.push({
          text: `⚠️ ${ev.detail || '发生错误'}`,
          isUser: false,
        })
      }
    })

    return () => {
      if (chatUnsubscribe) {
        chatUnsubscribe()
        chatUnsubscribe = null
      }
    }
  }

  /** Clear chat message history. */
  function clearChat() {
    chatMessages.value = []
  }

  return {
    // State
    formulaSteps,
    conceptSteps,
    isGenerating,
    chatMessages,
    currentTopic,
    // Actions
    getSteps,
    generateDerivation,
    askQuestion,
    subscribeToChat,
    clearChat,
  }
}
