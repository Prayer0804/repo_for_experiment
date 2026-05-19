# 最终交付清单

| 模块 | 验收项 | 状态 |
| --- | --- | --- |
| 官方数据 | 下载 NYC TLC Yellow Taxi 2024-01 官方 Parquet，记录 URL、大小、行数、字段 | 已完成 |
| 环境 | Conda 环境、Docker Desktop、Kafka/Flink/Spark 镜像可运行 | 已完成 |
| Spark Bronze | 读取官方 Parquet，统一字段名，输出 Bronze Parquet 和画像报告 | 已完成 |
| Spark Silver | 清洗异常值，生成时间、区域、OD 特征和质量报告 | 已完成 |
| Spark Gold | 生成小时、日期、热点、OD、支付方式、需求特征表 | 已完成 |
| 离线分析 | 6 类分析结果均有实际 CSV/JSON 输出 | 已完成 |
| Spark MLlib | 线性回归基线和随机森林模型实际训练并保存指标与模型 | 已完成 |
| Kafka 造流 | 交通事件生产者持续写入 `traffic-events` | 已完成 |
| Flink 窗口 | 1 分钟窗口、10 秒滑动步长，输出 `congestion-alerts` | 已完成 |
| 实时 API | `/api/health`、`/api/congestion/latest`、`/ws/congestion` | 已完成 |
| 实时大屏 | WebSocket 动态展示严重拥堵路段和窗口指标 | 已完成 |
| 离线结果大屏 | 展示 Gold 指标、离线分析、Spark MLlib 指标、预测值与实际值 | 已完成 |
| 文档 | README、环境配置指南与 docs 报告同步实际结果 | 已完成 |
| 测试 | 单元测试、编译检查、强验收脚本 | 已完成 |

最近运行命令：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/download_tlc_data.py
.\scripts\run_official_spark_all_docker.ps1
.\scripts\start_realtime_stack.ps1
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 80 --max-events 5200
conda run --no-capture-output -n traffic-bigdata pytest
conda run --no-capture-output -n traffic-bigdata python -m compileall scripts src tests
conda run --no-capture-output -n traffic-bigdata python scripts/validate_delivery.py
```

最近结果：

- 官方数据：2,964,624 行
- Silver：2,721,905 行
- Spark MLlib：随机森林 RMSE 41.5874，R2 0.6348
- Flink 作业：RUNNING
- 实时 API：已缓存 100 条窗口拥堵告警，并验证 `latest_window` 随新生产事件持续刷新
- 离线结果大屏：`frontend/public/offline.html`，数据文件 `frontend/public/data/offline_dashboard_data.json`
- 组员复现指南：`README.md`、`docs/setup_guide.md`、`docs/package_checklist.md`
