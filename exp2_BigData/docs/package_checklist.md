# 压缩包交付清单

打包给组员前，建议保留项目根目录的完整结构。组员写 PPT、报告、截图和复现实验时，最容易缺的是 `data/`、`outputs/` 和 `frontend/public/data/`，不要删掉这些目录。

## 必须保留

- `README.md`
- `environment.yml`
- `requirements.txt`
- `docker-compose.realtime.yml`
- `config/`
- `data/`
- `docker/`
- `docs/`
- `flink/`
- `frontend/`
- `outputs/`
- `scripts/`
- `src/`
- `tests/`

## 可以不打包

- `.pytest_cache/`
- `__pycache__/`
- 临时浏览器缓存
- 本机 Conda 环境目录
- Docker Desktop 的本地镜像缓存

## 建议打包前验证

```powershell
conda run --no-capture-output -n traffic-bigdata pytest
conda run --no-capture-output -n traffic-bigdata python -m compileall scripts src tests
conda run --no-capture-output -n traffic-bigdata python scripts/validate_delivery.py
```

完整验收脚本 `scripts/validate_delivery.py` 需要实时 Docker 链路正在运行。如果只想验证离线结果，至少运行：

```powershell
conda run --no-capture-output -n traffic-bigdata python scripts/export_offline_dashboard.py
conda run --no-capture-output -n traffic-bigdata pytest tests/test_pipeline_outputs.py
```

## 推荐给组员的阅读顺序

1. `README.md`
2. `docs/setup_guide.md`
3. `docs/architecture.md`
4. `docs/data_pipeline.md`
5. `docs/analysis_report.md`
6. `docs/model_report.md`
7. `docs/realtime_report.md`
8. `docs/team_work_split.md`
9. `docs/final_delivery_checklist.md`

## Windows 打包命令

如果使用 PowerShell 打包，可以在项目上级目录执行：

```powershell
Compress-Archive -Path .\BigData -DestinationPath .\BigData-delivery.zip -Force
```

如果压缩包太大，可以先删除缓存目录：

```powershell
Remove-Item -Recurse -Force .\BigData\.pytest_cache -ErrorAction SilentlyContinue
Get-ChildItem .\BigData -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

不要删除 `data/`、`outputs/`、`frontend/public/data/`，否则组员无法直接打开离线结果大屏。
