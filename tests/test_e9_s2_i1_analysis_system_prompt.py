"""E9-S2-I1 截图解析链路 SystemPrompt 注入测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from PySide6.QtWidgets import QDialog

from db.database import DatabaseBootstrap
from services.ai_service import AIService
from services.capture_workflow_service import CaptureWorkflowService
from services.config_service import (
    AIModelPayload,
    AIProviderPayload,
    CaptureTypePayload,
    ConfigService,
    DEFAULT_ANALYSIS_SYSTEM_PROMPT,
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


def test_ft_e9_s2_i1_01_ai请求命中业务类型system_prompt(
    config_service: ConfigService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：显式传入业务类型 system_prompt 时优先写入请求。"""
    ai_service = AIService(config_service=config_service)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        assert url == "https://api.example.com/v1/chat/completions"
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    ai_service.run_ai(
        prompt="输出JSON",
        ocr_text="OCR文本",
        system_prompt="你是业务类型专用系统提示词",
    )
    assert captured_payload["messages"][0]["role"] == "system"
    assert captured_payload["messages"][0]["content"] == "你是业务类型专用系统提示词"


def test_ft_e9_s2_i1_02_ai请求命中全局system_prompt(
    config_service: ConfigService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：未传业务类型 system_prompt 时命中全局配置。"""
    config_service.save_global_system_prompt("你是全局系统提示词")
    ai_service = AIService(config_service=config_service)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    assert captured_payload["messages"][0]["content"] == "你是全局系统提示词"


def test_bt_e9_s2_i1_01_ai请求无配置时回退默认system_prompt(
    config_service: ConfigService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：业务类型与全局均未配置时回退默认提示词。"""
    ai_service = AIService(config_service=config_service)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    captured_payload: dict = {}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    ai_service.run_ai(prompt="输出JSON", ocr_text="OCR文本")
    assert captured_payload["messages"][0]["content"] == DEFAULT_ANALYSIS_SYSTEM_PROMPT


def test_ft_e9_s2_i1_03_截图解析链路向ai阶段透传system_prompt(
    config_service: ConfigService,
) -> None:
    """功能测试：截图流程触发 AI 解析时透传业务类型 SystemPrompt。"""
    capture_type_id = config_service.create_capture_type(
        CaptureTypePayload(
            name="市场动态",
            prompt_template="输出结构化JSON",
            system_prompt="你是市场动态专用系统提示词",
            is_enabled=True,
        )
    )

    class FakeDialog:
        """业务类型选择框替身。"""

        def __init__(self, capture_types: list[dict], _parent: object | None) -> None:
            self.selected_capture_type = capture_types[0]

        def exec(self) -> int:
            return QDialog.Accepted

    class FakePipeline:
        """解析管线替身。"""

        def __init__(self) -> None:
            self.last_system_prompt = ""
            self.last_prompt = ""
            self.last_ocr_text = ""

        def is_running(self) -> bool:
            return False

        def start_ai(
            self,
            prompt: str,
            ocr_text: str,
            on_stage,
            on_success,
            on_error,
            system_prompt: str | None = None,
        ) -> bool:
            self.last_prompt = prompt
            self.last_ocr_text = ocr_text
            self.last_system_prompt = (system_prompt or "").strip()
            return True

    fake_pipeline = FakePipeline()
    workflow = CaptureWorkflowService(
        config_service,
        dialog_factory=FakeDialog,
        analysis_pipeline=fake_pipeline,  # type: ignore[arg-type]
    )
    selected, _ = workflow.select_capture_type()
    assert selected is True
    assert workflow.context.capture_type_id == capture_type_id
    workflow._on_ai_parse_requested("OCR已修正文本")

    assert fake_pipeline.last_prompt == "输出结构化JSON"
    assert fake_pipeline.last_ocr_text == "OCR已修正文本"
    assert fake_pipeline.last_system_prompt == "你是市场动态专用系统提示词"

