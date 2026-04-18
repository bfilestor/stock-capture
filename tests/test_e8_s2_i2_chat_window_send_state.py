"""E8-S2-I2 对话窗口发送状态测试。"""

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


class FakeChatPipeline:
    """对话管线替身。"""

    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self.started_count = 0
        self.last_messages: list[dict[str, str]] = []
        self._running = False

    def is_running(self) -> bool:
        """返回当前运行状态。"""
        return self._running

    def start_chat(self, messages, on_stage, on_success, on_error) -> bool:
        """模拟对话发送。"""
        if self._running:
            return False
        self.started_count += 1
        self.last_messages = list(messages)
        self._running = True
        on_stage("AI思考中")
        if self.mode == "success":
            self._running = False
            on_success("这是AI回复")
            return True
        self._running = False
        on_error("CHAT_001", "连接失败")
        return True


def test_ft_e8_s2_i2_02_发送成功后恢复按钮并追加回复(app: QApplication) -> None:
    """功能测试：发送成功后恢复发送按钮并追加助手回复。"""
    pipeline = FakeChatPipeline(mode="success")
    dialog = ChatWindow(chat_pipeline=pipeline)
    dialog.input_edit.setPlainText("你好")

    dialog.send_button.click()

    assert pipeline.started_count == 1
    assert dialog.send_button.isEnabled() is True
    assert dialog.send_button.text() == "发送"
    assert "这是AI回复" in dialog.message_area_placeholder.text()


def test_bt_e8_s2_i2_02_发送失败时保留输入并允许重试(app: QApplication) -> None:
    """边界测试：发送失败时输入保留，按钮恢复可重试。"""
    pipeline = FakeChatPipeline(mode="error")
    dialog = ChatWindow(chat_pipeline=pipeline)
    dialog.input_edit.setPlainText("请分析昨日热点")

    dialog.send_button.click()

    assert pipeline.started_count == 1
    assert dialog.input_edit.toPlainText() == "请分析昨日热点"
    assert dialog.send_button.isEnabled() is True
    assert dialog.send_button.text() == "发送"
    assert "连接失败" in dialog.status_label.text()
