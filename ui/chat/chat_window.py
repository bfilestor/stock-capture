"""AI 对话窗口。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.logging_config import get_logger


class ChatWindow(QWidget):
    """托盘对话入口窗口。"""

    def __init__(self) -> None:
        """初始化对话窗口。"""
        super().__init__()
        self._logger = get_logger(__name__)
        self._history_expanded = False
        self.setWindowTitle("AI对话")
        self.resize(960, 640)
        self._init_ui()
        self._logger.debug("ChatWindow 初始化完成")

    def _init_ui(self) -> None:
        """构建左右布局与基础交互控件。"""
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # 左侧历史面板：默认收起，后续 issue 再补真实数据渲染。
        self.history_panel = QWidget(self)
        self.history_panel.setObjectName("historyPanel")
        self.history_panel.setMinimumWidth(260)
        self.history_panel.setMaximumWidth(320)
        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.addWidget(QLabel("历史AI分析结果", self.history_panel))
        self.history_placeholder_label = QLabel("历史区将在后续 Issue 接入数据。", self.history_panel)
        self.history_placeholder_label.setWordWrap(True)
        history_layout.addWidget(self.history_placeholder_label)
        history_layout.addStretch(1)
        root_layout.addWidget(self.history_panel, 0)

        # 右侧对话区：当前提供输入/发送/清空占位。
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        toolbar_layout = QHBoxLayout()
        self.toggle_history_button = QPushButton("展开历史", self)
        self.toggle_history_button.clicked.connect(self.toggle_history_panel)
        toolbar_layout.addWidget(self.toggle_history_button, 0, Qt.AlignLeft)
        toolbar_layout.addStretch(1)
        right_layout.addLayout(toolbar_layout)

        self.message_area_placeholder = QLabel("聊天气泡区域将在后续 Issue 完成。", self)
        self.message_area_placeholder.setObjectName("chatMessageAreaPlaceholder")
        self.message_area_placeholder.setStyleSheet("border:1px solid #CFD8DC; padding:10px;")
        self.message_area_placeholder.setMinimumHeight(360)
        self.message_area_placeholder.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_layout.addWidget(self.message_area_placeholder, 1)

        self.input_edit = QTextEdit(self)
        self.input_edit.setPlaceholderText("请输入要与 AI 对话的内容...")
        self.input_edit.setMinimumHeight(120)
        right_layout.addWidget(self.input_edit)

        action_layout = QHBoxLayout()
        self.clear_button = QPushButton("清空聊天内容", self)
        self.send_button = QPushButton("发送", self)
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch(1)
        action_layout.addWidget(self.send_button)
        right_layout.addLayout(action_layout)

        root_layout.addWidget(right_panel, 1)
        self._set_history_expanded(False)
        self._logger.debug("对话窗口 UI 初始化完成，history_expanded=%s", self._history_expanded)

    def is_history_expanded(self) -> bool:
        """返回左侧历史面板是否处于展开态。"""
        return self._history_expanded

    def toggle_history_panel(self) -> None:
        """切换左侧历史面板展开状态。"""
        next_state = not self._history_expanded
        self._set_history_expanded(next_state)

    def _set_history_expanded(self, expanded: bool) -> None:
        """设置左侧历史面板显隐与按钮文案。"""
        self._history_expanded = expanded
        self.history_panel.setVisible(expanded)
        self.toggle_history_button.setText("收起历史" if expanded else "展开历史")
        self._logger.debug("历史面板状态更新，expanded=%s", expanded)
