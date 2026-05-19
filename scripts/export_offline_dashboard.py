from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.visualization_api.export_offline_dashboard import export_offline_dashboard_data


def main() -> None:
    outputs = export_offline_dashboard_data()
    print(f"离线结果大屏数据已导出: {outputs['offline_dashboard']}")


if __name__ == "__main__":
    main()
