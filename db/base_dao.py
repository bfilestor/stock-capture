"""DAO 基类。"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from utils.logging_config import get_logger


class BaseDAO:
    """数据访问基类，统一事务与异常处理口径。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 DAO。"""
        self._db_path = db_path
        self._logger = get_logger(self.__class__.__name__)
        self._logger.debug("BaseDAO 初始化完成，db_path=%s", db_path)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """提供事务上下文，异常时自动回滚。"""
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA foreign_keys = ON;")
        try:
            self._logger.debug("开启数据库事务")
            yield connection
            connection.commit()
            self._logger.debug("事务提交完成")
        except Exception:
            connection.rollback()
            self._logger.exception("事务执行失败，已回滚")
            raise
        finally:
            connection.close()

    def execute_write(self, sql: str, params: Sequence[object] = ()) -> int:
        """执行写操作并返回受影响行数。"""
        with self.transaction() as connection:
            cursor = connection.execute(sql, params)
            rowcount = cursor.rowcount
            self._logger.debug("写操作完成，影响行数=%s", rowcount)
            return rowcount

    def execute_query(self, sql: str, params: Sequence[object] = ()) -> list[tuple]:
        """执行查询并返回结果列表。"""
        with self.transaction() as connection:
            cursor = connection.execute(sql, params)
            rows = cursor.fetchall()
            self._logger.debug("查询完成，结果条数=%s", len(rows))
            return rows

