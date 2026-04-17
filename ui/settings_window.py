"""设置窗口。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from services.config_service import ConfigService
from ui.settings.ai_provider_tab import AIProviderTab
from ui.settings.capture_type_tab import CaptureTypeTab
from utils.logging_config import get_logger


class SettingsWindow(QWidget):
    """设置窗口，包含业务类型与AI配置两个页签。"""

    def __init__(self, db_path: Path, parent: QWidget | None = None) -> None:
        """初始化设置窗口。"""
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._config_service = ConfigService(db_path)
        self.setWindowTitle("设置")
        self.resize(980, 640)
        self._init_ui()

    def _init_ui(self) -> None:
        """构建设置窗口结构。"""
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget(self)
        self.capture_tab = CaptureTypeTab(self._config_service, self)
        self.ai_tab = AIProviderTab(self._config_service, self)
        tab_widget.addTab(self.capture_tab, "业务类型")
        tab_widget.addTab(self.ai_tab, "AI配置")
        layout.addWidget(tab_widget)
        self._logger.debug("设置窗口初始化完成")
