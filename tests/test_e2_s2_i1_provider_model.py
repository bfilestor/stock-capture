"""E2-S2-I1 供应商与模型管理测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from db.database import DatabaseBootstrap
from services.config_service import AIModelPayload, AIProviderPayload, ConfigService, ConfigValidationError

@pytest.fixture
def config_service(tmp_path: Path) -> ConfigService:
    """创建隔离数据库下的配置服务。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    return ConfigService(db_path)


def test_ft_e2_s2_i1_01_设置默认模型(config_service: ConfigService) -> None:
    """功能测试：设置默认模型时，同供应商仅保留一个默认模型。"""
    provider_id = config_service.create_provider(
        AIProviderPayload(
            name="OpenAI-兼容",
            api_base_url="https://api.example.com/v1",
            api_key="test-key",
            is_enabled=True,
            is_default=True,
        )
    )
    model_a = config_service.create_model(
        provider_id,
        AIModelPayload(model_code="model-a", model_name="模型A", is_enabled=True, is_default=True),
    )
    model_b = config_service.create_model(
        provider_id,
        AIModelPayload(model_code="model-b", model_name="模型B", is_enabled=True, is_default=False),
    )

    config_service.set_default_model(model_b)
    models = config_service.list_models(provider_id)
    model_default_map = {row["id"]: int(row["is_default"]) for row in models}

    assert model_default_map[model_a] == 0
    assert model_default_map[model_b] == 1


def test_bt_e2_s2_i1_01_禁用模型不可设默认(config_service: ConfigService) -> None:
    """边界测试：禁用模型设默认应被拦截。"""
    provider_id = config_service.create_provider(
        AIProviderPayload(
            name="DeepSeek",
            api_base_url="https://api.deepseek.com/v1",
            api_key="key",
            is_enabled=True,
            is_default=False,
        )
    )
    disabled_model_id = config_service.create_model(
        provider_id,
        AIModelPayload(model_code="disabled-model", model_name="禁用模型", is_enabled=False, is_default=False),
    )

    with pytest.raises(ConfigValidationError, match="禁用模型不可设为默认模型"):
        config_service.set_default_model(disabled_model_id)
