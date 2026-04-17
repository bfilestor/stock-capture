"""截图前置工作流服务。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QDialog, QWidget

from services.config_service import ConfigService
from ui.capture.capture_type_selector_dialog import CaptureTypeSelectorDialog
from utils.logging_config import get_logger
from workers.capture_context import CaptureContext


class CaptureWorkflowService:
    """负责截图入口选择与上下文维护。"""

    def __init__(
        self,
        config_service: ConfigService,
        parent: QWidget | None = None,
        dialog_factory: Callable[[list[dict], QWidget | None], QDialog] | None = None,
    ) -> None:
        """初始化截图工作流服务。"""
        self._logger = get_logger(__name__)
        self._config_service = config_service
        self._parent = parent
        self._dialog_factory = dialog_factory or (
            lambda capture_types, parent: CaptureTypeSelectorDialog(capture_types, parent)
        )
        self.context = CaptureContext()

    def select_capture_type(self) -> tuple[bool, str]:
        """打开业务类型面板并写入上下文。"""
        enabled_capture_types = self._config_service.list_enabled_capture_types()
        self._logger.debug("准备打开业务类型面板，启用数量=%s", len(enabled_capture_types))
        if not enabled_capture_types:
            self._logger.warning("没有启用业务类型，停止截图流程")
            return False, "请先在设置中启用至少一个业务类型"

        dialog = self._dialog_factory(enabled_capture_types, self._parent)
        result = dialog.exec()
        if result != QDialog.Accepted:
            self._logger.debug("用户取消业务类型选择")
            return False, "已取消选择业务类型"

        selected = getattr(dialog, "selected_capture_type", None)
        if not isinstance(selected, dict):
            self._logger.warning("业务类型选择结果为空")
            return False, "未选择业务类型"

        self.context.capture_type_id = int(selected["id"])
        self.context.capture_type_name = str(selected["name"])
        self._logger.debug(
            "截图上下文已更新，capture_type_id=%s, capture_type_name=%s",
            self.context.capture_type_id,
            self.context.capture_type_name,
        )
        return True, "业务类型选择成功"

