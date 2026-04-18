"""聊天消息气泡组件。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class ChatMessageBubble(QWidget):
    """单条聊天消息气泡，支持收起/展开。"""

    def __init__(self, role: str, text: str, parent: QWidget | None = None) -> None:
        """初始化消息气泡。"""
        super().__init__(parent)
        self.role = role
        self._full_text = text
        self._collapsed = False
        self._init_ui()
        self._refresh_content()

    def _init_ui(self) -> None:
        """构建气泡界面。"""
        self.setObjectName("chatMessageBubble")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        role_name = "你" if self.role == "user" else "AI"
        self.role_label = QLabel(role_name, self)
        self.role_label.setStyleSheet("font-weight:600; color:#37474F;")
        self.toggle_button = QPushButton("收起", self)
        self.toggle_button.setMinimumHeight(30)
        self.toggle_button.setStyleSheet("padding:4px 10px;")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        header_layout.addWidget(self.role_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.toggle_button)
        root_layout.addLayout(header_layout)

        self.content_label = QLabel(self)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root_layout.addWidget(self.content_label)

        bubble_bg = "#E3F2FD" if self.role == "user" else "#F5F5F5"
        # 仅给气泡根容器设置背景与边框，避免把子控件（如按钮）挤压到文字被裁切。
        self.setStyleSheet(
            f"#chatMessageBubble{{background:{bubble_bg}; border:1px solid #CFD8DC; border-radius:8px; padding:8px;}}"
        )
        self.setMinimumWidth(260)
        self.setMaximumWidth(560)

    def _on_toggle_clicked(self) -> None:
        """切换收起/展开状态。"""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        """设置收起状态。"""
        self._collapsed = collapsed
        self.toggle_button.setText("展开" if collapsed else "收起")
        self._refresh_content()

    def is_collapsed(self) -> bool:
        """返回当前是否为收起状态。"""
        return self._collapsed

    def display_text(self) -> str:
        """返回当前展示文本。"""
        return self.content_label.text()

    def full_text(self) -> str:
        """返回完整文本。"""
        return self._full_text

    def _collapsed_text(self) -> str:
        """计算收起状态展示文本（单行省略）。"""
        one_line = " ".join(self._full_text.splitlines())
        metrics = QFontMetrics(self.content_label.font())
        width = max(80, self.width() - 36)
        return metrics.elidedText(one_line, Qt.ElideRight, width)

    def _refresh_content(self) -> None:
        """刷新内容显示。"""
        if self._collapsed:
            self.content_label.setWordWrap(False)
            self.content_label.setText(self._collapsed_text())
            return
        self.content_label.setWordWrap(True)
        self.content_label.setText(self._full_text)

    def resizeEvent(self, event) -> None:
        """尺寸变化时刷新收起文本。"""
        super().resizeEvent(event)
        if self._collapsed:
            self._refresh_content()
