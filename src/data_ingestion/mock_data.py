from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PAYMENT_TYPES = ["credit_card", "cash", "mobile", "dispute"]
ZONE_IDS = np.arange(1, 31)


def generate_mock_tlc_data(output_path: Path, rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = np.datetime64("2024-01-01T00:00:00")
    minute_offsets = rng.integers(0, 31 * 24 * 60, size=rows)
    pickup = start + minute_offsets.astype("timedelta64[m]")
    pickup_hour = pd.to_datetime(pickup).hour.to_numpy()

    peak_boost = np.where(((pickup_hour >= 7) & (pickup_hour <= 9)) | ((pickup_hour >= 17) & (pickup_hour <= 19)), 1.7, 1.0)
    distance = np.round(rng.gamma(shape=2.2, scale=2.1, size=rows) * peak_boost, 2)
    duration = np.maximum(3, distance * rng.uniform(3.0, 7.5, size=rows) + rng.normal(4, 3, size=rows))
    dropoff = pickup + duration.astype("timedelta64[m]")
    fare = np.round(3.0 + distance * rng.uniform(2.2, 4.3, size=rows) + duration * 0.35 + rng.normal(0, 2, size=rows), 2)
    tip = np.round(np.maximum(0, fare * rng.choice([0, 0.08, 0.15, 0.2], size=rows, p=[0.35, 0.25, 0.3, 0.1])), 2)

    pickup_zone = rng.choice(ZONE_IDS, size=rows, p=_zone_weights())
    dropoff_zone = np.where(rng.random(rows) < 0.18, pickup_zone, rng.choice(ZONE_IDS, size=rows, p=_zone_weights()))
    passenger_count = rng.choice([1, 2, 3, 4, 5, 6], size=rows, p=[0.58, 0.23, 0.08, 0.05, 0.04, 0.02])

    df = pd.DataFrame(
        {
            "vendor_id": rng.choice([1, 2], size=rows),
            "pickup_datetime": pd.to_datetime(pickup).astype(str),
            "dropoff_datetime": pd.to_datetime(dropoff).astype(str),
            "passenger_count": passenger_count,
            "trip_distance": distance,
            "pickup_location_id": pickup_zone,
            "dropoff_location_id": dropoff_zone,
            "payment_type": rng.choice(PAYMENT_TYPES, size=rows, p=[0.67, 0.23, 0.08, 0.02]),
            "fare_amount": fare,
            "tip_amount": tip,
            "total_amount": np.round(fare + tip + rng.uniform(1.0, 6.0, size=rows), 2),
        }
    )

    anomaly_count = max(12, rows // 120)
    idx = rng.choice(df.index, size=anomaly_count, replace=False)
    df.loc[idx[: anomaly_count // 4], "trip_distance"] = -1
    df.loc[idx[anomaly_count // 4 : anomaly_count // 2], "fare_amount"] = -5
    df.loc[idx[anomaly_count // 2 : 3 * anomaly_count // 4], "passenger_count"] = 12
    df.loc[idx[3 * anomaly_count // 4 :], "dropoff_datetime"] = df.loc[idx[3 * anomaly_count // 4 :], "pickup_datetime"]

    df.to_csv(output_path, index=False)
    return df


def _zone_weights() -> np.ndarray:
    weights = np.linspace(2.0, 0.6, len(ZONE_IDS))
    weights[:5] += 2.0
    weights[12:16] += 1.2
    return weights / weights.sum()
