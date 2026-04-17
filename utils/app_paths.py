"""应用路径工具。"""

from __future__ import annotations

import os
from pathlib import Path


def get_project_root() -> Path:
    """返回项目根目录。"""
    return Path(__file__).resolve().parent.parent


def get_log_dir() -> Path:
    """返回日志目录，支持通过环境变量覆盖。"""
    custom_dir = os.getenv("STOCK_CAPTURE_LOG_DIR")
    if custom_dir:
        return Path(custom_dir)
    return get_project_root() / "runtime" / "logs"

