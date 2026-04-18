"""E8-S1-I2 对话窗口布局与历史区交互测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.chat.chat_window import ChatWindow


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e8_s1_i2_01_历史区默认收起并可展开收起(app: QApplication) -> None:
    """功能测试：历史区默认收起，点击按钮可展开并再次收起。"""
    dialog = ChatWindow()

    assert dialog.is_history_expanded() is False
    assert dialog.toggle_history_button.text() == "展开历史"

    dialog.toggle_history_button.click()
    assert dialog.is_history_expanded() is True
    assert dialog.toggle_history_button.text() == "收起历史"

    dialog.toggle_history_button.click()
    assert dialog.is_history_expanded() is False
    assert dialog.toggle_history_button.text() == "展开历史"


def test_bt_e8_s1_i2_01_历史区高频切换状态稳定(app: QApplication) -> None:
    """边界测试：快速多次切换历史区后状态与按钮文案保持一致。"""
    dialog = ChatWindow()
    toggle_count = 13
    for _ in range(toggle_count):
        dialog.toggle_history_button.click()

    assert dialog.is_history_expanded() is True
    assert dialog.toggle_history_button.text() == "收起历史"

    dialog.toggle_history_button.click()
    assert dialog.is_history_expanded() is False
    assert dialog.toggle_history_button.text() == "展开历史"
