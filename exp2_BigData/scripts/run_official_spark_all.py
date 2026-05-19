from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.spark_pipeline.analysis import run_spark_analysis
from src.spark_pipeline.ml import train_spark_mllib_models
from src.spark_pipeline.warehouse import build_bronze_spark, build_gold_spark, build_silver_spark
from src.common.spark import create_spark
from src.visualization_api.export_dashboard import export_dashboard_data


def main() -> None:
    spark = create_spark("official-tlc-spark-pipeline")
    try:
        bronze_path = build_bronze_spark(spark)
        print(f"Spark Bronze 层已生成: {bronze_path}")
        silver_path = build_silver_spark(spark)
        print(f"Spark Silver 层已生成: {silver_path}")
        gold_outputs = build_gold_spark(spark)
        print(f"Spark Gold 表已生成: {len(gold_outputs)}")
        analysis_outputs = run_spark_analysis(spark)
        print(f"Spark 离线分析结果已生成: {len(analysis_outputs)}")
        model_outputs = train_spark_mllib_models(spark)
        print(f"Spark MLlib 模型已训练: {model_outputs['metrics']}")
        dashboard_outputs = export_dashboard_data()
        print(f"离线大屏数据已导出: {dashboard_outputs['dashboard']}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
