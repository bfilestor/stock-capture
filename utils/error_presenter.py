"""统一错误展示转换工具。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from services.errors import ServiceError


API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{6,}")


@dataclass(slots=True)
class ErrorView:
    """用于 UI 展示的错误对象。"""

    code: str
    message: str
    raw_message: str

    def to_dict(self) -> dict[str, str]:
        """转换为统一结构字典。"""
        return {"code": self.code, "message": self.message}

    def to_ui_text(self) -> str:
        """转换为 UI 文本。"""
        return f"[{self.code}] {self.message}"


def _sanitize_message(text: str) -> str:
    """脱敏异常消息中的 API Key。"""
    return API_KEY_PATTERN.sub("sk-***", text)


def to_error_view(exc: Exception, max_message_length: int = 120) -> ErrorView:
    """将异常转换为统一错误展示结构。"""
    if isinstance(exc, ServiceError):
        code = exc.code
        raw_message = exc.message
    else:
        code = "SYS_001"
        raw_message = str(exc)

    sanitized = _sanitize_message(raw_message)
    if len(sanitized) > max_message_length:
        sanitized = sanitized[: max_message_length - 3] + "..."

    return ErrorView(code=code, message=sanitized, raw_message=raw_message)

