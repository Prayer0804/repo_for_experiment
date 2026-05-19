from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import write_json
from src.common.spark import remove_output


COLUMN_MAPPING = {
    "vendorid": "vendor_id",
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "ratecodeid": "ratecode_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "pulocationid": "pickup_location_id",
    "dolocationid": "dropoff_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
}

PAYMENT_LABELS = {
    1: "credit_card",
    2: "cash",
    3: "no_charge",
    4: "dispute",
    5: "unknown",
    6: "voided_trip",
}


def normalize_column_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def build_bronze_spark(spark: SparkSession) -> Path:
    config = load_config()
    ensure_dirs(config)
    source = configured_path(config, "data", "official_file")
    if not source.exists():
        raise FileNotFoundError(f"官方 TLC 数据不存在，请先运行 scripts/download_tlc_data.py: {source}")

    raw = spark.read.parquet(str(source))
    normalized = raw
    for old_name in raw.columns:
        normalized = normalized.withColumnRenamed(old_name, normalize_column_name(old_name))

    bronze_path = configured_path(config, "data", "bronze_file")
    remove_output(bronze_path)
    normalized.write.mode("overwrite").parquet(str(bronze_path))

    missing_counts = {
        row["column"]: int(row["missing_count"])
        for row in normalized.select(
            F.explode(
                F.array(
                    *[
                        F.struct(F.lit(col).alias("column"), F.count(F.when(F.col(col).isNull(), col)).alias("missing_count"))
                        for col in normalized.columns
                    ]
                )
            ).alias("m")
        )
        .select("m.column", "m.missing_count")
        .collect()
    }
    report = {
        "source_type": "official_nyc_tlc_yellow_taxi",
        "source_path": str(source),
        "output_path": str(bronze_path),
        "rows": normalized.count(),
        "columns": len(normalized.columns),
        "field_names": normalized.columns,
        "missing_values": missing_counts,
    }
    write_json(project_path("outputs/reports/bronze_profile.json"), report)
    return bronze_path


def standardize_official_columns(df: DataFrame) -> DataFrame:
    selected = df
    for source, target in COLUMN_MAPPING.items():
        if source in selected.columns and source != target:
            selected = selected.withColumnRenamed(source, target)
    if "payment_type" in selected.columns:
        mapping_expr = F.create_map([x for pair in PAYMENT_LABELS.items() for x in (F.lit(pair[0]), F.lit(pair[1]))])
        selected = selected.withColumn("payment_type_label", mapping_expr.getItem(F.col("payment_type").cast("int")))
    else:
        selected = selected.withColumn("payment_type_label", F.lit("unknown"))
    return selected


def build_silver_spark(spark: SparkSession) -> Path:
    config = load_config()
    bronze_path = configured_path(config, "data", "bronze_file")
    quality = config["quality"]
    bronze = spark.read.parquet(str(bronze_path))
    df = standardize_official_columns(bronze)
    before_rows = df.count()

    enriched = (
        df.withColumn("pickup_datetime", F.to_timestamp("pickup_datetime"))
        .withColumn("dropoff_datetime", F.to_timestamp("dropoff_datetime"))
        .withColumn("passenger_count", F.col("passenger_count").cast("double"))
        .withColumn("trip_distance", F.col("trip_distance").cast("double"))
        .withColumn("fare_amount", F.col("fare_amount").cast("double"))
        .withColumn("total_amount", F.col("total_amount").cast("double"))
        .withColumn("tip_amount", F.col("tip_amount").cast("double"))
        .withColumn(
            "trip_duration_min",
            (F.unix_timestamp("dropoff_datetime") - F.unix_timestamp("pickup_datetime")) / F.lit(60.0),
        )
    )
    valid = enriched.filter(
        F.col("pickup_datetime").isNotNull()
        & F.col("dropoff_datetime").isNotNull()
        & (F.col("trip_duration_min") > 0)
        & (F.col("trip_duration_min") <= quality["max_duration_min"])
        & (F.col("trip_distance") > 0)
        & (F.col("trip_distance") <= quality["max_trip_distance"])
        & (F.col("fare_amount") > 0)
        & (F.col("fare_amount") <= quality["max_fare_amount"])
        & (F.col("passenger_count") > 0)
        & (F.col("passenger_count") <= quality["max_passenger_count"])
        & F.col("pickup_location_id").isNotNull()
        & F.col("dropoff_location_id").isNotNull()
    )
    silver = (
        valid.withColumn("pickup_date", F.to_date("pickup_datetime"))
        .withColumn("pickup_month", F.date_format("pickup_datetime", "yyyy-MM"))
        .withColumn("pickup_hour", F.hour("pickup_datetime"))
        .withColumn("pickup_weekday", ((F.dayofweek("pickup_datetime") + 5) % 7).cast("int"))
        .withColumn("is_weekend", F.when(F.col("pickup_weekday").isin(5, 6), F.lit(1)).otherwise(F.lit(0)))
        .withColumn("pickup_zone", F.concat(F.lit("zone_"), F.col("pickup_location_id").cast("int").cast("string")))
        .withColumn("dropoff_zone", F.concat(F.lit("zone_"), F.col("dropoff_location_id").cast("int").cast("string")))
        .withColumn("od_pair", F.concat_ws("_to_", F.col("pickup_zone"), F.col("dropoff_zone")))
        .withColumn("revenue", F.coalesce(F.col("total_amount"), F.col("fare_amount")))
        .withColumn("payment_type_label", F.coalesce(F.col("payment_type_label"), F.lit("unknown")))
    )
    after_rows = silver.count()
    silver_path = configured_path(config, "data", "silver_file")
    remove_output(silver_path)
    silver.write.mode("overwrite").parquet(str(silver_path))

    summary_rows = (
        silver.select("trip_distance", "fare_amount", "total_amount", "trip_duration_min", "passenger_count")
        .summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "max")
        .collect()
    )
    report = {
        "engine": "spark",
        "input_path": str(bronze_path),
        "output_path": str(silver_path),
        "before_rows": before_rows,
        "after_rows": after_rows,
        "removed_rows": before_rows - after_rows,
        "removal_rate": round((before_rows - after_rows) / before_rows, 6) if before_rows else 0,
        "columns": silver.columns,
        "numeric_summary": [row.asDict() for row in summary_rows],
    }
    write_json(project_path("outputs/reports/silver_quality_report.json"), report)
    return silver_path


def _write_table_outputs(df: DataFrame, parquet_path: Path, csv_path: Path, json_path: Path, json_limit: int = 500) -> None:
    remove_output(parquet_path)
    df.write.mode("overwrite").parquet(str(parquet_path))
    pdf = df.toPandas()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(csv_path, index=False)
    pdf.head(json_limit).to_json(json_path, orient="records", force_ascii=False, indent=2, date_format="iso")


def build_gold_spark(spark: SparkSession) -> dict[str, Path]:
    config = load_config()
    silver_path = configured_path(config, "data", "silver_file")
    df = spark.read.parquet(str(silver_path))
    gold_dir = project_path(config["paths"]["gold_dir"])

    hourly = (
        df.groupBy("pickup_hour")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("trip_distance"), 3).alias("avg_distance"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
            F.round(F.avg("trip_duration_min"), 3).alias("avg_duration_min"),
            F.round(F.sum("revenue"), 3).alias("revenue"),
        )
        .orderBy("pickup_hour")
    )
    daily = (
        df.groupBy("pickup_date")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("revenue"), 3).alias("revenue"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
        )
        .orderBy("pickup_date")
    )
    hotspots = (
        df.groupBy("pickup_zone")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("revenue"), 3).alias("revenue"),
            F.round(F.avg("trip_distance"), 3).alias("avg_distance"),
        )
        .orderBy(F.desc("trip_count"))
    )
    od_routes = (
        df.groupBy("od_pair")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
            F.round(F.avg("trip_duration_min"), 3).alias("avg_duration_min"),
        )
        .orderBy(F.desc("trip_count"))
    )
    payment = (
        df.groupBy("payment_type_label")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("revenue"), 3).alias("revenue"),
            F.round(F.avg("tip_amount"), 3).alias("avg_tip"),
        )
        .withColumnRenamed("payment_type_label", "payment_type")
        .orderBy(F.desc("trip_count"))
    )
    features = (
        df.groupBy("pickup_date", "pickup_hour", "pickup_weekday", "is_weekend", "pickup_zone")
        .agg(
            F.count("*").alias("demand"),
            F.round(F.avg("trip_distance"), 3).alias("avg_distance"),
            F.round(F.avg("fare_amount"), 3).alias("avg_fare"),
            F.round(F.avg("trip_duration_min"), 3).alias("avg_duration_min"),
        )
        .orderBy("pickup_date", "pickup_hour", "pickup_zone")
    )

    tables = {
        "hourly_metrics": hourly,
        "daily_metrics": daily,
        "pickup_hotspots": hotspots,
        "od_routes": od_routes,
        "payment_metrics": payment,
        "demand_features": features,
    }
    outputs: dict[str, Path] = {}
    manifest = {}
    for name, table in tables.items():
        parquet_path = gold_dir / f"{name}.parquet"
        csv_path = gold_dir / f"{name}.csv"
        json_path = gold_dir / f"{name}.json"
        _write_table_outputs(table, parquet_path, csv_path, json_path)
        outputs[name] = parquet_path
        manifest[name] = {"path": str(parquet_path), "rows": table.count(), "columns": table.columns}

    write_json(project_path("outputs/reports/gold_manifest.json"), manifest)
    return outputs


def write_official_metadata_summary() -> None:
    config = load_config()
    metadata_path = configured_path(config, "data", "official_metadata_file")
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        write_json(project_path("outputs/reports/official_tlc_metadata.json"), metadata)
