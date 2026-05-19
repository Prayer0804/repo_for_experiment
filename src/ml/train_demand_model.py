from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.common.config import ensure_dirs, load_config, project_path
from src.common.io import read_table, write_json, write_table


def build_features(feature_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = feature_df.copy()
    df["pickup_zone"] = df["pickup_zone"].astype(str)
    x = df[["pickup_hour", "pickup_weekday", "is_weekend", "avg_distance", "avg_fare", "avg_duration_min", "pickup_zone"]]
    y = df["demand"].astype(float)
    return x, y


def evaluate_model(name: str, model: Pipeline | DummyRegressor, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    pred = model.predict(x_test)
    return {
        "model": name,
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
        "mae": round(float(mean_absolute_error(y_test, pred)), 4),
        "r2": round(float(r2_score(y_test, pred)), 4),
    }


def train_demand_models(input_path: Path | None = None) -> dict[str, Path]:
    config = load_config()
    ensure_dirs(config)
    feature_path = input_path or project_path("data/gold/demand_features.parquet")
    df = read_table(feature_path)
    x, y = build_features(df)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=config["project"]["seed"])

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train, y_train)

    numeric_features = ["pickup_hour", "pickup_weekday", "is_weekend", "avg_distance", "avg_fare", "avg_duration_min"]
    categorical_features = ["pickup_zone"]
    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    improved = Pipeline(
        steps=[
            ("preprocess", preprocess),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=120,
                    min_samples_leaf=2,
                    random_state=config["project"]["seed"],
                    n_jobs=-1,
                ),
            ),
        ]
    )
    improved.fit(x_train, y_train)

    baseline_metrics = evaluate_model("baseline_mean", baseline, x_test, y_test)
    improved_metrics = evaluate_model("random_forest", improved, x_test, y_test)
    predictions = x_test.copy()
    predictions["actual_demand"] = y_test.to_numpy()
    predictions["baseline_prediction"] = baseline.predict(x_test)
    predictions["improved_prediction"] = improved.predict(x_test)
    predictions = predictions.sort_values(["pickup_weekday", "pickup_hour", "pickup_zone"]).round(3)

    metrics_dir = project_path(config["paths"]["metrics_dir"])
    reports_dir = project_path(config["paths"]["reports_dir"])
    model_dir = metrics_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(baseline, model_dir / "baseline_demand_model.joblib")
    joblib.dump(improved, model_dir / "random_forest_demand_model.joblib")

    metrics = {
        "target": "hourly_zone_trip_demand",
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "metrics": [baseline_metrics, improved_metrics],
        "selected_model": "random_forest",
    }
    write_json(metrics_dir / "model_metrics.json", metrics)
    write_table(predictions, metrics_dir / "demand_predictions.csv")
    write_table(predictions.head(200), metrics_dir / "demand_predictions.json")
    write_json(reports_dir / "model_evaluation_report.json", metrics)
    return {
        "metrics": metrics_dir / "model_metrics.json",
        "predictions": metrics_dir / "demand_predictions.csv",
        "improved_model": model_dir / "random_forest_demand_model.joblib",
    }


if __name__ == "__main__":
    print(train_demand_models())
