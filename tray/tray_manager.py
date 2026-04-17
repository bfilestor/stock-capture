"""托盘管理器实现。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from utils.logging_config import get_logger


class TrayManager:
    """托盘管理器，负责托盘菜单与生命周期控制。"""

    def __init__(
        self,
        app: QApplication,
        tray_icon_factory: Callable[[QApplication], QSystemTrayIcon] | None = None,
    ) -> None:
        """初始化托盘管理器。"""
        self._app = app
        self._logger = get_logger(__name__)
        self._tray_icon_factory = tray_icon_factory

        self._menu: QMenu | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._capture_action: QAction | None = None
        self._settings_action: QAction | None = None
        self._exit_action: QAction | None = None

        self._on_capture: Callable[[], None] = lambda: None
        self._on_settings: Callable[[], None] = lambda: None
        self._on_exit: Callable[[], None] = lambda: None
        self._exit_handled = False
        self._shutdown_called = False

    def _create_tray_icon(self) -> QSystemTrayIcon:
        """创建托盘图标对象，方便测试注入。"""
        if self._tray_icon_factory is not None:
            return self._tray_icon_factory(self._app)
        tray_icon = QSystemTrayIcon(self._app)
        if tray_icon.icon().isNull():
            # 设置一个空图标占位，避免平台报错。
            tray_icon.setIcon(QIcon())
        return tray_icon

    def _build_menu(self) -> QMenu:
        """构建固定三项菜单。"""
        menu = QMenu()
        self._capture_action = menu.addAction("截图")
        self._settings_action = menu.addAction("设置")
        self._exit_action = menu.addAction("退出")
        self._logger.debug("托盘菜单创建完成，菜单项=%s", [a.text() for a in menu.actions()])
        return menu

    def bind_events(
        self,
        on_capture: Callable[[], None],
        on_settings: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        """绑定托盘菜单动作回调。"""
        self._on_capture = on_capture
        self._on_settings = on_settings
        self._on_exit = on_exit
        self._logger.debug("托盘动作回调绑定完成")

    def _handle_capture(self) -> None:
        """处理“截图”动作。"""
        self._logger.debug("点击托盘菜单：截图")
        self._on_capture()

    def _handle_settings(self) -> None:
        """处理“设置”动作。"""
        self._logger.debug("点击托盘菜单：设置")
        self._on_settings()

    def _handle_exit(self) -> None:
        """处理“退出”动作，并保证幂等。"""
        if self._exit_handled:
            self._logger.debug("退出动作重复触发，已忽略")
            return

        self._exit_handled = True
        self._logger.debug("点击托盘菜单：退出，开始执行退出流程")
        self._on_exit()
        self.shutdown()

    def initialize(self) -> None:
        """初始化托盘图标、菜单和动作。"""
        if self._tray_icon is not None:
            self._logger.debug("托盘已初始化，跳过重复初始化")
            return

        if self._tray_icon_factory is None and not QSystemTrayIcon.isSystemTrayAvailable():
            self._logger.warning("当前环境不支持系统托盘，降级为仅保留事件循环")
            return

        self._tray_icon = self._create_tray_icon()
        self._menu = self._build_menu()

        assert self._capture_action is not None
        assert self._settings_action is not None
        assert self._exit_action is not None

        self._capture_action.triggered.connect(self._handle_capture)
        self._settings_action.triggered.connect(self._handle_settings)
        self._exit_action.triggered.connect(self._handle_exit)

        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.show()
        self._logger.debug("托盘初始化完成")

    def shutdown(self) -> None:
        """释放托盘资源并退出应用（幂等）。"""
        if self._shutdown_called:
            self._logger.debug("shutdown 已执行过，忽略重复调用")
            return

        self._shutdown_called = True
        self._logger.debug("开始释放托盘资源")

        if self._tray_icon is not None:
            self._tray_icon.hide()
            self._tray_icon.deleteLater()
            self._tray_icon = None
        self._menu = None

        self._logger.debug("托盘资源释放完成，准备退出应用")
        self._app.quit()

    def menu_actions(self) -> list[QAction]:
        """返回当前菜单动作列表，便于测试校验。"""
        if self._menu is None:
            return []
        return list(self._menu.actions())
