from __future__ import annotations

import random
from datetime import datetime, timezone

from src.streaming.traffic_event_generator import classify_congestion, generate_traffic_event


def test_generate_traffic_event_contains_required_fields() -> None:
    event = generate_traffic_event(1, random.Random(20260509), datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc))
    expected = {
        "event_id",
        "event_time",
        "road_id",
        "road_name",
        "district",
        "speed_kmh",
        "vehicle_count",
        "occupancy",
        "travel_time_sec",
        "congestion_level",
        "lat",
        "lon",
    }
    assert expected.issubset(event)
    assert event["speed_kmh"] > 0
    assert 0 <= event["occupancy"] <= 1


def test_classify_congestion_marks_severe_roads() -> None:
    assert classify_congestion(8, 0.4) == "severe"
    assert classify_congestion(30, 0.9) == "severe"
    assert classify_congestion(18, 0.5) == "moderate"
    assert classify_congestion(50, 0.2) == "smooth"
