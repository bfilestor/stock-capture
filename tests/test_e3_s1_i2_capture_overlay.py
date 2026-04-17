"""E3-S1-I2 自由截图遮罩与取消测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QRect, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QDialog

from db.database import DatabaseBootstrap
from services.capture_workflow_service import CaptureWorkflowService
from services.config_service import CaptureTypePayload, ConfigService
from ui.capture.capture_overlay import CaptureOverlay


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


@pytest.fixture
def config_service(tmp_path: Path) -> ConfigService:
    """创建隔离数据库下的配置服务。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    return ConfigService(db_path)


def test_ft_e3_s1_i2_01_拖拽截图成功生成临时文件(
    app: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：有效选区可生成临时图片。"""
    monkeypatch.setenv("STOCK_CAPTURE_CAPTURE_DIR", str(tmp_path / "captures"))
    overlay = CaptureOverlay(min_selection_size=8)

    source_image = QImage(220, 180, QImage.Format_ARGB32)
    source_image.fill(0xFFFF0000)
    success, payload = overlay.complete_selection(QRect(10, 10, 80, 60), source_image=source_image)

    assert success is True
    image_path = Path(payload)
    assert image_path.exists()
    assert image_path.suffix.lower() == ".png"


def test_bt_e3_s1_i2_01_极小选区被拦截(app: QApplication) -> None:
    """边界测试：选区小于最小阈值时阻止保存。"""
    overlay = CaptureOverlay(min_selection_size=8)
    source_image = QImage(100, 100, QImage.Format_ARGB32)
    source_image.fill(0xFFFFFFFF)
    success, message = overlay.complete_selection(QRect(0, 0, 2, 2), source_image=source_image)

    assert success is False
    assert "选区过小" in message


def test_bt_e3_s1_i2_02_遮罩默认完全透明(app: QApplication) -> None:
    """边界测试：截图遮罩默认透明，避免遮挡底层内容。"""
    overlay = CaptureOverlay()
    assert overlay.current_mask_alpha() == 0


def test_bt_e3_s1_i2_03_未传source时优先使用缓存快照(
    app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """边界测试：未传 source_image 时应优先从缓存快照裁剪。"""
    overlay = CaptureOverlay(min_selection_size=8)
    snapshot = QImage(200, 120, QImage.Format_ARGB32)
    snapshot.fill(0xFF123456)
    overlay._screen_image = snapshot  # type: ignore[attr-defined]

    captured: dict[str, QImage] = {}

    def fake_save_selection_image(image: QImage) -> str:
        captured["image"] = image
        return "runtime/captures/fake.png"

    monkeypatch.setattr(overlay, "_save_selection_image", fake_save_selection_image)

    success, payload = overlay.complete_selection(QRect(10, 8, 60, 40), source_image=None)
    assert success is True
    assert payload.endswith(".png")
    assert "image" in captured
    assert captured["image"].width() == 60
    assert captured["image"].height() == 40


def test_esc_cancel_restores_idle_state(config_service: ConfigService) -> None:
    """Esc取消时，工作流状态恢复到 idle。"""
    config_service.create_capture_type(
        CaptureTypePayload(name="市场动态", prompt_template="模板", is_enabled=True)
    )

    class FakeDialog:
        """业务类型选择框替身。"""

        def __init__(self, capture_types: list[dict], _parent: object | None) -> None:
            self.selected_capture_type = capture_types[0]

        def exec(self) -> int:
            return QDialog.Accepted

    class FakeOverlay(QObject):
        """截图遮罩替身。"""

        capture_completed = Signal(str)
        capture_cancelled = Signal()
        capture_error = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.show_called = False

        def showFullScreen(self) -> None:
            self.show_called = True

        def activateWindow(self) -> None:
            pass

    fake_overlay = FakeOverlay()
    workflow = CaptureWorkflowService(
        config_service,
        dialog_factory=FakeDialog,
        overlay_factory=lambda _parent: fake_overlay,  # type: ignore[arg-type]
    )
    selected, _ = workflow.select_capture_type()
    assert selected is True
    assert workflow.context.state == "capturing"

    workflow.start_capture_overlay()
    assert fake_overlay.show_called is True
    fake_overlay.capture_cancelled.emit()
    assert workflow.context.state == "idle"
