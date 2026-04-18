"""截图预览对话框。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

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
        self._source_pixmap: QPixmap | None = None
        self._last_render_size: tuple[int, int] | None = None
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
        # 忽略 pixmap 尺寸提示，避免 setPixmap 反向驱动布局持续放大。
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
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

        self._source_pixmap = pixmap
        self._render_preview_pixmap()
        self._set_status("预览加载成功")

    def _render_preview_pixmap(self) -> None:
        """按当前控件尺寸刷新预览图片。"""
        if self._source_pixmap is None:
            return
        target_size = self.preview_label.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        scaled = self._source_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        rendered_size = (scaled.width(), scaled.height())
        if self._last_render_size == rendered_size:
            return
        self._last_render_size = rendered_size
        self.preview_label.setPixmap(scaled)
        self._logger.debug(
            "刷新预览图，source=%sx%s,target=%sx%s,render=%sx%s",
            self._source_pixmap.width(),
            self._source_pixmap.height(),
            target_size.width(),
            target_size.height(),
            scaled.width(),
            scaled.height(),
        )

    def resizeEvent(self, event) -> None:
        """窗口缩放时更新预览图尺寸。"""
        super().resizeEvent(event)
        self._render_preview_pixmap()

    def _on_retake_clicked(self) -> None:
        """处理重截动作。"""
        self._logger.debug("点击重新截取")
        self.retake_requested.emit()
        self.close()

    def _on_send_clicked(self) -> None:
        """处理发送解析动作。"""
        if not self.send_button.isEnabled():
            self._set_status("解析进行中，请勿重复点击", is_error=True)
            return
        self._logger.debug("点击发送解析，image_path=%s", self._image_path)
        self.send_requested.emit(self._image_path)

    def show_stage(self, stage_text: str) -> None:
        """显示处理中阶段并禁用发送按钮。"""
        self.send_button.setEnabled(False)
        self.retake_button.setEnabled(False)
        self._set_status(f"{stage_text}...")

    def allow_retry(self, message: str) -> None:
        """失败后恢复可重试状态。"""
        self.send_button.setEnabled(True)
        self.retake_button.setEnabled(True)
        self._set_status(message, is_error=True)

    def mark_send_complete(self, message: str) -> None:
        """发送流程完成后的状态更新。"""
        self.send_button.setEnabled(True)
        self.retake_button.setEnabled(True)
        self._set_status(message)
