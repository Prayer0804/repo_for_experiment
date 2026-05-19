CREATE TABLE traffic_events (
  event_id STRING,
  event_time TIMESTAMP(3),
  road_id STRING,
  road_name STRING,
  district STRING,
  speed_kmh DOUBLE,
  vehicle_count INT,
  occupancy DOUBLE,
  travel_time_sec DOUBLE,
  congestion_level STRING,
  lat DOUBLE,
  lon DOUBLE,
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'traffic-events',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'flink-traffic-congestion',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.timestamp-format.standard' = 'SQL',
  'json.ignore-parse-errors' = 'true'
);

CREATE TABLE congestion_alerts (
  window_start TIMESTAMP(3),
  window_end TIMESTAMP(3),
  road_id STRING,
  road_name STRING,
  district STRING,
  vehicle_count BIGINT,
  avg_speed_kmh DOUBLE,
  avg_occupancy DOUBLE,
  avg_travel_time_sec DOUBLE,
  severe_event_count BIGINT,
  severity STRING,
  alert_text STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'congestion-alerts',
  'properties.bootstrap.servers' = 'kafka:9092',
  'format' = 'json',
  'json.timestamp-format.standard' = 'SQL'
);

INSERT INTO congestion_alerts
SELECT
  window_start,
  window_end,
  road_id,
  road_name,
  district,
  COUNT(*) AS vehicle_count,
  ROUND(AVG(speed_kmh), 2) AS avg_speed_kmh,
  ROUND(AVG(occupancy), 4) AS avg_occupancy,
  ROUND(AVG(travel_time_sec), 2) AS avg_travel_time_sec,
  SUM(CASE WHEN speed_kmh <= 12 OR congestion_level = 'severe' THEN 1 ELSE 0 END) AS severe_event_count,
  CASE
    WHEN AVG(speed_kmh) <= 12 OR AVG(occupancy) >= 0.88 THEN 'severe'
    WHEN AVG(speed_kmh) <= 20 OR AVG(occupancy) >= 0.75 THEN 'moderate'
    ELSE 'slow'
  END AS severity,
  CONCAT(
    road_name,
    ' 在 ',
    CAST(window_start AS STRING),
    ' 至 ',
    CAST(window_end AS STRING),
    ' 窗口内平均速度 ',
    CAST(ROUND(AVG(speed_kmh), 2) AS STRING),
    ' km/h'
  ) AS alert_text
FROM TABLE(
  HOP(TABLE traffic_events, DESCRIPTOR(event_time), INTERVAL '10' SECOND, INTERVAL '1' MINUTE)
)
GROUP BY window_start, window_end, road_id, road_name, district
HAVING AVG(speed_kmh) <= 25
   OR AVG(occupancy) >= 0.65
   OR SUM(CASE WHEN speed_kmh <= 12 OR congestion_level = 'severe' THEN 1 ELSE 0 END) >= 5;
