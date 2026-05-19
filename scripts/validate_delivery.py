from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "environment.yml",
    "config/config.yaml",
    "scripts/download_tlc_data.py",
    "scripts/run_official_spark_all.py",
    "scripts/run_official_spark_all_docker.ps1",
    "scripts/produce_traffic_events.py",
    "scripts/start_realtime_stack.ps1",
    "frontend/public/index.html",
    "frontend/public/offline.html",
    "frontend/public/data/dashboard_data.json",
    "frontend/public/data/offline_dashboard_data.json",
    "data/raw/official/yellow_tripdata_2024-01.parquet",
    "data/bronze/tlc_trips_bronze.parquet",
    "data/silver/tlc_trips_silver.parquet",
    "data/gold/hourly_metrics.parquet",
    "data/gold/daily_metrics.parquet",
    "data/gold/pickup_hotspots.parquet",
    "data/gold/od_routes.parquet",
    "data/gold/payment_metrics.parquet",
    "data/gold/demand_features.parquet",
    "outputs/reports/official_tlc_metadata.json",
    "outputs/reports/bronze_profile.json",
    "outputs/reports/silver_quality_report.json",
    "outputs/reports/gold_manifest.json",
    "outputs/reports/analysis_demand_pattern.csv",
    "outputs/reports/analysis_peak_periods.csv",
    "outputs/reports/analysis_hotspots.csv",
    "outputs/reports/analysis_fare_distance.csv",
    "outputs/reports/analysis_time_features.csv",
    "outputs/reports/analysis_od_rank.csv",
    "outputs/metrics/model_metrics.json",
    "outputs/metrics/demand_predictions.csv",
    "outputs/metrics/spark_models/linear_regression_baseline",
    "outputs/metrics/spark_models/random_forest_regressor",
    "docs/architecture.md",
    "docs/data_pipeline.md",
    "docs/data_quality_report.md",
    "docs/analysis_report.md",
    "docs/model_report.md",
    "docs/package_checklist.md",
    "docs/realtime_report.md",
    "docs/setup_guide.md",
    "docs/team_work_split.md",
    "docs/final_delivery_checklist.md",
    "docker-compose.realtime.yml",
    "docker/spark-official/Dockerfile",
    "flink/sql/traffic_congestion.sql",
    "src/spark_pipeline/warehouse.py",
    "src/spark_pipeline/analysis.py",
    "src/spark_pipeline/ml.py",
    "src/visualization_api/realtime_api.py",
    "src/streaming/traffic_event_generator.py",
]


FORBIDDEN_PATTERNS = re.compile(r"TODO|NotImplemented|伪代码|占位实现|placeholder", re.IGNORECASE)
TEXT_GLOBS = ["*.md", "*.py", "*.yaml", "*.yml", "*.html", "*.json", "*.sql", "*.ps1", "Dockerfile"]
SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def fail(message: str) -> None:
    print(f"验收失败: {message}")
    sys.exit(1)


def assert_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.exists():
            fail(f"缺少文件或目录: {relative}")
        if path.is_file() and path.stat().st_size <= 0:
            fail(f"文件为空: {relative}")


def assert_official_data_and_warehouse() -> None:
    with (ROOT / "outputs/reports/official_tlc_metadata.json").open("r", encoding="utf-8") as f:
        official = json.load(f)
    if official.get("rows", 0) < 1_000_000:
        fail("官方 TLC 数据行数不足，不能用 mock 数据冒充")
    if "d37ci6vzurychx.cloudfront.net" not in official.get("source_url", ""):
        fail("官方 TLC 数据来源 URL 不正确")
    official_path = Path(official["local_path"])
    if not official_path.exists() or official_path.stat().st_size < 10_000_000:
        fail("官方 TLC Parquet 文件不存在或大小异常")

    with (ROOT / "outputs/reports/silver_quality_report.json").open("r", encoding="utf-8") as f:
        silver_report = json.load(f)
    if silver_report.get("engine") != "spark":
        fail("Silver 层不是 Spark 处理结果")
    if silver_report.get("after_rows", 0) < 1_000_000:
        fail("Silver 层行数不足，未跑官方完整月度数据")

    bronze = pd.read_parquet(ROOT / "data/bronze/tlc_trips_bronze.parquet")
    silver = pd.read_parquet(ROOT / "data/silver/tlc_trips_silver.parquet")
    demand_features = pd.read_parquet(ROOT / "data/gold/demand_features.parquet")
    if len(bronze) < 1_000_000:
        fail("Bronze 数据行数不足")
    if len(silver) < 1_000_000:
        fail("Silver 数据行数不足")
    if len(demand_features) < 10_000:
        fail("Spark ML 特征表行数不足")

    expected_silver_columns = {
        "pickup_datetime",
        "dropoff_datetime",
        "trip_duration_min",
        "pickup_hour",
        "pickup_weekday",
        "pickup_zone",
        "dropoff_zone",
        "od_pair",
        "payment_type_label",
    }
    missing = expected_silver_columns - set(silver.columns)
    if missing:
        fail(f"Silver 缺少字段: {sorted(missing)}")


def assert_analysis_outputs() -> None:
    expected = [
        "analysis_demand_pattern.csv",
        "analysis_peak_periods.csv",
        "analysis_hotspots.csv",
        "analysis_fare_distance.csv",
        "analysis_time_features.csv",
        "analysis_od_rank.csv",
    ]
    for name in expected:
        path = ROOT / "outputs/reports" / name
        if not path.exists() or path.stat().st_size <= 0:
            fail(f"分析输出缺失或为空: {name}")
    with (ROOT / "outputs/reports/analysis_summary.json").open("r", encoding="utf-8") as f:
        summary = json.load(f)
    if summary.get("engine") != "spark":
        fail("分析报告不是 Spark 输出")


def assert_model_metrics() -> None:
    metrics_path = ROOT / "outputs/metrics/model_metrics.json"
    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)
    if metrics.get("engine") != "spark_mllib":
        fail("模型不是 Spark MLlib 训练结果")
    models = {item["model"] for item in metrics.get("metrics", [])}
    if {"linear_regression_baseline", "random_forest_regressor"} - models:
        fail("模型指标缺少 Spark 基线模型或随机森林模型")
    for item in metrics["metrics"]:
        for key in ["rmse", "mae", "r2"]:
            if key not in item:
                fail(f"模型指标缺少 {key}")


def assert_dashboard_data() -> None:
    path = ROOT / "frontend/public/data/dashboard_data.json"
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    required = {"hourly", "daily", "hotspots", "od_routes", "payment", "predictions"}
    missing = required - set(payload)
    if missing:
        fail(f"离线大屏数据缺少模块: {sorted(missing)}")
    for key in required:
        if not payload[key]:
            fail(f"离线大屏数据模块为空: {key}")

    offline_path = ROOT / "frontend/public/data/offline_dashboard_data.json"
    with offline_path.open("r", encoding="utf-8") as f:
        offline = json.load(f)
    required_sections = {"quality", "gold", "analysis", "model"}
    missing_sections = required_sections - set(offline)
    if missing_sections:
        fail(f"离线结果大屏数据缺少模块: {sorted(missing_sections)}")
    if not offline["analysis"].get("demand_pattern") or not offline["analysis"].get("od_rank"):
        fail("离线结果大屏缺少分析结果")
    if offline["model"].get("metrics", {}).get("engine") != "spark_mllib":
        fail("离线结果大屏缺少 Spark MLlib 模型指标")
    if not offline["model"].get("predictions"):
        fail("离线结果大屏缺少机器学习预测明细")


def assert_realtime_stack() -> None:
    jobs = _read_json_url("http://localhost:8081/jobs")
    statuses = {job["status"] for job in jobs.get("jobs", [])}
    if "RUNNING" not in statuses:
        fail("Flink 作业不是 RUNNING 状态")

    health = _read_json_url("http://localhost:8000/api/health")
    if health.get("topic") != "congestion-alerts":
        fail("实时 API 未消费正式 congestion-alerts topic")

    alerts = _read_json_url("http://localhost:8000/api/congestion/latest")
    if not alerts.get("alerts"):
        fail("实时 API 没有返回 Flink 拥堵告警")
    first = alerts["alerts"][0]
    for key in ["road_id", "road_name", "severity", "avg_speed_kmh", "window_start", "window_end"]:
        if key not in first:
            fail(f"实时告警缺少字段: {key}")

    topics = subprocess.check_output(
        [
            "docker",
            "exec",
            "traffic-kafka",
            "/opt/kafka/bin/kafka-topics.sh",
            "--bootstrap-server",
            "localhost:9092",
            "--list",
        ],
        text=True,
        encoding="utf-8",
    )
    if "traffic-events" not in topics or "congestion-alerts" not in topics:
        fail("Kafka 缺少正式输入或输出 topic")


def _read_json_url(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_no_unfinished_markers() -> None:
    for pattern in TEXT_GLOBS:
        for path in ROOT.rglob(pattern):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            relative = path.relative_to(ROOT)
            if relative in {Path("scripts/validate_delivery.py"), Path("AGENTS.md")}:
                continue
            if relative.parts[0] in {"data", "outputs"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if FORBIDDEN_PATTERNS.search(text):
                fail(f"发现未完成标记: {relative}")


def main() -> None:
    assert_required_files()
    assert_official_data_and_warehouse()
    assert_analysis_outputs()
    assert_model_metrics()
    assert_dashboard_data()
    assert_realtime_stack()
    assert_no_unfinished_markers()
    print("交付验收通过: 官方 TLC 数据、Spark 数仓、Spark MLlib、Kafka/Flink 实时链路、实时 API 和大屏均已验证。")


if __name__ == "__main__":
    main()
