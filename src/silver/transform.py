from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import dataframe_profile, read_table, write_json, write_table


REQUIRED_COLUMNS = {
    "pickup_datetime",
    "dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "pickup_location_id",
    "dropoff_location_id",
    "payment_type",
    "fare_amount",
    "total_amount",
}


def clean_trips(df: pd.DataFrame, quality: dict) -> tuple[pd.DataFrame, dict]:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    before = len(df)
    cleaned = df.copy()
    cleaned["pickup_datetime"] = pd.to_datetime(cleaned["pickup_datetime"], errors="coerce")
    cleaned["dropoff_datetime"] = pd.to_datetime(cleaned["dropoff_datetime"], errors="coerce")
    cleaned["trip_duration_min"] = (
        cleaned["dropoff_datetime"] - cleaned["pickup_datetime"]
    ).dt.total_seconds() / 60

    numeric_cols = ["passenger_count", "trip_distance", "fare_amount", "total_amount"]
    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    invalid_mask = (
        cleaned["pickup_datetime"].isna()
        | cleaned["dropoff_datetime"].isna()
        | cleaned["trip_duration_min"].isna()
        | (cleaned["trip_duration_min"] <= 0)
        | (cleaned["trip_duration_min"] > quality["max_duration_min"])
        | (cleaned["trip_distance"] <= 0)
        | (cleaned["trip_distance"] > quality["max_trip_distance"])
        | (cleaned["fare_amount"] <= 0)
        | (cleaned["fare_amount"] > quality["max_fare_amount"])
        | (cleaned["passenger_count"] <= 0)
        | (cleaned["passenger_count"] > quality["max_passenger_count"])
    )

    cleaned = cleaned.loc[~invalid_mask].copy()
    cleaned["pickup_date"] = cleaned["pickup_datetime"].dt.date.astype(str)
    cleaned["pickup_month"] = cleaned["pickup_datetime"].dt.to_period("M").astype(str)
    cleaned["pickup_hour"] = cleaned["pickup_datetime"].dt.hour
    cleaned["pickup_weekday"] = cleaned["pickup_datetime"].dt.dayofweek
    cleaned["is_weekend"] = cleaned["pickup_weekday"].isin([5, 6]).astype(int)
    cleaned["pickup_zone"] = cleaned["pickup_location_id"].astype(int).astype(str).radd("zone_")
    cleaned["dropoff_zone"] = cleaned["dropoff_location_id"].astype(int).astype(str).radd("zone_")
    cleaned["od_pair"] = cleaned["pickup_zone"] + "_to_" + cleaned["dropoff_zone"]
    cleaned["revenue"] = cleaned["total_amount"].fillna(cleaned["fare_amount"])

    report = {
        "before_rows": int(before),
        "after_rows": int(len(cleaned)),
        "removed_rows": int(invalid_mask.sum()),
        "removal_rate": round(float(invalid_mask.mean()), 4),
        "profile": dataframe_profile(cleaned),
        "numeric_summary": cleaned[
            ["trip_distance", "fare_amount", "total_amount", "trip_duration_min", "passenger_count"]
        ].describe().round(3).to_dict(),
    }
    return cleaned, report


def build_silver(input_path: Path | None = None) -> Path:
    config = load_config()
    ensure_dirs(config)
    bronze_path = input_path or configured_path(config, "data", "bronze_file")
    df = read_table(bronze_path)
    cleaned, report = clean_trips(df, config["quality"])
    silver_path = configured_path(config, "data", "silver_file")
    write_table(cleaned, silver_path)
    report["input_path"] = str(bronze_path)
    report["output_path"] = str(silver_path)
    write_json(project_path("outputs/reports/silver_quality_report.json"), report)
    return silver_path


if __name__ == "__main__":
    print(build_silver())
