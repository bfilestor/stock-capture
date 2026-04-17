"""日志初始化配置。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TextIO

from utils.app_paths import get_log_dir

LOG_NAME = "stock_capture"
LOG_FILE_NAME = "stock_capture.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _reset_handlers(logger: logging.Logger) -> None:
    """重置旧 handler，避免重复输出。"""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def setup_logging(log_dir: Path | None = None, console_stream: TextIO | None = None) -> Path:
    """初始化日志系统，返回日志文件路径。"""
    resolved_log_dir = log_dir or get_log_dir()
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = resolved_log_dir / LOG_FILE_NAME
    formatter = logging.Formatter(LOG_FORMAT)

    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _reset_handlers(logger)

    # 控制台日志：便于开发期快速观察启动与故障信息。
    console_handler = logging.StreamHandler(console_stream or sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # 文件日志：便于排查线上/用户环境问题。
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.debug("日志初始化完成，log_dir=%s, file=%s", resolved_log_dir, log_file_path)
    return log_file_path


def get_logger(module_name: str | None = None) -> logging.Logger:
    """获取项目日志对象。"""
    if not module_name:
        return logging.getLogger(LOG_NAME)
    return logging.getLogger(f"{LOG_NAME}.{module_name}")

