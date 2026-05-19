# 数据处理流程说明

## 官方数据获取

正式数据集为 NYC TLC Yellow Taxi Trip Record Data：

- 月份：2024-01
- URL：`https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet`
- 本地文件：`data/raw/official/yellow_tripdata_2024-01.parquet`
- 行数：2,964,624
- 字段数：19

下载命令：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/download_tlc_data.py
```

## Bronze 层

实现文件：`src/spark_pipeline/warehouse.py`

处理逻辑：

- Spark 读取官方 Parquet。
- 将官方字段名统一为小写下划线风格。
- 保留原始记录，不做清洗过滤。
- 输出 `data/bronze/tlc_trips_bronze.parquet`。
- 输出 `outputs/reports/bronze_profile.json`，包含行数、字段数、字段名和缺失值统计。

## Silver 层

处理逻辑：

- 将官方字段映射为标准业务字段，例如：
  - `tpep_pickup_datetime` -> `pickup_datetime`
  - `tpep_dropoff_datetime` -> `dropoff_datetime`
  - `PULocationID` -> `pickup_location_id`
  - `DOLocationID` -> `dropoff_location_id`
- 解析上下车时间。
- 过滤空时间、负距离、负费用、异常乘客数和异常行程时长。
- 计算 `trip_duration_min`。
- 派生 `pickup_date`、`pickup_month`、`pickup_hour`、`pickup_weekday`、`is_weekend`。
- 构建 `pickup_zone`、`dropoff_zone`、`od_pair`。

输出：

- `data/silver/tlc_trips_silver.parquet`
- `outputs/reports/silver_quality_report.json`

最近一次结果：

- 输入行数：2,964,624
- 输出行数：2,721,905
- 删除异常行数：242,719

## Gold 层

Gold 层生成 6 张正式表：

- `hourly_metrics`：小时订单量、平均距离、平均费用、平均时长、收入。
- `daily_metrics`：每日订单量、收入、平均费用。
- `pickup_hotspots`：上车热点区域。
- `od_routes`：高频 OD 路线。
- `payment_metrics`：支付方式订单、收入、平均小费。
- `demand_features`：Spark MLlib 需求预测特征表。

每张表输出 Parquet、CSV 和 JSON。

## 离线分析与模型

离线分析基于 Silver 表输出 6 类报告，模型基于 `demand_features` 使用 Spark MLlib 训练线性回归基线和随机森林改进模型。
