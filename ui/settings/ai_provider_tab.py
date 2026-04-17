"""设置窗口 Tab2：AI 供应商与模型管理。"""

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
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from services.config_service import (
    AIModelPayload,
    AIProviderPayload,
    ConfigService,
    ConfigValidationError,
)
from utils.logging_config import get_logger


class AIProviderTab(QWidget):
    """AI 供应商与模型管理页。"""

    def __init__(self, config_service: ConfigService, parent: QWidget | None = None) -> None:
        """初始化 AI 配置页。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._service = config_service
        self._current_provider_id: int | None = None
        self._current_model_id: int | None = None
        self._init_ui()
        self.reload_provider_list()

    def _init_ui(self) -> None:
        """构建页面布局。"""
        root_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal, self)
        root_layout.addWidget(splitter, 1)

        # 供应商区域
        provider_panel = QWidget(self)
        provider_layout = QVBoxLayout(provider_panel)
        provider_layout.addWidget(QLabel("供应商列表", self))

        self.provider_list = QListWidget(self)
        self.provider_list.itemSelectionChanged.connect(self._on_provider_selected)
        provider_layout.addWidget(self.provider_list, 1)

        self.provider_name_edit = QLineEdit(self)
        self.provider_url_edit = QLineEdit(self)
        self.provider_key_edit = QLineEdit(self)
        self.provider_key_edit.setEchoMode(QLineEdit.Password)
        self.provider_enabled_checkbox = QCheckBox("启用供应商", self)
        self.provider_enabled_checkbox.setChecked(True)
        self.provider_default_checkbox = QCheckBox("设为默认供应商", self)
        self.provider_key_toggle_button = QPushButton("显示Key", self)
        self.provider_test_button = QPushButton("测试连接", self)

        provider_form = QFormLayout()
        provider_form.addRow("供应商名称*", self.provider_name_edit)
        provider_form.addRow("API Base URL*", self.provider_url_edit)
        provider_form.addRow("API Key", self.provider_key_edit)
        provider_form.addRow("", self.provider_enabled_checkbox)
        provider_form.addRow("", self.provider_default_checkbox)
        provider_layout.addLayout(provider_form)

        provider_button_layout = QHBoxLayout()
        self.provider_new_button = QPushButton("新增供应商", self)
        self.provider_save_button = QPushButton("保存供应商", self)
        self.provider_delete_button = QPushButton("删除供应商", self)
        provider_button_layout.addWidget(self.provider_new_button)
        provider_button_layout.addWidget(self.provider_save_button)
        provider_button_layout.addWidget(self.provider_delete_button)
        provider_button_layout.addWidget(self.provider_key_toggle_button)
        provider_button_layout.addWidget(self.provider_test_button)
        provider_layout.addLayout(provider_button_layout)

        splitter.addWidget(provider_panel)

        # 模型区域
        model_panel = QWidget(self)
        model_layout = QVBoxLayout(model_panel)
        model_layout.addWidget(QLabel("模型列表", self))

        self.model_list = QListWidget(self)
        self.model_list.itemSelectionChanged.connect(self._on_model_selected)
        model_layout.addWidget(self.model_list, 1)

        self.model_code_edit = QLineEdit(self)
        self.model_name_edit = QLineEdit(self)
        self.model_enabled_checkbox = QCheckBox("启用模型", self)
        self.model_enabled_checkbox.setChecked(True)
        self.model_default_checkbox = QCheckBox("设为默认模型", self)

        model_form = QFormLayout()
        model_form.addRow("模型标识*", self.model_code_edit)
        model_form.addRow("模型名称*", self.model_name_edit)
        model_form.addRow("", self.model_enabled_checkbox)
        model_form.addRow("", self.model_default_checkbox)
        model_layout.addLayout(model_form)

        model_button_layout = QHBoxLayout()
        self.model_new_button = QPushButton("新增模型", self)
        self.model_save_button = QPushButton("保存模型", self)
        self.model_delete_button = QPushButton("删除模型", self)
        self.model_set_default_button = QPushButton("设为默认", self)
        model_button_layout.addWidget(self.model_new_button)
        model_button_layout.addWidget(self.model_save_button)
        model_button_layout.addWidget(self.model_delete_button)
        model_button_layout.addWidget(self.model_set_default_button)
        model_layout.addLayout(model_button_layout)

        splitter.addWidget(model_panel)
        splitter.setSizes([470, 470])

        self.status_label = QLabel("准备就绪", self)
        self.status_label.setWordWrap(True)
        root_layout.addWidget(self.status_label)

        self.provider_new_button.clicked.connect(self.new_provider)
        self.provider_save_button.clicked.connect(self.save_provider)
        self.provider_delete_button.clicked.connect(self.delete_provider)
        self.provider_key_toggle_button.clicked.connect(self.toggle_key_visibility)
        self.provider_test_button.clicked.connect(self.test_connection)
        self.model_new_button.clicked.connect(self.new_model)
        self.model_save_button.clicked.connect(self.save_model)
        self.model_delete_button.clicked.connect(self.delete_model)
        self.model_set_default_button.clicked.connect(self.set_model_default)

    def _provider_text(self, row: dict[str, Any]) -> str:
        """生成供应商列表文本。"""
        enabled = "启用" if int(row.get("is_enabled", 0)) == 1 else "禁用"
        is_default = "默认" if int(row.get("is_default", 0)) == 1 else "-"
        return f"{row.get('name', '')} | {enabled} | {is_default}"

    def _model_text(self, row: dict[str, Any]) -> str:
        """生成模型列表文本。"""
        enabled = "启用" if int(row.get("is_enabled", 0)) == 1 else "禁用"
        is_default = "默认" if int(row.get("is_default", 0)) == 1 else "-"
        return f"{row.get('model_name', '')} ({row.get('model_code', '')}) | {enabled} | {is_default}"

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """更新状态提示。"""
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)
        if is_error:
            self._logger.warning("AI配置页提示: %s", message)
        else:
            self._logger.debug("AI配置页提示: %s", message)

    def reload_provider_list(self) -> None:
        """刷新供应商列表。"""
        providers = self._service.list_providers()
        self.provider_list.clear()
        for provider in providers:
            item = QListWidgetItem(self._provider_text(provider))
            item.setData(Qt.UserRole, provider)
            self.provider_list.addItem(item)

        if providers:
            self.provider_list.setCurrentRow(0)
        else:
            self.new_provider()
            self.model_list.clear()

    def reload_model_list(self) -> None:
        """刷新模型列表。"""
        self.model_list.clear()
        if self._current_provider_id is None:
            return
        models = self._service.list_models(self._current_provider_id)
        for model in models:
            item = QListWidgetItem(self._model_text(model))
            item.setData(Qt.UserRole, model)
            self.model_list.addItem(item)
        if models:
            self.model_list.setCurrentRow(0)
        else:
            self.new_model()

    def new_provider(self) -> None:
        """切换到新增供应商模式。"""
        self._current_provider_id = None
        self.provider_name_edit.clear()
        self.provider_url_edit.clear()
        self.provider_key_edit.clear()
        self.provider_key_edit.setEchoMode(QLineEdit.Password)
        self.provider_key_toggle_button.setText("显示Key")
        self.provider_enabled_checkbox.setChecked(True)
        self.provider_default_checkbox.setChecked(False)
        self.provider_list.clearSelection()
        self._set_status("已切换到新增供应商模式")

    def new_model(self) -> None:
        """切换到新增模型模式。"""
        self._current_model_id = None
        self.model_code_edit.clear()
        self.model_name_edit.clear()
        self.model_enabled_checkbox.setChecked(True)
        self.model_default_checkbox.setChecked(False)
        self.model_list.clearSelection()
        self._set_status("已切换到新增模型模式")

    def _on_provider_selected(self) -> None:
        """处理供应商选中。"""
        selected_items = self.provider_list.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].data(Qt.UserRole)
        if not isinstance(row, dict):
            return
        self._current_provider_id = int(row["id"])
        self.provider_name_edit.setText(str(row.get("name", "")))
        self.provider_url_edit.setText(str(row.get("api_base_url", "")))
        self.provider_key_edit.setText(str(row.get("api_key", "")))
        self.provider_key_edit.setEchoMode(QLineEdit.Password)
        self.provider_key_toggle_button.setText("显示Key")
        self.provider_enabled_checkbox.setChecked(int(row.get("is_enabled", 0)) == 1)
        self.provider_default_checkbox.setChecked(int(row.get("is_default", 0)) == 1)
        self._set_status("已加载供应商详情")
        self.reload_model_list()

    def _on_model_selected(self) -> None:
        """处理模型选中。"""
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].data(Qt.UserRole)
        if not isinstance(row, dict):
            return
        self._current_model_id = int(row["id"])
        self.model_code_edit.setText(str(row.get("model_code", "")))
        self.model_name_edit.setText(str(row.get("model_name", "")))
        self.model_enabled_checkbox.setChecked(int(row.get("is_enabled", 0)) == 1)
        self.model_default_checkbox.setChecked(int(row.get("is_default", 0)) == 1)
        self._set_status("已加载模型详情")

    def save_provider(self) -> bool:
        """保存供应商。"""
        payload = AIProviderPayload(
            name=self.provider_name_edit.text(),
            api_base_url=self.provider_url_edit.text(),
            api_key=self.provider_key_edit.text(),
            is_enabled=self.provider_enabled_checkbox.isChecked(),
            is_default=self.provider_default_checkbox.isChecked(),
        )
        try:
            message = ""
            if self._current_provider_id is None:
                provider_id = self._service.create_provider(payload)
                self._logger.debug("新增供应商成功，id=%s", provider_id)
                message = "保存成功：已新增供应商"
            else:
                self._service.update_provider(self._current_provider_id, payload)
                self._logger.debug("更新供应商成功，id=%s", self._current_provider_id)
                message = "保存成功：已更新供应商"
            self.reload_provider_list()
            self._set_status(message)
            return True
        except ConfigValidationError as exc:
            self._set_status(str(exc), is_error=True)
            return False
        except Exception as exc:  # pragma: no cover
            self._logger.exception("保存供应商失败")
            self._set_status(f"保存供应商失败：{exc}", is_error=True)
            return False

    def delete_provider(self) -> bool:
        """删除当前供应商。"""
        if self._current_provider_id is None:
            self._set_status("请先选择供应商", is_error=True)
            return False
        self._service.delete_provider(self._current_provider_id)
        self._logger.debug("删除供应商成功，id=%s", self._current_provider_id)
        self.new_provider()
        self.reload_provider_list()
        self._set_status("供应商删除成功")
        return True

    def save_model(self) -> bool:
        """保存模型。"""
        if self._current_provider_id is None:
            self._set_status("请先选择供应商后再维护模型", is_error=True)
            return False
        payload = AIModelPayload(
            model_code=self.model_code_edit.text(),
            model_name=self.model_name_edit.text(),
            is_enabled=self.model_enabled_checkbox.isChecked(),
            is_default=self.model_default_checkbox.isChecked(),
        )
        try:
            message = ""
            if self._current_model_id is None:
                model_id = self._service.create_model(self._current_provider_id, payload)
                self._logger.debug("新增模型成功，id=%s", model_id)
                message = "保存成功：已新增模型"
            else:
                self._service.update_model(self._current_model_id, self._current_provider_id, payload)
                self._logger.debug("更新模型成功，id=%s", self._current_model_id)
                message = "保存成功：已更新模型"
            self.reload_model_list()
            self._set_status(message)
            return True
        except ConfigValidationError as exc:
            self._set_status(str(exc), is_error=True)
            return False
        except Exception as exc:  # pragma: no cover
            self._logger.exception("保存模型失败")
            self._set_status(f"保存模型失败：{exc}", is_error=True)
            return False

    def delete_model(self) -> bool:
        """删除当前模型。"""
        if self._current_model_id is None:
            self._set_status("请先选择模型", is_error=True)
            return False
        self._service.delete_model(self._current_model_id)
        self._logger.debug("删除模型成功，id=%s", self._current_model_id)
        self.new_model()
        self.reload_model_list()
        self._set_status("模型删除成功")
        return True

    def set_model_default(self) -> bool:
        """设置当前模型为默认模型。"""
        if self._current_model_id is None:
            self._set_status("请先选择模型", is_error=True)
            return False
        try:
            self._service.set_default_model(self._current_model_id)
            self.reload_model_list()
            self._set_status("默认模型设置成功")
            return True
        except ConfigValidationError as exc:
            self._set_status(str(exc), is_error=True)
            return False

    def toggle_key_visibility(self) -> None:
        """切换 API Key 明文显示状态。"""
        if self.provider_key_edit.echoMode() == QLineEdit.Password:
            self.provider_key_edit.setEchoMode(QLineEdit.Normal)
            self.provider_key_toggle_button.setText("隐藏Key")
            self._set_status("已显示 API Key（注意信息安全）")
        else:
            self.provider_key_edit.setEchoMode(QLineEdit.Password)
            self.provider_key_toggle_button.setText("显示Key")
            self._set_status("已隐藏 API Key")

    def test_connection(self) -> bool:
        """测试当前供应商连接。"""
        if self._current_provider_id is None:
            self._set_status("请先保存并选择供应商后再测试连接", is_error=True)
            return False
        try:
            result = self._service.test_provider_connection(self._current_provider_id)
            code = result.get("code", "")
            message = result.get("message", "")
            if code == "OK":
                self._set_status(f"测试连接成功：{message}")
                return True
            self._set_status(f"测试连接失败：{code} - {message}", is_error=True)
            return False
        except ConfigValidationError as exc:
            self._set_status(f"测试连接失败：{exc}", is_error=True)
            return False
