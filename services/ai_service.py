"""AI 服务封装。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from services.base_service import BaseService
from services.config_service import ConfigService
from services.errors import ServiceError


@dataclass(slots=True)
class AIRunResult:
    """AI 调用结果。"""

    content: str
    raw_response: dict[str, Any]
    provider_id: int
    model_code: str


class AIService(BaseService):
    """封装 OpenAI 兼容接口调用。"""

    def __init__(self, config_service: ConfigService, timeout_seconds: float = 60.0) -> None:
        """初始化 AI 服务。"""
        super().__init__()
        self._config_service = config_service
        self._timeout_seconds = timeout_seconds
        self.last_raw_response: dict[str, Any] | None = None

    @staticmethod
    def _build_messages(prompt: str, ocr_text: str) -> list[dict[str, str]]:
        """构建 OpenAI 兼容消息体。"""
        user_content = (
            f"请根据以下Prompt和OCR文本进行结构化提取。\n\n"
            f"Prompt:\n{prompt}\n\n"
            f"OCR文本:\n{ocr_text}"
        )
        return [
            {"role": "system", "content": "只返回JSON"},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _build_chat_url(base_url: str) -> str:
        """拼接 chat/completions 请求地址。"""
        normalized = base_url.rstrip("/")
        if normalized.endswith("/v1"):
            return f"{normalized}/chat/completions"
        return f"{normalized}/v1/chat/completions"

    def run_ai_with_meta(self, prompt: str, ocr_text: str) -> AIRunResult:
        """执行 AI 调用并返回完整元信息。"""
        if not prompt.strip():
            raise ServiceError("AI_003", "Prompt 不能为空")
        if not ocr_text.strip():
            raise ServiceError("AI_003", "OCR 文本不能为空")

        provider, model = self._config_service.resolve_active_provider_model()
        provider_id = int(provider["id"])
        base_url = str(provider.get("api_base_url", "")).strip()
        api_key = str(provider.get("api_key", "")).strip()
        model_code = str(model.get("model_code", "")).strip()
        chat_url = self._build_chat_url(base_url)

        payload = {
            "model": model_code,
            "messages": self._build_messages(prompt, ocr_text),
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.logger.debug(
            "开始调用 AI，provider_id=%s, model=%s, url=%s", provider_id, model_code, chat_url
        )
        try:
            response = httpx.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=self._timeout_seconds,
            )
        except httpx.RequestError as exc:
            self.logger.exception("AI 连接失败")
            raise ServiceError("AI_001", f"连接失败: {exc}") from exc

        if response.status_code in {401, 403}:
            self.logger.warning("AI 认证失败，status=%s", response.status_code)
            raise ServiceError("AI_002", f"认证失败({response.status_code})")
        if response.status_code >= 400:
            self.logger.warning("AI 返回异常状态码: %s", response.status_code)
            raise ServiceError("AI_001", f"请求失败({response.status_code})")

        try:
            raw_response = response.json()
        except Exception as exc:
            self.logger.exception("AI 返回非 JSON")
            raise ServiceError("AI_003", "响应解析失败") from exc

        choices = raw_response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ServiceError("AI_003", "返回结构异常：choices为空")

        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise ServiceError("AI_003", "返回结构异常：content为空")

        self.last_raw_response = raw_response
        self.logger.debug("AI 调用成功，返回文本长度=%s", len(content))
        return AIRunResult(
            content=content,
            raw_response=raw_response,
            provider_id=provider_id,
            model_code=model_code,
        )

    def run_ai(self, prompt: str, ocr_text: str) -> str:
        """执行 AI 调用并返回内容字符串。"""
        return self.run_ai_with_meta(prompt, ocr_text).content

