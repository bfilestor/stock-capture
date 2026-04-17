"""配置服务，负责业务类型与 AI 配置管理。"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from db.ai_provider_dao import AIModelDAO, AIProviderDAO
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


@dataclass(slots=True)
class AIProviderPayload:
    """AI 供应商写入载荷。"""

    name: str
    api_base_url: str
    api_key: str
    is_enabled: bool = True
    is_default: bool = False


@dataclass(slots=True)
class AIModelPayload:
    """AI 模型写入载荷。"""

    model_code: str
    model_name: str
    is_enabled: bool = True
    is_default: bool = False


class ConfigService(BaseService):
    """配置服务。"""

    def __init__(self, db_path: Path) -> None:
        """初始化配置服务。"""
        super().__init__()
        self._capture_type_dao = CaptureTypeDAO(db_path)
        self._provider_dao = AIProviderDAO(db_path)
        self._model_dao = AIModelDAO(db_path)

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

    def _validate_provider(self, payload: AIProviderPayload) -> None:
        """校验供应商输入。"""
        if not payload.name.strip():
            raise ConfigValidationError("供应商名称不能为空")
        if not payload.api_base_url.strip():
            raise ConfigValidationError("API Base URL 不能为空")

    def _validate_model(self, payload: AIModelPayload) -> None:
        """校验模型输入。"""
        if not payload.model_code.strip():
            raise ConfigValidationError("模型标识不能为空")
        if not payload.model_name.strip():
            raise ConfigValidationError("模型名称不能为空")
        if payload.is_default and not payload.is_enabled:
            raise ConfigValidationError("禁用模型不可设为默认模型")

    def list_providers(self) -> list[dict[str, Any]]:
        """查询供应商列表。"""
        return self._provider_dao.list_all()

    def list_models(self, provider_id: int) -> list[dict[str, Any]]:
        """查询模型列表。"""
        return self._model_dao.list_by_provider(provider_id)

    def create_provider(self, payload: AIProviderPayload) -> int:
        """创建供应商。"""
        self._validate_provider(payload)
        provider_id = self._provider_dao.create(
            name=payload.name.strip(),
            api_base_url=payload.api_base_url.strip(),
            api_key=payload.api_key.strip(),
            is_enabled=1 if payload.is_enabled else 0,
            is_default=1 if payload.is_default else 0,
        )
        self.logger.debug("创建供应商成功，id=%s", provider_id)
        return provider_id

    def update_provider(self, provider_id: int, payload: AIProviderPayload) -> None:
        """更新供应商。"""
        self._validate_provider(payload)
        row_count = self._provider_dao.update(
            provider_id=provider_id,
            name=payload.name.strip(),
            api_base_url=payload.api_base_url.strip(),
            api_key=payload.api_key.strip(),
            is_enabled=1 if payload.is_enabled else 0,
            is_default=1 if payload.is_default else 0,
        )
        self.logger.debug("更新供应商完成，id=%s，影响行数=%s", provider_id, row_count)

    def delete_provider(self, provider_id: int) -> None:
        """删除供应商。"""
        row_count = self._provider_dao.delete(provider_id)
        self.logger.debug("删除供应商完成，id=%s，影响行数=%s", provider_id, row_count)

    def create_model(self, provider_id: int, payload: AIModelPayload) -> int:
        """创建模型。"""
        self._validate_model(payload)
        model_id = self._model_dao.create(
            provider_id=provider_id,
            model_code=payload.model_code.strip(),
            model_name=payload.model_name.strip(),
            is_enabled=1 if payload.is_enabled else 0,
            is_default=1 if payload.is_default else 0,
        )
        self.logger.debug("创建模型成功，id=%s, provider_id=%s", model_id, provider_id)
        return model_id

    def update_model(self, model_id: int, provider_id: int, payload: AIModelPayload) -> None:
        """更新模型。"""
        self._validate_model(payload)
        row_count = self._model_dao.update(
            model_id=model_id,
            provider_id=provider_id,
            model_code=payload.model_code.strip(),
            model_name=payload.model_name.strip(),
            is_enabled=1 if payload.is_enabled else 0,
            is_default=1 if payload.is_default else 0,
        )
        self.logger.debug("更新模型完成，id=%s，影响行数=%s", model_id, row_count)

    def delete_model(self, model_id: int) -> None:
        """删除模型。"""
        row_count = self._model_dao.delete(model_id)
        self.logger.debug("删除模型完成，id=%s，影响行数=%s", model_id, row_count)

    def set_default_model(self, model_id: int) -> None:
        """设置默认模型，并执行约束检查。"""
        model = self._model_dao.get_by_id(model_id)
        if model is None:
            raise ConfigValidationError(f"模型不存在: {model_id}")
        if int(model.get("is_enabled", 0)) != 1:
            raise ConfigValidationError("禁用模型不可设为默认模型")
        provider_id = int(model["provider_id"])
        self._model_dao.set_default(model_id=model_id, provider_id=provider_id)
        self.logger.debug("默认模型设置成功，model_id=%s, provider_id=%s", model_id, provider_id)
