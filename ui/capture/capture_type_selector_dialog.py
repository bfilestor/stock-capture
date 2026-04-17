"""业务类型选择面板。"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout

from utils.logging_config import get_logger


class CaptureTypeSelectorDialog(QDialog):
    """展示启用业务类型按钮列表的选择对话框。"""

    def __init__(self, capture_types: list[dict[str, Any]], parent: QDialog | None = None) -> None:
        """初始化选择面板。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._capture_types = capture_types
        self.selected_capture_type: dict[str, Any] | None = None
        self.setWindowTitle("选择业务类型")
        self.resize(420, 280)
        self._init_ui()

    def _init_ui(self) -> None:
        """构建按钮列表。"""
        layout = QVBoxLayout(self)
        title = QLabel("请选择本次截图的业务类型：", self)
        layout.addWidget(title)

        if not self._capture_types:
            empty_label = QLabel("暂无可用业务类型，请先在设置中启用。", self)
            empty_label.setWordWrap(True)
            layout.addWidget(empty_label)
            return

        grid = QGridLayout()
        for index, row in enumerate(self._capture_types):
            button = QPushButton(str(row.get("name", "")), self)
            button.clicked.connect(lambda _=False, payload=row: self._select(payload))
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)

    def _select(self, payload: dict[str, Any]) -> None:
        """处理业务类型选择。"""
        self.selected_capture_type = payload
        self._logger.debug(
            "业务类型已选择，id=%s, name=%s", payload.get("id"), payload.get("name")
        )
        self.accept()

