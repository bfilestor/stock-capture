"""配置服务，负责业务类型与 AI 配置管理。"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from db.capture_type_dao import CaptureTypeDAO
from services.base_service import BaseService


class ConfigValidationError(ValueError):
    """配置校验失败异常。"""


@dataclass(slots=True)
class CaptureTypePayload:
    """业务类型写入载荷。"""

    name: str
    prompt_template: str
    description: str = ""
    is_enabled: bool = True


class ConfigService(BaseService):
    """配置服务。"""

    def __init__(self, db_path: Path) -> None:
        """初始化配置服务。"""
        super().__init__()
        self._capture_type_dao = CaptureTypeDAO(db_path)

    @staticmethod
    def _now_text() -> str:
        """返回当前时间字符串。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _validate_capture_type(self, payload: CaptureTypePayload) -> None:
        """校验业务类型输入。"""
        if not payload.name.strip():
            raise ConfigValidationError("业务类型名称不能为空")
        if not payload.prompt_template.strip():
            raise ConfigValidationError("PromptTemplate 不能为空")

    def list_capture_types(self) -> list[dict[str, Any]]:
        """查询全部业务类型。"""
        return self._capture_type_dao.list_all()

    def create_capture_type(self, payload: CaptureTypePayload) -> int:
        """创建业务类型。"""
        self._validate_capture_type(payload)
        now_text = self._now_text()
        try:
            return self._capture_type_dao.create(
                name=payload.name.strip(),
                description=payload.description.strip(),
                prompt_template=payload.prompt_template.strip(),
                is_enabled=1 if payload.is_enabled else 0,
                created_at=now_text,
                updated_at=now_text,
            )
        except sqlite3.IntegrityError as exc:
            self.logger.exception("新增业务类型失败，可能存在重名: %s", payload.name)
            raise ConfigValidationError(f"业务类型名称已存在: {payload.name}") from exc

    def update_capture_type(self, capture_type_id: int, payload: CaptureTypePayload) -> None:
        """更新业务类型。"""
        self._validate_capture_type(payload)
        try:
            row_count = self._capture_type_dao.update(
                capture_type_id=capture_type_id,
                name=payload.name.strip(),
                description=payload.description.strip(),
                prompt_template=payload.prompt_template.strip(),
                is_enabled=1 if payload.is_enabled else 0,
                updated_at=self._now_text(),
            )
            self.logger.debug("更新业务类型完成，id=%s，影响行数=%s", capture_type_id, row_count)
        except sqlite3.IntegrityError as exc:
            self.logger.exception("更新业务类型失败，可能存在重名: %s", payload.name)
            raise ConfigValidationError(f"业务类型名称已存在: {payload.name}") from exc

    def delete_capture_type(self, capture_type_id: int) -> None:
        """删除业务类型。"""
        row_count = self._capture_type_dao.delete(capture_type_id)
        self.logger.debug("删除业务类型完成，id=%s，影响行数=%s", capture_type_id, row_count)

