from __future__ import annotations

import shutil
from pathlib import Path

from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.ml.regression import LinearRegression, RandomForestRegressor
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.common.config import ensure_dirs, load_config, project_path
from src.common.io import write_json
from src.common.spark import remove_output


def _metrics(predictions, prediction_col: str) -> dict:
    rmse = RegressionEvaluator(labelCol="demand", predictionCol=prediction_col, metricName="rmse").evaluate(predictions)
    mae = RegressionEvaluator(labelCol="demand", predictionCol=prediction_col, metricName="mae").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="demand", predictionCol=prediction_col, metricName="r2").evaluate(predictions)
    return {"rmse": round(float(rmse), 4), "mae": round(float(mae), 4), "r2": round(float(r2), 4)}


def train_spark_mllib_models(spark: SparkSession) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    feature_path = project_path("data/gold/demand_features.parquet")
    df = spark.read.parquet(str(feature_path)).filter(F.col("demand").isNotNull())
    train, test = df.randomSplit([0.75, 0.25], seed=int(config["project"]["seed"]))

    indexer = StringIndexer(inputCol="pickup_zone", outputCol="pickup_zone_index", handleInvalid="keep")
    encoder = OneHotEncoder(inputCols=["pickup_zone_index"], outputCols=["pickup_zone_vec"])
    assembler = VectorAssembler(
        inputCols=[
            "pickup_hour",
            "pickup_weekday",
            "is_weekend",
            "avg_distance",
            "avg_fare",
            "avg_duration_min",
            "pickup_zone_vec",
        ],
        outputCol="features",
        handleInvalid="keep",
    )
    baseline = Pipeline(
        stages=[
            indexer,
            encoder,
            assembler,
            LinearRegression(featuresCol="features", labelCol="demand", predictionCol="baseline_prediction", maxIter=50),
        ]
    )
    improved = Pipeline(
        stages=[
            indexer,
            encoder,
            assembler,
            RandomForestRegressor(
                featuresCol="features",
                labelCol="demand",
                predictionCol="improved_prediction",
                numTrees=80,
                maxDepth=8,
                seed=int(config["project"]["seed"]),
            ),
        ]
    )
    baseline_model = baseline.fit(train)
    improved_model = improved.fit(train)
    baseline_predictions = baseline_model.transform(test)
    improved_predictions = improved_model.transform(test)
    metrics = {
        "engine": "spark_mllib",
        "target": "hourly_zone_trip_demand",
        "train_rows": train.count(),
        "test_rows": test.count(),
        "metrics": [
            {"model": "linear_regression_baseline", **_metrics(baseline_predictions, "baseline_prediction")},
            {"model": "random_forest_regressor", **_metrics(improved_predictions, "improved_prediction")},
        ],
        "selected_model": "random_forest_regressor",
    }

    metrics_dir = project_path(config["paths"]["metrics_dir"])
    model_dir = metrics_dir / "spark_models"
    baseline_dir = model_dir / "linear_regression_baseline"
    improved_dir = model_dir / "random_forest_regressor"
    remove_output(baseline_dir)
    remove_output(improved_dir)
    baseline_model.write().overwrite().save(str(baseline_dir))
    improved_model.write().overwrite().save(str(improved_dir))

    prediction_cols = [
        "pickup_date",
        "pickup_hour",
        "pickup_weekday",
        "pickup_zone",
        "demand",
        "improved_prediction",
    ]
    predictions = improved_predictions.select(*prediction_cols).orderBy("pickup_date", "pickup_hour", "pickup_zone")
    predictions_pdf = predictions.limit(5000).toPandas()
    metrics_dir.mkdir(parents=True, exist_ok=True)
    predictions_pdf.to_csv(metrics_dir / "demand_predictions.csv", index=False)
    predictions_pdf.head(500).to_json(metrics_dir / "demand_predictions.json", orient="records", force_ascii=False, indent=2, date_format="iso")
    write_json(metrics_dir / "model_metrics.json", metrics)
    write_json(project_path("outputs/reports/model_evaluation_report.json"), metrics)
    return {
        "metrics": metrics_dir / "model_metrics.json",
        "predictions": metrics_dir / "demand_predictions.csv",
        "baseline_model": baseline_dir,
        "improved_model": improved_dir,
    }
