"""E1-S1-I2 托盘与生命周期测试。"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from PySide6.QtWidgets import QApplication, QMenu

from tray.tray_manager import TrayManager


@dataclass
class FakeTrayIcon:
    """用于测试的托盘图标替身。"""

    menu: QMenu | None = None
    show_count: int = 0
    hide_count: int = 0
    delete_count: int = 0

    def setContextMenu(self, menu: QMenu) -> None:
        """设置托盘右键菜单。"""
        self.menu = menu

    def show(self) -> None:
        """模拟显示托盘图标。"""
        self.show_count += 1

    def hide(self) -> None:
        """模拟隐藏托盘图标。"""
        self.hide_count += 1

    def deleteLater(self) -> None:
        """模拟延迟释放托盘图标。"""
        self.delete_count += 1


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication，避免重复创建。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e1_s1_i2_01_托盘菜单动作可触发(app: QApplication) -> None:
    """功能测试：托盘菜单固定三项且动作可触发。"""
    events = {"capture": 0, "settings": 0, "exit": 0}
    fake_tray_icon = FakeTrayIcon()

    manager = TrayManager(app, tray_icon_factory=lambda _app: fake_tray_icon)
    manager.bind_events(
        on_capture=lambda: events.__setitem__("capture", events["capture"] + 1),
        on_settings=lambda: events.__setitem__("settings", events["settings"] + 1),
        on_exit=lambda: events.__setitem__("exit", events["exit"] + 1),
    )
    manager.initialize()

    actions = manager.menu_actions()
    assert [action.text() for action in actions] == ["截图", "设置", "退出"]

    capture_action, settings_action, exit_action = actions
    capture_action.trigger()
    settings_action.trigger()
    exit_action.trigger()

    assert events == {"capture": 1, "settings": 1, "exit": 1}
    assert fake_tray_icon.show_count == 1
    assert fake_tray_icon.hide_count == 1
    assert fake_tray_icon.delete_count == 1


def test_bt_e1_s1_i2_01_重复触发退出保持幂等(app: QApplication) -> None:
    """边界测试：连续触发退出动作不会重复执行释放流程。"""
    exit_calls = {"count": 0}
    fake_tray_icon = FakeTrayIcon()

    manager = TrayManager(app, tray_icon_factory=lambda _app: fake_tray_icon)
    manager.bind_events(
        on_capture=lambda: None,
        on_settings=lambda: None,
        on_exit=lambda: exit_calls.__setitem__("count", exit_calls["count"] + 1),
    )
    manager.initialize()

    actions = manager.menu_actions()
    assert len(actions) == 3

    exit_action = actions[2]
    exit_action.trigger()
    exit_action.trigger()

    assert exit_calls["count"] == 1
    assert fake_tray_icon.hide_count == 1
    assert fake_tray_icon.delete_count == 1

