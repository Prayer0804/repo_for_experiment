# 数据质量与清洗报告

正式数据使用 NYC TLC 官方 Yellow Taxi 2024 年 1 月 Parquet。

- 官方原始行数：2,964,624
- 文件大小：49,961,641 bytes
- 原始字段数：19
- Spark Silver 输出行数：2,721,905
- 删除异常行数：242,719
- 删除比例：0.081872
- Silver 字段数：30

清洗规则：

- 删除上车或下车时间为空的记录。
- 删除行程时长小于等于 0 或超过 360 分钟的记录。
- 删除距离小于等于 0 或超过 80 英里的记录。
- 删除车费小于等于 0 或超过 400 的记录。
- 删除乘客数小于等于 0 或超过 8 的记录。
- 删除缺失上车区域或下车区域的记录。

主要统计：

- 平均行程距离：3.2876
- 平均车费：18.4228
- 平均总金额：27.3921
- 平均行程时长：14.9354 分钟
- 平均乘客数：1.3544

机器可读报告：

- `outputs/reports/official_tlc_metadata.json`
- `outputs/reports/bronze_profile.json`
- `outputs/reports/silver_quality_report.json`
