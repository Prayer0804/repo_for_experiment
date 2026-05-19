from __future__ import annotations

import pandas as pd

from src.silver.transform import clean_trips


def test_clean_trips_removes_invalid_rows_and_adds_features() -> None:
    df = pd.DataFrame(
        [
            {
                "vendor_id": 1,
                "pickup_datetime": "2024-01-01 08:00:00",
                "dropoff_datetime": "2024-01-01 08:20:00",
                "passenger_count": 1,
                "trip_distance": 3.2,
                "pickup_location_id": 1,
                "dropoff_location_id": 2,
                "payment_type": "cash",
                "fare_amount": 15.0,
                "tip_amount": 0.0,
                "total_amount": 18.0,
            },
            {
                "vendor_id": 1,
                "pickup_datetime": "2024-01-01 09:00:00",
                "dropoff_datetime": "2024-01-01 09:10:00",
                "passenger_count": 1,
                "trip_distance": -1.0,
                "pickup_location_id": 1,
                "dropoff_location_id": 2,
                "payment_type": "cash",
                "fare_amount": 10.0,
                "tip_amount": 0.0,
                "total_amount": 12.0,
            },
        ]
    )
    cleaned, report = clean_trips(
        df,
        {"max_duration_min": 360, "max_trip_distance": 80, "max_fare_amount": 400, "max_passenger_count": 8},
    )

    assert len(cleaned) == 1
    assert report["removed_rows"] == 1
    assert cleaned.iloc[0]["trip_duration_min"] == 20
    assert cleaned.iloc[0]["pickup_hour"] == 8
    assert cleaned.iloc[0]["od_pair"] == "zone_1_to_zone_2"
