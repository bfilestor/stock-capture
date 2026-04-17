"""数据库初始化实现。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

from utils.logging_config import get_logger

SCHEMA_SQL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS capture_types (
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE,
      description TEXT,
      prompt_template TEXT,
      is_enabled INTEGER,
      created_at TEXT,
      updated_at TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_providers (
      id INTEGER PRIMARY KEY,
      name TEXT,
      api_base_url TEXT,
      api_key TEXT,
      is_enabled INTEGER,
      is_default INTEGER
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_models (
      id INTEGER PRIMARY KEY,
      provider_id INTEGER,
      model_code TEXT,
      model_name TEXT,
      is_enabled INTEGER,
      is_default INTEGER
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS analysis_results (
      id INTEGER PRIMARY KEY,
      result_date TEXT,
      capture_type_id INTEGER,
      image_path TEXT,
      ocr_text TEXT,
      ai_raw_response TEXT,
      final_json_text TEXT,
      created_at TEXT,
      updated_at TEXT,
      UNIQUE(result_date, capture_type_id)
    );
    """,
)


class DatabaseBootstrap:
    """数据库初始化器，负责建库与建表。"""

    def __init__(self, db_path: Path) -> None:
        """初始化数据库启动器。"""
        self._db_path = db_path
        self._logger = get_logger(__name__)
        self._logger.debug("DatabaseBootstrap 初始化完成，db_path=%s", db_path)

    @property
    def db_path(self) -> Path:
        """返回数据库文件路径。"""
        return self._db_path

    def _ensure_parent_dir(self) -> None:
        """确保数据库目录存在。"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger.debug("数据库目录已确认存在: %s", self._db_path.parent)

    def _connect(self) -> sqlite3.Connection:
        """创建数据库连接。"""
        self._logger.debug("创建 SQLite 连接: %s", self._db_path)
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def initialize_schema(self, statements: Sequence[str] = SCHEMA_SQL) -> None:
        """执行建表语句。"""
        self._ensure_parent_dir()
        with self._connect() as connection:
            for sql in statements:
                first_line = sql.strip().splitlines()[0]
                self._logger.debug("执行建表语句: %s", first_line)
                connection.execute(sql)
            connection.commit()
        self._logger.debug("数据库结构初始化完成")

    def initialize(self) -> None:
        """执行数据库初始化入口。"""
        self._logger.debug("DatabaseBootstrap.initialize() 开始执行")
        self.initialize_schema()
        self._logger.info("数据库初始化完成: %s", self._db_path)
