from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported table format: {path}")


def write_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        df.to_parquet(path, index=False)
    elif suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".json":
        df.to_json(path, orient="records", force_ascii=False, indent=2, date_format="iso")
    else:
        raise ValueError(f"Unsupported table format: {path}")


def dataframe_profile(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_values": {col: int(value) for col, value in df.isna().sum().items()},
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
