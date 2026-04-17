"""设置窗口 Tab2：AI 配置（占位，后续 Issue 扩展）。"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AIProviderTab(QWidget):
    """AI 配置页占位组件。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化占位页面。"""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        tip_label = QLabel("AI 配置功能将在 E2-S2-I1 / E2-S2-I2 中实现。", self)
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        layout.addStretch(1)

