"""E8-S2-I2 对话窗口发送状态测试。"""

from __future__ import annotations

from pathlib import Path

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
        self.last_messages: list[dict] = []
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
    assert isinstance(pipeline.last_messages[-1]["content"], str)
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


def test_ft_e8_s2_i2_03_选择图片后按多模态发送(app: QApplication, tmp_path: Path) -> None:
    """功能测试：选择图片后应构建 image_url 片段并正常发送。"""
    pipeline = FakeChatPipeline(mode="success")
    dialog = ChatWindow(chat_pipeline=pipeline)
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-image")

    dialog.input_edit.setPlainText("请分析这张图")
    dialog._append_selected_images([str(image_path)])  # type: ignore[attr-defined]
    assert dialog.selected_image_count() == 1

    dialog.send_button.click()

    assert pipeline.started_count == 1
    user_message = pipeline.last_messages[-1]
    assert user_message["role"] == "user"
    assert isinstance(user_message["content"], list)
    assert user_message["content"][0]["type"] == "text"
    assert user_message["content"][1]["type"] == "image_url"
    assert user_message["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert dialog.selected_image_count() == 0


def test_bt_e8_s2_i2_03_最多仅允许选择三张图片(app: QApplication, tmp_path: Path) -> None:
    """边界测试：选择超过3张图片时应自动限制为3张。"""
    pipeline = FakeChatPipeline(mode="success")
    dialog = ChatWindow(chat_pipeline=pipeline)
    paths: list[str] = []
    for idx in range(4):
        image_path = tmp_path / f"sample_{idx}.png"
        image_path.write_bytes(b"fake-image")
        paths.append(str(image_path))

    dialog._append_selected_images(paths)  # type: ignore[attr-defined]
    assert dialog.selected_image_count() == 3


def test_ft_e8_s2_i2_04_截图上传成功后加入待发送图片(app: QApplication, tmp_path: Path) -> None:
    """功能测试：截图上传完成后应加入已选图片列表并参与后续发送。"""
    pipeline = FakeChatPipeline(mode="success")
    dialog = ChatWindow(chat_pipeline=pipeline)
    screenshot_path = tmp_path / "shot.png"
    screenshot_path.write_bytes(b"fake-shot-image")

    dialog._on_capture_image_completed(str(screenshot_path))  # type: ignore[attr-defined]
    assert dialog.selected_image_count() == 1
    assert dialog.selected_image_paths()[0].endswith("shot.png")

    dialog.input_edit.setPlainText("这是截图上传内容")
    dialog.send_button.click()

    assert pipeline.started_count == 1
    assert isinstance(pipeline.last_messages[-1]["content"], list)
