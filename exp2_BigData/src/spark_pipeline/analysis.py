from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import write_json


def _write_csv_json(df, csv_path: Path, json_path: Path, limit: int = 500) -> None:
    pdf = df.toPandas()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(csv_path, index=False)
    pdf.head(limit).to_json(json_path, orient="records", force_ascii=False, indent=2, date_format="iso")


def run_spark_analysis(spark: SparkSession) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    silver = spark.read.parquet(str(configured_path(config, "data", "silver_file")))
    reports = project_path(config["paths"]["reports_dir"])
    charts = project_path(config["paths"]["charts_dir"])

    demand_pattern = (
        silver.groupBy("pickup_hour")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("revenue"), 3).alias("revenue"),
            F.round(F.avg("trip_duration_min"), 3).alias("avg_duration_min"),
        )
        .orderBy("pickup_hour")
    )
    peak = (
        silver.withColumn(
            "period",
            F.when(F.col("pickup_hour").between(7, 9), "早高峰")
            .when(F.col("pickup_hour").between(17, 19), "晚高峰")
            .when(F.col("pickup_hour").between(0, 5), "夜间")
            .otherwise("平峰"),
        )
        .groupBy("period")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
            F.round(F.avg("trip_duration_min"), 3).alias("avg_duration_min"),
        )
        .orderBy(F.desc("trip_count"))
    )
    hotspots = (
        silver.groupBy("pickup_zone")
        .agg(F.count("*").alias("trip_count"), F.round(F.avg("fare_amount"), 3).alias("avg_fare"))
        .orderBy(F.desc("trip_count"))
        .limit(30)
    )
    fare_distance = (
        silver.withColumn(
            "distance_bucket",
            F.when(F.col("trip_distance") <= 1, "0-1")
            .when(F.col("trip_distance") <= 3, "1-3")
            .when(F.col("trip_distance") <= 5, "3-5")
            .when(F.col("trip_distance") <= 10, "5-10")
            .when(F.col("trip_distance") <= 20, "10-20")
            .otherwise("20+"),
        )
        .groupBy("distance_bucket")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
            F.round(F.avg("total_amount"), 3).alias("avg_total"),
        )
        .orderBy("distance_bucket")
    )
    time_features = (
        silver.groupBy("pickup_weekday", "pickup_hour")
        .agg(F.count("*").alias("trip_count"), F.round(F.avg("fare_amount"), 3).alias("avg_fare"))
        .orderBy("pickup_weekday", "pickup_hour")
    )
    od_rank = (
        silver.groupBy("od_pair")
        .agg(F.count("*").alias("trip_count"), F.round(F.avg("fare_amount"), 3).alias("avg_fare"))
        .orderBy(F.desc("trip_count"))
        .limit(50)
    )
    tables = {
        "demand_pattern": demand_pattern,
        "peak_periods": peak,
        "hotspots": hotspots,
        "fare_distance": fare_distance,
        "time_features": time_features,
        "od_rank": od_rank,
    }
    outputs = {}
    for name, table in tables.items():
        csv_path = reports / f"analysis_{name}.csv"
        json_path = charts / f"{name}.json"
        _write_csv_json(table, csv_path, json_path)
        outputs[name] = csv_path

    summary = {
        "engine": "spark",
        "top_hour": demand_pattern.orderBy(F.desc("trip_count")).first()["pickup_hour"],
        "top_zone": hotspots.first()["pickup_zone"],
        "top_od_pair": od_rank.first()["od_pair"],
        "analysis_outputs": {name: str(path) for name, path in outputs.items()},
    }
    write_json(reports / "analysis_summary.json", summary)
    return outputs
