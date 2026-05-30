<template>
<div class="app">
  <ResearcherNav active-tab="hotspot">
    <template #nav-extra>
      <select class="domain-select" v-model="currentDomain" @change="switchDomain(currentDomain)">
        <option v-for="d in domains" :key="d.key" :value="d.key">{{ d.label }}</option>
      </select>
      <input type="text" class="search-input" v-model="searchQuery" placeholder="检索论文、基因、品种…">
    </template>
  </ResearcherNav>

  <div class="main-wrapper" ref="mainWrapper">
    <!-- 左栏：最新论文 -->
    <div class="column col-left" ref="colLeft">
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>📄 最新论文 · <span>{{ domainData.label }}</span></div>
        <div class="card-body">
          <div class="paper-grid">
            <div v-for="(p, i) in domainData.papers" :key="i" class="paper-mini">
              <div class="paper-title">{{ p.title }}</div>
              <div class="paper-meta">{{ p.authors }} · {{ p.journal }} · 引用{{ p.citations }}</div>
              <div class="paper-tags">
                <span v-for="t in p.tags" :key="t" class="paper-tag">{{ t }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 拖拽条1 -->
    <div class="resize-bar" ref="bar1" @mousedown="startResize($event, 'bar1')"></div>
    <!-- 中栏：趋势图 + 热搜榜 -->
    <div class="column col-mid" ref="colMid">
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>📈 近5年发表趋势</div>
        <div class="card-body">
          <div class="chart-wrap"><svg viewBox="0 0 400 130" preserveAspectRatio="xMidYMid meet" v-html="trendSvg"></svg></div>
          <div class="stat-row">
            <div v-for="(s, i) in domainData.stats" :key="i" class="stat-card">
              <div class="stat-val">{{ s.val }}</div>
              <div class="stat-lbl">{{ s.lbl }}</div>
            </div>
          </div>
          <div class="trend-extra">{{ domainData.trendAnalysis }}</div>
        </div>
      </div>
      <div class="card" style="flex:1;">
        <div class="card-hd"><i></i>🔥 研究热搜榜</div>
        <div class="card-body">
          <div class="hot-search-list">
            <div v-for="(item, idx) in hotSearchItems" :key="idx" class="hot-item">
              <div class="hot-rank" :class="idx === 0 ? 'top1' : idx === 1 ? 'top2' : idx === 2 ? 'top3' : 'normal'">{{ idx + 1 }}</div>
              <div class="hot-info">
                <div class="hot-toprow">
                  <span class="hot-keyword">{{ item.kw }}</span>
                  <span class="hot-index">{{ Math.round(item.w * 100) }}</span>
                </div>
                <div class="hot-botrow">
                  <div class="hot-bar-wrap"><div class="hot-bar-fill" :style="{ width: item.w * 100 + '%' }"></div></div>
                  <span class="hot-papers">{{ Math.round(item.w * 120) }}篇</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 拖拽条2 -->
    <div class="resize-bar" ref="bar2" @mousedown="startResize($event, 'bar2')"></div>
    <!-- 右栏：旭日图 + 知识摘要 -->
    <div class="column col-right" ref="colRight">
      <div class="card flex-half">
        <div class="card-hd"><i></i>📊 研究热点图谱</div>
        <div class="card-body sunburst-card-body">
          <div ref="sunburstEl" id="sunburstChart"></div>
          <div class="sunburst-legend">
            <div class="legend-row"><span class="legend-dot infra"></span> 基础设施层</div>
            <div class="legend-row"><span class="legend-dot tech"></span> 关键技术层</div>
            <div class="legend-row"><span class="legend-dot scene"></span> 应用场景层</div>
          </div>
        </div>
      </div>
      <div class="card flex-half">
        <div class="card-hd"><i></i>📋 智能知识摘要</div>
        <div class="card-body insight-card-body">
          <div class="insight-scroll-wrap">
            <div class="insight-card">
              <div class="insight-title">📋 领域趋势总结</div>
              <div class="insight-text">{{ domainData.insight }}</div>
              <div class="insight-sources">
                <span v-for="s in domainData.insightSources" :key="s" class="insight-source">📄 {{ s }}</span>
              </div>
              <div class="insight-recommend">
                <div class="rec-title">📚 推荐阅读经典文献</div>
                <div v-for="(p, i) in domainData.recPapers" :key="i" class="rec-item">
                  • {{ p.title }} <span style="color:var(--text3);font-size:0.5rem;">— {{ p.authors }}, {{ p.journal }}</span>
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
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useAuth } from '../../composables/useAuth.js'
import ResearcherNav from '../../components/ResearcherNav.vue'

const isDark = ref(false)
const currentDomain = ref('fruit')
const searchQuery = ref('')
const mainWrapper = ref(null)
const colLeft = ref(null)
const colMid = ref(null)
const colRight = ref(null)
const bar1 = ref(null)
const bar2 = ref(null)
const router = useRouter()
const route = useRoute()
const { logout: authLogout } = useAuth()
function handleLogout() {
  authLogout()
  try { localStorage.removeItem('nanobot-webui.chatId') } catch {}
  router.push('/login')
}
const sunburstEl = ref(null)
let chartInstance = null

const domains = [
  { key: 'fruit', label: '果树栽培' },
  { key: 'veg', label: '蔬菜育种' },
  { key: 'smart', label: '智慧农业' },
  { key: 'path', label: '植物病理' },
  { key: 'soil', label: '土壤改良' },
]

const agriData = {
  fruit: {
    label: '果树栽培',
    papers: [
      { title: '苹果砧木耐盐性分子机制及MdNHX1基因功能解析', authors: '张立新 等', journal: '园艺学报 2025', citations: 38, tags: ['苹果', '耐盐', '基因功能'] },
      { title: '基于多光谱遥感的柑橘黄龙病早期诊断模型', authors: '李慧 等', journal: 'Comput. Electron. Agric. 2025', citations: 27, tags: ['柑橘', '病害诊断', '遥感'] },
      { title: '猕猴桃采后软腐病生防菌筛选及抑菌机理研究', authors: '王军 等', journal: 'Postharvest Biol. Technol. 2025', citations: 19, tags: ['猕猴桃', '采后病害', '生物防治'] },
      { title: '葡萄果实花色苷合成调控因子VvMYBA1的CRISPR编辑', authors: '陈明 等', journal: 'Plant Physiol. 2025', citations: 45, tags: ['葡萄', '基因编辑', '花色苷'] },
      { title: '干旱胁迫下梨树根系分泌物对土壤微生物群落的影响', authors: '赵强 等', journal: 'Soil Biol. Biochem. 2025', citations: 22, tags: ['梨', '干旱胁迫', '根际微生物'] },
      { title: '荔枝成花调控基因LcFT的表达模式与功能分析', authors: '韩雪 等', journal: 'Front. Plant Sci. 2025', citations: 16, tags: ['荔枝', '成花调控', '基因表达'] },
      { title: '基于GWAS的桃果实糖酸性状遗传位点解析', authors: '周明 等', journal: 'Horticulture Research 2025', citations: 33, tags: ['桃', 'GWAS', '糖酸'] },
      { title: '苹果MdMYB44基因在花青苷积累中的功能研究', authors: '刘芳 等', journal: 'Plant J. 2025', citations: 29, tags: ['苹果', '花青苷', 'MYB'] },
      { title: '柑橘果实柠檬酸代谢调控网络研究进展', authors: '王磊 等', journal: 'Front. Plant Sci. 2025', citations: 14, tags: ['柑橘', '柠檬酸', '代谢'] },
      { title: '葡萄抗寒性QTL定位及候选基因挖掘', authors: '李强 等', journal: 'BMC Plant Biol. 2025', citations: 18, tags: ['葡萄', '抗寒', 'QTL'] },
    ],
    keywords: ['基因编辑', '耐盐性', '砧木育种', '采后保鲜', '遥感监测', '生物防治', '花色苷', '根际微生物', '干旱胁迫', '分子标记'],
    kwWeights: [0.92, 0.82, 0.88, 0.75, 0.80, 0.70, 0.78, 0.65, 0.72, 0.60],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [420, 560, 780, 1050, 1380],
    stats: [{ val: '1,380', lbl: '2025' }, { val: '↑31%', lbl: '年增长' }, { val: '3.2万', lbl: '引用' }, { val: '86', lbl: '核心期刊' }],
    trendAnalysis: '2025年全球果树栽培领域发文量达到1,380篇，较2021年增长229%，年均增长率31%。基因编辑（CRISPR）相关论文占比从8%上升至22%，成为增长最快子方向。预测2026年发文量将突破1,600篇，基因编辑与智能传感交叉融合将成为新趋势。',
    insight: '基于近两年高水平论文分析，果树栽培领域呈现三大趋势：①基因编辑技术从模式作物向砧木育种快速渗透，MdNHX1等耐盐基因的功能验证成为热点；②多光谱无人机与深度学习结合，实现果园病虫害早期智能诊断；③采后生物防治剂筛选加速，替代化学保鲜剂的市场需求迫切。建议关注CRISPR与遥感交叉应用方向。',
    insightSources: ['Plant Physiology 2023', 'Precision Agric. 2024', 'Postharvest Biol. Technol. 2024', 'Horticulture Research 2023'],
    recPapers: [
      { title: 'CRISPR/Cas9-mediated mutagenesis of MdNHX1 enhances salt tolerance in apple rootstock', authors: 'Zhang et al.', journal: 'Plant Physiology 2023' },
      { title: 'Multi-spectral UAV remote sensing for early detection of citrus Huanglongbing', authors: 'Li & Wang', journal: 'Precision Agriculture 2024' },
      { title: 'Postharvest biocontrol of kiwifruit soft rot using Bacillus velezensis', authors: 'Wang et al.', journal: 'Postharvest Biol. Technol. 2024' },
    ]
  },
  veg: {
    label: '蔬菜育种',
    papers: [
      { title: '番茄耐热性QTL精细定位及SlHSP20鉴定', authors: '刘洋 等', journal: 'Theor. Appl. Genet. 2025', citations: 32, tags: ['番茄', '耐热性', 'QTL'] },
      { title: '基因组选择的辣椒果实品质性状遗传改良', authors: '黄丽 等', journal: 'Hortic. Res. 2025', citations: 28, tags: ['辣椒', '基因组选择', '品质'] },
      { title: '白菜抗根肿病基因CRa的等位变异分析', authors: '孙伟 等', journal: 'Front. Plant Sci. 2025', citations: 15, tags: ['白菜', '抗病基因', '等位变异'] },
      { title: '黄瓜单性结实调控网络及CsACS2功能验证', authors: '周芳 等', journal: 'Plant J. 2025', citations: 41, tags: ['黄瓜', '单性结实', '调控'] },
      { title: '茄子耐低温基因SmCBF3克隆与功能研究', authors: '吴刚 等', journal: 'Plant Sci. 2025', citations: 20, tags: ['茄子', '耐低温', '基因克隆'] },
      { title: '甘蓝型油菜花色变异分子机制及育种应用', authors: '郑丽 等', journal: 'Mol. Breed. 2025', citations: 12, tags: ['甘蓝', '花色', '分子育种'] },
      { title: '菠菜草酸代谢关键基因鉴定与低草酸种质创制', authors: '陈磊 等', journal: 'Theor. Appl. Genet. 2025', citations: 25, tags: ['菠菜', '草酸', '种质'] },
      { title: '洋葱鳞茎膨大期糖代谢转录组分析', authors: '王芳 等', journal: 'Front. Plant Sci. 2025', citations: 17, tags: ['洋葱', '糖代谢', '转录组'] },
    ],
    keywords: ['基因编辑', '基因组选择', '耐热性', 'QTL定位', '抗病基因', '单性结实', '分子标记', '品质改良', '杂种优势', '雄性不育'],
    kwWeights: [0.90, 0.88, 0.85, 0.80, 0.78, 0.72, 0.75, 0.82, 0.68, 0.62],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [380, 520, 710, 920, 1150],
    stats: [{ val: '1,150', lbl: '2025' }, { val: '↑25%', lbl: '年增长' }, { val: '2.8万', lbl: '引用' }, { val: '72', lbl: '核心期刊' }],
    trendAnalysis: '蔬菜育种领域近五年保持25%年增长率，分子标记辅助选择与基因编辑技术深度结合。',
    insight: '蔬菜育种正从单一性状改良转向多性状聚合，基因组选择与基因编辑的联合应用加速了育种进程。耐热性与抗病基因的精细定位为标记辅助育种提供了分子靶标。建议关注单性结实调控网络在设施蔬菜中的应用潜力。',
    insightSources: ['Theor. Appl. Genet. 2023', 'Horticulture Research 2024'],
    recPapers: [
      { title: 'Genome-wide association study of heat tolerance in tomato', authors: 'Liu et al.', journal: 'Theor. Appl. Genet. 2023' },
      { title: 'Genomic selection for fruit quality in pepper', authors: 'Huang et al.', journal: 'Horticulture Research 2024' }
    ]
  },
  smart: {
    label: '智慧农业',
    papers: [
      { title: '无人机多光谱与深度学习的冬小麦产量预测', authors: '杨帆 等', journal: 'Precis. Agric. 2025', citations: 55, tags: ['产量预测', '无人机', '深度学习'] },
      { title: '农业物联网边缘计算节点能耗优化策略', authors: '马超 等', journal: 'Comput. Electron. Agric. 2025', citations: 34, tags: ['物联网', '边缘计算', '能耗'] },
      { title: '视觉Transformer的田间杂草实时识别系统', authors: '林杰 等', journal: 'Biosyst. Eng. 2025', citations: 42, tags: ['杂草识别', 'Transformer'] },
      { title: '数字孪生技术在温室环境调控中的应用', authors: '何平 等', journal: 'Agronomy 2025', citations: 18, tags: ['数字孪生', '温室', '调控'] },
      { title: '强化学习的智能灌溉决策系统研究', authors: '钱程 等', journal: 'Agric. Water Manag. 2025', citations: 25, tags: ['智能灌溉', '强化学习'] },
    ],
    keywords: ['深度学习', '无人机', '产量预测', '物联网', '边缘计算', '杂草识别', '数字孪生', '温室调控', '智能灌溉', '机器人'],
    kwWeights: [0.92, 0.88, 0.85, 0.80, 0.72, 0.78, 0.68, 0.75, 0.65, 0.60],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [280, 480, 820, 1400, 2100],
    stats: [{ val: '2,100', lbl: '2025' }, { val: '↑50%', lbl: '年增长' }, { val: '4.5万', lbl: '引用' }, { val: '105', lbl: '核心期刊' }],
    trendAnalysis: '智慧农业是增长最快的子领域，五年间发文量增长650%，年增长率达50%。无人机遥感与深度学习的融合应用最为突出。',
    insight: '智慧农业的核心趋势是"感知-决策-执行"闭环的智能化。深度学习在遥感图像解析中表现优异，Transformer架构开始替代CNN成为主流。边缘计算解决了农田网络带宽瓶颈，数字孪生则推动温室管理从经验驱动向数据驱动转型。',
    insightSources: ['Precision Agric. 2024', 'Comput. Electron. Agric. 2024', 'Biosyst. Eng. 2025'],
    recPapers: [
      { title: 'Deep learning-based wheat yield prediction using UAV multispectral imagery', authors: 'Yang et al.', journal: 'Precision Agric. 2024' }
    ]
  },
  path: {
    label: '植物病理',
    papers: [
      { title: '小麦条锈菌无毒基因AvrStb6克隆与功能分析', authors: '高远 等', journal: 'Nat. Commun. 2025', citations: 62, tags: ['条锈菌', '无毒基因'] },
      { title: '稻瘟病菌效应蛋白MoCDIP4致病机制', authors: '徐亮 等', journal: 'Plant Cell 2025', citations: 48, tags: ['稻瘟病', '效应蛋白'] },
      { title: '宏基因组学的连作土壤病原菌群落解析', authors: '段鹏 等', journal: 'ISME J. 2025', citations: 35, tags: ['连作障碍', '宏基因组'] },
      { title: '晚疫病菌RXLR效应子寄主靶标鉴定', authors: '林峰 等', journal: 'New Phytol. 2025', citations: 40, tags: ['晚疫病', '效应子'] },
    ],
    keywords: ['无毒基因', '效应蛋白', '连作障碍', '宏基因组', '生物防治', '抗病育种', '病原菌检测', '分子互作', '土壤微生物'],
    kwWeights: [0.90, 0.85, 0.78, 0.80, 0.72, 0.82, 0.68, 0.75, 0.65],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [520, 650, 820, 980, 1200],
    stats: [{ val: '1,200', lbl: '2025' }, { val: '↑22%', lbl: '年增长' }, { val: '3.6万', lbl: '引用' }, { val: '92', lbl: '核心期刊' }],
    trendAnalysis: '植物病理学保持22%的年增长率，分子互作机制研究持续深入。效应蛋白与无毒基因的鉴定为抗病育种提供了精准靶点。',
    insight: '病原菌效应蛋白与寄主靶标的分子互作是当前研究焦点，结构生物学与功能基因组学的结合加速了无毒基因的克隆。土壤宏基因组学为连作障碍的微生物机制提供了新视角，生物防治剂的开发有望替代化学农药。',
    insightSources: ['Nat. Commun. 2024', 'Plant Cell 2024', 'ISME J. 2025'],
    recPapers: [
      { title: 'Cloning of wheat stripe rust avirulence gene AvrStb6', authors: 'Gao et al.', journal: 'Nat. Commun. 2024' },
      { title: 'Rice blast effector MoCDIP4 targets host defense pathways', authors: 'Xu et al.', journal: 'Plant Cell 2024' }
    ]
  },
  soil: {
    label: '土壤改良',
    papers: [
      { title: '生物炭配施有机肥对酸化茶园土壤的改良效果', authors: '胡涛 等', journal: 'Geoderma 2025', citations: 28, tags: ['生物炭', '有机肥'] },
      { title: '丛枝菌根真菌在盐碱地修复中的生态功能', authors: '魏然 等', journal: 'Soil Biol. Biochem. 2025', citations: 33, tags: ['菌根真菌', '盐碱地'] },
      { title: '纳米零价铁对稻田土壤重金属钝化效果', authors: '沈浩 等', journal: 'J. Hazard. Mater. 2025', citations: 44, tags: ['纳米材料', '重金属'] },
      { title: '蚯蚓堆肥对设施菜地微塑料降解的影响', authors: '顾伟 等', journal: 'Environ. Pollut. 2025', citations: 19, tags: ['蚯蚓堆肥', '微塑料'] },
    ],
    keywords: ['生物炭', '菌根真菌', '盐碱地修复', '重金属钝化', '有机肥', '纳米材料', '土壤微生物', '碳封存', '连作障碍', '养分循环'],
    kwWeights: [0.88, 0.80, 0.82, 0.85, 0.75, 0.72, 0.78, 0.68, 0.70, 0.62],
    trendYears: ['2021', '2022', '2023', '2024', '2025'],
    trendValues: [350, 480, 620, 780, 950],
    stats: [{ val: '950', lbl: '2025' }, { val: '↑22%', lbl: '年增长' }, { val: '2.2万', lbl: '引用' }, { val: '58', lbl: '核心期刊' }],
    trendAnalysis: '土壤改良领域稳步增长，生物炭与微生物修复是两大核心方向。重金属污染治理与盐碱地改良论文占比超过50%。',
    insight: '生物炭的改土效果已被大量研究证实，其与有机肥的协同施用可显著提升土壤有机碳和微生物活性。菌根真菌在盐碱地修复中的应用潜力巨大，纳米零价铁的重金属钝化效率优于传统修复剂。',
    insightSources: ['Geoderma 2024', 'Soil Biol. Biochem. 2024', 'J. Hazard. Mater. 2025'],
    recPapers: [
      { title: 'Biochar and organic fertilizer co-application improves acidified tea garden soil', authors: 'Hu et al.', journal: 'Geoderma 2024' },
      { title: 'Arbuscular mycorrhizal fungi in saline-alkali soil remediation', authors: 'Wei et al.', journal: 'Soil Biol. Biochem. 2024' }
    ]
  }
}

const sunburstData = {
  name: "root",
  children: [{
    name: "基础设施层",
    children: [
      { name: "物联网传感器·土壤/气象", value: 62 },
      { name: "农业无人机/机器人底盘", value: 48 },
      { name: "高光谱成像设备", value: 35 },
      { name: "边缘计算网关", value: 33 }
    ]
  }, {
    name: "关键技术层",
    children: [
      { name: "智慧灌溉·水肥一体化", value: 100 },
      { name: "AI病虫害识别", value: 96 },
      { name: "温室环境智能控制", value: 88 },
      { name: "农业机器视觉/采摘", value: 70 },
      { name: "无人机精准植保", value: 64 },
      { name: "作物生长模型", value: 52 },
      { name: "区块链溯源·可信农业", value: 28 }
    ]
  }, {
    name: "应用场景层",
    children: [
      { name: "设施园艺/温室大棚", value: 86 },
      { name: "果园精准管理", value: 74 },
      { name: "智能采收系统", value: 56 },
      { name: "种质资源数字化", value: 45 },
      { name: "都市农业/垂直农场", value: 36 }
    ]
  }]
}

const domainData = computed(() => agriData[currentDomain.value])

const hotSearchItems = computed(() => {
  const data = domainData.value
  return data.keywords.map((kw, i) => ({ kw, w: data.kwWeights[i] }))
    .sort((a, b) => b.w - a.w)
    .slice(0, 6)
})

const trendSvg = computed(() => {
  const data = domainData.value
  const w = 400, h = 130, pad = 30
  const maxV = Math.max(...data.trendValues)
  const n = data.trendValues.length, xStep = (w - 2 * pad) / (n - 1)
  let html = ''
  for (let i = 0; i <= 4; i++) {
    const y = pad + (h - 2 * pad) * i / 4
    html += `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" stroke="var(--divider)" stroke-width="0.5"/>`
  }
  html += `<line x1="${pad}" y1="${h - pad}" x2="${w - pad}" y2="${h - pad}" stroke="var(--divider)" stroke-width="1"/>`
  let areaPts = `${pad},${h - pad} `
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep
    const y = h - pad - (v / maxV) * (h - 2 * pad)
    areaPts += `${x},${y} `
  })
  areaPts += `${pad + (n - 1) * xStep},${h - pad}`
  html += `<defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--chart-line)" stop-opacity="0.18"/><stop offset="100%" stop-color="var(--chart-line)" stop-opacity="0.02"/></linearGradient></defs>`
  html += `<polygon points="${areaPts}" fill="url(#ag)"/>`
  let linePts = ''
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep
    const y = h - pad - (v / maxV) * (h - 2 * pad)
    linePts += `${x},${y} `
  })
  html += `<polyline points="${linePts.trim()}" fill="none" stroke="var(--chart-line)" stroke-width="2" stroke-linejoin="round"/>`
  data.trendValues.forEach((v, i) => {
    const x = pad + i * xStep, y = h - pad - (v / maxV) * (h - 2 * pad)
    html += `<circle cx="${x}" cy="${y}" r="3.5" fill="var(--card)" stroke="var(--chart-line)" stroke-width="2"/>`
    html += `<text x="${x}" y="${y - 10}" text-anchor="middle" font-size="7.5" fill="var(--accent)" font-weight="600">${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}</text>`
  })
  data.trendYears.forEach((yr, i) => {
    html += `<text x="${pad + i * xStep}" y="${h - 6}" text-anchor="middle" font-size="7" fill="var(--text3)">${yr}</text>`
  })
  return html
})

function switchDomain(key) {
  currentDomain.value = key
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.classList.toggle('dark', isDark.value)
  nextTick(() => {
    updateSunburstTheme()
    if (chartInstance) chartInstance.resize()
  })
}

function getSunBorderColor() {
  return document.body.classList.contains('dark') ? '#2d1b4e' : '#ffffff'
}

let initRetries = 0
function initSunburst() {
  if (!sunburstEl.value) return
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  const w = sunburstEl.value.clientWidth
  const h = sunburstEl.value.clientHeight
  if (w === 0 || h === 0) {
    initRetries++
    if (initRetries < 20) {
      requestAnimationFrame(() => initSunburst())
    }
    return
  }
  initRetries = 0
  chartInstance = echarts.init(sunburstEl.value)
  const borderColor = getSunBorderColor()
  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 10, 60, 0.95)',
      borderColor: '#a855f7',
      borderWidth: 1,
      textStyle: { color: '#f2eaff', fontSize: 11 },
      formatter: function(params) {
        if (!params.name || params.name === 'root') return ''
        const pathNodes = params.treePathInfo || []
        let pathStr = ''
        if (pathNodes.length > 1) {
          const names = pathNodes.slice(1).map(p => p.name)
          pathStr = names.join(' > ')
        }
        return '<strong>' + params.name + '</strong><br/>热度指数: ' + params.value +
          '<br/><span style="font-size:10px;color:#c4b5fd;">' + pathStr + '</span>'
      }
    },
    series: [{
      type: 'sunburst',
      data: [sunburstData],
      radius: [0, '78%'],
      center: ['50%', '52%'],
      sort: undefined,
      nodeClick: false,
      label: { show: false },
      emphasis: {
        focus: 'descendant',
        scale: true,
        label: {
          show: true,
          position: 'inside',
          fontSize: 8,
          fontWeight: '600',
          color: '#ffffff',
          textShadowBlur: 4,
          textShadowColor: 'rgba(0,0,0,0.6)',
          formatter: function(params) {
            if (params.name === 'root') return ''
            var n = params.name
            return n.length > 8 ? n.slice(0, 8) + '…' : n
          }
        },
        itemStyle: {
          shadowBlur: 14,
          shadowColor: 'rgba(130, 80, 200, 0.25)',
          borderWidth: 2,
          borderColor: '#ffffff'
        }
      },
      levels: [
        { r0: '0%', r: '18%', itemStyle: { color: '#4a3cc0', borderRadius: 0, borderWidth: 2.5, borderColor: borderColor } },
        { r0: '18%', r: '42%', itemStyle: { color: '#5a4cd8', borderRadius: 0, borderWidth: 2, borderColor: borderColor } },
        { r0: '42%', r: '60%', itemStyle: { color: '#6B5DF0', borderRadius: 0, borderWidth: 1.8, borderColor: borderColor } },
        { r0: '60%', r: '72%', itemStyle: { color: '#8B70FF', borderRadius: 0, borderWidth: 1.2, borderColor: borderColor } },
        { r0: '72%', r: '78%', itemStyle: { color: '#A78BFA', borderRadius: 0, borderWidth: 1, borderColor: borderColor } }
      ],
      itemStyle: { borderRadius: 0, borderColor: borderColor, borderWidth: 2 },
      animation: true,
      animationDuration: 800
    }]
  })
}

function updateSunburstTheme() {
  if (!chartInstance) return
  const borderColor = getSunBorderColor()
  chartInstance.setOption({
    series: [{
      levels: [
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } },
        { itemStyle: { borderColor: borderColor } }
      ],
      itemStyle: { borderColor: borderColor }
    }]
  })
}

// ---- Resize bars ----
let resizingBar = null, startX, startLW, startRW

function startResize(e, barId) {
  resizingBar = barId
  e.target.classList.add('active')
  startX = e.clientX
  if (barId === 'bar1') {
    startLW = colLeft.value.getBoundingClientRect().width
    startRW = colMid.value.getBoundingClientRect().width
  } else {
    startLW = colMid.value.getBoundingClientRect().width
    startRW = colRight.value.getBoundingClientRect().width
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

function onMouseMove(e) {
  if (!resizingBar) return
  const dx = e.clientX - startX
  const ww = mainWrapper.value.getBoundingClientRect().width
  let nl = startLW + dx, nr = startRW - dx
  if (nl < 200) nl = 200
  if (nr < 200) nr = 200
  if (resizingBar === 'bar1') {
    colLeft.value.style.width = (nl / ww * 100) + '%'
    colMid.value.style.width = (nr / ww * 100) + '%'
  } else {
    colMid.value.style.width = (nl / ww * 100) + '%'
    colRight.value.style.width = (nr / ww * 100) + '%'
  }
}

function onMouseUp() {
  if (resizingBar) {
    document.querySelectorAll('.resize-bar').forEach(b => b.classList.remove('active'))
    resizingBar = null
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    if (chartInstance) chartInstance.resize()
  }
}

function onWindowResize() {
  if (chartInstance) chartInstance.resize()
}

onMounted(() => {
  nextTick(() => {
    requestAnimationFrame(() => {
      initSunburst()
    })
  })
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('resize', onWindowResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style>
:root {
  --bg: #f2f1f6;
  --card: rgba(255, 255, 255, 0.72);
  --nav-bg: rgba(255, 255, 255, 0.92);
  --accent: #5a4cd8;
  --accent-light: rgba(90, 76, 216, 0.10);
  --accent-glow: rgba(90, 76, 216, 0.20);
  --border: rgba(0, 0, 0, 0.08);
  --text: #18161f;
  --text2: #4a4658;
  --text3: #7a7688;
  --divider: rgba(0, 0, 0, 0.05);
  --radius: 18px;
  --radius-sm: 10px;
  --chart-line: #5a4cd8;
  --tag-bg: rgba(90, 76, 216, 0.05);
  --tag-border: rgba(90, 76, 216, 0.22);
  --insight-accent: #5a4cd8;
  --scrollbar-thumb: rgba(0, 0, 0, 0.15);
  --insight-scroll-thumb: rgba(90, 76, 216, 0.35);
  --insight-scroll-track: rgba(90, 76, 216, 0.06);
}
body.dark {
  --bg: #06050f;
  --card: rgba(14, 13, 26, 0.60);
  --nav-bg: rgba(8, 7, 18, 0.92);
  --accent: #8B70FF;
  --accent-light: rgba(139, 112, 255, 0.15);
  --accent-glow: rgba(139, 112, 255, 0.25);
  --border: rgba(255, 255, 255, 0.06);
  --text: #e4e1f6;
  --text2: #a8a3c0;
  --text3: #6d6a88;
  --divider: rgba(255, 255, 255, 0.05);
  --chart-line: #8B70FF;
  --tag-bg: rgba(139, 112, 255, 0.08);
  --tag-border: rgba(139, 112, 255, 0.25);
  --insight-accent: #8B70FF;
  --scrollbar-thumb: rgba(255, 255, 255, 0.15);
  --insight-scroll-thumb: rgba(139, 112, 255, 0.45);
  --insight-scroll-track: rgba(139, 112, 255, 0.08);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg); color: var(--text); height: 100vh; overflow: hidden;
  transition: 0.3s; letter-spacing: 0.01em;
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 10px; }
.insight-scroll-wrap::-webkit-scrollbar { width: 8px; }
.insight-scroll-wrap::-webkit-scrollbar-track { background: var(--insight-scroll-track); border-radius: 10px; margin: 4px 0; }
.insight-scroll-wrap::-webkit-scrollbar-thumb { background: var(--insight-scroll-thumb); border-radius: 10px; border: 2px solid transparent; background-clip: padding-box; min-height: 40px; }
.insight-scroll-wrap::-webkit-scrollbar-thumb:hover { background: var(--accent); border: 2px solid transparent; background-clip: padding-box; }
.insight-scroll-wrap { scrollbar-width: thin; scrollbar-color: var(--insight-scroll-thumb) var(--insight-scroll-track); }

.app { display: flex; flex-direction: column; height: 100vh; max-width: 1832px; margin: 0 auto; padding: 6px 10px; gap: 4px; }

/* Top nav */
.top-nav {
  flex-shrink: 0; height: 48px; background: var(--nav-bg); backdrop-filter: blur(18px);
  border: 2px solid var(--accent); border-radius: var(--radius);
  padding: 0 20px; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 0 0 1px var(--accent-light), 0 0 18px var(--accent-glow);
}
.nav-left { display: flex; align-items: center; gap: 16px; }
.nav-logo {
  font-family: 'Playfair Display', serif; font-style: italic;
  font-size: 1.1rem; font-weight: 700; color: var(--accent);
  display: flex; align-items: center; gap: 8px;
}
.nav-logo .dot { width: 7px; height: 7px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 14px var(--accent-glow); animation: dotPulse 2.4s infinite; }
@keyframes dotPulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:0.5} }
.nav-right { display: flex; gap: 8px; align-items: center; }
.nav-center { display: flex; align-items: center; gap: 4px; }
.nav-tab {
  padding: 6px 14px; border-radius: 14px; font-size: 0.64rem; font-weight: 500;
  color: var(--text2); cursor: pointer; transition: all 0.2s; border: 1.5px solid transparent;
}
.nav-tab:hover { color: var(--text); background: var(--accent-light); }
.nav-tab.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow);
}

.domain-nav { display: flex; gap: 2px; flex-wrap: wrap; }
.domain-btn {
  padding: 6px 14px; border: 1.5px solid transparent; background: transparent;
  color: var(--text2); font-weight: 500; font-size: 0.64rem; cursor: pointer;
  transition: 0.2s; border-radius: 20px; letter-spacing: 0.03em; white-space: nowrap;
}
.domain-btn.active {
  color: var(--accent); background: var(--accent-light); border-color: var(--accent);
  font-weight: 600; box-shadow: inset 0 0 0 1px var(--accent-glow), 0 0 12px var(--accent-glow);
}
.search-input {
  padding: 7px 14px; border: 2px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.62rem; width: 170px; border-radius: 20px;
  font-family: inherit; transition: 0.2s;
}
.search-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
.domain-select {
  padding: 7px 10px; border: 2px solid var(--border); background: var(--card);
  color: var(--text); font-size: 0.62rem; border-radius: 20px;
  font-family: inherit; cursor: pointer; transition: 0.2s; outline: none;
}
.domain-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
.icon-btn {
  width: 32px; height: 32px; border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; color: var(--text2); font-size: 0.85rem; transition: 0.2s;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.icon-btn svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 1.8; }
.icon-btn:hover { color: var(--accent); border-color: var(--accent); box-shadow: 0 0 14px var(--accent-glow); }

.main-wrapper { flex: 1; min-height: 0; display: flex; gap: 0; position: relative; }
.column { display: flex; flex-direction: column; gap: 4px; padding: 0 3px; }
.col-left { width: 28.4%; min-width: 260px; }
.col-mid { width: 38.6%; min-width: 280px; }
.col-right { width: 33%; min-width: 260px; }
.resize-bar {
  width: 5px; cursor: col-resize; background: transparent; position: relative; z-index: 10;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: background 0.2s;
}
.resize-bar:hover, .resize-bar.active { background: var(--accent-light); }
.resize-bar::after {
  content: ''; width: 2px; height: 40px; background: var(--accent);
  border-radius: 1px; opacity: 0.4;
}
.resize-bar:hover::after { opacity: 0.8; }

.card {
  background: var(--card); backdrop-filter: blur(12px);
  border: 2px solid var(--accent); border-radius: var(--radius); overflow: hidden;
  display: flex; flex-direction: column; box-shadow: 0 0 0 1px var(--accent-light);
  transition: box-shadow 0.3s;
}
.card:hover { border-color: var(--accent); box-shadow: 0 0 28px var(--accent-glow), 0 0 0 2px var(--accent-light); }
.card-hd {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  border-bottom: 1px solid var(--divider); font-weight: 700; font-size: 0.68rem;
  text-transform: uppercase; letter-spacing: 0.04em; flex-shrink: 0;
}
.card-hd i { width: 4px; height: 16px; background: linear-gradient(180deg, var(--accent), #4a3cc0); border-radius: 2px; box-shadow: 0 0 6px var(--accent-glow); }
.card-body { padding: 8px 12px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 3px; flex: 1; min-height: 0; }
.card.flex-half { flex: 1; min-height: 0; max-height: 50%; }

.sunburst-card-body { overflow: hidden; padding: 4px 6px 6px 6px; display: flex; align-items: center; justify-content: center; position: relative; }
#sunburstChart { width: 100%; height: 100%; min-height: 180px; }

.sunburst-legend {
  position: absolute; top: 8px; right: 10px; display: flex; flex-direction: column; gap: 4px;
  background: var(--card); backdrop-filter: blur(6px); border: 1px solid var(--accent);
  border-radius: 10px; padding: 6px 10px; z-index: 20; pointer-events: none;
}
.legend-row { display: flex; align-items: center; gap: 6px; font-size: 0.55rem; font-weight: 500; color: var(--text); white-space: nowrap; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.legend-dot.infra { background: #4a3cc0; }
.legend-dot.tech { background: #5a4cd8; }
.legend-dot.scene { background: #8B70FF; }
body.dark .legend-dot.infra { background: #6d28d9; }
body.dark .legend-dot.tech { background: #7c3aed; }
body.dark .legend-dot.scene { background: #a78bfa; }

.card-body.insight-card-body { overflow-y: hidden; padding: 8px 8px 8px 12px; }

.paper-grid { display: flex; flex-direction: column; gap: 4px; }
.paper-mini {
  background: var(--tag-bg); border: 1px solid var(--tag-border); padding: 8px 10px;
  cursor: pointer; transition: 0.2s; font-size: 0.58rem; border-radius: var(--radius-sm); flex-shrink: 0;
}
.paper-mini:hover { border-color: var(--accent); background: var(--accent-light); box-shadow: 0 0 10px var(--accent-glow); transform: translateY(-1px); }
.paper-title { font-weight: 600; color: var(--text); font-size: 0.6rem; line-height: 1.4; }
.paper-meta { font-size: 0.5rem; color: var(--text3); margin-top: 2px; }
.paper-tags { margin-top: 4px; display: flex; gap: 3px; flex-wrap: wrap; }
.paper-tag {
  display: inline-block; padding: 2px 6px; border: 1px solid var(--accent);
  color: var(--accent); font-size: 0.46rem; font-weight: 500; cursor: pointer;
  transition: 0.15s; border-radius: 12px; background: var(--tag-bg);
}
.paper-tag:hover { background: var(--accent); color: #fff; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3px; margin-top: 2px; flex-shrink: 0; }
.stat-card { background: var(--tag-bg); border: 1px solid var(--tag-border); padding: 8px 4px 6px; text-align: center; border-radius: var(--radius-sm); transition: 0.2s; }
.stat-val { font-weight: 700; font-size: 0.75rem; color: var(--accent); }
.stat-lbl { font-size: 0.48rem; color: var(--text3); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.03em; }
.chart-wrap { display: flex; align-items: center; justify-content: center; flex: 1; min-height: 0; }
.chart-wrap svg { width: 100%; height: auto; max-height: 100%; }
.trend-extra { font-size: 0.56rem; color: var(--text2); line-height: 1.6; padding: 6px 0 0; border-top: 1px solid var(--divider); margin-top: 2px; flex-shrink: 0; }

.hot-search-list { display: flex; flex-direction: column; gap: 1px; }
.hot-item { display: flex; align-items: center; gap: 8px; padding: 3px 6px; border-radius: var(--radius-sm); transition: background 0.2s; cursor: pointer; flex-shrink: 0; }
.hot-item:hover { background: var(--accent-light); }
.hot-rank { width: 20px; height: 20px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.6rem; flex-shrink: 0; }
.hot-rank.top1 { background: linear-gradient(135deg, #6d28d9, #7c3aed); color: #fff; }
.hot-rank.top2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); color: #fff; }
.hot-rank.top3 { background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: #fff; }
.hot-rank.normal { background: var(--accent-light); color: var(--accent); }
.hot-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.hot-toprow { display: flex; align-items: baseline; gap: 8px; }
.hot-keyword { font-weight: 600; font-size: 0.62rem; color: var(--text); }
.hot-index { font-weight: 700; color: var(--accent); font-size: 0.55rem; flex-shrink: 0; }
.hot-botrow { display: flex; align-items: center; gap: 8px; }
.hot-bar-wrap { flex: 1; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
.hot-bar-fill { height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--accent), #A78BFA); }
.hot-papers { font-size: 0.46rem; color: var(--text3); flex-shrink: 0; }

.heat-matrix { display: flex; flex-wrap: wrap; gap: 4px; align-content: flex-start; justify-content: center; padding: 4px 0; }

.insight-scroll-wrap { flex: 1; min-height: 0; overflow-y: auto; padding-right: 4px; display: flex; flex-direction: column; gap: 6px; }
.insight-card {
  background: var(--card); border: 1px solid var(--tag-border); border-radius: var(--radius-sm);
  padding: 12px 14px; position: relative; overflow: hidden; flex-shrink: 0;
}
.insight-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--insight-accent); border-radius: 2px 0 0 2px; }
.insight-title { font-weight: 700; font-size: 0.7rem; color: var(--accent); margin-bottom: 6px; letter-spacing: 0.03em; }
.insight-text { font-size: 0.58rem; color: var(--text2); line-height: 1.7; margin-bottom: 8px; }
.insight-sources { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px; }
.insight-source { font-size: 0.48rem; padding: 2px 7px; border: 1px solid var(--accent); color: var(--accent); border-radius: 12px; background: var(--tag-bg); }
.insight-recommend { border-top: 1px solid var(--divider); padding-top: 6px; margin-top: 3px; }
.rec-title { font-weight: 700; font-size: 0.58rem; color: var(--accent); margin-bottom: 3px; }
.rec-item { font-size: 0.55rem; color: var(--text2); line-height: 1.5; padding: 1px 0; cursor: pointer; transition: 0.2s; }
.rec-item:hover { color: var(--accent); text-decoration: underline; }

@media(max-width:900px) {
  .main-wrapper { flex-direction: column; overflow-y: auto; }
  .resize-bar { display: none; }
  .col-left, .col-mid, .col-right { width: 100% !important; min-width: 0; flex: none; }
  #sunburstChart { min-height: 240px; }
}
</style>
