from __future__ import annotations

from pathlib import Path

from src.common.io import read_table


def test_core_outputs_exist_after_pipeline() -> None:
    expected = [
        Path("data/bronze/tlc_trips_bronze.parquet"),
        Path("data/silver/tlc_trips_silver.parquet"),
        Path("data/gold/hourly_metrics.parquet"),
        Path("data/gold/demand_features.parquet"),
        Path("outputs/metrics/model_metrics.json"),
        Path("frontend/public/data/dashboard_data.json"),
        Path("frontend/public/data/offline_dashboard_data.json"),
        Path("frontend/public/offline.html"),
    ]
    for path in expected:
        assert path.exists(), f"Missing output: {path}"
        assert path.stat().st_size > 0, f"Empty output: {path}"


def test_gold_schema_contains_expected_columns() -> None:
    hourly = read_table(Path("data/gold/hourly_metrics.parquet"))
    assert {"pickup_hour", "trip_count", "avg_distance", "avg_fare", "avg_duration_min"}.issubset(hourly.columns)
    features = read_table(Path("data/gold/demand_features.parquet"))
    assert {"pickup_date", "pickup_hour", "pickup_zone", "demand"}.issubset(features.columns)


def test_offline_dashboard_data_contains_analysis_and_model_results() -> None:
    import json

    payload = json.loads(Path("frontend/public/data/offline_dashboard_data.json").read_text(encoding="utf-8"))
    assert {"quality", "gold", "analysis", "model"}.issubset(payload)
    assert payload["gold"]["hourly"]
    assert payload["analysis"]["demand_pattern"]
    assert payload["analysis"]["peak_periods"]
    assert payload["analysis"]["od_rank"]
    assert payload["model"]["metrics"]["engine"] == "spark_mllib"
    assert payload["model"]["predictions"]

    models = {item["model"] for item in payload["model"]["metrics"]["metrics"]}
    assert {"linear_regression_baseline", "random_forest_regressor"}.issubset(models)
