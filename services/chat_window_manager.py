"""对话窗口单实例管理服务。"""

from __future__ import annotations

from typing import Callable, Protocol

from ui.chat.chat_window import ChatWindow
from utils.logging_config import get_logger


class _ChatWindowLike(Protocol):
    """对话窗口协议，便于测试替身注入。"""

    def show(self) -> None:
        """显示窗口。"""

    def raise_(self) -> None:
        """窗口置顶。"""

    def activateWindow(self) -> None:
        """激活窗口。"""


class ChatWindowManager:
    """管理对话窗口单实例生命周期。"""

    def __init__(
        self,
        window_factory: Callable[[], _ChatWindowLike] | None = None,
    ) -> None:
        """初始化窗口管理器。"""
        self._logger = get_logger(__name__)
        self._window_factory = window_factory or ChatWindow
        self._window: _ChatWindowLike | None = None

    def show_chat_window(self) -> None:
        """显示并激活对话窗口，重复调用仅复用已有实例。"""
        if self._window is None:
            self._logger.debug("首次打开对话窗口，创建新实例")
            self._window = self._window_factory()
        else:
            self._logger.debug("复用已存在的对话窗口实例")
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()
