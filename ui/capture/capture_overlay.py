"""自由截图遮罩层。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from utils.app_paths import get_capture_temp_dir
from utils.logging_config import get_logger


class CaptureOverlay(QWidget):
    """全屏截图遮罩，支持拖拽选区与Esc取消。"""

    capture_completed = Signal(str)
    capture_cancelled = Signal()
    capture_error = Signal(str)

    def __init__(self, min_selection_size: int = 8, parent: QWidget | None = None) -> None:
        """初始化截图遮罩层。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._min_selection_size = min_selection_size
        self._start_point: QPoint | None = None
        self._end_point: QPoint | None = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self._logger.debug("CaptureOverlay 初始化完成")

    def current_rect(self) -> QRect:
        """返回当前选区矩形。"""
        if self._start_point is None or self._end_point is None:
            return QRect()
        return QRect(self._start_point, self._end_point).normalized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """按下鼠标开始选区。"""
        if event.button() != Qt.LeftButton:
            return
        self._start_point = event.position().toPoint()
        self._end_point = self._start_point
        self._logger.debug("截图开始点: %s", self._start_point)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖拽更新选区。"""
        if self._start_point is None:
            return
        self._end_point = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """释放鼠标后完成截图。"""
        if event.button() != Qt.LeftButton or self._start_point is None:
            return
        self._end_point = event.position().toPoint()
        selection = self.current_rect()
        self._logger.debug("截图释放选区: %s", selection)
        success, payload = self.complete_selection(selection)
        if success:
            self.capture_completed.emit(payload)
            self.close()
            return
        self.capture_error.emit(payload)
        self._logger.warning("截图失败: %s", payload)
        # 失败后保持遮罩，让用户可继续重选。
        self._start_point = None
        self._end_point = None
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """按Esc取消截图。"""
        if event.key() == Qt.Key_Escape:
            self._logger.debug("检测到Esc，取消截图")
            self.capture_cancelled.emit()
            self.close()
            return
        super().keyPressEvent(event)

    def paintEvent(self, _event) -> None:
        """绘制遮罩与选区边框。"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        rect = self.current_rect()
        if rect.isNull():
            return

        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(rect, Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor(0, 191, 255), 2))
        painter.drawRect(rect)

    def _save_selection_image(self, image: QImage) -> str:
        """保存截图并返回文件路径。"""
        capture_dir = get_capture_temp_dir()
        capture_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        file_path = capture_dir / file_name
        if not image.save(str(file_path), "PNG"):
            raise RuntimeError("保存截图文件失败")
        self._logger.debug("截图保存成功: %s", file_path)
        return str(file_path)

    def complete_selection(
        self,
        selection: QRect,
        source_image: QImage | None = None,
    ) -> tuple[bool, str]:
        """完成选区并保存图片，用于测试与运行时共用。"""
        if (
            selection.width() < self._min_selection_size
            or selection.height() < self._min_selection_size
        ):
            return False, "选区过小，请重新选择"

        try:
            if source_image is not None:
                target_image = source_image.copy(selection)
            else:
                screen = QGuiApplication.primaryScreen()
                if screen is None:
                    return False, "未检测到可用屏幕"
                pixmap = screen.grabWindow(
                    0, selection.x(), selection.y(), selection.width(), selection.height()
                )
                target_image = pixmap.toImage()
            image_path = self._save_selection_image(target_image)
            return True, image_path
        except Exception as exc:
            self._logger.exception("保存截图异常")
            return False, f"截图保存失败: {exc}"

