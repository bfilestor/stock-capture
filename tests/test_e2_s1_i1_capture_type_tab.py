"""E2-S1-I1 业务类型管理测试。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from db.database import DatabaseBootstrap
from services.config_service import CaptureTypePayload, ConfigService
from ui.settings.capture_type_tab import CaptureTypeTab


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


@pytest.fixture
def db_path() -> Path:
    """创建独立测试数据库。"""
    runtime_root = PROJECT_ROOT / "tests" / "tmp_runtime" / "e2_s1_i1"
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    runtime_root.mkdir(parents=True, exist_ok=True)
    path = runtime_root / "stock_capture.db"
    DatabaseBootstrap(path).initialize()
    return path


def test_ft_e2_s1_i1_01_新增业务类型成功(app: QApplication, db_path: Path) -> None:
    """功能测试：输入名称与 Prompt 后可成功保存。"""
    service = ConfigService(db_path)
    tab = CaptureTypeTab(service)

    tab.new_capture_type()
    tab.name_edit.setText("市场动态")
    tab.description_edit.setPlainText("用于盘后情绪复盘")
    tab.prompt_edit.setPlainText("请按JSON输出市场动态结构化数据")
    saved = tab.save_current_capture_type()

    assert saved is True
    assert "保存成功" in tab.status_label.text()

    records = service.list_capture_types()
    assert len(records) == 1
    assert records[0]["name"] == "市场动态"
    assert records[0]["prompt_template"] == "请按JSON输出市场动态结构化数据"


def test_bt_e2_s1_i1_01_名称重复保存失败并保留编辑内容(
    app: QApplication, db_path: Path
) -> None:
    """边界测试：重名保存失败，且当前编辑内容不丢失。"""
    service = ConfigService(db_path)
    service.create_capture_type(
        CaptureTypePayload(name="市场总览", prompt_template="模板A", description="", is_enabled=True)
    )
    tab = CaptureTypeTab(service)

    tab.new_capture_type()
    tab.name_edit.setText("市场总览")
    tab.prompt_edit.setPlainText("模板B")
    saved = tab.save_current_capture_type()

    assert saved is False
    assert "已存在" in tab.status_label.text()
    assert tab.name_edit.text() == "市场总览"
    assert tab.prompt_edit.toPlainText() == "模板B"

