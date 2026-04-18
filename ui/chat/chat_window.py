"""AI 对话窗口（E8-S1-I1 占位实现）。"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from utils.logging_config import get_logger


class ChatWindow(QWidget):
    """托盘对话入口窗口。"""

    def __init__(self) -> None:
        """初始化对话窗口。"""
        super().__init__()
        self._logger = get_logger(__name__)
        self.setWindowTitle("AI对话")
        self.resize(960, 640)
        self._init_ui()
        self._logger.debug("ChatWindow 初始化完成")

    def _init_ui(self) -> None:
        """构建占位界面，详细布局在 E8-S1-I2 落地。"""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("对话窗口初始化完成，详细布局将在后续 Issue 实现。", self))

