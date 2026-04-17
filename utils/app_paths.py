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


def get_data_dir() -> Path:
    """返回数据目录，支持通过环境变量覆盖。"""
    custom_dir = os.getenv("STOCK_CAPTURE_DATA_DIR")
    if custom_dir:
        return Path(custom_dir)
    return get_project_root() / "runtime" / "data"


def get_db_path() -> Path:
    """返回 SQLite 数据库文件路径，支持通过环境变量覆盖。"""
    custom_path = os.getenv("STOCK_CAPTURE_DB_PATH")
    if custom_path:
        return Path(custom_path)
    return get_data_dir() / "stock_capture.db"
