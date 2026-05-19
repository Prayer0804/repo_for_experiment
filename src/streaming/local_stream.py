from __future__ import annotations

from collections import deque
from pathlib import Path

import pandas as pd

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import read_table, write_json, write_table


def simulate_stream(input_path: Path | None = None, window_size: int = 120, max_events: int = 500) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    silver_path = input_path or configured_path(config, "data", "silver_file")
    df = read_table(silver_path).sort_values("pickup_datetime").head(max_events)

    window: deque[dict] = deque(maxlen=window_size)
    snapshots: list[dict] = []
    events: list[dict] = []
    for i, row in enumerate(df.to_dict(orient="records"), start=1):
        event = {
            "event_id": i,
            "pickup_datetime": str(row["pickup_datetime"]),
            "pickup_zone": row["pickup_zone"],
            "fare_amount": float(row["fare_amount"]),
            "trip_distance": float(row["trip_distance"]),
        }
        events.append(event)
        window.append(event)
        if i % 25 == 0 or i == len(df):
            window_df = pd.DataFrame(window)
            top_zone = window_df["pickup_zone"].value_counts().idxmax()
            snapshots.append(
                {
                    "event_id": i,
                    "window_size": int(len(window_df)),
                    "trip_count": int(len(window_df)),
                    "avg_fare": round(float(window_df["fare_amount"].mean()), 3),
                    "avg_distance": round(float(window_df["trip_distance"].mean()), 3),
                    "hotspot_zone": str(top_zone),
                }
            )

    out_dir = project_path("outputs/reports")
    events_path = out_dir / "stream_events.json"
    snapshots_path = out_dir / "stream_window_metrics.json"
    write_json(events_path, events)
    write_json(snapshots_path, snapshots)
    write_table(pd.DataFrame(snapshots), out_dir / "stream_window_metrics.csv")
    return {"events": events_path, "metrics": snapshots_path}


if __name__ == "__main__":
    print(simulate_stream())
