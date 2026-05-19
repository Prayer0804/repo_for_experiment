# 环境配置说明

本文档说明如何使用 Python venv 配置项目环境（替代 Conda）。

## 已完成的配置

### 1. Python 虚拟环境
- **Python 版本**: 3.12.6
- **虚拟环境路径**: `E:\workplace\repo\BigData\venv`
- **依赖管理**: 使用 `requirements.txt`

### 2. 已安装的依赖
所有 Python 依赖已通过 pip 安装：
- pandas >= 2.2
- pyarrow >= 16
- scikit-learn >= 1.5
- PyYAML >= 6
- pytest >= 8
- requests >= 2.32
- joblib >= 1.4
- pyspark == 3.5.3
- kafka-python-ng == 2.2.3
- fastapi == 0.115.6
- uvicorn[standard] == 0.34.0

### 3. 前端依赖
- **Node.js 包管理**: npm
- **已安装**: echarts ^5.5.1
- **路径**: `frontend/node_modules`

### 4. Docker 环境
- **Docker 版本**: 27.3.1
- **Docker Compose 版本**: v2.29.7-desktop.1
- **状态**: 已验证可用

### 5. 测试验证
所有 7 个单元测试通过：
```
tests/test_ml_features.py::test_build_features_splits_target_and_predictors PASSED
tests/test_pipeline_outputs.py::test_core_outputs_exist_after_pipeline PASSED
tests/test_pipeline_outputs.py::test_gold_schema_contains_expected_columns PASSED
tests/test_pipeline_outputs.py::test_offline_dashboard_data_contains_analysis_and_model_results PASSED
tests/test_silver.py::test_clean_trips_removes_invalid_rows_and_adds_features PASSED
tests/test_traffic_streaming.py::test_generate_traffic_event_contains_required_fields PASSED
tests/test_traffic_streaming.py::test_classify_congestion_marks_severe_roads PASSED
```

## 使用方法

### 激活虚拟环境

**方式 1: 使用便捷脚本**
```powershell
.\activate.ps1
```

**方式 2: 手动激活**
```powershell
.\venv\Scripts\Activate.ps1
```

### 运行项目

激活虚拟环境后，可以运行以下命令：

**查看离线分析结果**
```powershell
python scripts/export_offline_dashboard.py
python -m http.server 8088 --directory frontend/public
# 浏览器访问: http://localhost:8088/offline.html
```

**启动实时流控（需要 Docker Desktop 运行）**
```powershell
.\scripts\start_realtime_stack.ps1
python scripts/produce_traffic_events.py --events-per-second 60
# 浏览器访问: http://localhost:8080
```

**运行测试**
```powershell
python -m pytest tests/ -v
```

**重新运行完整 Spark 流程**
```powershell
.\scripts\run_official_spark_all_docker.ps1
```

## 与 Conda 版本的区别

| 项目 | Conda 版本 | venv 版本 |
|------|-----------|----------|
| 环境管理 | `conda env create -f environment.yml` | `python -m venv venv` |
| 激活命令 | `conda activate traffic-bigdata` | `.\venv\Scripts\Activate.ps1` |
| 依赖安装 | Conda channels + pip | 纯 pip |
| 运行命令 | `conda run --no-capture-output -n traffic-bigdata python ...` | 激活后直接 `python ...` |

## 注意事项

1. **虚拟环境不要提交到 Git**: `venv/` 目录已在 `.gitignore` 中
2. **Docker Desktop 必须运行**: 实时流控功能需要 Docker
3. **端口占用**: 确保 8080, 8081, 8000, 19092 端口未被占用
4. **首次运行 Spark**: 会下载 Docker 镜像，需要较长时间

## 故障排除

### 虚拟环境激活失败
```powershell
# 如果提示执行策略错误，运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 依赖安装失败
```powershell
# 清理并重新安装
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Docker 相关问题
- 确保 Docker Desktop 左下角显示 "Engine running"
- 运行 `docker --version` 和 `docker compose version` 验证
- 如果容器启动失败，先运行 `.\scripts\stop_realtime_stack.ps1` 清理

## 环境配置完成

✅ Python 虚拟环境已创建并激活
✅ 所有 Python 依赖已安装
✅ 前端依赖已安装
✅ Docker 环境已验证
✅ 单元测试全部通过

项目已准备就绪，可以开始使用！
