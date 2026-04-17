"""服务层基类。"""

from __future__ import annotations

from utils.logging_config import get_logger


class BaseService:
    """服务层通用基类，统一日志入口。"""

    def __init__(self) -> None:
        """初始化服务层基类。"""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("BaseService 初始化完成: %s", self.__class__.__name__)

