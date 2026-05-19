# 实时流处理说明

实时链路使用真实 Kafka + Flink + FastAPI + ECharts。

## 组件

- Kafka：`apache/kafka:3.7.0`
- Flink：`flink:1.19.1-scala_2.12-java17`
- 实时 API：FastAPI + Kafka Consumer
- 大屏：Nginx 托管 ECharts 页面

## Topic

- 输入 topic：`traffic-events`
- 输出 topic：`congestion-alerts`

## 事件生产者

脚本：`scripts/produce_traffic_events.py`

事件字段：

- `event_id`
- `event_time`
- `road_id`
- `road_name`
- `district`
- `speed_kmh`
- `vehicle_count`
- `occupancy`
- `travel_time_sec`
- `congestion_level`
- `lat`
- `lon`

## Flink 滑动窗口

SQL 文件：`flink/sql/traffic_congestion.sql`

窗口设置：

- 窗口长度：1 分钟
- 滑动步长：10 秒
- 时间语义：事件时间
- Watermark：允许 5 秒乱序

窗口指标：

- 路段事件数
- 平均速度
- 平均道路占有率
- 平均通行时间
- 严重拥堵事件数
- 拥堵等级

## 已验证结果

- Flink 作业状态：RUNNING
- 生产者已多次向 `traffic-events` 写入验证事件，最后一次端到端验证写入 4,200 条事件
- `congestion-alerts` 输出 topic 随 Flink 窗口持续增长
- 实时 API 已从 `congestion-alerts` 回放并跟随最新窗口，缓存 100 条告警
- 最后一次验证中 API 的 `latest_window` 从 `2026-05-09 09:05:20` 连续刷新到 `2026-05-09 09:13:40`
- 示例告警路段：`会展中心环路`
- 大屏地址：`http://localhost:8080`

## 实时刷新修复

- API 消费者改为持久 KafkaConsumer，不再每秒重建 consumer。
- API 默认从 `earliest` 回放 `congestion-alerts`，读到最新后继续跟随新消息，避免大屏一直拿旧缓存。
- 大屏表格、状态栏和速度趋势改为按最新窗口排序刷新，严重程度排序只用于告警排行。
