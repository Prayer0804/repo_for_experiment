from __future__ import annotations

import json
import os
import threading
import time
import asyncio
from collections import deque
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer


BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:19092")
ALERT_TOPIC = os.getenv("CONGESTION_ALERT_TOPIC", "congestion-alerts")
MAX_ALERTS = int(os.getenv("MAX_ALERTS", "100"))
CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "").strip() or None
AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")

ROAD_LABELS = {
    "R001": ("人民大道东段", "中心区"),
    "R002": ("人民大道西段", "中心区"),
    "R003": ("中环北向南", "北城区"),
    "R004": ("中环南向北", "南城区"),
    "R005": ("机场快速路进城", "东城区"),
    "R006": ("机场快速路出城", "东城区"),
    "R007": ("跨江大桥北口", "滨江区"),
    "R008": ("跨江大桥南口", "滨江区"),
    "R009": ("大学城主干路", "西城区"),
    "R010": ("会展中心环路", "新区"),
}

app = FastAPI(title="实时交通拥堵大屏 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_alerts: deque[dict[str, Any]] = deque(maxlen=MAX_ALERTS)
alerts_lock = threading.Lock()
consumer_status: dict[str, Any] = {
    "running": False,
    "last_error": "",
    "last_message_ts": None,
    "messages_consumed": 0,
    "group_id": CONSUMER_GROUP,
    "auto_offset_reset": AUTO_OFFSET_RESET,
}


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=_consume_alerts_forever, daemon=True)
    thread.start()


@app.get("/api/health")
def health() -> dict[str, Any]:
    with alerts_lock:
        cached_alerts = len(latest_alerts)
    return {
        "status": "ok",
        "kafka_bootstrap_server": BOOTSTRAP_SERVER,
        "topic": ALERT_TOPIC,
        "consumer": consumer_status,
        "cached_alerts": cached_alerts,
    }


@app.get("/api/congestion/latest")
def latest() -> dict[str, Any]:
    with alerts_lock:
        alerts = [_normalize_alert(dict(item)) for item in latest_alerts]
    ranked = _rank_alerts(alerts)
    return {
        "alerts": ranked,
        "total_count": len(alerts),
        "updated_at": consumer_status["last_message_ts"],
    }


@app.websocket("/ws/congestion")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        last_seen = None
        while True:
            with alerts_lock:
                alerts = [_normalize_alert(dict(item)) for item in latest_alerts]
            current = consumer_status["last_message_ts"]
            if current != last_seen:
                await websocket.send_json(
                    {
                        "type": "snapshot",
                        "alerts": _rank_alerts(alerts),
                        "total_count": len(alerts),
                        "updated_at": current,
                    }
                )
                last_seen = current
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


def _consume_alerts_forever() -> None:
    while True:
        consumer: KafkaConsumer | None = None
        try:
            consumer = KafkaConsumer(
                ALERT_TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVER,
                group_id=CONSUMER_GROUP,
                auto_offset_reset=AUTO_OFFSET_RESET,
                enable_auto_commit=CONSUMER_GROUP is not None,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
            consumer_status.update({"running": True, "last_error": ""})
            for message in consumer:
                alert = _normalize_alert(message.value)
                with alerts_lock:
                    latest_alerts.appendleft(alert)
                consumer_status["last_message_ts"] = time.time()
                consumer_status["messages_consumed"] += 1
        except Exception as exc:
            consumer_status.update({"running": False, "last_error": str(exc)})
            time.sleep(3)
        finally:
            if consumer is not None:
                consumer.close()


def _rank_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        alerts,
        key=lambda item: (
            str(item.get("severity", "")) != "severe",
            float(item.get("avg_speed_kmh", 999)),
            -int(item.get("vehicle_count", 0)),
        ),
    )[:30]


def _normalize_alert(alert: dict[str, Any]) -> dict[str, Any]:
    road_id = str(alert.get("road_id", "")).strip()
    alert["road_id"] = road_id

    if "avg_speed_kmh" in alert and alert["avg_speed_kmh"] is not None:
        alert["avg_speed_kmh"] = round(float(alert["avg_speed_kmh"]), 2)
    if "avg_occupancy" in alert and alert["avg_occupancy"] is not None:
        alert["avg_occupancy"] = round(float(alert["avg_occupancy"]), 3)

    if road_id in ROAD_LABELS:
        road_name, district = ROAD_LABELS[road_id]
        alert["road_name"] = road_name
        alert["district"] = district
        alert["alert_text"] = (
            f"{road_name} 在 {alert.get('window_start')} 至 {alert.get('window_end')} "
            f"窗口内平均速度 {alert.get('avg_speed_kmh')} km/h，车辆数 {alert.get('vehicle_count')}"
        )
    return alert
