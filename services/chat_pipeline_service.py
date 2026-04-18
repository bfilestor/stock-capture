"""AI 对话异步编排服务。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from services.base_service import BaseService
from services.chat_service import ChatService
from services.errors import ServiceError


class ChatTaskSignals(QObject):
    """对话任务信号定义。"""

    stage = Signal(str)
    success = Signal(str)
    error = Signal(str, str)
    finished = Signal()


class ChatTaskWorker(QRunnable):
    """对话异步任务。"""

    def __init__(
        self,
        chat_service: ChatService,
        messages: list[dict[str, str]],
        max_retries: int = 1,
    ) -> None:
        """初始化对话任务。"""
        super().__init__()
        self.signals = ChatTaskSignals()
        self._chat_service = chat_service
        self._messages = messages
        self._max_retries = max_retries

    def _run_with_retry(self, func: Callable[[], str], retry_codes: set[str]) -> str:
        """带重试执行器。"""
        attempts = self._max_retries + 1
        last_exc: ServiceError | None = None
        for index in range(attempts):
            try:
                return func()
            except ServiceError as exc:
                last_exc = exc
                if exc.code not in retry_codes or index >= attempts - 1:
                    raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("对话重试执行异常：未获取到结果")

    def run(self) -> None:
        """在线程池中执行对话请求。"""
        try:
            self.signals.stage.emit("AI思考中")
            content = self._run_with_retry(
                lambda: self._chat_service.run_chat(self._messages),
                {"CHAT_001"},
            )
            self.signals.success.emit(content)
        except ServiceError as exc:
            self.signals.error.emit(exc.code, exc.message)
        except Exception as exc:  # pragma: no cover - 防御兜底
            self.signals.error.emit("PIPE_001", str(exc))
        finally:
            self.signals.finished.emit()


class ChatPipelineService(BaseService):
    """对话异步编排服务，提供防重入与状态回调。"""

    def __init__(
        self,
        chat_service: ChatService,
        thread_pool: QThreadPool | None = None,
        max_retries: int = 1,
    ) -> None:
        """初始化对话编排服务。"""
        super().__init__()
        self._chat_service = chat_service
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._max_retries = max_retries
        self._is_running = False
        self._worker: QRunnable | None = None

    def is_running(self) -> bool:
        """返回是否存在运行中的任务。"""
        return self._is_running

    def start_chat(
        self,
        messages: list[dict[str, str]],
        on_stage: Callable[[str], None],
        on_success: Callable[[str], None],
        on_error: Callable[[str, str], None],
    ) -> bool:
        """启动异步对话任务。"""
        if self._is_running:
            self.logger.debug("对话任务已在运行，拒绝重复启动")
            return False

        self._is_running = True
        worker = ChatTaskWorker(
            chat_service=self._chat_service,
            messages=messages,
            max_retries=self._max_retries,
        )
        self._worker = worker
        worker.signals.stage.connect(on_stage)

        def _on_success(content: str) -> None:
            """成功回调前先恢复可触发状态。"""
            self._is_running = False
            on_success(content)

        def _on_error(code: str, message: str) -> None:
            """失败回调前先恢复可触发状态。"""
            self._is_running = False
            on_error(code, message)

        worker.signals.success.connect(_on_success)
        worker.signals.error.connect(_on_error)
        worker.signals.finished.connect(self._on_worker_finished)
        self.logger.debug("对话任务已提交线程池")
        self._thread_pool.start(worker)
        return True

    def _on_worker_finished(self) -> None:
        """任务结束后恢复状态。"""
        self._is_running = False
        self._worker = None
        self.logger.debug("对话任务结束，状态恢复可触发")
