from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.config import configured_path, ensure_dirs, load_config, project_path


def official_tlc_url(taxi_type: str, year: int, month: int, base_url: str) -> str:
    return f"{base_url}/{taxi_type}_tripdata_{year}-{month:02d}.parquet"


def download_official_tlc(output_path: Path, url: str) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with temp_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    temp_path.replace(output_path)

    parquet_file = pq.ParquetFile(output_path)
    metadata = {
        "source_url": url,
        "local_path": str(output_path),
        "file_size_bytes": output_path.stat().st_size,
        "rows": parquet_file.metadata.num_rows,
        "row_groups": parquet_file.metadata.num_row_groups,
        "columns": parquet_file.schema.names,
    }
    return metadata


def main() -> None:
    config = load_config()
    ensure_dirs(config)
    official_path = configured_path(config, "data", "official_file")
    metadata_path = configured_path(config, "data", "official_metadata_file")
    url = official_tlc_url(
        config["download"]["taxi_type"],
        int(config["download"]["year"]),
        int(config["download"]["month"]),
        config["download"]["base_url"],
    )

    if official_path.exists() and official_path.stat().st_size > 0:
        parquet_file = pq.ParquetFile(official_path)
        metadata = {
            "source_url": url,
            "local_path": str(official_path),
            "file_size_bytes": official_path.stat().st_size,
            "rows": parquet_file.metadata.num_rows,
            "row_groups": parquet_file.metadata.num_row_groups,
            "columns": parquet_file.schema.names,
            "download_reused": True,
        }
    else:
        metadata = download_official_tlc(official_path, url)
        metadata["download_reused"] = False

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"官方 TLC 数据已就绪: {official_path}")
    print(f"来源 URL: {url}")
    print(f"文件大小: {metadata['file_size_bytes']} bytes")
    print(f"行数: {metadata['rows']}")
    print(f"字段数: {len(metadata['columns'])}")


if __name__ == "__main__":
    main()
