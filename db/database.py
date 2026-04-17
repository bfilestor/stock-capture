"""数据库初始化占位实现。"""

from __future__ import annotations

from pathlib import Path

from utils.logging_config import get_logger


class DatabaseBootstrap:
    """数据库初始化器（E1-S2-I1 补齐建表逻辑）。"""

    def __init__(self, db_path: Path) -> None:
        """初始化数据库启动器。"""
        self._db_path = db_path
        self._logger = get_logger(__name__)
        self._logger.debug("DatabaseBootstrap 初始化完成，db_path=%s", db_path)

    def initialize(self) -> None:
        """预留数据库初始化入口。"""
        self._logger.debug("DatabaseBootstrap.initialize() 调用完成，当前为占位逻辑")

