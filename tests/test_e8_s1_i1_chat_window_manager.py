"""E8-S1-I1 对话窗口单实例管理测试。"""

from __future__ import annotations

from dataclasses import dataclass

from services.chat_window_manager import ChatWindowManager


@dataclass
class FakeChatWindow:
    """对话窗口替身对象。"""

    show_count: int = 0
    raise_count: int = 0
    activate_count: int = 0

    def show(self) -> None:
        """模拟显示窗口。"""
        self.show_count += 1

    def raise_(self) -> None:
        """模拟窗口置顶。"""
        self.raise_count += 1

    def activateWindow(self) -> None:
        """模拟窗口激活。"""
        self.activate_count += 1


def test_ft_e8_s1_i1_01_首次打开对话窗口会创建并展示() -> None:
    """功能测试：点击对话入口可创建并显示窗口。"""
    created: list[FakeChatWindow] = []

    def factory() -> FakeChatWindow:
        window = FakeChatWindow()
        created.append(window)
        return window

    manager = ChatWindowManager(window_factory=factory)
    manager.show_chat_window()

    assert len(created) == 1
    assert created[0].show_count == 1
    assert created[0].raise_count == 1
    assert created[0].activate_count == 1


def test_bt_e8_s1_i1_01_重复打开仅激活已有实例不重复创建() -> None:
    """边界测试：连续点击对话入口时仅复用单实例窗口。"""
    created: list[FakeChatWindow] = []

    def factory() -> FakeChatWindow:
        window = FakeChatWindow()
        created.append(window)
        return window

    manager = ChatWindowManager(window_factory=factory)
    manager.show_chat_window()
    manager.show_chat_window()
    manager.show_chat_window()

    assert len(created) == 1
    assert created[0].show_count == 3
    assert created[0].raise_count == 3
    assert created[0].activate_count == 3
