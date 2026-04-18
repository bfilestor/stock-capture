"""AI 对话服务封装。"""

from __future__ import annotations

from typing import Any

import httpx

from services.base_service import BaseService
from services.config_service import ConfigService
from services.errors import ServiceError


class ChatService(BaseService):
    """封装 OpenAI 兼容对话请求。"""

    def __init__(self, config_service: ConfigService, timeout_seconds: float = 60.0) -> None:
        """初始化对话服务。"""
        super().__init__()
        self._config_service = config_service
        self._timeout_seconds = timeout_seconds
        self.last_raw_response: dict[str, Any] | None = None

    @staticmethod
    def _build_chat_url(base_url: str) -> str:
        """拼接 chat/completions 地址。"""
        normalized = base_url.rstrip("/")
        if normalized.endswith("/v1"):
            return f"{normalized}/chat/completions"
        return f"{normalized}/v1/chat/completions"

    @staticmethod
    def _validate_messages(messages: list[dict[str, Any]]) -> None:
        """校验消息体输入。"""
        if not messages:
            raise ServiceError("CHAT_003", "消息列表不能为空")
        for index, message in enumerate(messages):
            role = str(message.get("role", "")).strip()
            if role not in {"system", "user", "assistant"}:
                raise ServiceError("CHAT_003", f"消息角色非法(index={index})")

            content = message.get("content")
            if isinstance(content, str):
                if not content.strip():
                    raise ServiceError("CHAT_003", f"消息内容不能为空(index={index})")
                continue

            if isinstance(content, list):
                if not content:
                    raise ServiceError("CHAT_003", f"消息内容不能为空(index={index})")
                has_valid_part = False
                for part_index, part in enumerate(content):
                    if not isinstance(part, dict):
                        raise ServiceError("CHAT_003", f"消息片段结构非法(index={index}, part={part_index})")
                    part_type = str(part.get("type", "")).strip()
                    if part_type == "text":
                        text_value = str(part.get("text", "")).strip()
                        if text_value:
                            has_valid_part = True
                        continue
                    if part_type == "image_url":
                        image_url = part.get("image_url", {})
                        if not isinstance(image_url, dict):
                            raise ServiceError("CHAT_003", f"图片片段结构非法(index={index}, part={part_index})")
                        url_value = str(image_url.get("url", "")).strip()
                        if url_value:
                            has_valid_part = True
                            continue
                    raise ServiceError("CHAT_003", f"消息片段类型非法(index={index}, part={part_index})")
                if not has_valid_part:
                    raise ServiceError("CHAT_003", f"消息内容不能为空(index={index})")
                continue

            raise ServiceError("CHAT_003", f"消息内容结构非法(index={index})")

    @staticmethod
    def _strip_system_messages(messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        """剔除调用方传入的 system 消息，避免与服务层注入策略冲突。"""
        normalized_messages: list[dict[str, Any]] = []
        dropped_count = 0
        for message in messages:
            role = str(message.get("role", "")).strip()
            if role == "system":
                dropped_count += 1
                continue
            normalized_messages.append(message)
        return normalized_messages, dropped_count

    def _resolve_system_prompt(self, system_prompt: str | None) -> tuple[str, str]:
        """解析对话系统提示词来源。"""
        explicit_prompt = str(system_prompt or "").strip()
        if explicit_prompt:
            return explicit_prompt, "explicit"
        resolved = self._config_service.resolve_system_prompt(scene="chat")
        prompt_source = "global_or_default"
        if resolved == self._config_service.get_global_system_prompt():
            prompt_source = "global"
        elif resolved:
            prompt_source = "default"
        return resolved, prompt_source

    def run_chat(self, messages: list[dict[str, Any]], system_prompt: str | None = None) -> str:
        """执行 AI 对话请求并返回回复内容。"""
        self._validate_messages(messages)
        normalized_messages, dropped_system_count = self._strip_system_messages(messages)
        if not normalized_messages:
            raise ServiceError("CHAT_003", "消息列表不能为空")

        resolved_system_prompt, prompt_source = self._resolve_system_prompt(system_prompt)

        provider, model = self._config_service.resolve_active_provider_model()
        base_url = str(provider.get("api_base_url", "")).strip()
        api_key = str(provider.get("api_key", "")).strip()
        model_code = str(model.get("model_code", "")).strip()
        chat_url = self._build_chat_url(base_url)

        payload_messages = [
            {"role": "system", "content": resolved_system_prompt},
            *normalized_messages,
        ]
        payload = {"model": model_code, "messages": payload_messages}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        has_image_input = any(
            isinstance(msg.get("content"), list)
            and any(
                isinstance(part, dict) and str(part.get("type", "")).strip() == "image_url"
                for part in msg.get("content", [])
            )
            for msg in normalized_messages
        )
        self.logger.debug(
            "开始调用对话接口，url=%s, model=%s, message_count=%s, has_image_input=%s, "
            "system_prompt_source=%s, system_prompt_len=%s, dropped_system_count=%s",
            chat_url,
            model_code,
            len(payload_messages),
            has_image_input,
            prompt_source,
            len(resolved_system_prompt),
            dropped_system_count,
        )
        try:
            response = httpx.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=self._timeout_seconds,
            )
        except httpx.RequestError as exc:
            self.logger.exception("对话请求失败")
            raise ServiceError("CHAT_001", f"连接失败: {exc}") from exc

        if response.status_code in {401, 403}:
            self.logger.warning("对话认证失败，status=%s", response.status_code)
            raise ServiceError("CHAT_002", f"认证失败({response.status_code})")
        if response.status_code >= 400:
            self.logger.warning("对话请求状态码异常，status=%s", response.status_code)
            raise ServiceError("CHAT_001", f"请求失败({response.status_code})")

        try:
            raw_response = response.json()
        except Exception as exc:
            self.logger.exception("对话接口返回非JSON")
            raise ServiceError("CHAT_003", "响应解析失败") from exc

        choices = raw_response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ServiceError("CHAT_003", "返回结构异常：choices为空")

        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise ServiceError("CHAT_003", "返回结构异常：content为空")

        self.last_raw_response = raw_response
        self.logger.debug("对话请求成功，content_len=%s", len(content))
        return content
