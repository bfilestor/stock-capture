"""E6-S1-I1 统一异常提示测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from services.errors import ServiceError
from ui.capture.capture_preview_dialog import CapturePreviewDialog
from utils.error_presenter import to_error_view


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e6_s1_i1_01_ocr失败提示统一格式并恢复按钮(app: QApplication) -> None:
    """功能测试：统一错误格式可见，且失败后可恢复可重试状态。"""
    error_view = to_error_view(ServiceError("OCR_001", "连接失败"))
    assert error_view.to_dict() == {"code": "OCR_001", "message": "连接失败"}
    assert error_view.to_ui_text() == "[OCR_001] 连接失败"

    dialog = CapturePreviewDialog(image_path="missing.png", capture_type_name="市场动态")
    dialog.show_stage("OCR识别中")
    assert dialog.send_button.isEnabled() is False
    dialog.allow_retry(error_view.to_ui_text())
    assert dialog.send_button.isEnabled() is True
    assert "[OCR_001]" in dialog.status_label.text()


def test_bt_e6_s1_i1_01_超长异常信息裁剪与脱敏() -> None:
    """边界测试：超长错误信息会裁剪且隐藏敏感Key。"""
    long_message = "错误-" + ("x" * 300)
    view = to_error_view(ServiceError("AI_001", long_message), max_message_length=80)

    assert len(view.message) <= 80
    assert view.message.endswith("...")

    sensitive_view = to_error_view(
        ServiceError("AI_001", "请求失败，key=sk-1234567890ABCDEF"),
        max_message_length=80,
    )
    assert "sk-1234567890ABCDEF" not in sensitive_view.message
    assert "sk-***" in sensitive_view.message
