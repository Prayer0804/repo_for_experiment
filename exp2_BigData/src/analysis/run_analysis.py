from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import read_table, write_json, write_table


def run_offline_analysis(input_path: Path | None = None) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    silver_path = input_path or configured_path(config, "data", "silver_file")
    df = read_table(silver_path)
    out_dir = project_path("outputs/reports")
    chart_dir = project_path("outputs/charts")

    demand_pattern = (
        df.groupby("pickup_hour", as_index=False)
        .agg(trip_count=("vendor_id", "count"), revenue=("revenue", "sum"), avg_duration_min=("trip_duration_min", "mean"))
        .round(3)
        .sort_values("pickup_hour")
    )
    peak = df.assign(
        period=pd.cut(
            df["pickup_hour"],
            bins=[-1, 5, 10, 15, 20, 23],
            labels=["late_night", "morning_peak", "midday", "evening_peak", "night"],
        )
    ).groupby("period", observed=True, as_index=False).agg(
        trip_count=("vendor_id", "count"),
        avg_fare=("fare_amount", "mean"),
        avg_duration_min=("trip_duration_min", "mean"),
    ).round(3)
    hotspots = (
        df.groupby("pickup_zone", as_index=False)
        .agg(trip_count=("vendor_id", "count"), avg_fare=("fare_amount", "mean"))
        .round(3)
        .sort_values("trip_count", ascending=False)
        .head(20)
    )
    fare_distance = (
        df.assign(distance_bucket=pd.cut(df["trip_distance"], bins=[0, 1, 3, 5, 10, 20, 100]))
        .groupby("distance_bucket", observed=True, as_index=False)
        .agg(trip_count=("vendor_id", "count"), avg_fare=("fare_amount", "mean"), avg_total=("total_amount", "mean"))
        .round(3)
    )
    time_features = (
        df.groupby(["pickup_weekday", "pickup_hour"], as_index=False)
        .agg(trip_count=("vendor_id", "count"), avg_fare=("fare_amount", "mean"))
        .round(3)
    )
    od_rank = (
        df.groupby("od_pair", as_index=False)
        .agg(trip_count=("vendor_id", "count"), avg_fare=("fare_amount", "mean"))
        .round(3)
        .sort_values("trip_count", ascending=False)
        .head(30)
    )

    outputs = {
        "demand_pattern": out_dir / "analysis_demand_pattern.csv",
        "peak_periods": out_dir / "analysis_peak_periods.csv",
        "hotspots": out_dir / "analysis_hotspots.csv",
        "fare_distance": out_dir / "analysis_fare_distance.csv",
        "time_features": out_dir / "analysis_time_features.csv",
        "od_rank": out_dir / "analysis_od_rank.csv",
    }
    tables = {
        "demand_pattern": demand_pattern,
        "peak_periods": peak,
        "hotspots": hotspots,
        "fare_distance": fare_distance,
        "time_features": time_features,
        "od_rank": od_rank,
    }
    for name, table in tables.items():
        write_table(table, outputs[name])
        write_table(table, chart_dir / f"{name}.json")

    summary = {
        "top_hour": int(demand_pattern.sort_values("trip_count", ascending=False).iloc[0]["pickup_hour"]),
        "top_zone": str(hotspots.iloc[0]["pickup_zone"]),
        "top_od_pair": str(od_rank.iloc[0]["od_pair"]),
        "analysis_outputs": {name: str(path) for name, path in outputs.items()},
    }
    write_json(out_dir / "analysis_summary.json", summary)
    return outputs


if __name__ == "__main__":
    print(run_offline_analysis())
