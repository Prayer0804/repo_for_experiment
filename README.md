# 基于交通大数据的处理与分析

本项目使用 NYC TLC 官方 Yellow Taxi 月度 Parquet 数据，完成交通大数据处理、分析、预测、实时流处理和可视化展示。项目已经包含可复现代码、配置、脚本、数据产物、模型产物、测试和文档，适合直接打包给组员用于 PPT、报告和现场演示。

## 组员拿到压缩包后先看这里

如果只是查看已有结果、截图写 PPT，不需要重跑 Spark 全流程：

```powershell
cd 解压后的项目目录
conda env create -f environment.yml
conda run --no-capture-output -n traffic-bigdata python scripts/export_offline_dashboard.py
conda run --no-capture-output -n traffic-bigdata python -m http.server 8088 --directory frontend/public
```

浏览器打开：

- 离线分析与预测大屏：`http://localhost:8088/offline.html`
- 实时流控大屏静态页面入口：`http://localhost:8088/index.html`

如果要演示 Kafka + Flink 实时流控，需要先启动 Docker Desktop，然后运行：

```powershell
.\scripts\start_realtime_stack.ps1
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
```

浏览器打开：

- 实时流控大屏：`http://localhost:8080`
- 离线分析与预测大屏：`http://localhost:8080/offline.html`
- Flink Web UI：`http://localhost:8081`
- 实时 API 健康检查：`http://localhost:8000/api/health`

实时生产者窗口不要关。生产者停止后，Flink 事件时间窗口会在最后几个窗口输出完后停止推进，大屏也就不会继续变化，这是流处理正常行为。

组员写 PPT 和报告时，建议按这个顺序看文档：

1. `README.md`：完整运行说明。
2. `docs/setup_guide.md`：环境配置和演示步骤。
3. `docs/package_checklist.md`：压缩包交付清单。
4. `docs/architecture.md`：系统架构。
5. `docs/data_pipeline.md`：Bronze/Silver/Gold 数据流。
6. `docs/analysis_report.md`：离线分析。
7. `docs/model_report.md`：模型训练和评估。
8. `docs/realtime_report.md`：Kafka/Flink 实时流。
9. `docs/team_work_split.md`：四人分工。

## 环境要求

推荐系统：

- Windows 10/11 x64
- 16 GB 内存以上更稳，8 GB 也可以但首次拉镜像和跑 Spark 会慢
- 至少 10 GB 可用磁盘空间
- 网络可访问 Docker Hub；如果要重新下载官方 TLC 数据，还需要能访问 NYC TLC 数据地址

必须安装：

- Conda 或 Anaconda
- Docker Desktop
- PowerShell

Docker Desktop 要求：

1. 安装 Docker Desktop，建议安装到 D 盘或其他非系统盘。
2. 使用 WSL 2 backend。安装器如果提示启用 WSL 2、虚拟化或重启，按提示完成。
3. Docker Desktop 可以跳过登录。
4. 打开 Docker Desktop 后，左下角显示 `Engine running`。
5. 在 PowerShell 中确认 Docker 可用：

```powershell
docker --version
docker compose version
```

Conda 环境创建：

```powershell
conda env create -f environment.yml
conda activate traffic-bigdata
```

如果环境已经存在，更新即可：

```powershell
conda env update -n traffic-bigdata -f environment.yml --prune
```

## 已验证官方数据集

- 数据源：NYC TLC Taxi Trip Record Data
- 文件：`yellow_tripdata_2024-01.parquet`
- 官方 URL：`https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet`
- 本地路径：`data/raw/official/yellow_tripdata_2024-01.parquet`
- 文件大小：49,961,641 bytes
- 原始行数：2,964,624
- 原始字段数：19

元数据记录在 `outputs/reports/official_tlc_metadata.json`。

打包给组员时建议保留 `data/` 和 `outputs/`。如果压缩包里不带官方数据，可以让组员重新下载：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/download_tlc_data.py
```

## 项目结构

```text
config/                         配置文件
data/raw/official/              官方 TLC 原始 Parquet
data/bronze/                    Spark Bronze 原始落地层
data/silver/                    Spark Silver 清洗明细层
data/gold/                      Spark Gold 指标表和特征表
src/spark_pipeline/             Spark 数仓、分析、MLlib 主实现
src/streaming/                  Kafka 交通事件生成
src/visualization_api/          实时 API、WebSocket、前端数据导出
flink/sql/                      Flink SQL 滑动窗口作业
docker/                         Spark、Flink、API 镜像定义
frontend/public/                ECharts 实时大屏和离线大屏
outputs/                        报告、指标、模型和预测结果
tests/                          单元测试和输出校验
docs/                           架构、数据流、模型、实时处理和交付文档
```

## 完整重跑离线 Spark 流程

正式 Spark 流程在 Docker Linux 容器中运行，用来避开 Windows 本地 Hadoop NativeIO 对 Parquet 的限制。处理引擎仍然是 Spark 3.5.3。

先确保 Docker Desktop 是 `Engine running`，然后运行：

```powershell
.\scripts\run_official_spark_all_docker.ps1
```

该命令会执行：

1. Bronze：读取官方 TLC Parquet，统一字段命名，输出 `data/bronze/tlc_trips_bronze.parquet`。
2. Silver：清洗异常时间、距离、费用、乘客数，生成时间、区域、OD 特征。
3. Gold：生成小时、日期、热点区域、OD、支付方式、预测特征 6 张表。
4. 离线分析：输出 6 类分析 CSV/JSON。
5. Spark MLlib：训练线性回归基线模型和随机森林改进模型。
6. 导出前端数据：生成 `frontend/public/data/dashboard_data.json` 和 `frontend/public/data/offline_dashboard_data.json`。

首次运行会构建 Spark 镜像，时间取决于网络和机器性能。

## 当前离线结果

- Bronze 输入行数：2,964,624
- Silver 清洗后行数：2,721,905
- 删除异常行数：242,719
- 删除比例：0.081872
- 需求最高小时：18 点
- 订单最高上车区域：`zone_132`
- 高频 OD 路线：`zone_237_to_zone_236`

Spark MLlib 指标：

| 模型 | RMSE | MAE | R2 |
| --- | ---: | ---: | ---: |
| 线性回归基线 | 44.4817 | 27.0715 | 0.5822 |
| 随机森林回归 | 41.5874 | 24.7834 | 0.6348 |

离线大屏展示内容：

- 每小时订单量和收入
- 每日订单量和收入趋势
- 热点上车区域
- 高频 OD 路线
- 支付方式占比
- 高峰时段分析
- 距离与费用关系
- 星期与小时订单热力图
- 模型评估指标
- 预测值 vs 实际值
- 预测明细表

## Kafka/Flink 实时流控

启动 Kafka、Flink、实时 API 和 Nginx 大屏：

```powershell
.\scripts\start_realtime_stack.ps1
```

另开一个 PowerShell 窗口，持续向 Kafka 写入人造交通事件：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
```

限量验证命令：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 80 --max-events 5200
```

实时链路：

1. 生产者写入 Kafka topic `traffic-events`。
2. Flink SQL 使用事件时间和 watermark，按 1 分钟窗口、10 秒滑动步长计算路段拥堵。
3. Flink 将告警写入 Kafka topic `congestion-alerts`。
4. FastAPI 消费告警并提供 `/api/health`、`/api/congestion/latest`、`/ws/congestion`。
5. ECharts 大屏通过 WebSocket 和 3 秒轮询实时更新。

停止实时链路：

```powershell
.\scripts\stop_realtime_stack.ps1
```

## 访问地址

Docker 实时链路启动后：

- 实时流控大屏：`http://localhost:8080`
- 离线分析与预测大屏：`http://localhost:8080/offline.html`
- Flink Web UI：`http://localhost:8081`
- 实时 API：`http://localhost:8000/api/congestion/latest`
- API 健康检查：`http://localhost:8000/api/health`

只用 Python 静态服务器查看离线成果时：

- 离线分析与预测大屏：`http://localhost:8088/offline.html`

## 测试与验收

基础测试：

```powershell
conda run --no-capture-output -n traffic-bigdata pytest
conda run --no-capture-output -n traffic-bigdata python -m compileall scripts src tests
```

完整验收需要实时 Docker 链路正在运行：

```powershell
.\scripts\start_realtime_stack.ps1
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 80 --max-events 5200
conda run --no-capture-output -n traffic-bigdata python scripts/validate_delivery.py
```

当前已验证：

- 单元测试：7 passed
- Flink 作业状态：RUNNING
- 实时 API 已返回 `congestion-alerts` 告警，并验证最新窗口随新事件推进
- 实时大屏 HTTP 状态：200
- 离线大屏 HTTP 状态：200

## 关键产物

- `data/raw/official/yellow_tripdata_2024-01.parquet`
- `data/bronze/tlc_trips_bronze.parquet`
- `data/silver/tlc_trips_silver.parquet`
- `data/gold/*.parquet`
- `outputs/reports/*.json`
- `outputs/reports/analysis_*.csv`
- `outputs/metrics/model_metrics.json`
- `outputs/metrics/demand_predictions.json`
- `outputs/metrics/spark_models/`
- `docker-compose.realtime.yml`
- `flink/sql/traffic_congestion.sql`
- `frontend/public/index.html`
- `frontend/public/offline.html`
- `frontend/public/data/offline_dashboard_data.json`

## 常见问题

### Docker Desktop 需要登录吗？

不需要。可以跳过登录，只要左下角显示 `Engine running`，PowerShell 里 `docker --version` 正常即可。

### 大屏不刷新怎么办？

确认生产者还在运行：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
```

生产者停止后，Flink 事件时间不会无限推进，大屏不会继续刷新。

### 端口被占用怎么办？

本项目默认使用：

- `8080`：大屏
- `8081`：Flink UI
- `8000`：实时 API
- `19092`：Kafka 外部访问

如果端口被占用，先停止旧容器：

```powershell
.\scripts\stop_realtime_stack.ps1
```

或者在 Docker Desktop 中停止同名容器。

### 是否必须重跑完整 Spark？

不必须。压缩包如果保留 `data/`、`outputs/`、`frontend/public/data/`，组员可以直接看大屏和报告。只有需要证明全流程可复现时才重跑 `.\scripts\run_official_spark_all_docker.ps1`。

### 离线大屏图很小或样式没更新怎么办？

按 `Ctrl + F5` 强制刷新浏览器缓存。离线页已经避免在隐藏容器中初始化 ECharts。

### PowerShell 显示中文乱码怎么办？

文件本身是 UTF-8。PowerShell 输出乱码不影响运行。可以先执行：

```powershell
chcp 65001
```

## 已知限制

正式 Spark 处理在 Docker Linux 容器中运行，这是为了绕开 Windows 本地 Hadoop NativeIO 限制；处理引擎仍是 Spark 3.5.3。实时流控数据流为人造交通路段事件，不是 TLC 出租车行程事件，因为该模块目标是 Kafka/Flink 交通拥堵计算与实时大屏。
