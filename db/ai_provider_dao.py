"""AI 供应商与模型数据访问对象。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from db.base_dao import BaseDAO


class AIProviderDAO(BaseDAO):
    """封装 ai_providers 表 CRUD。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 AIProviderDAO。"""
        super().__init__(db_path)

    def list_all(self) -> list[dict[str, Any]]:
        """查询全部供应商。"""
        sql = """
        SELECT id, name, api_base_url, api_key, is_enabled, is_default
        FROM ai_providers
        ORDER BY id ASC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql).fetchall()
            result = [dict(row) for row in rows]
            self._logger.debug("查询供应商完成，数量=%s", len(result))
            return result

    def get_by_id(self, provider_id: int) -> dict[str, Any] | None:
        """按ID查询供应商。"""
        sql = """
        SELECT id, name, api_base_url, api_key, is_enabled, is_default
        FROM ai_providers
        WHERE id = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (provider_id,)).fetchone()
            return dict(row) if row else None

    def list_enabled(self) -> list[dict[str, Any]]:
        """查询启用中的供应商。"""
        sql = """
        SELECT id, name, api_base_url, api_key, is_enabled, is_default
        FROM ai_providers
        WHERE is_enabled = 1
        ORDER BY is_default DESC, id ASC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def create(
        self,
        *,
        name: str,
        api_base_url: str,
        api_key: str,
        is_enabled: int,
        is_default: int,
    ) -> int:
        """创建供应商并返回主键。"""
        sql = """
        INSERT INTO ai_providers (name, api_base_url, api_key, is_enabled, is_default)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.transaction() as connection:
            if is_default == 1:
                connection.execute("UPDATE ai_providers SET is_default = 0")
            cursor = connection.execute(
                sql, (name, api_base_url, api_key, is_enabled, is_default)
            )
            provider_id = int(cursor.lastrowid)
            self._logger.debug("创建供应商成功，id=%s, name=%s", provider_id, name)
            return provider_id

    def update(
        self,
        *,
        provider_id: int,
        name: str,
        api_base_url: str,
        api_key: str,
        is_enabled: int,
        is_default: int,
    ) -> int:
        """更新供应商。"""
        sql = """
        UPDATE ai_providers
        SET name = ?, api_base_url = ?, api_key = ?, is_enabled = ?, is_default = ?
        WHERE id = ?
        """
        with self.transaction() as connection:
            if is_default == 1:
                connection.execute("UPDATE ai_providers SET is_default = 0 WHERE id != ?", (provider_id,))
            cursor = connection.execute(
                sql, (name, api_base_url, api_key, is_enabled, is_default, provider_id)
            )
            row_count = int(cursor.rowcount)
            self._logger.debug("更新供应商完成，id=%s，影响行数=%s", provider_id, row_count)
            return row_count

    def delete(self, provider_id: int) -> int:
        """删除供应商。"""
        sql = "DELETE FROM ai_providers WHERE id = ?"
        return self.execute_write(sql, (provider_id,))


class AIModelDAO(BaseDAO):
    """封装 ai_models 表 CRUD。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 AIModelDAO。"""
        super().__init__(db_path)

    def list_by_provider(self, provider_id: int) -> list[dict[str, Any]]:
        """按供应商查询模型列表。"""
        sql = """
        SELECT id, provider_id, model_code, model_name, is_enabled, is_default
        FROM ai_models
        WHERE provider_id = ?
        ORDER BY id ASC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql, (provider_id,)).fetchall()
            result = [dict(row) for row in rows]
            self._logger.debug("查询模型完成，provider_id=%s, 数量=%s", provider_id, len(result))
            return result

    def list_enabled_by_provider(self, provider_id: int) -> list[dict[str, Any]]:
        """查询指定供应商的启用模型。"""
        sql = """
        SELECT id, provider_id, model_code, model_name, is_enabled, is_default
        FROM ai_models
        WHERE provider_id = ? AND is_enabled = 1
        ORDER BY is_default DESC, id ASC
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql, (provider_id,)).fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, model_id: int) -> dict[str, Any] | None:
        """按ID查询模型。"""
        sql = """
        SELECT id, provider_id, model_code, model_name, is_enabled, is_default
        FROM ai_models
        WHERE id = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (model_id,)).fetchone()
            return dict(row) if row else None

    def create(
        self,
        *,
        provider_id: int,
        model_code: str,
        model_name: str,
        is_enabled: int,
        is_default: int,
    ) -> int:
        """创建模型。"""
        sql = """
        INSERT INTO ai_models (provider_id, model_code, model_name, is_enabled, is_default)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.transaction() as connection:
            if is_default == 1:
                connection.execute("UPDATE ai_models SET is_default = 0 WHERE provider_id = ?", (provider_id,))
            cursor = connection.execute(
                sql, (provider_id, model_code, model_name, is_enabled, is_default)
            )
            model_id = int(cursor.lastrowid)
            self._logger.debug(
                "创建模型成功，id=%s, provider_id=%s, model_code=%s", model_id, provider_id, model_code
            )
            return model_id

    def update(
        self,
        *,
        model_id: int,
        provider_id: int,
        model_code: str,
        model_name: str,
        is_enabled: int,
        is_default: int,
    ) -> int:
        """更新模型。"""
        sql = """
        UPDATE ai_models
        SET provider_id = ?, model_code = ?, model_name = ?, is_enabled = ?, is_default = ?
        WHERE id = ?
        """
        with self.transaction() as connection:
            if is_default == 1:
                connection.execute("UPDATE ai_models SET is_default = 0 WHERE provider_id = ?", (provider_id,))
            cursor = connection.execute(
                sql, (provider_id, model_code, model_name, is_enabled, is_default, model_id)
            )
            row_count = int(cursor.rowcount)
            self._logger.debug("更新模型完成，id=%s, 影响行数=%s", model_id, row_count)
            return row_count

    def set_default(self, model_id: int, provider_id: int) -> None:
        """设置默认模型。"""
        with self.transaction() as connection:
            connection.execute("UPDATE ai_models SET is_default = 0 WHERE provider_id = ?", (provider_id,))
            connection.execute(
                "UPDATE ai_models SET is_default = 1 WHERE id = ? AND provider_id = ?",
                (model_id, provider_id),
            )
            self._logger.debug("设置默认模型完成，model_id=%s, provider_id=%s", model_id, provider_id)

    def delete(self, model_id: int) -> int:
        """删除模型。"""
        sql = "DELETE FROM ai_models WHERE id = ?"
        return self.execute_write(sql, (model_id,))
