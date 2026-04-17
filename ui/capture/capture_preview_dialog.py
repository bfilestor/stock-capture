"""截图预览对话框。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from utils.logging_config import get_logger


class CapturePreviewDialog(QDialog):
    """展示截图预览并提供重截/发送解析入口。"""

    retake_requested = Signal()
    send_requested = Signal(str)

    def __init__(
        self,
        image_path: str,
        capture_type_name: str,
        parent: QDialog | None = None,
    ) -> None:
        """初始化预览窗口。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._image_path = image_path
        self._capture_type_name = capture_type_name
        self.setWindowTitle("截图预览")
        self.resize(760, 520)
        self._init_ui()

    def _init_ui(self) -> None:
        """构建预览界面。"""
        layout = QVBoxLayout(self)

        type_label = QLabel(f"当前业务类型：{self._capture_type_name}", self)
        layout.addWidget(type_label)

        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(360)
        self.preview_label.setStyleSheet("border:1px solid #90A4AE; background:#F5F5F5;")
        layout.addWidget(self.preview_label, 1)

        self.status_label = QLabel("准备就绪", self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.retake_button = QPushButton("重新截取", self)
        self.send_button = QPushButton("发送解析", self)
        button_layout.addWidget(self.retake_button)
        button_layout.addWidget(self.send_button)
        layout.addLayout(button_layout)

        self.retake_button.clicked.connect(self._on_retake_clicked)
        self.send_button.clicked.connect(self._on_send_clicked)

        self._load_preview()

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """更新状态文本。"""
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color:{color};")
        self.status_label.setText(message)

    def _load_preview(self) -> None:
        """加载预览图片。"""
        image_file = Path(self._image_path)
        if not image_file.exists():
            self.preview_label.setText("截图文件不存在，请重新截取。")
            self.send_button.setEnabled(False)
            self._set_status("截图失效，请点击“重新截取”", is_error=True)
            self._logger.warning("预览文件缺失: %s", self._image_path)
            return

        pixmap = QPixmap(str(image_file))
        if pixmap.isNull():
            self.preview_label.setText("截图文件读取失败，请重新截取。")
            self.send_button.setEnabled(False)
            self._set_status("截图读取失败，请点击“重新截取”", is_error=True)
            self._logger.warning("预览文件读取失败: %s", self._image_path)
            return

        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        self._set_status("预览加载成功")

    def resizeEvent(self, event) -> None:
        """窗口缩放时更新预览图尺寸。"""
        super().resizeEvent(event)
        if self.preview_label.pixmap() is not None:
            self._load_preview()

    def _on_retake_clicked(self) -> None:
        """处理重截动作。"""
        self._logger.debug("点击重新截取")
        self.retake_requested.emit()
        self.close()

    def _on_send_clicked(self) -> None:
        """处理发送解析动作。"""
        self._logger.debug("点击发送解析，image_path=%s", self._image_path)
        self.send_requested.emit(self._image_path)

