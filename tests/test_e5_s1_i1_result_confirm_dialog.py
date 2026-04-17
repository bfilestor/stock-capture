"""E5-S1-I1 结果确认界面测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.result.result_confirm_dialog import ResultConfirmDialog


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e5_s1_i1_01_结果页展示完整(app: QApplication) -> None:
    """功能测试：展示业务类型、日期、OCR、AI结果。"""
    dialog = ResultConfirmDialog(
        capture_type_name="市场动态",
        ocr_text="OCR 原文内容",
        ai_text='{"trade_date":"2026-04-17"}',
    )
    assert "市场动态" in dialog.capture_type_label.text()
    assert dialog.current_date_text() == dialog.today_text()
    assert dialog.ai_text_edit.toPlainText() == '{"trade_date":"2026-04-17"}'

    dialog.ai_text_edit.setPlainText('{"trade_date":"2026-04-18"}')
    assert dialog.ai_text_edit.toPlainText() == '{"trade_date":"2026-04-18"}'


def test_bt_e5_s1_i1_01_ocr超长文本默认折叠可展开(app: QApplication) -> None:
    """边界测试：OCR 文本默认折叠，点击后可展开。"""
    long_ocr = "OCR内容" * 500
    dialog = ResultConfirmDialog(
        capture_type_name="市场总览",
        ocr_text=long_ocr,
        ai_text='{"k":"v"}',
    )

    assert dialog.ocr_text_edit.isHidden() is True
    dialog.ocr_toggle_button.click()
    assert dialog.ocr_text_edit.isHidden() is False
    assert dialog.ocr_text_edit.toPlainText() == long_ocr
