from __future__ import annotations

import pandas as pd

from src.ml.train_demand_model import build_features


def test_build_features_splits_target_and_predictors() -> None:
    df = pd.DataFrame(
        {
            "pickup_hour": [8, 9],
            "pickup_weekday": [0, 0],
            "is_weekend": [0, 0],
            "avg_distance": [2.5, 3.1],
            "avg_fare": [12.0, 14.0],
            "avg_duration_min": [16.0, 18.0],
            "pickup_zone": ["zone_1", "zone_2"],
            "demand": [10, 15],
        }
    )
    x, y = build_features(df)
    assert "demand" not in x.columns
    assert list(y) == [10.0, 15.0]
    assert x["pickup_zone"].tolist() == ["zone_1", "zone_2"]
    assert all(isinstance(value, str) for value in x["pickup_zone"])
