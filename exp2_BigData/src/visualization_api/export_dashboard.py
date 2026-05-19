from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from src.common.config import ensure_dirs, load_config, project_path
from src.common.io import read_table, write_json
from src.visualization_api.export_offline_dashboard import export_offline_dashboard_data


def _records(path: Path, limit: int | None = None) -> list[dict]:
    df = read_table(path)
    if limit:
        df = df.head(limit)
    return json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))


def export_dashboard_data() -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    target_dir = project_path(config["paths"]["frontend_data_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "hourly": _records(project_path("data/gold/hourly_metrics.parquet")),
        "daily": _records(project_path("data/gold/daily_metrics.parquet")),
        "hotspots": _records(project_path("data/gold/pickup_hotspots.parquet"), limit=15),
        "od_routes": _records(project_path("data/gold/od_routes.parquet"), limit=15),
        "payment": _records(project_path("data/gold/payment_metrics.parquet")),
        "predictions": _records(project_path("outputs/metrics/demand_predictions.csv"), limit=80),
    }
    dashboard_path = target_dir / "dashboard_data.json"
    write_json(dashboard_path, payload)

    for source in project_path("data/gold").glob("*.json"):
        shutil.copyfile(source, target_dir / source.name)
    outputs = {"dashboard": dashboard_path}
    outputs.update(export_offline_dashboard_data())
    return outputs


if __name__ == "__main__":
    print(export_dashboard_data())
