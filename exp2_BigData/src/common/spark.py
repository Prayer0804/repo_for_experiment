from __future__ import annotations

import shutil
import os
from pathlib import Path

from pyspark.sql import SparkSession

from src.common.config import load_config, project_path


def create_spark(app_name: str | None = None) -> SparkSession:
    config = load_config()
    spark_config = config["spark"]
    hadoop_home = project_path("tools/hadoop")
    if (hadoop_home / "bin" / "winutils.exe").exists():
        os.environ.setdefault("HADOOP_HOME", str(hadoop_home))
        os.environ["PATH"] = f"{hadoop_home / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"
    builder = (
        SparkSession.builder.appName(app_name or spark_config["app_name"])
        .master(spark_config["master"])
        .config("spark.sql.shuffle.partitions", str(spark_config["shuffle_partitions"]))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.host", "127.0.0.1")
    )
    return builder.getOrCreate()


def remove_output(path: str | Path) -> None:
    target = project_path(path)
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
