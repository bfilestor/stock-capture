"""E2-S2-I2 连接测试、默认回退与Key显示控制测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from PySide6.QtWidgets import QApplication, QLineEdit

from db.database import DatabaseBootstrap
from services.config_service import AIModelPayload, AIProviderPayload, ConfigService, ConfigValidationError
from ui.settings.ai_provider_tab import AIProviderTab


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


@pytest.fixture
def config_service(tmp_path: Path) -> ConfigService:
    """创建隔离数据库下的配置服务。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    return ConfigService(db_path)


def test_ft_e2_s2_i2_01_测试连接成功(
    monkeypatch: pytest.MonkeyPatch, config_service: ConfigService
) -> None:
    """功能测试：测试连接成功返回 OK。"""
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
        AIModelPayload(
            model_code="gpt-test",
            model_name="测试模型",
            is_enabled=True,
            is_default=True,
        ),
    )

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout: float) -> httpx.Response:
        assert url == "https://api.example.com/v1/chat/completions"
        assert "Authorization" in headers
        assert json["model"] == "gpt-test"
        assert json["messages"][0]["role"] == "system"
        assert "只回复ok" in json["messages"][0]["content"]
        assert timeout == 8.0
        return httpx.Response(
            status_code=200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = config_service.test_provider_connection(provider_id)
    assert result["code"] == "OK"
    assert "ok" in result["message"].lower()


def test_bt_e2_s2_i2_01_base_url非法不发起请求(
    monkeypatch: pytest.MonkeyPatch, config_service: ConfigService
) -> None:
    """边界测试：非法 URL 直接校验失败，不触发网络请求。"""
    provider_id = config_service.create_provider(
        AIProviderPayload(
            name="非法URL供应商",
            api_base_url="not-a-valid-url",
            api_key="xx",
            is_enabled=True,
            is_default=False,
        )
    )

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout: float) -> httpx.Response:
        raise AssertionError("非法 URL 不应发起请求")

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(ConfigValidationError, match="Base URL 格式非法"):
        config_service.test_provider_connection(provider_id)


def test_bt_e2_s2_i2_02_模型回复不含ok返回失败原因(
    monkeypatch: pytest.MonkeyPatch, config_service: ConfigService
) -> None:
    """边界测试：模型回复不包含 ok 时测试失败并返回原因。"""
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
        AIModelPayload(
            model_code="gpt-test",
            model_name="测试模型",
            is_enabled=True,
            is_default=True,
        ),
    )

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout: float) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": "连接正常"}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = config_service.test_provider_connection(provider_id)
    assert result["code"] == "AI_003"
    assert "未包含ok" in result["message"]


def test_default_provider_fallback_to_first_enabled(config_service: ConfigService) -> None:
    """未设置默认供应商时，回退首个启用供应商及其默认模型。"""
    provider_a = config_service.create_provider(
        AIProviderPayload(
            name="供应商A",
            api_base_url="https://a.example.com/v1",
            api_key="a-key",
            is_enabled=True,
            is_default=False,
        )
    )
    config_service.create_model(
        provider_a,
        AIModelPayload(model_code="a-model-1", model_name="A模型1", is_enabled=True, is_default=True),
    )

    provider_b = config_service.create_provider(
        AIProviderPayload(
            name="供应商B",
            api_base_url="https://b.example.com/v1",
            api_key="b-key",
            is_enabled=True,
            is_default=False,
        )
    )
    config_service.create_model(
        provider_b,
        AIModelPayload(model_code="b-model-1", model_name="B模型1", is_enabled=True, is_default=True),
    )

    provider, model = config_service.resolve_active_provider_model()
    assert int(provider["id"]) == provider_a
    assert int(model["provider_id"]) == provider_a


def test_api_key_default_hidden_and_can_toggle(app: QApplication, config_service: ConfigService) -> None:
    """API Key 默认隐藏，可手动切换显示。"""
    config_service.create_provider(
        AIProviderPayload(
            name="供应商-Key-Test",
            api_base_url="https://key.example.com/v1",
            api_key="secret-key-value",
            is_enabled=True,
            is_default=True,
        )
    )
    tab = AIProviderTab(config_service)
    tab.reload_provider_list()
    tab.provider_list.setCurrentRow(0)

    assert tab.provider_key_edit.echoMode() == QLineEdit.Password
    tab.toggle_key_visibility()
    assert tab.provider_key_edit.echoMode() == QLineEdit.Normal
    tab.toggle_key_visibility()
    assert tab.provider_key_edit.echoMode() == QLineEdit.Password
