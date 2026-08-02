# 科研绘图测试数据

这些 CSV 用于研究者端“科研绘图”功能测试。上传文件后选择对应图表类型，再点击“AI 自动匹配字段”或“生成图表”。

| 文件 | 推荐模板 | 关键字段 |
| --- | --- | --- |
| 火山图.csv | 火山图 | gene, log2fc, padj |
| ROC曲线.csv | ROC 曲线 | fpr, model_a, model_b |
| 表达点图.csv | 表达点图 | cell_type, gene, pct_exp, avg_exp_scaled |
| 边际分布图.csv | 边际分布图 | x, y, group |
| 配对数据图.csv | 配对数据图 | subject, condition, value |
| 分组柱状图.csv | 分组柱状图 | category, value, group |
| 箱线图.csv | 箱线图 | category, value |
| 散点图.csv | 散点图 | x, y |
| 折线图.csv | 折线图 | time, value, group |
| 热图.csv | 热图 | row, column, value |
| heatmap_cn_complete.csv | 热图 | 中文字段/分类；完整矩阵 |
| heatmap_cn_duplicate.csv | 热图 | 中文字段/分类；用于验证重复 row-column 组合报错 |
| heatmap_cn_missing.csv | 热图 | 中文字段/分类；用于验证矩阵缺失组合报错 |
| 热图_完整矩阵.csv | 热图 | 行分类, 列分类, 表达值 |
| 热图_重复组合.csv | 热图 | 用于验证重复 row-column 组合报错 |
| 热图_缺失组合.csv | 热图 | 用于验证矩阵缺失组合报错 |
| 森林图.csv | 森林图 | label, effect, lower, upper |
| 多面板组合图.csv | 多面板组合图 | panel, category, value |

机制示意图和图形摘要使用文字输入，不需要 CSV。可以使用：

```text
研究主题：肿瘤微环境中的纳米药物递送
左侧：纳米颗粒进入肿瘤组织
中间：酸性微环境触发药物释放
右侧：肿瘤细胞凋亡，周围免疫细胞被激活
```

这些数据是用于验证绘图流程的演示数据，不代表真实实验结果。
