"""后台任务基类占位。"""

from __future__ import annotations

from utils.logging_config import get_logger


class BaseWorker:
    """后台任务基类（后续 Issue 扩展为 QRunnable）。"""

    def __init__(self) -> None:
        """初始化后台任务基类。"""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("BaseWorker 初始化完成: %s", self.__class__.__name__)

