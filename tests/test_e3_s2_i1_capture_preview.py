"""E3-S2-I1 截图预览与重截流程测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QDialog, QSizePolicy

from db.database import DatabaseBootstrap
from services.capture_workflow_service import CaptureWorkflowService
from services.config_service import CaptureTypePayload, ConfigService
from ui.capture.capture_preview_dialog import CapturePreviewDialog


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


def _create_image_file(path: Path) -> str:
    """生成测试图片文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(100, 80, QImage.Format_ARGB32)
    image.fill(0xFF33AA66)
    assert image.save(str(path), "PNG")
    return str(path)


def _create_small_image_file(path: Path) -> str:
    """生成小尺寸测试图片文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(100, 20, QImage.Format_ARGB32)
    image.fill(0xFF2E7D32)
    assert image.save(str(path), "PNG")
    return str(path)


def test_ft_e3_s2_i1_01_预览重截与发送解析透传(
    app: QApplication, tmp_path: Path, config_service: ConfigService
) -> None:
    """功能测试：预览重截可回到截图，发送解析可透传上下文。"""
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
            self.show_count = 0

        def showFullScreen(self) -> None:
            self.show_count += 1

        def activateWindow(self) -> None:
            pass

    class FakePreview(QDialog):
        """预览窗口替身。"""

        retake_requested = Signal()
        send_requested = Signal(str)

        def __init__(self, image_path: str, _capture_type_name: str, _parent: object | None) -> None:
            super().__init__()
            self.image_path = image_path

        def show(self) -> None:
            pass

        def activateWindow(self) -> None:
            pass

    preview_instances: list[FakePreview] = []
    overlay_instances: list[FakeOverlay] = []
    parse_records: list[tuple[int | None, str, str]] = []

    class FakePipeline:
        """异步管线替身。"""

        def __init__(self) -> None:
            self.running = False

        def is_running(self) -> bool:
            return self.running

        def start_analysis(
            self,
            image_path: str,
            prompt: str,
            on_stage,
            on_success,
            on_error,
        ) -> bool:
            self.running = True
            on_stage("OCR识别中")
            on_stage("AI分析中")
            on_success("ocr文本", '{"ok":true}', '{"choices":[{"message":{"content":"{\\"ok\\":true}"}}]}')
            self.running = False
            return True

    def preview_factory(image_path: str, capture_type_name: str, parent: object | None) -> QDialog:
        preview = FakePreview(image_path, capture_type_name, parent)
        preview_instances.append(preview)
        return preview

    def on_parse_requested(context) -> None:
        parse_records.append((context.capture_type_id, context.capture_type_name, context.image_path))

    def overlay_factory(_parent: object | None):
        overlay = FakeOverlay()
        overlay_instances.append(overlay)
        return overlay

    workflow = CaptureWorkflowService(
        config_service,
        dialog_factory=FakeDialog,
        overlay_factory=overlay_factory,  # type: ignore[arg-type]
        preview_factory=preview_factory,
        on_parse_requested=on_parse_requested,
        analysis_pipeline=FakePipeline(),  # type: ignore[arg-type]
    )
    success, _ = workflow.select_capture_type()
    assert success is True

    workflow.start_capture_overlay()
    assert len(overlay_instances) == 1
    assert overlay_instances[0].show_count == 1

    image1 = _create_image_file(tmp_path / "capture_1.png")
    overlay_instances[0].capture_completed.emit(image1)
    assert workflow.context.state == "previewing"
    assert len(preview_instances) == 1

    preview_instances[-1].retake_requested.emit()
    assert workflow.context.state == "capturing"
    assert len(overlay_instances) == 2
    assert overlay_instances[1].show_count == 1
    assert not Path(image1).exists()

    image2 = _create_image_file(tmp_path / "capture_2.png")
    overlay_instances[1].capture_completed.emit(image2)
    assert len(preview_instances) == 2
    preview_instances[-1].send_requested.emit(image2)

    assert workflow.context.state == "editing"
    assert parse_records[-1][0] is not None
    assert parse_records[-1][1] == "市场动态"
    assert parse_records[-1][2] == image2


def test_bt_e3_s2_i1_01_预览图文件缺失提示重截(app: QApplication, tmp_path: Path) -> None:
    """边界测试：截图文件缺失时禁用发送并提示重截。"""
    missing_path = str(tmp_path / "not-exists.png")
    dialog = CapturePreviewDialog(missing_path, "市场动态")

    assert dialog.send_button.isEnabled() is False
    assert "截图失效" in dialog.status_label.text()


def test_bt_e3_s2_i1_03_小图预览尺寸策略避免自增长(
    app: QApplication, tmp_path: Path
) -> None:
    """边界测试：小图预览应使用忽略尺寸提示策略，避免布局被 pixmap 反向放大。"""
    image_path = _create_small_image_file(tmp_path / "small_preview.png")
    dialog = CapturePreviewDialog(image_path, "市场动态")

    policy = dialog.preview_label.sizePolicy()
    assert policy.horizontalPolicy() == QSizePolicy.Ignored
    assert policy.verticalPolicy() == QSizePolicy.Ignored


def test_bt_e3_s2_i1_02_重截遵循延时启动(
    config_service: ConfigService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """边界测试：重截请求应复用截图延时策略，避免预览框被截入快照。"""
    config_service.create_capture_type(
        CaptureTypePayload(name="市场总览", prompt_template="模板", is_enabled=True)
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
            self.show_count = 0

        def showFullScreen(self) -> None:
            self.show_count += 1

        def activateWindow(self) -> None:
            pass

    overlay_instances: list[FakeOverlay] = []

    def overlay_factory(_parent: object | None) -> FakeOverlay:
        overlay = FakeOverlay()
        overlay_instances.append(overlay)
        return overlay

    delay_record: dict[str, int] = {}

    def fake_single_shot(delay: int, callback) -> None:
        delay_record["value"] = delay
        callback()

    monkeypatch.setattr("services.capture_workflow_service.QTimer.singleShot", fake_single_shot)

    workflow = CaptureWorkflowService(
        config_service,
        dialog_factory=FakeDialog,
        overlay_factory=overlay_factory,  # type: ignore[arg-type]
        overlay_start_delay_ms=260,
    )
    selected, _ = workflow.select_capture_type()
    assert selected is True

    old_image = Path(_create_image_file(tmp_path / "retake_old.png"))
    workflow.context.image_path = str(old_image)
    workflow.context.state = "previewing"

    workflow._on_retake_requested()

    assert delay_record["value"] == 260
    assert workflow.context.state == "capturing"
    assert len(overlay_instances) == 1
    assert overlay_instances[0].show_count == 1
    assert old_image.exists() is False
