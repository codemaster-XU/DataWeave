# 离线分析子模块（基于现有 ecommerce.db）

## 作用
- 复用 Web 作业生成的 SQLite 数据库 `ecommerce.db`，做额外离线可视化。
- 输出图片文件，可用于 PPT/答辩展示。

## 依赖
```bash
pip install pandas matplotlib seaborn
```

## 数据源
- 直接使用项目根目录运行后的 `ecommerce.db`（由 `import mysql2.py` 自动生成并填充样本数据）。
- 如果放在其他路径，修改 `ANALYSIS_DB_PATH`。

## 运行
```bash
cd analysis-offline
python run_offline_charts.py
```
- 输出图片在 `analysis-offline/output/`。
- 如需重新造数据，先回到根目录运行 `python import mysql2.py` 一次（自动种子）。

## 生成的图表
- `orders_sales_trend.png`：订单数与销售额按日趋势
- `category_revenue.png`：品类销售额占比（条形图）
- `rfm_scatter.png`：用户 RFM 粗分散点（Recency/Frequency/Monetary）

## 如何接入 PPT/报告
1. 确认根目录已生成 `ecommerce.db`。
2. 运行脚本得到 output 图片。
3. 在 PPT 中插入这些图片，配上文字说明（数据源、口径）。

