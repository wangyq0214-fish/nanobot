/**
 * LaTeX Compiler composable - provides LaTeX compilation and PDF preview
 * Calls external LaTeX compilation API (Mini Overleaf backend)
 * Uses Vite proxy in development, direct URL in production
 */
import { ref } from 'vue'

// In dev, use empty string to go through Vite proxy; in prod, use env var or default
const API_URL = import.meta.env.DEV ? '' : (import.meta.env.VITE_LATEX_API_URL || 'http://10.100.132.162:8001')

function escapeLatexText(text) {
  return String(text || '')
    .replace(/\\/g, '\\textbackslash{}')
    .replace(/([{}_%&#$])/g, '\\$1')
    .replace(/\^/g, '\\textasciicircum{}')
    .replace(/~/g, '\\textasciitilde{}')
}

function normalizeLatexForCompile(texCode, attachments = []) {
  const attachmentNames = new Set(
    attachments.map(file => String(file?.name || '').split(/[\\/]/).pop().toLowerCase()).filter(Boolean)
  )
  let normalized = String(texCode || '')
    // Recover documents saved from a double-escaped AI editor payload.
    .replace(/\\n/g, '\n')
    .replace(/\\\\(?=[A-Za-z])/g, '\\')

  normalized = normalized
    .replace(/\\citet\*?\s*\{/g, '\\cite{')
    .replace(/\\citep\*?\s*\{/g, '\\cite{')
    .replace(/\\citealt\*?\s*\{/g, '\\cite{')
    .replace(/\\citeauthor\*?\s*\{/g, '\\cite{')
    .replace(/\\citeyear\*?\s*\{/g, '\\cite{')

  normalized = normalized.replace(/\\includegraphics(\[[^\]]*\])?\{([^}]+)\}/g, (match, options = '', rawPath) => {
    const fileName = String(rawPath || '').split(/[\\/]/).pop().toLowerCase()
    if (attachmentNames.has(fileName)) return match
    const label = escapeLatexText(rawPath)
    return `\\fbox{\\parbox{0.75\\textwidth}{\\centering 图示占位：${label}}}`
  })

  return normalized
}

function validateLatexForCompile(texCode) {
  const normalized = String(texCode || '').trim()
  if (!normalized) return 'LaTeX 内容为空'
  if (!/\\documentclass(?:\[[^\]]*\])?\{[^}]+\}/.test(normalized)) return '缺少 \\documentclass'
  if (!normalized.includes('\\begin{document}')) return '缺少 \\begin{document}'
  if (!normalized.includes('\\end{document}')) return '缺少 \\end{document}'
  return ''
}

async function blobLooksLikePdf(blob) {
  if (!blob || blob.size < 100) return false
  const header = new Uint8Array(await blob.slice(0, 5).arrayBuffer())
  return header[0] === 0x25 && header[1] === 0x50 && header[2] === 0x44 && header[3] === 0x46 && header[4] === 0x2d
}

export function useLatexCompiler() {
  const compiling = ref(false)
  const compileError = ref(null)
  const compileLog = ref(null)
  const pdfUrl = ref(null)
  const pdfData = ref(null)

  /**
   * Compile LaTeX code to PDF
   * @param {string} texCode - LaTeX source code
   * @param {File[]} attachments - Optional array of附件 files (.bib, .sty, .cls, images)
   */
  async function compileLatex(texCode, attachments = []) {
    compiling.value = true
    compileError.value = null
    compileLog.value = null
    // Clean up previous PDF URL
    if (pdfUrl.value) {
      URL.revokeObjectURL(pdfUrl.value)
      pdfUrl.value = null
    }
    pdfData.value = null

    try {
      const normalizedTexCode = normalizeLatexForCompile(texCode, attachments)
      const validationError = validateLatexForCompile(normalizedTexCode)
      if (validationError) {
        compileError.value = validationError
        compileLog.value = normalizedTexCode.slice(0, 2000)
        return { success: false, texCode: normalizedTexCode }
      }
      const texBlob = new Blob([normalizedTexCode], { type: 'text/plain' })
      const texFile = new File([texBlob], 'main.tex', { type: 'text/plain' })

      const formData = new FormData()

      if (attachments.length > 0) {
        formData.append('files', texFile)
        attachments.forEach(file => {
          formData.append('files', file)
        })
      } else {
        formData.append('file', texFile)
      }

      const url = attachments.length > 0 ? '/compile-with-files' : '/compile'

      const response = await fetch(`${API_URL}${url}`, {
        method: 'POST',
        body: formData
      })

      const contentType = response.headers.get('content-type') || ''

      // Check if response is JSON (error case)
      if (contentType.includes('application/json') || !response.ok) {
        const result = await response.json()
        if (result.success === false || result.error) {
          compileError.value = result.error || '编译失败'
          compileLog.value = result.log || null
          return false
        }
      }

      // Success - get PDF blob
      if (response.ok) {
        const blob = await response.blob()
        if (!(await blobLooksLikePdf(blob))) {
          let responseText = ''
          try { responseText = await blob.text() } catch {}
          compileError.value = '返回的 PDF 为空或无效'
          compileLog.value = responseText || `响应类型：${contentType || 'unknown'}，大小：${blob.size} bytes`
          return false
        }
        pdfUrl.value = URL.createObjectURL(blob)
        pdfData.value = blob
        return { success: true, texCode: normalizedTexCode }
      } else {
        compileError.value = '编译请求失败'
        return false
      }
    } catch (err) {
      compileError.value = '网络错误，请检查后端服务'
      console.error('LaTeX compile error:', err)
      return false
    } finally {
      compiling.value = false
    }
  }

  /**
   * Download the compiled PDF
   * @param {string} filename - Download filename (default: 'output.pdf')
   */
  function downloadPdf(filename = 'output.pdf') {
    if (!pdfUrl.value) return

    const link = document.createElement('a')
    link.href = pdfUrl.value
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  /**
   * Clean up resources
   */
  function cleanup() {
    if (pdfUrl.value) {
      URL.revokeObjectURL(pdfUrl.value)
      pdfUrl.value = null
    }
    pdfData.value = null
    compileError.value = null
    compileLog.value = null
  }

  return {
    // State
    compiling,
    compileError,
    compileLog,
    pdfUrl,
    pdfData,

    // Methods
    compileLatex,
    downloadPdf,
    cleanup
  }
}
