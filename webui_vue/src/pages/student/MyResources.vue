<template>
  <div class="my-resources" :class="{ 'review-active': reviewMode }">

    <!-- ==================== 复习模式（全屏覆盖） ==================== -->
    <div v-if="reviewMode" class="review-session">
      <!-- Review Config -->
      <div v-if="!reviewStarted && !reviewFinished" class="review-config">
        <h3 class="config-title">复习设置</h3>

        <!-- Category Selection -->
        <div class="config-section">
          <h4 class="config-label">选择题库</h4>
          <div class="config-chips">
            <label class="chip-option" :class="{ selected: reviewCategory === 'all' }">
              <input type="radio" value="all" v-model="reviewCategory" />
              <span>全部题目</span>
              <span class="chip-count">{{ questions.length }}</span>
            </label>
            <label class="chip-option" :class="{ selected: reviewCategory === 'uncategorized' }">
              <input type="radio" value="uncategorized" v-model="reviewCategory" />
              <span>未分类</span>
              <span class="chip-count">{{ questions.filter(q => !q.category_id).length }}</span>
            </label>
            <label v-for="cat in categories" :key="cat.id" class="chip-option" :class="{ selected: reviewCategory === cat.id }">
              <input type="radio" :value="cat.id" v-model="reviewCategory" />
              <span class="cat-dot" :style="{ background: cat.color || '#526e5a' }"></span>
              <span>{{ cat.name }}</span>
              <span class="chip-count">{{ cat.question_count }}</span>
            </label>
          </div>
        </div>

        <!-- Type Selection -->
        <div class="config-section">
          <h4 class="config-label">选择题型</h4>
          <div class="config-chips">
            <label v-for="type in reviewTypeOptions" :key="type.key" class="chip-option" :class="{ selected: reviewSelectedTypes.includes(type.key) }">
              <input type="checkbox" :value="type.key" v-model="reviewSelectedTypes" />
              <span>{{ type.label }}</span>
              <span class="chip-count">{{ getReviewTypeCount(type.key) }}</span>
            </label>
          </div>
        </div>

        <!-- Quantity -->
        <div class="config-section">
          <h4 class="config-label">复习数量</h4>
          <div class="config-chips">
            <button v-for="n in [5,10,15,20]" :key="n" class="chip-btn" :class="{ selected: reviewCount === n }" @click="reviewCount = n">{{ n }}</button>
            <button class="chip-btn" :class="{ selected: reviewCount === 0 }" @click="reviewCount = 0">全部</button>
          </div>
        </div>

        <div class="config-actions">
          <button class="btn-ghost" @click="reviewMode = false">取消</button>
          <button class="btn-dark" @click="beginReview" :disabled="reviewSelectedTypes.length === 0 || reviewTotal === 0">开始 ({{ reviewTotal }}题)</button>
        </div>
      </div>

      <!-- Review Question -->
      <div v-else-if="reviewStarted && !reviewFinished" class="review-question">
        <!-- Breadcrumb with Score -->
        <div class="review-breadcrumb">
          <span class="breadcrumb-text">我的题库</span>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">复习模式</span>
          <span class="review-counter">{{ reviewCorrectCount }}对 {{ reviewIndex + 1 - reviewCorrectCount }}错 · {{ reviewIndex + 1 }}/{{ reviewQuestions.length }}</span>
        </div>

        <!-- Main Content Area -->
        <div class="review-main">
          <!-- Question -->
          <h1 class="review-question-text">{{ reviewCurrentQ?.content }}</h1>

          <!-- Options -->
          <div class="review-options-list">
            <!-- Choice Options -->
            <template v-if="(reviewCurrentQ?.questionType || reviewCurrentQ?.metadata?.question_type) === 'choice'">
              <div v-for="opt in (reviewCurrentQ?.options || reviewCurrentQ?.metadata?.options)" :key="opt.key"
                   class="review-opt"
                   :class="{
                     'answered': reviewShowAnswer,
                     'selected-wrong': reviewShowAnswer && reviewUserAnswer === opt.key && opt.key !== (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer),
                     'correct': reviewShowAnswer && opt.key === (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer),
                     'user-selected': reviewShowAnswer && reviewUserAnswer === opt.key && opt.key !== (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer)
                   }"
                   @click="selectReviewAnswer(opt.key)">
                <div class="review-opt-header">
                  <span>{{ opt.key }}. {{ opt.text }}</span>
                  <span v-if="reviewShowAnswer && reviewUserAnswer === opt.key && opt.key !== (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer)" class="opt-tag wrong">你的错选</span>
                  <span v-if="reviewShowAnswer && opt.key === (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer)" class="opt-tag correct">正确选项</span>
                </div>
                <div v-if="reviewShowAnswer && (opt.key === reviewUserAnswer || opt.key === (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer))" class="review-opt-feedback">
                  <template v-if="opt.key === (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer)">
                    <div class="feedback-status correct">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                      <span>正确</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这是正确答案' }}</p>
                  </template>
                  <template v-else-if="opt.key === reviewUserAnswer">
                    <div class="feedback-status wrong">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                      <span>不全对</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这个选项不正确' }}</p>
                  </template>
                </div>
              </div>
            </template>

            <!-- True/False -->
            <template v-else-if="(reviewCurrentQ?.questionType || reviewCurrentQ?.metadata?.question_type) === 'true_false'">
              <div class="review-opt" :class="{ 'answered': reviewShowAnswer, 'selected-wrong': reviewShowAnswer && reviewUserAnswer === 'true' && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) !== 'true', 'correct': reviewShowAnswer && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'true' }" @click="selectReviewAnswer('true')">
                <div class="review-opt-header">
                  <span>✓ 正确</span>
                  <span v-if="reviewShowAnswer && reviewUserAnswer === 'true' && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) !== 'true'" class="opt-tag wrong">你的选择</span>
                  <span v-if="reviewShowAnswer && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'true'" class="opt-tag correct">正确答案</span>
                </div>
                <div v-if="reviewShowAnswer && (reviewUserAnswer === 'true' || (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'true')" class="review-opt-feedback">
                  <template v-if="(reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'true'">
                    <div class="feedback-status correct">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                      <span>正确</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这是正确答案' }}</p>
                  </template>
                  <template v-else-if="reviewUserAnswer === 'true'">
                    <div class="feedback-status wrong">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                      <span>不正确</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这个选项不正确' }}</p>
                  </template>
                </div>
              </div>
              <div class="review-opt" :class="{ 'answered': reviewShowAnswer, 'selected-wrong': reviewShowAnswer && reviewUserAnswer === 'false' && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) !== 'false', 'correct': reviewShowAnswer && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'false' }" @click="selectReviewAnswer('false')">
                <div class="review-opt-header">
                  <span>✕ 错误</span>
                  <span v-if="reviewShowAnswer && reviewUserAnswer === 'false' && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) !== 'false'" class="opt-tag wrong">你的选择</span>
                  <span v-if="reviewShowAnswer && (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'false'" class="opt-tag correct">正确答案</span>
                </div>
                <div v-if="reviewShowAnswer && (reviewUserAnswer === 'false' || (reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'false')" class="review-opt-feedback">
                  <template v-if="(reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer) === 'false'">
                    <div class="feedback-status correct">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                      <span>正确</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这是正确答案' }}</p>
                  </template>
                  <template v-else-if="reviewUserAnswer === 'false'">
                    <div class="feedback-status wrong">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                      <span>不正确</span>
                    </div>
                    <p>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation || '这个选项不正确' }}</p>
                  </template>
                </div>
              </div>
            </template>

            <!-- Text Input -->
            <template v-else>
              <div class="review-text-input">
                <textarea v-model="reviewUserAnswer" rows="4" placeholder="输入你的答案..." :disabled="reviewShowAnswer"></textarea>
                <button v-if="!reviewShowAnswer" class="btn-submit" @click="submitTextAnswer">提交答案</button>
              </div>
              <div v-if="reviewShowAnswer" class="review-opt answered correct">
                <div class="review-opt-header">
                  <span class="opt-tag correct">正确答案</span>
                </div>
                <div class="review-opt-feedback">
                  <div class="feedback-status correct">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                    <span>参考答案</span>
                  </div>
                  <p><strong>答案：</strong>{{ reviewCurrentQ?.answer || reviewCurrentQ?.metadata?.answer }}</p>
                  <p v-if="reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation"><strong>解析：</strong>{{ reviewCurrentQ?.explanation || reviewCurrentQ?.metadata?.explanation }}</p>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Bottom Bar -->
        <div class="review-bottom-bar">
          <button class="btn-ghost-sm" v-if="reviewShowAnswer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            查看全量长文本解释
          </button>
          <div v-else></div>

          <div class="review-bottom-right">
            <button class="btn-ghost-sm" @click="saveAndExit" title="保存并退出">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              保存退出
            </button>
            <button v-if="reviewShowAnswer && reviewIndex < reviewQuestions.length - 1" class="btn-dark" @click="reviewNext">
              下一个
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </button>
            <button v-else-if="reviewShowAnswer" class="btn-dark" @click="finishReview">
              完成复习
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Review Result -->
      <div v-if="reviewFinished" class="review-result">
        <h3 class="result-title">复习完成！</h3>
        <div class="result-score">
          <div class="score-circle" :class="{ excellent: reviewAccuracy >= 90, good: reviewAccuracy >= 70, bad: reviewAccuracy < 70 }">
            <span class="score-number">{{ reviewAccuracy }}%</span>
            <span class="score-label">正确率</span>
          </div>
        </div>
        <div class="result-stats">
          <div class="stat-item">
            <span class="stat-value">{{ reviewQuestions.length }}</span>
            <span class="stat-label">总题数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value correct">{{ reviewCorrectCount }}</span>
            <span class="stat-label">答对</span>
          </div>
          <div class="stat-item">
            <span class="stat-value wrong">{{ reviewQuestions.length - reviewCorrectCount }}</span>
            <span class="stat-label">答错</span>
          </div>
          <div class="stat-item">
            <span class="stat-value points">{{ reviewTotalScore }}分</span>
            <span class="stat-label">得分</span>
          </div>
        </div>
        <div class="config-actions">
          <button class="btn-ghost" @click="reviewMode = false; reviewFinished = false">返回</button>
          <button class="btn-dark" @click="beginReview">再做一次</button>
        </div>
      </div>
    </div>

    <!-- ==================== 列表模式 ==================== -->
    <template v-if="!reviewMode">
      <!-- Header -->
      <section class="page-header">
        <div class="header-left">
          <h1 class="page-title">我的资源</h1>
          <span class="resource-count font-mono">{{ totalCount }} 项资源</span>
        </div>
        <div class="search-box">
          <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索资源..." class="search-input" />
        </div>
      </section>

      <!-- Tabs & Actions -->
      <section class="tabs-section">
        <div class="tabs-bar">
          <button v-for="tab in tabs" :key="tab.key" class="tab-btn" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
            <span class="tab-icon" v-html="tab.icon"></span>
            <span>{{ tab.label }}</span>
            <span class="tab-count font-mono">{{ getTabCount(tab.key) }}</span>
          </button>
        </div>

        <div class="actions-bar" v-if="activeTab === 'question'">
          <button class="btn-dark" @click="startReview">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            开始复习
          </button>
          <button class="btn-outline" @click="showImportForm = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>
            </svg>
            导入文本
          </button>
          <button class="btn-ai" @click="showAIForm = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
            AI 生成
          </button>
        </div>
      </section>

      <!-- Content Area -->
      <div class="content-area">

        <!-- ==================== 题库模块 ==================== -->
        <template v-if="activeTab === 'question'">
          <div class="question-layout">
            <!-- Left Sidebar: Categories -->
            <aside class="category-sidebar">
              <div class="sidebar-header">
                <span class="sidebar-title font-bold text-xs uppercase tracking-wider text-gray-400">分类</span>
                <button class="btn-icon-xs" @click="showCategoryDialog = true; editingCategory = null" title="新建分类">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
                </button>
              </div>
              <div class="category-list">
                <div class="category-item" :class="{ active: selectedCategory === 'all' }" @click="selectedCategory = 'all'">
                  <span class="category-dot" style="background: #999"></span>
                  <span class="category-name">全部题目</span>
                  <span class="category-count font-mono">{{ questions.length }}</span>
                </div>
                <div class="category-item" :class="{ active: selectedCategory === 'uncategorized' }" @click="selectedCategory = 'uncategorized'">
                  <span class="category-dot" style="background: #ccc"></span>
                  <span class="category-name">未分类</span>
                  <span class="category-count font-mono">{{ uncategorizedCount }}</span>
                </div>
                <div class="category-divider"></div>
                <div v-for="cat in categories" :key="cat.id" class="category-item" :class="{ active: selectedCategory === cat.id }" @click="selectedCategory = cat.id">
                  <span class="category-dot" :style="{ background: cat.color || '#526e5a' }"></span>
                  <span class="category-name">{{ cat.name }}</span>
                  <span class="category-count font-mono">{{ cat.question_count }}</span>
                  <div class="category-actions">
                    <button class="btn-icon-xs" @click.stop="handleEditCategory(cat)" title="编辑">✎</button>
                    <button class="btn-icon-xs danger" @click.stop="handleDeleteCategory(cat)" title="删除">×</button>
                  </div>
                </div>
              </div>
            </aside>

            <!-- Right Content -->
            <div class="question-content">
              <!-- Filter -->
              <div class="filter-bar">
                <select v-model="filterType" class="filter-select">
                  <option value="">全部题型</option>
                  <option value="choice">选择题</option>
                  <option value="true_false">判断题</option>
                  <option value="fill">填空题</option>
                  <option value="short_answer">简答题</option>
                  <option value="essay">论述题</option>
                </select>
              </div>

              <!-- Empty State -->
              <div v-if="filteredQuestions.length === 0 && !showImportForm && !showAIForm" class="empty-state">
                <div class="empty-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
                  </svg>
                </div>
                <h3>{{ selectedCategory === 'all' ? '暂无题目' : '该分类下暂无题目' }}</h3>
                <p>导入文本或使用 AI 生成题目</p>
                <div class="empty-actions">
                  <button class="btn-outline" @click="showImportForm = true">导入文本</button>
                  <button class="btn-ai" @click="showAIForm = true">AI 生成</button>
                </div>
              </div>

              <!-- Import Form -->
              <div v-if="showImportForm" class="form-card">
                <div class="form-card-header">
                  <h4>导入文本自动转换</h4>
                  <button class="close-btn" @click="showImportForm = false">×</button>
                </div>
                <div class="form-card-body">
                  <p class="form-hint">粘贴包含题目的文本，AI 将自动解析并转换为标准格式。</p>
                  <div class="import-tabs">
                    <button class="import-tab" :class="{active: importMode === 'text'}" @click="importMode = 'text'">粘贴文本</button>
                    <button class="import-tab" :class="{active: importMode === 'file'}" @click="importMode = 'file'">上传文件</button>
                  </div>
                  <div v-if="importMode === 'text'" class="import-section">
                    <textarea v-model="importText" rows="8" placeholder="粘贴题目内容..." class="form-textarea"></textarea>
                  </div>
                  <div v-if="importMode === 'file'" class="import-section">
                    <div class="file-drop" @click="triggerImportFile" @dragover.prevent @drop.prevent="handleDrop">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
                      </svg>
                      <p>点击选择文件或拖拽文件到此处</p>
                      <span>支持 TXT、PDF、Word 文档</span>
                      <input ref="importFileInput" type="file" accept=".txt,.pdf,.doc,.docx" style="display:none" @change="handleImportFile" />
                    </div>
                    <div v-if="importFileName" class="file-info">
                      <span>{{ importFileName }}</span>
                      <button class="btn-icon-xs" @click="importFileName = ''; importText = ''">×</button>
                    </div>
                  </div>
                  <!-- Category Selection -->
                  <div class="form-group">
                    <label>选择分类</label>
                    <select v-model="importCategoryId" class="form-select">
                      <option :value="null">不指定分类</option>
                      <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                    </select>
                  </div>
                </div>
                <div class="form-card-footer">
                  <button class="btn-ghost" @click="showImportForm = false">取消</button>
                  <button class="btn-dark" @click="handleImportParse" :disabled="isParsing || !importText.trim()">
                    {{ isParsing ? '解析中...' : 'AI 解析' }}
                  </button>
                </div>
              </div>

              <!-- AI Form -->
              <div v-if="showAIForm" class="form-card">
                <div class="form-card-header">
                  <h4>AI 智能出题</h4>
                  <button class="close-btn" @click="showAIForm = false">×</button>
                </div>
                <div class="form-card-body">
                  <div class="form-group">
                    <label>知识内容</label>
                    <textarea v-model="aiForm.content" rows="4" placeholder="粘贴教材、笔记或知识点..." class="form-textarea"></textarea>
                  </div>
                  <div class="ai-grid">
                    <div class="form-group"><label>题目数量</label><input v-model.number="aiForm.numQuestions" type="number" min="1" max="50" class="form-input" /></div>
                    <div class="form-group"><label>选择题</label><input v-model.number="aiForm.typeDistribution.choice" type="number" min="0" class="form-input" placeholder="0" /></div>
                    <div class="form-group"><label>判断题</label><input v-model.number="aiForm.typeDistribution.true_false" type="number" min="0" class="form-input" placeholder="0" /></div>
                    <div class="form-group"><label>填空题</label><input v-model.number="aiForm.typeDistribution.fill" type="number" min="0" class="form-input" placeholder="0" /></div>
                    <div class="form-group"><label>简答题</label><input v-model.number="aiForm.typeDistribution.short_answer" type="number" min="0" class="form-input" placeholder="0" /></div>
                    <div class="form-group"><label>论述题</label><input v-model.number="aiForm.typeDistribution.essay" type="number" min="0" class="form-input" placeholder="0" /></div>
                  </div>
                  <div class="form-group">
                    <label>选择分类</label>
                    <select v-model="aiCategoryId" class="form-select">
                      <option :value="null">不指定分类</option>
                      <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                    </select>
                  </div>
                </div>
                <div class="form-card-footer">
                  <button class="btn-ghost" @click="showAIForm = false">取消</button>
                  <button class="btn-dark" @click="handleAIGenerate" :disabled="aiGenerating || !aiForm.content.trim()">{{ aiGenerating ? '生成中...' : '生成题目' }}</button>
                </div>
              </div>

              <!-- AI Preview -->
              <div v-if="previewQuestions.length > 0 || isParsing" class="preview-card">
                <div class="preview-header">
                  <div class="preview-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                    <span>AI 解析预览（{{ previewQuestions.length }} 道题目）</span>
                    <span v-if="isParsing" class="parsing-badge">解析中...</span>
                  </div>
                  <div class="preview-actions">
                    <button class="btn-ghost" @click="clearAll()">丢弃</button>
                    <button class="btn-dark" @click="handleSavePreview" :disabled="previewSaving || isParsing">{{ previewSaving ? '保存中...' : '全部入库' }}</button>
                  </div>
                </div>
                <div class="preview-hint">
                  <template v-if="isParsing">正在解析中，可以切换页面，解析会继续进行...</template>
                  <template v-else>请检查题目，确认后批量入库。</template>
                </div>
                <div class="preview-list">
                  <div v-for="(q, qi) in previewQuestions" :key="qi" class="q-card preview">
                    <div class="q-top">
                      <span class="q-num font-mono">{{ qi+1 }}</span>
                      <span class="q-type">{{ getTypeLabel(q.type) }}</span>
                      <span class="q-pts font-mono">{{ q.points }}分</span>
                      <button class="btn-icon-xs" @click="removeQuestion(qi)" title="移除">×</button>
                    </div>
                    <div class="q-content" @click="toggleExpand('preview-'+qi)">{{ q.content }}</div>
                    <template v-if="isExpanded('preview-'+qi)">
                      <div v-if="q.type==='choice' && q.options" class="q-options">
                        <div v-for="opt in q.options" :key="opt.key" class="q-opt"><span class="opt-key font-mono" :class="{correct:opt.key===q.answer}">{{ opt.key }}.</span>{{ opt.text }}</div>
                      </div>
                      <div v-if="q.answer" class="q-answer"><span class="label">答案：</span>{{ q.answer }}</div>
                      <div v-if="q.explanation" class="q-explain"><span class="label">解析：</span>{{ q.explanation }}</div>
                    </template>
                    <div class="q-expand-hint" @click="toggleExpand('preview-'+qi)">
                      {{ isExpanded('preview-'+qi) ? '收起' : '展开详情' }}
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: isExpanded('preview-'+qi) ? 'rotate(180deg)' : 'rotate(0deg)' }"><path d="m6 9 6 6 6-6"/></svg>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Question List -->
              <div v-if="filteredQuestions.length > 0 && !showImportForm && !showAIForm && previewQuestions.length === 0" class="question-list">
                <div v-for="(q, qi) in filteredQuestions" :key="q.id" class="q-card" :class="{editing: editingQuestion?.id === q.id}">
                  <template v-if="editingQuestion?.id !== q.id">
                    <div class="q-top">
                      <span class="q-num font-mono text-[#121212]">{{ qi+1 }}</span>
                      <span class="q-type bg-white text-gray-600 border border-gray-200/60">{{ getTypeLabel(q.questionType || q.metadata?.question_type) }}</span>
                      <span class="q-pts font-mono">{{ q.points || q.metadata?.points || 10 }}分</span>
                      <span v-if="getCategoryName(q.category_id)" class="q-category bg-gray-200/50 text-gray-600"># {{ getCategoryName(q.category_id) }}</span>
                      <div class="q-actions">
                        <select class="category-select" :value="q.category_id || ''" @change="handleCategorize(q, $event.target.value)" @click.stop>
                          <option value="">未分类</option>
                          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                        </select>
                        <button class="btn-icon" @click="handleEdit(q)" title="编辑">✎</button>
                        <button class="btn-icon danger" @click="handleDelete(q)" title="删除">✕</button>
                      </div>
                    </div>
                    <div class="q-content font-serif-sc" @click="toggleExpand(q.id)">{{ q.content }}</div>
                    <template v-if="isExpanded(q.id)">
                      <div v-if="(q.questionType||q.metadata?.question_type)==='choice' && (q.options||q.metadata?.options)" class="q-options">
                        <div v-for="opt in (q.options||q.metadata?.options)" :key="opt.key" class="q-opt"><span class="opt-key font-mono" :class="{correct:opt.key===(q.answer||q.metadata?.answer)}">{{ opt.key }}.</span>{{ opt.text }}</div>
                      </div>
                      <div v-if="q.answer||q.metadata?.answer" class="q-answer"><span class="label">答案：</span>{{ q.answer || q.metadata?.answer }}</div>
                      <div v-if="q.explanation||q.metadata?.explanation" class="q-explain"><span class="label">解析：</span>{{ q.explanation || q.metadata?.explanation }}</div>
                    </template>
                    <div class="q-expand-hint" @click="toggleExpand(q.id)">
                      {{ isExpanded(q.id) ? '收起' : '展开详情' }}
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: isExpanded(q.id) ? 'rotate(180deg)' : 'rotate(0deg)' }"><path d="m6 9 6 6 6-6"/></svg>
                    </div>
                  </template>
                  <template v-else>
                    <div class="edit-form">
                      <div class="form-row">
                        <select v-model="editingQuestion.questionType" class="form-select">
                          <option value="choice">选择题</option>
                          <option value="true_false">判断题</option>
                          <option value="fill">填空题</option>
                          <option value="short_answer">简答题</option>
                          <option value="essay">论述题</option>
                        </select>
                        <input v-model.number="editingQuestion.points" type="number" min="1" class="form-input w-24" placeholder="分值" />
                      </div>
                      <textarea v-model="editingQuestion.content" rows="3" class="form-textarea" placeholder="题目内容"></textarea>
                      <div v-if="editingQuestion.questionType==='choice'" class="options-section">
                        <div v-for="(opt,oi) in editingQuestion.options" :key="oi" class="option-row">
                          <span class="opt-key font-mono">{{ String.fromCharCode(65+oi) }}.</span>
                          <input v-model="editingQuestion.options[oi].text" class="form-input" />
                          <button class="btn-icon-xs" @click="editingQuestion.options.splice(oi,1)">×</button>
                        </div>
                        <button class="btn-dashed" @click="editingQuestion.options.push({key:String.fromCharCode(65+editingQuestion.options.length),text:''})">+ 添加选项</button>
                        <div class="answer-row">
                          <label>正确答案：</label>
                          <select v-model="editingQuestion.answer" class="form-select w-24">
                            <option v-for="opt in editingQuestion.options" :key="opt.key" :value="opt.key">{{ opt.key }}</option>
                          </select>
                        </div>
                      </div>
                      <div v-if="editingQuestion.questionType==='true_false'" class="answer-row">
                        <label>正确答案：</label>
                        <select v-model="editingQuestion.answer" class="form-select w-24">
                          <option value="true">正确</option>
                          <option value="false">错误</option>
                        </select>
                      </div>
                      <div v-if="['fill','short_answer','essay'].includes(editingQuestion.questionType)" class="answer-row">
                        <label>参考答案：</label>
                        <textarea v-model="editingQuestion.answer" rows="2" class="form-textarea"></textarea>
                      </div>
                      <textarea v-model="editingQuestion.explanation" rows="2" class="form-textarea" placeholder="解析（可选）"></textarea>
                    </div>
                    <div class="edit-actions">
                      <button class="btn-ghost" @click="editingQuestion=null">取消</button>
                      <button class="btn-dark" @click="handleSaveEdit" :disabled="!editingQuestion.content.trim()">保存</button>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ==================== 资料模块 ==================== -->
        <template v-if="activeTab === 'file'">
          <div class="toolbar">
            <div class="toolbar-info">共 {{ files.length }} 个文件</div>
            <button class="btn-dark" @click="triggerUpload">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
              </svg>
              上传文件
            </button>
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.md,.jpg,.jpeg,.png,.gif" style="display:none" @change="handleFileUpload" />
          </div>
          <div v-if="files.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <h3>暂无学习资料</h3>
            <p>上传 PDF、Word、PPT 等文件</p>
            <button class="btn-dark" @click="triggerUpload">上传文件</button>
          </div>
          <div v-else class="file-grid">
            <div v-for="f in files" :key="f.id" class="file-card">
              <div class="file-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div class="file-info">
                <div class="file-name">{{ f.title }}</div>
                <div class="file-meta">{{ formatFileSize(f.file_size) }} · {{ formatDate(f.created_at) }}</div>
              </div>
              <div class="file-actions">
                <button class="btn-icon danger" @click="handleDeleteFile(f)" title="删除">✕</button>
              </div>
            </div>
          </div>
        </template>

        <!-- ==================== 笔记模块 ==================== -->
        <template v-if="activeTab === 'note'">
          <div class="toolbar">
            <div class="toolbar-info">共 {{ notes.length }} 条笔记</div>
            <button class="btn-dark" @click="startCreateNote">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
              新建笔记
            </button>
          </div>
          <div v-if="notes.length === 0 && !editingNote" class="empty-state">
            <div class="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4Z"/></svg>
            </div>
            <h3>暂无笔记</h3>
            <p>记录学习心得和知识要点</p>
            <button class="btn-dark" @click="startCreateNote">新建笔记</button>
          </div>
          <div v-if="editingNote" class="note-editor">
            <input v-model="editingNote.title" class="note-title-input" placeholder="笔记标题" />
            <textarea v-model="editingNote.content" class="note-content-input" placeholder="开始记录..." rows="12"></textarea>
            <div class="note-actions">
              <button class="btn-ghost" @click="editingNote = null">取消</button>
              <button class="btn-dark" @click="handleSaveNote" :disabled="!editingNote.title.trim()">保存</button>
            </div>
          </div>
          <div v-if="notes.length > 0 && !editingNote" class="note-grid">
            <div v-for="n in notes" :key="n.id" class="note-card" @click="handleEditNote(n)">
              <div class="note-card-header">
                <div class="note-title">{{ n.title }}</div>
                <div class="note-actions-inner">
                  <button class="btn-icon danger" @click.stop="handleDeleteNote(n)" title="删除">✕</button>
                </div>
              </div>
              <div class="note-preview">{{ n.content?.substring(0, 150) }}{{ n.content?.length > 150 ? '...' : '' }}</div>
              <div class="note-date">{{ formatDate(n.created_at) }}</div>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- Category Dialog -->
    <Teleport to="body">
      <div v-if="showCategoryDialog" class="dialog-overlay" @click.self="showCategoryDialog = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h2>{{ editingCategory ? '编辑分类' : '新建分类' }}</h2>
            <button class="close-btn" @click="showCategoryDialog = false">×</button>
          </div>
          <div class="dialog-body">
            <div class="form-group">
              <label>分类名称</label>
              <input v-model="categoryForm.name" type="text" placeholder="如：深度学习、机器学习" class="form-input" />
            </div>
            <div class="form-group">
              <label>描述（可选）</label>
              <textarea v-model="categoryForm.description" rows="2" placeholder="分类描述" class="form-textarea"></textarea>
            </div>
            <div class="form-group">
              <label>颜色</label>
              <div class="color-options">
                <div v-for="color in colorOptions" :key="color" class="color-option" :class="{ active: categoryForm.color === color }" :style="{ background: color }" @click="categoryForm.color = color"></div>
              </div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showCategoryDialog = false">取消</button>
            <button class="btn-dark" @click="handleSaveCategory" :disabled="!categoryForm.name.trim()">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useMyResources } from '../../composables/useMyResources.js'
import { useGateway } from '../../composables/useGateway.js'
import { useParseContainer } from '../../composables/useParseContainer.js'

const {
  resources, categories, loading, error,
  fetchResources, createResource, deleteResource, updateResource, uploadFile,
  fetchCategories, createCategory, updateCategory, deleteCategory, categorizeResource
} = useMyResources()
const { getToken, sendAiGenerateQuestions, sendAiParseQuestions } = useGateway()
const {
  previewQuestions, isParsing, parseError,
  addQuestion, setParsing, setError, clearAll, removeQuestion
} = useParseContainer()

// State
const activeTab = ref('question')
const searchQuery = ref('')
const filterType = ref('')
const selectedCategory = ref('all')
const showImportForm = ref(false)
const showAIForm = ref(false)
const aiGenerating = ref(false)
const editingQuestion = ref(null)
const previewSaving = ref(false)
const editingNote = ref(null)
const fileInput = ref(null)
const importMode = ref('text')
const importText = ref('')
const importFileName = ref('')
const importFileInput = ref(null)
const importCategoryId = ref(null)
const aiCategoryId = ref(null)
const showCategoryDialog = ref(false)
const editingCategory = ref(null)
const categoryForm = reactive({ name: '', description: '', color: '#526e5a' })
const expandedQuestions = ref(new Set())

// Review state
const reviewMode = ref(false)
const reviewStarted = ref(false)
const reviewFinished = ref(false)
const reviewCategory = ref('all')
const reviewSelectedTypes = ref(['choice', 'true_false', 'fill', 'short_answer', 'essay'])
const reviewCount = ref(10)
const reviewQuestions = ref([])
const reviewIndex = ref(0)
const reviewUserAnswer = ref('')
const reviewShowAnswer = ref(false)
const reviewAnswers = ref({})
const reviewTypeOptions = [
  { key: 'choice', label: '选择题' },
  { key: 'true_false', label: '判断题' },
  { key: 'fill', label: '填空题' },
  { key: 'short_answer', label: '简答题' },
  { key: 'essay', label: '论述题' }
]

const colorOptions = ['#526e5a', '#1976d2', '#f57c00', '#388e3c', '#7b1fa2', '#c62828', '#00838f', '#4e342e']

const tabs = [
  { key: 'question', label: '我的题库', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>' },
  { key: 'file', label: '学习资料', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' },
  { key: 'note', label: '笔记', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4Z"/></svg>' }
]

const aiForm = reactive({ content: '', numQuestions: 10, typeDistribution: { choice: 0, true_false: 0, fill: 0, short_answer: 0, essay: 0 } })

// Computed
const questions = computed(() => resources.value.filter(r => r.resource_type === 'question'))
const files = computed(() => resources.value.filter(r => r.resource_type === 'file'))
const notes = computed(() => resources.value.filter(r => r.resource_type === 'note'))
const totalCount = computed(() => resources.value.length)
const uncategorizedCount = computed(() => questions.value.filter(q => !q.category_id).length)

const filteredQuestions = computed(() => {
  let result = questions.value
  if (selectedCategory.value === 'uncategorized') {
    result = result.filter(q => !q.category_id)
  } else if (selectedCategory.value !== 'all') {
    result = result.filter(q => q.category_id === selectedCategory.value)
  }
  if (filterType.value) {
    result = result.filter(q => (q.questionType || q.metadata?.question_type) === filterType.value)
  }
  if (searchQuery.value) {
    const s = searchQuery.value.toLowerCase()
    result = result.filter(q => q.content?.toLowerCase().includes(s) || q.title?.toLowerCase().includes(s))
  }
  return result
})

function getTabCount(key) {
  if (key === 'question') return questions.value.length
  if (key === 'file') return files.value.length
  return notes.value.length
}

function getTypeLabel(type) {
  return { choice: '选择题', true_false: '判断题', fill: '填空题', short_answer: '简答题', essay: '论述题' }[type] || type
}

function getCategoryName(catId) {
  if (!catId) return null
  const cat = categories.value.find(c => c.id === catId)
  return cat?.name || null
}

function getCategoryColor(catId) {
  if (!catId) return '#999'
  const cat = categories.value.find(c => c.id === catId)
  return cat?.color || '#526e5a'
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const u = ['B','KB','MB','GB']
  let i = 0, s = bytes
  while (s >= 1024 && i < 3) { s /= 1024; i++ }
  return s.toFixed(1) + ' ' + u[i]
}

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d), now = new Date(), diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff/60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff/3600000) + '小时前'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function toggleExpand(qId) {
  if (expandedQuestions.value.has(qId)) {
    expandedQuestions.value.delete(qId)
  } else {
    expandedQuestions.value.add(qId)
  }
}

function isExpanded(qId) {
  return expandedQuestions.value.has(qId)
}

// Review functions
function getTypeCount(type) {
  return questions.value.filter(q => (q.questionType || q.metadata?.question_type) === type).length
}

function getReviewTypeCount(type) {
  let filtered = questions.value
  if (reviewCategory.value === 'uncategorized') {
    filtered = filtered.filter(q => !q.category_id)
  } else if (reviewCategory.value !== 'all') {
    filtered = filtered.filter(q => q.category_id === reviewCategory.value)
  }
  return filtered.filter(q => (q.questionType || q.metadata?.question_type) === type).length
}

const reviewTotal = computed(() => {
  let filtered = questions.value
  if (reviewCategory.value === 'uncategorized') {
    filtered = filtered.filter(q => !q.category_id)
  } else if (reviewCategory.value !== 'all') {
    filtered = filtered.filter(q => q.category_id === reviewCategory.value)
  }
  filtered = filtered.filter(q => reviewSelectedTypes.value.includes(q.questionType || q.metadata?.question_type))
  return reviewCount.value === 0 ? filtered.length : Math.min(reviewCount.value, filtered.length)
})

const reviewCurrentQ = computed(() => reviewQuestions.value[reviewIndex.value])

const reviewProgressPercent = computed(() => {
  if (reviewQuestions.value.length === 0) return 0
  return ((reviewIndex.value + 1) / reviewQuestions.value.length) * 100
})

const reviewIsCorrect = computed(() => {
  if (!reviewCurrentQ.value || !reviewShowAnswer.value) return false
  const correct = (reviewCurrentQ.value.answer || reviewCurrentQ.value.metadata?.answer || '').toLowerCase()
  return (reviewUserAnswer.value || '').toLowerCase() === correct
})

const reviewCorrectCount = computed(() => {
  return Object.values(reviewAnswers.value).filter(a => a.correct).length
})

const reviewAccuracy = computed(() => {
  if (reviewQuestions.value.length === 0) return 0
  return Math.round((reviewCorrectCount.value / reviewQuestions.value.length) * 100)
})

const reviewTotalScore = computed(() => {
  let score = 0
  for (const [qId, answer] of Object.entries(reviewAnswers.value)) {
    if (answer.correct) {
      const q = reviewQuestions.value.find(q => q.id === qId)
      score += q?.points || q?.metadata?.points || 10
    }
  }
  return score
})

const hasSavedProgress = computed(() => {
  return loadReviewProgress() !== null
})

function startReview() {
  const saved = loadReviewProgress()
  if (saved) {
    if (confirm('检测到未完成的复习，是否继续？')) {
      restoreReviewProgress(saved)
      return
    }
  }
  reviewMode.value = true
  reviewStarted.value = false
  reviewFinished.value = false
  reviewCategory.value = selectedCategory.value || 'all'
  reviewSelectedTypes.value = ['choice', 'true_false', 'fill', 'short_answer', 'essay']
  reviewCount.value = 10
}

function saveReviewProgress() {
  const progress = {
    reviewQuestions: reviewQuestions.value,
    reviewIndex: reviewIndex.value,
    reviewAnswers: reviewAnswers.value,
    reviewCategory: reviewCategory.value,
    reviewSelectedTypes: reviewSelectedTypes.value,
    reviewCount: reviewCount.value,
    savedAt: new Date().toISOString()
  }
  localStorage.setItem('nanobot-review-progress', JSON.stringify(progress))
}

function loadReviewProgress() {
  try {
    const saved = localStorage.getItem('nanobot-review-progress')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load review progress:', e)
  }
  return null
}

function restoreReviewProgress(saved) {
  reviewQuestions.value = saved.reviewQuestions
  reviewIndex.value = saved.reviewIndex
  reviewAnswers.value = saved.reviewAnswers
  reviewCategory.value = saved.reviewCategory
  reviewSelectedTypes.value = saved.reviewSelectedTypes
  reviewCount.value = saved.reviewCount
  reviewMode.value = true
  reviewStarted.value = true
  reviewFinished.value = false
  loadReviewQuestion()
}

function clearReviewProgress() {
  localStorage.removeItem('nanobot-review-progress')
}

function beginReview() {
  let filtered = questions.value
  if (reviewCategory.value === 'uncategorized') {
    filtered = filtered.filter(q => !q.category_id)
  } else if (reviewCategory.value !== 'all') {
    filtered = filtered.filter(q => q.category_id === reviewCategory.value)
  }
  filtered = filtered.filter(q => reviewSelectedTypes.value.includes(q.questionType || q.metadata?.question_type))
  for (let i = filtered.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [filtered[i], filtered[j]] = [filtered[j], filtered[i]]
  }
  const count = reviewCount.value === 0 ? filtered.length : reviewCount.value
  reviewQuestions.value = filtered.slice(0, count)
  reviewIndex.value = 0
  reviewUserAnswer.value = ''
  reviewShowAnswer.value = false
  reviewAnswers.value = {}
  reviewStarted.value = true
  reviewFinished.value = false
}

function reviewPrev() {
  if (reviewIndex.value > 0) {
    reviewIndex.value--
    loadReviewQuestion()
    saveReviewProgress()
  }
}

function reviewNext() {
  if (reviewIndex.value < reviewQuestions.value.length - 1) {
    reviewIndex.value++
    loadReviewQuestion()
    saveReviewProgress()
  }
}

function recordReviewAnswer() {
  const qId = reviewCurrentQ.value.id
  reviewAnswers.value[qId] = {
    userAnswer: reviewUserAnswer.value,
    correct: reviewIsCorrect.value
  }
}

function loadReviewQuestion() {
  const qId = reviewCurrentQ.value.id
  if (reviewAnswers.value[qId]) {
    reviewUserAnswer.value = reviewAnswers.value[qId].userAnswer
    reviewShowAnswer.value = true
  } else {
    reviewUserAnswer.value = ''
    reviewShowAnswer.value = false
  }
}

function selectReviewAnswer(answer) {
  if (reviewShowAnswer.value) return
  reviewUserAnswer.value = answer
  reviewShowAnswer.value = true
  recordReviewAnswer()
  saveReviewProgress()
}

function submitTextAnswer() {
  if (!reviewUserAnswer.value.trim()) return
  reviewShowAnswer.value = true
  recordReviewAnswer()
  saveReviewProgress()
}

function finishReview() {
  if (!reviewAnswers.value[reviewCurrentQ.value.id]) {
    recordReviewAnswer()
  }
  reviewFinished.value = true
  reviewStarted.value = false
  clearReviewProgress()
}

function saveAndExit() {
  saveReviewProgress()
  reviewMode.value = false
  reviewStarted.value = false
  reviewFinished.value = false
}

// Category handlers
function handleEditCategory(cat) {
  editingCategory.value = cat
  categoryForm.name = cat.name
  categoryForm.description = cat.description || ''
  categoryForm.color = cat.color || '#526e5a'
  showCategoryDialog.value = true
}

async function handleSaveCategory() {
  if (!categoryForm.name.trim()) return
  try {
    if (editingCategory.value) {
      await updateCategory(editingCategory.value.id, { name: categoryForm.name, description: categoryForm.description, color: categoryForm.color })
    } else {
      await createCategory({ name: categoryForm.name, description: categoryForm.description, color: categoryForm.color })
    }
    showCategoryDialog.value = false
    editingCategory.value = null
    categoryForm.name = ''
    categoryForm.description = ''
    categoryForm.color = '#526e5a'
  } catch (e) { alert('保存失败: ' + e.message) }
}

async function handleDeleteCategory(cat) {
  if (!confirm(`确定删除分类"${cat.name}"？分类下的题目将变为未分类。`)) return
  try { await deleteCategory(cat.id) } catch (e) { alert('删除失败: ' + e.message) }
}

async function handleCategorize(q, value) {
  const categoryId = value === '' ? null : parseInt(value)
  try { await categorizeResource(q.id, categoryId) } catch (e) { alert('分类失败: ' + e.message) }
}

// Import handlers
function triggerImportFile() { importFileInput.value?.click() }

async function handleImportFile(e) {
  const file = e.target.files[0]
  if (!file) return
  importFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => { importText.value = e.target.result }
  reader.readAsText(file)
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) {
    importFileName.value = file.name
    const reader = new FileReader()
    reader.onload = (e) => { importText.value = e.target.result }
    reader.readAsText(file)
  }
}

async function handleImportParse() {
  if (!importText.value.trim()) return
  setParsing(true)
  clearAll()
  try {
    const result = await sendAiParseQuestions({
      content: importText.value,
      onItem: (question) => {
        addQuestion(question)
      }
    })
    showImportForm.value = false
  } catch (e) {
    setError(e.message)
    alert('解析失败: ' + e.message)
  } finally {
    setParsing(false)
  }
}

async function handleAIGenerate() {
  aiGenerating.value = true
  clearAll()
  try {
    const result = await sendAiGenerateQuestions({ content: aiForm.content, numQuestions: aiForm.numQuestions, typeDistribution: aiForm.typeDistribution })
    if (result?.questions) {
      result.questions.forEach(q => addQuestion(q))
      showAIForm.value = false
    }
  } catch (e) { alert('生成失败: ' + e.message) }
  finally { aiGenerating.value = false }
}

async function handleSavePreview() {
  previewSaving.value = true
  try {
    const categoryId = importCategoryId.value || aiCategoryId.value || null
    for (const q of previewQuestions.value) {
      await createResource({
        resource_type: 'question', title: q.content.substring(0,100), content: q.content, source_type: 'ai', category_id: categoryId,
        metadata: { question_type: q.type, points: q.points, answer: q.answer, options: q.options || [], explanation: q.explanation }
      })
    }
    clearAll()
    importCategoryId.value = null
    aiCategoryId.value = null
    alert('已保存')
  } catch (e) { alert('保存失败: ' + e.message) }
  finally { previewSaving.value = false }
}

function handleEdit(q) {
  editingQuestion.value = {
    id: q.id, questionType: q.questionType || q.metadata?.question_type || 'short_answer',
    content: q.content || '', points: q.points || q.metadata?.points || 10,
    answer: q.answer || q.metadata?.answer || '', options: q.options || q.metadata?.options || [],
    explanation: q.explanation || q.metadata?.explanation || ''
  }
}

async function handleSaveEdit() {
  try {
    await updateResource(editingQuestion.value.id, {
      title: editingQuestion.value.content.substring(0,100), content: editingQuestion.value.content,
      metadata: { question_type: editingQuestion.value.questionType, points: editingQuestion.value.points,
        answer: editingQuestion.value.answer, options: editingQuestion.value.options, explanation: editingQuestion.value.explanation }
    })
    editingQuestion.value = null
  } catch (e) { alert('保存失败: ' + e.message) }
}

async function handleDelete(q) {
  if (!confirm('确定删除？')) return
  try { await deleteResource(q.id) } catch (e) { alert('删除失败: ' + e.message) }
}

function triggerUpload() { fileInput.value?.click() }

async function handleFileUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try { await uploadFile(file); e.target.value = '' }
  catch (err) { alert('上传失败: ' + err.message) }
}

async function handleDeleteFile(f) {
  if (!confirm('确定删除？')) return
  try { await deleteResource(f.id) } catch (e) { alert('删除失败: ' + e.message) }
}

function startCreateNote() { editingNote.value = { id: null, title: '', content: '' } }
function handleEditNote(n) { editingNote.value = { id: n.id, title: n.title, content: n.content || '' } }

async function handleSaveNote() {
  if (!editingNote.value.title.trim()) return
  try {
    if (editingNote.value.id) {
      await updateResource(editingNote.value.id, { title: editingNote.value.title, content: editingNote.value.content })
    } else {
      await createResource({ resource_type: 'note', title: editingNote.value.title, content: editingNote.value.content, source_type: 'manual' })
    }
    editingNote.value = null
  } catch (e) { alert('保存失败: ' + e.message) }
}

async function handleDeleteNote(n) {
  if (!confirm('确定删除？')) return
  try { await deleteResource(n.id) } catch (e) { alert('删除失败: ' + e.message) }
}

onMounted(() => { fetchResources(); fetchCategories() })
</script>

<style scoped>
/* ====== Font Import ====== */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap');

.font-serif-sc {
  font-family: 'Noto Serif SC', serif;
}

.font-mono {
  font-family: 'SF Mono', 'Menlo', monospace;
}

/* ====== Layout ====== */
.my-resources {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-card, #ffffff);
}

.my-resources.review-active {
  background: var(--bg-card, #ffffff);
}

/* ====== Header ====== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px 16px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  margin: 0;
  font-family: 'Noto Serif SC', serif;
}

.resource-count {
  font-size: 12px;
  color: var(--text-muted, #999);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #e0e0e0);
  border-radius: 12px;
  width: 260px;
}

.search-icon {
  color: var(--text-muted, #999);
  flex-shrink: 0;
}

.search-input {
  border: none;
  background: none;
  outline: none;
  font-size: 13px;
  color: var(--text-primary, #121212);
  width: 100%;
  font-family: inherit;
}

/* ====== Tabs & Actions ====== */
.tabs-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  flex-shrink: 0;
}

.tabs-bar {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--bg-root, #fafafa);
  border: 1px solid var(--border-light, #edf0ed);
  border-radius: 12px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: none;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted, #999);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.tab-btn:hover {
  color: var(--text-primary, #121212);
}

.tab-btn.active {
  background: var(--bg-card, #fff);
  color: var(--text-primary, #121212);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.tab-icon {
  display: flex;
  color: var(--text-muted, #999);
}

.tab-btn.active .tab-icon {
  color: var(--text-primary, #121212);
}

.tab-count {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--border-light, #f0f0f0);
  border-radius: 6px;
  color: var(--text-muted, #666);
}

.tab-btn.active .tab-count {
  background: var(--text-primary, #121212);
  color: var(--bg-card, #fff);
}

.actions-bar {
  display: flex;
  gap: 8px;
}

/* ====== Buttons ====== */
.btn-dark {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--text-primary, #121212);
  color: var(--bg-card, #fff);
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-dark:hover {
  opacity: 0.9;
}

.btn-dark:disabled {
  background: var(--border-light, #ccc);
  cursor: not-allowed;
}

.btn-outline {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-card, #fff);
  color: var(--text-muted, #666);
  border: 1px solid var(--border-light, #e0e0e0);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-outline:hover {
  color: var(--text-primary, #121212);
  border-color: var(--text-muted, #ccc);
}

.btn-ai {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-card, #fff);
  color: var(--text-muted, #666);
  border: 1px solid var(--border-light, #e0e0e0);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-ai:hover {
  color: var(--text-primary, #121212);
  border-color: var(--text-muted, #ccc);
}

.btn-ghost {
  padding: 8px 16px;
  background: none;
  color: var(--text-muted, #666);
  border: none;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-ghost:hover {
  color: var(--text-primary, #121212);
  background: var(--bg-root, #f4f4f4);
}

.btn-ghost-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-card, #fff);
  color: var(--text-muted, #666);
  border: 1px solid var(--border-light, #e5e7eb);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-ghost-sm:hover {
  color: var(--text-primary, #121212);
  border-color: var(--text-muted, #d1d5db);
}

.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text-muted, #999);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: var(--bg-root, #f4f4f4);
  color: var(--text-primary, #121212);
}

.btn-icon.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.btn-icon-xs {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--text-muted, #999);
  cursor: pointer;
  font-size: 11px;
  transition: all 0.15s;
}

.btn-icon-xs:hover {
  background: var(--border-light, #e8e8e8);
  color: var(--text-primary, #121212);
}

.btn-icon-xs.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.btn-submit {
  align-self: flex-end;
  padding: 10px 20px;
  background: var(--text-primary, #121212);
  color: var(--bg-card, #fff);
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-submit:hover {
  opacity: 0.9;
}

.btn-dashed {
  display: inline-flex;
  padding: 6px 12px;
  background: none;
  border: 1px dashed var(--border-light, #ccc);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-muted, #666);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.btn-dashed:hover {
  border-color: var(--text-primary, #121212);
  color: var(--text-primary, #121212);
}

/* ====== Content Area ====== */
.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ====== Question Layout ====== */
.question-layout {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 0 28px 24px;
  overflow: hidden;
}

.category-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-root, #fafafa);
  border: 1px solid var(--border-light, #edf0ed);
  border-radius: 16px;
  padding: 16px;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.sidebar-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted, #999);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}

.category-item:hover {
  background: var(--border-light, #f0f0f0);
}

.category-item.active {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #edf0ed);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.category-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-muted, #666);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-item.active .category-name {
  font-weight: 600;
  color: var(--text-primary, #121212);
}

.category-count {
  font-size: 10px;
  color: var(--text-muted, #999);
}

.category-actions {
  display: none;
  gap: 2px;
  position: absolute;
  right: 4px;
}

.category-item:hover .category-actions {
  display: flex;
}

.category-divider {
  height: 1px;
  background: var(--border-light, #edf0ed);
  margin: 8px 0;
}

.question-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.filter-bar {
  margin-bottom: 16px;
}

.filter-select {
  padding: 8px 12px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #e0e0e0);
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  color: var(--text-muted, #666);
}

.question-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

/* ====== Question Card ====== */
.q-card {
  background: var(--bg-root, #f7f7f7);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.15s;
}

.q-card:hover {
  background: var(--border-light, #f0f0f0);
}

.q-card.editing {
  background: var(--bg-card, #fff);
  border: 1px solid var(--text-primary, #121212);
}

.q-card.preview {
  background: var(--bg-root, #f8f9f8);
}

.q-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.q-num {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary, #121212);
}

.q-type {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  background: var(--bg-card, #fff);
  color: var(--text-muted, #666);
  border: 1px solid var(--border-light, rgba(0,0,0,0.06));
  border-radius: 6px;
}

.q-pts {
  font-size: 10px;
  color: var(--text-muted, #999);
}

.q-category {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 8px;
  color: var(--text-muted, #666);
  background: var(--border-light, rgba(0,0,0,0.05));
  border-radius: 4px;
}

.q-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
  align-items: center;
  opacity: 0;
  transition: opacity 0.15s;
}

.q-card:hover .q-actions {
  opacity: 1;
}

.category-select {
  padding: 4px 8px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #e0e0e0);
  border-radius: 6px;
  font-size: 11px;
  font-family: inherit;
  outline: none;
  cursor: pointer;
  color: var(--text-muted, #666);
}

.q-content {
  font-size: 14px;
  color: var(--text-primary, #121212);
  line-height: 1.6;
  margin-bottom: 4px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
}

.q-options {
  margin-bottom: 10px;
}

.q-opt {
  font-size: 13px;
  color: var(--text-secondary, #333);
  padding: 3px 0;
}

.q-opt .opt-key {
  margin-right: 6px;
  font-weight: 600;
}

.q-opt .opt-key.correct {
  color: #388e3c;
}

.q-answer, .q-explain {
  font-size: 13px;
  color: var(--text-muted, #666);
  padding: 8px 12px;
  background: var(--bg-card, #fff);
  border-radius: 8px;
  margin-top: 8px;
}

.q-answer .label, .q-explain .label {
  font-weight: 600;
  color: var(--text-primary, #121212);
}

.q-expand-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted, #999);
  cursor: pointer;
  padding: 8px 0 0;
  transition: color 0.15s;
}

.q-expand-hint:hover {
  color: var(--text-primary, #121212);
}

.q-expand-hint svg {
  transition: transform 0.2s;
}

.edit-form {
  margin-bottom: 16px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light, #eaeaea);
}

.options-section {
  margin-top: 12px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.answer-row {
  margin-top: 12px;
}

.answer-row label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted, #666);
  margin-bottom: 6px;
}

/* ====== Form ====== */
.form-card {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 16px;
  margin-bottom: 20px;
  overflow: hidden;
}

.form-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-light, #eaeaea);
}

.form-card-header h4 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary, #121212);
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text-muted, #999);
  cursor: pointer;
  font-size: 18px;
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--bg-root, #f4f4f4);
  color: var(--text-primary, #121212);
}

.form-card-body {
  padding: 20px;
}

.form-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-light, #eaeaea);
}

.form-hint {
  font-size: 13px;
  color: var(--text-muted, #666);
  margin-bottom: 16px;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted, #666);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-root, #f4f4f4);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary, #121212);
  font-family: inherit;
  outline: none;
  transition: all 0.15s;
}

.form-input:focus {
  border-color: var(--text-primary, #121212);
  background: var(--bg-card, #fff);
}

.form-select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-root, #f4f4f4);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary, #121212);
  font-family: inherit;
  outline: none;
}

.form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-root, #f4f4f4);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary, #121212);
  font-family: inherit;
  outline: none;
  resize: vertical;
  min-height: 80px;
  transition: all 0.15s;
}

.form-textarea:focus {
  border-color: var(--text-primary, #121212);
  background: var(--bg-card, #fff);
}

.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.w-24 {
  width: 96px;
}

.import-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  padding: 4px;
  background: var(--bg-root, #f4f4f4);
  border-radius: 8px;
  width: fit-content;
}

.import-tab {
  padding: 6px 14px;
  background: none;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-muted, #666);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.import-tab:hover {
  background: var(--border-light, #e8e8e8);
}

.import-tab.active {
  background: var(--bg-card, #fff);
  color: var(--text-primary, #121212);
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.import-section {
  margin-top: 8px;
}

.file-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  border: 2px dashed var(--border-light, #eaeaea);
  border-radius: 12px;
  cursor: pointer;
  color: var(--text-muted, #999);
  transition: all 0.15s;
}

.file-drop:hover {
  border-color: var(--text-primary, #121212);
  color: var(--text-primary, #121212);
}

.file-drop p {
  margin: 12px 0 4px;
  font-size: 14px;
}

.file-drop span {
  font-size: 12px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-root, #f4f4f4);
  border-radius: 8px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary, #333);
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.color-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: var(--text-primary, #121212);
  box-shadow: 0 0 0 2px var(--bg-card, #fff), 0 0 0 4px var(--text-primary, #121212);
}

/* ====== Preview ====== */
.preview-card {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 16px;
  margin-bottom: 20px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-light, #eaeaea);
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #121212);
}

.preview-title svg {
  color: #667eea;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-hint {
  padding: 12px 20px;
  background: var(--bg-root, #f8f9fa);
  border-bottom: 1px solid var(--border-light, #eaeaea);
  font-size: 13px;
  color: var(--text-muted, #666);
}

.parsing-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: #667eea;
  color: #fff;
  border-radius: 10px;
  margin-left: 8px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.preview-list {
  padding: 16px;
}

/* ====== Toolbar ====== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 0 28px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-info {
  font-size: 13px;
  color: var(--text-muted, #999);
}

/* ====== Empty State ====== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  text-align: center;
}

.empty-icon {
  color: var(--border-light, #ccc);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 16px;
  color: var(--text-muted, #666);
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-muted, #999);
  margin: 0 0 20px;
}

.empty-actions {
  display: flex;
  gap: 12px;
}

/* ====== File Grid ====== */
.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 0 28px;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: var(--bg-root, #f7f7f7);
  border-radius: 12px;
  transition: all 0.15s;
}

.file-card:hover {
  background: var(--border-light, #f0f0f0);
}

.file-icon {
  color: var(--text-muted, #999);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #121212);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: var(--text-muted, #999);
  margin-top: 2px;
}

.file-actions {
  flex-shrink: 0;
}

/* ====== Note ====== */
.note-editor {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 16px;
  padding: 20px;
  margin: 0 28px 20px;
}

.note-title-input {
  width: 100%;
  border: none;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary, #121212);
  outline: none;
  margin-bottom: 16px;
  font-family: inherit;
  background: transparent;
}

.note-content-input {
  width: 100%;
  border: none;
  font-size: 14px;
  color: var(--text-secondary, #333);
  line-height: 1.8;
  outline: none;
  resize: vertical;
  font-family: inherit;
  background: transparent;
}

.note-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light, #eaeaea);
}

.note-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 0 28px;
}

.note-card {
  background: var(--bg-root, #f7f7f7);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.15s;
}

.note-card:hover {
  background: var(--border-light, #f0f0f0);
}

.note-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.note-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #121212);
}

.note-actions-inner {
  opacity: 0;
  transition: opacity 0.15s;
}

.note-card:hover .note-actions-inner {
  opacity: 1;
}

.note-preview {
  font-size: 13px;
  color: var(--text-muted, #666);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.note-date {
  font-size: 12px;
  color: var(--text-muted, #999);
  margin-top: 10px;
}

/* ====== Dialog ====== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.dialog-panel {
  background: var(--bg-card, #fff);
  border-radius: 20px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light, #eaeaea);
}

.dialog-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary, #121212);
}

.dialog-body {
  padding: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-light, #eaeaea);
}

/* ====== Review Mode ====== */
.review-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 32px 48px;
  overflow: hidden;
}

.review-config {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 16px;
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.config-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 20px;
  font-family: 'Noto Serif SC', serif;
  color: var(--text-primary, #121212);
}

.config-section {
  margin-bottom: 24px;
}

.config-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted, #666);
  margin: 0 0 12px;
}

.config-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-root, #f7f7f7);
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
  color: var(--text-secondary, #333);
}

.chip-option input {
  display: none;
}

.chip-option:hover {
  background: var(--border-light, #f0f0f0);
}

.chip-option.selected {
  background: var(--bg-card, #fff);
  border-color: var(--text-primary, #121212);
}

.chip-option .cat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.chip-option .chip-count {
  color: var(--text-muted, #999);
  font-size: 12px;
}

.chip-btn {
  padding: 6px 14px;
  background: var(--bg-root, #f7f7f7);
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  color: var(--text-secondary, #333);
}

.chip-btn:hover {
  background: var(--border-light, #f0f0f0);
}

.chip-btn.selected {
  background: var(--bg-card, #fff);
  border-color: var(--text-primary, #121212);
  font-weight: 600;
}

.config-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* Review Question */
.review-question {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
}

.review-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light, #f5f5f5);
  margin-bottom: 0;
  font-size: 12px;
  color: var(--text-muted, #999);
  flex-shrink: 0;
}

.breadcrumb-text {
  color: var(--text-muted, #999);
}

.breadcrumb-sep {
  font-family: monospace;
}

.breadcrumb-current {
  color: var(--text-primary, #121212);
  font-weight: 600;
}

.review-counter {
  margin-left: auto;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 10px;
  color: var(--text-muted, #9ca3af);
  letter-spacing: 0.05em;
}

.review-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 32px;
  overflow-y: auto;
  padding: 48px 0;
}

.review-question-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #121212);
  line-height: 1.8;
  font-family: 'Noto Serif SC', 'Georgia', serif;
  user-select: text;
}

.review-options-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-opt {
  padding: 20px 24px;
  background: var(--bg-root, #f7f7f7);
  border-radius: 16px;
  transition: all 0.2s;
  cursor: pointer;
}

.review-opt:hover:not(.answered) {
  background: var(--border-light, #f0f0f0);
}

.review-opt.answered {
  background: var(--bg-root, #fafafa);
  color: var(--text-muted, #999);
  border: 1px solid var(--border-light, #f0f0f0);
}

.review-opt.selected-wrong {
  border: 2px solid var(--text-primary, #121212);
  background: var(--bg-card, #fdfdfd);
  color: var(--text-primary, #121212);
}

.review-opt.correct {
  border: 1px solid #d1fae5;
  background: rgba(236, 253, 245, 0.1);
  color: #065f46;
}

.review-opt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  line-height: 1.6;
}

.opt-tag {
  font-size: 9px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.opt-tag.wrong {
  background: var(--border-light, #f3f4f6);
  color: var(--text-muted, #6b7280);
}

.opt-tag.correct {
  background: #d1fae5;
  color: #065f46;
}

.review-opt-feedback {
  margin-top: 16px;
  padding-left: 16px;
  border-left: 2px solid var(--border-light, #e5e7eb);
  font-size: 13px;
  line-height: 1.7;
  animation: fadeIn 0.3s ease;
}

.review-opt-feedback .feedback-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 700;
  margin-bottom: 8px;
  font-size: 12px;
}

.review-opt-feedback .feedback-status.correct {
  color: #059669;
}

.review-opt-feedback .feedback-status.wrong {
  color: var(--text-muted, #9ca3af);
}

.review-opt-feedback p {
  color: var(--text-secondary, #4b5563);
  font-family: 'Noto Serif SC', serif;
}

.review-opt.correct .review-opt-feedback {
  border-left-color: #059669;
}

/* Text Input */
.review-text-input {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-text-input textarea {
  width: 100%;
  padding: 20px;
  background: var(--bg-root, #f7f7f7);
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-family: 'Noto Serif SC', serif;
  resize: vertical;
  min-height: 140px;
  outline: none;
  transition: all 0.2s;
  line-height: 1.6;
  color: var(--text-primary, #121212);
}

.review-text-input textarea:focus {
  background: var(--border-light, #f0f0f0);
}

.review-text-input textarea:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Bottom Bar */
.review-bottom-bar {
  border-top: 1px solid var(--border-light, #f5f5f5);
  padding-top: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.review-bottom-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Review Result */
.review-result {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #eaeaea);
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  max-width: 500px;
  margin: auto;
  width: 100%;
}

.result-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 24px;
  font-family: 'Noto Serif SC', serif;
  color: var(--text-primary, #121212);
}

.result-score {
  margin-bottom: 24px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.score-circle.excellent {
  background: linear-gradient(135deg, #059669, #10b981);
}

.score-circle.good {
  background: linear-gradient(135deg, #d97706, #f59e0b);
}

.score-circle.bad {
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

.score-number {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.score-label {
  font-size: 12px;
  color: rgba(255,255,255,0.8);
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
}

.stat-value.correct {
  color: #059669;
}

.stat-value.wrong {
  color: #dc2626;
}

.stat-value.points {
  color: var(--text-primary, #121212);
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted, #999);
}

/* ====== Animations ====== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ====== Scrollbar ====== */
.question-list::-webkit-scrollbar,
.category-sidebar::-webkit-scrollbar,
.review-main::-webkit-scrollbar {
  width: 4px;
}

.question-list::-webkit-scrollbar-track,
.category-sidebar::-webkit-scrollbar-track,
.review-main::-webkit-scrollbar-track {
  background: transparent;
}

.question-list::-webkit-scrollbar-thumb,
.category-sidebar::-webkit-scrollbar-thumb,
.review-main::-webkit-scrollbar-thumb {
  background: var(--border-light, #e0e0e0);
  border-radius: 4px;
}

.question-list::-webkit-scrollbar-thumb:hover,
.category-sidebar::-webkit-scrollbar-thumb:hover,
.review-main::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted, #ccc);
}

/* ====== Responsive ====== */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
    padding: 16px 20px;
  }

  .search-box {
    width: 100%;
  }

  .tabs-section {
    flex-direction: column;
    gap: 12px;
    padding: 12px 20px;
  }

  .actions-bar {
    width: 100%;
    justify-content: flex-start;
  }

  .question-layout {
    flex-direction: column;
    padding: 0 20px 20px;
  }

  .category-sidebar {
    width: 100%;
  }

  .ai-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .file-grid, .note-grid {
    grid-template-columns: 1fr;
    padding: 0 20px;
  }

  .review-session {
    padding: 20px;
  }
}
</style>
