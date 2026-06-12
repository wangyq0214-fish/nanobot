<template>
<div class="app-shell">
<StudentNav active-tab="learning-path" />

        <div class="main-split">
            <div class="col-half">
                <div class="panel left-main-panel">
                    <div class="panel-strip top"></div>
                    <div class="panel-strip right"></div>
                    <div class="panel-strip bottom"></div>
                    <div class="panel-strip left"></div>
                    <div class="panel-hd"><i></i><span class="panel-title">学生掌握水平</span></div>
                    <div class="panel-body">
                        <div class="inner-section">
                            <div class="student-card">
                                <div class="avatar">张</div>
                                <div class="student-info-text">
                                    <div class="student-name">张禾丰</div>
                                    <div class="student-meta">园艺技术 · 大三 · 综合81.5</div>
                                </div>
                                <div class="score-badge">
                                    <div class="big">81.5</div>
                                    <div class="small">土壤学</div>
                                </div>
                            </div>
                            <div class="pref-tags">
                                <span class="pref-tag"><span class="pref-dot visual"></span>田间实践 65%</span>
                                <span class="pref-tag"><span class="pref-dot reading"></span>图谱阅读 55%</span>
                                <span class="pref-tag"><span class="pref-dot practice"></span>实验操作 48%</span>
                            </div>
                        </div>
                        <div class="section-divider"></div>

                        <div class="inner-section radar-container">
                            <div class="inner-section-title">技能维度雷达</div>
                            <div id="chartRadar" style="flex:1; width:100%;"></div>
                        </div>
                        <div class="section-divider"></div>

                        <div class="inner-section">
                            <div class="inner-section-title">章节进度 · 批注</div>
                            <div class="progress-list">
                                <div class="progress-row">
                                    <span class="progress-label">植物生理</span>
                                    <div class="progress-bar-wrap"><div class="progress-bar-fill low" style="width:42%;"></div></div>
                                    <span class="progress-pct">42%</span>
                                    <div class="annotation-dot">!
                                        <div class="annotation-bubble">📌 光合作用光反应与暗反应衔接薄弱，建议结合田间观测理解。</div>
                                    </div>
                                </div>
                                <div class="progress-row">
                                    <span class="progress-label">土壤肥料</span>
                                    <div class="progress-bar-wrap"><div class="progress-bar-fill mid" style="width:58%;"></div></div>
                                    <span class="progress-pct">58%</span>
                                    <div class="annotation-dot">!
                                        <div class="annotation-bubble">📌 氮磷钾配比计算需强化，推荐实地测土配方练习。</div>
                                    </div>
                                </div>
                                <div class="progress-row">
                                    <span class="progress-label">病虫害防治</span>
                                    <div class="progress-bar-wrap"><div class="progress-bar-fill high" style="width:78%;"></div></div>
                                    <span class="progress-pct">78%</span>
                                    <div class="annotation-dot">!
                                        <div class="annotation-bubble">📌 掌握良好，可挑战综合防治方案设计提升上限。</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="section-divider"></div>

                        <div class="inner-section" style="overflow-y:auto; flex-shrink:1; min-height:0;">
                            <div class="inner-section-title">薄弱知识点</div>
                            <table class="weak-table">
                                <thead><tr><th>知识点</th><th>掌握</th></tr></thead>
                                <tbody>
                                    <tr><td>光合作用光反应</td><td><span class="weak-badge danger">35%</span></td></tr>
                                    <tr><td>土壤阳离子交换</td><td><span class="weak-badge danger">40%</span></td></tr>
                                    <tr><td>果树修剪技术</td><td><span class="weak-badge warning">52%</span></td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-half">
                <div class="panel right-path">
                    <div class="panel-strip top"></div>
                    <div class="panel-strip right"></div>
                    <div class="panel-strip bottom"></div>
                    <div class="panel-strip left"></div>
                    <div class="panel-hd" style="border-bottom:none;">
                        <i></i><span class="panel-title">个性化学习路径 · 阶段递进</span>
                    </div>
                    <div class="panel-body scrollable" style="padding-top:0;">
                        <div class="path-container">
                            <div class="path-node done">
                                <div class="path-node-dot done"></div>
                                <div class="path-node-card">
                                    <div class="path-node-name">1. 土壤基础</div>
                                    <div class="path-node-desc">土壤质地、团粒结构、有机质</div>
                                    <div class="path-node-status" style="color:var(--green);">✅ 已完成 · 90%</div>
                                </div>
                                <div class="path-annotation">📌 基础扎实，可进入养分管理</div>
                            </div>
                            <div class="path-node current">
                                <div class="path-node-dot current"></div>
                                <div class="path-node-card">
                                    <div class="path-node-name">2. 养分与施肥 🔄</div>
                                    <div class="path-node-desc">氮磷钾吸收机理、测土配方</div>
                                    <div class="path-node-status" style="color:var(--accent);">🟣 当前学习 · 58%</div>
                                </div>
                                <div class="path-annotation">⚡ 瓶颈：配方计算，建议田间实训</div>
                            </div>
                            <div class="path-node future" style="opacity:0.85;">
                                <div class="path-node-dot future"></div>
                                <div class="path-node-card">
                                    <div class="path-node-name">3. 病虫害防治 → 推荐</div>
                                    <div class="path-node-desc">常见病害识别、综合防治方案</div>
                                    <div class="path-node-status" style="color:var(--text-muted);">⏳ 待开启</div>
                                </div>
                                <div class="path-annotation">🗺️ 掌握养分后，病害防治更系统</div>
                            </div>
                            <div class="path-node future" style="opacity:0.7;">
                                <div class="path-node-dot future"></div>
                                <div class="path-node-card">
                                    <div class="path-node-name">4. 园艺作物栽培</div>
                                    <div class="path-node-desc">果树修剪、蔬菜茬口安排</div>
                                    <div class="path-node-status" style="color:var(--text-muted);">⏳ 待开启</div>
                                </div>
                                <div class="path-annotation">🎯 目标：独立完成果园管理方案</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel right-res">
                    <div class="panel-strip top"></div>
                    <div class="panel-strip right"></div>
                    <div class="panel-strip bottom"></div>
                    <div class="panel-strip left"></div>
                    <div class="panel-hd"><i></i><span class="panel-title">智能资源推荐 · 基于弱项</span></div>
                    <div class="panel-body scrollable">
                        <div class="resource-list">
                            <div class="resource-card">
                                <div class="resource-card-header">
                                    <span class="resource-card-title">光合作用动态模拟 · 光反应详解</span>
                                    <span class="resource-type video">🎬 视频</span>
                                </div>
                                <div class="resource-meta">⏱ 22分钟 · 难度★★★ · 匹配度92%</div>
                                <div class="resource-note">💡 针对<b>「光合作用光反应」</b>薄弱，3D动画演示类囊体膜电子传递。</div>
                            </div>
                            <div class="resource-card">
                                <div class="resource-card-header">
                                    <span class="resource-card-title">测土配方施肥 · 田间实操手册</span>
                                    <span class="resource-type exercise">📝 实训</span>
                                </div>
                                <div class="resource-meta">⏱ 约40分钟 · 难度★★★☆ · 匹配度88%</div>
                                <div class="resource-note">💡 针对<b>「土壤阳离子交换量」</b>弱项，包含采样与计算步骤。</div>
                            </div>
                            <div class="resource-card">
                                <div class="resource-card-header">
                                    <span class="resource-card-title">果树修剪图谱 · 常见树形图解</span>
                                    <span class="resource-type doc">📄 图谱</span>
                                </div>
                                <div class="resource-meta">⏱ 阅读20分钟 · 难度★★ · 匹配度85%</div>
                                <div class="resource-note">💡 针对<b>「果树修剪技术」</b>，高清示意图与修剪对比。</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import echarts from '../../utils/echarts.js'
import { useAuth } from '../../composables/useAuth.js'
import StudentNav from '../../components/StudentNav.vue'

const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}

const isDark = ref(false)

function toggleTheme() {
    isDark.value = !isDark.value
    document.body.classList.toggle('dark', isDark.value)
    renderRadar()
}

function getColors() {
    const s = getComputedStyle(document.body)
    return {
        accent: s.getPropertyValue('--accent').trim(),
        accentSoft: s.getPropertyValue('--accent-soft').trim(),
        textSub: s.getPropertyValue('--text-muted').trim(),
    }
}

let radarChart = null

function renderRadar() {
    const el = document.getElementById('chartRadar')
    if (!el) return
    if (!radarChart) {
        radarChart = echarts.init(el)
    }
    const c = getColors()
    radarChart.setOption({
        radar: {
            indicator: [
                { name: '植物生理', max: 100 },
                { name: '土壤肥料', max: 100 },
                { name: '病虫害', max: 100 },
                { name: '田间操作', max: 100 },
                { name: '数据分析', max: 100 },
                { name: '综合规划', max: 100 }
            ],
            center: ['50%', '50%'],
            radius: '55%',
            axisName: { color: c.textSub, fontSize: 9, fontWeight: 600 },
            splitArea: { areaStyle: { color: ['rgba(128,128,128,0.02)', 'rgba(128,128,128,0.05)'] } },
            axisLine: { lineStyle: { color: 'rgba(128,128,128,0.28)' } },
            splitLine: { lineStyle: { color: 'rgba(128,128,128,0.26)' } }
        },
        series: [{
            type: 'radar',
            data: [{
                value: [42, 58, 78, 65, 40, 52],
                name: '张禾丰',
                areaStyle: { color: c.accentSoft },
                lineStyle: { color: c.accent, width: 2 },
                itemStyle: { color: c.accent, borderWidth: 2, borderColor: '#fff' },
                symbol: 'circle',
                symbolSize: 5
            }]
        }]
    }, true)
}

function handleResize() {
    if (radarChart) radarChart.resize()
}

onMounted(() => {
    renderRadar()
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (radarChart) {
        radarChart.dispose()
        radarChart = null
    }
})
</script>


<style>
:root {
  --bg-root: #f8f6f1;
  --bg-card: #ffffff;
  --bg-nav: #ffffff;
  --accent: #5b8def;
  --accent-2: #7B5CFF;
  --accent-light: rgba(91,141,239,0.3);
  --accent-soft: #eef4ff;
  --accent-glow: rgba(91,141,239,0.15);
  --accent-deep: #4a7de0;
  --border-light: #e8e4db;
  --border-medium: #e0dcd5;
  --border-active: #5b8def;
  --text-primary: #2c2c2c;
  --text-secondary: #666666;
  --text-muted: #999999;
  --divider: #e8e4db;
  --panel-radius: 16px;
  --green: #16a34a;
  --red: #e74c3c;
  --orange: #f59e0b;
  --annotation-bg: #fff9f0;
  --annotation-border: #f0d9a8;
  --annotation-text: #6b4e31;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --trans: 0.25s ease;
  --scrollbar-thumb: rgba(91,141,239,0.25);
  --scrollbar-track: transparent;
}
body.dark {
  --bg-root: #12121a;
  --bg-card: #1e1e2e;
  --bg-nav: #1e1e2e;
  --accent: #5b8def;
  --accent-light: rgba(91,141,239,0.3);
  --accent-soft: rgba(91,141,239,0.1);
  --accent-glow: rgba(91,141,239,0.2);
  --accent-deep: #4a7de0;
  --border-light: #333333;
  --border-medium: #444444;
  --border-active: #5b8def;
  --text-primary: #e0e0e0;
  --text-secondary: #aaaaaa;
  --text-muted: #777777;
  --divider: #333333;
  --annotation-bg: #2a2530;
  --annotation-border: #5e4a3a;
  --annotation-text: #d4ba8c;
  --scrollbar-thumb: rgba(91,141,239,0.35);
  --scrollbar-track: rgba(255,255,255,0.03);
}

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        html {
            font-size: 15px;
        }

        body {
            font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
            color: var(--text-primary);
            background: var(--bg-root);
            background-image: radial-gradient(circle at 20% 30%, rgba(108, 92, 231, 0.04) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(108, 92, 231, 0.03) 0%, transparent 50%);
            height: 100vh;
            overflow: hidden;
            transition: background 0.4s, color 0.4s;
        }

        ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
        }
        ::-webkit-scrollbar-track {
            background: var(--scrollbar-track);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb {
            background: var(--scrollbar-thumb);
            border-radius: 3px;
            transition: background 0.3s;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-light);
        }
    </style>
    <style scoped>
        .app-shell {
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            max-width: 1600px;
            margin: 0 auto;
            padding: 8px 10px;
            gap: 8px;
        }

        .top-nav {
            flex-shrink: 0;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-nav);
            border: 1px solid var(--border-light);
            border-radius: 24px;
            padding: 0 24px;
            box-shadow: 0 0 0 2px var(--accent-soft), 0 0 18px var(--accent-glow);
            position: relative;
        }
        .nav-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .nav-logo {
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .nav-logo .dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent);
        }
        .nav-center {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .nav-tab {
            padding: 6px 14px;
            border-radius: 14px;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
            border: 1.5px solid transparent;
        }
        .nav-tab:hover {
            color: var(--text-primary);
            background: var(--accent-soft);
        }
        .nav-tab.active {
            color: var(--accent);
            background: var(--accent-soft);
            border-color: var(--accent);
            box-shadow: 0 0 12px var(--accent-glow);
        }
        .nav-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .nav-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1.5px solid var(--border-medium);
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            transition: all 0.2s;
        }
        .nav-icon svg {
            width: 14px;
            height: 14px;
            stroke: currentColor;
            fill: none;
            stroke-width: 1.8;
        }
        .nav-icon:hover {
            color: var(--accent);
            border-color: var(--accent);
            box-shadow: 0 0 12px var(--accent-glow);
        }
        .nav-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7B5CFF, #A78BFA);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 600;
            font-size: 0.75rem;
            cursor: pointer;
            border: 2px solid transparent;
            box-shadow: 0 0 14px var(--accent-glow);
        }

        .main-split {
            flex: 1;
            min-height: 0;
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 10px;
        }
        .col-half {
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 0;
        }

        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--panel-radius);
            box-shadow: 0 0 14px var(--accent-soft), var(--shadow-sm);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            transition: all var(--trans);
        }
        .panel:hover {
            border-color: var(--border-active);
            box-shadow: 0 0 24px var(--accent-glow), var(--shadow-md);
        }

        .panel::before,
        .panel::after {
            content: '';
            position: absolute;
            z-index: 3;
            pointer-events: none;
            width: 20px;
            height: 20px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .panel::before {
            top: 5px;
            left: 5px;
            border-top: 2.5px solid var(--accent);
            border-left: 2.5px solid var(--accent);
            border-radius: 4px 0 0 0;
        }
        .panel::after {
            bottom: 5px;
            right: 5px;
            border-bottom: 2.5px solid var(--accent);
            border-right: 2.5px solid var(--accent);
            border-radius: 0 0 4px 0;
        }
        .panel:hover::before,
        .panel:hover::after {
            opacity: 1;
        }

        .panel-strip {
            display: none;
        }

        .panel-hd {
            padding: 11px 16px 9px;
            display: flex;
            align-items: center;
            gap: 9px;
            border-bottom: 1px solid var(--divider);
            flex-shrink: 0;
            position: relative;
            z-index: 2;
        }
        .panel-hd i {
            width: 4.5px;
            height: 15px;
            background: linear-gradient(180deg, var(--accent), var(--accent-deep));
            border-radius: 2.5px;
            box-shadow: 0 0 7px var(--accent-glow);
            flex-shrink: 0;
        }
        .panel-title {
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.4px;
        }
        .panel-body {
            flex: 1;
            min-height: 0;
            padding: 6px 10px 10px;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 2;
            overflow: hidden;
        }
        .panel-body.scrollable {
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 6px;
        }

        .left-main-panel {
            flex: 1;
        }
        .left-main-panel .panel-body {
            gap: 10px;
        }

        .inner-section {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .inner-section-title {
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .inner-section-title::before {
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background: var(--accent);
            border-radius: 50%;
            box-shadow: 0 0 6px var(--accent-glow);
        }
        .section-divider {
            height: 1px;
            background: var(--divider);
            margin: 4px 0;
        }

        /* 学生卡片 — 成绩在右上角 */
        .student-card {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            position: relative;
        }
        .student-info-text {
            flex: 1;
            min-width: 0;
        }
        .avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6C5CE7, #A78BFA);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 0 16px var(--accent-glow);
            border: 2px solid var(--accent-light);
            flex-shrink: 0;
        }
        .student-name {
            font-size: 0.9rem;
            font-weight: 700;
        }
        .student-meta {
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 2px;
        }
        .score-badge {
            background: var(--accent-soft);
            border-radius: 16px;
            padding: 4px 10px;
            text-align: center;
            margin-left: auto;
            align-self: flex-start;
            flex-shrink: 0;
            border: 1.5px solid var(--accent-light);
            box-shadow: 0 2px 8px var(--accent-glow);
        }
        .score-badge .big {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent);
        }
        .score-badge .small {
            font-size: 0.55rem;
            color: var(--text-muted);
        }
        .pref-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 6px;
        }
        .pref-tag {
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 0.62rem;
            border: 1px solid var(--accent-light);
            background: var(--accent-soft);
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: normal;
            word-break: keep-all;
            line-height: 1.3;
        }
        .pref-dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .pref-dot.visual {
            background: #6366f1;
        }
        .pref-dot.practice {
            background: #e17055;
        }
        .pref-dot.reading {
            background: #00b894;
        }

        .radar-container {
            flex: 1;
            min-height: 0;
        }

        .progress-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .progress-row {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .progress-label {
            width: 70px;
            font-size: 0.68rem;
            font-weight: 600;
            white-space: nowrap;
        }
        .progress-bar-wrap {
            flex: 1;
            height: 7px;
            background: var(--accent-soft);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            border-radius: 4px;
        }
        .progress-bar-fill.low {
            background: linear-gradient(90deg, #e17055, #f08a5d);
        }
        .progress-bar-fill.mid {
            background: linear-gradient(90deg, #fdcb6e, #f9ca24);
        }
        .progress-bar-fill.high {
            background: linear-gradient(90deg, #00b894, #55efc4);
        }
        .progress-pct {
            width: 34px;
            font-size: 0.68rem;
            font-weight: 700;
            text-align: right;
        }
        .annotation-dot {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--annotation-bg);
            border: 1.5px dashed var(--annotation-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.55rem;
            color: var(--annotation-text);
            cursor: pointer;
            position: relative;
            flex-shrink: 0;
        }
        .annotation-bubble {
            position: absolute;
            bottom: 130%;
            right: -8px;
            width: 180px;
            background: var(--annotation-bg);
            border: 1.5px dashed var(--annotation-border);
            border-radius: 8px;
            padding: 6px 8px;
            font-size: 0.58rem;
            color: var(--annotation-text);
            line-height: 1.5;
            display: none;
            z-index: 50;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            pointer-events: none;
        }
        .annotation-dot:hover .annotation-bubble {
            display: block;
        }

        .weak-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.68rem;
        }
        .weak-table th {
            text-align: left;
            padding: 5px 6px;
            color: var(--text-muted);
            font-size: 0.6rem;
            border-bottom: 1px solid var(--divider);
        }
        .weak-table td {
            padding: 6px;
            border-bottom: 1px solid var(--divider);
            color: var(--text-secondary);
        }
        .weak-badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 7px;
            font-size: 0.58rem;
            font-weight: 600;
        }
        .weak-badge.danger {
            color: #d63031;
            background: rgba(214, 48, 49, 0.08);
            border: 1px solid rgba(214, 48, 49, 0.2);
        }
        .weak-badge.warning {
            color: #b7791f;
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .right-path {
            flex: 2.05;
        }
        .right-res {
            flex: 1.65;
        }

        .path-container {
            display: flex;
            flex-direction: column;
            gap: 4px;
            position: relative;
            padding-left: 28px;
            margin-top: 2px;
            padding-bottom: 4px;
        }
        .path-container::before {
            content: '';
            position: absolute;
            left: 18px;
            top: 10px;
            bottom: 10px;
            width: 2px;
            background: linear-gradient(180deg, var(--green) 0%, var(--accent) 45%, #ccc 100%);
            border-radius: 2px;
            opacity: 0.6;
            z-index: 1;
        }
        .path-node {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 5px 0;
            position: relative;
            z-index: 2;
        }
        .path-node-dot {
            position: absolute;
            left: -13px;
            top: 10px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            z-index: 3;
            flex-shrink: 0;
        }
        .path-node-dot.done {
            background: var(--green);
            box-shadow: 0 0 8px rgba(0, 184, 148, 0.5);
            border: 2px solid white;
        }
        .path-node-dot.current {
            background: var(--accent);
            box-shadow: 0 0 14px var(--accent-glow);
            border: 2px solid white;
        }
        .path-node-dot.future {
            background: #dcdde1;
            border: 2px dashed var(--border-medium);
        }
        .path-node-card {
            flex: 1;
            background: var(--accent-soft);
            border: 1px solid var(--border-light);
            border-radius: 10px;
            padding: 8px 12px;
            transition: 0.2s;
            min-width: 0;
        }
        .path-node.current .path-node-card {
            border-color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
        }
        .path-node-name {
            font-weight: 700;
            font-size: 0.74rem;
        }
        .path-node-desc {
            font-size: 0.62rem;
            color: var(--text-muted);
            margin-top: 1px;
        }
        .path-node-status {
            font-size: 0.58rem;
            font-weight: 600;
            margin-top: 2px;
        }
        .path-annotation {
            flex-shrink: 0;
            width: 115px;
            background: var(--annotation-bg);
            border: 1.4px dashed var(--annotation-border);
            border-radius: 6px;
            padding: 5px 6px;
            font-size: 0.56rem;
            color: var(--annotation-text);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
            transform: rotate(0.2deg);
            align-self: center;
            line-height: 1.4;
        }

        .resource-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .resource-card {
            background: var(--accent-soft);
            border: 1px solid var(--accent-light);
            border-radius: 12px;
            padding: 10px 12px;
            cursor: pointer;
            transition: 0.2s;
            flex-shrink: 0;
        }
        .resource-card:hover {
            border-color: var(--accent);
            box-shadow: 0 0 12px var(--accent-glow);
        }
        .resource-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
            gap: 8px;
        }
        .resource-card-title {
            font-weight: 700;
            font-size: 0.74rem;
            flex: 1;
            min-width: 0;
        }
        .resource-type {
            font-size: 0.58rem;
            padding: 2px 8px;
            border-radius: 10px;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .resource-type.video {
            background: rgba(99, 102, 241, 0.1);
            color: #6366f1;
        }
        .resource-type.exercise {
            background: rgba(245, 158, 11, 0.1);
            color: #b7791f;
        }
        .resource-type.doc {
            background: rgba(0, 184, 148, 0.1);
            color: #00b894;
        }
        .resource-meta {
            font-size: 0.6rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }
        .resource-note {
            background: var(--annotation-bg);
            border: 1px dashed var(--annotation-border);
            border-radius: 5px;
            padding: 4px 6px;
            font-size: 0.56rem;
            color: var(--annotation-text);
            line-height: 1.5;
        }
</style>
