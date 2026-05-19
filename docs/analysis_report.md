# 离线分析报告

分析引擎：Spark SQL。

输入：`data/silver/tlc_trips_silver.parquet`

输出 6 类分析结果：

- `outputs/reports/analysis_demand_pattern.csv`
- `outputs/reports/analysis_peak_periods.csv`
- `outputs/reports/analysis_hotspots.csv`
- `outputs/reports/analysis_fare_distance.csv`
- `outputs/reports/analysis_time_features.csv`
- `outputs/reports/analysis_od_rank.csv`

最近一次官方数据运行摘要：

- 订单量最高小时：18 点
- 订单量最高上车区域：`zone_132`
- 最高频 OD 路线：`zone_237_to_zone_236`

分析覆盖：

- 城市交通需求小时规律。
- 早高峰、晚高峰、夜间和平峰对比。
- 上车热点区域排行。
- 距离分桶与费用关系。
- 星期和小时组合下的订单量关系。
- 高频 OD 路线排行。
## 可视化入口

- 离线分析与预测大屏：`http://localhost:8080/offline.html`
- 前端数据文件：`frontend/public/data/offline_dashboard_data.json`
- 展示内容：小时订单趋势、每日订单与收入、热点区域、高频 OD、支付方式、距离费用关系、星期小时热力、Spark MLlib 模型指标、预测值 vs 实际值。
