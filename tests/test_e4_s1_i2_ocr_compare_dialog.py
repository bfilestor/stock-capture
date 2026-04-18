"""E4-S1-I2 OCR 对照预览窗口测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from ui.capture.ocr_compare_dialog import OCRCompareDialog


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def _create_image_file(path: Path) -> str:
    """生成测试图片文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(120, 90, QImage.Format_ARGB32)
    image.fill(0xFF1976D2)
    assert image.save(str(path), "PNG")
    return str(path)


def test_ft_e4_s1_i2_01_图片与ocr可对照且允许编辑(app: QApplication, tmp_path: Path) -> None:
    """功能测试：显示截图与 OCR 内容，并透传编辑后的文本。"""
    image_path = _create_image_file(tmp_path / "ocr_compare.png")
    dialog = OCRCompareDialog(
        image_path=image_path,
        capture_type_name="市场动态",
        ocr_text="初始OCR文本",
    )

    emitted_text: list[str] = []
    dialog.ai_parse_requested.connect(lambda text: emitted_text.append(text))
    assert dialog.ocr_text_edit.toPlainText() == "初始OCR文本"
    dialog.ocr_text_edit.setPlainText("修正后的 OCR 文本")
    dialog.ai_parse_button.click()

    assert dialog.windowTitle() == "OCR 对照确认"
    assert emitted_text == ["修正后的 OCR 文本"]


def test_bt_e4_s1_i2_01_ocr为空时不允许触发ai(app: QApplication, tmp_path: Path) -> None:
    """边界测试：OCR 文本为空时不触发 AI 请求。"""
    image_path = _create_image_file(tmp_path / "ocr_compare_empty.png")
    dialog = OCRCompareDialog(
        image_path=image_path,
        capture_type_name="市场总览",
        ocr_text="",
    )
    emitted_text: list[str] = []
    dialog.ai_parse_requested.connect(lambda text: emitted_text.append(text))

    dialog.ocr_text_edit.setPlainText("   ")
    dialog.ai_parse_button.click()

    assert emitted_text == []
    assert "不能为空" in dialog.status_label.text()
