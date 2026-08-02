export const figureTemplates = [
  { id: 'volcano', category: '数据分析图', name: '火山图', description: '比较差异效应与统计显著性', input: 'csv', fields: [
    { key: 'gene', label: '基因或项目名称', type: 'categorical' }, { key: 'effect', label: '效应值（如 log2FC）', type: 'numeric' }, { key: 'pvalue', label: '校正后 P 值', type: 'numeric' }
  ], params: [{ key: 'effectThreshold', label: '效应阈值', type: 'number', default: 1 }, { key: 'pThreshold', label: 'P 值阈值', type: 'number', default: 0.05 }, { key: 'topLabels', label: '标注数量', type: 'number', default: 10 }] },
  { id: 'roc', category: '数据分析图', name: 'ROC 曲线', description: '展示模型灵敏度与假阳性率', input: 'csv', fields: [
    { key: 'fpr', label: '假阳性率（FPR）', type: 'numeric' }, { key: 'tpr', label: '真阳性率（可多选模型）', type: 'numeric', multiple: true }
  ], params: [{ key: 'showBaseline', label: '显示随机基线', type: 'boolean', default: true }] },
  { id: 'dotplot', category: '数据分析图', name: '表达点图', description: '用点大小和颜色展示二维分类矩阵', input: 'csv', fields: [
    { key: 'row', label: '行分类', type: 'categorical' }, { key: 'column', label: '列分类', type: 'categorical' }, { key: 'size', label: '点大小数值', type: 'numeric' }, { key: 'color', label: '点颜色数值', type: 'numeric' }
  ], params: [{ key: 'colorMap', label: '配色', type: 'select', options: ['viridis', 'coolwarm', 'Blues'], default: 'viridis' }] },
  { id: 'marginal', category: '数据分析图', name: '边际分布图', description: '散点关系与两侧分布联合展示', input: 'csv', fields: [
    { key: 'x', label: 'X 数值字段', type: 'numeric' }, { key: 'y', label: 'Y 数值字段', type: 'numeric' }, { key: 'group', label: '分组字段', type: 'categorical', optional: true }
  ], params: [{ key: 'bins', label: '分布分箱数', type: 'number', default: 24 }] },
  { id: 'paired', category: '数据分析图', name: '配对数据图', description: '展示同一样本在两个条件下的变化', input: 'csv', fields: [
    { key: 'subject', label: '样本 ID', type: 'categorical' }, { key: 'condition', label: '条件字段', type: 'categorical' }, { key: 'value', label: '测量值', type: 'numeric' }
  ], params: [{ key: 'showPoints', label: '显示样本点', type: 'boolean', default: true }] },
  { id: 'grouped_bar', category: '常规统计图', name: '分组柱状图', description: '支持 category/group/value/error 长表 CSV 的论文风格分组柱状图', input: 'csv', fields: [
    { key: 'category', label: '横轴分类 category', type: 'categorical' }, { key: 'group', label: '分组字段 group', type: 'categorical' }, { key: 'value', label: '柱高数值 value', type: 'numeric' }, { key: 'error', label: '误差数值 error', type: 'numeric', optional: true }
  ], params: [{ key: 'errorBar', label: '误差线类型', type: 'select', options: ['none', 'SD', 'SEM', '95% CI'], default: 'SEM' }] },
  { id: 'scatter', category: '常规统计图', name: '散点图', description: '支持 x,y,group CSV 的论文风格通用散点图', input: 'csv', fields: [
    { key: 'x', label: 'X 数值字段', type: 'numeric' }, { key: 'y', label: 'Y 数值字段', type: 'numeric' }, { key: 'group', label: '分组字段', type: 'categorical', optional: true }
  ], params: [{ key: 'trendLine', label: '显示线性趋势线', type: 'boolean', default: false }, { key: 'trendLineScope', label: '趋势线范围', type: 'select', options: ['overall', 'by_group'], default: 'overall' }] },
  { id: 'line', category: '常规统计图', name: '折线图', description: '展示时间、剂量或顺序趋势', input: 'csv', fields: [
    { key: 'x', label: 'X 字段（时间/数字/顺序）', type: 'any' }, { key: 'y', label: 'Y 字段（原始值）', type: 'numeric' }, { key: 'group', label: '曲线分组字段', type: 'categorical' }, { key: 'event', label: '事件标注字段', type: 'categorical', optional: true }
  ], params: [{ key: 'cumulative', label: '累计求和', type: 'boolean', default: false }, { key: 'showMarkers', label: '显示数据点', type: 'boolean', default: true }, { key: 'showEvents', label: '显示事件标注', type: 'boolean', default: true }, { key: 'showFill', label: '显示填充区域', type: 'boolean', default: false }] },
  { id: 'heatmap', category: '常规统计图', name: '热图', description: '展示行分类、列分类和矩阵数值', input: 'csv', fields: [
    { key: 'row', label: '行分类', type: 'categorical' }, { key: 'column', label: '列分类', type: 'categorical' }, { key: 'value', label: '矩阵数值', type: 'numeric' }
  ], params: [{ key: 'colorMap', label: '配色方案', type: 'select', options: ['Reds', 'viridis', 'coolwarm', 'Blues', 'YlGnBu', 'magma'], default: 'Reds' }, { key: 'showCellValues', label: '显示单元格数值', type: 'boolean', default: true }, { key: 'colorMin', label: '色阶最小值（留空自动）', type: 'number', default: '', min: null }, { key: 'colorMax', label: '色阶最大值（留空自动）', type: 'number', default: '', min: null }, { key: 'showColorbar', label: '显示 colorbar', type: 'boolean', default: true }] },
  { id: 'mechanism_schematic', category: '概念示意图', name: '机制示意图', description: '根据机制、实体和流程生成概念草图', input: 'text', fields: [], params: [] },
  { id: 'graphical_abstract', category: '概念示意图', name: '图形摘要', description: '根据研究问题、方法和结果生成图形摘要', input: 'text', fields: [], params: [] }
]

const nativeTemplateIds = new Set(['volcano', 'roc', 'dotplot', 'marginal', 'paired', 'grouped_bar', 'scatter', 'heatmap'])
for (const template of figureTemplates) {
  template.renderer = template.input === 'text' ? '文字生图模板' : nativeTemplateIds.has(template.id) ? 'skill 原生模板' : '扩展绘图模板'
}

export const templateGroups = [...new Set(figureTemplates.map(item => item.category))]
export const getFigureTemplate = id => figureTemplates.find(item => item.id === id) || figureTemplates[0]

export function defaultTemplateParams(template) {
  return Object.fromEntries((template.params || []).map(item => [item.key, item.default]))
}

