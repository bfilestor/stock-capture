"""结果处理服务。"""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

from services.base_service import BaseService
from services.errors import ServiceError


class ResultService(BaseService):
    """提供 JSON 格式化与合法性校验能力。"""

    def __init__(self) -> None:
        """初始化结果服务。"""
        super().__init__()

    def validate_json_text(self, json_text: str) -> dict[str, Any]:
        """校验 JSON 文本，要求为对象。"""
        content = json_text.strip()
        if not content:
            raise ServiceError("JSON_001", "JSON 内容不能为空")

        try:
            parsed = json.loads(content)
        except JSONDecodeError as exc:
            raise ServiceError(
                "JSON_001",
                f"JSON 解析失败，位置(line={exc.lineno}, col={exc.colno})",
            ) from exc

        if not isinstance(parsed, dict):
            raise ServiceError("JSON_001", "必须为对象JSON")
        return parsed

    def format_json_text(self, json_text: str) -> str:
        """格式化 JSON 文本并返回美化后的字符串。"""
        parsed = self.validate_json_text(json_text)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=False)
        self.logger.debug("JSON 格式化完成，长度=%s", len(formatted))
        return formatted

