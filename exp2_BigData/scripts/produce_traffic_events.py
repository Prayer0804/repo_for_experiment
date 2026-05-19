from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

from kafka import KafkaProducer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.config import load_config
from src.streaming.traffic_event_generator import generate_traffic_event


def parse_args() -> argparse.Namespace:
    config = load_config()
    realtime = config["realtime"]
    parser = argparse.ArgumentParser(description="持续造交通事件流并写入 Kafka。")
    parser.add_argument("--bootstrap-server", default=realtime["kafka_bootstrap_host"], help="Kafka bootstrap server，例如 localhost:19092")
    parser.add_argument("--topic", default=realtime["traffic_events_topic"], help="交通事件 topic")
    parser.add_argument("--events-per-second", type=float, default=float(realtime["events_per_second"]), help="每秒写入事件数")
    parser.add_argument("--seed", type=int, default=int(realtime["producer_seed"]), help="随机种子")
    parser.add_argument("--max-events", type=int, default=0, help="最多发送事件数，0 表示持续发送")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_server,
        key_serializer=lambda value: value.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        linger_ms=20,
        retries=5,
    )
    interval = 1 / max(args.events_per_second, 0.1)
    sent = 0
    print(f"开始向 Kafka 写入交通事件: topic={args.topic}, bootstrap={args.bootstrap_server}, eps={args.events_per_second}")
    try:
        while args.max_events <= 0 or sent < args.max_events:
            sent += 1
            event = generate_traffic_event(sent, rng)
            producer.send(args.topic, key=event["road_id"], value=event)
            if sent % 100 == 0:
                producer.flush()
                print(f"已发送 {sent} 条事件，最新路段={event['road_name']}，速度={event['speed_kmh']} km/h，等级={event['congestion_level']}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("收到中断信号，准备停止生产者。")
    finally:
        producer.flush()
        producer.close()
        print(f"生产者已停止，总发送事件数: {sent}")


if __name__ == "__main__":
    main()
