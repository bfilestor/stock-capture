"""托盘管理器占位实现。"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from utils.logging_config import get_logger


class TrayManager:
    """托盘管理器（E1-S1-I2 会补齐菜单和动作）。"""

    def __init__(self, app: QApplication) -> None:
        """初始化托盘管理器。"""
        self._app = app
        self._logger = get_logger(__name__)

    def initialize(self) -> None:
        """执行托盘初始化占位逻辑。"""
        self._logger.debug("TrayManager.initialize() 已执行，当前为占位实现")

