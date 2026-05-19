from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class RoadSegment:
    road_id: str
    road_name: str
    district: str
    base_speed_kmh: float
    capacity: int
    lat: float
    lon: float


ROAD_SEGMENTS = [
    RoadSegment("R001", "人民大道东段", "中心区", 42, 90, 31.231, 121.478),
    RoadSegment("R002", "人民大道西段", "中心区", 38, 75, 31.232, 121.464),
    RoadSegment("R003", "中环北向南", "北城区", 55, 120, 31.286, 121.439),
    RoadSegment("R004", "中环南向北", "南城区", 53, 120, 31.183, 121.432),
    RoadSegment("R005", "机场快速路进城", "东城区", 70, 150, 31.151, 121.681),
    RoadSegment("R006", "机场快速路出城", "东城区", 72, 150, 31.160, 121.699),
    RoadSegment("R007", "跨江大桥北口", "滨江区", 48, 85, 31.247, 121.503),
    RoadSegment("R008", "跨江大桥南口", "滨江区", 46, 85, 31.214, 121.506),
    RoadSegment("R009", "大学城主干路", "西城区", 40, 70, 31.291, 121.349),
    RoadSegment("R010", "会展中心环路", "新区", 35, 60, 31.197, 121.566),
]


def generate_traffic_event(index: int, rng: random.Random, now: datetime | None = None) -> dict:
    event_time = now or datetime.now(timezone.utc)
    segment = _pick_segment(index, rng)
    rush_factor = _rush_hour_factor(event_time)
    incident_factor = _incident_factor(index, segment)
    random_factor = rng.uniform(0.82, 1.12)
    speed = max(3.0, segment.base_speed_kmh * rush_factor * incident_factor * random_factor)
    vehicle_count = max(1, int(segment.capacity * (1.35 - min(speed / max(segment.base_speed_kmh, 1), 1.0)) * rng.uniform(0.55, 1.25)))
    occupancy = min(1.0, max(0.05, vehicle_count / segment.capacity))
    travel_time_sec = round(1000 / max(speed, 1) * 3.6, 2)
    congestion_level = classify_congestion(speed, occupancy)
    return {
        "event_id": f"evt-{event_time.strftime('%Y%m%d%H%M%S')}-{index:08d}",
        "event_time": event_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "road_id": segment.road_id,
        "road_name": segment.road_name,
        "district": segment.district,
        "speed_kmh": round(speed, 2),
        "vehicle_count": vehicle_count,
        "occupancy": round(occupancy, 4),
        "travel_time_sec": travel_time_sec,
        "congestion_level": congestion_level,
        "lat": segment.lat,
        "lon": segment.lon,
    }


def generate_events(seed: int, count: int, start_index: int = 1) -> Iterable[dict]:
    rng = random.Random(seed)
    for offset in range(count):
        yield generate_traffic_event(start_index + offset, rng)


def classify_congestion(speed_kmh: float, occupancy: float) -> str:
    if speed_kmh <= 12 or occupancy >= 0.88:
        return "severe"
    if speed_kmh <= 22 or occupancy >= 0.72:
        return "moderate"
    if speed_kmh <= 35 or occupancy >= 0.55:
        return "slow"
    return "smooth"


def _pick_segment(index: int, rng: random.Random) -> RoadSegment:
    if index % 17 in {0, 1, 2, 3}:
        return ROAD_SEGMENTS[6]
    if index % 29 in {0, 1, 2, 3, 4}:
        return ROAD_SEGMENTS[9]
    weights = [1.4, 1.3, 0.9, 0.9, 0.7, 0.7, 1.8, 1.5, 1.1, 1.6]
    return rng.choices(ROAD_SEGMENTS, weights=weights, k=1)[0]


def _rush_hour_factor(event_time: datetime) -> float:
    local_hour = (event_time.hour + 8) % 24
    morning_peak = math.exp(-((local_hour - 8) ** 2) / 7)
    evening_peak = math.exp(-((local_hour - 18) ** 2) / 8)
    return max(0.34, 1.0 - 0.42 * morning_peak - 0.48 * evening_peak)


def _incident_factor(index: int, segment: RoadSegment) -> float:
    if segment.road_id == "R007" and index % 140 < 55:
        return 0.24
    if segment.road_id == "R010" and index % 210 < 70:
        return 0.30
    if segment.road_id == "R002" and index % 260 < 50:
        return 0.38
    return 1.0
