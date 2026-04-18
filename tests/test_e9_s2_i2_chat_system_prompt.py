"""E9-S2-I2 对话链路 SystemPrompt 注入测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from db.database import DatabaseBootstrap
from services.chat_service import ChatService
from services.config_service import (
    AIModelPayload,
    AIProviderPayload,
    ConfigService,
    DEFAULT_CHAT_SYSTEM_PROMPT,
)


@pytest.fixture
def config_service(tmp_path: Path) -> ConfigService:
    """创建隔离数据库下的配置服务。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    service = ConfigService(db_path)
    provider_id = service.create_provider(
        AIProviderPayload(
            name="OpenAI-Compatible",
            api_base_url="https://api.example.com/v1",
            api_key="sk-test",
            is_enabled=True,
            is_default=True,
        )
    )
    service.create_model(
        provider_id,
        AIModelPayload(model_code="gpt-test", model_name="测试模型", is_enabled=True, is_default=True),
    )
    return service


@pytest.fixture
def chat_service(config_service: ConfigService) -> ChatService:
    """创建对话服务。"""
    return ChatService(config_service=config_service)


def test_ft_e9_s2_i2_01_对话命中全局system_prompt(
    config_service: ConfigService,
    chat_service: ChatService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """功能测试：纯文本对话优先命中全局 SystemPrompt。"""
    config_service.save_global_system_prompt("你是全局对话系统提示词")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        assert url == "https://api.example.com/v1/chat/completions"
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    chat_service.run_chat(messages=[{"role": "user", "content": "请总结今日行情"}])
    assert captured_payload["messages"][0]["role"] == "system"
    assert captured_payload["messages"][0]["content"] == "你是全局对话系统提示词"
    assert captured_payload["messages"][1]["role"] == "user"


def test_ft_e9_s2_i2_02_多模态对话命中全局system_prompt(
    config_service: ConfigService,
    chat_service: ChatService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """功能测试：含图多模态对话同样优先命中全局 SystemPrompt。"""
    config_service.save_global_system_prompt("你是全局多模态提示词")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        assert url == "https://api.example.com/v1/chat/completions"
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    chat_service.run_chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请结合图片分析"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
                ],
            }
        ]
    )
    assert captured_payload["messages"][0]["content"] == "你是全局多模态提示词"
    assert captured_payload["messages"][1]["role"] == "user"
    assert captured_payload["messages"][1]["content"][1]["type"] == "image_url"


def test_bt_e9_s2_i2_01_全局为空时回退默认system_prompt(
    chat_service: ChatService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：全局为空时回退内置默认提示词。"""

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    chat_service.run_chat(messages=[{"role": "user", "content": "你好"}])
    assert captured_payload["messages"][0]["content"] == DEFAULT_CHAT_SYSTEM_PROMPT


def test_bt_e9_s2_i2_02_运行中更新全局配置后立即生效(
    config_service: ConfigService,
    chat_service: ChatService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """边界测试：全局 SystemPrompt 修改后，后续请求应立即命中新值。"""
    config_service.save_global_system_prompt("全局提示词V1")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    captured_system_prompts: list[str] = []

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_system_prompts.append(str(json["messages"][0]["content"]))
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    chat_service.run_chat(
        messages=[
            {"role": "system", "content": "历史旧系统提示词"},
            {"role": "user", "content": "第一轮"},
        ]
    )

    config_service.save_global_system_prompt("全局提示词V2")
    chat_service.run_chat(
        messages=[
            {"role": "system", "content": "历史旧系统提示词"},
            {"role": "user", "content": "第二轮"},
        ]
    )

    assert captured_system_prompts == ["全局提示词V1", "全局提示词V2"]
