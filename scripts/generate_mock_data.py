from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.config import configured_path, ensure_dirs, load_config
from src.data_ingestion.mock_data import generate_mock_tlc_data


def main() -> None:
    config = load_config()
    ensure_dirs(config)
    output_path = configured_path(config, "data", "mock_file")
    df = generate_mock_tlc_data(output_path, config["project"]["sample_rows"], config["project"]["seed"])
    print(f"已生成 {len(df)} 行样例数据: {output_path}")


if __name__ == "__main__":
    main()
