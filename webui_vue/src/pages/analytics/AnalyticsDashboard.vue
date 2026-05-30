<template>
<div v-if="!user" class="login-screen">
  <div class="login-card">
    <div class="login-header">
      <div class="login-logo"><span class="dot"></span>Nanobot</div>
      <p class="login-subtitle">学情数据分析</p>
    </div>
    <input class="login-input" v-model="loginUserId" placeholder="输入用户名" @keydown.enter="handleLogin" autofocus />
    <p v-if="loginError" class="login-error">{{ loginError }}</p>
    <button class="login-submit" @click="handleLogin" :disabled="!loginUserId.trim()">进入</button>
  </div>
</div>

<div v-else class="app-shell">
  <nav class="top-nav">
    <div class="nav-left"><span class="nav-logo"><span class="dot"></span>Nanobot</span></div>
    <div class="nav-center">
      <span class="nav-tab" @click="goToLessonPlan">教案与活动</span>
      <span class="nav-tab" @click="goToHomework">作业批改</span>
      <span class="nav-tab active">学情分析</span>
    </div>
    <div class="nav-right">
      <button class="nav-icon" @click="toggleTheme" title="切换主题">
        <svg v-if="!isDark" viewBox="0 0 20 20"><circle cx="10" cy="10" r="4"/><path d="M10 2v2m0 12v2M2 10h2m12 0h2M4.5 4.5l1.5 1.5m8 8l1.5 1.5M4.5 15.5l1.5-1.5m8-8l1.5-1.5"/></svg>
        <svg v-else viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16 7 7 0 0 1 0-14"/></svg>
      </button>
      <div class="nav-avatar">{{ user?.userId?.[0] || '?' }}</div>
    </div>
  </nav>

  <div class="content">
    <div class="kpi-row">
      <div class="kpi-item"><div class="kpi-num">77.9</div><div class="kpi-label">年级平均分</div></div>
      <div class="kpi-item"><div class="kpi-num">68.5<small>%</small></div><div class="kpi-label">及格率</div></div>
      <div class="kpi-item"><div class="kpi-num">25.0<small>%</small></div><div class="kpi-label">优秀率 (≥90)</div></div>
      <div class="kpi-item"><div class="kpi-num">187</div><div class="kpi-label">薄弱知识点总数</div></div>
      <div class="kpi-item"><div class="kpi-num">62</div><div class="kpi-label">学困生人数</div></div>
      <div class="kpi-item"><div class="kpi-num">14</div><div class="kpi-label">待优化教学班</div></div>
    </div>

    <div class="grid-main">
      <!-- LEFT -->
      <div class="col">
        <div class="panel f1">
          <div class="panel-hd"><i></i><span class="panel-title">学生综合能力雷达</span></div>
          <div class="panel-body"><div id="chartRadar" class="chart-wrap"></div></div>
        </div>
        <div class="panel f1">
          <div class="panel-hd"><i></i><span class="panel-title">高频薄弱知识点频次</span></div>
          <div class="panel-body"><div id="chartBar" class="chart-wrap"></div></div>
        </div>
        <div class="panel f09">
          <div class="panel-hd"><i></i><span class="panel-title">班级学情动态与预警</span></div>
          <div class="panel-body" style="padding:2px 4px; overflow-y:auto;">
            <div v-for="r in warnList" :key="r.cls" class="table-row">
              <span>{{ r.cls }}</span><span>{{ r.desc }}</span><span class="s-tag" :class="r.tagClass">{{ r.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- CENTER -->
      <div class="col">
        <div class="panel panel-focal f22">
          <div class="panel-strip top"></div><div class="panel-strip right"></div><div class="panel-strip bottom"></div><div class="panel-strip left"></div>
          <div class="panel-hd" style="border-bottom:none;padding-bottom:2px;">
            <i></i><span class="panel-title">班级学情态势 & 薄弱干预点</span>
            <div class="leg" style="margin-left:auto;">
              <span><i style="background:var(--green);"></i>正常</span>
              <span><i style="background:var(--accent);"></i>运行中</span>
              <span><i style="background:var(--orange);"></i>关注</span>
              <span><i style="background:var(--red);"></i>预警</span>
              <span><i style="background:var(--accent-deep);"></i>科研</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="gh-grid">
              <div v-for="g in greenhouse" :key="g.id" class="gh-card" :class="g.level" :ref="el => { if (g.tip) ghTipRefs[g.id] = el }">
                <div class="gh-head"><span class="gh-name">{{ g.name }}</span><span class="gh-score">{{ g.score }}</span></div>
                <div class="gh-tags"><span v-for="t in g.tags" :key="t" class="gh-tag">{{ t }}</span></div>
                <div class="gh-foot"><span class="gh-weak">{{ g.weakness }}</span><span class="gh-act">{{ g.action }}</span></div>
                <div v-if="g.tip" class="tip-box"><div class="tt">{{ g.tipTitle }}</div><div v-for="tr in g.tipRows" :key="tr.k" class="tr"><span>{{ tr.k }}</span><span :style="tr.style">{{ tr.v }}</span></div></div>
              </div>
            </div>
          </div>
        </div>
        <div class="panel f125">
          <div class="panel-hd" style="justify-content:center;"><i></i><span class="panel-title">历次考试学业趋势</span></div>
          <div class="panel-body"><div id="chartMix" class="chart-wrap"></div></div>
        </div>
      </div>

      <!-- RIGHT -->
      <div class="col">
        <div class="panel f13">
          <div class="panel-hd"><i></i><span class="panel-title">学科成绩变化曲线</span></div>
          <div class="panel-body"><div id="chartLine" class="chart-wrap"></div></div>
        </div>
        <div class="panel f15">
          <div class="panel-hd"><i></i><span class="panel-title">班级平均分 / 及格率对比</span></div>
          <div class="panel-body"><div id="chartBlBar" class="chart-wrap"></div></div>
        </div>
        <div class="panel f12">
          <div class="panel-hd" style="border-bottom:none;padding-bottom:2px;">
            <span style="flex:1.15;display:flex;align-items:center;justify-content:flex-start;gap:6px;"><i></i><span class="panel-title">跨班级学情对比</span></span>
            <span style="flex:1;display:flex;align-items:center;justify-content:flex-start;gap:6px;"><i></i><span class="panel-title">差异化教学优化策略</span></span>
          </div>
          <div class="panel-body" style="padding-top:0;">
            <div style="display:flex;gap:8px;flex:1;min-height:0;">
              <div style="flex:1.15;" id="chartMap" class="chart-wrap"></div>
              <div style="flex:1;" class="strat-list">
                <div v-for="s in strategyList" :key="s.id" class="strat-card">
                  <span class="strat-num">{{ s.id }}</span>
                  <div class="strat-info"><div class="strat-subj">{{ s.cls }}</div><div class="strat-desc">{{ s.text }}</div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

const user = ref(null)
const loginUserId = ref('')
const loginError = ref('')
const isDark = ref(false)
const ghTipRefs = ref({})

onMounted(() => {
  user.value = { userId: '王老师', role: 'teacher' }
  document.body.classList.toggle('dark', isDark.value)
  nextTick(() => { renderAllCharts() })
})

function handleLogin() {
  if (!loginUserId.value.trim()) return
  user.value = { userId: loginUserId.value.trim(), role: 'teacher' }
  nextTick(() => { renderAllCharts() })
}
function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
  nextTick(() => { renderAllCharts() })
}
function goToLessonPlan() { window.location.href = '/' }
function goToHomework() { window.location.href = '/homework.html' }

// ==================== DATA ====================
const warnList = [
  { cls:'三(1)班 数学', desc:'均分86 / 弱项:分数应用题', tagClass:'s-on', label:'待提升' },
  { cls:'三(2)班 英语', desc:'均分91 / 语法薄弱', tagClass:'s-on', label:'临界关注' },
  { cls:'三(3)班 物理', desc:'均分52 / 力学概念混乱', tagClass:'s-off', label:'预警' },
  { cls:'三(4)班 语文', desc:'均分74 / 阅读理解薄弱', tagClass:'s-warn', label:'待推进' },
  { cls:'三(5)班 数学', desc:'均分49 / 函数大面积失分', tagClass:'s-off', label:'严重预警' },
]

const greenhouse = [
  { id:1, name:'1班·数学', score:'86.2', tags:['几何弱','运算稳定'], weakness:'● 辅助线', action:'专题突破', level:'normal' },
  { id:2, name:'2班·英语', score:'84.5', tags:['完形弱','阅读稳'], weakness:'● 完形失分', action:'听读强化', level:'running' },
  { id:3, name:'3班·物理', score:'58.3', tags:['力学薄弱','实验脱节'], weakness:'● 浮力压强31%', action:'紧急干预', level:'alert' },
  { id:4, name:'4班·语文', score:'79.4', tags:['文言文弱','作文偏题'], weakness:'● 文言失分', action:'专项训练', level:'running' },
  { id:5, name:'5班·数学', score:'54.7', tags:['函数薄弱','运算失误高'], weakness:'● 二次函数38%', action:'限时训练', level:'warning', tip:true, tipTitle:'5班数学 · 诊断', tipRows:[{k:'薄弱题型',v:'二次函数综合',style:''},{k:'得分率',v:'38%',style:'color:var(--red)'},{k:'当前均分',v:'54.7',style:''},{k:'目标均分',v:'68.0',style:''}] },
  { id:6, name:'6班·英语', score:'95.1', tags:['推理强','基础扎实'], weakness:'● 主旨大意', action:'稳中求进', level:'normal' },
  { id:7, name:'7班·化学', score:'81.5', tags:['方程式弱','实验待巩固'], weakness:'● 推断题52%', action:'专题复习', level:'running' },
  { id:8, name:'8班·语文', score:'84.9', tags:['古诗弱','名著一般'], weakness:'● 手法分析', action:'每日积累', level:'running' },
  { id:9, name:'9班·物理', score:'76.8', tags:['电学弱','电路图薄弱'], weakness:'● 欧姆定律', action:'实验模拟', level:'science' },
  { id:10, name:'10班·数学', score:'61.2', tags:['概率混淆','思路不清'], weakness:'● 统计读图', action:'数据专题', level:'alert' },
  { id:11, name:'11班·英语', score:'93.3', tags:['写作稳','长难句强'], weakness:'● 高级句型', action:'读写结合', level:'normal' },
  { id:12, name:'12班·化学', score:'72.5', tags:['推断弱','计算粗心'], weakness:'● 技巧计算', action:'每日一算', level:'running' },
]

const strategyList = [
  { id:1, cls:'5班数学', text:'函数薄弱 → 微专题 + 错题诊所' },
  { id:2, cls:'3班物理', text:'力学薄弱 → 实验小组 + 导学案分层' },
  { id:3, cls:'2班英语', text:'完形高频错 → 真题语境 + 词块记忆' },
  { id:4, cls:'跨班数学', text:'对比教学 → 动态走班、变式教学' },
]

// ==================== ECHARTS ====================
let radarChart, barChart, lineChart, mixChart, blBarChart, mapChart
let mapLoaded = false

function getColors() {
  const s = getComputedStyle(document.body)
  return {
    accent: s.getPropertyValue('--accent').trim(),
    accent2: s.getPropertyValue('--accent-2').trim(),
    accent3: s.getPropertyValue('--accent-3').trim(),
    accentDeep: s.getPropertyValue('--accent-deep').trim(),
    accentSoft: s.getPropertyValue('--accent-soft').trim(),
    accentLight: s.getPropertyValue('--accent-light').trim(),
    textSub: s.getPropertyValue('--text-muted').trim(),
    textPrimary: s.getPropertyValue('--text-primary').trim(),
  }
}

function renderAllCharts() {
  if (!radarChart) radarChart = echarts.init(document.getElementById('chartRadar'))
  if (!barChart) barChart = echarts.init(document.getElementById('chartBar'))
  if (!lineChart) lineChart = echarts.init(document.getElementById('chartLine'))
  if (!mixChart) mixChart = echarts.init(document.getElementById('chartMix'))
  if (!blBarChart) blBarChart = echarts.init(document.getElementById('chartBlBar'))
  if (!mapChart) mapChart = echarts.init(document.getElementById('chartMap'))
  renderRadar(); renderBar(); renderLine(); renderMix(); renderBlBar()
  if (mapLoaded) renderMapChart()
}

// ---- 1. RADAR ----
function renderRadar() {
  const c = getColors()
  radarChart.setOption({
    radar: {
      indicator: [{name:'运算能力',max:120},{name:'逻辑推理',max:120},{name:'空间想象',max:120},{name:'数据分析',max:120},{name:'语言表达',max:120},{name:'综合应用',max:120}],
      center: ['50%','52%'], radius: '62%',
      axisName: { color: c.textSub, fontSize: 10, fontWeight: 600 },
      splitArea: { areaStyle: { color: ['rgba(128,128,128,0.02)', 'rgba(128,128,128,0.05)'] } },
      axisLine: { lineStyle: { color: 'rgba(128,128,128,0.28)', width: 1.2 } },
      splitLine: { lineStyle: { color: 'rgba(128,128,128,0.26)', width: 1.4 } }
    },
    series: [{ type:'radar', data:[{value:[88,42,65,90,55,38],name:'年级平均能力'}], areaStyle:{color:c.accentSoft}, lineStyle:{color:c.accent,width:2.2}, itemStyle:{color:c.accent,borderWidth:2}, symbol:'circle', symbolSize:5 }]
  }, true)
}

// ---- 2. BAR ----
function renderBar() {
  const c = getColors()
  barChart.setOption({
    grid: { left:'22%', right:'6%', top:'8%', bottom:'4%' },
    xAxis: { type:'value', splitLine:{show:false}, axisLabel:{color:c.textSub,fontSize:10} },
    yAxis: { type:'category', data:['函数综合','力学分析','语法填空','文言文阅读','化学方程式'], axisLine:{show:false}, axisLabel:{color:c.textSub,fontSize:10} },
    series: [{ type:'bar', data:[210,95,165,55,175], barWidth:18,
      itemStyle:{ borderRadius:[0,5,5,0], color: new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:c.accentDeep},{offset:0.5,color:c.accent2},{offset:1,color:c.accent3}]) }
    }]
  }, true)
}

// ---- 3. LINE ----
function renderLine() {
  const c = getColors()
  lineChart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['数学','语文','英语'],textStyle:{color:c.textSub,fontSize:10},bottom:0,itemWidth:12,itemHeight:8},
    grid:{left:'6%',right:'8%',top:'10%',bottom:'18%'},
    xAxis:{type:'category',boundaryGap:false,data:['一模','二模','三模','期中','月考1','月考2','月考3','期末'],axisLabel:{color:c.textSub,fontSize:9},axisLine:{lineStyle:{color:'rgba(128,128,128,0.14)'}}},
    yAxis:[
      {type:'value',min:40,max:120,splitLine:{lineStyle:{color:'rgba(128,128,128,0.08)'}},axisLabel:{color:c.textSub,fontSize:9}},
      {type:'value',min:40,max:120,splitLine:{show:false},axisLabel:{color:c.textSub,fontSize:9}}
    ],
    series:[
      {name:'数学',type:'line',data:[58,65,72,68,80,86,92,99],smooth:true,color:c.accent,symbol:'circle',symbolSize:6,lineStyle:{width:2.4},areaStyle:{color:'rgba(107,93,240,0.08)'}},
      {name:'语文',type:'line',data:[88,72,90,68,78,85,70,82],smooth:true,color:'#0d9488',symbol:'diamond',symbolSize:6,lineStyle:{width:2.4},areaStyle:{color:'rgba(13,148,136,0.06)'}},
      {name:'英语',type:'line',data:[48,55,52,70,82,88,92,97],smooth:true,color:'#ffb74d',symbol:'triangle',symbolSize:6,lineStyle:{width:2.4},areaStyle:{color:'rgba(255,183,77,0.06)'}}
    ]
  }, true)
}

// ---- 4. MIX ----
function renderMix() {
  const c = getColors()
  mixChart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['年级均分','优秀率(≥90)'],textStyle:{color:c.textSub,fontSize:10},bottom:0,itemWidth:12,itemHeight:8},
    grid:{left:'12%',right:'6%',top:'10%',bottom:'18%'},
    xAxis:{type:'category',data:['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],axisLabel:{color:c.textSub,fontSize:10},axisLine:{lineStyle:{color:'rgba(128,128,128,0.14)'}}},
    yAxis:[
      {type:'value',name:'均分',nameTextStyle:{color:c.textSub,fontSize:11},splitLine:{lineStyle:{color:'rgba(128,128,128,0.08)'}},axisLabel:{color:c.textSub,fontSize:11,margin:8}},
      {type:'value',name:'优秀率',nameTextStyle:{color:c.textSub,fontSize:11},splitLine:{show:false},axisLabel:{color:c.textSub,fontSize:11}}
    ],
    series:[
      {name:'年级均分',type:'bar',data:[76,82,79,88,84,92,86,81,90,85,78,89],barWidth:28,barGap:'20%',
        itemStyle:{borderRadius:[5,5,0,0],color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:c.accent},{offset:1,color:c.accentDeep}])}
      },
      {name:'优秀率(≥90)',type:'line',yAxisIndex:1,data:[18,30,28,42,36,55,44,32,48,38,22,40],color:'#ffb74d',symbol:'circle',symbolSize:5,lineStyle:{width:2},smooth:true}
    ]
  }, true)
}

// ---- 5. COMBO BAR ----
const category = ["1班","2班","3班","4班","5班","6班","7班","8班","9班","10班","11班","12班"]
const barDataVal = [92.5, 85.5, 66.3, 81.4, 56.8, 93.1, 74.5, 87.9, 70.5, 63.2, 94.2, 68.6]
const lineDataVal = [93, 87, 38, 62, 24, 95, 52, 82, 44, 40, 92, 42]
const rateDataVal = barDataVal.map((b,i) => parseFloat((b/lineDataVal[i]).toFixed(2)))

function renderBlBar() {
  const c = getColors()
  blBarChart.setOption({
    tooltip:{show:true,trigger:'item',axisPointer:{type:'shadow'}},
    legend:{show:true,textStyle:{color:c.textPrimary,fontSize:10},top:0},
    grid:{left:'6%',right:'6%',top:'18%',bottom:'10%'},
    xAxis:{data:category,axisLine:{lineStyle:{color:'rgba(128,128,128,0.14)'}},axisTick:{show:false},axisLabel:{color:c.textPrimary,fontSize:9}},
    yAxis:[
      {splitLine:{show:false},axisLine:{lineStyle:{color:'rgba(128,128,128,0.14)'}},axisLabel:{formatter:'{value}',color:c.textPrimary,fontSize:10}},
      {splitLine:{show:false},axisLine:{lineStyle:{color:'rgba(128,128,128,0.14)'}},axisLabel:{formatter:'{value}',color:c.textPrimary,fontSize:10}}
    ],
    series:[
      {name:'平均分',type:'bar',barWidth:12,itemStyle:{normal:{barBorderRadius:5,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:c.accent},{offset:1,color:c.accentDeep}])}},data:barDataVal},
      {name:'及格率%',type:'bar',barGap:'-120%',barWidth:12,itemStyle:{normal:{barBorderRadius:5,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(180,160,240,0.55)'},{offset:0.3,color:'rgba(160,140,220,0.30)'},{offset:1,color:'rgba(140,120,200,0.10)'}])}},z:5,data:lineDataVal},
      {name:'提升率',type:'line',smooth:true,showAllSymbol:true,symbol:'emptyCircle',symbolSize:6,yAxisIndex:1,itemStyle:{normal:{color:'#F02FC2'}},z:10,data:rateDataVal}
    ]
  }, true)
}

// ---- 6. MAP ----
const nameMapping = {"福州市":"教学区","厦门市":"科创区","泉州市":"人文区","漳州市":"实践区","龙岩市":"山地训练区","三明市":"生态区","南平市":"综合区","莆田市":"体育区","宁德市":"艺术区"}
const classPoints = [
  {name:'1班',lng:119.30,lat:26.08,value:95},{name:'2班',lng:118.10,lat:24.48,value:88},{name:'3班',lng:118.59,lat:24.91,value:52},{name:'4班',lng:117.65,lat:24.51,value:76},{name:'5班',lng:116.83,lat:25.39,value:40},{name:'6班',lng:117.44,lat:26.47,value:93},{name:'7班',lng:118.18,lat:27.54,value:81},{name:'8班',lng:119.01,lat:25.59,value:90},{name:'9班',lng:119.53,lat:27.16,value:65},{name:'10班',lng:118.30,lat:25.10,value:58},{name:'11班',lng:117.95,lat:26.65,value:96},{name:'12班',lng:118.70,lat:24.80,value:72}
]
const scatterData = classPoints.map(p => ({name:p.name, value:[p.lng, p.lat, p.value]}))

function renderMapChart() {
  const c = getColors()
  const dark = isDark.value
  mapChart.setOption({
    tooltip:{trigger:'item',formatter(p){return p.seriesType==='effectScatter'?p.name+'<br/>互动指数: '+p.value[2]+'分':''},textStyle:{fontSize:11}},
    geo:{map:'customFujian',roam:false,zoom:1.3,center:[117.5,26.2],label:{show:false,emphasis:{show:false}},
      itemStyle:{normal:{areaColor:dark?'rgba(20,15,50,0.4)':'rgba(245,242,255,0.55)',borderColor:c.accent,borderWidth:1.5,shadowBlur:8,shadowColor:c.accentLight},emphasis:{areaColor:dark?'rgba(80,50,180,0.25)':'rgba(200,185,240,0.35)',borderWidth:2,borderColor:c.accent}}
    },
    series:[{type:'effectScatter',coordinateSystem:'geo',data:scatterData,symbolSize:7,showEffectOn:'render',rippleEffect:{period:3,scale:1.5,brushType:'stroke'},
      label:{show:true,formatter(p){return p.name},position:'top',color:c.accent,fontSize:9,fontWeight:'bold',textShadowBlur:2,textShadowColor:dark?'#000':'#fff'},
      itemStyle:{color:c.accent,shadowBlur:6,shadowColor:c.accent},z:10
    }]
  }, true)
}

function renderFallback() {
  const c = getColors()
  mapChart.setOption({
    tooltip:{trigger:'item',formatter(p){return p.name+'<br/>互动指数: '+p.value[2]+'分'}},
    xAxis:{show:false,min:115,max:120},yAxis:{show:false,min:24,max:28},
    series:[{type:'effectScatter',data:scatterData,symbolSize:7,label:{show:true,formatter:'{b}',position:'top',color:c.accent,fontSize:9},itemStyle:{color:c.accent}}]
  }, true)
}

fetch('https://geo.datav.aliyun.com/areas_v3/bound/350000_full.json')
  .then(r => r.json())
  .then(geoJson => {
    geoJson.features.forEach(f => { f.properties.name = nameMapping[f.properties.name] || '分区' })
    echarts.registerMap('customFujian', geoJson)
    mapLoaded = true
    if (mapChart) renderMapChart()
  })
  .catch(() => { mapLoaded = true; if (mapChart) renderFallback() })

window.addEventListener('resize', () => {
  radarChart?.resize(); barChart?.resize(); lineChart?.resize(); mixChart?.resize(); blBarChart?.resize(); mapChart?.resize()
})
</script>

<style>
:root {
  --bg-root: #f4f3f9;
  --bg-card: rgba(255,255,255,0.55);
  --bg-nav: rgba(255,255,255,0.82);
  --bg-tag: rgba(107,93,240,0.05);
  --bg-soft: rgba(107,93,240,0.03);
  --accent: #6B5DF0;
  --accent-2: #7B5CFF;
  --accent-3: #A78BFA;
  --accent-light: rgba(107,93,240,0.34);
  --accent-soft: rgba(107,93,240,0.09);
  --accent-glow: rgba(107,93,240,0.22);
  --accent-deep: #5A4AD0;
  --accent-dim: rgba(107,93,240,0.04);
  --border-light: rgba(0,0,0,0.08);
  --border-medium: rgba(0,0,0,0.14);
  --border-active: #6B5DF0;
  --text-primary: #1a1828;
  --text-secondary: #514e68;
  --text-muted: #85829e;
  --divider: rgba(0,0,0,0.06);
  --panel-radius: 16px;
  --trans: 0.35s cubic-bezier(0.22,0.08,0.22,1);
  --green: #0d9488;
  --red: #ef4444;
  --orange: #f59e0b;
}
body.dark {
  --bg-root: #080810;
  --bg-card: rgba(18,19,34,0.50);
  --bg-nav: rgba(10,11,22,0.88);
  --bg-tag: rgba(123,92,255,0.06);
  --bg-soft: rgba(139,112,255,0.04);
  --accent: #8B70FF;
  --accent-2: #7B5CFF;
  --accent-3: #A78BFA;
  --accent-light: rgba(139,112,255,0.40);
  --accent-soft: rgba(139,112,255,0.12);
  --accent-glow: rgba(139,112,255,0.30);
  --accent-deep: #6B50E0;
  --accent-dim: rgba(139,112,255,0.05);
  --border-light: rgba(255,255,255,0.08);
  --border-medium: rgba(255,255,255,0.16);
  --border-active: #8B70FF;
  --text-primary: #e2e0f4;
  --text-secondary: #a09cb8;
  --text-muted: #6d6a88;
  --divider: rgba(255,255,255,0.07);
}

* { margin:0; padding:0; box-sizing:border-box; }
html { font-size:15px; }
body { font-family:'Inter','SF Pro Display','PingFang SC','Microsoft YaHei',system-ui,sans-serif; color:var(--text-primary); background:var(--bg-root); -webkit-font-smoothing:antialiased; height:100vh; overflow:hidden; transition:background 0.4s,color 0.4s; }
#app { height:100vh; }

.login-screen { display:flex; align-items:center; justify-content:center; height:100vh; background:var(--bg-root); }
.login-card { width:380px; background:var(--bg-card); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); border:1.5px solid var(--border-medium); border-radius:20px; padding:36px 28px; box-shadow:0 8px 32px rgba(0,0,0,0.06); }
.login-header { text-align:center; margin-bottom:24px; }
.login-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.6rem; font-weight:700; color:var(--accent); display:flex; align-items:center; justify-content:center; gap:6px; }
.login-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); }
.login-subtitle { font-size:0.82rem; color:var(--text-muted); margin-top:4px; }
.login-input { width:100%; padding:12px; border-radius:12px; border:1.5px solid var(--border-light); background:rgba(255,255,255,0.50); font-size:0.88rem; color:var(--text-primary); outline:none; transition:all 0.25s; text-align:center; }
.login-input:focus { border-color:var(--border-active); box-shadow:0 0 20px var(--accent-glow); }
.login-error { color:var(--orange); font-size:0.76rem; text-align:center; margin-top:8px; }
.login-submit { width:100%; padding:11px; border-radius:12px; background:var(--accent); color:#fff; border:none; font-weight:600; font-size:0.88rem; cursor:pointer; margin-top:12px; transition:all 0.25s; }
.login-submit:hover:not(:disabled) { box-shadow:0 0 20px var(--accent-glow); }
.login-submit:disabled { opacity:0.45; cursor:not-allowed; }

.app-shell { display:flex; flex-direction:column; height:100vh; width:100%; overflow:hidden; padding:5px 8px; gap:5px; min-width:1360px; }
.top-nav { flex-shrink:0; height:48px; display:flex; align-items:center; justify-content:space-between; background:var(--bg-nav); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); border:1.8px solid var(--border-medium); border-radius:var(--panel-radius); padding:0 24px; position:relative; box-shadow:0 0 16px var(--accent-soft); }
.top-nav::before { content:''; position:absolute; pointer-events:none; top:-1px; left:28px; right:28px; height:1.5px; border-radius:1px; background:linear-gradient(90deg,transparent,var(--accent-light),transparent); opacity:0.55; }
.nav-left { display:flex; align-items:center; gap:20px; }
.nav-logo { font-family:'Playfair Display','Georgia',serif; font-style:italic; font-size:1.4rem; font-weight:700; color:var(--accent); letter-spacing:-0.01em; display:flex; align-items:center; gap:7px; }
.nav-logo .dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent-glow); animation:dotPulse 2s ease-in-out infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.6);opacity:0.6} }
.nav-center { display:flex; align-items:center; gap:3px; }
.nav-tab { padding:6px 14px; border-radius:13px; font-size:0.82rem; font-weight:500; color:var(--text-secondary); cursor:pointer; transition:all 0.25s; border:1.5px solid transparent; white-space:nowrap; }
.nav-tab:hover { color:var(--text-primary); background:var(--bg-tag); }
.nav-tab.active { color:var(--accent); background:var(--accent-soft); border-color:var(--accent); box-shadow:0 0 14px var(--accent-glow); }
.nav-right { display:flex; align-items:center; gap:8px; }
.nav-icon { width:32px; height:32px; border-radius:50%; border:1.5px solid var(--border-medium); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--text-secondary); transition:all 0.25s; flex-shrink:0; }
.nav-icon svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.nav-icon:hover { color:var(--accent); border-color:var(--border-active); box-shadow:0 0 16px var(--accent-glow); }
.nav-avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,#7B5CFF,#A78BFA); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:0.74rem; cursor:pointer; border:2px solid transparent; box-shadow:0 0 16px var(--accent-glow); transition:all 0.25s; }
.nav-avatar:hover { transform:scale(1.06); }

.content { flex:1; min-height:0; display:flex; flex-direction:column; gap:5px; }
.kpi-row { flex-shrink:0; display:grid; grid-template-columns:repeat(6,1fr); gap:8px; }
.kpi-item { background:var(--bg-card); backdrop-filter:blur(20px) saturate(1.2); -webkit-backdrop-filter:blur(20px) saturate(1.2); border:1.8px solid var(--accent); border-radius:12px; padding:10px 10px 8px; text-align:center; box-shadow:0 0 16px var(--accent-soft); transition:all 0.25s; position:relative; overflow:hidden; }
.kpi-item::before { content:''; position:absolute; top:0; left:12px; right:12px; height:2.5px; border-radius:0 0 3px 3px; background:linear-gradient(90deg,transparent,var(--accent),transparent); opacity:0.5; pointer-events:none; }
.kpi-item::after { content:''; position:absolute; top:0; left:0; width:100%; height:100%; background:radial-gradient(circle at 50% 120%, var(--accent-soft), transparent 70%); pointer-events:none; }
.kpi-item:hover { border-color:var(--border-active); transform:translateY(-2px); box-shadow:0 6px 24px var(--accent-glow); }
.kpi-num { font-family:'Playfair Display','Noto Serif SC','STSong','SimSun','宋体',serif; font-size:1.75rem; font-weight:700; color:var(--accent); text-shadow:0 0 20px var(--accent-glow); line-height:1.2; letter-spacing:-0.02em; }
.kpi-num small { font-size:0.68rem; font-weight:500; color:var(--text-muted); font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif; }
.kpi-label { font-size:0.68rem; color:var(--text-muted); letter-spacing:1px; margin-top:3px; font-weight:500; text-transform:uppercase; }

.grid-main { flex:1; min-height:0; display:grid; grid-template-columns:22% 50% 28%; gap:8px; }
.col { display:flex; flex-direction:column; gap:8px; min-height:0; overflow-y:auto; }
.col::-webkit-scrollbar { width:3px; }
.col::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }

.panel { background:var(--bg-card); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); border:1.8px solid var(--accent); border-radius:var(--panel-radius); position:relative; overflow:hidden; display:flex; flex-direction:column; flex-shrink:0; min-height:0; transition:all var(--trans); }
.panel:hover { border-color:var(--border-active); box-shadow:0 0 24px var(--accent-glow); }
.panel::before, .panel::after { content:''; position:absolute; z-index:3; pointer-events:none; width:20px; height:20px; opacity:0; transition:opacity 0.3s; }
.panel::before  { top:5px; left:5px;  border-top:2.5px solid var(--accent); border-left:2.5px solid var(--accent); border-radius:4px 0 0 0; }
.panel::after   { bottom:5px; right:5px; border-bottom:2.5px solid var(--accent); border-right:2.5px solid var(--accent); border-radius:0 0 4px 0; }
.panel:hover::before, .panel:hover::after { opacity:1; }

.panel-hd { flex-shrink:0; display:flex; align-items:center; gap:9px; padding:11px 16px 9px; position:relative; z-index:2; border-bottom:1px solid var(--divider); }
.panel-hd i { display:inline-block; width:4.5px; height:15px; background:linear-gradient(180deg,var(--accent),var(--accent-deep)); border-radius:2.5px; box-shadow:0 0 7px var(--accent-glow); flex-shrink:0; }
.panel-title { font-size:0.86rem; font-weight:700; color:var(--text-primary); letter-spacing:0.4px; }
.panel-body { flex:1; min-height:0; position:relative; z-index:2; padding:6px 10px 10px; display:flex; flex-direction:column; }

.f1 { flex:1; } .f09 { flex:0.9; } .f22 { flex:2.2; } .f13 { flex:1.3; } .f15 { flex:1.5; } .f12 { flex:1.2; } .f125 { flex:1.25; }

.panel-focal { border-color:var(--border-active); box-shadow:0 0 20px var(--accent-glow),0 0 44px var(--accent-soft); }
.panel-strip { position:absolute; pointer-events:none; z-index:1; }
.panel-strip.top, .panel-strip.bottom { left:-100%; width:100%; height:1.5px; background:linear-gradient(90deg,transparent,#C4B0FF,#7B5CFF,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
.panel-strip.right, .panel-strip.left { top:-100%; width:1.5px; height:100%; background:linear-gradient(180deg,transparent,#C4B0FF,#A78BFA,#C4B0FF,transparent); box-shadow:0 0 7px #C4B0FF; }
.panel-strip.top    { top:0;    animation:scanH 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); }
.panel-strip.right  { right:0;  animation:scanV 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:0.8s; }
.panel-strip.bottom { bottom:0; animation:scanHRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:1.6s; }
.panel-strip.left   { left:0;   animation:scanVRev 3.2s infinite cubic-bezier(0.45,0.05,0.55,0.95); animation-delay:2.4s; }
@keyframes scanH    { 0%{left:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:100%;opacity:0} }
@keyframes scanHRev { 0%{left:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:-100%;opacity:0} }
@keyframes scanV    { 0%{top:-100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:100%;opacity:0} }
@keyframes scanVRev { 0%{top:100%;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:-100%;opacity:0} }

.table-row { display:flex; justify-content:space-between; align-items:center; font-size:0.70rem; padding:7px 9px; gap:8px; border-radius:6px; color:var(--text-secondary); transition:all 0.2s; position:relative; }
.table-row:nth-child(odd) { background:var(--accent-dim); }
.table-row:hover { background:var(--accent-soft); }
.table-row > span:first-child { font-weight:600; color:var(--text-primary); white-space:nowrap; min-width:75px; font-size:0.72rem; }
.table-row > span:nth-child(2) { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:0.66rem; }
.s-tag { font-size:0.60rem; font-weight:600; padding:2px 9px; border-radius:10px; white-space:nowrap; flex-shrink:0; letter-spacing:0.3px; }
.s-on { color:var(--accent); background:var(--accent-soft); border:1px solid var(--accent-light); }
.s-warn { color:#c27800; background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); }
.s-off { color:#dc2626; background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); }

.gh-grid { display:grid; grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(3,1fr); gap:7px; flex:1; min-height:0; }
.gh-card { background:var(--accent-dim); border-width:1.8px; border-style:solid; border-radius:9px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; transition:all 0.2s; box-shadow:0 0 10px var(--accent-soft); position:relative; overflow:hidden; }
.gh-card::before { content:''; position:absolute; top:0; left:0; width:3px; height:100%; opacity:0; transition:opacity 0.2s; pointer-events:none; }
.gh-card.normal  { border-color:#0d9488; box-shadow:0 0 10px rgba(13,148,136,0.10); }
.gh-card.normal::before  { background:var(--green); }
.gh-card.running { border-color:var(--accent); }
.gh-card.running::before { background:var(--accent); }
.gh-card.warning { border-color:#e5980b; box-shadow:0 0 10px rgba(245,158,11,0.12); }
.gh-card.warning::before { background:var(--orange); }
.gh-card.alert   { border-color:#dc2626; box-shadow:0 0 10px rgba(239,68,68,0.12); }
.gh-card.alert::before   { background:var(--red); }
.gh-card.science { border-color:var(--accent-deep); }
.gh-card.science::before  { background:var(--accent-deep); }
.gh-card:hover { transform:scale(1.04); z-index:12; border-color:var(--border-active); box-shadow:0 0 18px var(--accent-glow); }
.gh-card:hover::before { opacity:1; }

.gh-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.gh-name { font-family:'Noto Serif SC','STSong','SimSun','宋体',serif; font-weight:700; color:var(--text-primary); font-size:0.82rem; }
.gh-score { font-family:'Noto Serif SC','STSong','SimSun','宋体',serif; font-weight:700; color:var(--accent); font-size:0.80rem; }
.gh-tags { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:5px; }
.gh-tag { background:var(--bg-tag); border:1px solid var(--accent-light); padding:3px 8px; border-radius:4px; font-size:0.66rem; color:var(--text-secondary); white-space:nowrap; }
.gh-foot { display:flex; justify-content:space-between; align-items:center; padding-top:4px; border-top:1px solid var(--divider); }
.gh-weak { color:var(--text-muted); font-size:0.68rem; display:flex; align-items:center; gap:2px; }
.gh-act { color:var(--accent); font-weight:700; font-size:0.70rem; }

.gh-card.tip { position:relative; cursor:pointer; }
.gh-card.tip .tip-box { position:absolute; top:-10px; left:-180px; width:172px; background:var(--bg-card); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); border:1.8px solid var(--accent-light); border-radius:10px; padding:12px; font-size:0.66rem; z-index:200; display:none; line-height:1.8; box-shadow:0 8px 32px rgba(0,0,0,0.08); }
.gh-card.tip:hover .tip-box { display:block; }
body.dark .gh-card.tip .tip-box { box-shadow:0 8px 32px rgba(0,0,0,0.6); }
.tip-box .tt { font-weight:700; color:var(--accent); margin-bottom:4px; font-size:0.72rem; }
.tip-box .tr { display:flex; justify-content:space-between; color:var(--text-secondary); }

.leg { display:flex; gap:10px; font-size:0.60rem; color:var(--text-muted); align-items:center; }
.leg span { display:flex; align-items:center; gap:3px; }
.leg i { display:inline-block; width:7px; height:7px; border-radius:50%; flex-shrink:0; }

.strat-list { display:flex; flex-direction:column; gap:8px; flex:1; overflow-y:auto; padding-right:3px; scroll-snap-type:y mandatory; }
.strat-card { background:var(--accent-dim); border:1.8px solid var(--accent); border-radius:10px; padding:16px 15px; display:flex; align-items:flex-start; gap:12px; transition:all 0.25s; box-shadow:0 0 10px var(--accent-soft); scroll-snap-align:start; }
.strat-card:hover { border-color:var(--accent); box-shadow:0 0 18px var(--accent-glow); transform:translateX(3px); }
.strat-num { width:26px; height:26px; border-radius:8px; background:linear-gradient(135deg,var(--accent),var(--accent-deep)); color:#fff; font-size:0.72rem; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 0 10px var(--accent-glow); }
.strat-info { flex:1; min-width:0; }
.strat-subj { font-size:0.78rem; font-weight:700; color:var(--text-primary); margin-bottom:4px; }
.strat-desc { font-size:0.70rem; color:var(--text-secondary); line-height:1.5; }

.chart-wrap { flex:1; width:100%; min-height:0; }

::-webkit-scrollbar { width:3px; }
::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:2px; }
</style>
