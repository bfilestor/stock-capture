"""截图前置工作流服务。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QDialog, QWidget

from services.ai_service import AIService
from services.analysis_pipeline_service import AnalysisPipelineService
from services.config_service import ConfigService
from services.ocr_service import OCRService
from ui.capture.capture_overlay import CaptureOverlay
from ui.capture.capture_preview_dialog import CapturePreviewDialog
from ui.capture.capture_type_selector_dialog import CaptureTypeSelectorDialog
from ui.result.result_confirm_dialog import ResultConfirmDialog
from utils.logging_config import get_logger
from workers.capture_context import CaptureContext


class CaptureWorkflowService:
    """负责截图入口选择与上下文维护。"""

    def __init__(
        self,
        config_service: ConfigService,
        parent: QWidget | None = None,
        dialog_factory: Callable[[list[dict], QWidget | None], QDialog] | None = None,
        overlay_factory: Callable[[QWidget | None], CaptureOverlay] | None = None,
        preview_factory: Callable[[str, str, QWidget | None], QDialog] | None = None,
        result_dialog_factory: Callable[[str, str, str, QWidget | None], QDialog] | None = None,
        on_parse_requested: Callable[[CaptureContext], None] | None = None,
        analysis_pipeline: AnalysisPipelineService | None = None,
    ) -> None:
        """初始化截图工作流服务。"""
        self._logger = get_logger(__name__)
        self._config_service = config_service
        self._parent = parent
        self._dialog_factory = dialog_factory or (
            lambda capture_types, parent: CaptureTypeSelectorDialog(capture_types, parent)
        )
        self._overlay_factory = overlay_factory or (lambda parent: CaptureOverlay(parent=parent))
        self._preview_factory = preview_factory or (
            lambda image_path, capture_type_name, parent: CapturePreviewDialog(
                image_path=image_path, capture_type_name=capture_type_name, parent=parent
            )
        )
        self._result_dialog_factory = result_dialog_factory or (
            lambda capture_type_name, ocr_text, ai_text, parent: ResultConfirmDialog(
                capture_type_name=capture_type_name,
                ocr_text=ocr_text,
                ai_text=ai_text,
                parent=parent,
            )
        )
        self._on_parse_requested = on_parse_requested
        self._analysis_pipeline = analysis_pipeline or AnalysisPipelineService(
            ocr_service=OCRService(),
            ai_service=AIService(config_service),
        )
        self.context = CaptureContext()
        self._overlay: CaptureOverlay | None = None
        self._preview_dialog: QDialog | None = None
        self._result_dialog: QDialog | None = None

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
        self.context.state = "capturing"
        self._logger.debug(
            "截图上下文已更新，capture_type_id=%s, capture_type_name=%s",
            self.context.capture_type_id,
            self.context.capture_type_name,
        )
        return True, "业务类型选择成功"

    def start_capture_overlay(self) -> None:
        """进入自由截图遮罩。"""
        self._overlay = self._overlay_factory(self._parent)
        self._overlay.capture_completed.connect(self._on_capture_completed)
        self._overlay.capture_cancelled.connect(self._on_capture_cancelled)
        self._overlay.capture_error.connect(self._on_capture_error)
        self._overlay.showFullScreen()
        self._overlay.activateWindow()
        self._logger.debug("已进入截图遮罩状态")

    def _on_capture_completed(self, image_path: str) -> None:
        """处理截图完成事件。"""
        self.context.image_path = image_path
        self.context.state = "previewing"
        self._logger.debug("截图完成，image_path=%s", image_path)
        self._open_preview_dialog()

    def _on_capture_cancelled(self) -> None:
        """处理截图取消事件。"""
        self.context.state = "idle"
        self._logger.debug("截图已取消，状态恢复为 idle")

    def _on_capture_error(self, message: str) -> None:
        """处理截图错误事件。"""
        self.context.state = "capturing"
        self._logger.warning("截图错误: %s", message)

    def _open_preview_dialog(self) -> None:
        """打开截图预览窗口。"""
        self._preview_dialog = self._preview_factory(
            self.context.image_path, self.context.capture_type_name, self._parent
        )
        if hasattr(self._preview_dialog, "retake_requested"):
            self._preview_dialog.retake_requested.connect(self._on_retake_requested)  # type: ignore[attr-defined]
        if hasattr(self._preview_dialog, "send_requested"):
            self._preview_dialog.send_requested.connect(self._on_send_requested)  # type: ignore[attr-defined]
        self._preview_dialog.show()
        self._preview_dialog.activateWindow()
        self._logger.debug("截图预览窗口已打开")

    def _remove_temp_image(self) -> None:
        """删除当前临时截图。"""
        if not self.context.image_path:
            return
        image_path = Path(self.context.image_path)
        if image_path.exists():
            image_path.unlink()
            self._logger.debug("已清理旧截图文件: %s", image_path)

    def _on_retake_requested(self) -> None:
        """处理重截流程。"""
        self._logger.debug("收到重截请求，准备重新进入截图")
        self._remove_temp_image()
        self.context.image_path = ""
        self.context.state = "capturing"
        self.start_capture_overlay()

    def _on_send_requested(self, image_path: str) -> None:
        """处理发送解析入口。"""
        if self.context.capture_type_id is None:
            self._logger.warning("发送解析失败：capture_type_id 为空")
            return
        if self._analysis_pipeline.is_running():
            self._show_preview_retry("解析进行中，请勿重复点击发送解析")
            return

        capture_type = self._config_service.get_capture_type(self.context.capture_type_id)
        prompt = str(capture_type.get("prompt_template", "")).strip()
        if not prompt:
            self._show_preview_retry("当前业务类型未配置 PromptTemplate")
            return

        self.context.image_path = image_path
        self.context.state = "ocr_processing"
        self._show_preview_stage("OCR识别中")

        started = self._analysis_pipeline.start_analysis(
            image_path=image_path,
            prompt=prompt,
            on_stage=self._on_pipeline_stage,
            on_success=self._on_pipeline_success,
            on_error=self._on_pipeline_error,
        )
        if not started:
            self._show_preview_retry("解析进行中，请勿重复点击发送解析")

    def _on_pipeline_stage(self, stage_text: str) -> None:
        """处理异步阶段更新。"""
        if stage_text == "OCR识别中":
            self.context.state = "ocr_processing"
        elif stage_text == "AI分析中":
            self.context.state = "ai_processing"
        self._show_preview_stage(stage_text)

    def _on_pipeline_success(self, ocr_text: str, ai_content: str, ai_raw_text: str) -> None:
        """处理解析成功。"""
        self.context.ocr_text = ocr_text
        self.context.ai_content = ai_content
        self.context.ai_raw_response = ai_raw_text
        self.context.state = "editing"
        self._show_preview_complete("解析完成，准备进入结果确认")
        self._open_result_dialog()
        if self._on_parse_requested is not None:
            self._on_parse_requested(self.context)

    def _on_pipeline_error(self, code: str, message: str) -> None:
        """处理解析失败。"""
        self.context.state = "failed"
        self._show_preview_retry(f"解析失败：{code} - {message}")

    def _show_preview_stage(self, stage: str) -> None:
        """更新预览窗口阶段提示。"""
        if self._preview_dialog is not None and hasattr(self._preview_dialog, "show_stage"):
            self._preview_dialog.show_stage(stage)  # type: ignore[attr-defined]

    def _show_preview_retry(self, message: str) -> None:
        """更新预览窗口为可重试状态。"""
        if self._preview_dialog is not None and hasattr(self._preview_dialog, "allow_retry"):
            self._preview_dialog.allow_retry(message)  # type: ignore[attr-defined]
        else:
            self._logger.warning(message)

    def _show_preview_complete(self, message: str) -> None:
        """更新预览窗口完成提示。"""
        if self._preview_dialog is not None and hasattr(self._preview_dialog, "mark_send_complete"):
            self._preview_dialog.mark_send_complete(message)  # type: ignore[attr-defined]
        else:
            self._logger.debug(message)

    def _open_result_dialog(self) -> None:
        """打开结果确认窗口。"""
        self._result_dialog = self._result_dialog_factory(
            self.context.capture_type_name,
            self.context.ocr_text,
            self.context.ai_content,
            self._parent,
        )
        if hasattr(self._result_dialog, "save_requested"):
            self._result_dialog.save_requested.connect(self._on_result_save_requested)  # type: ignore[attr-defined]
        self._result_dialog.show()
        self._result_dialog.activateWindow()
        self._logger.debug("结果确认窗口已打开")

    def _on_result_save_requested(self, result_date: str, json_text: str) -> None:
        """处理结果窗口的入库请求（E5-S2-I1 将接入数据库写入）。"""
        self._logger.debug(
            "收到入库请求，result_date=%s, json_len=%s", result_date, len(json_text)
        )
        if self._result_dialog is not None and hasattr(self._result_dialog, "set_status"):
            self._result_dialog.set_status("入库功能将在后续 Issue 完整实现")  # type: ignore[attr-defined]
