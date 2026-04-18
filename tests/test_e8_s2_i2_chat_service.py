"""E8-S2-I2 对话服务封装测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from db.database import DatabaseBootstrap
from services.chat_service import ChatService
from services.config_service import AIModelPayload, AIProviderPayload, ConfigService
from services.errors import ServiceError


@pytest.fixture
def chat_service(tmp_path: Path) -> ChatService:
    """创建隔离数据库下的对话服务实例。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    config_service = ConfigService(db_path)
    provider_id = config_service.create_provider(
        AIProviderPayload(
            name="OpenAI-Compatible",
            api_base_url="https://api.example.com/v1",
            api_key="sk-test",
            is_enabled=True,
            is_default=True,
        )
    )
    config_service.create_model(
        provider_id,
        AIModelPayload(model_code="gpt-test", model_name="测试模型", is_enabled=True, is_default=True),
    )
    return ChatService(config_service=config_service)


def test_ft_e8_s2_i2_01_对话发送成功(chat_service: ChatService, monkeypatch: pytest.MonkeyPatch) -> None:
    """功能测试：对话请求成功返回助手文本。"""

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "你好，我是AI助手"}}]}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        assert url == "https://api.example.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer sk-test"
        assert json["model"] == "gpt-test"
        assert json["messages"][0]["role"] == "system"
        assert timeout == 60.0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    content = chat_service.run_chat(
        messages=[
            {"role": "system", "content": "你是复盘助手"},
            {"role": "user", "content": "请总结今日市场情绪"},
        ]
    )
    assert content == "你好，我是AI助手"


def test_bt_e8_s2_i2_01_空消息列表返回chat_003(chat_service: ChatService) -> None:
    """边界测试：空消息列表时返回 CHAT_003。"""
    with pytest.raises(ServiceError, match="CHAT_003"):
        chat_service.run_chat(messages=[])


def test_ft_e8_s2_i2_03_含图片消息按多模态格式发送(
    chat_service: ChatService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：当消息包含图片片段时按 OpenAI 多模态格式透传。"""

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": "图片分析完成"}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        assert url == "https://api.example.com/v1/chat/completions"
        assert timeout == 60.0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    content = chat_service.run_chat(
        messages=[
            {"role": "system", "content": "你是复盘助手"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请结合图片分析"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
                ],
            },
        ]
    )

    assert content == "图片分析完成"
    assert isinstance(captured_payload.get("messages", [])[1]["content"], list)
    assert captured_payload["messages"][1]["content"][1]["type"] == "image_url"
