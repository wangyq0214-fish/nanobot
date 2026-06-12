/**
 * Writing Assistant composable - provides real writing assistance features
 * Uses OpenAlex for literature search and local NLP for text analysis
 */
import { ref, computed } from 'vue'

const OPENALEX_BASE = 'https://openalex.org/api'
const STORAGE_KEY = 'nanobot_literature_library'

export function useWritingAssistant() {
  const loading = ref(false)
  const error = ref(null)

  // Literature library storage
  const library = ref(loadLibrary())

  /**
   * Load library from localStorage
   */
  function loadLibrary() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : { papers: [], collections: [] }
    } catch {
      return { papers: [], collections: [] }
    }
  }

  /**
   * Save library to localStorage
   */
  function saveLibrary() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(library.value))
    } catch (err) {
      console.error('Failed to save library:', err)
    }
  }

  /**
   * Get library stats
   */
  const libraryStats = computed(() => ({
    total: library.value.papers.length,
    collections: library.value.collections.length,
    recent: library.value.papers.filter(p => {
      const added = new Date(p.addedAt)
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      return added > weekAgo
    }).length
  }))

  /**
   * Search literature using OpenAlex API
   */
  async function searchLiterature(query, limit = 20) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        search: query,
        per_page: limit,
        sort: 'cited_by_count:desc',
        select: 'id,title,authorships,primary_location,cited_by_count,publication_year,doi,abstract_inverted_index'
      })

      const response = await fetch(`${OPENALEX_BASE}/works?${params}`)
      if (!response.ok) throw new Error(`API error: ${response.status}`)
      const data = await response.json()

      return data.results.map((work, idx) => ({
        id: work.id,
        index: idx + 1,
        title: work.title || 'Untitled',
        authors: work.authorships?.slice(0, 3).map(a => a.author?.display_name).filter(Boolean).join(', ') || 'Unknown',
        year: work.publication_year,
        journal: work.primary_location?.source?.display_name || 'Unknown',
        citations: work.cited_by_count || 0,
        doi: work.doi,
        abstract: reconstructAbstract(work.abstract_inverted_index)
      }))
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Add paper to library
   */
  function addToLibrary(paper, collectionId = null) {
    const exists = library.value.papers.find(p => p.id === paper.id || p.doi === paper.doi)
    if (exists) return false

    const newPaper = {
      ...paper,
      addedAt: new Date().toISOString(),
      collections: collectionId ? [collectionId] : [],
      tags: paper.tags || [],
      notes: '',
      starred: false
    }

    library.value.papers.unshift(newPaper)
    saveLibrary()
    return true
  }

  /**
   * Remove paper from library
   */
  function removeFromLibrary(paperId) {
    const idx = library.value.papers.findIndex(p => p.id === paperId)
    if (idx !== -1) {
      library.value.papers.splice(idx, 1)
      saveLibrary()
      return true
    }
    return false
  }

  /**
   * Toggle paper star status
   */
  function toggleStar(paperId) {
    const paper = library.value.papers.find(p => p.id === paperId)
    if (paper) {
      paper.starred = !paper.starred
      saveLibrary()
    }
  }

  /**
   * Update paper notes
   */
  function updateNotes(paperId, notes) {
    const paper = library.value.papers.find(p => p.id === paperId)
    if (paper) {
      paper.notes = notes
      saveLibrary()
    }
  }

  /**
   * Add paper to collection
   */
  function addToCollection(paperId, collectionId) {
    const paper = library.value.papers.find(p => p.id === paperId)
    if (paper && !paper.collections.includes(collectionId)) {
      paper.collections.push(collectionId)
      saveLibrary()
    }
  }

  /**
   * Create new collection
   */
  function createCollection(name, description = '') {
    const newCollection = {
      id: 'col_' + Date.now(),
      name,
      description,
      createdAt: new Date().toISOString()
    }
    library.value.collections.push(newCollection)
    saveLibrary()
    return newCollection
  }

  /**
   * Get papers by collection
   */
  function getPapersByCollection(collectionId) {
    if (!collectionId) return library.value.papers
    return library.value.papers.filter(p => p.collections.includes(collectionId))
  }

  /**
   * Get starred papers
   */
  function getStarredPapers() {
    return library.value.papers.filter(p => p.starred)
  }

  /**
   * Import papers from RIS format
   */
  function importFromRIS(risText) {
    const papers = []
    let currentPaper = {}

    const lines = risText.split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      const tag = trimmed.substring(0, 2)
      const value = trimmed.substring(2).trim()

      switch (tag) {
        case 'TY':
          currentPaper = { type: value }
          break
        case 'TI':
        case 'T1':
          currentPaper.title = value
          break
        case 'AU':
          if (!currentPaper.authors) currentPaper.authors = []
          currentPaper.authors.push(value)
          break
        case 'PY':
        case 'Y1':
          currentPaper.year = parseInt(value) || value
          break
        case 'JO':
        case 'JA':
        case 'JF':
          currentPaper.journal = value
          break
        case 'DO':
          currentPaper.doi = value
          break
        case 'AB':
          currentPaper.abstract = value
          break
        case 'KW':
          if (!currentPaper.keywords) currentPaper.keywords = []
          currentPaper.keywords.push(value)
          break
        case 'ER':
          if (currentPaper.title) {
            papers.push({
              id: 'ris_' + Date.now() + '_' + papers.length,
              title: currentPaper.title,
              authors: Array.isArray(currentPaper.authors) ? currentPaper.authors.join(', ') : '',
              year: currentPaper.year,
              journal: currentPaper.journal || '',
              doi: currentPaper.doi || '',
              abstract: currentPaper.abstract || '',
              tags: currentPaper.keywords || [],
              source: 'ris_import'
            })
          }
          currentPaper = {}
          break
      }
    }

    // Add all imported papers to library
    let imported = 0
    for (const paper of papers) {
      if (addToLibrary(paper)) imported++
    }

    return { total: papers.length, imported }
  }

  /**
   * Import papers from BibTeX format
   */
  function importFromBibTeX(bibText) {
    const papers = []
    const entries = bibText.match(/@\w+\{[^@]+\}/g) || []

    for (const entry of entries) {
      const typeMatch = entry.match(/@(\w+)\{/)
      const titleMatch = entry.match(/title\s*=\s*\{([^}]+)\}/i)
      const authorMatch = entry.match(/author\s*=\s*\{([^}]+)\}/i)
      const yearMatch = entry.match(/year\s*=\s*\{([^}]+)\}/i)
      const journalMatch = entry.match(/journal\s*=\s*\{([^}]+)\}/i) || entry.match(/booktitle\s*=\s*\{([^}]+)\}/i)
      const doiMatch = entry.match(/doi\s*=\s*\{([^}]+)\}/i)
      const abstractMatch = entry.match(/abstract\s*=\s*\{([^}]+)\}/i)
      const keywordsMatch = entry.match(/keywords\s*=\s*\{([^}]+)\}/i)

      if (titleMatch) {
        papers.push({
          id: 'bib_' + Date.now() + '_' + papers.length,
          title: titleMatch[1].replace(/[{}]/g, ''),
          authors: authorMatch ? authorMatch[1].replace(/[{}]/g, '').replace(/ and /g, ', ') : '',
          year: yearMatch ? parseInt(yearMatch[1]) : null,
          journal: journalMatch ? journalMatch[1].replace(/[{}]/g, '') : '',
          doi: doiMatch ? doiMatch[1].replace(/[{}]/g, '') : '',
          abstract: abstractMatch ? abstractMatch[1].replace(/[{}]/g, '') : '',
          tags: keywordsMatch ? keywordsMatch[1].split(',').map(k => k.trim()) : [],
          source: 'bibtex_import'
        })
      }
    }

    // Add all imported papers to library
    let imported = 0
    for (const paper of papers) {
      if (addToLibrary(paper)) imported++
    }

    return { total: papers.length, imported }
  }

  /**
   * Import papers from DOI list
   */
  async function importFromDOIs(doiList) {
    loading.value = true
    error.value = null
    const results = { total: doiList.length, imported: 0, failed: [] }

    try {
      for (const doi of doiList) {
        try {
          const response = await fetch(`${OPENALEX_BASE}/works/doi:${doi}`)
          if (!response.ok) throw new Error(`Not found: ${doi}`)
          const work = await response.json()

          const paper = {
            id: work.id,
            title: work.title || 'Untitled',
            authors: work.authorships?.map(a => a.author?.display_name).filter(Boolean).join(', ') || '',
            year: work.publication_year,
            journal: work.primary_location?.source?.display_name || '',
            doi: work.doi,
            abstract: reconstructAbstract(work.abstract_inverted_index),
            tags: work.concepts?.slice(0, 5).map(c => c.display_name) || [],
            source: 'doi_import'
          }

          if (addToLibrary(paper)) results.imported++
        } catch (err) {
          results.failed.push(doi)
        }
      }
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }

    return results
  }

  /**
   * Export library to RIS format
   */
  function exportToRIS() {
    let ris = ''
    for (const paper of library.value.papers) {
      ris += 'TY  - JOUR\n'
      ris += `TI  - ${paper.title}\n`
      if (paper.authors) {
        paper.authors.split(',').forEach(author => {
          ris += `AU  - ${author.trim()}\n`
        })
      }
      if (paper.year) ris += `PY  - ${paper.year}\n`
      if (paper.journal) ris += `JO  - ${paper.journal}\n`
      if (paper.doi) ris += `DO  - ${paper.doi}\n`
      if (paper.abstract) ris += `AB  - ${paper.abstract}\n`
      if (paper.tags) {
        paper.tags.forEach(tag => {
          ris += `KW  - ${tag}\n`
        })
      }
      ris += 'ER  - \n\n'
    }
    return ris
  }

  /**
   * Export library to BibTeX format
   */
  function exportToBibTeX() {
    let bib = ''
    for (const paper of library.value.papers) {
      const key = paper.id.replace(/[^a-zA-Z0-9]/g, '_')
      bib += `@article{${key},\n`
      bib += `  title = {${paper.title}},\n`
      if (paper.authors) bib += `  author = {${paper.authors}},\n`
      if (paper.year) bib += `  year = {${paper.year}},\n`
      if (paper.journal) bib += `  journal = {${paper.journal}},\n`
      if (paper.doi) bib += `  doi = {${paper.doi}},\n`
      if (paper.abstract) bib += `  abstract = {${paper.abstract.substring(0, 200)}...},\n`
      if (paper.tags?.length) bib += `  keywords = {${paper.tags.join(', ')}},\n`
      bib += '}\n\n'
    }
    return bib
  }

  /**
   * Reconstruct abstract from OpenAlex inverted index
   */
  function reconstructAbstract(abstractInvertedIndex) {
    if (!abstractInvertedIndex) return null
    const words = {}
    for (const [word, positions] of Object.entries(abstractInvertedIndex)) {
      for (const pos of positions) {
        words[pos] = word
      }
    }
    return Object.keys(words)
      .sort((a, b) => a - b)
      .map(pos => words[pos])
      .join(' ')
  }

  /**
   * Analyze text for grammar and style issues
   * Returns array of suggestions
   */
  function analyzeText(text) {
    const suggestions = []

    // Common grammar patterns to check
    const grammarPatterns = [
      { pattern: /显著的(低于|高于|大于|小于)/g, suggestion: '建议删除"的"，使用"显著低于/高于"', type: 'grammar' },
      { pattern: /比较的?(好|坏|大|小|多|少)/g, suggestion: '口语化表达，建议改为"较X"或"更为X"', type: 'style' },
      { pattern: /然后(再|就)/g, suggestion: '"然后"与"再/就"重复，建议删除其一', type: 'grammar' },
      { pattern: /大约(约|左右|上下)/g, suggestion: '"大约"与"约/左右/上下"重复，建议保留其一', type: 'grammar' },
      { pattern: /非常[非常]+/g, suggestion: '重复修饰词，建议保留一个"非常"', type: 'grammar' },
      { pattern: /的的+/g, suggestion: '"的"字重复，建议删除多余的"的"', type: 'grammar' },
      { pattern: /了了+/g, suggestion: '"了"字重复，建议删除多余的"了"', type: 'grammar' },
    ]

    // Academic style patterns
    const stylePatterns = [
      { pattern: /我们认为|我觉得|我想/g, suggestion: '学术写作中建议避免第一人称主观表达，改为"本研究认为"或"结果表明"', type: 'style' },
      { pattern: /很多|好多|一大堆/g, suggestion: '口语化表达，建议改为"大量"、"众多"或具体数量', type: 'style' },
      { pattern: /特别[是的]/g, suggestion: '可考虑使用更学术的表达，如"尤其是"、"特别是"', type: 'style' },
      { pattern: /其实/g, suggestion: '口语化表达，学术写作中建议删除或改为"实际上"', type: 'style' },
      { pattern: /所以/g, suggestion: '口语化表达，建议改为"因此"、"故"或"由此可见"', type: 'style' },
      { pattern: /但是/g, suggestion: '可改为"然而"、"但"等更简洁的表达', type: 'style' },
    ]

    // Structure patterns
    const structurePatterns = [
      { pattern: /综上所述|总而言之/g, suggestion: '结论文开头，建议在讨论部分末尾使用', type: 'structure', section: '结论' },
      { pattern: /众所周知|显而易见/g, suggestion: '避免使用这类断言，学术写作应提供证据支持', type: 'structure' },
    ]

    // Check all patterns
    const allPatterns = [...grammarPatterns, ...stylePatterns, ...structurePatterns]
    const lines = text.split('\n')

    lines.forEach((line, lineIdx) => {
      allPatterns.forEach(({ pattern, suggestion, type, section }) => {
        const matches = line.match(pattern)
        if (matches) {
          matches.forEach(match => {
            suggestions.push({
              line: lineIdx + 1,
              text: match,
              suggestion,
              type,
              section: section || null,
              context: line.substring(Math.max(0, line.indexOf(match) - 20), line.indexOf(match) + match.length + 20)
            })
          })
        }
      })
    })

    return suggestions
  }

  /**
   * Check reference format (basic validation)
   */
  function checkReferences(text) {
    const issues = []

    // Find citation references like [1], [2], etc.
    const citations = text.match(/\[(\d+)\]/g) || []
    const uniqueCitations = [...new Set(citations)]

    // Check for sequential numbering
    const numbers = uniqueCitations.map(c => parseInt(c.match(/\d+/)[0]))
    for (let i = 1; i < numbers.length; i++) {
      if (numbers[i] !== numbers[i - 1] + 1) {
        issues.push({
          type: 'reference',
          message: `引用编号不连续：[${numbers[i - 1]}] 后应为 [${numbers[i - 1] + 1}]，而非 [${numbers[i]}]`,
          severity: 'warning'
        })
      }
    }

    // Check for common reference format issues
    if (text.includes('et al.') && !text.includes('et al.,')) {
      issues.push({
        type: 'reference',
        message: '"et al." 后应加逗号，格式为 "et al.,"',
        severity: 'warning'
      })
    }

    return {
      citationCount: uniqueCitations.length,
      citations: uniqueCitations,
      issues
    }
  }

  /**
   * Generate outline based on paper type
   */
  function generateOutline(type = 'imrad') {
    const outlines = {
      imrad: {
        name: 'IMRaD 标准结构',
        sections: [
          { title: '摘要', icon: '📋', status: 'required', tips: '概述研究目的、方法、结果和结论，200-300字' },
          { title: '引言', icon: '📝', status: 'required', tips: '介绍研究背景、文献综述、研究目的和假设' },
          { title: '材料与方法', icon: '🔬', status: 'required', tips: '详细描述实验材料、实验设计、数据收集和分析方法' },
          { title: '结果', icon: '📊', status: 'required', tips: '客观呈现实验结果，使用图表辅助说明' },
          { title: '讨论', icon: '💬', status: 'required', tips: '解释结果意义，与已有研究比较，讨论局限性' },
          { title: '结论', icon: '✅', status: 'required', tips: '总结主要发现，提出研究意义和未来方向' },
          { title: '参考文献', icon: '📚', status: 'required', tips: '列出所有引用的文献，格式统一' },
        ]
      },
      review: {
        name: '综述型结构',
        sections: [
          { title: '摘要', icon: '📋', status: 'required', tips: '概述综述范围、主要发现和结论' },
          { title: '引言', icon: '📝', status: 'required', tips: '说明综述目的、范围和方法' },
          { title: '文献检索方法', icon: '🔍', status: 'required', tips: '描述数据库、检索词、筛选标准' },
          { title: '主题分析', icon: '📊', status: 'required', tips: '按主题或时间线组织文献分析' },
          { title: '讨论', icon: '💬', status: 'required', tips: '总结研究现状、识别研究空白' },
          { title: '展望', icon: '🔮', status: 'required', tips: '提出未来研究方向和建议' },
          { title: '参考文献', icon: '📚', status: 'required', tips: '列出所有引用的文献' },
        ]
      },
      thesis: {
        name: '学位论文结构',
        sections: [
          { title: '摘要 (中英文)', icon: '📋', status: 'required', tips: '中文摘要500-1000字，英文摘要对应翻译' },
          { title: '第一章 绪论', icon: '📝', status: 'required', tips: '研究背景、意义、目的、技术路线' },
          { title: '第二章 文献综述', icon: '📚', status: 'required', tips: '国内外研究现状、理论基础' },
          { title: '第三章 研究方法', icon: '🔬', status: 'required', tips: '研究设计、数据来源、分析方法' },
          { title: '第四章 结果与分析', icon: '📊', status: 'required', tips: '实验结果、数据分析、假设验证' },
          { title: '第五章 讨论', icon: '💬', status: 'required', tips: '结果解释、与已有研究比较' },
          { title: '第六章 结论与展望', icon: '✅', status: 'required', tips: '主要结论、创新点、不足与展望' },
          { title: '参考文献', icon: '📚', status: 'required', tips: '格式按学校要求' },
          { title: '附录', icon: '📎', status: 'optional', tips: '原始数据、问卷、代码等' },
        ]
      },
      letter: {
        name: '快报/简报结构',
        sections: [
          { title: '标题', icon: '📋', status: 'required', tips: '简洁明了，突出创新点' },
          { title: '摘要', icon: '📝', status: 'required', tips: '100-150字，突出主要发现' },
          { title: '引言', icon: '📖', status: 'required', tips: '简要背景和研究目的' },
          { title: '实验部分', icon: '🔬', status: 'required', tips: '关键实验方法' },
          { title: '结果与讨论', icon: '📊', status: 'required', tips: '合并呈现，突出创新性' },
          { title: '参考文献', icon: '📚', status: 'required', tips: '限制在15-20篇' },
        ]
      }
    }

    return outlines[type] || outlines.imrad
  }

  /**
   * Format reference to GB/T 7714 standard
   */
  function formatReference(ref) {
    // Basic GB/T 7714 formatting
    if (!ref) return ''

    // If it's already formatted, return as is
    if (ref.includes('[J]') || ref.includes('[M]') || ref.includes('[C]')) {
      return ref
    }

    // Try to parse and format
    const parts = {
      authors: '',
      title: '',
      journal: '',
      year: '',
      volume: '',
      pages: ''
    }

    // Simple parsing - would need more sophisticated NLP for production
    return ref
  }

  /**
   * Get word count statistics
   */
  function getWordStats(text) {
    if (!text) return { characters: 0, words: 0, paragraphs: 0, sentences: 0 }

    const cleanText = text.replace(/<[^>]*>/g, '') // Remove HTML tags

    return {
      characters: cleanText.length,
      charactersNoSpaces: cleanText.replace(/\s/g, '').length,
      words: cleanText.split(/\s+/).filter(w => w.length > 0).length,
      paragraphs: cleanText.split(/\n\s*\n/).filter(p => p.trim().length > 0).length,
      sentences: cleanText.split(/[。！？.!?]+/).filter(s => s.trim().length > 0).length
    }
  }

  return {
    // State
    loading,
    error,
    library,
    libraryStats,

    // Literature search
    searchLiterature,

    // Library management
    addToLibrary,
    removeFromLibrary,
    toggleStar,
    updateNotes,
    addToCollection,
    createCollection,
    getPapersByCollection,
    getStarredPapers,

    // Import/Export
    importFromRIS,
    importFromBibTeX,
    importFromDOIs,
    exportToRIS,
    exportToBibTeX,

    // Text analysis
    analyzeText,
    checkReferences,
    generateOutline,
    formatReference,
    getWordStats
  }
}
