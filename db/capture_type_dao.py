"""CaptureType 数据访问对象。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from db.base_dao import BaseDAO


class CaptureTypeDAO(BaseDAO):
    """封装 capture_types 表的 CRUD 能力。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 CaptureTypeDAO。"""
        super().__init__(db_path)

    def list_all(self) -> list[dict[str, Any]]:
        """查询全部业务类型，按更新时间倒序。"""
        sql = """
        SELECT id, name, description, prompt_template, is_enabled, created_at, updated_at
        FROM capture_types
        ORDER BY datetime(updated_at) DESC, id DESC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql).fetchall()
            result = [dict(row) for row in rows]
            self._logger.debug("查询业务类型完成，数量=%s", len(result))
            return result

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """按名称查询业务类型。"""
        sql = """
        SELECT id, name, description, prompt_template, is_enabled, created_at, updated_at
        FROM capture_types
        WHERE name = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (name,)).fetchone()
            if row is None:
                return None
            return dict(row)

    def list_enabled(self) -> list[dict[str, Any]]:
        """查询启用中的业务类型。"""
        sql = """
        SELECT id, name, description, prompt_template, is_enabled, created_at, updated_at
        FROM capture_types
        WHERE is_enabled = 1
        ORDER BY id ASC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, capture_type_id: int) -> dict[str, Any] | None:
        """按ID查询业务类型。"""
        sql = """
        SELECT id, name, description, prompt_template, is_enabled, created_at, updated_at
        FROM capture_types
        WHERE id = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (capture_type_id,)).fetchone()
            return dict(row) if row else None

    def create(
        self,
        *,
        name: str,
        description: str,
        prompt_template: str,
        is_enabled: int,
        created_at: str,
        updated_at: str,
    ) -> int:
        """创建业务类型并返回主键。"""
        sql = """
        INSERT INTO capture_types (name, description, prompt_template, is_enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.transaction() as connection:
            cursor = connection.execute(
                sql, (name, description, prompt_template, is_enabled, created_at, updated_at)
            )
            capture_type_id = int(cursor.lastrowid)
            self._logger.debug("创建业务类型成功，id=%s, name=%s", capture_type_id, name)
            return capture_type_id

    def update(
        self,
        *,
        capture_type_id: int,
        name: str,
        description: str,
        prompt_template: str,
        is_enabled: int,
        updated_at: str,
    ) -> int:
        """更新业务类型并返回影响行数。"""
        sql = """
        UPDATE capture_types
        SET name = ?, description = ?, prompt_template = ?, is_enabled = ?, updated_at = ?
        WHERE id = ?
        """
        return self.execute_write(
            sql, (name, description, prompt_template, is_enabled, updated_at, capture_type_id)
        )

    def delete(self, capture_type_id: int) -> int:
        """删除业务类型并返回影响行数。"""
        sql = "DELETE FROM capture_types WHERE id = ?"
        return self.execute_write(sql, (capture_type_id,))
