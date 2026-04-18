"""E8-S2-I2 对话异步管线测试。"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from services.chat_pipeline_service import ChatPipelineService
from services.errors import ServiceError


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    """提供共享 QApplication，确保事件循环可运行。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


class DummyChatService:
    """对话服务替身。"""

    def __init__(self, content: str = "ok", delay: float = 0.0, error: ServiceError | None = None) -> None:
        self._content = content
        self._delay = delay
        self._error = error
        self.call_count = 0
        self.last_messages: list[dict[str, str]] = []

    def run_chat(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        self.last_messages = list(messages)
        if self._delay > 0:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return self._content


def _wait_loop(timeout_ms: int = 2000) -> QEventLoop:
    """创建带超时退出的事件循环。"""
    loop = QEventLoop()
    QTimer.singleShot(timeout_ms, loop.quit)
    return loop


def test_ft_e8_s2_i2_01_对话阶段与成功回调(qt_app: QApplication) -> None:
    """功能测试：发送后回传阶段并返回助手文本。"""
    pipeline = ChatPipelineService(
        chat_service=DummyChatService(content="助手回复"),
        thread_pool=QThreadPool(),
    )
    stages: list[str] = []
    success_messages: list[str] = []
    loop = _wait_loop()

    started = pipeline.start_chat(
        messages=[{"role": "system", "content": "x"}, {"role": "user", "content": "y"}],
        on_stage=lambda stage: stages.append(stage),
        on_success=lambda content: (success_messages.append(content), loop.quit()),
        on_error=lambda _code, _message: loop.quit(),
    )
    assert started is True
    loop.exec()

    assert stages == ["AI思考中"]
    assert success_messages == ["助手回复"]
    assert pipeline.is_running() is False


def test_bt_e8_s2_i2_01_重复点击发送仅触发一次(qt_app: QApplication) -> None:
    """边界测试：并发发送时仅第一条任务被接受。"""
    dummy_service = DummyChatService(content="助手回复", delay=0.3)
    pipeline = ChatPipelineService(chat_service=dummy_service, thread_pool=QThreadPool())
    loop = _wait_loop(timeout_ms=3000)

    first = pipeline.start_chat(
        messages=[{"role": "system", "content": "x"}, {"role": "user", "content": "first"}],
        on_stage=lambda _stage: None,
        on_success=lambda _content: loop.quit(),
        on_error=lambda _code, _message: loop.quit(),
    )
    second = pipeline.start_chat(
        messages=[{"role": "system", "content": "x"}, {"role": "user", "content": "second"}],
        on_stage=lambda _stage: None,
        on_success=lambda _content: None,
        on_error=lambda _code, _message: None,
    )
    assert first is True
    assert second is False
    loop.exec()
    assert dummy_service.call_count == 1
