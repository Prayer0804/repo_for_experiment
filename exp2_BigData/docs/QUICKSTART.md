# 快速开始指南 - 分步操作

本指南提供详细的分步操作说明，帮助你运行项目的各个功能。

---

## 场景 1: 查看离线分析结果（最简单，推荐新手）

这个场景不需要运行 Spark，只需要查看已有的分析结果和可视化大屏。

### 步骤 1: 打开 PowerShell
1. 按 `Win + X`，选择 "Windows PowerShell" 或 "终端"
2. 使用 `cd` 命令进入项目目录：
   ```powershell
   cd E:\workplace\repo\BigData
   ```

### 步骤 2: 激活虚拟环境
```powershell
.\venv\Scripts\Activate.ps1
```
成功后，命令提示符前会显示 `(venv)`

### 步骤 3: 导出离线数据到前端
```powershell
python scripts/export_offline_dashboard.py
```
这个命令会生成 `frontend/public/data/offline_dashboard_data.json` 文件

### 步骤 4: 启动静态 Web 服务器
```powershell
python -m http.server 8088 --directory frontend/public
```
看到 `Serving HTTP on :: port 8088` 表示启动成功

### 步骤 5: 在浏览器中查看
打开浏览器，访问：
- **离线分析大屏**: http://localhost:8088/offline.html
- **实时大屏静态页面**: http://localhost:8088/index.html

### 步骤 6: 停止服务器
在 PowerShell 窗口按 `Ctrl + C` 停止服务器

---

## 场景 2: 运行实时流控演示（需要 Docker）

这个场景会启动 Kafka、Flink、实时 API 和可视化大屏，展示实时交通拥堵监控。

### 前置条件检查

#### 检查 Docker Desktop 是否运行
1. 打开 Docker Desktop 应用
2. 确保左下角显示 "Engine running" 绿色图标
3. 如果没有运行，点击启动并等待完成

#### 验证 Docker 可用
```powershell
docker --version
docker compose version
```
应该看到版本号输出

### 步骤 1: 启动实时技术栈
打开 PowerShell，进入项目目录：
```powershell
cd E:\workplace\repo\BigData
.\scripts\start_realtime_stack.ps1
```

这个脚本会启动：
- Kafka (消息队列)
- Flink (流处理引擎)
- FastAPI (实时 API 服务)
- Nginx (Web 服务器)

**等待时间**: 首次运行需要下载 Docker 镜像，可能需要 5-10 分钟
**成功标志**: 看到类似 "Container traffic-realtime-api-1 Started" 的消息

### 步骤 2: 验证服务启动
在浏览器中访问以下地址，确认服务正常：
- Flink Web UI: http://localhost:8081
- API 健康检查: http://localhost:8000/api/health

### 步骤 3: 启动交通事件生产者
**重要**: 打开一个新的 PowerShell 窗口（不要关闭第一个）

```powershell
cd E:\workplace\repo\BigData
.\venv\Scripts\Activate.ps1
python scripts/produce_traffic_events.py --events-per-second 60
```

你会看到类似这样的输出：
```
Producing traffic events at 60 events/second...
Sent 60 events
Sent 120 events
...
```

**保持这个窗口运行**，不要关闭！

### 步骤 4: 查看实时大屏
打开浏览器，访问：
- **实时流控大屏**: http://localhost:8080
- **离线分析大屏**: http://localhost:8080/offline.html
- **Flink 作业监控**: http://localhost:8081

大屏会每 3 秒自动刷新，显示实时的交通拥堵情况。

### 步骤 5: 停止实时系统

#### 停止事件生产者
在生产者窗口按 `Ctrl + C`

#### 停止 Docker 容器
在另一个 PowerShell 窗口运行：
```powershell
cd E:\workplace\repo\BigData
.\scripts\stop_realtime_stack.ps1
```

---

## 场景 3: 重新运行完整 Spark 数据处理流程

这个场景会从原始数据开始，运行完整的 Spark ETL 流程、数据分析和机器学习。

### 前置条件
- Docker Desktop 必须运行
- 确保有足够的磁盘空间（至少 10 GB）
- 首次运行需要下载 Spark 镜像

### 步骤 1: 确认 Docker 运行
```powershell
docker ps
```
应该能看到命令正常执行（即使没有容器也没关系）

### 步骤 2: 运行完整 Spark 流程
```powershell
cd E:\workplace\repo\BigData
.\scripts\run_official_spark_all_docker.ps1
```

这个脚本会依次执行：
1. **Bronze 层**: 读取原始 TLC Parquet 数据
2. **Silver 层**: 数据清洗和特征工程
3. **Gold 层**: 生成分析指标表
4. **离线分析**: 生成 6 类分析报告
5. **机器学习**: 训练线性回归和随机森林模型
6. **导出前端数据**: 生成可视化数据文件

**预计时间**: 5-15 分钟（取决于机器性能）

### 步骤 3: 查看处理结果

#### 查看数据文件
```powershell
ls data/bronze/
ls data/silver/
ls data/gold/
```

#### 查看分析报告
```powershell
ls outputs/reports/
ls outputs/metrics/
```

#### 查看模型评估指标
```powershell
cat outputs/metrics/model_metrics.json
```

### 步骤 4: 查看可视化结果
按照 **场景 1** 的步骤启动 Web 服务器，查看更新后的大屏。

---

## 场景 4: 运行测试

验证代码是否正常工作。

### 步骤 1: 激活虚拟环境
```powershell
cd E:\workplace\repo\BigData
.\venv\Scripts\Activate.ps1
```

### 步骤 2: 运行所有测试
```powershell
python -m pytest tests/ -v
```

### 步骤 3: 查看测试结果
应该看到类似输出：
```
tests/test_ml_features.py::test_build_features_splits_target_and_predictors PASSED
tests/test_pipeline_outputs.py::test_core_outputs_exist_after_pipeline PASSED
...
============================== 7 passed in 5.00s ==============================
```

### 步骤 4: 运行特定测试
```powershell
# 只测试 ML 功能
python -m pytest tests/test_ml_features.py -v

# 只测试流处理
python -m pytest tests/test_traffic_streaming.py -v
```

---

## 常见问题排查

### 问题 1: 端口被占用
**错误信息**: `Address already in use` 或 `端口已被占用`

**解决方法**:
```powershell
# 查看占用端口的进程
netstat -ano | findstr :8080
netstat -ano | findstr :8081
netstat -ano | findstr :8000

# 停止旧的 Docker 容器
.\scripts\stop_realtime_stack.ps1

# 或者在 Docker Desktop 中手动停止容器
```

### 问题 2: Docker 容器启动失败
**错误信息**: `Cannot connect to the Docker daemon`

**解决方法**:
1. 打开 Docker Desktop
2. 等待左下角显示 "Engine running"
3. 重新运行启动脚本

### 问题 3: 虚拟环境激活失败
**错误信息**: `无法加载文件 ... 因为在此系统上禁止运行脚本`

**解决方法**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 4: Python 模块找不到
**错误信息**: `ModuleNotFoundError: No module named 'xxx'`

**解决方法**:
```powershell
# 确保虚拟环境已激活（提示符前有 (venv)）
.\venv\Scripts\Activate.ps1

# 重新安装依赖
pip install -r requirements.txt
```

### 问题 5: 大屏不刷新
**原因**: 事件生产者停止运行

**解决方法**:
确保生产者窗口还在运行，并且能看到 "Sent XXX events" 的输出

### 问题 6: Flink 作业没有运行
**检查方法**:
1. 访问 http://localhost:8081
2. 点击 "Running Jobs"
3. 应该看到 "Traffic Congestion Detection" 作业

**解决方法**:
```powershell
# 重启整个实时栈
.\scripts\stop_realtime_stack.ps1
.\scripts\start_realtime_stack.ps1
```

---

## 推荐的演示流程

如果要向他人演示项目，建议按以下顺序：

### 1. 快速演示（5 分钟）
1. 启动静态服务器查看离线大屏
2. 展示数据分析结果和模型评估

### 2. 完整演示（15 分钟）
1. 展示离线大屏（5 分钟）
2. 启动实时流控系统（5 分钟）
3. 展示实时大屏和 Flink UI（5 分钟）

### 3. 技术深度演示（30 分钟）
1. 展示项目结构和代码
2. 运行测试
3. 展示离线分析
4. 演示实时流控
5. 查看 Flink SQL 和数据流

---

## 快速命令参考

```powershell
# 激活环境
.\venv\Scripts\Activate.ps1

# 查看离线结果
python scripts/export_offline_dashboard.py
python -m http.server 8088 --directory frontend/public

# 启动实时系统
.\scripts\start_realtime_stack.ps1
python scripts/produce_traffic_events.py --events-per-second 60

# 停止实时系统
.\scripts\stop_realtime_stack.ps1

# 运行测试
python -m pytest tests/ -v

# 重跑 Spark
.\scripts\run_official_spark_all_docker.ps1
```

---

## 需要帮助？

- 查看 `README.md` 了解项目概述
- 查看 `SETUP.md` 了解环境配置
- 查看 `docs/` 目录下的详细文档
- 运行 `python -m pytest tests/ -v` 验证环境

祝使用愉快！
