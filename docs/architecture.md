# 系统架构说明

## 总体链路

```text
NYC TLC 官方 Yellow Taxi Parquet
  -> Spark Bronze 原始层
  -> Spark Silver 清洗明细层
  -> Spark Gold 指标表/特征表
  -> Spark SQL 离线分析
  -> Spark MLlib 需求预测
  -> 离线结果 JSON/CSV/Parquet

人造交通路段事件
  -> Kafka traffic-events
  -> Flink 事件时间滑动窗口
  -> Kafka congestion-alerts
  -> FastAPI/WebSocket
  -> ECharts 实时流控大屏
```

## 离线数据工程

- `scripts/download_tlc_data.py`：下载 NYC TLC 官方月度 Parquet，并写入 `outputs/reports/official_tlc_metadata.json`。
- `scripts/run_official_spark_all_docker.ps1`：使用 Docker Linux Spark 运行正式离线全流程。
- `src/spark_pipeline/warehouse.py`：实现 Bronze、Silver、Gold 三层数仓。
- `src/spark_pipeline/analysis.py`：实现 6 类 Spark SQL 离线分析。
- `src/spark_pipeline/ml.py`：实现 Spark MLlib 需求预测模型。

## 实时流控

- `docker-compose.realtime.yml`：启动 Kafka、Flink、实时 API 和大屏。
- `scripts/produce_traffic_events.py`：持续造交通路段事件并写入 Kafka。
- `flink/sql/traffic_congestion.sql`：Flink SQL 滑动窗口作业。
- `src/visualization_api/realtime_api.py`：消费 Flink 告警并通过 REST/WebSocket 提供给前端。
- `frontend/public/index.html`：实时流控大屏。

## 运行环境

- Spark：`apache/spark:3.5.3` 容器。
- Kafka：`apache/kafka:3.7.0` 容器。
- Flink：`flink:1.19.1-scala_2.12-java17` 容器。
- API：FastAPI 容器。
- 前端：Nginx 容器。

正式 Spark 流程在 Linux 容器中运行，以避免 Windows 本地 Hadoop NativeIO 问题；这不改变 Spark 作为主处理引擎的事实。
