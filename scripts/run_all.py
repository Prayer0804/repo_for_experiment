from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.run_analysis import run_offline_analysis
from src.bronze.build_bronze import build_bronze
from src.common.config import configured_path, ensure_dirs, load_config
from src.data_ingestion.mock_data import generate_mock_tlc_data
from src.gold.build_gold import build_gold
from src.ml.train_demand_model import train_demand_models
from src.silver.transform import build_silver
from src.streaming.local_stream import simulate_stream
from src.visualization_api.export_dashboard import export_dashboard_data


def main() -> None:
    config = load_config()
    ensure_dirs(config)
    sample_path = configured_path(config, "data", "mock_file")
    raw_path = configured_path(config, "data", "raw_file")
    generate_mock_tlc_data(sample_path, config["project"]["sample_rows"], config["project"]["seed"])
    shutil.copyfile(sample_path, raw_path)
    print(f"数据已准备: {raw_path}")

    bronze_path = build_bronze(raw_path)
    print(f"Bronze 层已生成: {bronze_path}")
    silver_path = build_silver(bronze_path)
    print(f"Silver 层已生成: {silver_path}")
    gold_outputs = build_gold(silver_path)
    print(f"Gold 表已生成: {len(gold_outputs)}")
    analysis_outputs = run_offline_analysis(silver_path)
    print(f"离线分析结果已生成: {len(analysis_outputs)}")
    model_outputs = train_demand_models()
    print(f"模型已训练: {model_outputs['metrics']}")
    stream_outputs = simulate_stream(silver_path)
    print(f"实时流模拟结果已写入: {stream_outputs['metrics']}")
    dashboard_outputs = export_dashboard_data()
    print(f"大屏数据已导出: {dashboard_outputs['dashboard']}")


if __name__ == "__main__":
    main()
