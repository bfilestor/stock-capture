"""E3-S1-I1 截图入口业务类型选择测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialog

from db.database import DatabaseBootstrap
from services.capture_workflow_service import CaptureWorkflowService
from services.config_service import CaptureTypePayload, ConfigService


@pytest.fixture
def config_service(tmp_path: Path) -> ConfigService:
    """创建隔离数据库下的配置服务。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    return ConfigService(db_path)


def test_ft_e3_s1_i1_01_业务类型面板仅展示启用项(config_service: ConfigService) -> None:
    """功能测试：截图入口仅展示启用业务类型，选中后写入上下文。"""
    config_service.create_capture_type(
        CaptureTypePayload(name="市场动态", prompt_template="模板1", is_enabled=True)
    )
    config_service.create_capture_type(
        CaptureTypePayload(name="涨停复盘", prompt_template="模板2", is_enabled=True)
    )
    config_service.create_capture_type(
        CaptureTypePayload(name="禁用类型", prompt_template="模板3", is_enabled=False)
    )

    captured_payload: dict[str, object] = {}

    class FakeDialog:
        """测试用选择框替身。"""

        def __init__(self, capture_types: list[dict], _parent: object | None) -> None:
            captured_payload["names"] = [row["name"] for row in capture_types]
            self.selected_capture_type = capture_types[1]

        def exec(self) -> int:
            return QDialog.Accepted

    workflow = CaptureWorkflowService(config_service, dialog_factory=FakeDialog)
    success, message = workflow.select_capture_type()

    assert success is True
    assert "成功" in message
    assert captured_payload["names"] == ["市场动态", "涨停复盘"]
    assert workflow.context.capture_type_name == "涨停复盘"
    assert workflow.context.capture_type_id is not None


def test_bt_e3_s1_i1_01_无启用类型时中断流程(config_service: ConfigService) -> None:
    """边界测试：无启用业务类型时提示并中断。"""
    config_service.create_capture_type(
        CaptureTypePayload(name="全部禁用", prompt_template="模板", is_enabled=False)
    )
    called = {"dialog_called": False}

    class FakeDialog:
        """测试用对话框替身。"""

        def __init__(self, capture_types: list[dict], _parent: object | None) -> None:
            called["dialog_called"] = True
            self.selected_capture_type = capture_types[0] if capture_types else None

        def exec(self) -> int:
            return QDialog.Accepted

    workflow = CaptureWorkflowService(config_service, dialog_factory=FakeDialog)
    success, message = workflow.select_capture_type()

    assert success is False
    assert "先在设置中启用" in message
    assert called["dialog_called"] is False

