"""E4-S2-I1 AI 服务测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from db.database import DatabaseBootstrap
from services.ai_service import AIService
from services.config_service import AIModelPayload, AIProviderPayload, ConfigService
from services.errors import ServiceError


@pytest.fixture
def ai_service(tmp_path: Path) -> AIService:
    """创建隔离数据库下的 AI 服务实例。"""
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
    return AIService(config_service=config_service)


def test_ft_e4_s2_i1_01_ai成功返回内容(
    ai_service: AIService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：AI 成功返回 content。"""

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        assert url == "https://api.example.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer sk-test"
        assert json["model"] == "gpt-test"
        assert timeout == 60.0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    content = ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    assert content == '{"ok": true}'
    assert ai_service.last_raw_response is not None


def test_bt_e4_s2_i1_01_choices为空映射ai_003(
    ai_service: AIService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：choices 为空时返回 AI_003。"""

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": []}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(ServiceError, match="AI_003"):
        ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")


def test_ai认证失败映射ai_002(ai_service: AIService, monkeypatch: pytest.MonkeyPatch) -> None:
    """认证失败时返回 AI_002。"""

    class FakeResponse:
        status_code = 401

        @staticmethod
        def json() -> dict:
            return {}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(ServiceError, match="AI_002"):
        ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")

