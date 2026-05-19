# 环境配置与运行演示指南

本文档面向拿到项目压缩包的组员，用于配置环境、查看结果、运行测试和现场演示。

## 1. 解压位置

建议解压到英文或简单中文路径，例如：

```text
D:\code\school\BigData
```

不要只拷贝 `src` 或 `frontend`，报告和演示需要以下目录一起保留：

- `data/`
- `outputs/`
- `frontend/public/data/`
- `docs/`
- `docker/`
- `flink/`
- `scripts/`
- `src/`
- `tests/`

## 2. 安装 Conda 环境

打开 PowerShell，进入项目根目录：

```powershell
cd D:\code\school\BigData
conda env create -f environment.yml
```

如果已经有 `traffic-bigdata` 环境：

```powershell
conda env update -n traffic-bigdata -f environment.yml --prune
```

验证环境：

```powershell
conda run --no-capture-output -n traffic-bigdata python -c "import pandas, pyarrow, pyspark, kafka, fastapi; print('env ok')"
```

## 3. 安装和启动 Docker Desktop

Docker Desktop 用于运行 Kafka、Flink、实时 API、大屏 Nginx 和 Linux Spark。

安装要求：

- Windows 10/11 x64
- 开启 CPU 虚拟化
- 使用 WSL 2 backend
- 可以跳过 Docker 登录
- 建议安装到 D 盘或其他非系统盘

启动后确认：

1. 打开 Docker Desktop。
2. 左下角显示 `Engine running`。
3. PowerShell 中执行：

```powershell
docker --version
docker compose version
```

如果 Docker 提示需要重启，先重启电脑，再打开 Docker Desktop。

## 4. 最短查看离线成果

如果只是截图、写 PPT、看离线分析和模型结果，不需要启动 Kafka/Flink。

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/export_offline_dashboard.py
conda run --no-capture-output -n traffic-bigdata python -m http.server 8088 --directory frontend/public
```

打开：

```text
http://localhost:8088/offline.html
```

页面包含：

- 数据质量概览
- 小时订单趋势
- 每日订单与收入
- 热点区域
- 高频 OD 路线
- 支付方式占比
- 距离费用关系
- 星期小时热力图
- Spark MLlib 模型指标
- 预测值 vs 实际值
- 预测明细表

## 5. 启动实时 Kafka/Flink 演示

先保证 Docker Desktop 是 `Engine running`。

启动实时链路：

```powershell
.\scripts\start_realtime_stack.ps1
```

另开一个 PowerShell 窗口，持续造交通事件流：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
```

打开：

```text
http://localhost:8080
```

其他地址：

- 离线大屏：`http://localhost:8080/offline.html`
- Flink UI：`http://localhost:8081`
- API 健康检查：`http://localhost:8000/api/health`
- 最新拥堵告警：`http://localhost:8000/api/congestion/latest`

停止实时链路：

```powershell
.\scripts\stop_realtime_stack.ps1
```

## 6. 完整重跑 Spark 离线流程

如果要证明数据工程、分析和模型训练完整可复现，运行：

```powershell
.\scripts\run_official_spark_all_docker.ps1
```

该流程会使用 Docker 中的 Spark 3.5.3 执行：

1. 读取官方 NYC TLC Yellow Taxi 2024-01 Parquet。
2. 生成 Bronze/Silver/Gold 三层数据。
3. 输出 6 类离线分析结果。
4. 训练 Spark MLlib 线性回归基线和随机森林模型。
5. 保存模型、评估指标和预测明细。
6. 导出前端展示数据。

首次运行需要构建 Spark 镜像，耗时取决于网络和机器性能。

## 7. 测试和验收

基础测试：

```powershell
conda run --no-capture-output -n traffic-bigdata pytest
conda run --no-capture-output -n traffic-bigdata python -m compileall scripts src tests
```

完整验收需要实时链路正在运行：

```powershell
.\scripts\start_realtime_stack.ps1
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 80 --max-events 5200
conda run --no-capture-output -n traffic-bigdata python scripts/validate_delivery.py
```

## 8. 常见问题

### Docker Desktop 可以跳过登录吗？

可以。只要显示 `Engine running`，命令行能执行 `docker --version`，就可以运行本项目。

### 大屏不刷新怎么办？

实时大屏依赖生产者持续写入 Kafka。确认这个命令仍在运行：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
```

生产者停止后，Flink 的事件时间窗口不会一直推进，大屏不再变化是正常现象。

### 端口冲突怎么办？

默认端口：

- `8080`：大屏
- `8081`：Flink UI
- `8000`：实时 API
- `19092`：Kafka

先停止旧容器：

```powershell
.\scripts\stop_realtime_stack.ps1
```

### 需要重新下载官方数据吗？

如果压缩包保留了 `data/raw/official/yellow_tripdata_2024-01.parquet`，不需要。文件缺失时运行：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/download_tlc_data.py
```

### PowerShell 中文乱码影响运行吗？

不影响。可以执行：

```powershell
chcp 65001
```

### 只想写报告，应该看哪些文档？

- `README.md`：完整运行说明
- `docs/setup_guide.md`：环境配置和演示步骤
- `docs/package_checklist.md`：压缩包交付清单
- `docs/architecture.md`：系统架构
- `docs/data_pipeline.md`：Bronze/Silver/Gold 数据流
- `docs/data_quality_report.md`：数据质量
- `docs/analysis_report.md`：离线分析
- `docs/model_report.md`：模型训练和评估
- `docs/realtime_report.md`：Kafka/Flink 实时流
- `docs/team_work_split.md`：四人分工
- `docs/final_delivery_checklist.md`：交付清单
