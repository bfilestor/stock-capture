"""结果确认窗口。"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QDialog,
)

from services.errors import ServiceError
from services.result_service import ResultService
from utils.logging_config import get_logger


class ResultConfirmDialog(QDialog):
    """展示 OCR 与 AI 结果，并支持用户编辑确认。"""

    save_requested = Signal(str, str)

    def __init__(
        self,
        capture_type_name: str,
        ocr_text: str,
        ai_text: str,
        result_service: ResultService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """初始化结果确认窗口。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._capture_type_name = capture_type_name
        self._ocr_text = ocr_text
        self._ai_text = ai_text
        self._result_service = result_service or ResultService()
        self.setWindowTitle("结果确认")
        self.resize(900, 680)
        self._init_ui()

    def _init_ui(self) -> None:
        """构建结果确认页面。"""
        layout = QVBoxLayout(self)

        self.capture_type_label = QLabel(f"业务类型：{self._capture_type_name}", self)
        layout.addWidget(self.capture_type_label)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("结果日期：", self))
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch(1)
        layout.addLayout(date_layout)

        self.ocr_toggle_button = QToolButton(self)
        self.ocr_toggle_button.setText("显示 OCR 原文")
        self.ocr_toggle_button.setCheckable(True)
        self.ocr_toggle_button.setChecked(False)
        self.ocr_toggle_button.toggled.connect(self._toggle_ocr_area)
        layout.addWidget(self.ocr_toggle_button)

        self.ocr_text_edit = QPlainTextEdit(self)
        self.ocr_text_edit.setReadOnly(True)
        self.ocr_text_edit.setPlainText(self._ocr_text)
        self.ocr_text_edit.setVisible(False)
        self.ocr_text_edit.setMinimumHeight(180)
        layout.addWidget(self.ocr_text_edit)

        layout.addWidget(QLabel("AI 结果（可编辑）：", self))
        self.ai_text_edit = QPlainTextEdit(self)
        self.ai_text_edit.setPlainText(self._ai_text)
        self.ai_text_edit.setMinimumHeight(260)
        layout.addWidget(self.ai_text_edit, 1)

        button_layout = QHBoxLayout()
        self.format_button = QPushButton("格式化JSON", self)
        self.save_button = QPushButton("入库", self)
        button_layout.addWidget(self.format_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.status_label = QLabel("请确认结果后入库", self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.save_button.clicked.connect(self._on_save_clicked)
        self.format_button.clicked.connect(self._on_format_clicked)

    def _toggle_ocr_area(self, checked: bool) -> None:
        """切换 OCR 折叠区域显示状态。"""
        self.ocr_text_edit.setVisible(checked)
        self.ocr_toggle_button.setText("隐藏 OCR 原文" if checked else "显示 OCR 原文")

    def _on_save_clicked(self) -> None:
        """触发入库请求信号。"""
        result_date = self.date_edit.date().toString("yyyy-MM-dd")
        json_text = self.ai_text_edit.toPlainText()
        try:
            self._result_service.validate_json_text(json_text)
            self._logger.debug("点击入库，result_date=%s, json_len=%s", result_date, len(json_text))
            self.save_requested.emit(result_date, json_text)
        except ServiceError as exc:
            self.set_status(str(exc), is_error=True)

    def _on_format_clicked(self) -> None:
        """格式化 JSON 内容。"""
        json_text = self.ai_text_edit.toPlainText()
        try:
            formatted = self._result_service.format_json_text(json_text)
            self.ai_text_edit.setPlainText(formatted)
            self.set_status("JSON 格式化成功")
        except ServiceError as exc:
            self.set_status(str(exc), is_error=True)

    def current_date_text(self) -> str:
        """返回当前选择日期字符串。"""
        return self.date_edit.date().toString("yyyy-MM-dd")

    def set_status(self, message: str, is_error: bool = False) -> None:
        """更新状态提示。"""
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)

    @staticmethod
    def today_text() -> str:
        """返回当天日期（yyyy-MM-dd）。"""
        return date.today().strftime("%Y-%m-%d")
