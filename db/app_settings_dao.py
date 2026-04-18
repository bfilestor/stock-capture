"""应用级配置数据访问对象。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from db.base_dao import BaseDAO


class AppSettingsDAO(BaseDAO):
    """封装 app_settings 表读写能力。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 AppSettingsDAO。"""
        super().__init__(db_path)

    def get_by_key(self, setting_key: str) -> dict[str, Any] | None:
        """按配置键查询配置值。"""
        sql = """
        SELECT id, setting_key, setting_value, updated_at
        FROM app_settings
        WHERE setting_key = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (setting_key,)).fetchone()
            return dict(row) if row else None

    def upsert(self, setting_key: str, setting_value: str, updated_at: str) -> None:
        """按键执行配置写入或更新。"""
        sql = """
        INSERT INTO app_settings (setting_key, setting_value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET
          setting_value = excluded.setting_value,
          updated_at = excluded.updated_at
        """
        with self.transaction() as connection:
            connection.execute(sql, (setting_key, setting_value, updated_at))
            self._logger.debug("写入应用配置成功，setting_key=%s", setting_key)

