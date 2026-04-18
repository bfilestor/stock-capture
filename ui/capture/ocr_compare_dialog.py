"""OCR 对照预览窗口。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from utils.logging_config import get_logger


class OCRCompareDialog(QDialog):
    """展示图片与 OCR 对照内容，允许用户编辑后触发 AI 解析。"""

    ai_parse_requested = Signal(str)

    def __init__(
        self,
        image_path: str,
        capture_type_name: str,
        ocr_text: str,
        parent: QDialog | None = None,
    ) -> None:
        """初始化 OCR 对照窗口。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._image_path = image_path
        self._capture_type_name = capture_type_name
        self._source_pixmap: QPixmap | None = None
        self._last_render_size: tuple[int, int] | None = None
        self.setWindowTitle("OCR 对照确认")
        self.resize(980, 620)
        self._init_ui(ocr_text)

    def _init_ui(self, ocr_text: str) -> None:
        """构建 OCR 对照页面。"""
        layout = QVBoxLayout(self)

        title_label = QLabel(f"业务类型：{self._capture_type_name}", self)
        layout.addWidget(title_label)

        content_layout = QHBoxLayout()

        image_layout = QVBoxLayout()
        image_layout.addWidget(QLabel("截图预览：", self))
        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.preview_label.setMinimumSize(360, 360)
        self.preview_label.setStyleSheet("border:1px solid #90A4AE; background:#F5F5F5;")
        image_layout.addWidget(self.preview_label, 1)
        content_layout.addLayout(image_layout, 1)

        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel("OCR 文本（可编辑）：", self))
        self.ocr_text_edit = QPlainTextEdit(self)
        self.ocr_text_edit.setPlainText(ocr_text)
        self.ocr_text_edit.setMinimumHeight(360)
        text_layout.addWidget(self.ocr_text_edit, 1)
        content_layout.addLayout(text_layout, 1)

        layout.addLayout(content_layout, 1)

        button_layout = QHBoxLayout()
        self.ai_parse_button = QPushButton("AI解析", self)
        button_layout.addStretch(1)
        button_layout.addWidget(self.ai_parse_button)
        layout.addLayout(button_layout)

        self.status_label = QLabel("请确认 OCR 文本，确认后点击 AI解析", self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.ai_parse_button.clicked.connect(self._on_ai_parse_clicked)
        self._load_preview()

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """更新状态文本。"""
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color:{color};")
        self.status_label.setText(message)

    def _load_preview(self) -> None:
        """加载截图预览图片。"""
        image_file = Path(self._image_path)
        if not image_file.exists():
            self.preview_label.setText("截图文件不存在，请重新截图后再试。")
            self.ai_parse_button.setEnabled(False)
            self._set_status("截图文件不存在，无法继续 AI 解析", is_error=True)
            self._logger.warning("OCR 对照窗口加载失败，图片不存在: %s", self._image_path)
            return

        pixmap = QPixmap(str(image_file))
        if pixmap.isNull():
            self.preview_label.setText("截图读取失败，请重新截图后再试。")
            self.ai_parse_button.setEnabled(False)
            self._set_status("截图读取失败，无法继续 AI 解析", is_error=True)
            self._logger.warning("OCR 对照窗口加载失败，图片无法读取: %s", self._image_path)
            return

        self._source_pixmap = pixmap
        self._render_preview_pixmap()
        self._set_status("OCR 识别完成，请校对文本后点击 AI解析")

    def _render_preview_pixmap(self) -> None:
        """按当前窗口尺寸刷新图片显示。"""
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
            "刷新 OCR 对照图，source=%sx%s,target=%sx%s,render=%sx%s",
            self._source_pixmap.width(),
            self._source_pixmap.height(),
            target_size.width(),
            target_size.height(),
            scaled.width(),
            scaled.height(),
        )

    def resizeEvent(self, event) -> None:
        """窗口缩放时同步刷新预览图。"""
        super().resizeEvent(event)
        self._render_preview_pixmap()

    def _on_ai_parse_clicked(self) -> None:
        """点击 AI 解析后发送编辑后的 OCR 文本。"""
        ocr_text = self.ocr_text_edit.toPlainText().strip()
        if not ocr_text:
            self._set_status("OCR 文本不能为空，请先补充文本后重试", is_error=True)
            self._logger.warning("AI解析触发失败：OCR 文本为空")
            return

        self._logger.debug("提交 AI 解析请求，ocr_len=%s", len(ocr_text))
        self.ai_parse_requested.emit(ocr_text)

    def show_stage(self, stage_text: str) -> None:
        """显示处理中阶段并禁止重复触发。"""
        self.ai_parse_button.setEnabled(False)
        self._set_status(f"{stage_text}...")

    def allow_retry(self, message: str) -> None:
        """失败后恢复为可重试状态。"""
        self.ai_parse_button.setEnabled(True)
        self._set_status(message, is_error=True)

    def mark_ai_complete(self, message: str) -> None:
        """AI 完成后的状态展示。"""
        self.ai_parse_button.setEnabled(True)
        self._set_status(message)
