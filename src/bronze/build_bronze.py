from __future__ import annotations

from pathlib import Path

from src.common.config import configured_path, ensure_dirs, load_config, project_path
from src.common.io import dataframe_profile, read_table, write_json, write_table


def normalize_columns(columns: list[str]) -> list[str]:
    return [c.strip().lower().replace(" ", "_") for c in columns]


def build_bronze(input_path: Path | None = None) -> Path:
    config = load_config()
    ensure_dirs(config)
    source_path = input_path or configured_path(config, "data", "raw_file")
    if not source_path.exists():
        sample_path = configured_path(config, "data", "mock_file")
        source_path = sample_path
    df = read_table(source_path)
    df.columns = normalize_columns(list(df.columns))
    bronze_path = configured_path(config, "data", "bronze_file")
    write_table(df, bronze_path)

    report = dataframe_profile(df)
    report["source_path"] = str(source_path)
    report["output_path"] = str(bronze_path)
    write_json(project_path("outputs/reports/bronze_profile.json"), report)
    return bronze_path


if __name__ == "__main__":
    print(build_bronze())
