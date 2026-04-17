"""E5-S1-I2 JSON 格式化与拦截测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from services.result_service import ResultService
from ui.result.result_confirm_dialog import ResultConfirmDialog


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e5_s1_i2_01_合法json可格式化(app: QApplication) -> None:
    """功能测试：合法 JSON 点击格式化后按缩进重排。"""
    dialog = ResultConfirmDialog(
        capture_type_name="市场动态",
        ocr_text="ocr",
        ai_text='{"b":1,"a":{"x":2}}',
        result_service=ResultService(),
    )
    dialog.format_button.click()
    text = dialog.ai_text_edit.toPlainText()
    assert '"b": 1' in text
    assert "\n" in text


def test_bt_e5_s1_i2_01_非对象json入库被拦截(app: QApplication) -> None:
    """边界测试：数组 JSON 入库前被拦截。"""
    dialog = ResultConfirmDialog(
        capture_type_name="市场动态",
        ocr_text="ocr",
        ai_text="[]",
        result_service=ResultService(),
    )
    emitted: list[tuple[str, str]] = []
    dialog.save_requested.connect(lambda d, t: emitted.append((d, t)))

    dialog.save_button.click()
    assert emitted == []
    assert "必须为对象JSON" in dialog.status_label.text()

