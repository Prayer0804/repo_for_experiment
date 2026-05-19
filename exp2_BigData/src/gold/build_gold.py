from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import read_table, write_json, write_table


def build_gold(input_path: Path | None = None) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    silver_path = input_path or configured_path(config, "data", "silver_file")
    df = read_table(silver_path)
    gold_dir = project_path(config["paths"]["gold_dir"])

    hourly = (
        df.groupby("pickup_hour", as_index=False)
        .agg(
            trip_count=("vendor_id", "count"),
            avg_distance=("trip_distance", "mean"),
            avg_fare=("fare_amount", "mean"),
            avg_duration_min=("trip_duration_min", "mean"),
            revenue=("revenue", "sum"),
        )
        .round(3)
        .sort_values("pickup_hour")
    )
    daily = (
        df.groupby("pickup_date", as_index=False)
        .agg(trip_count=("vendor_id", "count"), revenue=("revenue", "sum"), avg_fare=("fare_amount", "mean"))
        .round(3)
        .sort_values("pickup_date")
    )
    hotspots = (
        df.groupby("pickup_zone", as_index=False)
        .agg(trip_count=("vendor_id", "count"), revenue=("revenue", "sum"), avg_distance=("trip_distance", "mean"))
        .round(3)
        .sort_values("trip_count", ascending=False)
    )
    od_routes = (
        df.groupby("od_pair", as_index=False)
        .agg(trip_count=("vendor_id", "count"), avg_fare=("fare_amount", "mean"), avg_duration_min=("trip_duration_min", "mean"))
        .round(3)
        .sort_values("trip_count", ascending=False)
    )
    payment = (
        df.groupby("payment_type", as_index=False)
        .agg(trip_count=("vendor_id", "count"), revenue=("revenue", "sum"), avg_tip=("tip_amount", "mean"))
        .round(3)
        .sort_values("trip_count", ascending=False)
    )
    feature_table = (
        df.groupby(["pickup_date", "pickup_hour", "pickup_zone"], as_index=False)
        .agg(
            demand=("vendor_id", "count"),
            avg_distance=("trip_distance", "mean"),
            avg_fare=("fare_amount", "mean"),
            avg_duration_min=("trip_duration_min", "mean"),
            weekend_share=("is_weekend", "mean"),
        )
        .round(3)
        .sort_values(["pickup_date", "pickup_hour", "pickup_zone"])
    )
    feature_table["pickup_weekday"] = pd.to_datetime(feature_table["pickup_date"]).dt.dayofweek
    feature_table["is_weekend"] = feature_table["pickup_weekday"].isin([5, 6]).astype(int)

    outputs = {
        "hourly_metrics": gold_dir / "hourly_metrics.parquet",
        "daily_metrics": gold_dir / "daily_metrics.parquet",
        "pickup_hotspots": gold_dir / "pickup_hotspots.parquet",
        "od_routes": gold_dir / "od_routes.parquet",
        "payment_metrics": gold_dir / "payment_metrics.parquet",
        "demand_features": gold_dir / "demand_features.parquet",
    }
    tables = {
        "hourly_metrics": hourly,
        "daily_metrics": daily,
        "pickup_hotspots": hotspots,
        "od_routes": od_routes,
        "payment_metrics": payment,
        "demand_features": feature_table,
    }
    for name, table in tables.items():
        write_table(table, outputs[name])
        write_table(table, gold_dir / f"{name}.csv")
        write_table(table.head(200), gold_dir / f"{name}.json")

    write_json(
        project_path("outputs/reports/gold_manifest.json"),
        {name: {"path": str(path), "rows": int(len(tables[name])), "columns": list(tables[name].columns)} for name, path in outputs.items()},
    )
    return outputs


if __name__ == "__main__":
    print(build_gold())
