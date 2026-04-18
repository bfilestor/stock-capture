"""E4-S2-I1 AI 服务测试。"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from db.database import DatabaseBootstrap
from services.ai_service import AIService
from services.config_service import AIModelPayload, AIProviderPayload, ConfigService
from services.errors import ServiceError


def _debug(message: str) -> None:
    """输出带时间与线程信息的调试日志。"""
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[E4-S2-I1][{now}][{threading.current_thread().name}] {message}", flush=True)


@pytest.fixture
def ai_service(tmp_path: Path) -> AIService:
    """创建隔离数据库下的 AI 服务实例。"""
    _debug(f"开始创建 ai_service fixture, tmp_path={tmp_path}")
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    _debug(f"数据库初始化完成, db_path={db_path}")
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
    _debug(f"创建 provider 完成, provider_id={provider_id}")
    config_service.create_model(
        provider_id,
        AIModelPayload(model_code="gpt-test", model_name="测试模型", is_enabled=True, is_default=True),
    )
    _debug("创建 model 完成, 返回 AIService 实例")
    return AIService(config_service=config_service)


def test_ft_e4_s2_i1_01_ai成功返回内容(
    ai_service: AIService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：AI 成功返回 content。"""
    _debug("test_ft_e4_s2_i1_01_ai成功返回内容 开始")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        _debug(
            "fake_post 被调用, "
            f"url={url}, timeout={timeout}, model={json.get('model')}, "
            f"messages_count={len(json.get('messages', []))}"
        )
        assert url == "https://api.example.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer sk-test"
        assert json["model"] == "gpt-test"
        assert timeout == 60.0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    _debug("已 monkeypatch httpx.post，开始调用 ai_service.run_ai")
    content = ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    _debug(f"ai_service.run_ai 返回内容: {content}")
    assert content == '{"ok": true}'
    assert ai_service.last_raw_response is not None
    _debug("test_ft_e4_s2_i1_01_ai成功返回内容 结束")


def test_bt_e4_s2_i1_01_choices为空映射ai_003(
    ai_service: AIService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：choices 为空时返回 AI_003。"""
    _debug("test_bt_e4_s2_i1_01_choices为空映射ai_003 开始")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": []}

    def _fake_post(*args, **kwargs) -> FakeResponse:
        _debug(f"fake_post 被调用，args={args}, kwargs_keys={list(kwargs.keys())}")
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", _fake_post)
    _debug("已 monkeypatch httpx.post，预期抛出 AI_003")
    with pytest.raises(ServiceError, match="AI_003"):
        ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    _debug("捕获到预期 AI_003，测试结束")


def test_ai认证失败映射ai_002(ai_service: AIService, monkeypatch: pytest.MonkeyPatch) -> None:
    """认证失败时返回 AI_002。"""
    _debug("test_ai认证失败映射ai_002 开始")

    class FakeResponse:
        status_code = 401

        @staticmethod
        def json() -> dict:
            return {}

    def _fake_post(*args, **kwargs) -> FakeResponse:
        _debug(f"fake_post 被调用，args={args}, kwargs_keys={list(kwargs.keys())}")
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", _fake_post)
    _debug("已 monkeypatch httpx.post，预期抛出 AI_002")
    with pytest.raises(ServiceError, match="AI_002"):
        ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    _debug("捕获到预期 AI_002，测试结束")
