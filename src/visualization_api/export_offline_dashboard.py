from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.common.config import ensure_dirs, load_config, project_path
from src.common.io import write_json


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_records(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    records = _read_json(path)
    if not isinstance(records, list):
        raise ValueError(f"Expected JSON records list: {path}")
    return records[:limit] if limit is not None else records


def export_offline_dashboard_data() -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    target_dir = project_path(config["paths"]["frontend_data_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "generated_from": {
            "gold_dir": "data/gold",
            "analysis_dir": "outputs/charts",
            "metrics_dir": "outputs/metrics",
            "reports_dir": "outputs/reports",
        },
        "quality": {
            "official_tlc": _read_json(project_path("outputs/reports/official_tlc_metadata.json")),
            "bronze_profile": _read_json(project_path("outputs/reports/bronze_profile.json")),
            "silver_quality": _read_json(project_path("outputs/reports/silver_quality_report.json")),
            "gold_manifest": _read_json(project_path("outputs/reports/gold_manifest.json")),
        },
        "gold": {
            "hourly": _read_records(project_path("data/gold/hourly_metrics.json")),
            "daily": _read_records(project_path("data/gold/daily_metrics.json")),
            "hotspots": _read_records(project_path("data/gold/pickup_hotspots.json"), 50),
            "od_routes": _read_records(project_path("data/gold/od_routes.json"), 50),
            "payment": _read_records(project_path("data/gold/payment_metrics.json")),
            "demand_features": _read_records(project_path("data/gold/demand_features.json"), 500),
        },
        "analysis": {
            "summary": _read_json(project_path("outputs/reports/analysis_summary.json")),
            "demand_pattern": _read_records(project_path("outputs/charts/demand_pattern.json")),
            "peak_periods": _read_records(project_path("outputs/charts/peak_periods.json")),
            "hotspots": _read_records(project_path("outputs/charts/hotspots.json"), 30),
            "fare_distance": _read_records(project_path("outputs/charts/fare_distance.json")),
            "time_features": _read_records(project_path("outputs/charts/time_features.json")),
            "od_rank": _read_records(project_path("outputs/charts/od_rank.json"), 50),
        },
        "model": {
            "metrics": _read_json(project_path("outputs/metrics/model_metrics.json")),
            "evaluation_report": _read_json(project_path("outputs/reports/model_evaluation_report.json")),
            "predictions": _read_records(project_path("outputs/metrics/demand_predictions.json"), 500),
        },
    }

    output_path = target_dir / "offline_dashboard_data.json"
    write_json(output_path, payload)
    return {"offline_dashboard": output_path}


if __name__ == "__main__":
    print(export_offline_dashboard_data())
