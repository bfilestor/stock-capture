"""应用路径工具。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """返回项目根目录。"""
    if bool(getattr(sys, "frozen", False)):
        # 打包后优先使用 exe 所在目录，避免路径落在临时解压目录。
        return Path(sys.executable).resolve().parent
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
    if bool(getattr(sys, "frozen", False)):
        # 打包运行时默认将数据库放在 exe 同目录，便于整包迁移。
        return Path(sys.executable).resolve().parent / "stock_capture.db"
    return get_data_dir() / "stock_capture.db"


def get_capture_temp_dir() -> Path:
    """返回临时截图目录。"""
    custom_dir = os.getenv("STOCK_CAPTURE_CAPTURE_DIR")
    if custom_dir:
        return Path(custom_dir)
    return get_project_root() / "runtime" / "captures"
