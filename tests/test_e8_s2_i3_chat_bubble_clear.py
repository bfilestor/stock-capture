"""E8-S2-I3 聊天气泡与清空能力测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.chat.chat_message_bubble import ChatMessageBubble
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

    def is_running(self) -> bool:
        """替身中始终无运行任务。"""
        return False

    def start_chat(self, messages, on_stage, on_success, on_error) -> bool:
        """同步返回固定回复。"""
        on_stage("AI思考中")
        on_success("这是助手回复")
        return True


def test_ft_e8_s2_i3_01_清空聊天不会影响后续输入(app: QApplication) -> None:
    """功能测试：清空聊天后消息区为空且可继续输入。"""
    dialog = ChatWindow(chat_pipeline=FakeChatPipeline())
    dialog.input_edit.setPlainText("请总结今日热点")
    dialog.send_button.click()

    assert dialog.message_bubble_count() == 2
    roles = [bubble.role for bubble in dialog.message_bubbles()]
    assert roles == ["user", "assistant"]

    dialog.clear_button.click()
    assert dialog.message_bubble_count() == 0
    assert dialog.message_area_placeholder.isHidden() is False
    assert dialog.input_edit.isEnabled() is True


def test_bt_e8_s2_i3_01_超长消息收起仅显示一行(app: QApplication) -> None:
    """边界测试：超长消息收起时仅显示一行并可恢复全文。"""
    long_text = "超长消息内容" * 80
    bubble = ChatMessageBubble(role="assistant", text=long_text)
    bubble.resize(320, 160)
    bubble.set_collapsed(True)

    collapsed_text = bubble.display_text()
    assert bubble.is_collapsed() is True
    assert "\n" not in collapsed_text
    assert len(collapsed_text) < len(long_text)

    bubble.set_collapsed(False)
    assert bubble.is_collapsed() is False
    assert bubble.display_text() == long_text
