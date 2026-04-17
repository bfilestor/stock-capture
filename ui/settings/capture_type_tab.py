"""设置窗口 Tab1：业务类型管理。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from services.config_service import CaptureTypePayload, ConfigService, ConfigValidationError
from utils.logging_config import get_logger


class CaptureTypeTab(QWidget):
    """业务类型配置 Tab。"""

    def __init__(self, config_service: ConfigService, parent: QWidget | None = None) -> None:
        """初始化业务类型管理页面。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._service = config_service
        self._current_id: int | None = None
        self._init_ui()
        self.reload_list()

    def _init_ui(self) -> None:
        """初始化界面。"""
        root_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal, self)
        root_layout.addWidget(splitter, 1)

        self.list_widget = QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self._on_item_selected)
        splitter.addWidget(self.list_widget)

        form_container = QWidget(self)
        form_layout = QVBoxLayout(form_container)

        self.name_edit = QLineEdit(self)
        self.description_edit = QPlainTextEdit(self)
        self.prompt_edit = QPlainTextEdit(self)
        self.prompt_edit.setPlaceholderText("请输入 PromptTemplate（支持多行）")
        self.enabled_checkbox = QCheckBox("启用", self)
        self.enabled_checkbox.setChecked(True)

        form = QFormLayout()
        form.addRow("业务类型名称*", self.name_edit)
        form.addRow("描述", self.description_edit)
        form.addRow("PromptTemplate*", self.prompt_edit)
        form.addRow("状态", self.enabled_checkbox)
        form_layout.addLayout(form)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton("新增", self)
        self.save_button = QPushButton("保存", self)
        self.delete_button = QPushButton("删除", self)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        form_layout.addLayout(button_layout)

        self.status_label = QLabel("准备就绪", self)
        self.status_label.setWordWrap(True)
        form_layout.addWidget(self.status_label)
        form_layout.addStretch(1)

        splitter.addWidget(form_container)
        splitter.setSizes([280, 620])

        self.new_button.clicked.connect(self.new_capture_type)
        self.save_button.clicked.connect(self.save_current_capture_type)
        self.delete_button.clicked.connect(self.delete_current_capture_type)

    def _item_text(self, item: dict[str, Any]) -> str:
        """生成列表显示文本。"""
        enabled_text = "启用" if int(item.get("is_enabled", 0)) == 1 else "禁用"
        updated_at = item.get("updated_at", "")
        return f"{item['name']} | {enabled_text} | {updated_at}"

    def reload_list(self) -> None:
        """刷新业务类型列表。"""
        self.list_widget.clear()
        records = self._service.list_capture_types()
        self._logger.debug("刷新业务类型列表，数量=%s", len(records))
        for record in records:
            item = QListWidgetItem(self._item_text(record))
            item.setData(Qt.UserRole, record)
            self.list_widget.addItem(item)
        if records:
            self.list_widget.setCurrentRow(0)
        else:
            self.new_capture_type()

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """更新状态文本。"""
        self.status_label.setText(message)
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color: {color};")
        if is_error:
            self._logger.warning("业务类型页面提示: %s", message)
        else:
            self._logger.debug("业务类型页面提示: %s", message)

    def _read_form(self) -> CaptureTypePayload:
        """读取表单内容。"""
        return CaptureTypePayload(
            name=self.name_edit.text(),
            description=self.description_edit.toPlainText(),
            prompt_template=self.prompt_edit.toPlainText(),
            is_enabled=self.enabled_checkbox.isChecked(),
        )

    def _fill_form(self, record: dict[str, Any]) -> None:
        """将记录写入表单。"""
        self._current_id = int(record["id"])
        self.name_edit.setText(str(record.get("name", "")))
        self.description_edit.setPlainText(str(record.get("description", "")))
        self.prompt_edit.setPlainText(str(record.get("prompt_template", "")))
        self.enabled_checkbox.setChecked(int(record.get("is_enabled", 0)) == 1)

    def _on_item_selected(self) -> None:
        """处理列表项选中事件。"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        record = selected_items[0].data(Qt.UserRole)
        if isinstance(record, dict):
            self._fill_form(record)
            self._set_status("已加载业务类型详情")

    def new_capture_type(self) -> None:
        """切换到新增模式。"""
        self._current_id = None
        self.name_edit.clear()
        self.description_edit.clear()
        self.prompt_edit.clear()
        self.enabled_checkbox.setChecked(True)
        self.list_widget.clearSelection()
        self._set_status("已切换到新增模式")

    def save_current_capture_type(self) -> bool:
        """保存当前业务类型。"""
        payload = self._read_form()
        try:
            success_message = ""
            if self._current_id is None:
                capture_type_id = self._service.create_capture_type(payload)
                self._logger.debug("新增业务类型成功，id=%s", capture_type_id)
                success_message = "保存成功：已新增业务类型"
            else:
                self._service.update_capture_type(self._current_id, payload)
                self._logger.debug("更新业务类型成功，id=%s", self._current_id)
                success_message = "保存成功：已更新业务类型"
            self.reload_list()
            self._set_status(success_message)
            return True
        except ConfigValidationError as exc:
            self._set_status(str(exc), is_error=True)
            return False
        except Exception as exc:  # pragma: no cover - 异常兜底分支
            self._logger.exception("保存业务类型失败")
            self._set_status(f"保存失败：{exc}", is_error=True)
            return False

    def delete_current_capture_type(self) -> bool:
        """删除当前选中的业务类型。"""
        if self._current_id is None:
            self._set_status("请先选择要删除的业务类型", is_error=True)
            return False

        answer = QMessageBox.question(
            self,
            "确认删除",
            "确定删除当前业务类型吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self._set_status("已取消删除")
            return False

        self._service.delete_capture_type(self._current_id)
        self._logger.debug("删除业务类型成功，id=%s", self._current_id)
        self.new_capture_type()
        self.reload_list()
        self._set_status("删除成功")
        return True
